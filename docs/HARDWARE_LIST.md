# Hardware List & Simple Wiring

## What We Already Have
- **Raspberry Pi 4 Model B (4 GB)** + microSD card
- **Raspberry Pi Camera Module 3** (12 MP, Autofocus, HDR)

## Parts Needed

| Part | Model | Why | Est. Price |
| :--- | :--- | :--- | :---: |
| **Motion Sensor (PIR)** | HC-SR501 (or AM312) | Wakes AI only when something moves (~50 µA standby) | ~5 € |
| **Audio Amplifier** | MAX98357A (I2S, 3W) | Drives speaker + GPIO shutdown pin (`0 mA` standby) | ~6 € |
| **Waterproof Speaker** | 4Ω 3W–5W IP65 Speaker | Reaches ~65–70 dB at 10 m | ~12 € |
| **Passive Heatsink** | Pi 4 Aluminum Heatsink | Silent cooling with 0 W power draw (no fan) | ~5 € |
| **Lab Power Supply** | Official Pi 4 USB-C 5V 3A | Stable power during testing | ~10 € |
| **Battery** | 20,000 mAh Powerbank *or* 12V 12Ah LiFePO4 + 5V Buck | Outdoor battery power | 30–50 € |
| **Outdoor Case** | IP65 Plastic Box + Acrylic Window + Silica Gel + Tree Strap | Hang safely on a tree in rain/cold | ~20 € |
| **Optional (Recommended)** | USB-C Wattmeter + DS3231 RTC | Measure real Watts + keep accurate offline clock | ~15 € |

## Simple GPIO Wiring (Raspberry Pi 4B)

| Module | Module Pin | Raspberry Pi 4 Pin |
| :--- | :--- | :--- |
| **Camera Module 3** | 15-pin CSI Ribbon | CSI Camera Port |
| **HC-SR501 PIR** | `VCC` / `GND` / `OUT` | Pin 2 (`5V`) / Pin 6 (`GND`) / Pin 11 (`GPIO 17`) |
| **MAX98357A Amp** | `VIN` / `GND` | Pin 4 (`5V`) / Pin 9 (`GND`) |
| **MAX98357A Amp** | `BCLK` / `LRC` / `DIN` | Pin 12 (`GPIO 18`) / Pin 35 (`GPIO 19`) / Pin 40 (`GPIO 21`) |
| **MAX98357A Amp** | `SD` (Shutdown) | Pin 13 (`GPIO 27`) — `LOW` = off, `HIGH` = on |
