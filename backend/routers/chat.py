from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any
import json
import logging
import os
from openai import RateLimitError

from database import get_session
from models import Agent, AgentMCPServer, ChatRequest, ChatResponse, MCPServer, AgentKnowledgeFile
from dependencies import get_mcp_manager, get_zai_client
from mcp_manager import MCPManager
from zai_client import ZaiClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest, 
    session: Session = Depends(get_session),
    mcp_manager: MCPManager = Depends(get_mcp_manager),
    zai_client: ZaiClient = Depends(get_zai_client)
):
    # 1. Load Agent
    agent = session.get(Agent, request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # 1.5. Inject Knowledge Files into System Prompt
    knowledge_files = session.exec(select(AgentKnowledgeFile).where(AgentKnowledgeFile.agent_id == agent.id)).all()
    injected_context = ""
    if knowledge_files:
        injected_context = "\n\n--- Contextual Information ---\n"
        for k_file in knowledge_files:
            injected_context += f"File: {k_file.filename}\nContent:\n{k_file.content}\n\n"
        injected_context += "----------------------------\n\n"
    
    final_system_prompt = agent.system_prompt + injected_context

    # 2. Load Linked MCP Servers
    links = session.exec(select(AgentMCPServer).where(AgentMCPServer.agent_id == agent.id)).all()
    mcp_server_ids = [link.mcp_server_id for link in links]
    
    # 3. Fetch Tools and Build Map
    tools = []
    tool_map = {} # tool_name -> mcp_server_id
    
    # Determine paths relative to this file's parent (backend/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.getenv("MCP_SCRIPTS_DIR", os.path.join(base_dir, "mcp-runtime-scripts"))

    for server_id in mcp_server_ids:
        try:
            # Ensure server is "started" (registered in manager)
            mcp_server_db = session.get(MCPServer, server_id)
            if mcp_server_db:
                # Check if registered
                status = await mcp_manager.get_mcp_status(str(server_id))
                if status.get("status") == "not found":
                     # Register it
                     env_vars = {}
                     if mcp_server_db.env_vars:
                         try:
                             env_vars = json.loads(mcp_server_db.env_vars)
                         except:
                             pass
                    
                     args = []
                     if mcp_server_db.args:
                         try:
                             args = json.loads(mcp_server_db.args)
                         except:
                             pass
                     
                     if not args and mcp_server_db.command == "python":
                         # Resolve full path
                         full_script_path = os.path.join(scripts_dir, mcp_server_db.script)
                         args = [full_script_path]

                     await mcp_manager.spawn_mcp(
                         str(server_id), 
                         mcp_server_db.command, 
                         args,
                         cwd=mcp_server_db.cwd,
                         env=env_vars
                     )

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
            logger.warning(f"Error fetching tools from server {server_id}: {e}")
            # Continue without these tools

    # 4. Prepare Chat History
    messages = [
        {"role": "system", "content": final_system_prompt},
        {"role": "user", "content": request.message}
    ]

    # 5. Chat Loop (Handle Tool Calls)
    max_turns = 5
    for _ in range(max_turns):
        # Call Z.ai
        try:
            message = await zai_client.chat(
                messages=messages,
                model=agent.model,
                tools=tools if tools else None,
                include_reasoning=agent.reasoning_enabled
            )
        except RateLimitError:
            logger.error("Z.ai Rate Limit Exceeded")
            raise HTTPException(status_code=429, detail="Z.ai API Rate Limit Exceeded. Please try again later.")
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Z.ai Error: {str(e)}")

        # Append assistant message to history
        messages.append(message)

        # Check for tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments
                tool_args = json.loads(tool_args_str)
                
                if tool_name in tool_map:
                    server_id = tool_map[tool_name]
                    try:
                        # Execute Tool
                        result = await mcp_manager.call_mcp_tool(server_id, tool_name, tool_args)
                        
                        # Format result for OpenAI
                        content_str = str(result)
                        if isinstance(result, list):
                             content_str = "\n".join([c.text for c in result if c.type == 'text'])
                        elif hasattr(result, 'content') and isinstance(result.content, list):
                             content_str = "\n".join([c.text for c in result.content if c.type == 'text'])

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content_str
                        })
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error executing tool: {str(e)}"
                        })
                else:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "Tool not found or not linked to this agent."
                    })
        else:
            # No tool calls, final response
            return ChatResponse(response=message.content)
            
    return ChatResponse(response="Max chat turns reached.")
