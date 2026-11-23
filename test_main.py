"""Simple unit tests for main.py."""

from pathlib import Path
import tempfile
import unittest

import main as app


class TestWolfDet(unittest.TestCase):
    def test_random_sound_does_not_repeat_back_to_back(self):
        last = None
        for _ in range(25):
            chosen = app.pick_random_sound(last)
            self.assertNotEqual(chosen, last)
            last = chosen

    def test_wolf_needs_3_frames_to_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "events.csv"
            action, streak, sound = app.process_labels([("wolf", 0.85)], 0, silent=True, log_file=log_file)
            self.assertIsNone(sound)
            self.assertEqual(streak, 1)

            action, streak, sound = app.process_labels([("wolf", 0.88)], streak, silent=True, log_file=log_file)
            self.assertIsNone(sound)
            self.assertEqual(streak, 2)

            action, streak, sound = app.process_labels([("wolf", 0.91)], streak, silent=True, log_file=log_file)
            self.assertEqual(action, "WOLF_TRIGGERED")
            self.assertIsNotNone(sound)
            self.assertTrue(log_file.exists())

    def test_person_is_ignored_and_resets_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "events.csv"
            action, streak, sound = app.process_labels([("person", 0.92)], 2, silent=True, log_file=log_file)
            self.assertEqual(action, "PERSON_IGNORED")
            self.assertEqual(streak, 0)
            self.assertIsNone(sound)

    def test_deer_does_not_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "events.csv"
            action, streak, sound = app.process_labels([("deer", 0.90)], 1, silent=True, log_file=log_file)
            self.assertEqual(action, "NO_WOLF")
            self.assertEqual(streak, 0)
            self.assertIsNone(sound)


if __name__ == "__main__":
    unittest.main()
