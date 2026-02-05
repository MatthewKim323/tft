# TFT Bot

AI-powered Teamfight Tactics coach that analyzes your game in real-time and provides recommendations.

## Features

- **Real-time game state extraction** via screen capture
- **Hybrid detection system**: OCR + Template Matching + YOLO
- **AI Coach** that recommends buys, levels, and economy decisions
- **React dashboard** for live game monitoring
- **WebSocket streaming** for instant updates

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the API server
python run_state_api.py

# 3. Open dashboard (in another terminal)
cd frontend && npm run dev

# 4. Open TFT and play!
```

## Project Structure

```
tft_bot/
├── run_state_api.py      # Main API server entry point
├── run_bot.py            # Bot executor (for automated play)
├── requirements.txt      # Python dependencies
├── tft_data.json         # Game data (champions, items, traits)
│
├── bot/                  # AI Coach logic
│   ├── coach.py          # Main decision engine
│   ├── decisions.py      # Decision types and formatting
│   ├── actions.py        # Mouse controller for automation
│   └── analyzers/        # Game state analyzers
│       ├── economy.py    # Gold, interest, level timing
│       ├── board.py      # Board strength, upgrades
│       └── shop.py       # Shop value, buy recommendations
│
├── state_extraction/     # Screen capture & detection
│   ├── api.py            # FastAPI server + WebSocket
│   ├── state_builder.py  # Hybrid extraction pipeline
│   ├── capture.py        # Screen capture
│   ├── ocr.py            # Text extraction (gold, HP, stage)
│   ├── detector.py       # YOLO detection (champions)
│   ├── template_matcher.py # Icon matching (shop, items)
│   └── config.py         # ROI coordinates
│
├── training/             # YOLO training tools
│   ├── calibrate_roi.py  # Visual ROI calibration
│   ├── capture_training_data.py  # Screenshot capture
│   └── train_yolo.py     # YOLO training script
│
├── tools/                # Utility scripts
│   ├── extract_data.py   # Download TFT data
│   ├── filter_set.py     # Filter to current set
│   ├── analyze_data.py   # Analyze data structure
│   └── test_capture.py   # Test screen capture
│
└── frontend/             # React dashboard
    └── src/
        ├── pages/        # Dashboard, Logs, Home
        ├── components/   # UI components
        └── hooks/        # WebSocket hooks
```

## How It Works

### Hybrid Extraction

The bot uses multiple detection methods for reliability:

| Method | What it extracts | Training needed? |
|--------|-----------------|------------------|
| **OCR** (EasyOCR) | Gold, HP, Level, Stage | No |
| **Template Matching** | Shop champions, Items | No (uses Riot icons) |
| **Star Detection** | 1★/2★/3★ levels | No (color analysis) |
| **YOLO** | Board/bench champions | Yes |

### API Endpoints

```
GET  /status        - Check extraction capabilities
GET  /state         - Current game state
GET  /decision      - Coach recommendation
WS   /ws/state      - Stream game state
WS   /ws/decisions  - Stream coach decisions
```

## Configuration

### Screen Calibration

Different monitors require calibration:

```bash
python training/calibrate_roi.py
```

Click corners of TFT window → Preview regions → Press 's' to save.

### Update Game Data

When a new TFT set releases:

```bash
python tools/extract_data.py
python tools/filter_set.py
```

## YOLO Training

For board/bench champion detection:

```bash
# 1. Capture screenshots while playing
python training/capture_training_data.py
# Press \ to capture regions

# 2. Annotate with LabelImg or Roboflow

# 3. Train
python training/train_yolo.py --action setup
python training/train_yolo.py --action train
```

## Data Source

Game data from [CommunityDragon](https://communitydragon.org) - current set only.

## License

Educational/personal use only. Not affiliated with Riot Games.
