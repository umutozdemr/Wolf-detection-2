# Human-Speech Deterrent Audio Exemplars

Following **Zanette et al. (2023)** (*Current Biology*) and **Suraci et al. (2017)** (*Methods in Ecology and Evolution*), wildlife exhibits the strongest and most consistent avoidance response to **calm, neutral human conversation** (the *"human super predator"* effect) — significantly stronger than barking dogs, gunshots, or apex predators.

## Protocol Guidelines
1. **Content:** Women and men speaking calmly in everyday conversation (German / English) — **no shouting, sirens, or aggressive tones**.
2. **Diversity (Anti-Habituation):** Maintain **8–14 distinct `.wav` exemplars** (`16 kHz` or `44.1 kHz`, mono, ~10 seconds each). `AudioDeterrent` randomizes selection and prevents immediate repetition.
3. **Volume Standardization:** Normalize clips (RMS / LUFS) so outdoor playback delivers **~60 dB SPL at 10 m** (approx. **80–85 dB SPL at 1 m**).

## Quick Generation for Midterm Demo
To generate 8 local calm-speech `.wav` demo files immediately (no internet required):

```bash
python scripts/generate_audio_exemplars.py
```

For final outdoor deployment, replace the synthetic demo files with real recorded human conversations.
