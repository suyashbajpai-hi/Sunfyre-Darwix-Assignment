# Q1 — Test call transcripts and results

Use case: **health-insurance lead qualification** for fictional Sentinel Health Insurance. The bot retrieves from the Question 2 knowledge base; FAQs and objections are not hardcoded.

Scenarios: 5 · Leads: 3 · Escalations: 1 · Unavailable fallback used: 3

## Cooperative customer (`q1_cooperative`)

- Call ID: `C-F6CED511`  |  Lead: `LD-82B8E38C`  |  End: None
- Slots: `{"name": "Rohan Mehta", "age": "34", "city": "Pune", "members": "Family Shield with 10 lakh cover sounds right.", "conditions": "none", "sum_insured": "10 lakh"}`
- Qualification: `{"status": "Qualified", "plan": "Family Shield", "reasons": ["age 34 is inside 18–65; suggested plan Family Shield"], "zone": "A", "ppme_required": false, "disclaimers": ["Eligibility is preliminary and subject to underwriting; this is not an approval.", "Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting."]}`
- Transcript file: `D:\DarwixAI Assignment\data\transcripts\q1_cooperative.json`

| Who | Text | Grounding |
|---|---|---|
| agent | Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation. I am calling to see if a Sentinel health plan could be a fit for you or your family — this is only a preliminary qualification, not an approval. May I have your name to begin? |  |
| customer | Hi, my name is Rohan Mehta. |  |
| agent | What is your age? | conf=0.31<br>[kb_in_customer_service_004 | Sentinel Health - Customer Service Log Export (Jan 2024) | docs/customer_service_log.txt | v1.0]<br>[kb_in_forms_003 | Health Insurance Proposal Form > Insured Members | forms/proposal_form.json § Insured Members | v1.0] |
| customer | I am 34 years old, I live in Pune. |  |
| agent | Who would you like to cover — just yourself, or spouse and children as well? | conf=0.405<br>[kb_in_premium_pricing_006 | FAQ > Frequently Asked Questions > Premiums And Payment > How Much Does It Cost? | website/faq.html § How Much Does It Cost? | v1.0]<br>[kb_in_eligibility_underwriting_003 | Sentinel Health - Underwriting & Qualification Rules (Internal) > Entry Age | docs/underwriting_rules.md § Entry Age | v1.0] |
| customer | I want to cover myself, my wife and one child. |  |
| agent | Any declared health conditions I should note, such as diabetes or blood pressure? | conf=0.418<br>[kb_in_premium_pricing_006 | FAQ > Frequently Asked Questions > Premiums And Payment > How Much Does It Cost? | website/faq.html § How Much Does It Cost? | v1.0]<br>[kb_in_product_019 | Plans > Our Health Insurance Plans > Sentinel Family Shield | website/plans.html § Sentinel Family Shield | v1.0] |
| customer | No health issues, we are all healthy. |  |
| agent | Based on what you have shared, preliminary status is Qualified for Family Shield. age 34 is inside 18–65; suggested plan Family Shield. Eligibility is preliminary and subject to underwriting; this is not an approval. Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting. I can create a lead and arrange a callback with a licensed advisor. What time works for you? | conf=0.526<br>[kb_in_objection_handling_004 | Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "I Am Young And Healthy, I Do Not Need It." | docs/objection_handling_playbook.md § Objection: "I Am Young And Healthy, I Do Not Need It." | v1.0]<br>[kb_in_product_011 | Sentinel Family Shield - Policy Wording > Coverage > Day Care Treatment: All Day Care Procedures Are Covered. | docs/policy_wording_family_shield.pdf § page 1 | v1.0] |
| customer | Family Shield with 10 lakh cover sounds right. |  |
| agent | Based on what you have shared, preliminary status is Qualified for Family Shield. age 34 is inside 18–65; suggested plan Family Shield. Eligibility is preliminary and subject to underwriting; this is not an approval. Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting. I can create a lead and arrange a callback with a licensed advisor. What time works for you? | conf=0.55<br>[kb_in_product_019 | Plans > Our Health Insurance Plans > Sentinel Family Shield | website/plans.html § Sentinel Family Shield | v1.0]<br>[kb_in_premium_pricing_006 | FAQ > Frequently Asked Questions > Premiums And Payment > How Much Does It Cost? | website/faq.html § How Much Does It Cost? | v1.0] |
| customer | Please create the lead and call me tomorrow at 6 pm. |  |
| agent | Based on what you have shared, preliminary status is Qualified for Family Shield. age 34 is inside 18–65; suggested plan Family Shield. Eligibility is preliminary and subject to underwriting; this is not an approval. Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting. I can create a lead and arrange a callback with a licensed advisor. What time works for you? | conf=0.435<br>[kb_in_compliance_005 | Mandatory Call Disclosures & Conduct Rules (Compliance) > Do-not-call | docs/compliance_disclosures.md § Do-not-call | v1.0]<br>[kb_in_partnership_005 | Branch Partners > Become A Sentinel Branch Partner > Contact The Partnerships Team | website/partners.html § Contact The Partnerships Team | v1.0] |

## Objection — too expensive / employer cover (`q1_objection`)

- Call ID: `C-80248999`  |  Lead: `LD-1DF2960C`  |  End: None
- Slots: `{"name": "Priya", "age": "30", "city": "Bengaluru", "callback_time": "call me back Friday."}`
- Qualification: `{"status": "Qualified", "plan": "Essential", "reasons": ["age 30 is inside 18–65; suggested plan Essential"], "zone": "A", "ppme_required": false, "disclaimers": ["Eligibility is preliminary and subject to underwriting; this is not an approval.", "Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting."]}`
- Transcript file: `D:\DarwixAI Assignment\data\transcripts\q1_objection.json`

| Who | Text | Grounding |
|---|---|---|
| agent | Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation. I am calling to see if a Sentinel health plan could be a fit for you or your family — this is only a preliminary qualification, not an approval. May I have your name to begin? |  |
| customer | This is Priya. |  |
| agent | What is your age? | conf=0.77<br>[kb_in_customer_service_007 | Sentinel Health - Customer Service Log Export (Jan 2024) | docs/customer_service_log.txt | v1.0] |
| customer | I am 30, from Bengaluru. |  |
| agent | Who would you like to cover — just yourself, or spouse and children as well? | conf=0.53<br>[kb_in_premium_pricing_004 | Sentinel Health - Underwriting & Qualification Rules (Internal) > Geography | docs/underwriting_rules.md § Geography | v1.0]<br>[kb_in_customer_service_002 | Sentinel Health - Customer Service Log Export (Jan 2024) | docs/customer_service_log.txt | v1.0] |
| customer | Just myself for now. |  |
| agent | Who would you like to cover — just yourself, or spouse and children as well? |  |
| customer | It is too expensive, I already have cover from my employer. |  |
| agent | "That is a great start. Employer cover ends when you change jobs or retire, and most group plans are Rs 3 to 5 lakh shared across the family. A personal policy bought while you are young keeps waiting periods served and locks in lifetime renewability. Many customers keep both - the personal policy as a top-up." Who would you like to cover — just yourself, or spouse and children as well? | conf=0.674<br>[kb_in_objection_handling_003 | Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "I Already Have Cover From My Employer." | docs/objection_handling_playbook.md § Objection: "I Already Have Cover From My Employer." | v1.0]<br>[kb_in_objection_handling_002 | Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "It Is Too Expensive." | docs/objection_handling_playbook.md § Objection: "It Is Too Expensive." | v1.0] |
| customer | Okay, send me a summary and call me back Friday. |  |
| agent | I will schedule a callback (call me back Friday.) and save a lead summary for a licensed advisor. Eligibility is preliminary and subject to underwriting; this is not an approval. Any premium mentioned is indicative, exclusive of 18% GST, and subject to underwriting. | conf=0.733<br>[kb_in_objection_handling_006 | Objection Handling Playbook - Health Insurance Tele-Sales > Objection: "I Need To Discuss With My Spouse / Family." | docs/objection_handling_playbook.md § Objection: "I Need To Discuss With My Spouse / Family." | v1.0]<br>[kb_in_claims_003 | Sentinel Family Shield - Policy Wording > Claims > Reimbursement: Submit The Claim Form, Discharge Summary, Original Bills And Receipts, | docs/policy_wording_family_shield.pdf § page 2 | v1.0] |

## Incomplete then conflicting details (`q1_conflicting`)

- Call ID: `C-95D5270C`  |  Lead: `None`  |  End: None
- Slots: `{"name": "Imran", "age": "40", "age_conflict": "stated age 40 vs DOB year 1978 (~48)", "city": "Delhi"}`
- Qualification: `{"status": "Referred", "plan": null, "reasons": ["stated age conflicts with date of birth — do not promise eligibility; clarify or refer"], "zone": "A", "ppme_required": false, "disclaimers": ["Eligibility is preliminary and subject to underwriting."]}`
- Transcript file: `D:\DarwixAI Assignment\data\transcripts\q1_conflicting.json`

| Who | Text | Grounding |
|---|---|---|
| agent | Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation. I am calling to see if a Sentinel health plan could be a fit for you or your family — this is only a preliminary qualification, not an approval. May I have your name to begin? |  |
| customer | Hello. |  |
| agent | May I have your full name? |  |
| customer | Name is Imran. |  |
| agent | What is your age? | conf=0.563<br>[kb_in_customer_service_006 | Sentinel Health - Customer Service Log Export (Jan 2024) | docs/customer_service_log.txt | v1.0]<br>[kb_in_forms_003 | Health Insurance Proposal Form > Insured Members | forms/proposal_form.json § Insured Members | v1.0] |
| customer | I am 40 but my date of birth is 1978. |  |
| agent | Which city are you based in? | conf=0.518<br>[kb_in_forms_003 | Health Insurance Proposal Form > Insured Members | forms/proposal_form.json § Insured Members | v1.0]<br>[kb_in_forms_001 | Health Insurance Proposal Form > Proposer Details | forms/proposal_form.json § Proposer Details | v1.0] |
| customer | I live in Delhi. |  |
| agent | Who would you like to cover — just yourself, or spouse and children as well? | conf=0.457<br>[kb_in_premium_pricing_004 | Sentinel Health - Underwriting & Qualification Rules (Internal) > Geography | docs/underwriting_rules.md § Geography | v1.0] |
| customer | Father is 82, can he buy a policy? |  |
| agent | Ticket #CS-24-0163 Customer: Imran Sheikh, [PHONE] Policy: none yet (prospect) Issue: Asked whether his father aged 82 can be covered. Resolution: Senior Care entry age is 61 to 80. Not eligible for a new policy at 82. Suggested checking whether the father has an existing policy that can be ported or renewed (renewal is lifetime). Lead closed - not eligible. Who would you like to cover — just yourself, or spouse and children as well? | conf=0.881<br>[kb_in_customer_service_006 | Sentinel Health - Customer Service Log Export (Jan 2024) | docs/customer_service_log.txt | v1.0]<br>[kb_in_product_015 | FAQ > Frequently Asked Questions > Buying A Policy > Who Can Buy A Sentinel Health Policy? | website/faq.html § Who Can Buy A Sentinel Health Policy? | v1.0] |

## Out-of-scope question (must not invent) (`q1_oos`)

- Call ID: `C-647CB421`  |  Lead: `None`  |  End: None
- Slots: `{"name": "Neha", "city": "Chennai"}`
- Qualification: `{"status": "Incomplete", "plan": null, "reasons": ["still need: age"], "zone": null, "ppme_required": false, "disclaimers": []}`
- Transcript file: `D:\DarwixAI Assignment\data\transcripts\q1_oos.json`

| Who | Text | Grounding |
|---|---|---|
| agent | Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation. I am calling to see if a Sentinel health plan could be a fit for you or your family — this is only a preliminary qualification, not an approval. May I have your name to begin? |  |
| customer | Hi I am Neha, 29, from Chennai, just myself, no conditions. |  |
| agent | What is your age? |  |
| customer | What is the stock price of Sentinel Health? |  |
| agent | I do not have that information in our knowledge base, so I will not guess. I can connect you with a licensed advisor who can check and call you back. |  |
| customer | Do you sell motor insurance? |  |
| agent | I do not have that information in our knowledge base, so I will not guess. I can connect you with a licensed advisor who can check and call you back. |  |
| customer | Who is your CEO? |  |
| agent | I do not have that information in our knowledge base, so I will not guess. I can connect you with a licensed advisor who can check and call you back. |  |

## Human-assistance request (`q1_human`)

- Call ID: `C-6FDCFD33`  |  Lead: `LD-B7821290`  |  End: escalated
- Slots: `{"name": "Arjun"}`
- Qualification: `{"status": "Incomplete", "plan": null, "reasons": ["still need: age, city"], "zone": null, "ppme_required": false, "disclaimers": []}`
- Transcript file: `D:\DarwixAI Assignment\data\transcripts\q1_human.json`

| Who | Text | Grounding |
|---|---|---|
| agent | Hello, this is Aisha from Sentinel Health Insurance. This call is being recorded for quality and training purposes. Insurance is the subject matter of solicitation. I am calling to see if a Sentinel health plan could be a fit for you or your family — this is only a preliminary qualification, not an approval. May I have your name to begin? |  |
| customer | My name is Arjun, 45, Mumbai. |  |
| agent | What is your age? | conf=0.336<br>[kb_in_premium_pricing_004 | Sentinel Health - Underwriting & Qualification Rules (Internal) > Geography | docs/underwriting_rules.md § Geography | v1.0]<br>[kb_in_eligibility_underwriting_007 | FAQ > Frequently Asked Questions > Buying A Policy > Do I Need A Medical Test Before Buying? | website/faq.html § Do I Need A Medical Test Before Buying? | v1.0] |
| customer | I want to speak to a human advisor please, not a bot. |  |
| agent | Of course — I will connect you with a human advisor. Let me capture a callback time. | escalate |
