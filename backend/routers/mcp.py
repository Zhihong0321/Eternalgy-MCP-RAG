from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List
import shutil
import os

from database import get_session
from models import MCPServer
from dependencies import get_mcp_manager
from mcp_manager import MCPManager

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP Management"])

@router.get("/servers", response_model=List[MCPServer])
def list_mcp_servers(session: Session = Depends(get_session)):
    servers = session.exec(select(MCPServer)).all()
    return servers

@router.post("/servers", response_model=MCPServer)
def create_mcp_server(server: MCPServer, session: Session = Depends(get_session)):
    session.add(server)
    session.commit()
    session.refresh(server)
    return server

@router.delete("/servers/{server_id}")
async def delete_mcp_server(server_id: int, session: Session = Depends(get_session), mcp_manager: MCPManager = Depends(get_mcp_manager)):
    server = session.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Stop if running
    await mcp_manager.terminate_mcp(str(server_id))
    
    session.delete(server)
    session.commit()
    return {"ok": True}

@router.post("/servers/{server_id}/start")
async def start_mcp_server(server_id: int, session: Session = Depends(get_session), mcp_manager: MCPManager = Depends(get_mcp_manager)):
    server = session.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Parse args from string if stored as JSON string, or assume simple list
    # For now, assuming 'script' is the filename and we run with python
    # In a real app, 'script' might be the full command or we parse 'env_vars'
    
    # We'll assume standard python script execution for now
    command = "python"
    args = [server.script] 
    
    try:
        result = await mcp_manager.spawn_mcp(str(server_id), command, args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_id}/stop")
async def stop_mcp_server(server_id: int, mcp_manager: MCPManager = Depends(get_mcp_manager)):
    await mcp_manager.terminate_mcp(str(server_id))
    return {"message": "Server stopped"}

@router.get("/servers/{server_id}/status")
async def mcp_server_status(server_id: int, mcp_manager: MCPManager = Depends(get_mcp_manager)):
    status = await mcp_manager.get_mcp_status(str(server_id))
    return {"status": status}

@router.get("/servers/{server_id}/tools")
async def mcp_server_tools(server_id: int, mcp_manager: MCPManager = Depends(get_mcp_manager)):
    try:
        tools = await mcp_manager.list_mcp_tools(str(server_id))
        return {"tools": [tool.model_dump() for tool in tools]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_id}/call/{tool_name}")
async def call_mcp_server_tool(server_id: int, tool_name: str, tool_args: dict, mcp_manager: MCPManager = Depends(get_mcp_manager)):
    try:
        result = await mcp_manager.call_mcp_tool(str(server_id), tool_name, tool_args)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_mcp_script(file: UploadFile = File(...)):
    upload_dir = "/app/scripts"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "path": file_path}
