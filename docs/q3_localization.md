# Q3 — Localization evidence (not literal translation)

Two **separate** bots share the Q1 conversation engine and the Q2 retrieval pipeline. They do **not** share the India health-insurance script. Each market has its own KB sources, ASR config, TTS voice, politeness, and fallback language.

## ASR configuration (tested separately)

| Market | Provider / model | Language knob | Vocabulary prompt (excerpt) | Why |
|---|---|---|---|---|
| Philippines | OpenAI Whisper `whisper-1` | **None (auto)** | premium, policy, beneficiary, rider, lapse, coverage, bank referral, po, opo, magkano, asawa | Taglish code-switch fails if language is forced to `en` or `tl` |
| Indonesia | OpenAI Whisper `whisper-1` | **None (auto)** | cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan, nggih, monggo | Colloquial Bahasa + English loanwords + Jawa particles |
| India (Q1) | Whisper `whisper-1` | `en` | Sentinel plan names, PED, lakh, GST | Monolingual English qualifier |

Observed behaviour we expect / document after live tests (fill exact WER when you run with a key):

- Taglish turns like "Magkano po ang premium for one million?" should keep both `magkano` and `premium`.
- Indonesian "Dendanya kejebak, DP MotorPlus bisa diturunin?" should keep `denda`, `DP`, `MotorPlus`.
- Yogyakarta "Nggih Pak, monggo dicek tenornya" — Whisper often normalises to standard Indonesian; we still **reply** with nggih/monggo rather than "OK sure".
- Regional-accent TTS compromise: Edge neural `id-ID-GadisNeural` is **Jakarta standard**, not Yogya. We cannot synthesise a true Javanese accent without a custom voice. That gap is listed in limitations.

Native TTS: `fil-PH-BlessicaNeural`, `id-ID-GadisNeural` via Edge TTS (no extra API key). OpenAI `tts-1` is the fallback and is **not** a native Filipino/Indonesian accent.

## At least three localization examples per market

### Philippines (vs a naive English→Filipino translation)

| # | Literal translation (wrong) | What we actually do |
|---|---|---|
| 1 | "Magkano ang premium na bayad buwan-buwan para sa seguro ng buhay?" | "Magkano po ang premium for ₱1M Term Protect?" — keep **premium**, add **po** |
| 2 | "Ang benepisyaryo ay ang asawa" as a stiff calque | "Asawa ko ang **beneficiary**" — industry English stays |
| 3 | "Kung hindi kayo magbayad, mawawala ang coverage" | "May 31-day grace; kung mag-**lapse** still, reinstatement needs new underwriting — hindi automatic." |
| 4 extra | Date "October 15, 2024" | "ika-15 ng Oktubre" / "15th of the month" depending on the customer's mix |
| 5 extra | Switching to English when they ask for a person | "Sige po, i-e-escalate kita sa **tao** sa branch" — stay in their register |

### Indonesia (vs a naive English→Bahasa translation)

| # | Literal translation (wrong) | What we actually do |
|---|---|---|
| 1 | "Biaya keterlambatan pembayaran angsuran" | "**Denda** 0,5% per hari, max 3% sebulan" |
| 2 | "Uang muka dua puluh persen" | "**DP** 20% untuk MotorPlus bekas" |
| 3 | "Pinjaman kendaraan bermotor" | "**pembiayaan** MotorPlus / MobilPlus, **tenor** 12–48 bulan, **jatuh tempo** tanggal kontrak" |
| 4 extra | Jakarta slang at a Yogya customer | Customer: "Nggih, monggo dicek tenornya." Agent: "Nggih, Pak. Tenor Bapak 36 bulan…" not "Oke gas, kita cek loan-nya ya." |
| 5 extra | Collections threat | Payment-support + callback, never "kami datang malam ini" |

## Code-switching behaviour

The agent prompt says: match the customer's mix; do not bounce into unexpected English. Fallback/escalation strings live **inside** the locale pack (`q1_voice_agent/locale.py`) in Filipino or Bahasa, not English.

## Known native-speaker / compliance gaps

- No native-speaker linguist signed off these lines; a Tagalog and a Javanese reviewer should punch through the scripts before production.
- Credit-life and collections are regulated; this prototype is not a licensed solicitation in either market.
- Whisper will still drop particles (`po`, `nggih`) on noisy audio.
- Edge TTS cannot do a regional Indonesian accent; documenting that is the required compromise.
