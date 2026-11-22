"""Ultralytics YOLOv8n / YOLO11n / ONNX / NCNN detector for PC & Raspberry Pi 4B."""

from __future__ import annotations

from pathlib import Path

from wolfdet.detection.base import WolfDetector
from wolfdet.types import BoundingBox, Detection, FramePacket


class YOLOWolfDetector(WolfDetector):
    """Runs lightweight YOLO weights (PyTorch .pt, ONNX .onnx, or NCNN directory).

    For Raspberry Pi 4B (4 GB), exporting a fine-tuned YOLOv8n/YOLO11n model to
    NCNN or ONNX gives ~5-10 FPS on CPU at 640x480 / 416x416, well above the
    2-4 FPS duty-cycled detection budget.
    """

    def __init__(
        self,
        model_path: str | Path = "models/wolfdet_yolov8n.onnx",
        conf_threshold: float = 0.50,
        iou_threshold: float = 0.45,
        imgsz: int = 416,
    ) -> None:
        self.model_path = str(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required for YOLOWolfDetector. "
                "Install requirements.txt or use --demo-scenarios."
            ) from exc
        self._model = YOLO(self.model_path, task="detect")

    def detect(self, packet: FramePacket) -> list[Detection]:
        if packet.image is None:
            return []

        results = self._model.predict(
            source=packet.image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )
        detections: list[Detection] = []
        for result in results:
            names = result.names or {}
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                label = str(names.get(cls_id, cls_id)).lower()
                detections.append(
                    Detection(
                        label=label,
                        confidence=conf,
                        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    )
                )
        return detections
