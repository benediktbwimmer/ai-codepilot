from fastapi import WebSocket

class WebSocketCommunicator:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def send(self, type: str, content: str):
        await self.websocket.send_json({"type": type, "content": content})

    async def receive(self) -> str:
        data = await self.websocket.receive_json()
        return data.get("content", "")
