"""
Board Analyzer - Evaluates board strength and composition

Analyzes:
- Overall board power
- Active synergies/traits
- Upgrade opportunities
- Positioning quality
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json
from pathlib import Path


@dataclass
class BoardAnalysis:
    """Result of board analysis"""
    unit_count: int
    total_power: float
    power_tier: str  # "weak", "medium", "strong", "dominant"
    
    active_traits: List[Dict[str, Any]]
    strongest_trait: Optional[str]
    
    upgrade_opportunities: List[Dict[str, Any]]  # Units close to 2/3 star
    sellable_units: List[str]  # 1-star units with no pair
    
    reasoning: str


class BoardAnalyzer:
    """Analyzes board strength and composition"""
    
    # Champion base power by cost
    COST_POWER = {1: 10, 2: 20, 3: 35, 4: 55, 5: 80}
    
    # Star level multipliers
    STAR_MULT = {1: 1.0, 2: 1.8, 3: 3.0}
    
    # Trait tier values
    TRAIT_TIERS = {
        "bronze": 5,
        "silver": 12,
        "gold": 25,
        "chromatic": 40,
        "prismatic": 50,
    }
    
    # Power thresholds for tiers
    POWER_TIERS = {
        "weak": (0, 150),
        "medium": (150, 300),
        "strong": (300, 500),
        "dominant": (500, float('inf')),
    }
    
    def __init__(self, tft_data_path: str = None):
        self.champion_data: Dict[str, Any] = {}
        
        if tft_data_path is None:
            tft_data_path = Path(__file__).parent.parent.parent / "tft_data.json"
        
        self._load_data(tft_data_path)
    
    def _load_data(self, path: str):
        """Load champion cost data"""
        path = Path(path)
        if not path.exists():
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            for champ in data.get('champions', []):
                name = champ.get('name', champ.get('apiName', ''))
                cost = champ.get('cost', 1)
                if name:
                    self.champion_data[name.lower()] = {'cost': cost}
        except Exception as e:
            print(f"Could not load TFT data: {e}")
    
    def get_unit_power(self, unit: Dict[str, Any]) -> float:
        """Calculate power of a single unit"""
        name = unit.get('champion', '').lower()
        star = unit.get('star', 1)
        items = unit.get('items', [])
        
        # Get cost from data or estimate
        cost = 1
        if name in self.champion_data:
            cost = self.champion_data[name].get('cost', 1)
        
        base_power = self.COST_POWER.get(cost, 10)
        power = base_power * self.STAR_MULT.get(star, 1.0)
        
        # Item bonus (rough estimate)
        power += len(items) * 15
        
        return power
    
    def analyze(self, game_state: Dict[str, Any]) -> BoardAnalysis:
        """
        Analyze board strength and composition
        
        Args:
            game_state: Full game state dict
            
        Returns:
            BoardAnalysis with evaluation and recommendations
        """
        board = game_state.get('board', [])
        bench = game_state.get('bench', [])
        traits = game_state.get('traits', [])
        
        # Calculate total power
        total_power = sum(self.get_unit_power(u) for u in board)
        
        # Determine power tier
        power_tier = "weak"
        for tier, (low, high) in self.POWER_TIERS.items():
            if low <= total_power < high:
                power_tier = tier
                break
        
        # Find strongest trait
        strongest_trait = None
        max_trait_value = 0
        for trait in traits:
            tier = trait.get('tier', '').lower()
            value = self.TRAIT_TIERS.get(tier, 0)
            if value > max_trait_value:
                max_trait_value = value
                strongest_trait = f"{trait.get('name', '')} ({tier})"
        
        # Find upgrade opportunities
        unit_counts: Dict[str, Dict] = {}
        for unit in board + bench:
            name = unit.get('champion', '').lower()
            star = unit.get('star', 1)
            if not name:
                continue
            
            if name not in unit_counts:
                unit_counts[name] = {'1star': 0, '2star': 0, '3star': 0}
            
            unit_counts[name][f'{star}star'] += 1
        
        upgrade_opportunities = []
        sellable_units = []
        
        for name, counts in unit_counts.items():
            # Check for 2-star upgrade potential
            if counts['1star'] >= 2:
                need = 3 - counts['1star']
                upgrade_opportunities.append({
                    'champion': name,
                    'current_count': counts['1star'],
                    'need_for_upgrade': need,
                    'priority': 'high' if need == 1 else 'medium'
                })
            
            # Check for 3-star upgrade potential (already have 2-star)
            if counts['2star'] >= 2:
                upgrade_opportunities.append({
                    'champion': name,
                    'current_count': counts['2star'] * 3,  # Equivalent 1-stars
                    'need_for_upgrade': 3 - counts['2star'],
                    'priority': 'high',
                    'to_3star': True
                })
            
            # Find sellable 1-stars with no pair
            if counts['1star'] == 1 and counts['2star'] == 0 and counts['3star'] == 0:
                sellable_units.append(name)
        
        # Sort upgrades by priority
        upgrade_opportunities.sort(key=lambda x: (x['priority'] != 'high', x['need_for_upgrade']))
        
        # Generate reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Board power: {power_tier} ({total_power:.0f})")
        
        if strongest_trait:
            reasoning_parts.append(f"Strongest trait: {strongest_trait}")
        
        if upgrade_opportunities:
            top_upgrade = upgrade_opportunities[0]
            reasoning_parts.append(f"Close to upgrade: {top_upgrade['champion']} (need {top_upgrade['need_for_upgrade']})")
        
        if sellable_units and len(sellable_units) <= 3:
            reasoning_parts.append(f"Consider selling: {', '.join(sellable_units[:3])}")
        
        return BoardAnalysis(
            unit_count=len(board),
            total_power=total_power,
            power_tier=power_tier,
            active_traits=[{
                'name': t.get('name', ''),
                'count': t.get('count', 0),
                'tier': t.get('tier', '')
            } for t in traits],
            strongest_trait=strongest_trait,
            upgrade_opportunities=upgrade_opportunities[:5],  # Top 5
            sellable_units=sellable_units[:5],
            reasoning=" | ".join(reasoning_parts)
        )
    
    def estimate_lobby_position(self, health: int, board_power: float) -> str:
        """Rough estimate of position in lobby"""
        # Very rough heuristic
        if health >= 80 and board_power >= 300:
            return "1st-2nd"
        elif health >= 60 and board_power >= 200:
            return "2nd-4th"
        elif health >= 40:
            return "3rd-5th"
        elif health >= 20:
            return "5th-7th"
        else:
            return "7th-8th"
