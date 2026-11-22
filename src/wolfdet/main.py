"""CLI entrypoint for WolfDet (Midterm Demo, PC Video/Webcam, and Raspberry Pi 4B)."""

from __future__ import annotations

import argparse
from pathlib import Path
import time

from wolfdet.audio.deterrent import AudioDeterrent
from wolfdet.camera.opencv_source import OpenCVCameraSource, SyntheticScenarioCamera
from wolfdet.camera.picamera_source import PiCameraModule3Source
from wolfdet.config import AppConfig, load_config
from wolfdet.detection.mock_detector import ScenarioMockDetector
from wolfdet.detection.yolo_detector import YOLOWolfDetector
from wolfdet.motion.pir_gpio import GPIOPIRTrigger
from wolfdet.motion.software_motion import MockMotionTrigger, SoftwareMotionTrigger
from wolfdet.power.energy_model import RuntimeEnergyTracker
from wolfdet.recorder.event_logger import EventRecorder
from wolfdet.state_machine import WolfResponseStateMachine
from wolfdet.ui.hud import DemoHUD


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wolfdet",
        description=(
            "Energy-Efficient Wolf Detection & Automated Human-Speech Response System "
            "(Raspberry Pi 4B + Camera Module 3)"
        ),
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Path to YAML configuration file (default: config/settings.yaml)",
    )
    parser.add_argument(
        "--demo-scenarios",
        action="store_true",
        help="Run the built-in 3-scenario Midterm Presentation demo (Deer -> Hiker/GDPR -> Wolf)",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Video file path, webcam index ('0'), or 'picamera2' for Raspberry Pi Camera Module 3",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Path to YOLO/ONNX/NCNN model weights (enables real YOLOWolfDetector)",
    )
    parser.add_argument(
        "--proxy-wolf",
        action="store_true",
        help="Demo helper: map stock COCO 'dog' detections to 'wolf' when testing before custom training",
    )
    parser.add_argument(
        "--pi",
        action="store_true",
        help="Shortcut for Raspberry Pi 4B deployment (picamera2 + HC-SR501 GPIO PIR + headless)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Disable OpenCV GUI window (CLI telemetry only)",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Disable audible speaker output (still logs selected audio exemplars)",
    )
    return parser


def run_pipeline(args: argparse.Namespace) -> dict:
    cfg: AppConfig = load_config(args.config)

    if args.proxy_wolf:
        cfg.detection.demo_dog_as_wolf_proxy = True
    if args.silent:
        cfg.response.enable_sound_output = False

    # Select mode & backends
    if args.pi:
        cfg.camera.backend = "picamera2"
        cfg.motion.backend = "pir_gpio"
        cfg.detection.backend = "yolo"
        args.headless = True
    elif args.demo_scenarios:
        cfg.camera.backend = "synthetic"
        cfg.motion.backend = "mock"
        cfg.detection.backend = "mock"
    elif args.source is not None:
        cfg.camera.backend = "picamera2" if args.source == "picamera2" else "opencv"
        cfg.camera.source = args.source
        cfg.motion.backend = "software"
        cfg.detection.backend = "yolo" if args.model else cfg.detection.backend

    if args.model:
        cfg.detection.model_path = args.model
        cfg.detection.backend = "yolo"

    # Instantiate CameraSource
    if cfg.camera.backend == "picamera2":
        camera = PiCameraModule3Source(
            width=cfg.camera.width,
            height=cfg.camera.height,
            fps=cfg.camera.detect_fps,
            autofocus=cfg.camera.autofocus,
            hdr=cfg.camera.hdr,
        )
    elif cfg.camera.backend == "opencv":
        camera = OpenCVCameraSource(
            source=cfg.camera.source,
            width=cfg.camera.width,
            height=cfg.camera.height,
        )
    else:
        camera = SyntheticScenarioCamera(
            width=cfg.camera.width,
            height=cfg.camera.height,
            render_images=not args.headless,
        )

    # Instantiate MotionTrigger
    if cfg.motion.backend == "pir_gpio":
        motion = GPIOPIRTrigger(gpio_pin=cfg.motion.pir_gpio_pin)
    elif cfg.motion.backend == "software":
        motion = SoftwareMotionTrigger(
            diff_threshold=cfg.motion.software_diff_threshold,
            min_area_ratio=cfg.motion.software_min_area_ratio,
        )
    else:
        motion = MockMotionTrigger(default=False)

    # Instantiate WolfDetector
    if cfg.detection.backend == "yolo":
        detector = YOLOWolfDetector(
            model_path=cfg.detection.model_path,
            conf_threshold=cfg.detection.conf_threshold,
            iou_threshold=cfg.detection.iou_threshold,
        )
    else:
        detector = ScenarioMockDetector()

    audio = AudioDeterrent(
        audio_dir=cfg.response.audio_dir,
        randomize_no_repeat=cfg.response.randomize_no_repeat,
        amp_shutdown_gpio_pin=cfg.response.amp_shutdown_gpio_pin if args.pi else None,
        enable_sound_output=cfg.response.enable_sound_output,
        simulate_timing=not args.demo_scenarios,
    )

    buffer_frames = max(4, int(cfg.recorder.pre_trigger_buffer_s * cfg.camera.detect_fps))
    recorder = EventRecorder(
        log_dir=cfg.system.log_dir,
        recording_dir=cfg.system.recording_dir,
        max_buffer_frames=buffer_frames,
        fps=cfg.camera.detect_fps,
        save_video_clips=cfg.recorder.save_video_clips,
        enabled=cfg.recorder.enabled,
    )

    energy = RuntimeEnergyTracker(cfg.power_model)
    fsm = WolfResponseStateMachine(
        config=cfg,
        detector=detector,
        audio=audio,
        recorder=recorder,
        energy_tracker=energy,
    )
    hud = DemoHUD(show_gui=not args.headless)

    print("=" * 88)
    print(f"WolfDet v0.2.0 | Device: {cfg.system.device_id} | Camera: {cfg.camera.backend} | Detector: {cfg.detection.backend}")
    print("=" * 88)

    camera.open()
    frame_interval_s = 1.0 / max(1.0, cfg.camera.detect_fps)
    try:
        while True:
            packet = camera.read()
            if packet is None:
                break

            motion_active = packet.motion_detected or motion.check_motion(packet.image)
            result = fsm.step(packet, motion_active=motion_active)
            keep_going = hud.render(packet, result, energy)
            if not keep_going:
                break

            if not args.demo_scenarios and cfg.camera.backend != "synthetic":
                time.sleep(frame_interval_s)
    except KeyboardInterrupt:
        print("\nInterrupted by user; shutting down cleanly...")
    finally:
        hud.close()
        camera.close()
        motion.close()
        audio.close()

    summary = energy.summary()
    print("-" * 88)
    print(
        f"SESSION SUMMARY | Events logged: {len(fsm.events)} | "
        f"Avg Power: {summary['average_power_w']:.2f} W | "
        f"Energy Savings vs Continuous AI: {summary['savings_vs_continuous_pct']:.1f}% | "
        f"Est. Battery Runtime: {summary['projected_battery_hours']:.1f} h"
    )
    if recorder.jsonl_path.exists():
        print(f"Event log saved to: {Path(recorder.jsonl_path)}")
    print("=" * 88)
    return {"events": [e.to_dict() for e in fsm.events], "energy": summary}


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not (args.demo_scenarios or args.source or args.pi):
        args.demo_scenarios = True
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
