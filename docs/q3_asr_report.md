# Q3 — ASR / TTS configuration notes

Each market is configured **separately** in `q1_voice_agent/locale.py`. Whisper is not forced to a single language for PH/ID because that breaks code-switching.

| | Philippines | Indonesia | India (Q1) |
|---|---|---|---|
| Provider / model | OpenAI Whisper `whisper-1` | OpenAI Whisper `whisper-1` | OpenAI Whisper `whisper-1` |
| `language` knob | `None` (auto) | `None` (auto) | `en` |
| Vocabulary prompt | premium, policy, beneficiary, rider, lapse, coverage, bank referral, po, opo, magkano, asawa | cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan, nggih, monggo | Sentinel plan names, PED, lakh, GST |
| Native TTS | Edge `fil-PH-BlessicaNeural` | Edge `id-ID-GadisNeural` | Edge `en-US-AriaNeural` / OpenAI `alloy` |
| Fallback language | Stay in Taglish / Filipino (`unavailable` string is Filipino) | Stay in Bahasa | English |

## How to measure quality on your machine

With `OPENAI_API_KEY` set, start a call at `/native`, hold-to-talk the lines in `q3_native_bots/test_calls.py`, and note:

1. Did `magkano` + `premium` both survive Taglish?
2. Did `denda` / `DP` / `MotorPlus` survive colloquial Bahasa?
3. Did `nggih` / `monggo` survive Yogyakarta phrasing, or did Whisper normalise to standard Indonesian?
4. Approximate WER on a 4–6 turn call (count substitutions / deletions).
5. Regional accent: Edge TTS is Jakarta-standard Indonesian — it cannot synthesise Yogya. That compromise is required evidence.

Until a key is present the scripted transcripts still run (text in, grounded text out) so the rest of the submission is reviewable offline.

See also `docs/q3_localization.md` for the not-a-translation examples.
