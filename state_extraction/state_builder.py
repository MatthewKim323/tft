"""
State Builder Module for TFT State Extraction
Combines YOLO detections and OCR results into a unified game state JSON
"""

import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .capture import ScreenCapture, CapturedFrame
from .ocr import OCRExtractor
from .detector import YOLODetector, BoardUnit
from .config import Config


@dataclass
class GameState:
    """Complete TFT game state"""
    timestamp: str
    stage: Dict[str, str]
    player: Dict[str, Any]
    board: List[Dict[str, Any]]
    bench: List[Dict[str, Any]]
    shop: List[Dict[str, Any]]
    items: List[str]
    augments: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())
    
    @classmethod
    def empty(cls) -> 'GameState':
        """Return an empty game state"""
        return cls(
            timestamp=datetime.now().isoformat(),
            stage={"current": "1-1", "phase": "planning"},
            player={
                "health": 100,
                "gold": 0,
                "level": 1,
                "xp": {"current": 0, "required": 2}
            },
            board=[],
            bench=[],
            shop=[],
            items=[],
            augments=[]
        )


class StateBuilder:
    """
    Builds complete game state by combining:
    - OCR for HUD values (gold, HP, level, stage)
    - YOLO for unit/item detection (board, bench, shop, items)
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.capture = ScreenCapture(self.config)
        self.ocr = OCRExtractor(self.config)
        self.detector = YOLODetector(self.config)
        
        # Caching for performance
        self._last_state = None
        self._last_capture_time = 0
    
    def build_state(self, use_yolo: bool = True, use_ocr: bool = True) -> GameState:
        """
        Build complete game state from current screen
        
        Args:
            use_yolo: Whether to use YOLO for unit detection
            use_ocr: Whether to use OCR for text extraction
        
        Returns:
            GameState object with all extracted information
        """
        timestamp = datetime.now().isoformat()
        
        # Initialize empty state
        state = GameState.empty()
        state.timestamp = timestamp
        
        # Extract OCR values (gold, HP, level, stage)
        if use_ocr:
            ocr_frames = self.capture.capture_ocr_regions()
            hud_data = self.ocr.extract_all_hud(ocr_frames)
            
            state.stage = hud_data["stage"]
            state.player = {
                "health": hud_data["health"],
                "gold": hud_data["gold"],
                "level": hud_data["level"],
                "xp": hud_data.get("xp", {"current": 0, "required": 4})
            }
        
        # Extract YOLO detections (board, bench, shop, items)
        if use_yolo:
            yolo_frames = self.capture.capture_yolo_regions()
            
            # Board units
            if "board" in yolo_frames:
                board_units = self.detector.detect_board(yolo_frames["board"])
                state.board = [self._unit_to_dict(u) for u in board_units]
            
            # Bench units
            if "bench" in yolo_frames:
                bench_units = self.detector.detect_bench(yolo_frames["bench"])
                state.bench = [self._unit_to_dict(u, is_bench=True) for u in bench_units]
            
            # Shop
            if "shop" in yolo_frames:
                state.shop = self.detector.detect_shop(yolo_frames["shop"])
            
            # Items
            if "item_inventory" in yolo_frames:
                state.items = self.detector.detect_items(yolo_frames["item_inventory"])
        
        self._last_state = state
        self._last_capture_time = time.time()
        
        return state
    
    def build_state_fast(self) -> GameState:
        """
        Fast state extraction - OCR only, skip YOLO
        Useful for high-frequency updates of numeric values
        """
        return self.build_state(use_yolo=False, use_ocr=True)
    
    def build_state_full(self) -> GameState:
        """
        Full state extraction - both OCR and YOLO
        More accurate but slower
        """
        return self.build_state(use_yolo=True, use_ocr=True)
    
    def _unit_to_dict(self, unit: BoardUnit, is_bench: bool = False) -> Dict[str, Any]:
        """Convert BoardUnit to dictionary format"""
        if is_bench:
            return {
                "slot": unit.position[0] if unit.position else 0,
                "champion": unit.champion,
                "star": unit.star_level,
                "items": unit.items
            }
        else:
            return {
                "slot": list(unit.position) if unit.position else [0, 0],
                "champion": unit.champion,
                "star": unit.star_level,
                "items": unit.items
            }
    
    def get_state_changes(self, old_state: GameState, new_state: GameState) -> Dict[str, Any]:
        """
        Compare two states and return what changed
        Useful for logging and decision triggers
        """
        changes = {}
        
        # Check gold change
        old_gold = old_state.player.get("gold", 0)
        new_gold = new_state.player.get("gold", 0)
        if old_gold != new_gold:
            changes["gold"] = {"from": old_gold, "to": new_gold, "diff": new_gold - old_gold}
        
        # Check health change
        old_hp = old_state.player.get("health", 100)
        new_hp = new_state.player.get("health", 100)
        if old_hp != new_hp:
            changes["health"] = {"from": old_hp, "to": new_hp, "diff": new_hp - old_hp}
        
        # Check level change
        old_level = old_state.player.get("level", 1)
        new_level = new_state.player.get("level", 1)
        if old_level != new_level:
            changes["level"] = {"from": old_level, "to": new_level}
        
        # Check stage change
        if old_state.stage.get("current") != new_state.stage.get("current"):
            changes["stage"] = {"from": old_state.stage, "to": new_state.stage}
        
        # Check board changes
        old_board_champs = {u.get("champion") for u in old_state.board}
        new_board_champs = {u.get("champion") for u in new_state.board}
        
        added = new_board_champs - old_board_champs
        removed = old_board_champs - new_board_champs
        
        if added or removed:
            changes["board"] = {"added": list(added), "removed": list(removed)}
        
        return changes
    
    def close(self):
        """Clean up resources"""
        self.capture.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_state_builder():
    """Test state building"""
    print("Testing State Builder...")
    
    with StateBuilder() as builder:
        # Test OCR-only state
        print("\n--- Fast State (OCR only) ---")
        state = builder.build_state_fast()
        print(state.to_json(pretty=True))
        
        # Test full state (if YOLO model available)
        print("\n--- Full State (OCR + YOLO) ---")
        try:
            state = builder.build_state_full()
            print(state.to_json(pretty=True))
        except Exception as e:
            print(f"Full state extraction failed: {e}")
            print("(YOLO model may not be trained yet)")


if __name__ == "__main__":
    test_state_builder()
