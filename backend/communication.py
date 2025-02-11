import asyncio
from fastapi import WebSocket
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class WebSocketCommunicator:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self._receiver_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start the message receiver task"""
        if self._receiver_task is None:
            self._receiver_task = asyncio.create_task(self._receive_messages())
            logger.info("WebSocket receiver task started")

    async def stop(self):
        """Stop the message receiver task"""
        if self._receiver_task:
            self._stop_event.set()
            try:
                await self._receiver_task
            except Exception as e:
                logger.error(f"Error during receiver shutdown: {e}")
            self._receiver_task = None
            logger.info("WebSocket receiver task stopped")

    def get_queue(self, message_type: str) -> asyncio.Queue:
        """Get or create a queue for a specific message type"""
        if message_type not in self.message_queues:
            self.message_queues[message_type] = asyncio.Queue()
            logger.debug(f"Created new queue for message type: {message_type}")
        return self.message_queues[message_type]

    async def _receive_messages(self):
        """Background task to receive and route messages"""
        try:
            while not self._stop_event.is_set():
                try:
                    message = await self.websocket.receive_json()
                    message_type = message.get("type", "default")
                    logger.debug(f"Received message of type {message_type}: {message}")
                    
                    # Route the message to appropriate queue
                    queue = self.get_queue(message_type)
                    await queue.put(message)
                    logger.debug(f"Routed message to queue: {message_type}")
                except Exception as e:
                    if "connection is closed" in str(e).lower():
                        logger.info("WebSocket connection closed")
                        break
                    logger.error(f"Error receiving message: {e}")
        except Exception as e:
            logger.error(f"Message receiver task error: {e}")
            self._stop_event.set()

    async def receive(self, message_type: str = "default") -> dict:
        """Receive a message of a specific type"""
        queue = self.get_queue(message_type)
        logger.debug(f"Waiting for message of type: {message_type}")
        message = await queue.get()
        logger.debug(f"Retrieved message from queue {message_type}: {message}")
        return message

    async def send(self, type_: str, content: Any):
        """Send a message with a specific type"""
        try:
            message = {"type": type_, "content": content}
            logger.debug(f"Sending message: {message}")
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._stop_event.set()
            raise
