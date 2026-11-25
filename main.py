"""
Simple Energy-Efficient Wolf Detection & Human-Speech Response System
Hardware: Raspberry Pi 4B (4GB) + Raspberry Pi Camera Module 3

How it works:
  1. Wait for motion (PIR sensor on Pi, or simple frame difference on PC)
  2. Run YOLO detection at low FPS (4 FPS) to save power
  3. Ignore humans (privacy/GDPR) and non-target animals (deer, fox, dog)
  4. If a wolf is seen in 3 frames in a row -> play a random calm human voice clip
  5. Log the event to events.csv and wait during cooldown
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path
import platform
import random
import subprocess
import time

# --- Simple settings ---
CONF_THRESHOLD = 0.60      # Minimum detection confidence
CONFIRM_FRAMES = 3         # Wolf must be seen in 3 frames to avoid false alarms
DETECT_FPS = 4             # Low FPS saves Raspberry Pi 4 CPU & battery
DETECT_WINDOW_SEC = 15     # Stop AI after 15s if no wolf is found
COOLDOWN_SEC = 30          # Wait 30s after playing sound
PRE_PLAY_DELAY_SEC = 2     # Small delay before sound (Zanette 2023 / Suraci 2017)

PIR_PIN = 17               # HC-SR501 PIR sensor OUT -> GPIO 17
AMP_PIN = 27               # MAX98357A amp shutdown pin -> GPIO 27 (LOW = 0mA)
SOUNDS_DIR = Path("sounds")
LOG_FILE = Path("events.csv")

DEFAULT_SOUNDS = [
    "human_voice_1.wav",
    "human_voice_2.wav",
    "human_voice_3.wav",
    "human_voice_4.wav",
    "human_voice_5.wav",
]


def pick_random_sound(last_sound=None):
    """Pick a random human speech .wav file without repeating the last one."""
    files = sorted(p.name for p in SOUNDS_DIR.glob("*.wav")) if SOUNDS_DIR.exists() else []
    pool = files if files else DEFAULT_SOUNDS
    if len(pool) > 1 and last_sound in pool:
        pool = [s for s in pool if s != last_sound]
    return random.choice(pool)


def play_sound(sound_name, amp_device=None, silent=False):
    """Turn on amp (on Pi), play the .wav clip, then turn amp back off."""
    if amp_device is not None:
        amp_device.on()
    try:
        sound_path = SOUNDS_DIR / sound_name
        if silent or not sound_path.exists():
            print(f"  [AUDIO] Playing: {sound_name}")
            return
        if platform.system() == "Windows":
            import winsound
            winsound.PlaySound(str(sound_path), winsound.SND_FILENAME)
        else:
            subprocess.run(["aplay", "-q", str(sound_path)], check=False)
    finally:
        if amp_device is not None:
            amp_device.off()


def log_event(event_type, label, confidence, sound_name="", log_file=LOG_FILE):
    """Append one row to events.csv."""
    with log_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["time", "event", "label", "confidence", "sound"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type,
            label,
            round(confidence, 2),
            sound_name,
        ])


def check_frame_motion(prev_gray, frame):
    """Simple software motion check using frame difference (used on PC instead of PIR)."""
    import cv2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (15, 15), 0)
    if prev_gray is None:
        return True, gray
    diff = cv2.absdiff(prev_gray, gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    moved_pixels = cv2.countNonZero(thresh)
    return (moved_pixels / thresh.size) > 0.01, gray


def process_labels(labels, wolf_streak, last_sound=None, amp_device=None, silent=False, log_file=LOG_FILE):
    """
    Core decision logic on one frame's detections:
    labels = list of (name, confidence)
    Returns: (action, new_wolf_streak, played_sound)
    """
    # 1. Privacy rule (GDPR): never record or trigger if a person is in frame
    for name, conf in labels:
        if name == "person" and conf >= CONF_THRESHOLD:
            log_event("PERSON_IGNORED", "person", conf, log_file=log_file)
            return "PERSON_IGNORED", 0, None

    # 2. Check for wolf
    wolf_confs = [conf for name, conf in labels if name == "wolf" and conf >= CONF_THRESHOLD]
    if wolf_confs:
        wolf_streak += 1
        best_conf = max(wolf_confs)
        if wolf_streak >= CONFIRM_FRAMES:
            sound = pick_random_sound(last_sound)
            play_sound(sound, amp_device=amp_device, silent=silent)
            log_event("WOLF_DETERRENT", "wolf", best_conf, sound, log_file=log_file)
            return "WOLF_TRIGGERED", 0, sound
        return f"WOLF_CHECK ({wolf_streak}/{CONFIRM_FRAMES})", wolf_streak, None

    # 3. No wolf in this frame
    return "NO_WOLF", 0, None


def run_demo(silent=False, log_file=LOG_FILE):
    """Simple 3-case demo for the Midterm Presentation (works with zero extra packages)."""
    print("=== WolfDet Midterm Demo ===")
    print("Scenarios: 1) Deer (ignore) -> 2) Person (GDPR ignore) -> 3) Wolf (play human speech)\n")

    scenarios = [
        ("IDLE", []),
        ("DEER_PASSING", [("deer", 0.88)]),
        ("DEER_PASSING", [("deer", 0.85)]),
        ("HUMAN_HIKER", [("person", 0.93)]),
        ("WOLF_FRAME_1", [("wolf", 0.82)]),
        ("WOLF_FRAME_2", [("wolf", 0.86)]),
        ("WOLF_FRAME_3", [("wolf", 0.91)]),
    ]

    wolf_streak = 0
    last_sound = None
    for i, (step_name, labels) in enumerate(scenarios, start=1):
        if not labels:
            print(f"[{i}] {step_name:<14} -> IDLE (sleeping, ~2.1 W)")
            continue
        action, wolf_streak, played = process_labels(
            labels, wolf_streak, last_sound=last_sound, silent=silent, log_file=log_file
        )
        if played:
            last_sound = played
            print(f"[{i}] {step_name:<14} -> {action} | Sound: {played} | Entering {COOLDOWN_SEC}s cooldown")
        else:
            print(f"[{i}] {step_name:<14} -> {action} | Labels: {labels}")

    print(f"\nDone! Events saved to {log_file}")


def run_camera(source="0", model_path="yolov8n.pt", use_pi=False, proxy_wolf=False,
               silent=False, log_file=LOG_FILE):
    """Run live detection on webcam, video file, or Raspberry Pi Camera Module 3."""
    import cv2
    from ultralytics import YOLO

    model = YOLO(model_path)

    # Setup camera & optional Raspberry Pi GPIO
    pir = None
    amp = None
    picam = None
    cap = None

    if use_pi:
        from gpiozero import MotionSensor, OutputDevice
        from picamera2 import Picamera2

        pir = MotionSensor(PIR_PIN)
        amp = OutputDevice(AMP_PIN, initial_value=False)
        picam = Picamera2()
        picam.configure(picam.create_video_configuration(main={"size": (640, 480), "format": "RGB888"}))
        picam.start()
    else:
        src = int(source) if source.isdigit() else source
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera/video: {source}")

    state = "IDLE"
    detect_until = 0.0
    cooldown_until = 0.0
    wolf_streak = 0
    last_sound = None
    prev_gray = None

    print(f"Running live mode | Pi={use_pi} | Model={model_path} | Press 'q' to quit")
    try:
        while True:
            now = time.time()

            # Read frame
            if use_pi:
                frame = picam.capture_array()
                motion = pir.motion_detected
            else:
                ok, frame = cap.read()
                if not ok:
                    break
                motion, prev_gray = check_frame_motion(prev_gray, frame)

            # Simple state machine: IDLE -> DETECTING -> COOLDOWN
            if state == "COOLDOWN":
                if now >= cooldown_until:
                    state = "IDLE"
                status = f"COOLDOWN ({max(0, cooldown_until - now):.0f}s)"
            elif state == "IDLE":
                if motion:
                    state = "DETECTING"
                    detect_until = now + DETECT_WINDOW_SEC
                    wolf_streak = 0
                status = "IDLE (waiting for motion)"
            else:  # DETECTING
                results = model.predict(frame, conf=CONF_THRESHOLD, imgsz=416, verbose=False)
                labels = []
                for box in results[0].boxes:
                    cls_name = str(results[0].names[int(box.cls[0])]).lower()
                    if proxy_wolf and cls_name == "dog":
                        cls_name = "wolf"
                    conf = float(box.conf[0])
                    labels.append((cls_name, conf))

                    # Draw simple box on PC window
                    if not use_pi:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        color = (0, 0, 255) if cls_name == "wolf" else (0, 200, 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{cls_name} {conf:.2f}", (x1, max(20, y1 - 8)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                action, wolf_streak, played = process_labels(
                    labels, wolf_streak, last_sound=last_sound, amp_device=amp,
                    silent=silent, log_file=log_file
                )
                status = f"DETECTING | {action}"

                if played:
                    last_sound = played
                    if PRE_PLAY_DELAY_SEC > 0 and use_pi:
                        time.sleep(PRE_PLAY_DELAY_SEC)
                    state = "COOLDOWN"
                    cooldown_until = time.time() + COOLDOWN_SEC
                elif now >= detect_until:
                    state = "IDLE"

            if not use_pi:
                cv2.putText(frame, status, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.imshow("WolfDet", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            time.sleep(1.0 / DETECT_FPS)
    finally:
        if cap is not None:
            cap.release()
            cv2.destroyAllWindows()
        if picam is not None:
            picam.stop()
        if amp is not None:
            amp.off()


def main():
    parser = argparse.ArgumentParser(description="Simple Wolf Detection & Response System")
    parser.add_argument("--demo", action="store_true", help="Run simple 3-scenario demo (default)")
    parser.add_argument("--source", default=None, help="Webcam index ('0') or video file path")
    parser.add_argument("--model", default="yolov8n.pt", help="Path to YOLO model")
    parser.add_argument("--pi", action="store_true", help="Run on Raspberry Pi 4B + Camera Module 3 + PIR")
    parser.add_argument("--proxy-wolf", action="store_true", help="Treat COCO 'dog' as 'wolf' for quick testing")
    parser.add_argument("--silent", action="store_true", help="Do not play audio out loud")
    parser.add_argument("--log-file", type=Path, default=LOG_FILE,
                        help="Event CSV path (default: events.csv)")
    args = parser.parse_args()

    if not args.log_file.parent.is_dir():
        parser.error(f"Log directory does not exist: {args.log_file.parent}")
    if args.log_file.is_dir():
        parser.error(f"Log path is a directory: {args.log_file}")

    if args.pi:
        run_camera(model_path=args.model, use_pi=True, proxy_wolf=args.proxy_wolf,
                   silent=args.silent, log_file=args.log_file)
    elif args.source is not None:
        run_camera(source=args.source, model_path=args.model, use_pi=False,
                   proxy_wolf=args.proxy_wolf, silent=args.silent, log_file=args.log_file)
    else:
        run_demo(silent=args.silent, log_file=args.log_file)


if __name__ == "__main__":
    main()

