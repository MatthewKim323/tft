# TFT Bot - Complete Usage Guide

How to set up, calibrate, train, and use the TFT Coach system.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [How Extraction Works](#how-extraction-works)
3. [Data Storage](#data-storage)
4. [Screen Calibration](#screen-calibration)
5. [Running the Coach](#running-the-coach)
   - [Manual Mode](#manual-mode-recommended)
   - [Autonomous Mode](#autonomous-mode)
6. [Capturing Screenshots](#capturing-screenshots)
7. [Training the Model](#training-the-model)
8. [Using the Dashboard](#using-the-dashboard)
9. [Troubleshooting](#troubleshooting)

---

## How Extraction Works

The bot uses a **hybrid extraction system** with 4 layers:

### Layer 1: OCR (EasyOCR)
**What it extracts:** Gold, HP, Level, Stage, XP  
**How:** Reads text from the HUD using optical character recognition  
**Training needed:** None ✓

### Layer 2: Template Matching
**What it extracts:** Shop champions, Items  
**How:** Matches Riot Data Dragon icons against your shop/item regions  
**Training needed:** None ✓ (downloads official icons automatically)

### Layer 3: Star Level Detection
**What it extracts:** Champion star levels (1★, 2★, 3★)  
**How:** Color analysis - gray/white=1★, gold=2★, pink=3★  
**Training needed:** None ✓

### Layer 4: YOLO Object Detection
**What it extracts:** Board champions, Bench champions  
**How:** Neural network trained on TFT screenshots  
**Training needed:** Yes ⚠️ (annotate screenshots + train)

### What Works Without YOLO Training?

| Feature | Works Now | Needs YOLO |
|---------|-----------|------------|
| Gold/HP/Level tracking | ✓ | - |
| Stage detection | ✓ | - |
| Shop champion detection | ✓ | - |
| Item detection | ✓ | - |
| Star level detection | ✓ | - |
| Board champion positions | - | ✓ |
| Bench champion positions | - | ✓ |

**Bottom line:** You can use the coach for economy decisions and shop recommendations right now. For board composition analysis, train YOLO.

---

## Data Storage

### Where Does Game Data Go?

**Answer: Nowhere permanently (by default).**

| Data Type | Storage Location | Persists? |
|-----------|-----------------|-----------|
| Live game state | RAM (in-memory) | No - cleared on close |
| Coach decisions | RAM (last ~20) | No - cleared on close |
| Decision history (dashboard) | Browser localStorage | Yes - up to 100 entries |
| Training screenshots | `training/screenshots/` | Yes - you captured them |

### No Database Needed

The system is designed for **real-time streaming**, not historical analysis:
- Game state is extracted → streamed to dashboard → discarded
- Your browser keeps recent decisions in localStorage
- When you close the browser tab, localStorage persists

### If You Want Persistent Storage

For ML training or game history, you'd need to:
1. **Save to JSON files** - Add file writing to `state_builder.py`
2. **Use a database** - Add SQLite, PostgreSQL, or a cloud service like Railway/Supabase
3. **Log to CSV** - Simple append-only logging

This isn't implemented because most users just want real-time coaching, not game archives.

---

## Quick Start

### Prerequisites

```bash
# Make sure you're in the project directory
cd /Users/matthewkim/Documents/tft_bot

# Activate virtual environment
source venv/bin/activate

# Install ALL dependencies (required!)
pip install -r requirements.txt
```

**Dependencies include:** opencv-python, easyocr, ultralytics (YOLO), fastapi, mss, pynput, pyautogui, requests

### The Basic Flow

```
1. Calibrate screen regions (one-time per computer)
2. Start the API server
3. Open the dashboard
4. Play TFT - coach analyzes and recommends
```

---

## Screen Calibration

**Why calibrate?** Different monitors have different resolutions and TFT window positions. Calibration maps the exact pixel locations of game elements on YOUR screen.

### Running Calibration

```bash
python training/calibrate_roi.py
```

### Steps

1. **Open TFT** and make sure the game window is visible
2. **Run the calibration tool** - it captures your screen
3. **Click the TOP-LEFT corner** of the TFT game area (where items panel starts)
4. **Click the BOTTOM-RIGHT corner** of the TFT game area
5. **Preview** - colored rectangles show where each region will be captured:
   - Blue = Items
   - Green = Traits
   - Yellow = Board
   - Magenta = Players
   - Orange = Bench
   - Cyan = Shop
   - Pink = Top HUD
6. **Press 's'** to save calibration
7. **Press 'q'** to quit

### Calibration Output

Saves to `roi_calibration.json`:

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
  "board": {"x": 360, "y": 120, "width": 1760, "height": 1040},
  ...
}
```

### Tips

- Make sure TFT is in **windowed fullscreen** or **borderless** mode for consistent captures
- If regions look wrong in preview, press **'r'** to reset and try again
- Calibration only needs to be done once per computer/monitor setup
- If you change monitors or resolution, recalibrate

---

## Running the Coach

The bot has **two operation modes**:

| Mode | Flag | When to Use |
|------|------|-------------|
| **Manual** | `--manual` | You control when analysis happens (recommended) |
| **Autonomous** | `--auto` | Continuous real-time analysis |

Both modes use the same calibration (`roi_calibration.json`), same dashboard, and same decision logs.

---

### Manual Mode (Recommended)

Best for learning and when the bot isn't fully trained. Analysis only happens when YOU trigger it.

**Terminal 1: Start API in manual mode**

```bash
source venv/bin/activate
python run_state_api.py --manual
```

**Terminal 2: Start the hotkey trigger**

```bash
python analyze_screenshot.py
```

**Terminal 3: Start the frontend (optional)**

```bash
cd frontend && npm run dev
```

**Workflow:**

1. Play TFT normally
2. When you want the coach's advice, press `\`
3. See recommendation in:
   - Terminal (instant feedback)
   - Dashboard Logs tab (if frontend running)
4. Screenshots saved to `screenshots/manual/`
5. Execute the recommendation manually

**Why use manual mode?**

- Bot isn't "smart enough" yet for full autonomy
- You stay in control of game decisions
- Great for learning what the coach thinks
- Builds up screenshot history for later training

---

### Autonomous Mode

Continuous real-time analysis. The bot constantly watches your screen and streams recommendations.

**Terminal 1: Start API in autonomous mode**

```bash
source venv/bin/activate
python run_state_api.py --auto
```

**Terminal 2: Start the frontend**

```bash
cd frontend && npm run dev
```

**Workflow:**

1. Open `http://localhost:5173`
2. Click **"logs"** in navigation
3. Play TFT
4. Watch real-time recommendations stream in
5. Execute decisions manually (or use `--live` mode with `run_bot.py` for automation)

---

### Mode Comparison

| Feature | Manual (`--manual`) | Autonomous (`--auto`) |
|---------|---------------------|----------------------|
| Analysis trigger | Press `\` | Continuous |
| CPU usage | Low (on-demand) | Higher (constant) |
| Screenshots saved | Yes (`screenshots/manual/`) | No |
| Best for | Learning, training data | Full automation |
| Hotkey script needed | Yes (`analyze_screenshot.py`) | No |

---

### Quick Reference

```bash
# Manual mode (recommended)
python run_state_api.py --manual
python analyze_screenshot.py  # In another terminal

# Autonomous mode
python run_state_api.py --auto
```

---

## Capturing Screenshots

There are two types of screenshot capture:

| Type | Script | Purpose | Output Location |
|------|--------|---------|-----------------|
| **Manual Analysis** | `analyze_screenshot.py` | Get coach advice on-demand | `screenshots/manual/` |
| **Training Data** | `training/capture_training_data.py` | Collect data for YOLO | `training/screenshots/` |

### Manual Analysis Capture

Used with manual mode to get coach recommendations:

```bash
# Start API in manual mode first
python run_state_api.py --manual

# Then run the hotkey trigger
python analyze_screenshot.py
```

Press `\` to:
1. Take full screenshot
2. Analyze with coach
3. Show recommendation in terminal
4. Save screenshot to `screenshots/manual/`

---

### Training Data Capture (for YOLO)

```bash
python training/capture_training_data.py
```

### Hotkeys

| Key | Action |
|-----|--------|
| `\` | Capture all 7 regions + full screen |
| `]` | Capture full screen only |
| `F12` | Quit capture tool |

### What Gets Captured

Each press of `\` saves 8 images:

```
training/screenshots/
├── full/
│   └── 20260205_143205_123_full.png
├── board/
│   └── 20260205_143205_123_board.png
├── bench/
│   └── 20260205_143205_123_bench.png
├── shop/
│   └── 20260205_143205_123_shop.png
├── items/
│   └── 20260205_143205_123_items.png
├── traits/
│   └── 20260205_143205_123_traits.png
├── players/
│   └── 20260205_143205_123_players.png
└── top_hud/
    └── 20260205_143205_123_top_hud.png
```

### Capture Strategy

For training, capture during:
- **Planning phases** (when you can see your board clearly)
- **Different stages** (early, mid, late game)
- **Various comps** (different champions visible)
- **Different board states** (full board, empty bench, etc.)

Aim for **200-500 screenshots** for good model training.

---

## Training the Model

### Overview

The YOLO model detects champions on your board and bench. Training requires:
1. Screenshots (captured above)
2. Annotations (bounding boxes around champions)
3. Training run

### Step 1: Prepare Dataset

```bash
python training/train_yolo.py --action prepare
```

This:
- Copies screenshots to `training/dataset/`
- Creates train/val split (80/20)
- Generates `classes.txt` for labeling

### Step 2: Annotate Images

Install labelImg:

```bash
pip install labelImg
```

Run it:

```bash
labelImg training/dataset/images/train
```

**In labelImg:**

1. **Change format to YOLO** (View → Change Save Format → YOLO)
2. **Set save directory** to `training/dataset/labels/train/`
3. **Open images** from `training/dataset/images/train/`
4. For each image:
   - Press `W` to create a box
   - Draw box around each champion
   - Label it: `TFTUnit_ChampionName` (e.g., `TFTUnit_Veigar`)
   - Press `D` for next image, `A` for previous
5. Repeat for validation set (`images/val/` → `labels/val/`)

**Labeling tips:**
- Box should tightly fit the champion sprite
- Include star indicators in the box
- Don't include health bars
- Label each champion individually, even if stacked

### Step 3: Train

```bash
python training/train_yolo.py --action train --epochs 100 --batch 16
```

Training takes 1-4 hours depending on:
- Dataset size
- GPU availability
- Number of epochs

**Output:**
- Best model saved to `models/tft_yolo.pt`
- Training metrics in `models/tft_yolo/`

### Step 4: Validate

```bash
python training/train_yolo.py --action validate
```

Shows mAP (mean Average Precision) - aim for 0.7+ for good detection.

---

## Using the Dashboard

### Logs Page (Coach)

The Logs page has two panels:

**Left: Live Coach Recommendations**
- Real-time decisions streamed via WebSocket
- Shows: action, target, priority, reasoning
- Click cards to expand for details
- Color-coded priorities:
  - Red = Critical (do immediately)
  - Orange = High
  - Green = Medium
  - Blue = Low

**Right: Session History**
- Historical logs from the session
- Filter by type (decisions, analysis, economy)

### How Decisions Work

The coach analyzes:

1. **Economy** - Gold, interest, level timing
2. **Board** - Unit power, synergies, upgrades
3. **Shop** - Value of available champions

Then recommends:
- `BUY` - Purchase champion (completes upgrade, builds toward upgrade, fits comp)
- `SELL` - Sell unit (no pair, clearing bench)
- `LEVEL` - Buy XP (hit level timing)
- `REROLL` - Refresh shop (find upgrades)
- `HOLD` - Save gold (build interest)

### Decision Format

```
┌─────────────────────────────────────┐
│ [14:32:05]              CRITICAL    │
│ ┌────┐                              │
│ │ ●  │  buy                         │
│ └────┘  Zoe in slot 1               │
│                                     │
│ Completes 2★ upgrade!               │
├─────────────────────────────────────┤
│ game state                          │
│ ┌────┬────┬────┬────┐               │
│ │3-2 │ 78 │ 34 │ 6  │               │
│ └────┴────┴────┴────┘               │
│ analysis                            │
│ ● healthy  ● medium  ● 3rd-4th     │
│ alternatives                        │
│ level - Could level to 7            │
│ hold - Save for interest            │
└─────────────────────────────────────┘
```

---

## Complete Workflow

### First Time Setup

```bash
# 1. Install dependencies
cd /Users/matthewkim/Documents/tft_bot
source venv/bin/activate
pip install -r requirements.txt

# 2. Calibrate screen (TFT must be open)
python training/calibrate_roi.py
# Click corners, press 's' to save

# 3. Test capture
python training/capture_training_data.py
# Press '\' a few times, check training/screenshots/
```

### Playing with Coach (Manual Mode - Recommended)

```bash
# Terminal 1: Start API in manual mode
source venv/bin/activate
python run_state_api.py --manual

# Terminal 2: Start hotkey trigger
python analyze_screenshot.py

# Terminal 3 (optional): Start frontend
cd frontend && npm run dev
```

1. Play TFT normally
2. Press `\` when you want coach advice
3. See recommendation in terminal
4. (Optional) Check dashboard at `http://localhost:5173` → Logs tab
5. Execute decisions manually

### Playing with Coach (Autonomous Mode)

```bash
# Terminal 1: Start API in auto mode
source venv/bin/activate
python run_state_api.py --auto

# Terminal 2: Start frontend
cd frontend && npm run dev
```

1. Open `http://localhost:5173`
2. Click **"logs"** in nav
3. Play TFT
4. Watch recommendations stream in real-time
5. Execute decisions manually

### Training Session

```bash
# 1. Capture ~200-500 screenshots during games
python training/capture_training_data.py

# 2. Prepare dataset
python training/train_yolo.py --action prepare

# 3. Annotate with labelImg
labelImg training/dataset/images/train

# 4. Train model
python training/train_yolo.py --action train

# 5. Copy model for use
cp models/tft_yolo/weights/best.pt models/tft_yolo.pt
```

---

## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/status` | GET | **Extraction capabilities status** |
| `/state` | GET | Current game state (fast mode) |
| `/state?mode=full` | GET | Full state with YOLO detection |
| `/decision` | GET | Single coach decision |
| `/decision/history` | GET | Recent decisions |
| `/manual_capture_and_analyze` | POST | **Manual mode: capture + analyze** |
| `/regions` | GET | ROI definitions |
| `/test/templates` | GET | Test template matching |

### Check Extraction Status

```bash
curl http://127.0.0.1:8000/status
```

```json
{
  "status": "online",
  "extraction_methods": {
    "ocr": {"available": true, "description": "Text extraction for HUD"},
    "template_matching": {"available": true, "description": "Icon matching for shop/items"},
    "star_detection": {"available": true, "description": "Color-based 1/2/3 star detection"},
    "yolo": {"available": false, "description": "Object detection for board/bench"}
  },
  "coach_available": true
}
```

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/state?fps=5` | Stream game state at 5 FPS |
| `/ws/decisions?fps=2` | Stream coach decisions |
| `/ws/changes` | Stream only state changes |

### Example: Get Decision via API

```bash
curl http://127.0.0.1:8000/decision
```

```json
{
  "timestamp": "2026-02-05T14:32:05",
  "game_state_summary": {
    "stage": "3-2",
    "health": 78,
    "gold": 34,
    "level": 6
  },
  "decision": {
    "action": "BUY",
    "target": "Zoe in slot 1",
    "priority": "critical",
    "reasoning": "Completes 2★ upgrade!"
  }
}
```

---

## Troubleshooting

### "Not connected" in dashboard

- Make sure API is running: `python run_state_api.py`
- Check terminal for errors
- API should show "AI Coach initialized ✓"

### Screenshots capturing wrong areas

- Recalibrate: `python training/calibrate_roi.py`
- Make sure TFT window position hasn't changed
- Use windowed fullscreen mode for consistency

### OCR not reading gold/HP

- Ensure TFT UI scale is at default (100%)
- Check that top_hud region captures the right area
- OCR works best with clear, high-contrast text

### Coach recommendations seem wrong

- The coach uses heuristics, not a trained ML model for decisions
- Economy analyzer assumes standard level timings
- Board evaluator uses approximate power calculations
- Improve by adjusting thresholds in `bot/analyzers/`

### YOLO not detecting champions

- Model needs to be trained first
- Without training, system falls back to template matching
- Train with 200+ annotated screenshots for good accuracy

### Test extraction is working

```bash
# Check what's available
curl http://127.0.0.1:8000/status

# Test template matching specifically
curl http://127.0.0.1:8000/test/templates

# Run state builder test
python -c "from state_extraction.state_builder import test_state_builder; test_state_builder()"
```

### Calibration window too small/large

- The window is resized to 1280x800 for viewing
- Your actual captures use native resolution
- Coordinates are saved at native resolution

---

## File Locations

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `roi_calibration.json` | Your screen calibration |
| `analyze_screenshot.py` | Manual mode hotkey trigger |
| `run_state_api.py` | API server (--manual or --auto) |
| `models/tft_yolo.pt` | Trained YOLO model |
| `tft_data.json` | Champion/trait data |
| `training/screenshots/` | Captured training images |
| `screenshots/manual/` | Manual mode captures |
| `training/dataset/` | Prepared training data |
| `assets/data_dragon/` | Cached Riot icons |

## Project Structure

```
tft_bot/
├── run_state_api.py       # Start API server (--manual or --auto)
├── run_bot.py             # Start bot (--test, --dry-run, --live)
├── analyze_screenshot.py  # Manual mode hotkey trigger
├── requirements.txt       # Python dependencies
├── roi_calibration.json   # Your screen calibration
├── tft_data.json          # Game data
│
├── bot/                   # AI Coach
│   ├── coach.py           # Decision engine
│   ├── decisions.py       # Decision types
│   ├── actions.py         # Mouse control
│   └── analyzers/         # economy.py, board.py, shop.py
│
├── state_extraction/      # Screen capture & detection
│   ├── api.py             # FastAPI server
│   ├── state_builder.py   # Hybrid extraction
│   ├── capture.py         # Screen capture
│   ├── ocr.py             # Text extraction
│   ├── detector.py        # YOLO detection
│   ├── template_matcher.py # Icon matching
│   └── config.py          # ROI coordinates
│
├── training/              # Training tools
│   ├── calibrate_roi.py   # Screen calibration
│   ├── capture_training_data.py
│   └── train_yolo.py
│
├── tools/                 # Utility scripts
│   ├── extract_data.py    # Download TFT data
│   ├── filter_set.py      # Filter to current set
│   ├── analyze_data.py    # Analyze data structure
│   └── test_capture.py    # Test screen capture
│
├── screenshots/           # Saved screenshots
│   └── manual/            # Manual mode captures
│
└── frontend/              # React dashboard
```

---

## Summary

```
┌─────────────────────────────────────────────────────────┐
│                    TFT Bot Workflow                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. CALIBRATE (one-time)                               │
│     python training/calibrate_roi.py                    │
│                                                         │
│  2. PICK A MODE                                        │
│                                                         │
│     ┌─────────────────┬─────────────────────────────┐  │
│     │  MANUAL (rec.)  │  AUTONOMOUS                 │  │
│     ├─────────────────┼─────────────────────────────┤  │
│     │ run_state_api   │ run_state_api.py --auto     │  │
│     │   .py --manual  │                             │  │
│     │ analyze_screen  │ (no hotkey script)          │  │
│     │   shot.py       │                             │  │
│     │                 │                             │  │
│     │ Press \ for     │ Continuous real-time        │  │
│     │ analysis        │ analysis                    │  │
│     └─────────────────┴─────────────────────────────┘  │
│                                                         │
│  3. START FRONTEND (optional)                          │
│     cd frontend && npm run dev                         │
│                                                         │
│  4. PLAY TFT                                           │
│     → Manual: Press \ when you want advice             │
│     → Auto: Recommendations stream continuously        │
│     → See decisions in terminal or Logs tab            │
│     → You execute manually                             │
│                                                         │
│  5. TRAIN (optional, improves detection)               │
│     → Capture screenshots during games                 │
│     → Annotate with labelImg                           │
│     → Train YOLO model                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
