"""
Train a lightweight YOLOv8n model on a custom wolf dataset and export for Raspberry Pi 4B.
Dataset classes: 0: wolf, 1: dog, 2: fox, 3: deer, 4: person
"""

from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolov8n.pt")
    model.train(
        data="dataset.yaml",  # Point this to your Roboflow / YOLO dataset yaml
        epochs=50,
        imgsz=416,
        batch=16,
    )
    # Export to NCNN for fastest CPU inference on Raspberry Pi 4B
    best = YOLO("runs/detect/train/weights/best.pt")
    best.export(format="ncnn", imgsz=416)
