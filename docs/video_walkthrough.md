# Video walkthrough script (~8–10 min)

Record the running app (`python -m app`) plus these talking points. The PDF requires: overview, architecture, KB/retrieval, voice flow, multilingual, live nudges, fallbacks, limitations.

1. **Overview (1 min)** — Four questions, one repo. Use case is health-insurance lead qualification for fictional Sentinel Health. Q2 is the source of truth.
2. **Architecture (1 min)** — Open `docs/architecture.md`. Point at retrieval → agent → CRM, and chunked Q4 path.
3. **KB (2 min)** — `/kb`. Search “waiting period for pre-existing”, “too expensive”, “stock price of Sentinel”. Show citations, confidence tier, low-confidence refuse. Mention PII masking and the failed PDF in `data/kb/build_report.md`.
4. **Voice agent (2 min)** — `/agent`. Start call, cooperative path (name/age/city/family), then an out-of-scope question, then “I want a human”. Show CRM lead at `/agent/leads`.
5. **Multilingual (2 min)** — `/native`. PH: “Magkano po ang premium for one million?” then “Gusto ko kausapin ang tao”. ID: “Dendanya kejebak” then “Nggih Pak, monggo dicek tenornya”. Point at `docs/q3_localization.md` table (not translations).
6. **Live nudges (1.5 min)** — `/live`. Run `skipped_disclosure`, `missed_cross_sell`, `rising_frustration`, `noisy_ambiguous`. Show suppression on noisy. Open `docs/q4_latency.md` for P50/P95.
7. **Close (30 s)** — Limitations page: no DID, Jakarta TTS, need native review, 10× ASR plan.
