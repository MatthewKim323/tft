"""
Template Matching for TFT Shop Champions and Items

Uses Riot Data Dragon icons for matching fixed-position elements.
Much faster than YOLO for known positions like shop slots.
"""

import cv2
import numpy as np
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class TemplateMatch:
    """Result of a template match"""
    name: str
    confidence: float
    position: Tuple[int, int]  # (x, y) of match
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)


class DataDragonClient:
    """Client to download assets from Riot Data Dragon"""
    
    BASE_URL = "https://ddragon.leagueoflegends.com"
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "assets" / "data_dragon"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._version = None
        self._tft_champions = None
        self._tft_items = None
    
    def get_latest_version(self) -> str:
        """Get the latest Data Dragon version"""
        if self._version:
            return self._version
        
        version_file = self.cache_dir / "version.txt"
        
        # Try to fetch latest version
        try:
            response = requests.get(f"{self.BASE_URL}/api/versions.json", timeout=5)
            if response.status_code == 200:
                versions = response.json()
                self._version = versions[0]
                version_file.write_text(self._version)
                return self._version
        except Exception as e:
            print(f"Could not fetch version: {e}")
        
        # Fall back to cached version
        if version_file.exists():
            self._version = version_file.read_text().strip()
            return self._version
        
        # Default fallback
        self._version = "14.23.1"
        return self._version
    
    def get_tft_champions(self) -> Dict:
        """Get TFT champion data"""
        if self._tft_champions:
            return self._tft_champions
        
        version = self.get_latest_version()
        cache_file = self.cache_dir / f"tft_champions_{version}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self._tft_champions = json.load(f)
            return self._tft_champions
        
        try:
            url = f"{self.BASE_URL}/cdn/{version}/data/en_US/tft-champion.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self._tft_champions = response.json()
                with open(cache_file, 'w') as f:
                    json.dump(self._tft_champions, f)
                return self._tft_champions
        except Exception as e:
            print(f"Could not fetch TFT champions: {e}")
        
        return {"data": {}}
    
    def get_tft_items(self) -> Dict:
        """Get TFT item data"""
        if self._tft_items:
            return self._tft_items
        
        version = self.get_latest_version()
        cache_file = self.cache_dir / f"tft_items_{version}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self._tft_items = json.load(f)
            return self._tft_items
        
        try:
            url = f"{self.BASE_URL}/cdn/{version}/data/en_US/tft-item.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self._tft_items = response.json()
                with open(cache_file, 'w') as f:
                    json.dump(self._tft_items, f)
                return self._tft_items
        except Exception as e:
            print(f"Could not fetch TFT items: {e}")
        
        return {"data": {}}
    
    def download_champion_icon(self, champion_id: str) -> Optional[np.ndarray]:
        """Download champion icon and return as numpy array"""
        version = self.get_latest_version()
        
        # Try TFT-specific champion images
        icon_dir = self.cache_dir / "champions"
        icon_dir.mkdir(exist_ok=True)
        icon_path = icon_dir / f"{champion_id}.png"
        
        if icon_path.exists():
            return cv2.imread(str(icon_path))
        
        # Try multiple URL patterns
        urls = [
            f"{self.BASE_URL}/cdn/{version}/img/tft-champion/{champion_id}.png",
            f"{self.BASE_URL}/cdn/{version}/img/tft-champion/{champion_id}.TFT_Set13.png",
            f"{self.BASE_URL}/cdn/{version}/img/champion/{champion_id}.png",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img_array = np.frombuffer(response.content, np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        cv2.imwrite(str(icon_path), img)
                        return img
            except Exception:
                continue
        
        return None
    
    def download_item_icon(self, item_id: str) -> Optional[np.ndarray]:
        """Download item icon and return as numpy array"""
        version = self.get_latest_version()
        
        icon_dir = self.cache_dir / "items"
        icon_dir.mkdir(exist_ok=True)
        icon_path = icon_dir / f"{item_id}.png"
        
        if icon_path.exists():
            return cv2.imread(str(icon_path))
        
        try:
            url = f"{self.BASE_URL}/cdn/{version}/img/tft-item/{item_id}.png"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    cv2.imwrite(str(icon_path), img)
                    return img
        except Exception as e:
            print(f"Could not download item {item_id}: {e}")
        
        return None


class TemplateMatcher:
    """Match TFT shop champions and items using template matching"""
    
    def __init__(self, cache_dir: str = None):
        self.data_dragon = DataDragonClient(cache_dir)
        self.champion_templates: Dict[str, np.ndarray] = {}
        self.item_templates: Dict[str, np.ndarray] = {}
        self._loaded = False
        
        # Shop slot positions (relative to shop region)
        # 5 shop slots evenly spaced
        self.shop_slot_width = 280  # Approximate width per slot
        self.shop_slot_count = 5
        
    def load_templates(self, champion_list: List[str] = None, item_list: List[str] = None):
        """Load champion and item templates from Data Dragon"""
        print("Loading templates from Data Dragon...")
        
        # Get champion data
        if champion_list is None:
            champions = self.data_dragon.get_tft_champions()
            champion_list = list(champions.get("data", {}).keys())[:60]  # Limit to current set
        
        loaded_champs = 0
        for champ_id in champion_list:
            icon = self.data_dragon.download_champion_icon(champ_id)
            if icon is not None:
                # Resize to expected shop icon size
                icon_resized = cv2.resize(icon, (80, 80))
                self.champion_templates[champ_id] = icon_resized
                loaded_champs += 1
        
        print(f"  Loaded {loaded_champs} champion templates")
        
        # Get item data
        if item_list is None:
            items = self.data_dragon.get_tft_items()
            item_list = list(items.get("data", {}).keys())[:50]  # Core items
        
        loaded_items = 0
        for item_id in item_list:
            icon = self.data_dragon.download_item_icon(item_id)
            if icon is not None:
                icon_resized = cv2.resize(icon, (40, 40))
                self.item_templates[item_id] = icon_resized
                loaded_items += 1
        
        print(f"  Loaded {loaded_items} item templates")
        self._loaded = True
    
    def match_shop(self, shop_image: np.ndarray, threshold: float = 0.6) -> List[TemplateMatch]:
        """
        Match champions in shop slots
        
        Args:
            shop_image: Screenshot of the shop region
            threshold: Minimum confidence threshold (0-1)
            
        Returns:
            List of TemplateMatch objects for detected champions
        """
        if not self._loaded:
            self.load_templates()
        
        matches = []
        h, w = shop_image.shape[:2]
        slot_width = w // self.shop_slot_count
        
        for slot_idx in range(self.shop_slot_count):
            # Extract slot region (center portion where champion portrait appears)
            slot_x = slot_idx * slot_width
            slot_region = shop_image[:, slot_x:slot_x + slot_width]
            
            best_match = None
            best_confidence = threshold
            
            for champ_name, template in self.champion_templates.items():
                result = cv2.matchTemplate(slot_region, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    th, tw = template.shape[:2]
                    best_match = TemplateMatch(
                        name=champ_name,
                        confidence=max_val,
                        position=(slot_x + max_loc[0], max_loc[1]),
                        bounding_box=(slot_x + max_loc[0], max_loc[1], tw, th)
                    )
            
            if best_match:
                matches.append(best_match)
        
        return matches
    
    def match_items(self, item_image: np.ndarray, threshold: float = 0.65) -> List[TemplateMatch]:
        """
        Match items in the item inventory region
        
        Args:
            item_image: Screenshot of the items region
            threshold: Minimum confidence threshold (0-1)
            
        Returns:
            List of TemplateMatch objects for detected items
        """
        if not self._loaded:
            self.load_templates()
        
        matches = []
        
        for item_name, template in self.item_templates.items():
            result = cv2.matchTemplate(item_image, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            
            th, tw = template.shape[:2]
            
            for pt in zip(*locations[::-1]):
                # Check if this match overlaps with existing matches
                overlaps = False
                for existing in matches:
                    ex, ey, ew, eh = existing.bounding_box
                    if (abs(pt[0] - ex) < tw * 0.5 and abs(pt[1] - ey) < th * 0.5):
                        # Keep higher confidence match
                        if result[pt[1], pt[0]] > existing.confidence:
                            matches.remove(existing)
                        else:
                            overlaps = True
                        break
                
                if not overlaps:
                    matches.append(TemplateMatch(
                        name=item_name,
                        confidence=result[pt[1], pt[0]],
                        position=pt,
                        bounding_box=(pt[0], pt[1], tw, th)
                    ))
        
        return matches
    
    def match_single_template(self, image: np.ndarray, template: np.ndarray, 
                              threshold: float = 0.7) -> Optional[TemplateMatch]:
        """Match a single template against an image"""
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            th, tw = template.shape[:2]
            return TemplateMatch(
                name="template",
                confidence=max_val,
                position=max_loc,
                bounding_box=(max_loc[0], max_loc[1], tw, th)
            )
        return None
    
    def visualize_matches(self, image: np.ndarray, matches: List[TemplateMatch]) -> np.ndarray:
        """Draw bounding boxes and labels on matches"""
        result = image.copy()
        
        for match in matches:
            x, y, w, h = match.bounding_box
            color = (0, 255, 0)  # Green
            cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
            
            label = f"{match.name} ({match.confidence:.2f})"
            cv2.putText(result, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return result


class StarLevelDetector:
    """Detect champion star levels using color/shape analysis"""
    
    # Star colors in BGR
    STAR_COLORS = {
        1: (255, 255, 255),  # White/gray stars
        2: (0, 215, 255),    # Gold stars
        3: (255, 0, 255),    # Pink/magenta stars
    }
    
    def detect_stars(self, champion_image: np.ndarray) -> int:
        """
        Detect star level from champion portrait
        
        Stars appear above the champion portrait as small colored shapes.
        1-star: 1 gray star
        2-star: 2 gold stars  
        3-star: 3 pink stars
        
        Returns: 1, 2, or 3
        """
        # Look at top portion of image where stars appear
        h, w = champion_image.shape[:2]
        star_region = champion_image[0:int(h * 0.2), :]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(star_region, cv2.COLOR_BGR2HSV)
        
        # Check for 3-star (magenta/pink)
        pink_lower = np.array([140, 100, 100])
        pink_upper = np.array([170, 255, 255])
        pink_mask = cv2.inRange(hsv, pink_lower, pink_upper)
        if cv2.countNonZero(pink_mask) > 50:
            return 3
        
        # Check for 2-star (gold/yellow)
        gold_lower = np.array([20, 150, 150])
        gold_upper = np.array([35, 255, 255])
        gold_mask = cv2.inRange(hsv, gold_lower, gold_upper)
        if cv2.countNonZero(gold_mask) > 30:
            return 2
        
        # Default to 1-star
        return 1


def main():
    """Test template matching"""
    print("=" * 50)
    print("Template Matcher Test")
    print("=" * 50)
    
    matcher = TemplateMatcher()
    
    print("\nFetching Data Dragon version...")
    version = matcher.data_dragon.get_latest_version()
    print(f"  Version: {version}")
    
    print("\nLoading champion data...")
    champions = matcher.data_dragon.get_tft_champions()
    print(f"  Found {len(champions.get('data', {}))} champions")
    
    print("\nLoading item data...")
    items = matcher.data_dragon.get_tft_items()
    print(f"  Found {len(items.get('data', {}))} items")
    
    # Load a subset of templates
    print("\nDownloading sample templates...")
    sample_champs = list(champions.get("data", {}).keys())[:10]
    for champ in sample_champs:
        icon = matcher.data_dragon.download_champion_icon(champ)
        if icon is not None:
            print(f"  ✓ {champ}")
        else:
            print(f"  ✗ {champ}")
    
    print("\n" + "=" * 50)
    print("Template matcher ready for use!")
    print("=" * 50)


if __name__ == "__main__":
    main()
