"""Randomized human-speech deterrence playback with GPIO amplifier power gating.

Grounded in Zanette et al. (2023) and Suraci et al. (2017):
  - Uses a pool of 8-14 calm human speech exemplars (never repeating the same clip
    back-to-back) to minimize wildlife habituation.
  - Supports pre-playback delay (0-3 s) so pre-playback behavior is captured.
  - Controls MAX98357A Class-D amplifier's Shutdown (SD) pin over GPIO so standby
    audio power draw is 0 mA.
"""

from __future__ import annotations

from pathlib import Path
import platform
import random
import subprocess
import time
from typing import Callable


DEFAULT_VIRTUAL_EXEMPLARS: tuple[str, ...] = (
    "human_de_female_calm_01.wav",
    "human_de_male_calm_02.wav",
    "human_de_conversation_03.wav",
    "human_en_female_calm_04.wav",
    "human_en_male_calm_05.wav",
    "human_de_hiking_chat_06.wav",
    "human_de_female_calm_07.wav",
    "human_de_male_calm_08.wav",
)


class AudioDeterrent:
    """Manages anti-habituation audio selection, amp power gating, and playback."""

    def __init__(
        self,
        audio_dir: str | Path = "assets/audio",
        randomize_no_repeat: bool = True,
        amp_shutdown_gpio_pin: int | None = None,
        enable_sound_output: bool = True,
        simulate_timing: bool = False,
        seed: int | None = None,
        amp_pin_callback: Callable[[bool], None] | None = None,
    ) -> None:
        self.audio_dir = Path(audio_dir)
        self.randomize_no_repeat = randomize_no_repeat
        self.amp_shutdown_gpio_pin = amp_shutdown_gpio_pin
        self.enable_sound_output = enable_sound_output
        self.simulate_timing = simulate_timing
        self._rng = random.Random(seed)
        self._amp_pin_callback = amp_pin_callback

        self._last_played: str | None = None
        self.play_history: list[str] = []
        self.amp_powered: bool = False
        self._gpio_output = None

        self._init_gpio_amp()
        self.exemplars: list[Path] = self._discover_exemplars()

    def _init_gpio_amp(self) -> None:
        if self.amp_shutdown_gpio_pin is None:
            return
        try:
            from gpiozero import OutputDevice  # type: ignore

            # MAX98357A SD pin: LOW = shutdown (0 mA), HIGH = active
            self._gpio_output = OutputDevice(
                self.amp_shutdown_gpio_pin, active_high=True, initial_value=False
            )
        except Exception:
            # Running on PC or without GPIO hardware: track logical amp state cleanly.
            self._gpio_output = None

    def _discover_exemplars(self) -> list[Path]:
        if not self.audio_dir.exists():
            return []
        files = sorted(
            p for p in self.audio_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".wav", ".mp3", ".ogg"}
        )
        return files

    def refresh_exemplars(self) -> list[Path]:
        self.exemplars = self._discover_exemplars()
        return self.exemplars

    def select_next_exemplar(self) -> str:
        """Select a human-speech exemplar while avoiding immediate repetition."""
        candidates = (
            [p.name for p in self.exemplars]
            if self.exemplars
            else list(DEFAULT_VIRTUAL_EXEMPLARS)
        )
        if len(candidates) == 1:
            choice = candidates[0]
        elif self.randomize_no_repeat and self._last_played in candidates:
            pool = [c for c in candidates if c != self._last_played]
            choice = self._rng.choice(pool)
        else:
            choice = self._rng.choice(candidates)

        self._last_played = choice
        return choice

    def set_amp_power(self, enabled: bool) -> None:
        """Power-gate the external Class-D amplifier (MAX98357A SD pin)."""
        self.amp_powered = enabled
        if self._gpio_output is not None:
            if enabled:
                self._gpio_output.on()
            else:
                self._gpio_output.off()
        if self._amp_pin_callback is not None:
            self._amp_pin_callback(enabled)

    def trigger_deterrent(self, delay_s: float = 0.0, duration_s: float = 10.0) -> str:
        """Wait optional pre-playback delay, power amp, play random speech clip, power off."""
        exemplar_name = self.select_next_exemplar()
        self.play_history.append(exemplar_name)

        if self.simulate_timing and delay_s > 0:
            time.sleep(delay_s)

        self.set_amp_power(True)
        try:
            clip_path = self.audio_dir / exemplar_name
            if self.enable_sound_output and clip_path.exists():
                self._play_file(clip_path, duration_s=duration_s)
        finally:
            self.set_amp_power(False)

        return exemplar_name

    def _play_file(self, clip_path: Path, duration_s: float) -> None:
        system = platform.system().lower()
        if system == "windows" and clip_path.suffix.lower() == ".wav":
            try:
                import winsound

                winsound.PlaySound(str(clip_path), winsound.SND_FILENAME)
                return
            except Exception:
                return

        if system == "linux":
            cmd = ["aplay", "-q", str(clip_path)]
            try:
                subprocess.run(cmd, timeout=max(2.0, duration_s + 2.0), check=False)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

    def close(self) -> None:
        self.set_amp_power(False)
        if self._gpio_output is not None:
            self._gpio_output.close()
            self._gpio_output = None
