# Hardware Bill of Materials (BOM), GPIO Wiring & Outdoor Enclosure

## 1. Existing Hardware (On-Hand)
* **Raspberry Pi 4 Model B (4 GB RAM)**
* **Raspberry Pi Camera Module 3 (IMX708)** *(12 MP, PDAF Autofocus, HDR, 15-pin CSI cable)*
* **microSD Storage** *(recommended: ≥ 32–64 GB, Class 10 / A1 or A2)*

---

## 2. Bill of Materials (BOM) — Germany / EU Estimates

### Tier 1 — Core MVP (Working Prototype & Outdoor Enclosure)

| Component | Recommended Part | Purpose | Est. Cost (€) |
| :--- | :--- | :--- | :---: |
| **PIR Motion Sensor** | **HC-SR501** (or AM312) × 2 | Ultra-low-power (~50 µA) motion wake gate; 5V VCC, 3.3V logic OUT (Suraci et al., 2017) | 4–6 € |
| **Audio Amplifier** | **MAX98357A I2S 3W Class-D** | Digital I2S audio; built-in `SD` shutdown pin gives **0 mA standby** via 1 GPIO pin | 5–7 € |
| **Waterproof Speaker** | **4Ω 3W–5W IP65 Speaker** (e.g., Visaton K 50 WP / K 64 WP) | Delivers ~88–90 dB @ 1 m (~68–70 dB @ 10 m, exceeding Zanette et al.'s 60 dB @ 10 m target) | 10–15 € |
| **Passive Cooling** | Aluminum Heatsink Set for Pi 4B | 0 W silent thermal management (avoids 0.5–1 W fan drain & motor noise) | 4–6 € |
| **Lab Power Supply** | Official RPi 4 USB-C 5V 3A PSU (15 W) | Reliable voltage during lab development & benchmarking | 9–12 € |
| **Field Battery** | **Option A:** 20,000 mAh USB-C Powerbank (5V/3A)<br>**Option B:** 12V 12Ah LiFePO4 + 12V→5V 5A Buck | Option A for 1-day demos; Option B for cold-weather multi-day field runs & hard-sleep compatibility | A: 25–35 €<br>B: 45–60 € |
| **Weatherproof Box** | IP65/IP66 Polycarbonate Enclosure (~200×150×100 mm) + PG7 cable glands + acrylic lens disc + silica gel | Rain/condensation protection for outdoor tree mounting | 12–18 € |
| **Tree Strap** | 25 mm Cam-Buckle Nylon Strap (2 m) | Non-destructive mounting to tree trunks at 1.0–1.5 m height | 5–8 € |
| **Wiring & Mounts** | Jumper wires (F-F), M2.5 standoffs, WAGO terminals | Clean internal assembly inside IP65 housing | 8–10 € |

### Tier 2 — Energy Profiling & Offline Field Reliability (Strongly Recommended)

| Component | Recommended Part | Purpose | Est. Cost (€) |
| :--- | :--- | :--- | :---: |
| **Power Meter** | **USB-C Power Meter** or **INA219 I2C Sensor** | Real mW/mA measurements across FSM states for Final evaluation plots | 4–15 € |
| **Real-Time Clock** | **DS3231 I2C RTC Module** (+ CR2032 cell) | Pi 4B lacks an onboard RTC; preserves accurate offline timestamps in forests without Wi-Fi | 3–5 € |

### Tier 3 — Optional Field Autonomy & Night Vision Upgrades

| Component | Recommended Part | Purpose | Est. Cost (€) |
| :--- | :--- | :--- | :---: |
| **Hard-Sleep Power Manager** | **Witty Pi 4** (includes DS3231 RTC!) or ESP32 + MOSFET | Cuts idle draw from 2.1 W → ~0.02 W (multi-week runtime; ~18 s boot trade-off) | 8–30 € |
| **Solar Charging** | 12V 20–30 W Solar Panel + MPPT/PWM Controller | Continuous off-grid recharging for LiFePO4 pack | 35–50 € |
| **Nocturnal Vision** | **Camera Module 3 NoIR** + 940 nm IR LED + MOSFET | Required for pitch-dark operation (standard Camera Module 3 has an IR-cut filter) | 35–45 € |

---

## 3. Raspberry Pi 4B GPIO Pinout & Wiring Table

| Peripheral | Module Pin | Raspberry Pi 4B Pin | BCM / Function | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Camera Module 3** | 15-pin CSI Ribbon | CSI Camera Port | CSI-2 | Standard 15-pin cable (blue side toward Ethernet/USB) |
| **HC-SR501 PIR** | `VCC` | Physical Pin 2 | `5V` | Power input (4.5–20 V) |
| **HC-SR501 PIR** | `GND` | Physical Pin 6 | `GND` | Common ground |
| **HC-SR501 PIR** | `OUT` | Physical Pin 11 | `GPIO 17` | 3.3V TTL safe; trigger input to `GPIOPIRTrigger` |
| **MAX98357A Amp** | `VIN` | Physical Pin 4 | `5V` | Powers 3W Class-D stage |
| **MAX98357A Amp** | `GND` | Physical Pin 9 | `GND` | Common ground |
| **MAX98357A Amp** | `BCLK` | Physical Pin 12 | `GPIO 18` (I2S CLK) | Digital I2S bit clock |
| **MAX98357A Amp** | `LRC` | Physical Pin 35 | `GPIO 19` (I2S FS) | Digital I2S word select |
| **MAX98357A Amp** | `DIN` | Physical Pin 40 | `GPIO 21` (I2S DOUT) | Digital I2S audio data |
| **MAX98357A Amp** | `SD` | Physical Pin 13 | `GPIO 27` | **Power Gate:** `LOW` = 0 mA shutdown, `HIGH` = active |
| **DS3231 RTC / INA219** | `VCC` / `GND` | Pin 1 (`3.3V`) / Pin 14 | `3.3V` / `GND` | Shared I2C bus |
| **DS3231 RTC / INA219** | `SDA` / `SCL` | Pin 3 / Pin 5 | `GPIO 2` / `GPIO 3` | Hardware I2C1 (`i2c-1`) |

---

## 4. Outdoor Mechanical & Acoustic Design Notes
* **Lens Window:** Mount Camera Module 3 flush against a clear acrylic/glass window with a dark foam ring to eliminate internal glare; add a small top overhang hood to shed rain droplets.
* **Speaker Placement:** Mount the waterproof speaker pointing slightly downward (or protected by an acoustic hydrophobic mesh) to prevent water pooling on the cone.
* **Mounting Height & Distance:** Strap unit to a tree at **1.0–1.5 m** height facing a game trail or pasture fence ~5–10 m away (following Zanette et al., 2023 & Suraci et al., 2017 field procedures).
* **Condensation Prevention:** Place 1–2 replaceable **silica gel desiccant packs** inside the sealed IP65 enclosure.
