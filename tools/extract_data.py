#!/usr/bin/env python3
"""
Script to extract all TFT game data from CommunityDragon
"""

import json
import urllib.request
import sys
from pathlib import Path

# CommunityDragon TFT data endpoint
BASE_URL = "https://raw.communitydragon.org/latest/cdragon/tft"
LANGUAGES = ["en_us"]  # Can add more languages if needed

def download_tft_data(language="en_us"):
    """Download TFT data for a specific language"""
    url = f"{BASE_URL}/{language}.json"
    print(f"Downloading TFT data from {url}...")
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            data_str = json.dumps(data)
            print(f"✓ Successfully downloaded {len(data_str)} bytes of data")
            return data
    except urllib.error.URLError as e:
        print(f"✗ Error downloading data: {e}")
        return None
    except Exception as e:
        print(f"✗ Error processing data: {e}")
        return None

def save_data(data, filename="tft_data.json"):
    """Save data to JSON file"""
    output_path = Path(__file__).parent.parent / filename
    print(f"\nSaving data to {output_path}...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"✓ Successfully saved {file_size:,} bytes to {output_path}")
        return output_path
    except Exception as e:
        print(f"✗ Error saving file: {e}")
        return None

def analyze_data_structure(data):
    """Analyze and print the structure of the TFT data"""
    print("\n" + "="*60)
    print("TFT Data Structure Analysis")
    print("="*60)
    
    if isinstance(data, dict):
        print(f"\nTop-level keys ({len(data)}):")
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                print(f"  - {key}: dict with {len(value)} keys")
            elif isinstance(value, list):
                print(f"  - {key}: list with {len(value)} items")
            else:
                print(f"  - {key}: {type(value).__name__}")
    
    # Look for common TFT data structures
    common_keys = ['sets', 'champions', 'items', 'traits', 'augments', 'units']
    print("\nCommon TFT data structures found:")
    for key in common_keys:
        if key in data:
            print(f"  ✓ {key}")
        else:
            # Check for variations
            variations = [k for k in data.keys() if key.lower() in k.lower()]
            if variations:
                print(f"  ? {key} (found variations: {variations})")

def main():
    print("="*60)
    print("TFT Data Extractor from CommunityDragon")
    print("="*60)
    
    # Download data
    data = download_tft_data("en_us")
    
    if data is None:
        print("\n✗ Failed to download TFT data")
        sys.exit(1)
    
    # Analyze structure
    analyze_data_structure(data)
    
    # Save to file
    output_path = save_data(data, "tft_data.json")
    
    if output_path:
        print(f"\n✓ Complete! TFT data saved to: {output_path}")
        print(f"  File size: {output_path.stat().st_size:,} bytes")
    else:
        print("\n✗ Failed to save data")
        sys.exit(1)

if __name__ == "__main__":
    main()
