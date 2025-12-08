from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class AgentMCPServer(SQLModel, table=True):
    agent_id: Optional[int] = Field(default=None, foreign_key="agent.id", primary_key=True)
    mcp_server_id: Optional[int] = Field(
        default=None, foreign_key="mcpserver.id", primary_key=True
    )


class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    system_prompt: str
    model: str

    chat_sessions: List["ChatSession"] = Relationship(back_populates="agent")
    mcp_servers: List["MCPServer"] = Relationship(
        back_populates="agents", link_model=AgentMCPServer
    )
    knowledge_files: List["AgentKnowledgeFile"] = Relationship(back_populates="agent")


class AgentKnowledgeFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    filename: str
    content: str

    agent: "Agent" = Relationship(back_populates="knowledge_files")


class MCPServer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    script: str
    env_vars: str

    agents: List["Agent"] = Relationship(
        back_populates="mcp_servers", link_model=AgentMCPServer
    )


class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")

    agent: "Agent" = Relationship(back_populates="chat_sessions")
    chat_messages: List["ChatMessage"] = Relationship(back_populates="chat_session")


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chatsession.id")
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





class ChatResponse(SQLModel):


    response: str

