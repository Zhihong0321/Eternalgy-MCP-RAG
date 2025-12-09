import os
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, text, Session
from sqlalchemy.exc import OperationalError
import logging

from database import engine
from dependencies import mcp_manager, zai_client
from routers import mcp, chat, agents, websocket_chat, settings
from models import SystemSetting

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
app.include_router(websocket_chat.router)
app.include_router(settings.router)

# Set up CORS
origins = ["http://localhost:8080"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def seed_mcp_scripts():
    """Seeds initial MCP scripts to the persistent volume if missing."""
    # Determine paths relative to this file (main.py) to ensure compatibility 
    # with different environments (Docker, Railway/Nixpacks, Local).
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default: ./mcp-runtime-scripts (relative to backend/)
    scripts_dir = os.getenv("MCP_SCRIPTS_DIR", os.path.join(base_dir, "mcp-runtime-scripts"))
    
    # Default: ./mcp_servers (relative to backend/)
    initial_dir = os.getenv("MCP_INITIAL_DIR", os.path.join(base_dir, "mcp_servers"))
    
    # Create target dir if it doesn't exist (it should be a volume, but just in case)
    os.makedirs(scripts_dir, exist_ok=True)
    
    if os.path.exists(initial_dir):
        logger.info(f"Syncing MCP scripts from {initial_dir} to {scripts_dir}...")
        for item_name in os.listdir(initial_dir):
            src_path = os.path.join(initial_dir, item_name)
            dst_path = os.path.join(scripts_dir, item_name)

            try:
                if os.path.isdir(src_path):
                    # dirs_exist_ok=True allows overwriting/merging
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    logger.info(f"Synced directory {item_name}")
                elif os.path.isfile(src_path) and (item_name.endswith(".py") or item_name.endswith(".json")):
                    shutil.copy2(src_path, dst_path)
                    logger.info(f"Synced file {item_name}")
            except Exception as e:
                logger.error(f"Failed to sync {item_name}: {e}")
    else:
        logger.warning(f"Initial MCP directory {initial_dir} not found. Skipping seeding.")

@app.on_event("startup")
async def on_startup():
    # create_db_and_tables() # Disabled for production/Railway. Database schema is managed externally.
    seed_mcp_scripts()
    # Load Z.ai Key from DB if exists
    try:
        with Session(engine) as session:
            setting = session.get(SystemSetting, "zai_api_key")
            if setting and setting.value:
                logger.info("Loading Z.ai API Key from Database...")
                zai_client.update_api_key(setting.value)
    except Exception as e:
        logger.warning(f"Failed to load Z.ai key from DB on startup: {e}")

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

# ---------- Frontend Static Hosting ----------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend-dist")
INDEX_PATH = os.path.join(FRONTEND_DIR, "index.html")

if os.path.isdir(FRONTEND_DIR):
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")


@app.get("/", include_in_schema=False)
def serve_frontend_index():
    if os.path.isfile(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"status": "Z.ai Backend API is running (frontend not built)"}


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    if os.path.isfile(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
