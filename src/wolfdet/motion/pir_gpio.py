"""Hardware PIR motion sensor trigger (HC-SR501 / AM312) for Raspberry Pi 4B."""

from __future__ import annotations

from typing import Any

from wolfdet.motion.base import MotionTrigger


class GPIOPIRTrigger(MotionTrigger):
    """Reads digital 3.3V motion interrupts from an HC-SR501 / AM312 PIR sensor.

    Wiring (Raspberry Pi 4 Model B):
        VCC -> Physical Pin 2 or 4 (5V)
        GND -> Physical Pin 6 (GND)
        OUT -> Physical Pin 11 (BCM GPIO 17, 3.3V logic safe)
    """

    def __init__(self, gpio_pin: int = 17, queue_len: int = 1) -> None:
        self.gpio_pin = gpio_pin
        self._sensor = None
        try:
            from gpiozero import MotionSensor  # type: ignore

            self._sensor = MotionSensor(gpio_pin, queue_len=queue_len)
        except ImportError as exc:
            raise RuntimeError(
                "gpiozero is required for GPIOPIRTrigger on Raspberry Pi. "
                "Install requirements-pi.txt or switch motion.backend to 'software'."
            ) from exc

    def check_motion(self, frame: Any = None) -> bool:
        if self._sensor is None:
            return False
        return bool(self._sensor.motion_detected)

    def close(self) -> None:
        if self._sensor is not None:
            self._sensor.close()
            self._sensor = None
