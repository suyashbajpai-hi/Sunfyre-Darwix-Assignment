"""Shared infrastructure used by all four assessment questions.

- config:     environment-driven settings
- llm:        chat completion wrapper (JSON mode, timing, graceful no-key fallback)
- embeddings: embedding client with on-disk cache
- asr:        speech-to-text wrapper (language hints + vocabulary prompt for code-switching)
- tts:        text-to-speech (Edge TTS native voices / OpenAI)
- latency:    timers and percentile helpers
- pii:        PII detection & masking
- audio:      WAV chunking / concat helpers for Q4 and test-call synthesis
"""
