"""
Simple battery life & energy comparison for Raspberry Pi 4B + Camera Module 3.
Assumes a typical forest trail: 40 motion triggers + 2 wolf events per day.
"""

BATTERY_WH = 74.0 * 0.85   # 20,000 mAh powerbank (~62.9 Wh usable)
LIFEPO4_WH = 153.6 * 0.85  # 12V 12Ah LiFePO4 battery (~130.6 Wh usable)

MOTION_EVENTS_PER_DAY = 40
WOLF_EVENTS_PER_DAY = 2

DETECT_SEC = (MOTION_EVENTS_PER_DAY + WOLF_EVENTS_PER_DAY) * 15
PLAYBACK_SEC = WOLF_EVENTS_PER_DAY * 12
IDLE_SEC = 86400 - DETECT_SEC - PLAYBACK_SEC


def print_mode(name, idle_w, detect_w, play_w, battery_wh):
    daily_wh = (IDLE_SEC * idle_w + DETECT_SEC * detect_w + PLAYBACK_SEC * play_w) / 3600
    avg_w = daily_wh / 24
    hours = battery_wh / avg_w
    runtime = f"{hours / 24:.1f} days" if hours >= 48 else f"{hours:.1f} hours"
    print(f"{name:<28} | {avg_w:5.2f} W avg | {daily_wh:6.1f} Wh/day | {runtime}")


if __name__ == "__main__":
    for label, wh in [("20,000 mAh Powerbank", BATTERY_WH), ("12V 12Ah LiFePO4", LIFEPO4_WH)]:
        print(f"\n=== {label} ({wh:.1f} Wh usable) ===")
        print_mode("1. Continuous AI (24/7)",   idle_w=5.10, detect_w=5.10, play_w=6.20, battery_wh=wh)
        print_mode("2. PIR-Gated Pi 4B (MVP)",  idle_w=2.10, detect_w=4.80, play_w=6.20, battery_wh=wh)
        print_mode("3. MCU Hard-Sleep + PIR",   idle_w=0.02, detect_w=4.80, play_w=6.20, battery_wh=wh)
