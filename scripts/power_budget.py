"""Quantitative Power Budget & Field Battery Autonomy Calculator for WolfDet.

Compares three realistic energy architectures for Raspberry Pi 4B + Camera Module 3:
  1. Continuous AI Baseline (always-on camera + YOLO inference, no PIR gating)
  2. PIR-Gated Pi 4B (optimized OS idle ~2.1W, HC-SR501 wake, MAX98357A SD-pin gating)
  3. Tier-2 MCU Hard-Sleep (Witty Pi 4 / ESP32 + PIR cuts Pi 4 power to ~0.015W in idle)
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wolfdet.power.energy_model import (  # noqa: E402
    DutyCycleScenario,
    EnergyProfile,
    compute_autonomy,
)


PROFILES: list[EnergyProfile] = [
    EnergyProfile(
        name="Continuous AI (Baseline)",
        idle_w=5.10,
        detecting_w=5.10,
        responding_w=6.20,
        cooldown_w=5.10,
        boot_latency_s=0.0,
        description="Camera + YOLO running 24/7 on Pi 4B CPU with no motion gating.",
    ),
    EnergyProfile(
        name="PIR-Gated Pi 4B (MVP)",
        idle_w=2.10,
        detecting_w=4.80,
        responding_w=6.20,
        cooldown_w=2.40,
        boot_latency_s=0.35,
        description="HDMI/BT/Wi-Fi off, HC-SR501 wakes camera @ 4 FPS, MAX98357A SD-gated.",
    ),
    EnergyProfile(
        name="MCU Hard-Sleep + PIR (Field)",
        idle_w=0.02,
        detecting_w=4.80,
        responding_w=6.20,
        cooldown_w=2.40,
        boot_latency_s=18.0,
        description="Witty Pi 4 / ESP32 cuts Pi 4B power completely during idle (boot trade-off).",
    ),
]

SCENARIOS: list[DutyCycleScenario] = [
    DutyCycleScenario(
        name="Typical Forest Trail (40 motion / 2 wolf events per day)",
        false_motion_events_per_day=40,
        wolf_events_per_day=2,
        detect_window_s=15.0,
        response_duration_s=12.0,
        cooldown_duration_s=30.0,
    ),
    DutyCycleScenario(
        name="High-Activity Pasture Edge (120 motion / 5 wolf events per day)",
        false_motion_events_per_day=120,
        wolf_events_per_day=5,
        detect_window_s=15.0,
        response_duration_s=12.0,
        cooldown_duration_s=30.0,
    ),
]

BATTERIES: list[tuple[str, float]] = [
    ("20,000 mAh Powerbank (74 Wh)", 74.0),
    ("12V 12Ah LiFePO4 (153.6 Wh)", 153.6),
]


def main() -> int:
    for scenario in SCENARIOS:
        print("=" * 98)
        print(f"SCENARIO: {scenario.name}")
        print("=" * 98)
        header = (
            f"{'Architecture':<30} | {'Battery Pack':<28} | {'Avg W':>6} | "
            f"{'Wh/Day':>7} | {'Runtime':>10} | {'Savings':>7} | {'Latency':>7}"
        )
        print(header)
        print("-" * 98)
        for battery_name, battery_wh in BATTERIES:
            for profile in PROFILES:
                est = compute_autonomy(
                    profile=profile,
                    scenario=scenario,
                    battery_name=battery_name,
                    battery_wh=battery_wh,
                    usable_efficiency=0.85,
                    continuous_baseline_w=5.10,
                )
                runtime_str = (
                    f"{est.runtime_days:5.1f} d"
                    if est.runtime_days >= 2.0
                    else f"{est.runtime_hours:5.1f} h"
                )
                print(
                    f"{est.profile_name:<30} | {est.battery_name:<28} | "
                    f"{est.avg_power_w:6.2f} | {est.daily_energy_wh:7.2f} | "
                    f"{runtime_str:>10} | {est.savings_vs_continuous_pct:6.1f}% | "
                    f"{est.boot_latency_s:5.1f} s"
                )
            print("-" * 98)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
