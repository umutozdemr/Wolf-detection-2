# Wolf Detection System

Ubiquitous Computing project at University of Siegen.

The goal is to build an energy-efficient system on a Raspberry Pi 4B (4 GB) with a Raspberry Pi Camera Module 3 that detects wolves and plays human talking sounds to scare them away. The idea is based on Suraci et al. (2017) and Zanette et al. (2023), which show that wildlife reacts much more strongly to normal human speech than to dog barking or gunshots.

## How it works

1. The system stays idle until motion is detected (PIR sensor on the Pi, or frame differencing on a PC).
2. Once triggered, it runs YOLO at 4 FPS for up to 15 seconds to save CPU and battery.
3. Non-target animals like deer, foxes, or dogs are ignored. If a person is detected, nothing is triggered or saved for privacy.
4. If a wolf is detected in 3 frames in a row, the script picks a random `.wav` clip from `sounds/`, plays it, logs the event to a CSV file, and waits 30 seconds before triggering again.

## Files

- `main.py` - main script for motion check, YOLO detection, audio playback, and CSV logging
- `power_calc.py` - rough battery life estimates for different power setups
- `train.py` - script to train YOLOv8n on a custom wolf dataset and export to NCNN for the Pi
- `test_main.py` - basic unit tests for the detection/audio logic
- `sounds/` - `.wav` clips of people talking (currently includes two sample clips)
- `docs/HARDWARE_LIST.md` - parts list and GPIO wiring notes
- `docs/MIDTERM_PRESENTATION.md` - notes and slide plan for the midterm presentation

## Setup and usage

Install dependencies if you want to run with a real camera or video:

```bash
pip install -r requirements.txt
```

### Demo mode (no camera or packages needed)

```bash
python main.py --demo
```

### Webcam or video file on PC

If you only have stock COCO weights (`yolov8n.pt`), you can pass `--proxy-wolf` to treat `dog` detections as `wolf` while testing:

```bash
python main.py --source 0 --model yolov8n.pt --proxy-wolf
```

### Raspberry Pi 4B with Camera Module 3 and PIR sensor

```bash
python3 main.py --pi --model best_ncnn_model
```

### Logging events to an external SSD

Mount the SSD first and replace `/mnt/wolfdet` with your mount path. You can test logging without a camera or speaker like this:

```bash
python3 main.py --demo --silent --log-file /mnt/wolfdet/demo-events.csv
```

And with the Pi camera:

```bash
python3 main.py --pi --model best_ncnn_model --log-file /mnt/wolfdet/events.csv
```

Make sure the target folder already exists and the drive is mounted before starting. Without `--log-file`, events go to `events.csv` in the project directory.

### Power estimate and tests

```bash
python power_calc.py
python -m unittest test_main.py -v
```
