# Midterm Presentation Outline (10 Slides — Rubric Aligned)

**Target:** 8–10 minutes | **Grading Rubric:** Progress (`/4`), Demo (`/4`), Technical (`/5`), Challenges & Next Steps (`/3`), Presentation Quality (`/4`).

1. **Title & Problem** — Wolves returning to our area; need a non-lethal, battery-powered outdoor deterrent.
2. **Scientific Basis** — **Zanette et al. (2023):** calm human speech scares wildlife more than dogs/gunshots/lions (use 8–14 random clips). **Suraci et al. (2017):** ABR camera-speaker trap — our upgrade adds AI so it triggers *only* on wolves, not wind/deer.
3. **Progress Overview (`/4`)** — Literature review done, hardware BOM & wiring finalized, simple working Python prototype (`main.py`), unit tests passing, power calculation ready.
4. **Hardware & Outdoor Design (`/5`)** — Raspberry Pi 4B (4 GB) + Camera Module 3 + HC-SR501 PIR + MAX98357A Amp (GPIO shutoff) + IP65 waterproof box + tree strap.
5. **Software Flow (`/5`)** — Simple 3-state loop: `IDLE (wait for motion)` → `DETECTING (4 FPS YOLO, 3-frame wolf confirmation, GDPR ignore person)` → `COOLDOWN (after playing random human speech & logging to events.csv)`.
6. **AI Model Plan (`/5`)** — Stock COCO has no `wolf` class → fine-tune `YOLOv8n` (`train.py`) on `wolf, dog, fox, deer, person` and export to **NCNN** for fast CPU inference on Pi 4B.
7. **Energy Efficiency (`/5`)** — Output from `python power_calc.py`:
   - Continuous AI (5.1 W): ~12 h on powerbank / ~26 h on LiFePO4.
   - PIR-Gated Pi 4B (2.1 W avg): ~30 h on powerbank / ~2.6 days on LiFePO4 (**~58% savings**).
   - MCU Hard-Sleep + PIR (0.06 W avg): **~93 days** on LiFePO4 (trade-off: ~18 s boot time).
8. **Live Prototype Demo (`/4`)** — Run `python main.py --demo` (or `--source video.mp4 --proxy-wolf`) showing Deer ignored → Person ignored (GDPR) → Wolf confirmed in 3 frames → Random human speech played + `events.csv` logged.
9. **Challenges & Blockers (`/3`)** — Wolf vs. dog similarity; standard Camera Module 3 has IR-cut filter (night vision needs NoIR + 940 nm IR LED); Pi 4 idle draw vs. boot time; no onboard RTC clock offline.
10. **Next Steps (`/3`)** — Assemble hardware in IP65 box → train custom wolf model → measure real Watts on Pi 4B → outdoor volume (60 dB @ 10 m) & field test.
