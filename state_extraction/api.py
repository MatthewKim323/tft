"""
FastAPI Server for TFT State Extraction
Provides REST API and WebSocket for real-time state streaming

Supports two modes:
  - MANUAL: Only analyze when /analyze is called
  - AUTO: Continuous real-time analysis
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .state_builder import StateBuilder, GameState
from .config import Config

# Import coach for decision streaming
try:
    from bot.coach import TFTCoach
    COACH_AVAILABLE = True
except ImportError:
    COACH_AVAILABLE = False
    print("Warning: bot.coach not available")


# Global state
state_builder: Optional[StateBuilder] = None
coach: Optional['TFTCoach'] = None
config = Config()

# Mode: "manual" or "auto"
MODE = os.environ.get('TFT_MODE', 'manual')

# Latest analysis result (for manual mode)
latest_analysis: Optional[Dict[str, Any]] = None
analysis_event = asyncio.Event()  # Signals new analysis available


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage state builder lifecycle"""
    global state_builder, coach, MODE
    print("Initializing State Extraction API...")
    print(f"Mode: {'📸 MANUAL' if MODE == 'manual' else '🤖 AUTO'}")
    
    state_builder = StateBuilder(config)
    
    # Initialize AI Coach
    if COACH_AVAILABLE:
        coach = TFTCoach()
        print("AI Coach initialized ✓")
    else:
        print("AI Coach not available (import error)")
    
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


@app.get("/status")
async def get_status():
    """
    Get detailed status of extraction capabilities
    
    Shows which extraction methods are available and ready.
    """
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    return {
        "status": "online",
        "mode": MODE,
        "extraction_methods": {
            "ocr": {
                "available": True,
                "description": "Text extraction for HUD (gold, HP, level, stage)"
            },
            "template_matching": {
                "available": state_builder._templates_loaded,
                "description": "Icon matching for shop champions and items"
            },
            "star_detection": {
                "available": True,
                "description": "Color-based star level detection (1/2/3 stars)"
            },
            "yolo": {
                "available": state_builder._yolo_available,
                "model_path": state_builder.config.yolo_model_path,
                "description": "Object detection for board/bench champions"
            }
        },
        "coach_available": COACH_AVAILABLE and coach is not None,
        "latest_analysis": latest_analysis is not None
    }


@app.post("/analyze")
async def trigger_analysis(save_screenshot: bool = True):
    """
    Trigger a manual analysis (for manual mode)
    
    Captures screenshot, runs coach analysis, and broadcasts to WebSocket.
    
    Args:
        save_screenshot: Whether to save the screenshot to disk
    """
    global latest_analysis
    
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    if not COACH_AVAILABLE or not coach:
        raise HTTPException(status_code=503, detail="Coach not available")
    
    try:
        # Capture and analyze
        state = state_builder.build_state_full()
        state_dict = state.to_dict()
        
        # Run coach
        decision = coach.analyze(state_dict)
        
        # Save screenshot if requested
        screenshot_path = None
        if save_screenshot:
            try:
                import cv2
                from pathlib import Path
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                screenshot_dir = Path("screenshots/manual")
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                
                frame = state_builder.capture.capture_full_screen()
                if frame:
                    screenshot_path = str(screenshot_dir / f"{timestamp}_full.png")
                    cv2.imwrite(screenshot_path, frame.image)
                    
                    # Also save state JSON
                    state_json_path = screenshot_dir / f"{timestamp}_state.json"
                    with open(state_json_path, 'w') as f:
                        json.dump(state_dict, f, indent=2, default=str)
            except Exception as e:
                print(f"Screenshot save error: {e}")
        
        # Build result
        result = {
            "timestamp": datetime.now().isoformat(),
            "type": "manual_analysis",
            "game_state": state_dict,
            "decision": decision.to_dict(),
            "screenshot_path": screenshot_path
        }
        
        # Store for WebSocket broadcast
        latest_analysis = result
        analysis_event.set()  # Signal WebSocket clients
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/latest")
async def get_latest_analysis():
    """Get the most recent analysis result (manual mode)"""
    if latest_analysis is None:
        raise HTTPException(status_code=404, detail="No analysis yet. Call POST /analyze first.")
    return latest_analysis


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


@app.get("/test/templates")
async def test_template_matching():
    """
    Test template matching functionality
    
    Downloads templates if needed and tests shop detection.
    """
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    try:
        # Ensure templates are loaded
        state_builder._ensure_templates_loaded()
        
        # Get counts
        champion_count = len(state_builder.template_matcher.champion_templates)
        item_count = len(state_builder.template_matcher.item_templates)
        
        # Try to match shop
        shop_frame = state_builder.capture.capture_region("shop")
        shop_results = []
        
        if shop_frame:
            matches = state_builder.template_matcher.match_shop(shop_frame.image)
            shop_results = [
                {"slot": i, "champion": m.name, "confidence": round(m.confidence, 3)}
                for i, m in enumerate(matches)
            ]
        
        return {
            "status": "ok",
            "templates_loaded": {
                "champions": champion_count,
                "items": item_count
            },
            "shop_detection": shop_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === AI Coach Endpoints ===

@app.get("/decision")
async def get_decision():
    """
    Get a single AI coach decision based on current game state
    
    Returns the coach's recommendation with reasoning
    """
    if not state_builder:
        raise HTTPException(status_code=503, detail="State builder not initialized")
    
    if not COACH_AVAILABLE or not coach:
        raise HTTPException(status_code=503, detail="AI Coach not available")
    
    try:
        # Get current game state
        state = state_builder.build_state_fast()
        
        # Get coach decision
        decision = coach.analyze(state.to_dict())
        
        return decision.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decision/history")
async def get_decision_history(limit: int = 10):
    """Get recent decision history"""
    if not COACH_AVAILABLE or not coach:
        raise HTTPException(status_code=503, detail="AI Coach not available")
    
    return {"decisions": coach.get_history(limit)}


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
    
    In MANUAL mode: Returns last analysis or placeholder (no continuous capture)
    In AUTO mode: Continuous real-time capture
    
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
                    # In manual mode, return last analysis or placeholder
                    if MODE == "manual":
                        if latest_analysis and "game_state" in latest_analysis:
                            await websocket.send_text(json.dumps(latest_analysis["game_state"]))
                        else:
                            await websocket.send_text(json.dumps({
                                "mode": "manual",
                                "message": "Press hotkey to analyze",
                                "player": {"health": "--", "gold": "--", "level": "--"},
                                "stage": {"current": "--"}
                            }))
                    else:
                        # Auto mode: continuous capture
                        if mode == "full":
                            state = state_builder.build_state_full()
                        else:
                            state = state_builder.build_state_fast()
                        await websocket.send_text(state.to_json())
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    try:
                        await websocket.send_text(json.dumps({"error": str(e)}))
                    except:
                        break
            
            await asyncio.sleep(interval)
    
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        try:
            manager.disconnect(websocket)
        except:
            pass


@app.websocket("/ws/changes")
async def websocket_changes(websocket: WebSocket):
    """
    WebSocket endpoint that only sends state changes
    
    In MANUAL mode: No continuous capture, just keeps connection alive
    In AUTO mode: Continuous change detection
    """
    await manager.connect(websocket)
    
    last_state = None
    
    try:
        while True:
            # In manual mode, just keep connection alive without capturing
            if MODE == "manual":
                await asyncio.sleep(1.0)
                continue
            
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
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    try:
                        await websocket.send_text(json.dumps({"error": str(e)}))
                    except:
                        break
            
            await asyncio.sleep(0.2)  # 5 Hz for change detection
    
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        try:
            manager.disconnect(websocket)
        except:
            pass


@app.websocket("/ws/decisions")
async def websocket_decisions(websocket: WebSocket, fps: int = 2):
    """
    WebSocket endpoint for AI Coach decision streaming
    
    Behavior depends on mode:
    - MANUAL: Waits for /analyze to be called, then sends result
    - AUTO: Continuous real-time analysis
    
    Args:
        fps: Decision updates per second (1-5, default 2) - only used in auto mode
    """
    global analysis_event
    
    await manager.connect(websocket)
    
    # Send initial status
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "mode": MODE,
            "message": f"Connected in {MODE} mode"
        }))
    except:
        return
    
    if MODE == "manual":
        # MANUAL MODE: Wait for analysis triggers
        try:
            while True:
                # Wait for analysis event or timeout for heartbeat
                try:
                    await asyncio.wait_for(analysis_event.wait(), timeout=5.0)
                    analysis_event.clear()
                    
                    # Send the latest analysis
                    if latest_analysis:
                        await websocket.send_text(json.dumps({
                            "type": "decision",
                            **latest_analysis.get("decision", {})
                        }))
                except asyncio.TimeoutError:
                    # Send heartbeat
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "heartbeat",
                            "mode": "manual",
                            "timestamp": datetime.now().isoformat()
                        }))
                    except:
                        break
                except WebSocketDisconnect:
                    break
        
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            try:
                manager.disconnect(websocket)
            except:
                pass
    
    else:
        # AUTO MODE: Continuous analysis
        fps = max(1, min(5, fps))
        interval = 1.0 / fps
        last_decision_hash = None
        
        try:
            while True:
                if state_builder and COACH_AVAILABLE and coach:
                    try:
                        # Get current game state
                        current_state = state_builder.build_state_fast()
                        
                        # Get coach decision
                        decision = coach.analyze(current_state.to_dict())
                        
                        # Only send if decision changed (avoid spam)
                        decision_dict = decision.to_dict()
                        decision_hash = f"{decision_dict['decision']['action']}_{decision_dict['decision']['target']}"
                        
                        if decision_hash != last_decision_hash:
                            await websocket.send_text(json.dumps({
                                "type": "decision",
                                **decision_dict
                            }))
                            last_decision_hash = decision_hash
                        else:
                            # Send heartbeat with same decision
                            await websocket.send_text(json.dumps({
                                "type": "heartbeat",
                                "timestamp": decision_dict["timestamp"]
                            }))
                        
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "error": str(e)
                            }))
                        except:
                            break
                else:
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "error": "Coach or state builder not available"
                        }))
                    except:
                        break
                
                await asyncio.sleep(interval)
        
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            try:
                manager.disconnect(websocket)
            except:
                pass


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the API server"""
    print(f"Starting TFT State Extraction API on http://{host}:{port}")
    print(f"WebSocket: ws://{host}:{port}/ws/state")
    print(f"API Docs: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
