# Q2 - Retrieval Test Results

Retrieval mode: **bm25** | Total: 22 | Correct: 20 | Partially correct: 2 | Incorrect: 0

Verdict rules: *correct* = top-1 record contains the expected evidence with high grounding confidence; *partially correct* = evidence in top-3 or confidence tier medium; *incorrect* = evidence absent. For out-of-scope questions, *correct* means the system reports low confidence so the voice agent says the information is unavailable instead of inventing an answer.

## 1. What is the difference between Family Shield and Essential?

- **Intent type:** product  |  **Market:** IN
- **Retrieved record:** `kb_in_product_021` - Plans > Our Health Insurance Plans > Plan Comparison
- **Source reference:** website/plans.html § table
- **Excerpt:** Type - Essential: Individual; Family Shield: Family floater; Senior Care: Individual / 2-adult floater.
Entry age - Essential: 18-65; Family Shield: 18-65 (children 91 days-25 years); Senior Care: 61-80.
Sum insured (Rs)...
- **Confidence:** 0.673 (tier: high)
- **Relevance explanation:** matched terms: family, shield, essential, comparison; bm25=17.86
- **Verdict:** **correct** - top-1 record contains expected evidence

## 2. Does Senior Care have a co-pay?

- **Intent type:** product  |  **Market:** IN
- **Retrieved record:** `kb_in_faq_001` - FAQ > Frequently Asked Questions > Policy Servicing > Is There A Co-pay?
- **Source reference:** website/faq.html § Is There A Co-pay?
- **Excerpt:** Essential has a 10% co-payment on every claim. Family Shield has no co-payment unless a member was 61 or older at entry, in which case 20% applies to that member. Senior Care has a 20% co-payment, which can be removed wi...
- **Confidence:** 0.908 (tier: high)
- **Relevance explanation:** matched terms: senior, care, co-payment; bm25=8.85
- **Verdict:** **correct** - top-1 record contains expected evidence

## 3. How much does Family Shield cost for two adults and one child?

- **Intent type:** faq  |  **Market:** IN
- **Retrieved record:** `kb_in_premium_pricing_006` - FAQ > Frequently Asked Questions > Premiums And Payment > How Much Does It Cost?
- **Source reference:** website/faq.html § How Much Does It Cost?
- **Excerpt:** Premium depends on plan, age of the oldest member, sum insured, city tier and any loadings. For example, a 30-year-old buying Sentinel Essential with Rs 5 lakh sum insured pays about Rs 7,200 a year plus GST. A family of...
- **Confidence:** 0.916 (tier: high)
- **Relevance explanation:** matched terms: family, shield, cost, two, adult, one, child, premium; bm25=20.36
- **Verdict:** **correct** - top-1 record contains expected evidence

## 4. What is the waiting period for pre-existing diseases?

- **Intent type:** policy  |  **Market:** IN
- **Retrieved record:** `kb_in_waiting_periods_004` - FAQ > Frequently Asked Questions > Buying A Policy > What Is A Pre-existing Disease (PED)?
- **Source reference:** website/faq.html § What Is A Pre-existing Disease (PED)?
- **Excerpt:** A pre-existing disease is any condition, ailment or injury that was diagnosed, or for which medical advice or treatment was received, within 48 months before your first policy with us. pre-existing disease are covered af...
- **Confidence:** 0.962 (tier: high)
- **Relevance explanation:** matched terms: waiting, period, pre-existing, disease; bm25=10.71
- **Verdict:** **correct** - top-1 record contains expected evidence

## 5. What happens if I miss a premium payment?

- **Intent type:** policy  |  **Market:** IN
- **Retrieved record:** `kb_in_premium_pricing_008` - FAQ > Frequently Asked Questions > Premiums And Payment > What Happens If I Miss A Premium Payment?
- **Source reference:** website/faq.html § What Happens If I Miss A Premium Payment?
- **Excerpt:** You get a grace period of 30 days (15 days for monthly mode) to pay without losing continuity benefits. If you do not pay within the grace period, the policy lapses and any claim arising during the lapse period is not pa...
- **Confidence:** 1.0 (tier: high)
- **Relevance explanation:** matched terms: happen, miss, premium, payment; bm25=19.46
- **Verdict:** **correct** - top-1 record contains expected evidence

## 6. Is maternity covered and after how long?

- **Intent type:** policy  |  **Market:** IN
- **Retrieved record:** `kb_in_waiting_periods_003` - Sentinel Family Shield - Policy Wording > Waiting Periods > Maternity Waiting Period: 24 Months.
- **Source reference:** docs/policy_wording_family_shield.pdf § page 2
- **Excerpt:** C.4 Maternity waiting period: 24 months. C.5 Waiting periods already served under a previous indemnity health policy are credited on portability as per IRDAI guidelines....
- **Confidence:** 0.621 (tier: high)
- **Relevance explanation:** matched terms: maternity, waiting, period; bm25=17.64
- **Verdict:** **correct** - top-1 record contains expected evidence

## 7. I have controlled type 2 diabetes, can I get a policy?

- **Intent type:** qualification  |  **Market:** IN
- **Retrieved record:** `kb_in_eligibility_underwriting_008` - FAQ > Frequently Asked Questions > Buying A Policy > Have Diabetes. Can I Still Buy?
- **Source reference:** website/faq.html § Have Diabetes. Can I Still Buy?
- **Excerpt:** Yes, in most cases. Controlled Type 2 diabetes (HbA1c below 8) is accepted with a 36-month pre-existing disease waiting period and, depending on age, a premium loading of 10% to 25%. Insulin-dependent diabetes or diabete...
- **Confidence:** 1.0 (tier: high)
- **Relevance explanation:** matched terms: controlled, type, diabete, policy; bm25=13.87
- **Verdict:** **partially correct** - evidence in top-3 but not ranked first

## 8. Can my father who is 82 years old buy a policy?

- **Intent type:** qualification  |  **Market:** IN
- **Retrieved record:** `kb_in_customer_service_006` - Sentinel Health - Customer Service Log Export (Jan 2024)
- **Source reference:** docs/customer_service_log.txt § 
- **Excerpt:** Ticket #CS-24-0163
Customer: Imran Sheikh, [PHONE]
Policy: none yet (prospect)
Issue: Asked whether his father aged 82 can be covered.
Resolution: Senior Care entry age is 61 to 80. Not eligible for a new policy at 82. S...
- **Confidence:** 0.765 (tier: high)
- **Relevance explanation:** matched terms: father, 82, policy, senior, care, age; bm25=16.53
- **Verdict:** **correct** - top-1 record contains expected evidence

## 9. Do I need a medical test if I am 50?

- **Intent type:** qualification  |  **Market:** IN
- **Retrieved record:** `kb_in_eligibility_underwriting_007` - FAQ > Frequently Asked Questions > Buying A Policy > Do I Need A Medical Test Before Buying?
- **Source reference:** website/faq.html § Do I Need A Medical Test Before Buying?
- **Excerpt:** If you are 45 or younger and have no pre-existing disease, no medical test is required - you can buy on the basis of your health declaration. If you are above 45, or you declare any pre-existing disease such as diabetes,...
- **Confidence:** 0.669 (tier: high)
- **Relevance explanation:** matched terms: medical, test; bm25=8.71
- **Verdict:** **correct** - top-1 record contains expected evidence

## 10. Customer says it is too expensive, how should I respond?

- **Intent type:** objection  |  **Market:** IN
- **Retrieved record:** `kb_in_objection_handling_002` - Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "It Is Too Expensive."
- **Source reference:** docs/objection_handling_playbook.md § Objection: "It Is Too Expensive."
- **Excerpt:** Approved response: Acknowledge, then reframe to daily cost and risk. "I understand - let me put it in perspective. For a 30-year-old, Sentinel Essential with 5 lakh cover costs around Rs 7,200 a year, which is about Rs 2...
- **Confidence:** 0.581 (tier: high)
- **Relevance explanation:** matched terms: too, expensive; bm25=10.60
- **Verdict:** **correct** - top-1 record contains expected evidence

## 11. Customer already has insurance from employer

- **Intent type:** objection  |  **Market:** IN
- **Retrieved record:** `kb_in_objection_handling_003` - Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "I Already Have Cover From My Employer."
- **Source reference:** docs/objection_handling_playbook.md § Objection: "I Already Have Cover From My Employer."
- **Excerpt:** Approved response: "That is a great start. Employer cover ends when you change jobs or retire, and most group plans are Rs 3 to 5 lakh shared across the family. A personal policy bought while you are young keeps waiting ...
- **Confidence:** 1.0 (tier: high)
- **Relevance explanation:** matched terms: customer, already, insurance, employer; bm25=15.07
- **Verdict:** **correct** - top-1 record contains expected evidence

## 12. Insurance companies always reject claims

- **Intent type:** objection  |  **Market:** IN
- **Retrieved record:** `kb_in_objection_handling_005` - Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "Insurance Companies Always Reject Claims."
- **Source reference:** docs/objection_handling_playbook.md § Objection: "Insurance Companies Always Reject Claims."
- **Excerpt:** Approved response: "I understand the concern. Sentinel's claim settlement ratio for FY 2023-24 was 96.4%, and we process claims in-house without a TPA. The main reason claims are rejected anywhere is non-disclosure of a ...
- **Confidence:** 1.0 (tier: high)
- **Relevance explanation:** matched terms: insurance, company, alway, reject, claim, rejected, non-disclosure; bm25=26.07
- **Verdict:** **correct** - top-1 record contains expected evidence

## 13. Which disclosures are mandatory at the start of a sales call?

- **Intent type:** compliance  |  **Market:** IN
- **Retrieved record:** `kb_in_compliance_002` - Mandatory Call Disclosures & Conduct Rules (Compliance) > Mandatory Disclosures
- **Source reference:** docs/compliance_disclosures.md § Mandatory Disclosures
- **Excerpt:** 1. **Identity & purpose** (start of call): State the agent's name, that the call is from Sentinel Health Insurance, and the purpose of the call.
2. **Call recording consent** (start of call): "This call is being recorded...
- **Confidence:** 0.84 (tier: high)
- **Relevance explanation:** matched terms: disclosure, mandatory, start, call; bm25=16.42
- **Verdict:** **correct** - top-1 record contains expected evidence

## 14. Can I port my existing policy from another insurer?

- **Intent type:** faq  |  **Market:** IN
- **Retrieved record:** `kb_in_policy_terms_006` - FAQ > Frequently Asked Questions > Policy Servicing > Can I Port My Existing Policy To Sentinel?
- **Source reference:** website/faq.html § Can I Port My Existing Policy To Sentinel?
- **Excerpt:** Yes. Under IRDAI portability rules you can move to Sentinel at renewal time and carry forward the waiting periods you have already served with your previous insurer. Apply at least 45 days before your current policy expi...
- **Confidence:** 0.862 (tier: high)
- **Relevance explanation:** matched terms: port, existing, policy, insurer, portability; bm25=19.33
- **Verdict:** **correct** - top-1 record contains expected evidence

## 15. Is cosmetic surgery covered?

- **Intent type:** policy  |  **Market:** IN
- **Retrieved record:** `kb_in_exclusions_001` - Sentinel Family Shield - Policy Wording > Exclusions > Cosmetic Or Plastic Surgery Unless For Reconstruction Following An Accident, Burn Or
- **Source reference:** docs/policy_wording_family_shield.pdf § page 2
- **Excerpt:** D.1 Cosmetic or plastic surgery unless for reconstruction following an accident, burn or cancer....
- **Confidence:** 0.845 (tier: high)
- **Relevance explanation:** matched terms: cosmetic, surgery; bm25=12.55
- **Verdict:** **correct** - top-1 record contains expected evidence

## 16. What is the stock price of Sentinel Health?

- **Intent type:** out_of_scope  |  **Market:** IN
- **Retrieved record:** `kb_in_compliance_003` - Mandatory Call Disclosures & Conduct Rules (Compliance) > Prohibited Statements (risky Statements)
- **Source reference:** docs/compliance_disclosures.md § Prohibited Statements (risky Statements)
- **Excerpt:** Agents and voice bots must NOT:
- say or imply cover is "guaranteed", "approved", "100% covered", or that there are "no exclusions";
- promise claim settlement, a settlement timeline shorter than the documented SLA, or "...
- **Confidence:** 0.29 (tier: low)
- **Relevance explanation:** matched terms: price, premium; bm25=4.51
- **Verdict:** **correct** - low confidence -> agent will say information is unavailable

## 17. Who is the CEO of Sentinel?

- **Intent type:** out_of_scope  |  **Market:** IN
- **Retrieved record:** `kb_in_customer_service_001` - Sentinel Health - Customer Service Log Export (Jan 2024)
- **Source reference:** docs/customer_service_log.txt § 
- **Excerpt:** SENTINEL HEALTH - CUSTOMER SERVICE LOG EXPORT (Jan 2024)...
- **Confidence:** 0.021 (tier: low)
- **Relevance explanation:** matched terms: sentinel; bm25=0.21
- **Verdict:** **correct** - low confidence -> agent will say information is unavailable

## 18. Do you sell motor insurance?

- **Intent type:** out_of_scope  |  **Market:** IN
- **Retrieved record:** `kb_in_company_001` - Sentinel Health Insurance > Health Cover That Actually Pays When It Matters > About Sentinel Health Insurance
- **Source reference:** website/index.html § About Sentinel Health Insurance
- **Excerpt:** Sentinel Health Insurance Company Ltd. is a standalone health insurer licensed by the Insurance Regulatory and Development Authority of India (IRDAI), registration no. 162. Our head office is in Pune, Maharashtra and we ...
- **Confidence:** 0.142 (tier: low)
- **Relevance explanation:** matched terms: insurance; bm25=2.15
- **Verdict:** **correct** - low confidence -> agent will say information is unavailable

## 19. Magkano ang premium for ShieldLife Term Protect one million?

- **Intent type:** product  |  **Market:** PH
- **Retrieved record:** `kb_ph_product_001` - ShieldLife × Banco Isla - Product Guide (Philippines) > ShieldLife Term Protect
- **Source reference:** products.md § ShieldLife Term Protect
- **Excerpt:** Term life with level premium. Coverage 5, 10, 15 or 20 years, or up to age 65. Sum insured ₱500,000 to ₱10,000,000. Medical exam required above ₱3,000,000 or age 50. No cash value. If the policy **lapses** after the 31-d...
- **Confidence:** 0.632 (tier: high)
- **Relevance explanation:** matched terms: premium, shieldlife, term, protect; bm25=14.45
- **Verdict:** **correct** - top-1 record contains expected evidence

## 20. What happens if the policy lapses in the Philippines?

- **Intent type:** policy  |  **Market:** PH
- **Retrieved record:** `kb_ph_product_003` - ShieldLife × Banco Isla - Product Guide (Philippines) > Bancassurance Conduct
- **Source reference:** products.md § Bancassurance Conduct
- **Excerpt:** - Face-to-face or recorded call from a licensed advisor / AI qualifier is a solicitation.
- Customer may mix English and Filipino (Taglish). Answer in the same mix. Keep industry words: premium, policy, beneficiary, ride...
- **Confidence:** 0.606 (tier: high)
- **Relevance explanation:** matched terms: policy, lapse, philippine; bm25=7.56
- **Verdict:** **partially correct** - evidence in top-3 but not ranked first

## 21. Berapa denda keterlambatan cicilan MitraDana?

- **Intent type:** policy  |  **Market:** ID
- **Retrieved record:** `kb_id_premium_pricing_001` - MitraDana Multifinance - Produk & Aturan Cicilan (Indonesia) > DanaCepat (pembiayaan Dana Tunai)
- **Source reference:** produk.md § DanaCepat (pembiayaan Dana Tunai)
- **Excerpt:** Pinjaman tanpa agunan. Plafon Rp 5 juta - Rp 50 juta. Tenor 6, 12, 18, 24 bulan. Bunga flat sesuai rate card cabang. **DP** tidak berlaku (karena bukan kendaraan). **Cicilan / angsuran** jatuh tempo setiap tanggal kontra...
- **Confidence:** 0.643 (tier: high)
- **Relevance explanation:** matched terms: denda, keterlambatan, cicilan, mitradana, angsuran; bm25=16.52
- **Verdict:** **correct** - top-1 record contains expected evidence

## 22. Berapa DP MotorPlus bekas?

- **Intent type:** product  |  **Market:** ID
- **Retrieved record:** `kb_id_faq_013` - MitraDana Multifinance - Produk & Aturan Cicilan (Indonesia) > MotorPlus
- **Source reference:** produk.md § MotorPlus
- **Excerpt:** Pembiayaan motor baru atau bekas (maks. 8 tahun). DP mulai 10% (baru) / 20% (bekas). Tenor 12-48 bulan. BPKB dipegang MitraDana sampai lunas. Asuransi kendaraan wajib....
- **Confidence:** 0.742 (tier: high)
- **Relevance explanation:** matched terms: dp, motorplu, beka; bm25=15.62
- **Verdict:** **correct** - top-1 record contains expected evidence
