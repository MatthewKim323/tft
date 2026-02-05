#!/usr/bin/env python3
"""
Filter TFT data to only include the current set (Set 16)
"""

import json
from pathlib import Path

def filter_current_set(input_file=None, output_file=None):
    """Filter data to only include Set 16"""
    base_dir = Path(__file__).parent.parent
    
    if input_file is None:
        input_file = base_dir / "tft_data.json"
    if output_file is None:
        output_file = base_dir / "tft_data.json"
    
    print("="*70)
    print("Filtering TFT Data to Current Set (Set 16)")
    print("="*70)
    
    # Load data
    print(f"\nLoading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find the latest Set 16 entry
    set_16_entries = [s for s in data.get('setData', []) if s.get('number') == 16]
    if not set_16_entries:
        print("✗ No Set 16 data found!")
        return
    
    # Get the most recent Set 16 (usually the last one)
    latest_set_16 = max(set_16_entries, key=lambda x: len(x.get('augments', [])))
    
    print(f"\n✓ Found Set 16: {latest_set_16.get('name')}")
    print(f"  - Champions: {len(latest_set_16.get('champions', []))}")
    print(f"  - Items: {len(latest_set_16.get('items', []))}")
    print(f"  - Traits: {len(latest_set_16.get('traits', []))}")
    print(f"  - Augments: {len(latest_set_16.get('augments', []))}")
    
    # Filter items to only Set 16 items
    print(f"\nFiltering items (from {len(data.get('items', []))} total)...")
    set_16_items = []
    # Items in setData are just apiName strings
    set_16_item_names = set(latest_set_16.get('items', []))
    set_16_augment_names = set(latest_set_16.get('augments', []))
    
    for item in data.get('items', []):
        api_name = item.get('apiName', '')
        # Include if it's in Set 16 items/augments list or if it's a Set 16 item (TFT16_ prefix)
        if api_name in set_16_item_names or api_name in set_16_augment_names or 'TFT16_' in api_name:
            set_16_items.append(item)
    
    print(f"✓ Filtered to {len(set_16_items)} Set 16 items")
    
    # Create filtered data structure
    filtered_data = {
        "set": {
            "number": 16,
            "name": latest_set_16.get('name'),
            "mutator": latest_set_16.get('mutator')
        },
        "champions": latest_set_16.get('champions', []),
        "items": set_16_items,
        "traits": latest_set_16.get('traits', []),
        "augments": latest_set_16.get('augments', [])
    }
    
    # Save filtered data
    print(f"\nSaving filtered data to {output_file}...")
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    
    file_size = output_path.stat().st_size
    print(f"✓ Successfully saved {file_size:,} bytes")
    print(f"\n✓ Complete! Current set data saved to: {output_path}")
    print(f"  - Champions: {len(filtered_data['champions'])}")
    print(f"  - Items: {len(filtered_data['items'])}")
    print(f"  - Traits: {len(filtered_data['traits'])}")
    print(f"  - Augments: {len(filtered_data['augments'])}")

if __name__ == "__main__":
    filter_current_set()
