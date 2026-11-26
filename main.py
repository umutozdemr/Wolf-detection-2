import argparse
import csv
from datetime import datetime
from pathlib import Path
import platform
import random
import subprocess
import time

# Detection and timing settings
CONF_THRESHOLD = 0.60
CONFIRM_FRAMES = 3      # require 3 hits in a row to cut down false positives
DETECT_FPS = 4          # keep FPS low on the Pi 4 to save power
DETECT_WINDOW_SEC = 15
COOLDOWN_SEC = 30
PRE_PLAY_DELAY_SEC = 2  # short delay before playback (Suraci 2017 / Zanette 2023)

# Raspberry Pi BCM pins
PIR_PIN = 17            # HC-SR501 output
AMP_PIN = 27            # MAX98357A shutdown pin (LOW turns amp off)

SOUNDS_DIR = Path("sounds")
LOG_FILE = Path("events.csv")

FALLBACK_SOUNDS = [
    "human_voice_1.wav",
    "human_voice_2.wav",
    "human_voice_3.wav",
    "human_voice_4.wav",
    "human_voice_5.wav",
]


def pick_random_sound(last_sound=None):
    files = sorted(p.name for p in SOUNDS_DIR.glob("*.wav")) if SOUNDS_DIR.exists() else []
    pool = files if files else FALLBACK_SOUNDS
    if len(pool) > 1 and last_sound in pool:
        pool = [s for s in pool if s != last_sound]
    return random.choice(pool)


def play_sound(sound_name, amp_device=None, silent=False):
    if amp_device is not None:
        amp_device.on()
    try:
        sound_path = SOUNDS_DIR / sound_name
        if silent or not sound_path.exists():
            print(f"  [audio] {sound_name}")
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
    import cv2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (15, 15), 0)
    if prev_gray is None:
        return True, gray
    diff = cv2.absdiff(prev_gray, gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    moved_ratio = cv2.countNonZero(thresh) / thresh.size
    return moved_ratio > 0.01, gray


def process_labels(labels, wolf_streak, last_sound=None, amp_device=None, silent=False, log_file=LOG_FILE):
    # Skip immediately if a person is in frame (privacy)
    for name, conf in labels:
        if name == "person" and conf >= CONF_THRESHOLD:
            log_event("PERSON_IGNORED", "person", conf, log_file=log_file)
            return "PERSON_IGNORED", 0, None

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

    return "NO_WOLF", 0, None


def run_demo(silent=False, log_file=LOG_FILE):
    print("Running demo (deer -> person -> wolf)...\n")

    steps = [
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
    for i, (step_name, labels) in enumerate(steps, start=1):
        if not labels:
            print(f"[{i}] {step_name:<14} -> idle (~2.1 W)")
            continue
        action, wolf_streak, played = process_labels(
            labels, wolf_streak, last_sound=last_sound, silent=silent, log_file=log_file
        )
        if played:
            last_sound = played
            print(f"[{i}] {step_name:<14} -> {action} (played {played}, cooldown {COOLDOWN_SEC}s)")
        else:
            print(f"[{i}] {step_name:<14} -> {action} {labels}")

    print(f"\nLogged events to {log_file}")


def run_camera(source="0", model_path="yolov8n.pt", use_pi=False, proxy_wolf=False,
               silent=False, log_file=LOG_FILE):
    import cv2
    from ultralytics import YOLO

    model = YOLO(model_path)

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
            raise RuntimeError(f"Could not open video source: {source}")

    state = "IDLE"
    detect_until = 0.0
    cooldown_until = 0.0
    wolf_streak = 0
    last_sound = None
    prev_gray = None

    print(f"Started camera mode (pi={use_pi}, model={model_path}). Press 'q' to quit.")
    try:
        while True:
            now = time.time()

            if use_pi:
                frame = picam.capture_array()
                motion = pir.motion_detected
            else:
                ok, frame = cap.read()
                if not ok:
                    break
                motion, prev_gray = check_frame_motion(prev_gray, frame)

            if state == "COOLDOWN":
                if now >= cooldown_until:
                    state = "IDLE"
                status = f"COOLDOWN ({max(0, cooldown_until - now):.0f}s)"
            elif state == "IDLE":
                if motion:
                    state = "DETECTING"
                    detect_until = now + DETECT_WINDOW_SEC
                    wolf_streak = 0
                status = "IDLE"
            else:
                results = model.predict(frame, conf=CONF_THRESHOLD, imgsz=416, verbose=False)
                labels = []
                for box in results[0].boxes:
                    cls_name = str(results[0].names[int(box.cls[0])]).lower()
                    if proxy_wolf and cls_name == "dog":
                        cls_name = "wolf"
                    conf = float(box.conf[0])
                    labels.append((cls_name, conf))

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
                cv2.imshow("Wolf Detection", frame)
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
    parser = argparse.ArgumentParser(description="Wolf detection and audio deterrent")
    parser.add_argument("--demo", action="store_true", help="Run the offline demo")
    parser.add_argument("--source", default=None, help="Webcam index (0) or video path")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO weights path")
    parser.add_argument("--pi", action="store_true", help="Use Raspberry Pi Camera Module 3 and PIR")
    parser.add_argument("--proxy-wolf", action="store_true", help="Map COCO dog class to wolf for testing")
    parser.add_argument("--silent", action="store_true", help="Skip audio playback")
    parser.add_argument("--log-file", type=Path, default=LOG_FILE, help="Path for event CSV file")
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
