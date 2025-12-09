from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class SystemSetting(SQLModel, table=True):
    __tablename__ = "zairag_system_settings"
    key: str = Field(primary_key=True)
    value: str

class AgentMCPServer(SQLModel, table=True):
    __tablename__ = "zairag_agent_mcp_links"
    agent_id: Optional[int] = Field(default=None, foreign_key="zairag_agents.id", primary_key=True)
    mcp_server_id: Optional[int] = Field(
        default=None, foreign_key="zairag_mcp_servers.id", primary_key=True
    )


class Agent(SQLModel, table=True):
    __tablename__ = "zairag_agents"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    system_prompt: str
    model: str

    chat_sessions: List["ChatSession"] = Relationship(back_populates="agent")
    mcp_servers: List["MCPServer"] = Relationship(
        back_populates="agents", link_model=AgentMCPServer
    )
    knowledge_files: List["AgentKnowledgeFile"] = Relationship(back_populates="agent")


class AgentRead(SQLModel):
    """
    Lightweight response model for agent listings that includes MCP linkage info.
    """

    id: Optional[int]
    name: str
    system_prompt: str
    model: str

    linked_mcp_ids: List[int] = Field(default_factory=list)
    linked_mcp_count: int = 0

    class Config:
        from_attributes = True


class AgentKnowledgeFile(SQLModel, table=True):
    __tablename__ = "zairag_agent_knowledge_files"
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="zairag_agents.id")
    filename: str
    content: str

    agent: "Agent" = Relationship(back_populates="knowledge_files")


class MCPServer(SQLModel, table=True):
    __tablename__ = "zairag_mcp_servers"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    script: str
    command: str = Field(default="python")
    args: str = Field(default="[]") # JSON list of args
    cwd: str = Field(default="/app")
    env_vars: str = Field(default="{}") # JSON dict of env vars
    
    # Observability & Metadata
    status: str = Field(default="stopped") # stopped, running, error
    last_heartbeat: Optional[str] = Field(default=None) # ISO format datetime
    last_error: Optional[str] = Field(default=None)
    checksum: Optional[str] = Field(default=None) # SHA256
    size_bytes: Optional[int] = Field(default=None)

    agents: List["Agent"] = Relationship(
        back_populates="mcp_servers", link_model=AgentMCPServer
    )


class ChatSession(SQLModel, table=True):
    __tablename__ = "zairag_chat_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="zairag_agents.id")
    
    total_tokens: int = Field(default=0)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)

    agent: "Agent" = Relationship(back_populates="chat_sessions")
    chat_messages: List["ChatMessage"] = Relationship(back_populates="chat_session")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "zairag_chat_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="zairag_chat_sessions.id")
    role: str
    content: str

    chat_session: "ChatSession" = Relationship(back_populates="chat_messages")


# Request models


class SpawnMCPRequest(SQLModel):


    command: str


    args: List[str]


    cwd: str = "/app"





class ChatRequest(SQLModel):
    agent_id: int
    message: str
    include_reasoning: bool = True





class ChatResponse(SQLModel):


    response: str
