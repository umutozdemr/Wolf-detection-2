"""Unit tests for randomized anti-habituation audio pool and GPIO amp gating."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wolfdet.audio.deterrent import AudioDeterrent


class TestAudioDeterrent(unittest.TestCase):
    def test_no_immediate_repeat_in_random_pool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            deterrent = AudioDeterrent(
                audio_dir=Path(tmp) / "none",
                randomize_no_repeat=True,
                enable_sound_output=False,
                seed=7,
            )
            chosen = [deterrent.select_next_exemplar() for _ in range(40)]
            for prev, curr in zip(chosen, chosen[1:]):
                self.assertNotEqual(prev, curr)

    def test_amp_power_gating_turns_off_after_playback(self) -> None:
        pin_states: list[bool] = []
        with tempfile.TemporaryDirectory() as tmp:
            deterrent = AudioDeterrent(
                audio_dir=Path(tmp) / "none",
                enable_sound_output=False,
                amp_pin_callback=pin_states.append,
                seed=1,
            )
            self.assertFalse(deterrent.amp_powered)
            deterrent.trigger_deterrent(delay_s=0.0, duration_s=1.0)
            self.assertEqual(pin_states, [True, False])
            self.assertFalse(deterrent.amp_powered)


if __name__ == "__main__":
    unittest.main()
