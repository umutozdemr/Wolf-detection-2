"""Energy consumption tracker and field battery-autonomy model."""

from __future__ import annotations

from dataclasses import dataclass, field

from wolfdet.config import PowerModelConfig
from wolfdet.types import SystemState


@dataclass
class EnergyProfile:
    """Named power architecture used for midterm/final trade-off analysis."""

    name: str
    idle_w: float
    detecting_w: float
    responding_w: float
    cooldown_w: float
    boot_latency_s: float
    description: str


@dataclass
class DutyCycleScenario:
    """Daily wildlife activity profile in a forest deployment."""

    name: str
    false_motion_events_per_day: int
    wolf_events_per_day: int
    detect_window_s: float = 15.0
    response_duration_s: float = 12.0
    cooldown_duration_s: float = 30.0


@dataclass
class BatteryAutonomyEstimate:
    """Computed energy metrics for a given profile and battery pack."""

    profile_name: str
    battery_name: str
    usable_wh: float
    avg_power_w: float
    daily_energy_wh: float
    runtime_hours: float
    runtime_days: float
    savings_vs_continuous_pct: float
    boot_latency_s: float


def compute_autonomy(
    profile: EnergyProfile,
    scenario: DutyCycleScenario,
    battery_name: str,
    battery_wh: float,
    usable_efficiency: float = 0.85,
    continuous_baseline_w: float = 5.10,
) -> BatteryAutonomyEstimate:
    """Calculate average power, daily Wh, runtime, and savings vs continuous AI."""
    seconds_per_day = 86_400.0
    total_motion_events = scenario.false_motion_events_per_day + scenario.wolf_events_per_day

    detect_s = min(seconds_per_day, total_motion_events * scenario.detect_window_s)
    respond_s = min(seconds_per_day - detect_s, scenario.wolf_events_per_day * scenario.response_duration_s)
    cooldown_s = min(
        seconds_per_day - detect_s - respond_s,
        scenario.wolf_events_per_day * scenario.cooldown_duration_s,
    )
    idle_s = max(0.0, seconds_per_day - detect_s - respond_s - cooldown_s)

    daily_joules = (
        idle_s * profile.idle_w
        + detect_s * profile.detecting_w
        + respond_s * profile.responding_w
        + cooldown_s * profile.cooldown_w
    )
    daily_wh = daily_joules / 3600.0
    avg_power_w = daily_wh / 24.0
    usable_wh = battery_wh * usable_efficiency
    runtime_hours = usable_wh / avg_power_w if avg_power_w > 0 else float("inf")
    runtime_days = runtime_hours / 24.0
    savings_pct = max(0.0, (1.0 - avg_power_w / continuous_baseline_w) * 100.0)

    return BatteryAutonomyEstimate(
        profile_name=profile.name,
        battery_name=battery_name,
        usable_wh=round(usable_wh, 2),
        avg_power_w=round(avg_power_w, 3),
        daily_energy_wh=round(daily_wh, 2),
        runtime_hours=round(runtime_hours, 1),
        runtime_days=round(runtime_days, 2),
        savings_vs_continuous_pct=round(savings_pct, 1),
        boot_latency_s=profile.boot_latency_s,
    )


@dataclass
class RuntimeEnergyTracker:
    """Tracks live state dwell time and cumulative energy during execution/demos."""

    config: PowerModelConfig = field(default_factory=PowerModelConfig)
    state_seconds: dict[SystemState, float] = field(
        default_factory=lambda: {state: 0.0 for state in SystemState}
    )
    total_joules: float = 0.0
    baseline_joules: float = 0.0

    def power_for_state(self, state: SystemState) -> float:
        mapping = {
            SystemState.IDLE: self.config.idle_w,
            SystemState.DETECTING: self.config.detecting_w,
            SystemState.RESPONDING: self.config.responding_w,
            SystemState.COOLDOWN: self.config.cooldown_w,
        }
        return mapping[state]

    def record_interval(self, state: SystemState, duration_s: float) -> float:
        """Accumulate energy consumed over duration_s in the given state."""
        dt = max(0.0, duration_s)
        watts = self.power_for_state(state)
        self.state_seconds[state] += dt
        self.total_joules += watts * dt
        self.baseline_joules += self.config.detecting_w * dt
        return watts

    @property
    def total_seconds(self) -> float:
        return sum(self.state_seconds.values())

    @property
    def average_power_w(self) -> float:
        total_s = self.total_seconds
        if total_s <= 0:
            return self.config.idle_w
        return self.total_joules / total_s

    @property
    def energy_savings_pct(self) -> float:
        if self.baseline_joules <= 0:
            return 0.0
        return max(0.0, (1.0 - self.total_joules / self.baseline_joules) * 100.0)

    def projected_battery_hours(self) -> float:
        usable_wh = self.config.battery_capacity_wh * self.config.usable_efficiency
        avg_w = self.average_power_w
        return usable_wh / avg_w if avg_w > 0 else 0.0

    def summary(self) -> dict[str, float]:
        return {
            "total_seconds": round(self.total_seconds, 2),
            "average_power_w": round(self.average_power_w, 3),
            "total_mwh": round((self.total_joules / 3600.0) * 1000.0, 3),
            "savings_vs_continuous_pct": round(self.energy_savings_pct, 1),
            "projected_battery_hours": round(self.projected_battery_hours(), 1),
        }
