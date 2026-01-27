# TFT Bot - Data Extraction

This repository contains extracted TFT (Teamfight Tactics) game data from CommunityDragon for the **current set only** (Set 16).

## Data Source

All data is extracted from [CommunityDragon](https://communitydragon.org/documentation), which provides scraped data from Riot Games' TFT client.

**Data URL**: `https://raw.communitydragon.org/latest/cdragon/tft/en_us.json`

## Extracted Data

The `tft_data.json` file contains **only Set 16 (current set)** data including:

### 📦 Current Set: Set 16
- **Champions**: 116 champions with complete stats, abilities, costs, and traits
- **Items**: 852 items (including all items and augments)
- **Traits**: 53 traits/synergies with descriptions and scaling
- **Augments**: 277 augments available in Set 16

### Data Structure

```json
{
  "set": {
    "number": 16,
    "name": "Set16",
    "mutator": "TFTSet16"
  },
  "champions": [
    {
      "apiName": "...",
      "name": "...",
      "cost": 1,
      "traits": [...],
      "ability": {...},
      "stats": {...},
      ...
    },
    ...
  ],
  "items": [
    {
      "apiName": "...",
      "name": "...",
      "desc": "...",
      "icon": "...",
      "effects": {...},
      ...
    },
    ...
  ],
  "traits": [
    {
      "apiName": "...",
      "name": "...",
      "desc": "...",
      "effects": {...},
      ...
    },
    ...
  ],
  "augments": [
    {
      "apiName": "...",
      "name": "...",
      "desc": "...",
      ...
    },
    ...
  ]
}
```

## Files

- `tft_data.json` - Current set (Set 16) TFT game data (~980 KB)
- `extract_tft_data.py` - Script to download data from CommunityDragon
- `filter_current_set.py` - Script to filter data to only current set
- `analyze_tft_data.py` - Script to analyze and summarize the data

## Usage

### Download Latest Data

```bash
python3 extract_tft_data.py
```

### Analyze Data

```bash
python3 analyze_tft_data.py
```

### Load Data in Python

```python
import json

with open('tft_data.json', 'r', encoding='utf-8') as f:
    tft_data = json.load(f)

# Access set info
set_info = tft_data['set']
print(f"Current set: {set_info['name']} (Set {set_info['number']})")

# Access champions
champions = tft_data['champions']
for champ in champions:
    print(f"{champ['name']} - Cost: {champ['cost']}, Traits: {champ['traits']}")

# Access items
items = tft_data['items']

# Access traits
traits = tft_data['traits']

# Access augments
augments = tft_data['augments']
```

## Legal Notice

This data is extracted from CommunityDragon, which operates under Riot Games' "Legal Jibber Jabber" policy. Riot Games does not endorse or sponsor this project. The usage of this data does not pose a risk to your API key.

**CommunityDragon does not endorse, condone or support the usage of Riot's assets provided through CommunityDragon's services with the purpose of ill intent, such as scripting or hacking.**

## Notes

- Data is updated regularly by CommunityDragon (check the last modified date)
- The file size is ~980 KB (uncompressed JSON)
- **Only current set (Set 16) data is included** - historical sets are filtered out
- To update to a new set, run `extract_tft_data.py` then `filter_current_set.py`
