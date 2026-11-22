"""OpenCV live heads-up display and headless CLI telemetry renderer."""

from __future__ import annotations

from wolfdet.power.energy_model import RuntimeEnergyTracker
from wolfdet.types import FramePacket, StepResult, SystemState


STATE_COLORS_BGR: dict[SystemState, tuple[int, int, int]] = {
    SystemState.IDLE: (130, 130, 130),
    SystemState.DETECTING: (0, 190, 255),
    SystemState.RESPONDING: (40, 40, 230),
    SystemState.COOLDOWN: (210, 150, 40),
}


class DemoHUD:
    """Renders real-time FSM state, detections, and energy telemetry."""

    def __init__(self, window_name: str = "WolfDet - Energy-Efficient ABR Prototype", show_gui: bool = True) -> None:
        self.window_name = window_name
        self.show_gui = show_gui
        self._cv2 = None
        if self.show_gui:
            try:
                import cv2  # type: ignore

                self._cv2 = cv2
            except ImportError:
                self._cv2 = None

    def render(
        self,
        packet: FramePacket,
        result: StepResult,
        energy: RuntimeEnergyTracker,
    ) -> bool:
        """Print CLI telemetry and optionally render OpenCV window.

        Returns False if the user pressed 'q' to quit the GUI window.
        """
        self._print_cli_line(packet, result, energy)

        if self._cv2 is None or packet.image is None:
            return True

        cv2 = self._cv2
        frame = packet.image.copy()
        h, w = frame.shape[:2]

        # Top telemetry bar
        bar_color = STATE_COLORS_BGR.get(result.state, (100, 100, 100))
        cv2.rectangle(frame, (0, 0), (w, 56), (22, 26, 30), -1)
        cv2.rectangle(frame, (0, 0), (14, 56), bar_color, -1)

        header = f"STATE: {result.state.value}  |  POWER: {result.estimated_power_w:.2f} W  |  SAVINGS: {energy.energy_savings_pct:.1f}%"
        cv2.putText(frame, header, (22, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 245, 245), 2)
        cv2.putText(frame, result.status_message[:74], (22, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (190, 215, 210), 1)

        # Draw detections (mask person bounding box to illustrate GDPR privacy guard)
        for det in result.detections:
            box = det.bbox
            if det.label == "person":
                cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), (45, 45, 45), -1)
                cv2.putText(
                    frame,
                    "GDPR PRIVACY REDACTED",
                    (box.x1 + 6, max(72, box.y1 + 24)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (120, 220, 255),
                    2,
                )
            else:
                color = (40, 50, 240) if det.label == "wolf" else (70, 210, 120)
                cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), color, 2)
                cv2.putText(
                    frame,
                    f"{det.label.upper()} {det.confidence:.2f}",
                    (box.x1, max(72, box.y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    color,
                    2,
                )

        if result.deterrent_triggered and result.audio_exemplar:
            cv2.rectangle(frame, (18, 66), (w - 18, 104), (35, 35, 195), -1)
            cv2.putText(
                frame,
                f"AUDIO DETERRENT ACTIVE: {result.audio_exemplar}",
                (28, 91),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.56,
                (255, 255, 255),
                2,
            )

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(350 if packet.scenario_tag != "picamera3_live" else 1) & 0xFF
        return key != ord("q")

    def _print_cli_line(
        self,
        packet: FramePacket,
        result: StepResult,
        energy: RuntimeEnergyTracker,
    ) -> None:
        tag = f" [{packet.scenario_tag}]" if packet.scenario_tag else ""
        print(
            f"[F{packet.frame_id:03d}]{tag:<24} "
            f"STATE={result.state.value:<10} "
            f"PWR={result.estimated_power_w:4.2f}W "
            f"INF={result.inference_ms:5.1f}ms "
            f"SAVE={energy.energy_savings_pct:4.1f}% | {result.status_message}"
        )

    def close(self) -> None:
        if self._cv2 is not None:
            self._cv2.destroyAllWindows()
