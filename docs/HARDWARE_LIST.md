# Hardware List and Wiring

## Already available
- Raspberry Pi 4 Model B (4 GB) + microSD card
- Raspberry Pi Camera Module 3 (12 MP, autofocus, HDR)

## Parts to get

| Part | Model | Purpose | Approx. price |
| :--- | :--- | :--- | :---: |
| PIR motion sensor | HC-SR501 or AM312 | Wakes detection only on motion (~50 uA standby) | ~5 EUR |
| Audio amplifier | MAX98357A (I2S, 3W) | Drives speaker and supports GPIO shutdown (0 mA standby) | ~6 EUR |
| Outdoor speaker | 4 Ohm 3-5W IP65 speaker | Loud enough for ~65-70 dB at 10 m | ~12 EUR |
| Heatsink | Pi 4 aluminum heatsink | Passive cooling without a fan | ~5 EUR |
| Power adapter | Official Pi 4 USB-C 5V 3A | Stable power for lab testing | ~10 EUR |
| Battery | 20,000 mAh powerbank or 12V 12Ah LiFePO4 + 5V buck | Outdoor power supply | 30-50 EUR |
| Enclosure | IP65 box + clear acrylic window + silica gel + strap | Weather protection and tree mounting | ~20 EUR |
| Optional | USB-C wattmeter + DS3231 RTC | Real power measurements and offline clock | ~15 EUR |

## Raspberry Pi 4B GPIO wiring

| Part | Pin on module | Pin on Pi 4B |
| :--- | :--- | :--- |
| Camera Module 3 | 15-pin ribbon cable | CSI port |
| HC-SR501 PIR | VCC / GND / OUT | Pin 2 (5V) / Pin 6 (GND) / Pin 11 (GPIO 17) |
| MAX98357A Amp | VIN / GND | Pin 4 (5V) / Pin 9 (GND) |
| MAX98357A Amp | BCLK / LRC / DIN | Pin 12 (GPIO 18) / Pin 35 (GPIO 19) / Pin 40 (GPIO 21) |
| MAX98357A Amp | SD (shutdown) | Pin 13 (GPIO 27), LOW = off, HIGH = on |
