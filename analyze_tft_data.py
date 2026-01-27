#!/usr/bin/env python3
"""
Analyze the extracted TFT data to show what's included
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_tft_data(filepath="tft_data.json"):
    """Analyze and summarize TFT data"""
    print("="*70)
    print("TFT Data Analysis")
    print("="*70)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Analyze sets
    print(f"\n📦 SETS: {len(data.get('sets', {}))} sets found")
    for set_id, set_info in sorted(data.get('sets', {}).items()):
        if isinstance(set_info, dict):
            name = set_info.get('name', 'Unknown')
            print(f"   - Set {set_id}: {name}")
    
    # Analyze setData
    print(f"\n📊 SET DATA: {len(data.get('setData', []))} set entries")
    for i, set_entry in enumerate(data.get('setData', [])):
        if isinstance(set_entry, dict):
            set_num = set_entry.get('number', i)
            set_name = set_entry.get('name', 'Unknown')
            champions = len(set_entry.get('champions', []))
            items = len(set_entry.get('items', []))
            traits = len(set_entry.get('traits', []))
            augments = len(set_entry.get('augments', []))
            print(f"   - Set {set_num} ({set_name}):")
            print(f"     • Champions: {champions}")
            print(f"     • Items: {items}")
            print(f"     • Traits: {traits}")
            print(f"     • Augments: {augments}")
    
    # Analyze items
    print(f"\n🎒 ITEMS: {len(data.get('items', []))} total items")
    
    # Categorize items
    item_types = defaultdict(int)
    for item in data.get('items', []):
        api_name = item.get('apiName', '')
        if 'Augment' in api_name:
            item_types['Augments'] += 1
        elif 'Item' in api_name or item.get('composition'):
            item_types['Items'] += 1
        elif 'Trait' in api_name:
            item_types['Trait Items'] += 1
        else:
            item_types['Other'] += 1
    
    for item_type, count in sorted(item_types.items()):
        print(f"   - {item_type}: {count}")
    
    # Sample champions from setData
    print(f"\n👥 CHAMPIONS (sample from latest set):")
    latest_set = data.get('setData', [])[-1] if data.get('setData') else {}
    champions = latest_set.get('champions', [])
    if champions:
        print(f"   Total champions in latest set: {len(champions)}")
        print(f"   Sample champions:")
        for champ in champions[:5]:
            name = champ.get('name', 'Unknown')
            cost = champ.get('cost', '?')
            traits = ', '.join(champ.get('traits', []))
            print(f"     - {name} (Cost: {cost}, Traits: {traits})")
    
    # Sample traits
    print(f"\n🏷️  TRAITS (sample from latest set):")
    traits = latest_set.get('traits', [])
    if traits:
        print(f"   Total traits in latest set: {len(traits)}")
        print(f"   Sample traits:")
        for trait in traits[:5]:
            name = trait.get('name', 'Unknown')
            desc = trait.get('desc', '')[:80] + '...' if len(trait.get('desc', '')) > 80 else trait.get('desc', '')
            print(f"     - {name}")
            print(f"       {desc}")
    
    print("\n" + "="*70)
    print("✓ Analysis complete!")
    print("="*70)

if __name__ == "__main__":
    analyze_tft_data()
