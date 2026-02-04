"""
YOLO Training Script for TFT Detection
Fine-tunes YOLOv8 on TFT champions, items, and game elements
"""

import os
import sys
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("ultralytics required. Install with: pip install ultralytics")


def create_dataset_yaml(data_dir: str, output_path: str = "tft_dataset.yaml"):
    """
    Create YOLO dataset configuration file
    
    Expected directory structure:
        data_dir/
            images/
                train/
                val/
            labels/
                train/
                val/
    """
    data_dir = Path(data_dir)
    
    # Load class names from tft_data.json
    classes = []
    tft_data_path = Path(__file__).parent.parent / "tft_data.json"
    
    if tft_data_path.exists():
        import json
        with open(tft_data_path, 'r') as f:
            data = json.load(f)
        
        # Add champions
        if 'champions' in data:
            for champ in data['champions']:
                name = champ.get('name', champ.get('apiName', ''))
                if name:
                    classes.append(f"champion_{name}")
        
        # Add items
        if 'items' in data:
            for item in data['items']:
                name = item.get('name', item.get('apiName', ''))
                if name:
                    classes.append(f"item_{name}")
    
    # Add special classes
    classes.extend([
        "star_1", "star_2", "star_3",  # Star level indicators
        "gold_coin",                    # Gold indicator
        "hp_bar",                       # Health bar
    ])
    
    # Create dataset config
    config = {
        'path': str(data_dir.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'names': {i: name for i, name in enumerate(classes)}
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Dataset config saved to {output_path}")
    print(f"Total classes: {len(classes)}")
    
    return output_path, classes


def train_model(
    data_yaml: str = "tft_dataset.yaml",
    model_size: str = "n",  # n=nano, s=small, m=medium, l=large, x=xlarge
    epochs: int = 100,
    batch_size: int = 16,
    img_size: int = 640,
    output_dir: str = "models"
):
    """
    Train YOLO model on TFT dataset
    
    Args:
        data_yaml: Path to dataset configuration
        model_size: YOLOv8 model size (n/s/m/l/x)
        epochs: Number of training epochs
        batch_size: Batch size
        img_size: Input image size
        output_dir: Directory to save trained model
    """
    if not YOLO_AVAILABLE:
        print("ultralytics required for training")
        return None
    
    # Load pretrained YOLOv8 model
    model = YOLO(f"yolov8{model_size}.pt")
    
    print(f"\n=== Starting YOLO Training ===")
    print(f"Model: YOLOv8{model_size}")
    print(f"Dataset: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Image size: {img_size}")
    print("=" * 40)
    
    # Train
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        project=output_dir,
        name="tft_yolo",
        exist_ok=True,
        patience=20,  # Early stopping patience
        save=True,
        save_period=10,  # Save checkpoint every 10 epochs
        plots=True,
        verbose=True
    )
    
    # Copy best model to standard location
    best_model_path = Path(output_dir) / "tft_yolo" / "weights" / "best.pt"
    if best_model_path.exists():
        import shutil
        final_path = Path(output_dir) / "tft_yolo.pt"
        shutil.copy(best_model_path, final_path)
        print(f"\nBest model saved to: {final_path}")
    
    return results


def validate_model(model_path: str = "models/tft_yolo.pt", data_yaml: str = "tft_dataset.yaml"):
    """Validate trained model on validation set"""
    if not YOLO_AVAILABLE:
        print("ultralytics required")
        return None
    
    model = YOLO(model_path)
    results = model.val(data=data_yaml)
    
    print("\n=== Validation Results ===")
    print(f"mAP50: {results.box.map50:.4f}")
    print(f"mAP50-95: {results.box.map:.4f}")
    
    return results


def export_model(model_path: str = "models/tft_yolo.pt", format: str = "onnx"):
    """
    Export model to different formats
    
    Formats: onnx, torchscript, openvino, engine (TensorRT)
    """
    if not YOLO_AVAILABLE:
        print("ultralytics required")
        return None
    
    model = YOLO(model_path)
    exported_path = model.export(format=format)
    print(f"Model exported to: {exported_path}")
    return exported_path


def prepare_dataset(source_dir: str = "training/screenshots", output_dir: str = "training/dataset"):
    """
    Prepare dataset structure from captured screenshots
    
    Creates the proper YOLO directory structure:
        dataset/
            images/train/
            images/val/
            labels/train/
            labels/val/
    """
    import shutil
    import random
    
    source = Path(source_dir)
    output = Path(output_dir)
    
    # Create directory structure
    for split in ["train", "val"]:
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)
    
    # Find all board and bench images (the ones we need to annotate)
    board_imgs = list(source.glob("board/*.png"))
    bench_imgs = list(source.glob("bench/*.png"))
    
    all_imgs = board_imgs + bench_imgs
    
    if not all_imgs:
        print(f"No images found in {source_dir}/board or {source_dir}/bench")
        print("\nCapture screenshots first:")
        print("  python training/capture_training_data.py")
        return
    
    # Shuffle and split 80/20
    random.shuffle(all_imgs)
    split_idx = int(len(all_imgs) * 0.8)
    
    train_imgs = all_imgs[:split_idx]
    val_imgs = all_imgs[split_idx:]
    
    # Copy images
    for img_path in train_imgs:
        shutil.copy(img_path, output / "images" / "train" / img_path.name)
    
    for img_path in val_imgs:
        shutil.copy(img_path, output / "images" / "val" / img_path.name)
    
    print(f"\n✅ Dataset prepared in {output_dir}")
    print(f"   Training images: {len(train_imgs)}")
    print(f"   Validation images: {len(val_imgs)}")
    print("\n" + "=" * 50)
    print("NEXT STEPS - Annotate your images:")
    print("=" * 50)
    print("\n1. Install labelImg:")
    print("   pip install labelImg")
    print("\n2. Run labelImg:")
    print(f"   labelImg {output_dir}/images/train")
    print("\n3. Settings in labelImg:")
    print("   - Change save format to YOLO")
    print("   - Save labels to: dataset/labels/train/")
    print("\n4. Draw bounding boxes around champions")
    print("   - Label format: TFTUnit_ChampionName (e.g., TFTUnit_Veigar)")
    print("\n5. Repeat for validation set:")
    print(f"   labelImg {output_dir}/images/val")
    print("\n6. After annotation, train:")
    print("   python training/train_yolo.py --action train")
    print("=" * 50)


def get_tft_classes() -> list:
    """Get list of TFT Set 13 champions for annotation"""
    classes = [
        # Set 13 Champions (example - update with current set)
        "TFTUnit_Ambessa", "TFTUnit_Caitlyn", "TFTUnit_Camille", "TFTUnit_Corki",
        "TFTUnit_Darius", "TFTUnit_Draven", "TFTUnit_Ekko", "TFTUnit_Elise",
        "TFTUnit_Ezreal", "TFTUnit_Gangplank", "TFTUnit_Garen", "TFTUnit_Heimerdinger",
        "TFTUnit_Illaoi", "TFTUnit_Irelia", "TFTUnit_Jayce", "TFTUnit_Jinx",
        "TFTUnit_KogMaw", "TFTUnit_Leona", "TFTUnit_Lulu", "TFTUnit_Maddie",
        "TFTUnit_MissFortune", "TFTUnit_Morgana", "TFTUnit_Nami", "TFTUnit_Nocturne",
        "TFTUnit_Nunu", "TFTUnit_Powder", "TFTUnit_Renata", "TFTUnit_Renni",
        "TFTUnit_Scar", "TFTUnit_Sevika", "TFTUnit_Silco", "TFTUnit_Singed",
        "TFTUnit_Smeech", "TFTUnit_Steb", "TFTUnit_Swain", "TFTUnit_Tristana",
        "TFTUnit_Trundle", "TFTUnit_TwistedFate", "TFTUnit_Urgot", "TFTUnit_Vander",
        "TFTUnit_Veigar", "TFTUnit_Vi", "TFTUnit_Viktor", "TFTUnit_Violet",
        "TFTUnit_Vladimir", "TFTUnit_Warwick", "TFTUnit_Zeri", "TFTUnit_Ziggs",
        "TFTUnit_Zoe", "TFTUnit_Zyra",
        # Star indicators
        "Star_1", "Star_2", "Star_3",
    ]
    return classes


def create_classes_file(output_dir: str = "training/dataset"):
    """Create classes.txt for labelImg"""
    classes = get_tft_classes()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    
    classes_file = output / "classes.txt"
    with open(classes_file, 'w') as f:
        for cls in classes:
            f.write(f"{cls}\n")
    
    print(f"✅ Created {classes_file}")
    print(f"   {len(classes)} classes")
    return classes_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Train YOLO model for TFT")
    parser.add_argument("--action", choices=["setup", "prepare", "train", "validate", "export"],
                       default="setup", help="Action to perform")
    parser.add_argument("--data-dir", default="training/dataset",
                       help="Dataset directory")
    parser.add_argument("--model-size", default="n", choices=["n", "s", "m", "l", "x"],
                       help="YOLO model size")
    parser.add_argument("--epochs", type=int, default=100,
                       help="Training epochs")
    parser.add_argument("--batch", type=int, default=16,
                       help="Batch size")
    
    args = parser.parse_args()
    
    if args.action == "setup":
        # Create dataset configuration and classes file
        create_classes_file(args.data_dir)
        create_dataset_yaml(args.data_dir)
        print("\n" + "=" * 50)
        print("YOLO TRAINING WORKFLOW")
        print("=" * 50)
        print("\nStep 1: Capture screenshots during a TFT game")
        print("  python training/capture_training_data.py")
        print("\nStep 2: Prepare dataset structure")
        print("  python training/train_yolo.py --action prepare")
        print("\nStep 3: Annotate with labelImg (see instructions above)")
        print("\nStep 4: Train the model")
        print("  python training/train_yolo.py --action train")
        print("=" * 50)
    
    elif args.action == "prepare":
        prepare_dataset(output_dir=args.data_dir)
    
    elif args.action == "train":
        train_model(
            model_size=args.model_size,
            epochs=args.epochs,
            batch_size=args.batch
        )
    
    elif args.action == "validate":
        validate_model()
    
    elif args.action == "export":
        export_model()


if __name__ == "__main__":
    main()
