"""Motion gating providers (PIR hardware & software fallback)."""

from wolfdet.motion.base import MotionTrigger
from wolfdet.motion.pir_gpio import GPIOPIRTrigger
from wolfdet.motion.software_motion import MockMotionTrigger, SoftwareMotionTrigger

__all__ = ["MotionTrigger", "GPIOPIRTrigger", "SoftwareMotionTrigger", "MockMotionTrigger"]
