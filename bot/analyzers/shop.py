"""
Shop Analyzer - Evaluates shop value and purchase decisions

Analyzes:
- Champions in shop
- Upgrade opportunities from shop
- Value of each purchase
- Buy/pass recommendations
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
from pathlib import Path


@dataclass
class ShopItem:
    """A champion in the shop"""
    slot: int
    champion: str
    cost: int
    value_score: float
    reason: str
    priority: str  # "must_buy", "high", "medium", "low", "skip"


@dataclass
class ShopAnalysis:
    """Result of shop analysis"""
    items: List[ShopItem]
    best_buy: Optional[ShopItem]
    total_cost_for_recommended: int
    reasoning: str


class ShopAnalyzer:
    """Analyzes shop and recommends purchases"""
    
    def __init__(self, tft_data_path: str = None):
        self.champion_data: Dict[str, Any] = {}
        
        if tft_data_path is None:
            tft_data_path = Path(__file__).parent.parent.parent / "tft_data.json"
        
        self._load_data(tft_data_path)
    
    def _load_data(self, path: str):
        """Load champion data"""
        path = Path(path)
        if not path.exists():
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            for champ in data.get('champions', []):
                name = champ.get('name', champ.get('apiName', ''))
                cost = champ.get('cost', 1)
                traits = champ.get('traits', [])
                if name:
                    self.champion_data[name.lower()] = {
                        'cost': cost,
                        'traits': traits
                    }
        except Exception as e:
            print(f"Could not load TFT data: {e}")
    
    def analyze(self, game_state: Dict[str, Any]) -> ShopAnalysis:
        """
        Analyze shop and recommend purchases
        
        Args:
            game_state: Full game state dict
            
        Returns:
            ShopAnalysis with purchase recommendations
        """
        shop = game_state.get('shop', [])
        board = game_state.get('board', [])
        bench = game_state.get('bench', [])
        player = game_state.get('player', {})
        traits = game_state.get('traits', [])
        
        gold = player.get('gold', 0)
        
        # Count owned champions
        owned_counts: Dict[str, Dict] = {}
        for unit in board + bench:
            name = unit.get('champion', '').lower()
            star = unit.get('star', 1)
            if not name:
                continue
            
            if name not in owned_counts:
                owned_counts[name] = {'count': 0, 'max_star': 0}
            
            # Count equivalent 1-stars
            if star == 1:
                owned_counts[name]['count'] += 1
            elif star == 2:
                owned_counts[name]['count'] += 3
            elif star == 3:
                owned_counts[name]['count'] += 9
            
            owned_counts[name]['max_star'] = max(owned_counts[name]['max_star'], star)
        
        # Get active trait names
        active_trait_names = set(t.get('name', '').lower() for t in traits)
        
        # Analyze each shop slot
        shop_items: List[ShopItem] = []
        
        for slot_idx, shop_unit in enumerate(shop):
            champ_name = shop_unit.get('champion', '').lower()
            cost = shop_unit.get('cost', 1)
            
            if not champ_name:
                continue
            
            # Calculate value score
            value_score = 0
            reasons = []
            priority = "low"
            
            # Check if it completes an upgrade
            owned = owned_counts.get(champ_name, {'count': 0, 'max_star': 0})
            count_after = owned['count'] + 1
            
            if owned['count'] >= 2 and owned['count'] < 3:
                # Completes 2-star!
                value_score += 100
                reasons.append("Completes 2★ upgrade!")
                priority = "must_buy"
            elif owned['count'] >= 8:
                # Completes 3-star!
                value_score += 200
                reasons.append("Completes 3★ upgrade!")
                priority = "must_buy"
            elif owned['count'] >= 1:
                # Building toward upgrade
                value_score += 30
                reasons.append(f"Have {owned['count']}/3 for 2★")
                priority = "medium"
            
            # Check if traits match current comp
            champ_traits = self.champion_data.get(champ_name, {}).get('traits', [])
            matching_traits = [t for t in champ_traits if t.lower() in active_trait_names]
            if matching_traits:
                value_score += 15 * len(matching_traits)
                reasons.append(f"Fits comp: {', '.join(matching_traits)}")
                if priority == "low":
                    priority = "medium"
            
            # Penalize if can't afford
            if cost > gold:
                value_score -= 50
                reasons.append("Can't afford")
                priority = "skip"
            
            # Default reason
            if not reasons:
                reasons.append("No immediate value")
                priority = "skip"
            
            shop_items.append(ShopItem(
                slot=slot_idx,
                champion=champ_name.title(),
                cost=cost,
                value_score=value_score,
                reason=" | ".join(reasons),
                priority=priority
            ))
        
        # Sort by value
        shop_items.sort(key=lambda x: -x.value_score)
        
        # Find best buy
        best_buy = None
        recommended_cost = 0
        
        for item in shop_items:
            if item.priority in ["must_buy", "high", "medium"] and item.cost <= gold:
                if best_buy is None or item.value_score > best_buy.value_score:
                    best_buy = item
        
        # Calculate total cost for all recommended
        for item in shop_items:
            if item.priority in ["must_buy", "high"]:
                recommended_cost += item.cost
        
        # Generate reasoning
        if best_buy:
            if best_buy.priority == "must_buy":
                reasoning = f"BUY {best_buy.champion} in slot {best_buy.slot + 1} - {best_buy.reason}"
            else:
                reasoning = f"Consider {best_buy.champion} ({best_buy.cost}g) - {best_buy.reason}"
        else:
            reasoning = "No valuable purchases in shop"
        
        return ShopAnalysis(
            items=shop_items,
            best_buy=best_buy,
            total_cost_for_recommended=recommended_cost,
            reasoning=reasoning
        )
    
    def should_reroll(self, game_state: Dict[str, Any], economy_status: str) -> tuple[bool, str]:
        """
        Determine if player should reroll
        
        Returns:
            (should_reroll, reason)
        """
        player = game_state.get('player', {})
        gold = player.get('gold', 0)
        
        shop_analysis = self.analyze(game_state)
        
        # Check if current shop has value
        has_value = any(item.priority in ["must_buy", "high"] for item in shop_analysis.items)
        
        if has_value:
            return False, "Current shop has value"
        
        # Check economy status
        if economy_status == "desperate" and gold >= 2:
            return True, "Need to find upgrades to stabilize"
        
        if economy_status == "critical" and gold >= 30:
            return True, "Low HP - roll to find power"
        
        if gold >= 50:
            # Count upgrade opportunities
            upgrade_count = sum(1 for item in shop_analysis.items 
                              if "building toward" in item.reason.lower() or "2★" in item.reason)
            if upgrade_count >= 2:
                return True, "At max interest with upgrade potential"
        
        return False, "Save gold for interest"
