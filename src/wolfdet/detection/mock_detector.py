"""Scenario-driven detector for repeatable Midterm demos and automated tests."""

from __future__ import annotations

from wolfdet.detection.base import WolfDetector
from wolfdet.types import BoundingBox, Detection, FramePacket


class ScenarioMockDetector(WolfDetector):
    """Maps SyntheticScenarioCamera tags to realistic wildlife detection outputs."""

    def __init__(self, custom_script: dict[str, list[Detection]] | None = None) -> None:
        self._script = custom_script or {
            "deer_non_target": [
                Detection("deer", 0.88, BoundingBox(210, 175, 430, 355)),
            ],
            "human_hiker_gdpr": [
                Detection("person", 0.93, BoundingBox(255, 110, 385, 390)),
            ],
            "wolf_confirmed": [
                Detection("wolf", 0.87, BoundingBox(180, 200, 445, 365)),
            ],
        }

    def detect(self, packet: FramePacket) -> list[Detection]:
        return list(self._script.get(packet.scenario_tag, []))
