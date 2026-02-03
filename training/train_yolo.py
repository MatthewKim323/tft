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


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Train YOLO model for TFT")
    parser.add_argument("--action", choices=["setup", "train", "validate", "export"],
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
        # Create dataset configuration
        create_dataset_yaml(args.data_dir)
        print("\nNext steps:")
        print("1. Capture training screenshots: python training/capture_training_data.py")
        print("2. Annotate images using labelImg or Roboflow")
        print("3. Organize into training/dataset/images/{train,val} and labels/{train,val}")
        print("4. Run training: python training/train_yolo.py --action train")
    
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
