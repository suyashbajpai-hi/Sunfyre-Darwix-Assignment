# Q4 — Live insights: latency, nudges, false-positive controls

Realtime replay: **False** · Scenarios passed: 9/9

## False-positive / suppression

```json
{
  "nudges_emitted_all_scenarios": 8,
  "nudges_suppressed_all_scenarios": 4,
  "noisy_scenario_emitted": 0,
  "noisy_scenario_suppressed": 0,
  "approx_precision_note": "Precision proxy = 1 - (noisy_emitted / max(emitted,1)). A true FP rate needs labelled frames; this is the assessment's 'approximate' bar.",
  "approx_precision": 1.0
}
```

Controls: confidence threshold (default 0.65), per-kind cooldown 45s, duplicate-evidence overlap, TTL 60s, priority order compliance > frustration > payment > cross-sell > callback > buying.

## Missed multi-vehicle / family cross-sell — PASS

Expected kinds: `['missed_cross_sell']`

### Emitted nudges

- `missed_cross_sell` prio=60 conf=0.82 — Customer mentioned another vehicle / family member. Offer the relevant multi-cover or rider before closing.

### Suppressed

_None._

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 5 | 120.0 | 120.0 | 120.0 | 120.0 |
| signal_extraction | 5 | 0.0 | 0.0 | 0.0 | 0.0 |
| nudge_control | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| delivery | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 1 | 120.0 | 120.0 | 120.0 | 120.0 |

## Skipped recording disclosure + risky guaranteed line — PASS

Expected kinds: `['compliance_gap']`

### Emitted nudges

- `compliance_gap` prio=100 conf=0.93 — Risky statement. Correct course: do NOT promise guaranteed cover. Restate underwriting disclaimer.

### Suppressed

- `compliance_gap` cooldown compliance_gap last=5.0s — Yes, pre-existing is covered from day one, no exclusions.
- `compliance_gap` cooldown compliance_gap last=5.0s — No recording/solicitation disclosure heard in the first seconds of the call.

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 3 | 120.0 | 120.0 | 120.0 | 120.0 |
| signal_extraction | 3 | 0.0 | 0.0 | 0.0 | 0.0 |
| nudge_control | 3 | 0.0 | 0.0 | 0.0 | 0.0 |
| delivery | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 3 | 120.0 | 120.0 | 120.0 | 120.0 |

## Rising frustration — PASS

Expected kinds: `['rising_frustration']`

### Emitted nudges

- `rising_frustration` prio=90 conf=0.88 — Acknowledge the frustration in one sentence before asking anything else. Offer a human.

### Suppressed

- `rising_frustration` cooldown rising_frustration last=9.0s — This is ridiculous, you are a useless bot, I already told you twice!!

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 4 | 120.0 | 120.0 | 120.0 | 120.0 |
| signal_extraction | 4 | 0.0 | 0.0 | 0.0 | 0.0 |
| nudge_control | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| delivery | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 2 | 120.0 | 120.0 | 120.0 | 120.0 |

## Noisy / ambiguous — must NOT spray nudges — PASS

Expected kinds: `[]`

### Emitted nudges

_None (good for the noisy scenario)._

### Suppressed

_None._

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 5 | 120.0 | 120.0 | 120.0 | 120.0 |
| signal_extraction | 5 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 1 | 120.0 | 120.0 | 120.0 | 120.0 |

## Payment difficulty + callback (Indonesia-style loanwords on a mixed call) — PASS

Expected kinds: `['payment_difficulty', 'callback_need']`

### Emitted nudges

- `payment_difficulty` prio=70 conf=0.8 — Offer an approved payment-support / lower SI / monthly mode / callback path. Do not invent a discount.
- `callback_need` prio=50 conf=0.75 — Stop pitching. Capture a callback slot and confirm it.

### Suppressed

_None._

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 3 | 120.0 | 120.0 | 120.0 | 120.0 |
| signal_extraction | 3 | 0.0 | 0.0 | 0.0 | 0.0 |
| nudge_control | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| delivery | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 2 | 120.0 | 120.0 | 120.0 | 120.0 |

## Replay of q1_cooperative.json — PASS

Expected kinds: `[]`

### Emitted nudges

_None (good for the noisy scenario)._

### Suppressed

_None._

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 13 | 110.0 | 110.0 | 110.0 | 110.0 |
| signal_extraction | 13 | 0.0 | 0.1 | 0.0 | 0.1 |
| e2e_chunk | 1 | 110.1 | 110.1 | 110.1 | 110.1 |

## Replay of q1_oos.json — PASS

Expected kinds: `[]`

### Emitted nudges

_None (good for the noisy scenario)._

### Suppressed

_None._

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 9 | 110.0 | 110.0 | 110.0 | 110.0 |
| signal_extraction | 9 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 1 | 110.0 | 110.0 | 110.0 | 110.0 |

## Replay of ph_cooperative_taglish.json — PASS

Expected kinds: `[]`

### Emitted nudges

- `buying_signal` prio=40 conf=0.78 — Buying signal. Recap plan + disclaimer and offer to create the lead / illustration.

### Suppressed

- `buying_signal` cooldown buying_signal last=27.8s — Sige po, pakicall back tomorrow evening.

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 9 | 110.0 | 110.0 | 110.0 | 110.0 |
| signal_extraction | 9 | 0.0 | 0.0 | 0.0 | 0.0 |
| nudge_control | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| delivery | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 2 | 110.0 | 110.0 | 110.0 | 110.0 |

## Replay of id_colloquial_denda.json — PASS

Expected kinds: `[]`

### Emitted nudges

- `payment_difficulty` prio=70 conf=0.8 — Offer an approved payment-support / lower SI / monthly mode / callback path. Do not invent a discount.
- `callback_need` prio=50 conf=0.75 — Stop pitching. Capture a callback slot and confirm it.

### Suppressed

_None._

### Component latency

| Component | n | P50 ms | P95 ms | mean | max |
|---|---|---|---|---|---|
| asr | 7 | 110.0 | 110.0 | 110.0 | 110.0 |
| signal_extraction | 7 | 0.0 | 0.1 | 0.0 | 0.1 |
| nudge_control | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| delivery | 2 | 0.0 | 0.0 | 0.0 | 0.0 |
| e2e_chunk | 2 | 110.0 | 110.0 | 110.0 | 110.0 |

## 10× scale and noisy audio (limitations)

- At 10× concurrent calls the bottleneck is ASR (Whisper HTTP). A production design batches partials on a streaming ASR (Deepgram / Whisper streaming) and runs rules on every partial, LLM only on topic shifts.
- Noisy audio raises WER; rules that key on rare phrases will miss, and LLM-on-garbage will over-fire unless the confidence threshold stays high (we default 0.65 and suppress duplicates).
- Speaker separation is not diarised from mixed WAV; the web demo labels agent vs customer from the calling UI. A production trunk would use stereo (agent/customer channels).
