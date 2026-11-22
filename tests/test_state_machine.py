"""Unit tests for WolfResponseStateMachine (FSM transitions, M-of-N voting, GDPR guard)."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wolfdet.audio.deterrent import AudioDeterrent
from wolfdet.config import AppConfig
from wolfdet.detection.base import WolfDetector
from wolfdet.recorder.event_logger import EventRecorder
from wolfdet.state_machine import WolfResponseStateMachine
from wolfdet.types import BoundingBox, Detection, FramePacket, SystemState


class _SequenceDetector(WolfDetector):
    def __init__(self, outputs: list[list[Detection]]) -> None:
        self._outputs = iter(outputs)

    def detect(self, packet: FramePacket) -> list[Detection]:
        return next(self._outputs, [])


class TestWolfResponseStateMachine(unittest.TestCase):
    def _make_fsm(self, outputs: list[list[Detection]], tmpdir: str) -> tuple[WolfResponseStateMachine, AudioDeterrent, EventRecorder]:
        cfg = AppConfig()
        cfg.motion.detect_window_s = 10.0
        cfg.detection.confirm_hits = 3
        cfg.detection.confirm_window = 5
        cfg.response.cooldown_s = 15.0
        cfg.response.enable_sound_output = False
        cfg.system.log_dir = tmpdir
        cfg.system.recording_dir = tmpdir

        audio = AudioDeterrent(
            audio_dir=Path(tmpdir) / "empty_audio",
            enable_sound_output=False,
            seed=42,
        )
        recorder = EventRecorder(
            log_dir=tmpdir,
            recording_dir=tmpdir,
            save_video_clips=False,
            enabled=True,
        )
        fsm = WolfResponseStateMachine(
            config=cfg,
            detector=_SequenceDetector(outputs),
            audio=audio,
            recorder=recorder,
        )
        return fsm, audio, recorder

    def test_single_false_positive_does_not_trigger_deterrent(self) -> None:
        wolf = [Detection("wolf", 0.85, BoundingBox(10, 10, 100, 100))]
        deer = [Detection("deer", 0.90, BoundingBox(20, 20, 120, 120))]
        with tempfile.TemporaryDirectory() as tmp:
            fsm, audio, _ = self._make_fsm([wolf, deer, deer, deer], tmp)
            # Wake up on motion
            r1 = fsm.step(FramePacket(1, 0.0), motion_active=True)
            self.assertEqual(r1.state, SystemState.DETECTING)

            # 1 wolf hit + 3 deer frames -> never reaches 3/5 confirmation -> times out to IDLE
            fsm.step(FramePacket(2, 2.0), motion_active=False)
            fsm.step(FramePacket(3, 5.0), motion_active=False)
            fsm.step(FramePacket(4, 8.0), motion_active=False)
            r_end = fsm.step(FramePacket(5, 11.0), motion_active=False)

            self.assertEqual(r_end.state, SystemState.IDLE)
            self.assertEqual(len(audio.play_history), 0)

    def test_confirmed_wolf_triggers_playback_and_cooldown(self) -> None:
        wolf = [Detection("wolf", 0.91, BoundingBox(50, 50, 200, 200))]
        with tempfile.TemporaryDirectory() as tmp:
            fsm, audio, recorder = self._make_fsm([wolf, wolf, wolf], tmp)

            fsm.step(FramePacket(1, 10.0), motion_active=True)
            fsm.step(FramePacket(2, 11.0), motion_active=False)
            fsm.step(FramePacket(3, 12.0), motion_active=False)
            r_confirm = fsm.step(FramePacket(4, 13.0), motion_active=False)

            self.assertTrue(r_confirm.deterrent_triggered)
            self.assertIsNotNone(r_confirm.audio_exemplar)
            self.assertEqual(len(audio.play_history), 1)
            self.assertEqual(fsm.state, SystemState.COOLDOWN)
            self.assertTrue(recorder.jsonl_path.exists())
            self.assertTrue(recorder.csv_path.exists())

            # Still in cooldown at t=20 (< 13 + 15)
            r_cool = fsm.step(FramePacket(5, 20.0), motion_active=True)
            self.assertEqual(r_cool.state, SystemState.COOLDOWN)

            # Exits cooldown to IDLE at t=29 (>= 28)
            r_idle = fsm.step(FramePacket(6, 29.0), motion_active=False)
            self.assertEqual(r_idle.state, SystemState.IDLE)

    def test_gdpr_privacy_guard_wipes_buffer_and_blocks_audio(self) -> None:
        person = [Detection("person", 0.95, BoundingBox(100, 50, 220, 350))]
        with tempfile.TemporaryDirectory() as tmp:
            fsm, audio, recorder = self._make_fsm([person], tmp)
            fsm.step(FramePacket(1, 0.0), motion_active=True)
            recorder.push_frame(FramePacket(99, 0.5))
            self.assertEqual(recorder.buffered_frame_count, 1)

            r_priv = fsm.step(FramePacket(2, 1.0), motion_active=False)
            self.assertTrue(r_priv.privacy_suppressed)
            self.assertFalse(r_priv.deterrent_triggered)
            self.assertEqual(recorder.buffered_frame_count, 0)
            self.assertEqual(len(audio.play_history), 0)
            self.assertIsNotNone(r_priv.event_record)
            self.assertEqual(r_priv.event_record.event_type, "PRIVACY_SUPPRESSED")


if __name__ == "__main__":
    unittest.main()
