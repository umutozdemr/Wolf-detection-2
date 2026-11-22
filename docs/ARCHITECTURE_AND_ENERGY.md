# System Architecture & Energy Efficiency Analysis

## 1. Software Architecture (Hardware Abstraction Layer)

To allow rapid prototyping, unit testing, and Midterm demonstrations **before** external sensors and enclosures arrive, WolfDet decouples business logic from physical hardware via clean abstract interfaces:

| Layer | Interface (`src/wolfdet/`) | PC / Midterm Demo Backend | Raspberry Pi 4B Field Backend |
| :--- | :--- | :--- | :--- |
| **Motion Gate** | `motion.base.MotionTrigger` | `SoftwareMotionTrigger` / `MockMotionTrigger` | `GPIOPIRTrigger` (HC-SR501 on BCM GPIO 17) |
| **Camera** | `camera.base.CameraSource` | `OpenCVCameraSource` / `SyntheticScenarioCamera` | `PiCameraModule3Source` (`picamera2`, HDR, PDAF, 4 FPS) |
| **Detector** | `detection.base.WolfDetector` | `ScenarioMockDetector` / `YOLOWolfDetector` | `YOLOWolfDetector` (NCNN / ONNX on Pi 4B CPU) |
| **Audio** | `audio.deterrent.AudioDeterrent` | PC Speaker (`winsound` / `aplay`) | MAX98357A I2S Amp + GPIO 27 `SD`-pin gating |
| **Logging** | `recorder.event_logger.EventRecorder` | Ring-buffer MP4 + `events.jsonl` / `events.csv` | Same (with DS3231 RTC accurate offline timestamps) |

Switching from PC Demo to Raspberry Pi 4B requires **zero changes** to `WolfResponseStateMachine` — only selecting `--pi` or updating `config/settings.yaml`.

---

## 2. Detection & Anti-False-Alarm Pipeline

1. **Stage-1 Motion Gating (PIR):** Keeps the camera pipeline dormant while the forest scene is static.
2. **Low-FPS Capture (`4 FPS`):** A wolf traversing a 10 m detection zone remains visible for several seconds (Suraci et al., 2017). Sampling at 4 FPS instead of 30 FPS slashes Pi 4B CPU load and thermal dissipation without hurting recall.
3. **5-Class Custom YOLO Model (`training/dataset.yaml`):**
   * `0: wolf` — primary target triggering deterrence.
   * `1: dog` — primary hard negative (domestic/livestock guardian dogs must **not** trigger).
   * `2: fox` — secondary canid hard negative.
   * `3: deer` — frequent non-target forest wildlife.
   * `4: person` — GDPR privacy class.
4. **M-of-N Temporal Confirmation (`3 of 5 frames`):** Eliminates transient single-frame false positives caused by motion blur, foliage, or shadow artifacts.
5. **GDPR Privacy-by-Design:** Whenever `person` is detected, `EventRecorder.clear_buffer()` immediately discards all buffered RAM frames, logs an anonymized `PRIVACY_SUPPRESSED` telemetry entry (no image), and suppresses deterrence.

---

## 3. Quantitative Power Budget Analysis

Computed using `scripts/power_budget.py` for **Raspberry Pi 4 Model B (4 GB) + Camera Module 3 + MAX98357A**.

### State Power Estimates

| State | Active Components | Est. Power | Notes |
| :--- | :--- | :---: | :--- |
| **MCU Hard-Sleep (Tier-2)** | Witty Pi 4 / ESP32 + HC-SR501 PIR | **0.02 W** | Pi 4B fully powered off (~18 s wake latency) |
| **IDLE (MVP)** | Pi 4B (HDMI/BT/Wi-Fi/LEDs off) + PIR | **2.10 W** | Instant wake (~0.35 s camera start) |
| **DETECTING** | Pi 4B + Camera Module 3 + YOLOv8n @ 4 FPS | **4.80 W** | Active only during 15 s motion windows |
| **RESPONDING** | Pi 4B + Cam + MAX98357A 3W playback + SD write | **6.20 W** | Active ~12 s only on confirmed wolf events |
| **COOLDOWN** | Pi 4B standby + Amp OFF (`SD=LOW`) | **2.40 W** | 30 s debounce window |

### Daily Energy & Battery Autonomy (40 Motion + 2 Wolf Events / Day)

| Architecture | Battery Pack (85% Usable) | Avg Power | Energy / Day | Est. Runtime | Savings vs. Baseline | Wake Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Continuous AI (Baseline)** | 20,000 mAh Powerbank (74 Wh) | 5.10 W | 122.41 Wh | **12.3 h** | 0.0% | 0.0 s |
| **PIR-Gated Pi 4B (MVP)** | 20,000 mAh Powerbank (74 Wh) | 2.12 W | 50.90 Wh | **29.7 h** | **58.4%** | 0.35 s |
| **MCU Hard-Sleep + PIR** | 20,000 mAh Powerbank (74 Wh) | 0.06 W | 1.40 Wh | **45.0 d** | **98.9%** | 18.0 s |
| **Continuous AI (Baseline)** | 12V 12Ah LiFePO4 (153.6 Wh) | 5.10 W | 122.41 Wh | **25.6 h** | 0.0% | 0.0 s |
| **PIR-Gated Pi 4B (MVP)** | 12V 12Ah LiFePO4 (153.6 Wh) | 2.12 W | 50.90 Wh | **2.6 d** | **58.4%** | 0.35 s |
| **MCU Hard-Sleep + PIR** | 12V 12Ah LiFePO4 (153.6 Wh) | 0.06 W | 1.40 Wh | **93.4 d** | **98.9%** | 18.0 s |

### Key Engineering Trade-Off: Idle Power vs. Wake Latency
* **PIR-Gated Pi 4B (MVP)** cuts daily energy by **~58%** while preserving sub-second response (`~0.35 s`), ensuring even fast-moving wolves are captured and deterred immediately.
* **MCU Hard-Sleep (Tier-2)** extends autonomy by **~35×** (weeks/months on LiFePO4), at the cost of Pi 4B's **~15–20 s Linux cold boot** — best suited for baited/corralled sites (where animals linger, as in Suraci et al.'s Bwindi/Santa Cruz trials) or paired with a small solar panel (20–30 W) to run the low-latency MVP continuously.

---

## 4. Raspberry Pi OS Power-Tuning Checklist (Field Deployment)

When deploying onto the Raspberry Pi 4B, add the following optimizations:

```ini
# /boot/firmware/config.txt
dtoverlay=disable-bt
dtoverlay=disable-wifi          # Only for offline field deployment!
dtparam=act_led_trigger=none
dtparam=pwr_led_trigger=none
dtoverlay=hifiberry-dac         # Enable I2S audio for MAX98357A
```

And disable HDMI output + set CPU governor to `powersave` / `ondemand` in `/etc/rc.local` or systemd service.
