"""Unit tests for energy consumption model and battery autonomy projections."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wolfdet.power.energy_model import (
    DutyCycleScenario,
    EnergyProfile,
    RuntimeEnergyTracker,
    compute_autonomy,
)
from wolfdet.types import SystemState


class TestEnergyModel(unittest.TestCase):
    def test_pir_gating_reduces_daily_energy_over_continuous_ai(self) -> None:
        scenario = DutyCycleScenario("Forest", false_motion_events_per_day=40, wolf_events_per_day=2)
        continuous = EnergyProfile("Continuous", 5.1, 5.1, 6.2, 5.1, 0.0, "")
        pir_gated = EnergyProfile("PIR-Gated", 2.1, 4.8, 6.2, 2.4, 0.35, "")

        est_cont = compute_autonomy(continuous, scenario, "74Wh", 74.0)
        est_pir = compute_autonomy(pir_gated, scenario, "74Wh", 74.0)

        self.assertLess(est_pir.daily_energy_wh, est_cont.daily_energy_wh)
        self.assertGreater(est_pir.runtime_hours, est_cont.runtime_hours * 2.0)
        self.assertGreater(est_pir.savings_vs_continuous_pct, 50.0)

    def test_runtime_tracker_computes_savings(self) -> None:
        tracker = RuntimeEnergyTracker()
        tracker.record_interval(SystemState.IDLE, 80.0)
        tracker.record_interval(SystemState.DETECTING, 20.0)
        self.assertGreater(tracker.energy_savings_pct, 40.0)
        self.assertLess(tracker.average_power_w, tracker.config.detecting_w)


if __name__ == "__main__":
    unittest.main()
