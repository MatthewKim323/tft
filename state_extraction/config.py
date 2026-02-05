"""
Configuration for TFT State Extraction
Screen regions, thresholds, and settings
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, List
import json
import os


@dataclass
class Region:
    """Defines a rectangular region on screen"""
    x: int
    y: int
    width: int
    height: int
    name: str = ""
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Return (left, top, right, bottom) format"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    @property
    def mss_format(self) -> Dict:
        """Return format for mss screen capture"""
        return {
            "left": self.x,
            "top": self.y,
            "width": self.width,
            "height": self.height
        }
    
    def scale(self, scale_x: float, scale_y: float) -> 'Region':
        """Scale region for different resolutions"""
        return Region(
            x=int(self.x * scale_x),
            y=int(self.y * scale_y),
            width=int(self.width * scale_x),
            height=int(self.height * scale_y),
            name=self.name
        )


@dataclass
class GameRegions:
    """
    All TFT game screen regions
    Base resolution: 2560x1664 (macOS Retina)
    Using macOS screencapture for true native pixel capture
    
    Loads from roi_calibration.json if available, otherwise uses defaults.
    """
    
    # Base resolution these coordinates are calibrated for (NATIVE)
    base_width: int = 2560
    base_height: int = 1664
    
    # Current screen resolution (NATIVE - detected at runtime)
    screen_width: int = 2560
    screen_height: int = 1664
    
    # Calibration data (loaded from roi_calibration.json)
    _calibration: dict = field(default_factory=dict, repr=False)
    _calibration_loaded: bool = False
    
    def __post_init__(self):
        self._load_calibration()
        self._calculate_scale()
    
    def _load_calibration(self):
        """Load calibration from roi_calibration.json if it exists"""
        # Look for calibration file in project root
        calibration_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'roi_calibration.json'),
            'roi_calibration.json',
        ]
        
        for path in calibration_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        self._calibration = json.load(f)
                    self._calibration_loaded = True
                    print(f"✓ Loaded ROI calibration from {os.path.basename(path)}")
                    return
                except Exception as e:
                    print(f"⚠ Error loading calibration: {e}")
        
        # No calibration file found - use defaults
        print("⚠ No roi_calibration.json found - using default regions")
    
    def _calculate_scale(self):
        self.scale_x = self.screen_width / self.base_width
        self.scale_y = self.screen_height / self.base_height
    
    def set_resolution(self, width: int, height: int):
        """Update for different screen resolution"""
        self.screen_width = width
        self.screen_height = height
        self._calculate_scale()
    
    def _get_calibrated_region(self, name: str, default: Region) -> Region:
        """Get region from calibration if available, otherwise use default"""
        if self._calibration_loaded and name in self._calibration:
            cal = self._calibration[name]
            return Region(
                x=cal.get('x', default.x),
                y=cal.get('y', default.y),
                width=cal.get('width', default.width),
                height=cal.get('height', default.height),
                name=name
            )
        return default.scale(self.scale_x, self.scale_y)
    
    # === ROI REGIONS FOR 2560x1664 (macOS Retina) ===
    # Precise pixel coordinates - no guessing!
    
    @property
    def gold(self) -> Region:
        """Gold amount - extracted from shop region via OCR"""
        return Region(900, 1450, 100, 50, "gold").scale(self.scale_x, self.scale_y)
    
    @property
    def health(self) -> Region:
        """Player health - extracted from player list"""
        return Region(2120, 120, 440, 100, "health").scale(self.scale_x, self.scale_y)
    
    @property
    def level(self) -> Region:
        """Player level - bottom left of shop area"""
        return Region(360, 1450, 150, 50, "level").scale(self.scale_x, self.scale_y)
    
    @property
    def xp_bar(self) -> Region:
        """XP progress bar"""
        return Region(510, 1450, 200, 50, "xp_bar").scale(self.scale_x, self.scale_y)
    
    @property
    def stage(self) -> Region:
        """Stage/round display - part of top HUD"""
        return Region(360, 0, 400, 120, "stage").scale(self.scale_x, self.scale_y)
    
    @property
    def round_timer(self) -> Region:
        """Round timer - part of top HUD"""
        return Region(1800, 0, 320, 120, "timer").scale(self.scale_x, self.scale_y)
    
    # === MAIN ROI REGIONS (for YOLO/CV pipelines) ===
    # Uses calibration from roi_calibration.json if available, otherwise defaults
    
    @property
    def board(self) -> Region:
        """Current Board - main hex board"""
        default = Region(360, 120, 1760, 1040, "board")
        return self._get_calibrated_region("board", default)
    
    @property
    def bench(self) -> Region:
        """Bench Champions - bottom, above shop"""
        default = Region(360, 1120, 1520, 220, "bench")
        return self._get_calibrated_region("bench", default)
    
    @property
    def shop(self) -> Region:
        """Shop - champions, gold, reroll, buy XP"""
        default = Region(360, 1340, 1620, 324, "shop")
        return self._get_calibrated_region("shop", default)
    
    @property
    def item_inventory(self) -> Region:
        """Items - far left item inventory"""
        default = Region(0, 120, 80, 1140, "items")
        return self._get_calibrated_region("items", default)
    
    @property
    def augment_display(self) -> Region:
        """Top HUD - round, stage, streaks, timer, augments"""
        default = Region(360, 0, 1760, 120, "augments")
        return self._get_calibrated_region("top_hud", default)
    
    @property
    def trait_panel(self) -> Region:
        """Traits Panel - just right of items"""
        default = Region(80, 120, 260, 1040, "traits")
        return self._get_calibrated_region("traits", default)
    
    # === OPPONENT INFO ===
    
    @property
    def opponent_portraits(self) -> Region:
        """Player List - all 8 players on the right"""
        default = Region(2120, 120, 440, 1180, "players")
        return self._get_calibrated_region("players", default)
    
    @property
    def top_hud(self) -> Region:
        """Top HUD - round number, stage, streaks, timer, augments"""
        default = Region(360, 0, 1760, 120, "top_hud")
        return self._get_calibrated_region("top_hud", default)
    
    # === FULL SCREEN ===
    
    @property
    def full_screen(self) -> Region:
        """Full game screen"""
        return Region(0, 0, self.screen_width, self.screen_height, "full")
    
    def get_all_regions(self) -> Dict[str, Region]:
        """Return all regions as a dictionary"""
        return {
            "items": self.item_inventory,
            "traits": self.trait_panel,
            "board": self.board,
            "players": self.opponent_portraits,
            "bench": self.bench,
            "shop": self.shop,
            "top_hud": self.top_hud,
        }
    
    def get_7_rois(self) -> Dict[str, Region]:
        """Return the 7 main ROIs for CV/ML pipelines"""
        return {
            "items": self.item_inventory,      # 80x1140 (extended down)
            "traits": self.trait_panel,         # 260x1040
            "board": self.board,                # 1760x1040
            "players": self.opponent_portraits, # 440x1180
            "bench": self.bench,                # 1520x220 (pushed up)
            "shop": self.shop,                  # 1620x324 (expanded up+right)
            "top_hud": self.top_hud,            # 1760x120
        }
    
    def get_ocr_regions(self) -> Dict[str, Region]:
        """Return regions that need OCR processing"""
        return {
            "shop": self.shop,        # gold, level, xp
            "players": self.opponent_portraits,  # player names, HP
            "top_hud": self.top_hud,  # stage, timer
            "traits": self.trait_panel,
        }
    
    def get_yolo_regions(self) -> Dict[str, Region]:
        """Return regions that need YOLO detection"""
        return {
            "board": self.board,
            "bench": self.bench,
            "shop": self.shop,
            "items": self.item_inventory,
        }


@dataclass
class Config:
    """Global configuration settings"""
    
    # Capture settings
    capture_fps: int = 10
    capture_format: str = "BGR"
    
    # OCR settings
    ocr_lang: List[str] = field(default_factory=lambda: ['en'])
    ocr_confidence_threshold: float = 0.7
    
    # YOLO settings
    yolo_model_path: str = "models/tft_yolo.pt"
    yolo_confidence_threshold: float = 0.5
    yolo_iou_threshold: float = 0.45
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    websocket_path: str = "/ws/state"
    
    # Debug settings
    debug_mode: bool = True
    save_debug_frames: bool = False
    debug_output_dir: str = "debug_frames"
    
    # Game data
    tft_data_path: str = "tft_data.json"
    
    def save(self, path: str = "config.json"):
        """Save config to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
    
    @classmethod
    def load(cls, path: str = "config.json") -> 'Config':
        """Load config from JSON file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        return cls()


# Hex grid positions for board slots (base 2560x1664 Retina)
# Each position is (row, col) where row 0 is closest to player
# Board region starts at x=360, y=120, w=1760, h=1040
# Hex centers are relative to full screen coordinates
BOARD_HEXES = {
    # Row 0 (closest to player, your side) - 7 hexes
    (0, 0): (580, 1000), (0, 1): (750, 1000), (0, 2): (920, 1000),
    (0, 3): (1090, 1000), (0, 4): (1260, 1000), (0, 5): (1430, 1000), (0, 6): (1600, 1000),
    
    # Row 1 - 7 hexes (offset for hex grid)
    (1, 0): (665, 870), (1, 1): (835, 870), (1, 2): (1005, 870),
    (1, 3): (1175, 870), (1, 4): (1345, 870), (1, 5): (1515, 870), (1, 6): (1685, 870),
    
    # Row 2 - 7 hexes
    (2, 0): (580, 740), (2, 1): (750, 740), (2, 2): (920, 740),
    (2, 3): (1090, 740), (2, 4): (1260, 740), (2, 5): (1430, 740), (2, 6): (1600, 740),
    
    # Row 3 (enemy side) - 7 hexes (offset)
    (3, 0): (665, 610), (3, 1): (835, 610), (3, 2): (1005, 610),
    (3, 3): (1175, 610), (3, 4): (1345, 610), (3, 5): (1515, 610), (3, 6): (1685, 610),
}

# Bench slot positions (9 slots) - bench at y=1180, h=220
BENCH_SLOTS = {
    0: (500, 1290), 1: (650, 1290), 2: (800, 1290), 3: (950, 1290), 4: (1100, 1290),
    5: (1250, 1290), 6: (1400, 1290), 7: (1550, 1290), 8: (1700, 1290),
}

# Shop slot positions (5 champion cards) - shop at y=1400, h=264
SHOP_SLOTS = {
    0: (550, 1530), 1: (850, 1530), 2: (1150, 1530), 3: (1450, 1530), 4: (1750, 1530),
}
