from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session, select
import json
import logging
import asyncio
import os
from typing import List, Dict, Any, Tuple

from database import get_session
from models import Agent, AgentMCPServer, MCPServer, AgentKnowledgeFile, ChatSession, ChatMessage
from dependencies import get_mcp_manager, get_zai_client
from mcp_manager import MCPManager
from zai_client import ZaiClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["WebSocket Chat"])

# Global Semaphore to limit concurrent Active Chats (Queue Manager)
MAX_CONCURRENT_CHATS = 5
chat_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHATS)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)

manager = ConnectionManager()

def save_message(session: Session, chat_session_id: int, role: str, content: str):
    msg = ChatMessage(chat_session_id=chat_session_id, role=role, content=content)
    session.add(msg)
    session.commit()

@router.websocket("/chat/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    agent_id: int,
    session: Session = Depends(get_session),
    mcp_manager: MCPManager = Depends(get_mcp_manager),
    zai_client: ZaiClient = Depends(get_zai_client)
):
    await manager.connect(websocket)
    try:
        # 1. Load Agent
        agent = session.get(Agent, agent_id)
        if not agent:
            await manager.send_json(websocket, {"type": "error", "content": "Agent not found"})
            await websocket.close()
            return
            
        # 1.5 Create Chat Session
        chat_session = ChatSession(agent_id=agent.id)
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)

        # 2. Inject Knowledge
        knowledge_files = session.exec(select(AgentKnowledgeFile).where(AgentKnowledgeFile.agent_id == agent.id)).all()
        injected_context = ""
        if knowledge_files:
            injected_context = "\n\n--- Contextual Information ---\n"
            for k_file in knowledge_files:
                injected_context += f"File: {k_file.filename}\nContent:\n{k_file.content}\n\n"
            injected_context += "----------------------------\n\n"
        
        final_system_prompt = agent.system_prompt + injected_context
        
        # 3. Setup Tools
        links = session.exec(select(AgentMCPServer).where(AgentMCPServer.agent_id == agent.id)).all()
        mcp_server_ids = [link.mcp_server_id for link in links]
        tools = []
        tool_map = {} 

        for server_id in mcp_server_ids:
            try:
                mcp_server_db = session.get(MCPServer, server_id)
                if mcp_server_db:
                    status = await mcp_manager.get_mcp_status(str(server_id))
                    if status.get("status") == "not found":
                         # Resolve script path
                         base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                         scripts_dir = os.getenv("MCP_SCRIPTS_DIR", os.path.join(base_dir, "mcp-runtime-scripts"))
                         full_script_path = os.path.join(scripts_dir, mcp_server_db.script)
                         
                         # Parse env_vars
                         env_vars = {}
                         if mcp_server_db.env_vars:
                             try:
                                 env_vars = json.loads(mcp_server_db.env_vars)
                             except Exception:
                                 logger.warning(f"Invalid env_vars for MCP {server_id}")

                         await mcp_manager.spawn_mcp(str(server_id), "python", [full_script_path], env=env_vars)
                
                server_tools = await mcp_manager.list_mcp_tools(str(server_id))
                for tool in server_tools:
                    tool_def = tool.model_dump(exclude_none=True)
                    openai_tool = {
                        "type": "function",
                        "function": {
                            "name": tool_def["name"],
                            "description": tool_def.get("description"),
                            "parameters": tool_def.get("inputSchema") 
                        }
                    }
                    tools.append(openai_tool)
                    tool_map[tool_def["name"]] = str(server_id)
            except Exception as e:
                logger.warning(f"Error loading tools for server {server_id}: {e}")
                # Notify client of the error
                await manager.send_json(websocket, {
                    "type": "token", 
                    "content": f"\n\n[System Warning: Failed to load MCP tools for '{mcp_server_db.name if mcp_server_db else server_id}'. Error: {str(e)}]\n\n"
                })

        # 4. Message Loop
        messages = [{"role": "system", "content": final_system_prompt}]
        
        while True:
            # Wait for user input
            try:
                data = await websocket.receive_text()
                # Parse if JSON, else treat as string
                try:
                    payload = json.loads(data)
                    user_msg = payload.get("message", "")
                    include_reasoning = payload.get("include_reasoning", True)
                except:
                    user_msg = data
                    include_reasoning = True
                
                messages.append({"role": "user", "content": user_msg})
                save_message(session, chat_session.id, "user", user_msg)

                # Queue Manager: Acquire Semaphore
                async with chat_semaphore:
                    # Start Multi-Turn Loop
                    prompt_tok, compl_tok, total_tok = await run_chat_loop(
                        websocket, zai_client, mcp_manager, messages, agent.model, tools, tool_map, session, chat_session.id, include_reasoning
                    )
                    
                    # Update Session Token Usage
                    chat_session.prompt_tokens += prompt_tok
                    chat_session.completion_tokens += compl_tok
                    chat_session.total_tokens += total_tok
                    session.add(chat_session)
                    session.commit()

                # Send Done signal for this turn
                await manager.send_json(websocket, {"type": "done", "tokens": {"prompt": prompt_tok, "completion": compl_tok, "total": total_tok}})

            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
            except Exception as e:
                logger.error(f"WS Error: {e}")
                await manager.send_json(websocket, {"type": "error", "content": str(e)})
                break

    except Exception as e:
         logger.error(f"Critical WS Error: {e}")
         await manager.disconnect(websocket)


async def run_chat_loop(
    websocket: WebSocket, 
    zai_client: ZaiClient, 
    mcp_manager: MCPManager,
    messages: List[Dict], 
    model: str, 
    tools: List[Dict], 
    tool_map: Dict,
    session: Session,
    chat_session_id: int,
    include_reasoning: bool = True
) -> Tuple[int, int, int]:
    max_turns = 5
    
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens_sum = 0

    for turn in range(max_turns):
        # Stream response from Z.ai
        stream = zai_client.chat_stream(
            messages=messages,
            model=model,
            tools=tools if tools else None,
            stream_options={"include_usage": True} 
        )

        current_content = ""
        tool_calls = []
        current_tool_call = None
        
        # Usage tracking for this turn
        turn_usage = None

        async for chunk in stream:
            # Check for usage field first
            if hasattr(chunk, "usage") and chunk.usage:
                turn_usage = chunk.usage

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            
            # Handle Content
            response_text = delta.content
            if include_reasoning and not response_text and hasattr(delta, "reasoning_content") and delta.reasoning_content:
                response_text = delta.reasoning_content

            if response_text:
                current_content += response_text
                await manager.send_json(websocket, {"type": "token", "content": response_text})

            # Handle Tool Calls
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    if tc_delta.id:
                        # New Tool Call starting
                        if current_tool_call:
                            tool_calls.append(current_tool_call)
                        
                        current_tool_call = {
                            "id": tc_delta.id,
                            "function": {
                                "name": tc_delta.function.name,
                                "arguments": ""
                            },
                            "type": "function"
                        }
                    
                    if current_tool_call and tc_delta.function.arguments:
                        current_tool_call["function"]["arguments"] += tc_delta.function.arguments

        # Append last tool call if any
        if current_tool_call:
            tool_calls.append(current_tool_call)

        # Accumulate Tokens
        if turn_usage:
            total_prompt_tokens += turn_usage.prompt_tokens
            total_completion_tokens += turn_usage.completion_tokens
            total_tokens_sum += turn_usage.total_tokens

        # Construct the assistant message for history
        assistant_msg = {"role": "assistant"}
        if current_content:
            assistant_msg["content"] = current_content
            save_message(session, chat_session_id, "assistant", current_content)
            
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
            # We don't save full structured tool calls to simple text DB easily, 
            # but we can save a summary or modify schema later. 
            # For now, just save content if exists.
        
        messages.append(assistant_msg)

        # If no tools called, we are done with this turn loop (wait for user)
        if not tool_calls:
            return total_prompt_tokens, total_completion_tokens, total_tokens_sum

        # Execute Tools
        for tool_call in tool_calls:
            fn_name = tool_call["function"]["name"]
            args_str = tool_call["function"]["arguments"]
            call_id = tool_call["id"]
            
            await manager.send_json(websocket, {"type": "tool_start", "tool": fn_name, "input": args_str})
            
            result_content = "Error executing tool"
            if fn_name in tool_map:
                try:
                    args = json.loads(args_str)
                    server_id = tool_map[fn_name]
                    
                    # Call MCP
                    result = await mcp_manager.call_mcp_tool(server_id, fn_name, args)
                    
                    # Format result
                    if isinstance(result, list):
                        result_content = "\n".join([c.text for c in result if c.type == 'text'])
                    elif hasattr(result, 'content') and isinstance(result.content, list):
                        result_content = "\n".join([c.text for c in result.content if c.type == 'text'])
                    else:
                        result_content = str(result)
                        
                except Exception as e:
                    result_content = f"Error: {str(e)}"
            else:
                result_content = "Tool not found"

            await manager.send_json(websocket, {"type": "tool_end", "result": result_content})
            
            # Append Tool Result to history
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": result_content
            })
            save_message(session, chat_session_id, "tool", f"Tool: {fn_name}\nResult: {result_content}")
        
        # Loop continues to next turn to let AI process tool results
        
    return total_prompt_tokens, total_completion_tokens, total_tokens_sum
