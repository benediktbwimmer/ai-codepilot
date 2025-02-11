from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import asyncio
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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



async def listen_for_stop(comm: WebSocketCommunicator):
    """
    Listen for a stop command from the frontend.
    Assumes that a message with {"type": "stop"} is sent.
    """
    message = await comm.receive("stop")
    return message

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection initiated.")
    await websocket.accept()
    comm = WebSocketCommunicator(websocket)
    orchestration_task = None
    
    try:
        # Start the message router and wait for it to be ready
        await comm.start()
        logger.info("WebSocket communicator started.")
        
        # Wait for the initial message containing the user request
        init_msg = await comm.receive("default")
        if not init_msg:
            raise ValueError("No initial message received")
            
        user_prompt = init_msg.get("content", "")
        if not user_prompt:
            raise ValueError("No user prompt in initial message")
            
        logger.info(f"Received user prompt: {user_prompt}")
        
        # Extract config from init message
        config = init_msg.get("config", {})
        review = config.get("review", True)
        max_iterations = config.get("max_iterations", 1)
        root_directory = config.get("root_directory", ".")
        
        # Build the repository map and generate the stub.
        rm = RepoMap(root_directory)
        rm.build_map()
        repo_stub = rm.to_python_stub()
        logger.info("Repository map built and stub generated.")
        
        # Create and run the orchestrator agent.
        orchestrator = OrchestratorAgent(
            repo_stub, comm, review=review, max_iterations=max_iterations, root_directory=root_directory
        )
        await comm.send("log", "Starting orchestration...")
        logger.info("Starting orchestration.")
        
        # Start the orchestration task and stop listener
        orchestration_task = asyncio.create_task(orchestrator.run(user_prompt))
        stop_task = asyncio.create_task(listen_for_stop(comm))
        
        # Wait until one of the tasks completes
        done, pending = await asyncio.wait(
            [orchestration_task, stop_task], return_when=asyncio.FIRST_COMPLETED
        )
        
        if stop_task in done:
            if not orchestration_task.done():
                orchestration_task.cancel()
                await comm.send("log", "Orchestration cancelled by user.")
                logger.info("Orchestration cancelled by user.")
        else:
            stop_task.cancel()
            await comm.send("completed", "Orchestration completed successfully.")
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except asyncio.CancelledError:
        logger.info("Orchestration task cancelled.")
    except Exception as e:
        logger.error(f"Error in WebSocket communication: {str(e)}")
        await comm.send("error", str(e))
    finally:
        await comm.stop()
        if orchestration_task and not orchestration_task.done():
            orchestration_task.cancel()