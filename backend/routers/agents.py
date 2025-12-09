from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List
from sqlalchemy.exc import IntegrityError

from database import get_session
from models import Agent, AgentMCPServer, MCPServer, AgentKnowledgeFile, AgentRead, AgentUpdate

router = APIRouter(prefix="/api/v1/agents", tags=["Agent Management"])

@router.get("/", response_model=List[AgentRead])
def list_agents(session: Session = Depends(get_session)):
    agents = session.exec(select(Agent)).all()
    results: List[AgentRead] = []

    for agent in agents:
        linked_ids = [
            link_id
            for link_id in session.exec(
                select(AgentMCPServer.mcp_server_id).where(AgentMCPServer.agent_id == agent.id)
            ).all()
            if link_id is not None
        ]

        agent_data = agent.dict(exclude={"chat_sessions", "mcp_servers", "knowledge_files"})
        results.append(
            AgentRead(
                **agent_data,
                linked_mcp_ids=linked_ids,
                linked_mcp_count=len(linked_ids)
            )
        )

    return results

@router.post("/", response_model=Agent)
def create_agent(agent: Agent, session: Session = Depends(get_session)):
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent

@router.put("/{agent_id}", response_model=Agent)
def update_agent(agent_id: int, payload: AgentUpdate, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if payload.name is not None:
        agent.name = payload.name
    if payload.system_prompt is not None:
        agent.system_prompt = payload.system_prompt
    if payload.model is not None:
        agent.model = payload.model

    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent

@router.delete("/{agent_id}")
def delete_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    session.delete(agent)
    session.commit()
    return {"message": "Agent deleted"}

@router.post("/{agent_id}/link-mcp/{server_id}")
def link_mcp_to_agent(agent_id: int, server_id: int, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    server = session.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")

    # Idempotent link: skip duplicates instead of throwing 500 on unique constraint
    existing_link = session.get(AgentMCPServer, (agent_id, server_id))
    if existing_link:
        return {"message": "MCP already linked to agent"}

    link = AgentMCPServer(agent_id=agent_id, mcp_server_id=server_id)
    session.add(link)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # Likely duplicate link raced in; treat as success to keep UI happy
        return {"message": "MCP already linked to agent"}

    return {"message": "Linked successfully"}

@router.post("/{agent_id}/knowledge")
async def upload_agent_knowledge(agent_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    content = await file.read()
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
         raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
         
    knowledge = AgentKnowledgeFile(agent_id=agent_id, filename=file.filename, content=content_str)
    session.add(knowledge)
    session.commit()
    session.refresh(knowledge)
    return knowledge
