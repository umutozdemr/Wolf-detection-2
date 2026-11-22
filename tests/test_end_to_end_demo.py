"""End-to-end integration test of the 3-scenario Midterm Presentation demo."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wolfdet.audio.deterrent import AudioDeterrent
from wolfdet.camera.opencv_source import SyntheticScenarioCamera
from wolfdet.config import AppConfig
from wolfdet.detection.mock_detector import ScenarioMockDetector
from wolfdet.recorder.event_logger import EventRecorder
from wolfdet.state_machine import WolfResponseStateMachine


class TestEndToEndMidtermDemo(unittest.TestCase):
    def test_three_midterm_scenarios_execute_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = AppConfig()
            cfg.system.log_dir = tmp
            cfg.system.recording_dir = tmp
            cfg.response.enable_sound_output = False

            cam = SyntheticScenarioCamera(render_images=False)
            det = ScenarioMockDetector()
            audio = AudioDeterrent(audio_dir=Path(tmp), enable_sound_output=False, seed=123)
            rec = EventRecorder(log_dir=tmp, recording_dir=tmp, save_video_clips=False, enabled=True)
            fsm = WolfResponseStateMachine(cfg, det, audio, rec)

            cam.open()
            try:
                while (pkt := cam.read()) is not None:
                    fsm.step(pkt, motion_active=pkt.motion_detected)
            finally:
                cam.close()

            event_types = [e.event_type for e in fsm.events]
            self.assertIn("NON_TARGET_IGNORED", event_types)
            self.assertIn("PRIVACY_SUPPRESSED", event_types)
            self.assertIn("WOLF_DETERRENCE", event_types)
            # Only the wolf scenario should trigger human speech playback
            self.assertEqual(len(audio.play_history), 1)
            self.assertGreater(fsm.energy.energy_savings_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
