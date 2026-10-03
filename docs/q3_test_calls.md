# Q3 — Native-language test calls

Two markets, same grounded-agent core as Q1, **localized KB + locale pack** (not a translated India script). ASR is configured per market in `q1_voice_agent/locale.py`.

## PH cooperative Taglish lead (`ph_cooperative_taglish` · PH)

- End: None · Lead: `LD-BB9EA1E4` · file `D:\DarwixAI Assignment\data\transcripts\ph_cooperative_taglish.json`

- **Agent**: Hello po, this is Mia from ShieldLife, partner ng Banco Isla. Nire-record po namin ang tawag for quality and training. Hindi po ito hard sell — titingnan lang natin kung qualified po kayo sa term life o credit life cover. Pwede po bang makuha ang pangalan ninyo?
- **Customer**: Hello po, ako si Ana Reyes, 32, from Quezon City.
- **Agent**: Ilang taon po kayo?
- **Customer**: Gusto ko sana term life, asawa ko ang beneficiary.
- **Agent**: Ilang taon po kayo?  
  _[kb_ph_objection_handling_003 | ShieldLife - Objection & FAQ Playbook (PH) > Objection: "May Insurance Na Ako Sa Office." | objections_faq.md § Objection: "May Insurance Na Ako Sa Office." | v1.0]_
- **Customer**: Hindi po ako smoker. Magkano po ang premium for one million coverage?
- **Agent**: Whole-life participating plan. Premiums payable to age 60 or 20 years, whichever later. Builds cash value after year 3. Optional **riders**: accidental death, waiver of premium, critical illness (20 conditions, 90-day waiting, 30-day survival). Beneficiary must be named; if none, estate. "Magkano ang premium" depends on age, gender, smoker status, sum insured - never quote a number that is not on the rate card. Ilang taon po kayo?  
  _[kb_ph_product_002 | ShieldLife × Banco Isla - Product Guide (Philippines) > ShieldLife Whole Life | products.md § ShieldLife Whole Life | v1.0]_
- **Customer**: Sige po, pakicall back tomorrow evening.
- **Agent**: I will schedule a callback (a time you prefer) and save a lead summary for a licensed advisor.

## PH objection + human escalation (`ph_objection_lapse` · PH)

- End: escalated · Lead: `LD-1913947B` · file `D:\DarwixAI Assignment\data\transcripts\ph_objection_lapse.json`

- **Agent**: Hello po, this is Mia from ShieldLife, partner ng Banco Isla. Nire-record po namin ang tawag for quality and training. Hindi po ito hard sell — titingnan lang natin kung qualified po kayo sa term life o credit life cover. Pwede po bang makuha ang pangalan ninyo?
- **Customer**: This is Carlo, 40, Makati, smoker.
- **Agent**: Ilang taon po kayo?  
  _[kb_ph_objection_handling_007 | ShieldLife - Objection & FAQ Playbook (PH) > FAQ: Pwede Ba Ang Smoker? | objections_faq.md § FAQ: Pwede Ba Ang Smoker? | v1.0]_
- **Customer**: Baka mag-lapse, sayang. May insurance na ako sa office.
- **Agent**: Ilang taon po kayo?  
  _[kb_ph_objection_handling_004 | ShieldLife - Objection & FAQ Playbook (PH) > Objection: "Baka Mag-lapse, Sayang." | objections_faq.md § Objection: "Baka Mag-lapse, Sayang." | v1.0]_
- **Customer**: Gusto ko kausapin ang tao sa branch, please.
- **Agent**: Sige po, i-e-escalate kita sa tao / licensed advisor. Anong oras po kayo available for callback?

## PH mixed English finance terms + out of scope (`ph_codeswitch_creditlife` · PH)

- End: None · Lead: `None` · file `D:\DarwixAI Assignment\data\transcripts\ph_codeswitch_creditlife.json`

- **Agent**: Hello po, this is Mia from ShieldLife, partner ng Banco Isla. Nire-record po namin ang tawag for quality and training. Hindi po ito hard sell — titingnan lang natin kung qualified po kayo sa term life o credit life cover. Pwede po bang makuha ang pangalan ninyo?
- **Customer**: Hi I'm Bea, 28, Cebu. Wala akong loan sa Banco Isla.
- **Agent**: Ilang taon po kayo?  
  _[kb_ph_eligibility_underwriting_001 | ShieldLife × Banco Isla - Product Guide (Philippines) > Credit Life (bank Referral) | products.md § Credit Life (bank Referral) | v1.0]_
- **Customer**: Pwede ba credit life? Also what is ShieldLife stock price?
- **Agent**: Wala po akong exact na detalye niyan sa knowledge base namin, kaya hindi ko po i-ge-guess. Pwede po kitang i-refer sa licensed advisor sa branch.

## ID cooperative formal Bahasa (`id_cooperative_formal` · ID)

- End: None · Lead: `LD-057F1D23` · file `D:\DarwixAI Assignment\data\transcripts\id_cooperative_formal.json`

- **Agent**: Selamat siang, Bu, Pak. Saya Sari dari MitraDana. Panggilan ini direkam untuk kualitas layanan. Saya hubungi terkait pembiayaan MitraDana — cek kelayakan atau pengingat cicilan, bukan penagihan kasar. Boleh minta nama Bapak/Ibu?
- **Customer**: Selamat siang, nama saya Budi Santoso, usia 35, tinggal di Jakarta.
- **Agent**: Usia berapa tahun?  
  _[kb_id_faq_011 | MitraDana - Kepatuhan Panggilan > Data Yang Boleh Diambil | kepatuhan.md § Data Yang Boleh Diambil | v1.0]_
- **Customer**: Saya mau tanya DanaCepat, plafon 20 juta, tenor 12 bulan. Berapa angsurannya?
- **Agent**: Pinjaman tanpa agunan. Plafon Rp 5 juta - Rp 50 juta. Tenor 6, 12, 18, 24 bulan. Bunga flat sesuai rate card cabang. **DP** tidak berlaku (karena bukan kendaraan). **Cicilan / angsuran** jatuh tempo setiap tanggal kontrak. **Denda** keterlambatan 0,5% per hari dari angsuran, maksimum 3% per bulan. Contoh: plafon Rp 20 juta, tenor 12 bulan, angsuran sekitar Rp 2,05 juta / bulan (indikatif, belum termasuk biaya admin). Usia berapa tahun?  
  _[kb_id_premium_pricing_001 | MitraDana Multifinance - Produk & Aturan Cicilan (Indonesia) > DanaCepat (pembiayaan Dana Tunai) | produk.md § DanaCepat (pembiayaan Dana Tunai) | v1.0]_
- **Customer**: Baik, silakan callback besok sore.
- **Agent**: I will schedule a callback (callback besok sore.) and save a lead summary for a licensed advisor.

## ID colloquial + denda objection + mixed loanwords (`id_colloquial_denda` · ID)

- End: None · Lead: `None` · file `D:\DarwixAI Assignment\data\transcripts\id_colloquial_denda.json`

- **Agent**: Selamat siang, Bu, Pak. Saya Sari dari MitraDana. Panggilan ini direkam untuk kualitas layanan. Saya hubungi terkait pembiayaan MitraDana — cek kelayakan atau pengingat cicilan, bukan penagihan kasar. Boleh minta nama Bapak/Ibu?
- **Customer**: Halo Mbak, aku Rina, 29 tahun, di Bandung.
- **Agent**: Siapa nama Bapak/Ibu?
- **Customer**: Cicilannya telat, dendanya kejebak mahal banget dong. DP MotorPlus bisa diturunin?
- **Agent**: Disetujui: "Saya paham, Pak/Bu. Denda 0,5% per hari, max 3% sebulan, itu sesuai kontrak. Kalau Bapak bayar hari ini sebelum pukul 20.00, kita kunci denda yang sudah jalan saja - tidak nambah malam ini. Kalau masih berat, saya bisa minta petugas cabang tawarkan reschedule." Jangan: hapus denda sendiri. Siapa nama Bapak/Ibu?  
  _[kb_id_exclusions_001 | MitraDana - Keberatan, FAQ, Dan Eskalasi > Keberatan: "Dendanya Kejebak, Mahal." | keberatan_faq.md § Keberatan: "Dendanya Kejebak, Mahal." | v1.0]_
- **Customer**: Ya udah, hubungi aku setelah gajian tanggal 10.
- **Agent**: Siapa nama Bapak/Ibu?  
  _[kb_id_faq_003 | MitraDana - Keberatan, FAQ, Dan Eskalasi > Keberatan: "Nanti Saja, Gaji Belum Masuk." | keberatan_faq.md § Keberatan: "Nanti Saja, Gaji Belum Masuk." | v1.0]_

## ID Yogyakarta phrasing (regional) + human ask (`id_jawa_accent_escalation` · ID)

- End: escalated · Lead: `LD-60063C25` · file `D:\DarwixAI Assignment\data\transcripts\id_jawa_accent_escalation.json`

- **Agent**: Selamat siang, Bu, Pak. Saya Sari dari MitraDana. Panggilan ini direkam untuk kualitas layanan. Saya hubungi terkait pembiayaan MitraDana — cek kelayakan atau pengingat cicilan, bukan penagihan kasar. Boleh minta nama Bapak/Ibu?
- **Customer**: Nggih Mbak, kula Pak Slamet, umur 47, Yogyakarta.
- **Agent**: Siapa nama Bapak/Ibu?  
  _[kb_id_faq_014 | MitraDana Multifinance - Produk & Aturan Cicilan (Indonesia) > Regional (Jawa / Yogyakarta) | produk.md § Regional (Jawa / Yogyakarta) | v1.0]_
- **Customer**: Monggo dicek tenor MobilPlus kula, jatuh tempo kapan, angsuran berapa.
- **Agent**: Siapa nama Bapak/Ibu?  
  _[kb_id_faq_006 | MitraDana - Keberatan, FAQ, Dan Eskalasi > Nada Jawa | keberatan_faq.md § Nada Jawa | v1.0]_
- **Customer**: Kula nyuwun ngomong kalih petugas cabang, nggih.
- **Agent**: Baik, saya alihkan ke petugas. Kapan Bapak/Ibu bisa dihubungi kembali?
