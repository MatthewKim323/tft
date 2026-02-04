# TFT Bot - Complete Documentation

A fully automated Teamfight Tactics bot that captures game state, makes intelligent decisions, and executes actions via mouse control.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Usage Guide](#usage-guide)
6. [Configuration](#configuration)
7. [Training YOLO](#training-yolo)
8. [How It Works](#how-it-works)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This bot uses a **hybrid extraction system** combining:
- **OCR** for text (gold, HP, level, stage)
- **Template Matching** for shop champions and items (fast, no training needed)
- **YOLO** for board/bench champion detection (requires training)

The bot operates in a continuous loop:
```
Screen Capture → State Extraction → Decision Engine → Action Execution → Repeat
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 1: State Extraction                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌─────────────────────────────────────────┐   │
│  │  Screen  │───▶│         Region Capture (ROIs)           │   │
│  │  Capture │    │  items│traits│board│players│bench│shop  │   │
│  └──────────┘    └─────────────────────────────────────────┘   │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐     │
│  │     OCR     │    │   Template  │    │      YOLO       │     │
│  │  (EasyOCR)  │    │   Matching  │    │   (Optional)    │     │
│  │             │    │             │    │                 │     │
│  │ • Gold      │    │ • Shop      │    │ • Board champs  │     │
│  │ • HP        │    │ • Items     │    │ • Bench champs  │     │
│  │ • Level     │    │ • Stars     │    │ • Star levels   │     │
│  │ • Stage     │    │             │    │                 │     │
│  └─────────────┘    └─────────────┘    └─────────────────┘     │
│         │                    │                    │             │
│         └────────────────────┼────────────────────┘             │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │  State Builder  │                          │
│                    │   (JSON Output) │                          │
│                    └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 2: Decision Engine                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ Board Evaluator │    │ Economy Evaluator│                    │
│  │                 │    │                  │                    │
│  │ • Unit power    │    │ • Interest calc  │                    │
│  │ • Synergies     │    │ • Level timing   │                    │
│  │ • Items         │    │ • Roll timing    │                    │
│  │ • Upgrades      │    │ • Save vs spend  │                    │
│  └────────┬────────┘    └────────┬─────────┘                    │
│           │                      │                              │
│           └──────────┬───────────┘                              │
│                      ▼                                          │
│           ┌─────────────────────┐                               │
│           │  Strategy Selector  │                               │
│           │                     │                               │
│           │ • Econ (save gold)  │                               │
│           │ • Slow Roll (50g)   │                               │
│           │ • Fast 8 (rush lvl) │                               │
│           │ • All-in (desperate)│                               │
│           └──────────┬──────────┘                               │
│                      ▼                                          │
│           ┌─────────────────────┐                               │
│           │  Action Generator   │                               │
│           │                     │                               │
│           │ Prioritized list:   │                               │
│           │ 1. Buy upgrades     │                               │
│           │ 2. Level up         │                               │
│           │ 3. Buy pairs        │                               │
│           │ 4. Reroll           │                               │
│           │ 5. Equip items      │                               │
│           └─────────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 3: Action Executor                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Position Mapping                         ││
│  │                                                             ││
│  │  Shop: [slot0] [slot1] [slot2] [slot3] [slot4]             ││
│  │                                                             ││
│  │  Buttons: [Buy XP] [Reroll] [Lock]                         ││
│  │                                                             ││
│  │  Board:  ◇ ◇ ◇ ◇ ◇ ◇ ◇  (hex grid)                        ││
│  │           ◇ ◇ ◇ ◇ ◇ ◇                                      ││
│  │          ◇ ◇ ◇ ◇ ◇ ◇ ◇                                     ││
│  │           ◇ ◇ ◇ ◇ ◇ ◇                                      ││
│  │                                                             ││
│  │  Bench: [0][1][2][3][4][5][6][7][8]                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Mouse Controller                          ││
│  │                   (pyautogui)                               ││
│  │                                                             ││
│  │  • click(x, y)      - Buy champions, press buttons         ││
│  │  • drag(from, to)   - Move units, equip items              ││
│  │                                                             ││
│  │  Safety: Move mouse to corner to abort (failsafe)          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Screen Capture (`state_extraction/capture.py`)
Captures screenshots at native resolution (2560x1664 on Retina displays).

**ROI Regions:**
| Region | Position | Size | Purpose |
|--------|----------|------|---------|
| Items | (0, 120) | 80×1040 | Item inventory |
| Traits | (80, 120) | 260×1040 | Active traits |
| Board | (360, 120) | 1760×1040 | Champion board |
| Players | (2120, 120) | 440×1180 | Player portraits |
| Bench | (360, 1180) | 1520×220 | Bench champions |
| Shop | (360, 1400) | 1520×264 | Shop area |
| Top HUD | (360, 0) | 1760×120 | Stage, timer |

### 2. OCR Engine (`state_extraction/ocr.py`)
Uses EasyOCR to extract text values:
- **Gold**: Current gold amount
- **Health**: Player HP
- **Level**: Current level
- **XP**: Experience progress
- **Stage**: Current stage (e.g., "3-2")

### 3. Template Matcher (`state_extraction/template_matcher.py`)
Matches known images against screen regions.

**How it works:**
1. Downloads champion/item icons from Riot Data Dragon API
2. Caches icons locally in `assets/data_dragon/`
3. Uses OpenCV `matchTemplate()` to find matches
4. Returns confidence scores and positions

**Star Level Detection:**
- Analyzes color in top portion of champion portrait
- Pink/Magenta = 3-star
- Gold/Yellow = 2-star
- Default = 1-star

### 4. YOLO Detector (`state_extraction/detector.py`)
Deep learning object detection for champions on board/bench.

**Why YOLO for board/bench:**
- Champions move around (variable positions)
- Multiple champions visible at once
- Need bounding boxes for positioning

**Training required** - see [Training YOLO](#training-yolo) section.

### 5. State Builder (`state_extraction/state_builder.py`)
Combines all extraction methods into a single JSON game state:

```json
{
  "timestamp": "2026-02-03T14:32:05Z",
  "stage": {"current": "3-2", "phase": "planning"},
  "player": {
    "health": 78,
    "gold": 34,
    "level": 6,
    "xp": {"current": 12, "required": 24}
  },
  "board": [
    {"slot": [2, 1], "champion": "Veigar", "star": 2, "items": ["Rabadon"]}
  ],
  "bench": [
    {"slot": 0, "champion": "Lulu", "star": 1, "items": []}
  ],
  "shop": [
    {"slot": 0, "champion": "Teemo", "cost": 3}
  ],
  "items": ["BF Sword", "Chain Vest"],
  "traits": [
    {"name": "Sorcerer", "count": 4, "tier": "gold"}
  ]
}
```

### 6. Board Evaluator (`bot/evaluator.py`)
Calculates board strength on a 0-100 scale:

**Scoring factors:**
- **Unit Power (40%)**: Champion cost × star multiplier
- **Synergies (25%)**: Active trait bonuses
- **Items (20%)**: Equipped item count
- **Positioning (15%)**: (placeholder for future)

**Star multipliers:**
- 1-star: 1.0x
- 2-star: 1.8x
- 3-star: 3.0x

**Strength tiers:**
- Dominant: 80+
- Strong: 60-79
- Average: 40-59
- Weak: <40

### 7. Economy Evaluator (`bot/evaluator.py`)
Recommends economic decisions based on:

**Interest calculation:**
- +1 gold per 10 gold (max +5 at 50g)

**Stage guidelines:**
| Stage | Target Level | Min Gold |
|-------|--------------|----------|
| 1 | 3 | 10 |
| 2 | 5 | 30 |
| 3 | 6 | 50 |
| 4 | 7 | 50 |
| 5 | 8 | 30 |
| 6 | 9 | 0 |

**Decision outputs:**
- `should_econ`: Save for interest
- `should_level`: Buy XP
- `should_roll`: Spend gold on rerolls

### 8. Decision Engine (`bot/decision_engine.py`)
The bot brain that selects strategy and generates actions.

**Strategies:**
| Strategy | Description | When Used |
|----------|-------------|-----------|
| Econ | Save gold, hit interest | Default, healthy HP |
| Slow Roll | Roll at 50g maintaining interest | Mid-game, weak board |
| Fast 8 | Rush to level 8 | Late game, level 7+ |
| All-in | Spend everything | HP ≤ 20, desperate |

**Action Priority:**
1. Buy champions that complete upgrades (priority 1)
2. Level up if strategic (priority 5)
3. Buy pairs for future upgrades (priority 10)
4. Buy key champions for comp (priority 15)
5. Reroll for upgrades (priority 20)
6. Equip items (priority 25)
7. Sell weak units (priority 30)

### 9. Action Executor (`bot/actions.py`)
Converts actions into mouse movements.

**Available actions:**
- `buy_shop_champion(slot)` - Click shop slot
- `sell_unit(bench_slot)` - Drag to sell area
- `buy_xp()` - Click XP button
- `reroll()` - Click reroll button
- `move_unit(from, to)` - Drag unit
- `equip_item(item_slot, target)` - Drag item to unit
- `place_from_bench(slot, col, row)` - Drag bench to board

---

## Installation

### Prerequisites
- Python 3.10+
- macOS (tested on Retina displays)
- TFT installed and running in windowed mode

### Install dependencies

```bash
cd /Users/matthewkim/Documents/tft_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r state_extraction/requirements.txt
```

### Key dependencies:
- `ultralytics` - YOLOv8
- `easyocr` - Text extraction
- `opencv-python` - Image processing
- `pyautogui` - Mouse control
- `pynput` - Hotkey capture
- `requests` - Data Dragon API

---

## Usage Guide

### Step 1: Calibrate ROIs

First, align the capture regions with your TFT window:

```bash
python training/calibrate_roi.py
```

1. Make sure TFT is visible on screen
2. Click the **top-left** corner of the game area
3. Click the **bottom-right** corner
4. Press **'s'** to save calibration
5. Press **'q'** to quit

Saves to `roi_calibration.json`.

### Step 2: Test Components

Verify everything is working:

```bash
python run_bot.py --test
```

Expected output:
```
1. Testing imports...
   ✓ ScreenCapture
   ✓ OCREngine
   ✓ TemplateMatcher
   ✓ StateBuilder
   ✓ DecisionEngine
   ✓ Evaluators
   ✓ ActionExecutor

2. Testing screen capture...
   ✓ Captured 2560x1664 screenshot

3. Testing decision engine...
   ✓ Generated 3 actions
   ✓ Top action: Buy Zoe for upgrade
```

### Step 3: Analyze Current Game

Take a snapshot and see what the bot would do:

```bash
python run_bot.py --analyze
```

### Step 4: Dry Run Mode

Continuous analysis without mouse control:

```bash
python run_bot.py --dry-run
```

Output:
```
--- Iteration 1 ---
Stage: 3-2 | HP: 78 | Gold: 34 | Level: 6
Board: average (52.3) | Strategy: econ
Top Action: Buy Lulu for upgrade
```

Press `Ctrl+C` to stop.

### Step 5: Live Mode

⚠️ **Warning**: This will control your mouse!

```bash
python run_bot.py --live
```

**Safety:** Move mouse to any corner to trigger failsafe and abort.

---

## Configuration

### ROI Calibration File (`roi_calibration.json`)

```json
{
  "game_window": {
    "x": 0,
    "y": 0,
    "width": 2560,
    "height": 1664
  },
  "items": {"x": 0, "y": 120, "width": 80, "height": 1040},
  "traits": {"x": 80, "y": 120, "width": 260, "height": 1040},
  ...
}
```

### TFT Data (`tft_data.json`)

Contains champion costs, traits, and items for the current set. Used for:
- Evaluating board strength
- Identifying upgrade opportunities
- YOLO class definitions

### Adjusting Bot Behavior

In `bot/decision_engine.py`:

```python
# Change strategy thresholds
STRATEGIES = {
    "econ": Strategy("econ", target_level=8, roll_threshold=50, key_champions=[]),
    "slow_roll": Strategy("slow_roll", target_level=6, roll_threshold=50, key_champions=[]),
    ...
}
```

In `bot/evaluator.py`:

```python
# Change stage guidelines
STAGE_GUIDELINES = {
    "3": {"target_level": 6, "min_gold": 50},
    "4": {"target_level": 7, "min_gold": 50},
    ...
}
```

---

## Training YOLO

For best champion detection, train a custom YOLO model:

### Step 1: Capture Screenshots

```bash
python training/capture_training_data.py
```

**Hotkeys:**
- `\` - Capture all regions
- `]` - Capture full screen only
- `F12` - Quit

Play several TFT games, capturing regularly. Aim for 200-500 board/bench screenshots.

### Step 2: Prepare Dataset

```bash
python training/train_yolo.py --action prepare
```

This organizes screenshots into:
```
training/dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### Step 3: Annotate Images

Install labelImg:
```bash
pip install labelImg
```

Run annotation tool:
```bash
labelImg training/dataset/images/train
```

**In labelImg:**
1. Change format to **YOLO** (View → Auto Save Mode)
2. Set save directory to `training/dataset/labels/train/`
3. Draw bounding boxes around each champion
4. Label format: `TFTUnit_ChampionName` (e.g., `TFTUnit_Veigar`)

Repeat for validation set.

### Step 4: Train Model

```bash
python training/train_yolo.py --action train --epochs 100 --batch 16
```

Training outputs to `models/tft_yolo.pt`.

### Step 5: Validate

```bash
python training/train_yolo.py --action validate
```

---

## How It Works

### Decision Flow Example

**Scenario:** Stage 3-2, 45 gold, Level 6, 70 HP, weak board

1. **State Extraction**
   - Captures screen regions
   - OCR extracts: gold=45, HP=70, level=6, stage="3-2"
   - Template matcher finds shop champions
   - (YOLO detects board champions if trained)

2. **Board Evaluation**
   - Unit power: 35/100 (low cost, few 2-stars)
   - Synergies: 20/100 (only 1 bronze trait active)
   - Items: 15/100 (2 items equipped)
   - **Total: 45 (average tier)**

3. **Economy Evaluation**
   - Gold: 45 (earning +4 interest)
   - Stage 3 guideline: target level 6 ✓, min gold 50
   - `should_econ = True` (save to 50)
   - `should_level = False` (already at target)
   - `should_roll = False` (HP healthy)

4. **Strategy Selection**
   - HP > 50 → not desperate
   - Board is weak but HP is fine
   - **Selected: "econ"** (save gold)

5. **Action Generation**
   - Found: Lulu in shop, have 2x Lulu on bench
   - **Action 1:** Buy Lulu (completes 2-star) - priority 1
   - Found: saving for interest
   - **Action 2:** Wait - priority 100

6. **Execution**
   - Click shop slot containing Lulu
   - Wait for next decision cycle

### The Game Loop

```python
while game_running:
    # 1. Capture (100-200ms)
    screenshot = capture.capture_full_screen()
    
    # 2. Extract (200-500ms)
    game_state = state_builder.build_state_fast()
    
    # 3. Decide (10-50ms)
    actions = engine.decide(game_state)
    
    # 4. Execute (100-300ms per action)
    executor.execute_actions(actions, max_actions=3)
    
    # 5. Wait for game to update (2s default)
    time.sleep(2.0)
```

---

## Troubleshooting

### "Could not capture game state"
- Make sure TFT window is visible (not minimized)
- Run calibration: `python training/calibrate_roi.py`
- Check screen resolution matches calibration

### "OCR not detecting gold/HP"
- Ensure TFT UI is at default scale
- Try capturing a fresh screenshot and check the `top_hud` region
- OCR works best with high contrast text

### "Template matching not finding shop champions"
- Run template matcher test: `python -m state_extraction.template_matcher`
- This downloads fresh icons from Data Dragon
- Shop champions may need higher resolution templates

### "YOLO not detecting champions"
- YOLO requires training! See [Training YOLO](#training-yolo)
- Without training, bot uses template matching (less accurate for board)

### "Mouse clicks in wrong positions"
- Re-run calibration: `python training/calibrate_roi.py`
- Check `roi_calibration.json` was created
- Test in dry-run mode first: `python run_bot.py --dry-run`

### "Bot moves too fast/slow"
Adjust in `bot/actions.py`:
```python
self.move_duration = 0.1  # Mouse move time
self.action_delay = 0.3   # Delay between actions
```

### Failsafe triggered
- This is intentional! Move mouse to corner to abort
- Disable with `pyautogui.FAILSAFE = False` (not recommended)

---

## File Structure

```
tft_bot/
├── run_bot.py                    # Main entry point
├── roi_calibration.json          # Calibrated positions (generated)
├── tft_data.json                 # Champion/item/trait data
│
├── state_extraction/
│   ├── __init__.py
│   ├── api.py                    # FastAPI server
│   ├── capture.py                # Screen capture
│   ├── config.py                 # ROI definitions
│   ├── detector.py               # YOLO detector
│   ├── ocr.py                    # OCR engine
│   ├── state_builder.py          # JSON state builder
│   ├── template_matcher.py       # Template matching
│   └── requirements.txt
│
├── bot/
│   ├── __init__.py
│   ├── actions.py                # Mouse controller
│   ├── decision_engine.py        # Strategy & actions
│   └── evaluator.py              # Board/economy analysis
│
├── training/
│   ├── calibrate_roi.py          # ROI calibration tool
│   ├── capture_training_data.py  # Screenshot capture
│   ├── train_yolo.py             # YOLO training
│   └── dataset/                  # Training data (generated)
│
├── models/
│   └── tft_yolo.pt              # Trained YOLO model (generated)
│
└── assets/
    └── data_dragon/             # Cached champion icons (generated)
```

---

## Credits & Acknowledgments

- **Riot Games** - TFT game and Data Dragon API
- **Ultralytics** - YOLOv8
- **EasyOCR** - OCR engine
- **PyAutoGUI** - Mouse control

---

*This bot is for educational purposes. Use responsibly and in accordance with Riot Games' Terms of Service.*
