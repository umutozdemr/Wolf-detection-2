# Midterm Presentation Plan

Length: ~8-10 minutes (10 slides)

1. **Problem and motivation**: Wolves are showing up more around our area, so we want a low-cost, non-lethal deterrent that can run outside on battery.
2. **Background papers**: Zanette et al. (2023) showed wildlife avoids normal human speech more than dogs, gunshots, or lions (using multiple random clips so animals don't get used to it). Suraci et al. (2017) built an automated camera-speaker trap; we add edge AI so it only plays audio for wolves instead of every moving branch or deer.
3. **Progress so far**: Finished literature review, selected parts and GPIO wiring, set up the GitHub repo, added real sample talking `.wav` clips, implemented the prototype (`main.py`) with external SSD CSV logging (`--log-file`), wrote unit tests and rough battery estimates.
4. **Hardware setup**: Raspberry Pi 4B (4 GB), Camera Module 3, HC-SR501 PIR sensor, MAX98357A I2S amp (shut down via GPIO when idle), waterproof speaker, IP65 box with tree strap.
5. **Software flow**: Idle until motion -> run YOLO at 4 FPS -> ignore humans for privacy and ignore non-target animals -> after 3 wolf frames play a random voice clip, write to `events.csv`, and wait in cooldown.
6. **Model plan**: Standard COCO weights don't have a wolf class, so we plan to fine-tune YOLOv8n (`train.py`) on wolf, dog, fox, deer, and person, then export to NCNN for the Pi 4 CPU.
7. **Energy estimates**: From `power_calc.py`, continuous AI (~5.1 W) lasts ~12h on a 20,000 mAh powerbank (~26h on 12V 12Ah LiFePO4). PIR gating drops average draw to ~2.1 W (~30h / ~2.6 days). Adding an external MCU for deep sleep could reach weeks/months, with the trade-off of Pi boot time (~18s).
8. **Demo**: Run `python main.py --demo` (or webcam/video with `--proxy-wolf`) showing deer ignored, person ignored, wolf confirmed on 3rd frame, audio played, and CSV logged.
9. **Challenges**: Telling wolves apart from domestic dogs/foxes; standard Camera Module 3 has an IR-cut filter (night use needs NoIR + 940 nm IR LED); Pi 4 idle power vs boot latency; no onboard RTC without Wi-Fi.
10. **Next steps**: Build the weatherproof hardware setup, train and test the custom wolf model on the Pi 4, measure actual power consumption with a wattmeter, and test outdoor audio level (~60 dB at 10 m).
