"""Generate calm human-speech WAV exemplars for local Midterm demos.

Zanette et al. (2023) protocol:
  - Calm, neutral everyday human conversation (NOT shouting, sirens, or dogs).
  - 8-14 distinct exemplars randomized without immediate repetition to prevent habituation.
  - For final outdoor field deployment, replace synthetic demo clips with real recorded
    human voices (men & women speaking calmly in local languages, normalized to 60 dB @ 10 m).
"""

from __future__ import annotations

from pathlib import Path
import platform
import shutil
import subprocess


EXEMPLAR_SCRIPTS: list[tuple[str, str]] = [
    (
        "human_en_calm_01.wav",
        "Good evening, the trail ahead looks clear. Let us keep walking toward the main road before it gets dark.",
    ),
    (
        "human_en_calm_02.wav",
        "Did you check the fence along the upper pasture? Everything looked quiet near the trees this morning.",
    ),
    (
        "human_en_calm_03.wav",
        "The weather is cooler tonight. Let us head back to the cabin and make some warm tea.",
    ),
    (
        "human_en_calm_04.wav",
        "I think we should take the left path by the stream. It is a little shorter and much easier to walk.",
    ),
    (
        "human_en_calm_05.wav",
        "Wait a moment, I am just adjusting my backpack. Okay, I am ready to continue down the hill.",
    ),
    (
        "human_en_calm_06.wav",
        "We saw a lot of tracks near the valley yesterday, so let us remember to check the gate on our way back.",
    ),
    (
        "human_en_calm_07.wav",
        "That was a long hike through the woods. We should arrive at the parking area in about fifteen minutes.",
    ),
    (
        "human_en_calm_08.wav",
        "Can you pass me the flashlight? The path under these tall spruce trees is getting quite dim now.",
    ),
]


def generate_windows_sapi(out_dir: Path) -> int:
    """Use Windows SAPI COM (SpVoice + SpFileStream) to render local WAV speech clips."""
    generated = 0
    for filename, text in EXEMPLAR_SCRIPTS:
        target = out_dir / filename
        escaped_text = text.replace("'", "''")
        escaped_path = str(target.resolve()).replace("'", "''")
        ps = (
            "$voice = New-Object -ComObject SAPI.SpVoice; "
            "$stream = New-Object -ComObject SAPI.SpFileStream; "
            f"$stream.Open('{escaped_path}', 3, $false); "
            "$voice.AudioOutputStream = $stream; "
            "$voice.Rate = -1; "
            f"$voice.Speak('{escaped_text}') | Out-Null; "
            "$stream.Close();"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and target.exists() and target.stat().st_size > 1000:
            generated += 1
            print(f"[OK] Generated {target.name} ({target.stat().st_size // 1024} KB)")
        else:
            print(f"[WARN] Could not generate {filename}: {res.stderr.strip().splitlines()[:1]}")
    return generated


def generate_linux_tts(out_dir: Path) -> int:
    engine = shutil.which("espeak-ng") or shutil.which("espeak")
    if not engine:
        print("[INFO] Install espeak-ng ('sudo apt install espeak-ng') or drop real .wav clips into assets/audio/.")
        return 0
    generated = 0
    for filename, text in EXEMPLAR_SCRIPTS:
        target = out_dir / filename
        res = subprocess.run(
            [engine, "-s", "145", "-w", str(target), text],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and target.exists():
            generated += 1
            print(f"[OK] Generated {target.name}")
    return generated


def main() -> int:
    out_dir = Path(__file__).resolve().parents[1] / "assets" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    system = platform.system().lower()
    if system == "windows":
        count = generate_windows_sapi(out_dir)
    elif system == "linux":
        count = generate_linux_tts(out_dir)
    else:
        print("Place 8-14 calm human-speech .wav clips directly into assets/audio/.")
        return 0
    print(f"\nGenerated {count}/{len(EXEMPLAR_SCRIPTS)} calm human-speech demo exemplars in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
