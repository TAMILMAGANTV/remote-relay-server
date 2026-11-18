import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()
hosts = {}

@app.get("/")
def home():
    return {"status": "Remote Desktop Relay Server is Running"}

@app.websocket("/ws/host/{host_id}/{password}")
async def host_endpoint(websocket: WebSocket, host_id: str, password: str):
    await websocket.accept()
    hosts[host_id] = {"ws": websocket, "password": password, "client": None}
    try:
        while True:
            data = await websocket.receive_text()
            client_ws = hosts[host_id].get("client")
            if client_ws:
                await client_ws.send_text(data)
    except WebSocketDisconnect:
        if host_id in hosts:
            client_ws = hosts[host_id].get("client")
            if client_ws:
                await client_ws.close()
            del hosts[host_id]

@app.websocket("/ws/client/{host_id}/{password}")
async def client_endpoint(websocket: WebSocket, host_id: str, password: str):
    await websocket.accept()
    if host_id not in hosts or hosts[host_id]["password"] != password:
        await websocket.send_text(json.dumps({"type": "error", "message": "தவறான ID அல்லது Password"}))
        await websocket.close()
        return

    hosts[host_id]["client"] = websocket
    await websocket.send_text(json.dumps({"type": "connected"}))
    try:
        while True:
            data = await websocket.receive_text()
            host_ws = hosts[host_id].get("ws")
            if host_ws:
                await host_ws.send_text(data)
    except WebSocketDisconnect:
        if host_id in hosts:
            hosts[host_id]["client"] = None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
  
