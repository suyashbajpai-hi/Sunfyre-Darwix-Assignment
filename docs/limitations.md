# Limitations and production-improvement plan

## What this prototype is

A working, explainable system for the 48-hour assessment: grounded voice qualification, a messy-document KB, two localized bots, and a real-time nudge pipeline with suppression and latency numbers.

## Known gaps

| Area | Gap | Production move |
|---|---|---|
| Telephony | Web calling UI, no DID | Hosted voice (Vapi/Retell) or SIP + Twilio |
| ASR | Whisper HTTP per turn/chunk | Streaming ASR (Deepgram nova / Whisper streaming) with partials |
| Diarization | UI-labelled agent vs customer | Stereo recording or pyannote / provider diarization |
| Embeddings | Optional; BM25-only works offline | Always-on dense index in pgvector/Qdrant + hybrid |
| LLM grounding | Prompt-level citations | Constrained decoding / answer-span check against chunk text |
| Q3 linguist review | Author is not a native Tagalog/Javanese speaker | Native review + compliance legal in PH/ID |
| Q3 TTS accent | Edge `id-ID` is Jakarta, not Yogya | Custom voice or provider with regional voices |
| Q4 10× scale | One process, one Whisper client | Queue per call, rule-first, LLM only on topic shift, GPU ASR |
| Q4 noisy audio | Phrase rules miss; garbage LLM over-fires | SNR gate, don’t run LLM below ASR confidence, keep cooldown |
| CRM | JSONL file | Salesforce / internal lead API with auth |
| Secrets | `.env` locally | Cloud secret manager, never in git |
| Eval | Scripted transcripts | Shadow mode on real calls, native-speaker score, hallucination audit |

## Error / fallback cases already implemented

- KB source PDF that cannot be parsed → `status=failed` in the build report, pipeline continues.
- Out-of-scope questions → low grounding → spoken “I do not have that information”.
- Conflicting age vs DOB → qualification status `Referred`, no promise of eligibility.
- Customer asks for a human → escalate + webhook/CRM, stop the pitch.
- DNC phrases → mark and end.
- No `OPENAI_API_KEY` → BM25 retrieval + template agent + Edge TTS still run end-to-end.

## What I would not add in 48 hours

A pretty marketing site, a real insurer scrape, or a fine-tuned local LLM. The PDF scores working grounded outcomes over polish.
