import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, text
from sqlalchemy.exc import OperationalError
import logging

from database import engine
from dependencies import mcp_manager # Use the shared instance
from routers import mcp, chat, agents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI(
    title="Z.ai Chatbot System API",
    description="Backend API for the Z.ai Chatbot System.",
    version="0.1.0",
)

app.include_router(mcp.router)
app.include_router(chat.router)
app.include_router(agents.router)

# Set up CORS
origins = ["http://localhost:8080"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ZaiClient globally (Moved to dependencies.py)
# zai_client = ZaiClient(api_key=os.getenv("ZAI_API_KEY"))


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()

@app.on_event("shutdown")
async def on_shutdown():
    await mcp_manager.shutdown_all_mcps()


def check_database_connection():
    if not engine:
        return False, "DATABASE_URL not configured"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection successful"
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False, "Database connection failed"
    except Exception as e:
        logger.error(f"An unexpected error occurred during database check: {e}")
        return False, "An unexpected error occurred"

@app.get("/api/v1/", tags=["Status"])
def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"status": "Z.ai Backend API is running"}

@app.get("/api/v1/health", tags=["Health Check"])
def health_check():
    """
    Checks the status of the database connection and returns a summary.
    """
    db_ok, db_status = check_database_connection()
    
    status_code = 200 if db_ok else 503
    
    return {
        "api_status": "ok",
        "database_status": {
            "ok": db_ok,
            "message": db_status,
        }
    }




if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
