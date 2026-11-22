"""Inference Latency, FPS, and CPU Profiler for Raspberry Pi 4B (4 GB).

Run this directly on your Raspberry Pi 4 Model B to collect real Midterm/Final
benchmark numbers comparing PyTorch (.pt), ONNX (.onnx), and NCNN formats.

Example:
    python scripts/benchmark_pi4.py --model yolov8n.pt --imgsz 416 --runs 50
"""

from __future__ import annotations

import argparse
import statistics
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark YOLO model latency & FPS on RPi 4B / PC.")
    parser.add_argument("--model", default="yolov8n.pt", help="Path to .pt, .onnx, or _ncnn_model")
    parser.add_argument("--imgsz", type=int, default=416, help="Inference resolution (e.g. 320, 416, 640)")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup iterations")
    parser.add_argument("--runs", type=int, default=40, help="Timed benchmark iterations")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        import numpy as np  # type: ignore
        from ultralytics import YOLO  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Please install numpy and ultralytics (pip install -r requirements-pi.txt)."
        ) from exc

    model = YOLO(args.model, task="detect")
    dummy = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    for _ in range(args.warmup):
        model.predict(dummy, imgsz=args.imgsz, verbose=False)

    latencies_ms: list[float] = []
    for _ in range(args.runs):
        t0 = time.perf_counter()
        model.predict(dummy, imgsz=args.imgsz, verbose=False)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = statistics.mean(latencies_ms)
    median_ms = statistics.median(latencies_ms)
    p95_ms = sorted(latencies_ms)[int(0.95 * len(latencies_ms)) - 1]
    fps = 1000.0 / mean_ms if mean_ms > 0 else 0.0

    print("=" * 64)
    print(f"BENCHMARK RESULTS | Model: {args.model} | imgsz: {args.imgsz}")
    print("-" * 64)
    print(f"  Mean Latency   : {mean_ms:6.1f} ms")
    print(f"  Median Latency : {median_ms:6.1f} ms")
    print(f"  P95 Latency    : {p95_ms:6.1f} ms")
    print(f"  Throughput     : {fps:6.2f} FPS")
    print(f"  Meets 4 FPS budget (<=250 ms)? {'YES' if mean_ms <= 250.0 else 'NO'}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
