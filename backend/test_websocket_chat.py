import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import asyncio
from sqlmodel import Session, SQLModel, create_engine, select
from fastapi import FastAPI
import os
import sys

# Adjust path to import main from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app
from database import get_session
from dependencies import get_zai_client
from models import Agent, ChatSession, ChatMessage, AgentKnowledgeFile, MCPServer, AgentMCPServer

# Setup for in-memory SQLite for testing
engine = create_engine("sqlite:///test.db")

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override

    # Mock the ZaiClient
    mock_zai_client = AsyncMock()
    app.dependency_overrides[get_zai_client] = lambda: mock_zai_client

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_websocket_chat_reasoning_content_fallback(client: TestClient, session: Session):
    # Create a dummy agent
    agent = Agent(name="TestAgent", system_prompt="You are a test agent.", model="glm-4.5-flash")
    session.add(agent)
    session.commit()
    session.refresh(agent)

    agent_id = agent.id

    # Configure mock_zai_client to return specific chunks
    mock_zai_client = app.dependency_overrides[get_zai_client]()
    
    async def mock_chat_stream(*args, **kwargs):
        # Simulate a stream where content is empty but reasoning_content exists
        class MockDelta:
            def __init__(self, content=None, reasoning_content=None, tool_calls=None):
                self.content = content
                self.reasoning_content = reasoning_content
                self.tool_calls = tool_calls or []

        class MockChoice:
            def __init__(self, delta):
                self.delta = delta

        class MockChunk:
            def __init__(self, choices):
                self.choices = choices
                self.usage = None 

        # First chunk: empty content, but reasoning content
        yield MockChunk(choices=[MockChoice(delta=MockDelta(content="", reasoning_content="This is the reasoning part. "))])
        await asyncio.sleep(0.01) 
        # Second chunk: normal content
        yield MockChunk(choices=[MockChoice(delta=MockDelta(content="This is the content part."))])
        await asyncio.sleep(0.01)
        # Third chunk: empty content, but reasoning content
        yield MockChunk(choices=[MockChoice(delta=MockDelta(content=None, reasoning_content="More reasoning. "))])
        await asyncio.sleep(0.01)
        # Final chunk
        yield MockChunk(choices=[MockChoice(delta=MockDelta(content="Final piece."))])

    mock_zai_client.chat_stream.return_value = mock_chat_stream()

    # Connect to the websocket
    with client.websocket_connect(f"/api/v1/ws/chat/{agent_id}") as websocket:
        websocket.send_text("Hello agent")

        received_tokens = []
        full_response = ""

        # Expect 4 token chunks and 1 done message
        for _ in range(5): 
            response = websocket.receive_json()
            if response["type"] == "token":
                received_tokens.append(response["content"])
                full_response += response["content"]
            elif response["type"] == "done":
                break
        
        expected_response = "This is the reasoning part. This is the content part.More reasoning. Final piece."
        assert full_response == expected_response
        assert received_tokens == [
            "This is the reasoning part. ", 
            "This is the content part.", 
            "More reasoning. ", 
            "Final piece."
        ]
    
    # Verify chat session and messages are saved
    chat_sessions = session.exec(select(ChatSession)).all()
    assert len(chat_sessions) == 1
    
    messages = session.exec(select(ChatMessage).where(ChatMessage.chat_session_id == chat_sessions[0].id)).all()
    assert len(messages) == 2 # user message + assistant message
    assert messages[0].role == "user"
    assert messages[0].content == "Hello agent"
    assert messages[1].role == "assistant"
    assert messages[1].content == expected_response
