# Train YOLOv8n on our 5-class dataset (wolf, dog, fox, deer, person)
# and export to NCNN for faster CPU inference on Raspberry Pi 4B

from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolov8n.pt")
    model.train(data="dataset.yaml", epochs=50, imgsz=416, batch=16)

    best = YOLO("runs/detect/train/weights/best.pt")
    best.export(format="ncnn", imgsz=416)
