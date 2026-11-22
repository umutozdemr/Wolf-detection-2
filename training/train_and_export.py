"""Fine-tune YOLOv8n / YOLO11n on the 5-class WolfDet dataset and export for Raspberry Pi 4B.

Usage (PC with GPU or Google Colab):
    python training/train_and_export.py --base-model yolov8n.pt --epochs 60 --imgsz 416

Exports:
    - ONNX (FP32 / dynamic opset) for cross-platform CPU inference (onnxruntime)
    - NCNN (recommended for fastest ARMv8 Cortex-A72 inference on Raspberry Pi 4B)
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and export WolfDet YOLO model for RPi 4B.")
    parser.add_argument("--data", default="training/dataset.yaml", help="Path to dataset YAML")
    parser.add_argument("--base-model", default="yolov8n.pt", help="Pretrained base weights")
    parser.add_argument("--epochs", type=int, default=60, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=416, help="Input resolution (416 is optimal for Pi 4B)")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--project", default="runs/wolfdet", help="Output directory")
    parser.add_argument("--name", default="yolov8n_wolf_v1", help="Experiment name")
    parser.add_argument("--export-only", default=None, help="Skip training and export an existing .pt file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "ultralytics is not installed. Run: pip install -r requirements.txt"
        ) from exc

    if args.export_only:
        best_pt = Path(args.export_only)
    else:
        model = YOLO(args.base_model)
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            project=args.project,
            name=args.name,
            # Camera-trap augmentations: dusk/low-light, blur, partial foliage occlusion
            hsv_h=0.015,
            hsv_s=0.5,
            hsv_v=0.45,
            degrees=8.0,
            translate=0.1,
            scale=0.45,
            fliplr=0.5,
            mosaic=0.8,
            patience=15,
        )
        best_pt = Path(results.save_dir) / "weights" / "best.pt"

    print(f"\nExporting {best_pt} for Raspberry Pi 4B deployment (ONNX + NCNN)...")
    trained = YOLO(str(best_pt))
    onnx_path = trained.export(format="onnx", imgsz=args.imgsz, simplify=True)
    ncnn_path = trained.export(format="ncnn", imgsz=args.imgsz)
    print(f"Exported ONNX: {onnx_path}")
    print(f"Exported NCNN: {ncnn_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
