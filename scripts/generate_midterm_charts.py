"""Pure-Python SVG chart generator for WolfDet Midterm Presentation slides.

Generates crisp, vector charts under docs/assets/ with zero external dependencies:
  1. docs/assets/power_by_state.svg      - Power draw (W) across FSM states on RPi 4B + Cam Mod 3
  2. docs/assets/energy_comparison.svg   - Daily energy (Wh/day) & battery autonomy comparison
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


def write_power_by_state_svg(out_path: Path) -> None:
    bars = [
        ("MCU Hard-Sleep\n(Tier-2 Idle)", 0.02, "#10b981", "0.02 W"),
        ("Pi 4B Idle\n(PIR Active)", 2.10, "#3b82f6", "2.10 W"),
        ("Cooldown\n(Amp Off)", 2.40, "#6366f1", "2.40 W"),
        ("AI Detection\n(Cam3 + 4 FPS)", 4.80, "#f59e0b", "4.80 W"),
        ("Wolf Response\n(Speech + Rec)", 6.20, "#ef4444", "6.20 W"),
    ]
    width, height = 820, 420
    margin_left, margin_bottom, chart_h = 85, 85, 250
    max_w = 7.0
    bar_w = 96
    gap = 42

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="14"/>',
        '<text x="410" y="38" text-anchor="middle" fill="#f8fafc" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700">Estimated Power Draw by System State (RPi 4B + Camera Module 3)</text>',
        '<text x="410" y="60" text-anchor="middle" fill="#94a3b8" font-family="Segoe UI, Arial, sans-serif" font-size="12">MAX98357A Amp SD-pin power gated (0 mA standby) | HDMI, Wi-Fi &amp; Bluetooth disabled</text>',
    ]

    # Grid lines
    for tick in range(0, 8):
        y = height - margin_bottom - (tick / max_w) * chart_h
        svg.append(f'<line x1="{margin_left}" y1="{y:.1f}" x2="{width - 35}" y2="{y:.1f}" stroke="#1e293b" stroke-width="1"/>')
        svg.append(f'<text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" fill="#94a3b8" font-family="Segoe UI, Arial, sans-serif" font-size="12">{tick} W</text>')

    for idx, (label, watts, color, val_txt) in enumerate(bars):
        x = margin_left + 24 + idx * (bar_w + gap)
        bh = max(4.0, (watts / max_w) * chart_h)
        y = height - margin_bottom - bh
        svg.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{bh:.1f}" fill="{color}" rx="6"/>')
        svg.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" fill="#f8fafc" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">{val_txt}</text>')
        for line_i, line in enumerate(label.split("\n")):
            svg.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{height - margin_bottom + 22 + line_i * 16}" '
                f'text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Arial, sans-serif" font-size="12">{line}</text>'
            )

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def write_energy_comparison_svg(out_path: Path) -> None:
    scenario = DutyCycleScenario(
        name="Typical Forest Trail",
        false_motion_events_per_day=40,
        wolf_events_per_day=2,
    )
    profiles = [
        (EnergyProfile("Continuous AI (24/7)", 5.10, 5.10, 6.20, 5.10, 0.0, ""), "#ef4444"),
        (EnergyProfile("PIR-Gated Pi 4B (MVP)", 2.10, 4.80, 6.20, 2.40, 0.35, ""), "#3b82f6"),
        (EnergyProfile("MCU Hard-Sleep + PIR", 0.02, 4.80, 6.20, 2.40, 18.0, ""), "#10b981"),
    ]
    estimates = [
        (compute_autonomy(p, scenario, "12V 12Ah LiFePO4 (153.6 Wh)", 153.6), color)
        for p, color in profiles
    ]

    width, height = 820, 390
    max_wh = 130.0
    left = 235
    bar_max_w = 430

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="14"/>',
        '<text x="410" y="38" text-anchor="middle" fill="#f8fafc" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700">Daily Energy Consumption &amp; Battery Autonomy (40 Motion + 2 Wolf / Day)</text>',
        '<text x="410" y="60" text-anchor="middle" fill="#94a3b8" font-family="Segoe UI, Arial, sans-serif" font-size="12">12V 12Ah LiFePO4 Pack (130.6 Wh usable @ 85% efficiency)</text>',
    ]

    for idx, (est, color) in enumerate(estimates):
        y = 105 + idx * 88
        bw = max(12.0, (est.daily_energy_wh / max_wh) * bar_max_w)
        svg.append(f'<text x="{left - 14}" y="{y + 18}" text-anchor="end" fill="#e2e8f0" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="600">{est.profile_name}</text>')
        svg.append(f'<text x="{left - 14}" y="{y + 38}" text-anchor="end" fill="#94a3b8" font-family="Segoe UI, Arial, sans-serif" font-size="11">Wake latency: {est.boot_latency_s:.1f} s</text>')
        svg.append(f'<rect x="{left}" y="{y}" width="{bar_max_w}" height="40" fill="#1e293b" rx="6"/>')
        svg.append(f'<rect x="{left}" y="{y}" width="{bw:.1f}" height="40" fill="{color}" rx="6"/>')

        runtime_txt = f"{est.runtime_days:.1f} days" if est.runtime_days >= 2 else f"{est.runtime_hours:.1f} hrs"
        detail = f"{est.daily_energy_wh:.1f} Wh/day  |  {runtime_txt}  (-{est.savings_vs_continuous_pct:.0f}%)"
        svg.append(f'<text x="{left + 12}" y="{y + 60}" fill="#cbd5e1" font-family="Segoe UI, Arial, sans-serif" font-size="12">{detail}</text>')

    svg.append("</svg>")
    out_path.write_text("\n".join(svg), encoding="utf-8")


def main() -> int:
    assets_dir = ROOT / "docs" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    p1 = assets_dir / "power_by_state.svg"
    p2 = assets_dir / "energy_comparison.svg"
    write_power_by_state_svg(p1)
    write_energy_comparison_svg(p2)
    print(f"Generated: {p1}")
    print(f"Generated: {p2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
