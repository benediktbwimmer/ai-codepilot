from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
from backend.repo_map import RepoMap
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.communication import WebSocketCommunicator
from backend.utils import get_file_content
import logging

# Load environment variables
load_dotenv()

# Validate required environment variables
required_vars = ['OPENAI_API_KEY', 'GEMINI_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")


# Serve the frontend page.
@app.get("/")
async def get_index():
    logger.info("Received request for index page.")
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        logger.info("Successfully read index.html.")
        return HTMLResponse(html_content)
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to fetch file content.
@app.get("/api/file_content")
async def get_file_content_endpoint(file_path: str):
    logger.info(f"Received request for file content: {file_path}")
    try:
        content = get_file_content(file_path)
        if content.startswith("Error"):
            logger.warning(f"Error fetching file content: {content}")
            raise HTTPException(status_code=404, detail=content)
        logger.info(f"Successfully fetched content for {file_path}")
        return {"content": content}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error fetching file content: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection initiated.")
    await websocket.accept()
    comm = WebSocketCommunicator(websocket)
    try:
        # Wait for the initial message containing the user request.
        init_msg = await websocket.receive_json()
        user_prompt = init_msg.get("content", "")
        logger.info(f"Received user prompt: {user_prompt}")
        
        # Build the repository map and generate the stub.
        rm = RepoMap(".")
        rm.build_map()
        repo_stub = rm.to_python_stub()
        logger.info("Repository map built and stub generated.")
        logger.info(f"Repository stub: {repo_stub}")

        # Extract review and max_iterations flags
        review = init_msg.get("review", True)
        max_iterations = init_msg.get("max_iterations", 1)
        # Create and run the orchestrator agent.
        orchestrator = OrchestratorAgent(repo_stub, comm, review=review, max_iterations=max_iterations)
        await comm.send("log", "Starting orchestration...")
        logger.info("Starting orchestration.")
        await orchestrator.run(user_prompt)
        await comm.send("log", "Orchestration completed.")
        logger.info("Orchestration completed.")
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket communication: {e}")