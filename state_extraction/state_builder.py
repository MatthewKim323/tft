"""
State Builder Module for TFT State Extraction
Combines YOLO detections, OCR, and Template Matching into a unified game state JSON

Hybrid Extraction Pipeline:
- OCR: Gold, HP, Level, Stage (text extraction)
- Template Matching: Shop champions, items (fast, no training needed)
- Star Detection: Champion star levels (color-based)
- YOLO: Board/bench champions (requires trained model)
"""

import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .capture import ScreenCapture, CapturedFrame
from .ocr import OCRExtractor
from .detector import YOLODetector, BoardUnit
from .template_matcher import TemplateMatcher, StarLevelDetector
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
    Builds complete game state using hybrid extraction:
    
    1. OCR (EasyOCR) - Text extraction for HUD values
       → Gold, HP, Level, Stage, XP
       
    2. Template Matching - Fast icon matching (no training needed)
       → Shop champions (using Riot Data Dragon icons)
       → Item inventory
       
    3. Star Level Detection - Color analysis
       → 1/2/3 star detection by star color
       
    4. YOLO Detection - Object detection (requires trained model)
       → Board champions
       → Bench champions
       → Falls back gracefully if model not trained
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.capture = ScreenCapture(self.config)
        self.ocr = OCRExtractor(self.config)
        self.detector = YOLODetector(self.config)
        
        # Template matching (no training needed - uses Riot icons)
        self.template_matcher = TemplateMatcher()
        self.star_detector = StarLevelDetector()
        self._templates_loaded = False
        
        # Caching for performance
        self._last_state = None
        self._last_capture_time = 0
        
        # Track YOLO availability
        self._yolo_available = self._check_yolo_model()
    
    def _check_yolo_model(self) -> bool:
        """Check if a trained YOLO model exists"""
        import os
        model_path = self.config.yolo_model_path
        if os.path.exists(model_path) and 'yolov8n.pt' not in model_path:
            print(f"✓ Custom YOLO model found: {model_path}")
            return True
        else:
            print("⚠ No trained YOLO model - using template matching for shop/items")
            print("  Train YOLO for board/bench detection: python training/train_yolo.py --action train")
            return False
    
    def _ensure_templates_loaded(self):
        """Lazy-load templates on first use"""
        if not self._templates_loaded:
            print("Loading template icons from Riot Data Dragon...")
            try:
                self.template_matcher.load_templates()
                self._templates_loaded = True
                print("✓ Templates loaded successfully")
            except Exception as e:
                print(f"⚠ Template loading failed: {e}")
                self._templates_loaded = True  # Don't retry
    
    def build_state(self, use_yolo: bool = True, use_ocr: bool = True, 
                    use_templates: bool = True) -> GameState:
        """
        Build complete game state from current screen using hybrid extraction
        
        Args:
            use_yolo: Whether to use YOLO for board/bench detection
            use_ocr: Whether to use OCR for text extraction
            use_templates: Whether to use template matching for shop/items
        
        Returns:
            GameState object with all extracted information
        """
        timestamp = datetime.now().isoformat()
        
        # Initialize empty state
        state = GameState.empty()
        state.timestamp = timestamp
        
        # === LAYER 1: OCR for HUD text (gold, HP, level, stage) ===
        if use_ocr:
            try:
                ocr_frames = self.capture.capture_ocr_regions()
                hud_data = self.ocr.extract_all_hud(ocr_frames)
                
                state.stage = hud_data["stage"]
                state.player = {
                    "health": hud_data["health"],
                    "gold": hud_data["gold"],
                    "level": hud_data["level"],
                    "xp": hud_data.get("xp", {"current": 0, "required": 4})
                }
            except Exception as e:
                print(f"OCR extraction error: {e}")
        
        # === LAYER 2: Template Matching for Shop & Items (fast, no training) ===
        if use_templates:
            self._ensure_templates_loaded()
            
            try:
                # Capture regions for template matching
                shop_frame = self.capture.capture_region("shop")
                items_frame = self.capture.capture_region("items")
                
                # Shop detection via template matching
                if shop_frame and self.template_matcher.champion_templates:
                    shop_matches = self.template_matcher.match_shop(shop_frame.image)
                    state.shop = [
                        {
                            "slot": idx,
                            "champion": match.name,
                            "cost": self._get_champion_cost(match.name),
                            "confidence": round(match.confidence, 2)
                        }
                        for idx, match in enumerate(shop_matches)
                    ]
                
                # Items detection via template matching
                if items_frame and self.template_matcher.item_templates:
                    item_matches = self.template_matcher.match_items(items_frame.image)
                    state.items = [match.name for match in item_matches]
                    
            except Exception as e:
                print(f"Template matching error: {e}")
        
        # === LAYER 3: YOLO for Board & Bench (requires trained model) ===
        if use_yolo and self._yolo_available:
            try:
                yolo_frames = self.capture.capture_yolo_regions()
                
                # Board units with star detection
                if "board" in yolo_frames:
                    board_units = self.detector.detect_board(yolo_frames["board"])
                    state.board = [
                        self._unit_to_dict_with_stars(u, yolo_frames["board"].image) 
                        for u in board_units
                    ]
                
                # Bench units with star detection
                if "bench" in yolo_frames:
                    bench_units = self.detector.detect_bench(yolo_frames["bench"])
                    state.bench = [
                        self._unit_to_dict_with_stars(u, yolo_frames["bench"].image, is_bench=True)
                        for u in bench_units
                    ]
                    
            except Exception as e:
                print(f"YOLO detection error: {e}")
        
        # If no YOLO but templates available, try template matching for bench
        elif use_templates and not self._yolo_available:
            try:
                bench_frame = self.capture.capture_region("bench")
                if bench_frame and self.template_matcher.champion_templates:
                    # Template match bench champions
                    bench_matches = self.template_matcher.match_shop(bench_frame.image, threshold=0.5)
                    state.bench = [
                        {
                            "slot": idx,
                            "champion": match.name,
                            "star": 1,  # Can't detect stars without YOLO crop
                            "items": []
                        }
                        for idx, match in enumerate(bench_matches)
                    ]
            except Exception as e:
                print(f"Bench template matching error: {e}")
        
        self._last_state = state
        self._last_capture_time = time.time()
        
        return state
    
    def _unit_to_dict_with_stars(self, unit: BoardUnit, region_image, 
                                  is_bench: bool = False) -> Dict[str, Any]:
        """Convert BoardUnit to dict with star level detection"""
        # Try to detect star level from the unit's region
        star_level = unit.star_level  # Default from YOLO
        
        try:
            # Crop the unit's region for star detection
            x1, y1, x2, y2 = unit.position if len(unit.position) == 4 else (0, 0, 80, 80)
            if hasattr(unit, 'bbox'):
                x1, y1, x2, y2 = unit.bbox
            
            # Ensure bounds are valid
            h, w = region_image.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 > x1 and y2 > y1:
                unit_crop = region_image[y1:y2, x1:x2]
                star_level = self.star_detector.detect_stars(unit_crop)
        except Exception:
            pass  # Keep default star level
        
        if is_bench:
            return {
                "slot": unit.position[0] if unit.position else 0,
                "champion": unit.champion,
                "star": star_level,
                "items": unit.items
            }
        else:
            return {
                "slot": list(unit.position) if unit.position else [0, 0],
                "champion": unit.champion,
                "star": star_level,
                "items": unit.items
            }
    
    def _get_champion_cost(self, champion_name: str) -> int:
        """Get champion cost from TFT data"""
        import os
        tft_data_path = self.config.tft_data_path
        
        if os.path.exists(tft_data_path):
            try:
                import json
                with open(tft_data_path, 'r') as f:
                    data = json.load(f)
                
                for champ in data.get('champions', []):
                    if champ.get('name', '').lower() == champion_name.lower():
                        return champ.get('cost', 1)
                    if champ.get('apiName', '').lower() == champion_name.lower():
                        return champ.get('cost', 1)
            except:
                pass
        
        return 1  # Default to 1-cost
    
    def build_state_fast(self) -> GameState:
        """
        Fast state extraction - OCR + Template Matching, skip YOLO
        
        Gets:
        - HUD values (gold, HP, level, stage) via OCR
        - Shop champions via template matching
        - Items via template matching
        
        Skips:
        - Board/bench detection (requires YOLO)
        """
        return self.build_state(use_yolo=False, use_ocr=True, use_templates=True)
    
    def build_state_full(self) -> GameState:
        """
        Full state extraction - OCR + Template Matching + YOLO
        
        Gets everything:
        - HUD values via OCR
        - Shop/items via template matching
        - Board/bench via YOLO (if model trained)
        - Star levels via color detection
        
        More accurate but slower.
        """
        return self.build_state(use_yolo=True, use_ocr=True, use_templates=True)
    
    def build_state_ocr_only(self) -> GameState:
        """
        Minimal extraction - OCR only
        
        Fastest option, only gets numeric HUD values.
        Useful for tracking gold/HP changes at high frequency.
        """
        return self.build_state(use_yolo=False, use_ocr=True, use_templates=False)
    
    def _unit_to_dict(self, unit: BoardUnit, is_bench: bool = False) -> Dict[str, Any]:
        """Convert BoardUnit to dictionary format (legacy compatibility)"""
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
    """Test hybrid state extraction"""
    print("=" * 60)
    print("TFT State Builder - Hybrid Extraction Test")
    print("=" * 60)
    
    with StateBuilder() as builder:
        # Test OCR-only state (fastest)
        print("\n" + "-" * 40)
        print("TEST 1: OCR Only (fastest)")
        print("-" * 40)
        try:
            state = builder.build_state_ocr_only()
            print(f"  Stage: {state.stage}")
            print(f"  Gold: {state.player.get('gold')}")
            print(f"  HP: {state.player.get('health')}")
            print(f"  Level: {state.player.get('level')}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test fast state (OCR + Template Matching)
        print("\n" + "-" * 40)
        print("TEST 2: Fast State (OCR + Templates)")
        print("-" * 40)
        try:
            state = builder.build_state_fast()
            print(f"  Stage: {state.stage}")
            print(f"  Gold: {state.player.get('gold')}")
            print(f"  Shop: {len(state.shop)} champions detected")
            for s in state.shop:
                print(f"    - {s.get('champion')} ({s.get('confidence', 0):.0%})")
            print(f"  Items: {len(state.items)} items detected")
            for item in state.items[:5]:  # Show first 5
                print(f"    - {item}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test full state (OCR + Templates + YOLO)
        print("\n" + "-" * 40)
        print("TEST 3: Full State (OCR + Templates + YOLO)")
        print("-" * 40)
        try:
            state = builder.build_state_full()
            print(f"  Board: {len(state.board)} units")
            for u in state.board:
                print(f"    - {u.get('champion')} ★{u.get('star', 1)} @ {u.get('slot')}")
            print(f"  Bench: {len(state.bench)} units")
            for u in state.bench:
                print(f"    - {u.get('champion')} ★{u.get('star', 1)}")
        except Exception as e:
            print(f"  Error: {e}")
            if not builder._yolo_available:
                print("  (YOLO model not trained - train with: python training/train_yolo.py --action train)")
        
        print("\n" + "=" * 60)
        print("Full JSON output:")
        print("=" * 60)
        print(state.to_json(pretty=True))


if __name__ == "__main__":
    test_state_builder()
