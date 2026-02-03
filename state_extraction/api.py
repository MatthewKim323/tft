"""
FastAPI Server for TFT State Extraction
Provides REST API and WebSocket for real-time state streaming
"""

import asyncio
import json
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .state_builder import StateBuilder, GameState
from .config import Config


# Global state builder instance
state_builder: Optional[StateBuilder] = None
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage state builder lifecycle"""
    global state_builder
    print("Initializing State Extraction API...")
    state_builder = StateBuilder(config)
    yield
    print("Shutting down State Extraction API...")
    if state_builder:
        state_builder.close()


app = FastAPI(
    title="TFT State Extraction API",
    description="Real-time TFT game state extraction using YOLO + OCR",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === REST Endpoints ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "TFT State Extraction API"}


@app.get("/state")
async def get_state(mode: str = "fast"):
    """
    Get current game state
    
    Args:
        mode: "fast" (OCR only) or "full" (OCR + YOLO)
    """
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    try:
        if mode == "full":
            state = state_builder.build_state_full()
        else:
            state = state_builder.build_state_fast()
        
        return state.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/player")
async def get_player_state():
    """Get only player HUD info (gold, HP, level)"""
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    try:
        state = state_builder.build_state_fast()
        return {
            "player": state.player,
            "stage": state.stage,
            "timestamp": state.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/board")
async def get_board_state():
    """Get board and bench state"""
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    try:
        state = state_builder.build_state_full()
        return {
            "board": state.board,
            "bench": state.bench,
            "timestamp": state.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/regions")
async def get_regions():
    """Get all ROI region definitions"""
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    regions = {}
    for name, region in state_builder.capture.regions.get_all_regions().items():
        regions[name] = {
            "x": region.x,
            "y": region.y,
            "width": region.width,
            "height": region.height
        }
    return regions


@app.post("/calibrate/save")
async def save_calibration_image():
    """Save a debug image showing all regions"""
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    try:
        path = state_builder.capture.draw_regions_debug()
        return {"status": "saved", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === WebSocket Endpoints ===

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/state")
async def websocket_state(websocket: WebSocket, fps: int = 5, mode: str = "fast"):
    """
    WebSocket endpoint for real-time state streaming
    
    Args:
        fps: Updates per second (1-30)
        mode: "fast" or "full"
    """
    await manager.connect(websocket)
    
    fps = max(1, min(30, fps))
    interval = 1.0 / fps
    
    try:
        while True:
            if state_builder:
                try:
                    if mode == "full":
                        state = state_builder.build_state_full()
                    else:
                        state = state_builder.build_state_fast()
                    
                    await websocket.send_text(state.to_json())
                except Exception as e:
                    await websocket.send_text(json.dumps({"error": str(e)}))
            
            await asyncio.sleep(interval)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/changes")
async def websocket_changes(websocket: WebSocket):
    """
    WebSocket endpoint that only sends state changes
    More efficient for tracking game events
    """
    await manager.connect(websocket)
    
    last_state = None
    
    try:
        while True:
            if state_builder:
                try:
                    current_state = state_builder.build_state_fast()
                    
                    if last_state:
                        changes = state_builder.get_state_changes(last_state, current_state)
                        if changes:
                            await websocket.send_text(json.dumps({
                                "type": "change",
                                "timestamp": current_state.timestamp,
                                "changes": changes
                            }))
                    
                    last_state = current_state
                except Exception as e:
                    await websocket.send_text(json.dumps({"error": str(e)}))
            
            await asyncio.sleep(0.2)  # 5 Hz for change detection
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the API server"""
    print(f"Starting TFT State Extraction API on http://{host}:{port}")
    print(f"WebSocket: ws://{host}:{port}/ws/state")
    print(f"API Docs: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
