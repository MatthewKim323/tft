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
    Base resolution: 1920x1200 (NATIVE resolution)
    Using macOS screencapture for true native pixel capture
    """
    
    # Base resolution these coordinates are calibrated for (NATIVE)
    base_width: int = 1920
    base_height: int = 1200
    
    # Current screen resolution (NATIVE - detected at runtime)
    screen_width: int = 1920
    screen_height: int = 1200
    
    def __post_init__(self):
        self._calculate_scale()
    
    def _calculate_scale(self):
        self.scale_x = self.screen_width / self.base_width
        self.scale_y = self.screen_height / self.base_height
    
    def set_resolution(self, width: int, height: int):
        """Update for different screen resolution"""
        self.screen_width = width
        self.screen_height = height
        self._calculate_scale()
    
    # === HUD REGIONS (OCR targets) ===
    # Calibrated for TFT Set 14 (2026) at 1920x1200 NATIVE resolution
    # MEASURED FROM ACTUAL SCREENSHOT
    
    @property
    def gold(self) -> Region:
        """Gold amount display - shows "7" in screenshot, next to gold icon"""
        # Located in the bottom center HUD area
        return Region(680, 890, 50, 40, "gold").scale(self.scale_x, self.scale_y)
    
    @property
    def health(self) -> Region:
        """Player health display - the yellow HP bar under player name"""
        # Shows HP bar for "bigwinner445" 
        return Region(740, 440, 100, 25, "health").scale(self.scale_x, self.scale_y)
    
    @property
    def level(self) -> Region:
        """Player level display - shows 'Lvl. 3' in bottom left"""
        return Region(145, 890, 60, 35, "level").scale(self.scale_x, self.scale_y)
    
    @property
    def xp_bar(self) -> Region:
        """XP progress bar region - shows '0/6' next to level"""
        return Region(205, 890, 80, 35, "xp_bar").scale(self.scale_x, self.scale_y)
    
    @property
    def stage(self) -> Region:
        """Current stage display (e.g., 1-4) - top center"""
        return Region(560, 8, 120, 50, "stage").scale(self.scale_x, self.scale_y)
    
    @property
    def round_timer(self) -> Region:
        """Round timer - shows '6' in top right area"""
        return Region(780, 8, 60, 50, "timer").scale(self.scale_x, self.scale_y)
    
    # === GAME BOARD REGIONS (YOLO targets) ===
    # Coordinates for 1920x1200 native resolution - FINE-TUNED
    
    @property
    def board(self) -> Region:
        """Main hex board area - JUST champions on the battlefield"""
        # Tighter crop: less right side, less bottom (no bench champions)
        return Region(320, 170, 720, 370, "board").scale(self.scale_x, self.scale_y)
    
    @property
    def bench(self) -> Region:
        """Bench area - where benched champions stand"""
        # Moved UP and LEFT to capture champions waiting on bench
        return Region(180, 480, 900, 100, "bench").scale(self.scale_x, self.scale_y)
    
    @property
    def shop(self) -> Region:
        """Shop area (5 champion cards) - the buyable champions"""
        # Made taller to show more of the champion cards
        return Region(270, 680, 900, 130, "shop").scale(self.scale_x, self.scale_y)
    
    @property
    def item_inventory(self) -> Region:
        """Left side panel - JUST traits and items"""
        # Less right, less bottom - focused on the actual items/traits
        return Region(0, 200, 145, 400, "items").scale(self.scale_x, self.scale_y)
    
    @property
    def augment_display(self) -> Region:
        """Augment icons (top left area)"""
        return Region(20, 200, 130, 180, "augments").scale(self.scale_x, self.scale_y)
    
    @property
    def trait_panel(self) -> Region:
        """Active traits panel (left side) - shows Defender, Demacia, etc."""
        return Region(50, 220, 140, 380, "traits").scale(self.scale_x, self.scale_y)
    
    # === OPPONENT INFO ===
    
    @property
    def opponent_portraits(self) -> Region:
        """All player health bars (right side) - shows all 8 players"""
        return Region(1220, 150, 200, 520, "opponents").scale(self.scale_x, self.scale_y)
    
    # === FULL SCREEN ===
    
    @property
    def full_screen(self) -> Region:
        """Full game screen"""
        return Region(0, 0, self.screen_width, self.screen_height, "full")
    
    def get_all_regions(self) -> Dict[str, Region]:
        """Return all regions as a dictionary"""
        return {
            "gold": self.gold,
            "health": self.health,
            "level": self.level,
            "xp_bar": self.xp_bar,
            "stage": self.stage,
            "round_timer": self.round_timer,
            "board": self.board,
            "bench": self.bench,
            "shop": self.shop,
            "item_inventory": self.item_inventory,
            "augment_display": self.augment_display,
            "trait_panel": self.trait_panel,
            "opponent_portraits": self.opponent_portraits,
        }
    
    def get_ocr_regions(self) -> Dict[str, Region]:
        """Return regions that need OCR processing"""
        return {
            "gold": self.gold,
            "health": self.health,
            "level": self.level,
            "stage": self.stage,
        }
    
    def get_yolo_regions(self) -> Dict[str, Region]:
        """Return regions that need YOLO detection"""
        return {
            "board": self.board,
            "bench": self.bench,
            "shop": self.shop,
            "item_inventory": self.item_inventory,
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


# Hex grid positions for board slots (base 1920x1200 NATIVE)
# Each position is (row, col) where row 0 is closest to player
# These are center coordinates of each hex - measured from actual screenshot
BOARD_HEXES = {
    # Row 0 (closest to player, your side) - 7 hexes, y ≈ 580
    (0, 0): (350, 580), (0, 1): (460, 580), (0, 2): (570, 580),
    (0, 3): (680, 580), (0, 4): (790, 580), (0, 5): (900, 580), (0, 6): (1010, 580),
    
    # Row 1 - 7 hexes (offset for hex grid), y ≈ 480
    (1, 0): (405, 480), (1, 1): (515, 480), (1, 2): (625, 480),
    (1, 3): (735, 480), (1, 4): (845, 480), (1, 5): (955, 480), (1, 6): (1065, 480),
    
    # Row 2 - 7 hexes, y ≈ 380
    (2, 0): (350, 380), (2, 1): (460, 380), (2, 2): (570, 380),
    (2, 3): (680, 380), (2, 4): (790, 380), (2, 5): (900, 380), (2, 6): (1010, 380),
    
    # Row 3 (enemy side) - 7 hexes (offset), y ≈ 280
    (3, 0): (405, 280), (3, 1): (515, 280), (3, 2): (625, 280),
    (3, 3): (735, 280), (3, 4): (845, 280), (3, 5): (955, 280), (3, 6): (1065, 280),
}

# Bench slot positions (9 slots between board and shop)
BENCH_SLOTS = {
    0: (320, 720), 1: (420, 720), 2: (520, 720), 3: (620, 720), 4: (720, 720),
    5: (820, 720), 6: (920, 720), 7: (1020, 720), 8: (1120, 720),
}

# Shop slot positions (5 champion cards at bottom)
SHOP_SLOTS = {
    0: (390, 990), 1: (550, 990), 2: (710, 990), 3: (870, 990), 4: (1030, 990),
}
