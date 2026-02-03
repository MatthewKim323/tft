# TFT YOLO Training Guide

## Overview

Training a YOLO model to detect TFT champions, items, and game elements requires:
1. **Capture** - Take screenshots during TFT gameplay
2. **Annotate** - Label objects in the screenshots
3. **Train** - Fine-tune YOLOv8 on your dataset
4. **Validate** - Test detection accuracy

---

## Step 1: Capture Training Screenshots

### Option A: Use the capture tool (recommended)
```bash
cd "/Users/matthewkim/Documents/tft bot"
source venv/bin/activate
python training/capture_training_data.py
```

Controls:
- `c` - Capture all regions
- `b` - Capture board only
- `s` - Capture shop only
- `a` - Toggle auto-capture (every 2 seconds)
- `q` - Quit

**Tip**: Play several TFT games while capturing. Aim for 200-500+ screenshots covering different:
- Champions (all 60+)
- Star levels (1★, 2★, 3★)
- Items (components + completed)
- Board positions
- Shop layouts

### Option B: Use Roboflow (easier annotation)
1. Go to [roboflow.com](https://roboflow.com)
2. Create a new project for "Object Detection"
3. Upload your screenshots
4. Annotate directly in browser
5. Export in "YOLOv8" format

---

## Step 2: Annotate Images

### Using LabelImg (local)
```bash
pip install labelImg
labelImg training/screenshots/board
```

For each image:
1. Draw bounding boxes around champions/items
2. Label with class name (e.g., "Ahri", "BF_Sword", "star_2")
3. Save in YOLO format (.txt files)

### Using Roboflow (recommended for beginners)
- Web-based annotation tool
- Auto-labeling assistance
- Easy export to YOLO format
- Free tier available

---

## Step 3: Organize Dataset

Structure your data like this:
```
training/dataset/
├── images/
│   ├── train/    (80% of images)
│   │   ├── img001.png
│   │   └── ...
│   └── val/      (20% of images)
│       ├── img101.png
│       └── ...
└── labels/
    ├── train/    (matching .txt files)
    │   ├── img001.txt
    │   └── ...
    └── val/
        ├── img101.txt
        └── ...
```

Each `.txt` label file contains:
```
# class_id x_center y_center width height (all normalized 0-1)
0 0.5 0.5 0.1 0.15
3 0.3 0.4 0.08 0.12
```

---

## Step 4: Train the Model

```bash
cd "/Users/matthewkim/Documents/tft bot"
source venv/bin/activate

# First, create the dataset config
python training/train_yolo.py --action setup

# Then train (adjust epochs/batch as needed)
python training/train_yolo.py --action train --epochs 100 --batch 16
```

Training takes 1-4 hours depending on:
- Dataset size
- Number of epochs
- GPU availability (much faster with GPU)

---

## Step 5: Validate & Use

```bash
# Validate model accuracy
python training/train_yolo.py --action validate

# Model will be saved to: models/tft_yolo.pt
```

---

## Quick Start (Minimal Dataset)

If you just want to test the pipeline quickly:

1. Capture 50-100 board screenshots
2. Annotate just the champions (ignore items for now)
3. Train for 50 epochs
4. See if basic detection works

You can always add more data and retrain later!

---

## Class List

The model will detect these classes (from tft_data.json):
- ~60 Champions (Ahri, Akali, etc.)
- ~40 Items (BF Sword, Chain Vest, etc.)
- Star indicators (star_1, star_2, star_3)
- Gold coins, HP bars

---

## Tips

1. **More data = better results** - Aim for 500+ annotated images
2. **Include variety** - Different game states, board layouts
3. **Start small** - Test with 50 images first to verify pipeline
4. **Use GPU** - Training is 10x faster with CUDA
5. **Roboflow is easier** - Especially for first-time annotation
