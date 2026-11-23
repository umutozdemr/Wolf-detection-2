# WolfDet — Simple Energy-Efficient Wolf Detection & Response System

**Ubiquitous Computing Project (Universität Siegen)**  
**Hardware:** Raspberry Pi 4B (4 GB) + Raspberry Pi Camera Module 3

Detects wolves using edge AI and plays randomized **calm human speech** to deter them — grounded in **Suraci et al. (2017)** (ABR camera-speaker system) and **Zanette et al. (2023)** (wildlife fears human speech more than dogs, gunshots, or apex predators).

## How It Works
1. **IDLE:** Waits in low-power mode for motion (PIR sensor on Pi, or frame difference on PC).
2. **DETECTING:** Runs lightweight YOLO at **4 FPS** for up to 15 seconds.
   - Ignores non-target animals (deer, fox, dog).
   - Ignores humans (`person`) for privacy (GDPR).
   - Confirms a wolf only after **3 consecutive frames** (prevents false alarms).
3. **RESPOND & COOLDOWN:** Plays a random calm human voice clip from `sounds/`, logs the event to `events.csv`, and enters a 30-second cooldown.

## Project Files
```text
Wolf-detection-2/
├── main.py                       # Complete detection, audio & logging script
├── power_calc.py                 # Simple battery life & energy savings calculator
├── train.py                      # YOLOv8n training + NCNN export for Pi 4B
├── test_main.py                  # Simple unit tests
├── requirements.txt              # Python dependencies (opencv-python, ultralytics)
├── sounds/README.md              # Drop calm human speech .wav files here
└── docs/
    ├── MIDTERM_PRESENTATION.md   # 10-slide Midterm outline aligned with rubric
    └── HARDWARE_LIST.md          # Hardware BOM & Raspberry Pi GPIO wiring
```

## Quickstart

### 1. Run Midterm Demo (No extra packages needed)
```bash
python main.py --demo
```

### 2. Run Power & Battery Comparison
```bash
python power_calc.py
```

### 3. Run Unit Tests
```bash
python -m unittest test_main.py -v
```

### 4. Run with Webcam / Video (PC) or Raspberry Pi 4B
```bash
pip install -r requirements.txt

# On PC with webcam or wildlife video:
python main.py --source 0 --model yolov8n.pt --proxy-wolf

# On Raspberry Pi 4B + Camera Module 3 + HC-SR501 PIR:
python3 main.py --pi --model best_ncnn_model
```
