"""Typed configuration model and YAML loader for WolfDet."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SystemConfig:
    device_id: str = "siegen-wolfdet-01"
    mode: str = "demo"
    log_dir: str = "logs"
    recording_dir: str = "recordings"


@dataclass
class CameraConfig:
    backend: str = "synthetic"
    source: str = "0"
    width: int = 640
    height: int = 480
    detect_fps: float = 4.0
    idle_poll_interval_s: float = 0.25
    autofocus: bool = True
    hdr: bool = True


@dataclass
class MotionConfig:
    backend: str = "software"
    pir_gpio_pin: int = 17
    detect_window_s: float = 15.0
    software_diff_threshold: int = 25
    software_min_area_ratio: float = 0.01


@dataclass
class DetectionConfig:
    backend: str = "mock"
    model_path: str = "models/wolfdet_yolov8n.onnx"
    target_classes: list[str] = field(default_factory=lambda: ["wolf"])
    privacy_classes: list[str] = field(default_factory=lambda: ["person"])
    conf_threshold: float = 0.60
    iou_threshold: float = 0.45
    confirm_hits: int = 3
    confirm_window: int = 5
    demo_dog_as_wolf_proxy: bool = False


@dataclass
class ResponseConfig:
    pre_playback_delay_s: float = 2.0
    playback_duration_s: float = 10.0
    cooldown_s: float = 30.0
    audio_dir: str = "assets/audio"
    randomize_no_repeat: bool = True
    amp_shutdown_gpio_pin: int = 27
    enable_sound_output: bool = True


@dataclass
class RecorderConfig:
    enabled: bool = True
    pre_trigger_buffer_s: float = 3.0
    post_trigger_record_s: float = 10.0
    save_video_clips: bool = True


@dataclass
class PowerModelConfig:
    idle_w: float = 2.10
    detecting_w: float = 4.80
    responding_w: float = 6.20
    cooldown_w: float = 2.40
    battery_capacity_wh: float = 74.0
    usable_efficiency: float = 0.85


@dataclass
class AppConfig:
    system: SystemConfig = field(default_factory=SystemConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    motion: MotionConfig = field(default_factory=MotionConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    response: ResponseConfig = field(default_factory=ResponseConfig)
    recorder: RecorderConfig = field(default_factory=RecorderConfig)
    power_model: PowerModelConfig = field(default_factory=PowerModelConfig)


def _merge_dataclass(instance: Any, data: dict[str, Any] | None) -> None:
    if not data:
        return
    for key, value in data.items():
        if hasattr(instance, key):
            setattr(instance, key, value)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Minimal fallback parser for flat 2-level YAML when PyYAML is not installed."""
    root: dict[str, Any] = {}
    current_section: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, raw_val = line.strip().partition(":")
        key = key.strip()
        val_str = raw_val.strip()
        if indent == 0 and not val_str:
            current_section = {}
            root[key] = current_section
            continue
        if current_section is None:
            continue
        current_section[key] = _coerce_scalar(val_str)
    return root


def _coerce_scalar(raw: str) -> Any:
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(part.strip()) for part in inner.split(",")]
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load AppConfig from a YAML file, falling back gracefully to defaults."""
    cfg = AppConfig()
    if path is None:
        return cfg

    config_path = Path(path)
    if not config_path.exists():
        return cfg

    raw_text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(raw_text) or {}
    except ImportError:
        parsed = _parse_simple_yaml(raw_text)

    if isinstance(parsed, dict):
        _merge_dataclass(cfg.system, parsed.get("system"))
        _merge_dataclass(cfg.camera, parsed.get("camera"))
        _merge_dataclass(cfg.motion, parsed.get("motion"))
        _merge_dataclass(cfg.detection, parsed.get("detection"))
        _merge_dataclass(cfg.response, parsed.get("response"))
        _merge_dataclass(cfg.recorder, parsed.get("recorder"))
        _merge_dataclass(cfg.power_model, parsed.get("power_model"))
    return cfg
