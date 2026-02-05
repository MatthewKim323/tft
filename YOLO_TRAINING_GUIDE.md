# YOLO Training Guide for TFT Bot

Train YOLOv8 to detect champions on your board and bench.

---

## What YOLO Does

| Already Working (no training) | Needs YOLO Training |
|------------------------------|---------------------|
| Gold, HP, Level (OCR) | Board champions |
| Shop champions (template matching) | Bench champions |
| Items (template matching) | Champion positions |
| Star levels (color detection) | |

---

## Step 1: Capture Training Screenshots

```bash
cd /path/to/tft_bot
source venv/bin/activate
python training/capture_training_data.py
```

**While playing TFT:**
| Key | Action |
|-----|--------|
| `\` | Capture all regions |
| `]` | Full screen only (augments, carousel) |
| `F10` | Board only |
| `F12` | Quit |

**What to capture:**
- Planning phases (board clearly visible)
- Different game stages (early, mid, late)
- Different comps (variety of champions)
- Different board positions
- 1★, 2★, 3★ units

**Target: 200-500+ screenshots**

Screenshots save to `screenshots/board/` and `screenshots/bench/`

---

## Step 2: Upload to Roboflow

### Create Workspace

1. Go to [roboflow.com](https://roboflow.com) and sign up
2. Create a new **Workspace** (e.g., "TFT Bot Team")
3. Invite your team members to the workspace

### Create Project

1. Click **Create New Project**
2. Settings:
   - **Project Name**: `tft-champions`
   - **Project Type**: `Object Detection`
   - **Annotation Group**: Your workspace
   - **License**: Private (or your choice)

### Upload Images

1. Click **Upload Data**
2. Drag and drop your `screenshots/board/` and `screenshots/bench/` images
3. Click **Save and Continue**

---

## Step 3: Set Up Classes

Before annotating, define your champion classes.

1. Go to **Classes** in your project
2. Add all TFT champions you want to detect:

```
Ahri
Akali
Amumu
Annie
Azir
Bard
Blitzcrank
...
(add all champions from current set)
```

**Tip:** You can import from a text file. Use `training/dataset/classes.txt` after running:
```bash
python training/train_yolo.py --action setup
```

---

## Step 4: Annotate (Team Effort)

### Assign Images

1. Go to **Annotate** tab
2. Click **Assign Images** to distribute work among team members
3. Each person gets their batch

### How to Annotate

1. Select an image
2. Press `B` or click the bounding box tool
3. Draw a tight box around each champion
4. Select the champion name from the class list
5. Repeat for all champions in the image
6. Press `→` or click **Save & Next**

### Annotation Rules

```
┌─────────────────────────────────────┐
│                                     │
│    ┌─────┐     ┌─────┐             │
│    │Ahri │     │Zoe  │             │  ← Tight box around sprite
│    │ ★★  │     │ ★   │             │  ← Include star indicator
│    └─────┘     └─────┘             │  ← Don't include HP bar
│                                     │
└─────────────────────────────────────┘
```

**DO:**
- ✅ Draw tight boxes around champion sprites
- ✅ Include the star indicator (★★★) in the box
- ✅ Label every visible champion
- ✅ Label partially visible champions too

**DON'T:**
- ❌ Include health bars in box
- ❌ Make boxes too loose
- ❌ Skip champions

### Keyboard Shortcuts (Roboflow)

| Key | Action |
|-----|--------|
| `B` | Bounding box tool |
| `V` | Select tool |
| `→` | Save & next image |
| `←` | Previous image |
| `Del` | Delete selected box |
| `Ctrl+Z` | Undo |

---

## Step 5: Generate Dataset Version

Once annotation is complete:

1. Go to **Generate** tab
2. Click **Create New Version**
3. **Preprocessing** (recommended):
   - Auto-Orient: ✅
   - Resize: Stretch to 640x640
4. **Augmentation** (recommended for more data):
   - Flip: Horizontal
   - Rotation: ±15°
   - Brightness: ±15%
   - Blur: Up to 1px
5. Click **Generate**

This creates multiple versions of your images, effectively 3-5x your dataset size.

---

## Step 6: Export Dataset

1. Go to **Versions** tab
2. Click on your generated version
3. Click **Export Dataset**
4. Select format: **YOLOv8**
5. Choose **Download zip**
6. Extract to `training/dataset/`

Your folder structure should look like:
```
training/dataset/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/           (optional)
│   ├── images/
│   └── labels/
└── data.yaml
```

---

## Step 7: Train the Model

```bash
cd /path/to/tft_bot
source venv/bin/activate

# Train with Roboflow dataset
python training/train_yolo.py --action train --data training/dataset/data.yaml --epochs 100
```

**Training options:**
```bash
# Quick test (less accurate)
--epochs 50 --batch 8

# Standard training
--epochs 100 --batch 16

# Best quality (slower)
--epochs 200 --batch 32
```

**Training time:**
- CPU: 2-6 hours
- GPU: 30min - 2 hours

---

## Step 8: Deploy Model

After training completes:

```bash
# Copy best model to the expected location
cp models/tft_yolo/weights/best.pt models/tft_yolo.pt
```

Now when you start the API:
```bash
python run_state_api.py --manual
```

You'll see:
```
✓ YOLO model loaded: models/tft_yolo.pt
```

---

## Team Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│                   TEAM WORKFLOW                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. CAPTURE (everyone plays TFT)                       │
│     python training/capture_training_data.py            │
│     → Upload screenshots to shared Drive/Discord        │
│                                                         │
│  2. UPLOAD TO ROBOFLOW (one person)                    │
│     → Create project, upload all images                 │
│     → Set up champion classes                           │
│                                                         │
│  3. ANNOTATE (team splits work)                        │
│     → Assign batches to each person                     │
│     → Everyone annotates their images                   │
│     → Review each other's work                          │
│                                                         │
│  4. GENERATE & EXPORT (one person)                     │
│     → Create version with augmentation                  │
│     → Export as YOLOv8 format                           │
│                                                         │
│  5. TRAIN (one person with good hardware)              │
│     python training/train_yolo.py --action train        │
│                                                         │
│  6. SHARE MODEL                                        │
│     → Upload best.pt to shared storage                  │
│     → Everyone copies to models/tft_yolo.pt             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Roboflow Tips

### Quality Control

- Use **Review** feature to check annotations
- Enable **Smart Polygon** for better box suggestions
- Use **Model-Assisted Labeling** after first training round

### Versioning

- Create new versions when adding more data
- Keep old versions for comparison
- Name versions descriptively: `v1-initial`, `v2-more-data`, etc.

### API Integration (Advanced)

Roboflow can host your model too:
```python
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("your-workspace").project("tft-champions")
model = project.version(1).model

# Inference
prediction = model.predict("screenshot.png", confidence=40).json()
```

---

## Troubleshooting

### Low Accuracy

- Add more training images
- Check annotation quality (boxes too loose?)
- Increase epochs
- Add more augmentation

### Model Not Loading

```bash
# Check if model exists
ls -la models/tft_yolo.pt

# If missing, copy from training output
cp models/tft_yolo/weights/best.pt models/tft_yolo.pt
```

### Roboflow Export Issues

- Make sure to select **YOLOv8** format (not YOLOv5)
- Check that `data.yaml` points to correct paths
- Verify images and labels folders have matching files

---

## Quick Commands Reference

```bash
# Capture training data
python training/capture_training_data.py

# Setup classes file (for Roboflow import)
python training/train_yolo.py --action setup

# Train model
python training/train_yolo.py --action train --epochs 100

# Deploy model
cp models/tft_yolo/weights/best.pt models/tft_yolo.pt

# Test with API
python run_state_api.py --manual
```

---

## Resources

- [Roboflow Docs](https://docs.roboflow.com/)
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [Annotation Best Practices](https://blog.roboflow.com/tips-for-how-to-label-images/)
