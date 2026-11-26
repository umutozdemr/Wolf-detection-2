# Rough battery life comparison for Pi 4B + Camera Module 3
# Assuming ~40 motion triggers and 2 wolf detections per day

POWERBANK_WH = 74.0 * 0.85   # 20,000 mAh powerbank (~85% usable)
LIFEPO4_WH = 153.6 * 0.85    # 12V 12Ah LiFePO4 battery

MOTION_PER_DAY = 40
WOLVES_PER_DAY = 2

detect_sec = (MOTION_PER_DAY + WOLVES_PER_DAY) * 15
play_sec = WOLVES_PER_DAY * 12
idle_sec = 86400 - detect_sec - play_sec


def show_estimate(label, idle_w, detect_w, play_w, battery_wh):
    wh_per_day = (idle_sec * idle_w + detect_sec * detect_w + play_sec * play_w) / 3600
    avg_w = wh_per_day / 24
    hours = battery_wh / avg_w
    runtime = f"{hours / 24:.1f} days" if hours >= 48 else f"{hours:.1f} hours"
    print(f"{label:<25} | {avg_w:4.2f} W avg | {wh_per_day:5.1f} Wh/day | {runtime}")


if __name__ == "__main__":
    for name, wh in [("20,000 mAh Powerbank", POWERBANK_WH), ("12V 12Ah LiFePO4", LIFEPO4_WH)]:
        print(f"\n{name} ({wh:.1f} Wh usable)")
        print("-" * 62)
        show_estimate("Continuous AI",         5.10, 5.10, 6.20, wh)
        show_estimate("PIR + Pi 4 idle",       2.10, 4.80, 6.20, wh)
        show_estimate("PIR + MCU deep sleep",  0.02, 4.80, 6.20, wh)
