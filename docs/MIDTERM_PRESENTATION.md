# Midterm Presentation Guide — Energy-Efficient Wolf Detection & Response System

**Course:** Ubiquitous Computing (Universität Siegen)
**Target Hardware:** Raspberry Pi 4 Model B (4 GB) + Raspberry Pi Camera Module 3 (IMX708)
**Target Duration:** 8–10 minutes + Q&A (10 slides)

---

## Grading Rubric Alignment (20 / 20 Target)

| Rubric Criterion | Weight | How This Presentation Achieves "Excellent" |
| :--- | :---: | :--- |
| **Progress Overview** | `/4` | Slide 3 presents a clear, milestone-based checklist of completed research, architecture, BOM, GitHub codebase, automated tests (8/8 passing), and working software prototype. |
| **Prototype Preview / Demo** | `/4` | Slide 8 runs the **live working prototype (`wolfdet --demo-scenarios` / video HUD)** demonstrating non-target rejection, GDPR human redaction, audible randomized human-speech deterrence, and JSONL event logging (with backup recording). |
| **Technical Development** | `/5` | Slides 2, 4, 5, 6, 7 detail the Hardware Abstraction Layer (HAL), energy-aware FSM, `M-of-N` temporal wolf confirmation, 5-class Wolf-vs-Dog dataset strategy, MAX98357A power gating, and quantitative power budget charts. |
| **Challenges & Next Steps** | `/3` | Slides 9 & 10 explicitly identify 5 concrete engineering blockers (Wolf vs. Dog, Camera Module 3 IR-cut night vision, Pi 4 idle power vs. boot latency, offline RTC, GDPR) paired with a week-by-week roadmap to the Final Presentation. |
| **Presentation Quality** | `/4` | Clean 10-slide flow, vector diagrams (Mermaid + generated SVGs in `docs/assets/`), structured comparison tables instead of dense text walls. |

---

## Slide-by-Slide Content & Speaker Notes

### Slide 1 — Title & Motivation
* **Title:** *WolfDet: An Energy-Efficient Wolf Detection & Automated Response System*
* **Key Points:**
  * Wolves (*Canis lupus*) are increasingly returning to European rural and forest-adjacent regions (including NRW / Siegerland).
  * Livestock protection needs **non-lethal, low-cost, autonomous** deterrents that can be hung outdoors on trees or pasture perimeters.
  * **Goal:** Detect wolves reliably on edge hardware (**Raspberry Pi 4B + Camera Module 3**) and trigger scientifically proven acoustic deterrence while maximizing battery life.

### Slide 2 — Scientific Grounding (Related Work)
* **Zanette et al. (2023), *Current Biology*:**
  * Large-scale field experiment (4,238 trials): Wildlife fears **calm human speech** (*"human super predator"*) significantly more than apex predators, barking dogs, or gunshots (**2× higher flee odds, 40% faster abandonment**).
  * **Design Rule:** Broadcast **8–14 randomized, neutral human conversation clips** (~10 s, ~60 dB at 10 m) — never repeating the same clip consecutively to avoid habituation.
* **Suraci et al. (2017), *Methods in Ecology and Evolution*:**
  * Pioneered the **Automated Behavioural Response (ABR)** camera-speaker trap.
  * **Limitation we solve:** Motion-only ABR triggers on wind, branches, and non-target wildlife (deer, foxes), wasting battery and disturbing non-target species.
  * **Our Contribution:** **Species-Selective Smart ABR** — Edge AI ensures playback occurs *only* when a wolf is confirmed.

### Slide 3 — Progress Overview *(Rubric: 4/4)*
* **Completed So Far:**
  * ✅ Literature review & formal requirement derivation from Suraci (2017) & Zanette (2023).
  * ✅ End-to-end hardware architecture, GPIO pinout, outdoor IP65 design & Bill of Materials (BOM).
  * ✅ Modular GitHub repository (`Wolf-detection-2`) with Hardware Abstraction Layer (HAL) supporting both PC simulation and Raspberry Pi 4B deployment.
  * ✅ Implemented core **Energy-Aware Finite State Machine**, **M-of-N temporal filter**, **GDPR Privacy Guard**, **anti-habituation audio controller**, and **ring-buffer ABR logger**.
  * ✅ Automated test suite (**8/8 unit & end-to-end tests passing**) + quantitative power budget simulator.
* **Available Hardware On-Hand:** Raspberry Pi 4 Model B (4 GB), microSD storage, Raspberry Pi Camera Module 3.

### Slide 4 — Hardware Architecture & Outdoor Deployment *(Rubric: 5/5)*
* **Visual:** Hardware block diagram (from `README.md` / `docs/HARDWARE_BOM_AND_WIRING.md`).
* **Key Choices:**
  * **Compute & Vision:** Raspberry Pi 4B (4 GB) + **Camera Module 3 (IMX708)** — Phase-Detection Autofocus (2–15 m) & native HDR for forest shadow/sunlight contrast.
  * **Stage-1 Motion Gate:** **HC-SR501 PIR sensor** (~50 µA standby, 3.3V logic output) — exact sensor validated in Suraci et al. (2017).
  * **Audio Subsystem:** **MAX98357A I2S 3W Class-D Amp** + IP65 waterproof 4Ω speaker (~65–70 dB @ 10 m). Uses GPIO `SD` pin for **0 mA standby**.
  * **Outdoor Enclosure ("Hang it outside"):** IP65 polycarbonate box, acrylic lens window with rain hood, silica gel desiccant, passive Pi 4 heatsink (no fan!), tree-friendly cam-buckle strap (1.0–1.5 m height), **DS3231 RTC** for accurate offline timestamps.

### Slide 5 — Software Architecture & State Machine *(Rubric: 5/5)*
* **Visual:** FSM diagram (`IDLE → DETECTING → RESPONDING → COOLDOWN`) + HAL modular structure.
* **Why Hardware Abstraction Layer (HAL)?**
  * Clean interfaces (`MotionTrigger`, `CameraSource`, `WolfDetector`, `AudioDeterrent`, `EventRecorder`) allow full development, CI testing, and live Midterm demos on a laptop today, and **zero-code-change deployment** on Raspberry Pi 4B via `config/settings.yaml`.
* **Built-in Safeguards:**
  * **M-of-N Temporal Voting (3/5 frames):** Suppresses single-frame motion blur or dog/fox misclassifications.
  * **GDPR / Privacy-by-Design:** Detecting `person` immediately wipes RAM frame buffers and suppresses both recording and deterrence.

### Slide 6 — Edge AI Strategy (Wolf Detection on RPi 4B) *(Rubric: 5/5)*
* **Key Challenge:** Standard COCO pretrained weights have **no `wolf` class** (wolves are typically misclassified as `dog` or `bear`).
* **Our ML Pipeline (`training/train_and_export.py`):**
  * **Model:** Lightweight **YOLOv8n / YOLO11n** (`imgsz=416`) exported to **NCNN / ONNX** for fast ARMv8 Cortex-A72 CPU execution (~5–10 FPS on Pi 4B — easily exceeding our energy-saving **4 FPS** detection budget).
  * **5-Class Fine-Tuning Schema (`training/dataset.yaml`):** `wolf` (target), `dog` (hard negative #1), `fox` (hard negative #2), `deer` (common forest wildlife), `person` (GDPR filter).
  * **Data Sources & Augmentation:** Wildlife camera-trap datasets (LILA BC, iNaturalist, Roboflow Wolf) + dusk/low-light, blur, and foliage-occlusion augmentations.

### Slide 7 — Energy Efficiency & Power Budget *(Rubric: 5/5)*
* **Visuals:** Embed `docs/assets/power_by_state.svg` and `docs/assets/energy_comparison.svg`.
* **Key Numbers (Typical Forest Trail: 40 motion + 2 wolf events/day, 12V 12Ah LiFePO4):**
  * **Continuous AI Baseline (5.10 W):** `122.4 Wh/day` → **25.6 hours** runtime.
  * **PIR-Gated Pi 4B MVP (2.12 W avg):** `50.9 Wh/day` → **2.6 days** (**58.4% energy savings**, ~0.35 s wake latency).
  * **Tier-2 MCU Hard-Sleep + PIR (0.06 W avg):** `1.4 Wh/day` → **93.4 days** (**98.9% energy savings**, ~18 s boot latency trade-off).
* **Software Optimizations:** Disable HDMI/BT/Wi-Fi/LEDs, passive cooling, low-FPS (4 FPS) detection window, GPIO `SD`-pin amplifier gating.

### Slide 8 — Live Prototype Preview / Demo *(Rubric: 4/4)*
* **Live Command (run on laptop with speakers ON!):**
  ```bash
  python scripts/generate_audio_exemplars.py
  $env:PYTHONPATH="src"
  python -m wolfdet.main --demo-scenarios
  ```
* **Walk the audience through the 3 live scenarios:**
  1. **Roe Deer passes** → Motion wakes AI → Classified as `deer` → **No sound played**, returns to `IDLE` (saves energy & avoids disturbing deer).
  2. **Human Hiker passes** → Classified as `person` → **GDPR Privacy Redacted**, RAM buffer wiped, no clip saved.
  3. **Grey Wolf approaches** → Confirmed across **3/5 frames** → **Audible calm human speech plays in the presentation room!** → Event written to `logs/events.jsonl` & `logs/events.csv`.
* **Tip:** Also record a 45-second backup screen capture beforehand in case projector/audio fails!

### Slide 9 — Technical Challenges & Engineering Trade-Offs *(Rubric: 3/3)*
| Challenge / Blocker | Engineering Impact | Planned Mitigation |
| :--- | :--- | :--- |
| **1. Wolf vs. Domestic Dog / Fox** | High visual similarity causes false triggers on herding dogs. | Dedicated `dog` & `fox` hard-negative classes + 3-of-5 temporal confirmation + confidence calibration. |
| **2. Night Vision (Camera Module 3 IR-Cut)** | Standard Camera Module 3 has an IR-cut filter, limiting pitch-dark nocturnal range. | Optimize twilight/low-light exposure for MVP; evaluate **NoIR Module 3 + 940 nm GPIO-gated IR LED** for nocturnal field upgrade. |
| **3. Pi 4 Idle Power (~2.1 W) vs. Boot Latency** | Always-on Pi 4 limits battery life to days; full power-off adds ~18 s cold-boot delay (risking missing fast wolves). | Measure real power via USB Wattmeter/INA219; evaluate LiFePO4 + 20W solar vs. Witty Pi 4 / ESP32 wake controller. |
| **4. Offline Timestamps (No Pi 4 RTC)** | Forest deployments lack Wi-Fi/NTP, corrupting event logs after power loss. | Add low-cost I2C **DS3231 RTC** module (~€4). |
| **5. Outdoor Durability & Acoustics** | Rain, condensation, cold weather, and achieving 60 dB at 10 m outdoors. | IP65 box + silica gel + hydrophobic speaker mount + SPL meter calibration at 1 m & 10 m. |

### Slide 10 — Next Steps & Roadmap to Final Presentation *(Rubric: 3/3)*
* **Phase 1 (Hardware Assembly):** Procure PIR (HC-SR501), MAX98357A amp + waterproof speaker, IP65 enclosure, DS3231 RTC, USB Wattmeter/INA219; assemble & wire onto Raspberry Pi 4B.
* **Phase 2 (Custom Model & Pi 4 Optimization):** Curate 5-class dataset (`wolf/dog/fox/deer/person`), fine-tune YOLOv8n/YOLO11n, export to NCNN, benchmark real latency/FPS & confusion matrix on RPi 4B.
* **Phase 3 (Real Energy Profiling):** Measure real W/mA per state (`IDLE`, `DETECTING`, `RESPONDING`) and compare Continuous AI vs. PIR-Gated Pi 4B.
* **Phase 4 (Outdoor Evaluation & Final Demo):** Weatherproof enclosure test, acoustic SPL check (60 dB @ 10 m), Suraci ABR success metrics, Final Presentation & live Pi 4 hardware demo.

---

## Likely Professor Q&A (Preparation Cheat Sheet)

1. **Q: Why use a Raspberry Pi 4B instead of a microcontroller like ESP32-CAM?**
   * **A:** Reliable wolf vs. domestic dog discrimination requires modern object detection (YOLOv8n/YOLO11n at ≥416 px) plus pre/post-playback video recording for ABR evaluation, which exceeds MCU SRAM/compute. We mitigate Pi 4B's higher power by gating it behind a 50 µA PIR sensor and evaluating a Tier-2 MCU hard-sleep controller.
2. **Q: Wolves are often active at night — how does your Camera Module 3 handle darkness?**
   * **A:** Great catch — our current Camera Module 3 includes an IR-cut filter, so it works in daylight and twilight (assisted by native HDR), while full pitch-dark nocturnal operation requires swapping to the **Camera Module 3 NoIR** paired with a GPIO-gated **940 nm IR LED** (invisible to wolves). Our software pipeline and enclosure are already designed for that drop-in swap.
3. **Q: Why not use a Bluetooth speaker or siren?**
   * **A:** Two reasons: (1) Scientifically, Zanette et al. (2023) proved calm human voices trigger stronger avoidance than loud/unnatural sounds or dogs, and randomized exemplars prevent habituation. (2) Technically, Bluetooth speakers draw continuous standby power and suffer wake-up audio lag (the same issue Suraci et al. faced with MP3 players), whereas an I2S **MAX98357A** wakes in milliseconds and draws **0 mA** when its `SD` pin is pulled LOW.
4. **Q: How do you handle GDPR if hikers walk past the tree-mounted camera?**
   * **A:** Our detector explicitly includes a `person` class. Any frame containing a human immediately wipes the RAM ring buffer and suppresses both video storage and audio playback — no human image is ever written to the SD card.
