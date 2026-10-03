"""Scripted live-call scenarios for Q4 required coverage.

Each turn has a speaker, text, and duration_s. The simulator releases turns
only after waiting `duration_s` (real-time replay). This is not "upload a
finished file and analyse it".
"""
from __future__ import annotations

from typing import Dict, List

Turn = Dict[str, object]

SCENARIOS: Dict[str, Dict] = {
    "missed_cross_sell": {
        "title": "Missed multi-vehicle / family cross-sell",
        "expect_kinds": ["missed_cross_sell"],
        "turns": [
            {"speaker": "agent", "duration_s": 6, "text":
             "Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation."},
            {"speaker": "customer", "duration_s": 5, "text": "Hi, I am Rohan, 36, Pune. I want cover for myself."},
            {"speaker": "agent", "duration_s": 4, "text": "Sure — Essential or Family Shield are the usual starting points. Any health conditions?"},
            {"speaker": "customer", "duration_s": 6, "text": "No conditions. Also I have a second car at home and my wife drives it daily — not sure if that matters."},
            {"speaker": "agent", "duration_s": 4, "text": "Health insurance does not cover cars, but Family Shield would cover your wife. Shall I quote Essential only?"},
        ],
    },
    "skipped_disclosure": {
        "title": "Skipped recording disclosure + risky guaranteed line",
        "expect_kinds": ["compliance_gap"],
        "turns": [
            {"speaker": "agent", "duration_s": 5, "text": "Hi, I am calling about a health plan, you are 100% covered, guaranteed approval today."},
            {"speaker": "customer", "duration_s": 4, "text": "Really? From day one even for my diabetes?"},
            {"speaker": "agent", "duration_s": 4, "text": "Yes, pre-existing is covered from day one, no exclusions."},
        ],
    },
    "rising_frustration": {
        "title": "Rising frustration",
        "expect_kinds": ["rising_frustration"],
        "turns": [
            {"speaker": "agent", "duration_s": 5, "text": "Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes."},
            {"speaker": "customer", "duration_s": 4, "text": "I already told you my age, I am 42."},
            {"speaker": "agent", "duration_s": 3, "text": "Sorry — could I have your age please?"},
            {"speaker": "customer", "duration_s": 5, "text": "This is ridiculous, you are a useless bot, I already told you twice!!"},
        ],
    },
    "noisy_ambiguous": {
        "title": "Noisy / ambiguous — must NOT spray nudges",
        "expect_kinds": [],  # zero or only suppressed
        "turns": [
            {"speaker": "agent", "duration_s": 5, "text": "Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation."},
            {"speaker": "customer", "duration_s": 4, "text": "uh hmm yeah okay um traffic is bad hang on"},
            {"speaker": "agent", "duration_s": 3, "text": "Take your time."},
            {"speaker": "customer", "duration_s": 4, "text": "maybe later I don't know, just looking, nothing specific"},
            {"speaker": "agent", "duration_s": 3, "text": "Of course. I will not push a plan today."},
        ],
    },
    "payment_and_callback": {
        "title": "Payment difficulty + callback (Indonesia-style loanwords on a mixed call)",
        "expect_kinds": ["payment_difficulty", "callback_need"],
        "turns": [
            {"speaker": "agent", "duration_s": 5, "text": "Selamat siang, saya Sari dari MitraDana. Panggilan ini direkam untuk kualitas layanan."},
            {"speaker": "customer", "duration_s": 5, "text": "Cicilannya mahal banget dong, gaji belum masuk, dendanya kejebak."},
            {"speaker": "customer", "duration_s": 4, "text": "Hubungi aku setelah gajian tanggal 10, now is not a good time."},
        ],
    },
}


def all_scenarios() -> List[str]:
    return list(SCENARIOS)
