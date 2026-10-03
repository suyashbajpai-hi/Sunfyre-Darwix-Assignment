"""Generate the PDF source documents for the knowledge base.

Uses a minimal hand-rolled PDF writer (Helvetica, one text block per page) so
the repository has no dependency on reportlab. Run once:

    python -m q2_knowledge_base.sources.build_pdf_sources
"""
from __future__ import annotations

import textwrap
from pathlib import Path

HERE = Path(__file__).parent / "docs"

POLICY_WORDING = """
SENTINEL FAMILY SHIELD - POLICY WORDING
UIN: SENHLIP24001V012324 | Version 1.2 | Effective April 1, 2024

SECTION A - DEFINITIONS

A.1 "Hospital" means an institution registered with local authorities having at least 10 in-patient beds (15 in towns with population above 10 lakh), qualified nursing staff round the clock, a qualified medical practitioner in charge round the clock, and a fully equipped operation theatre.

A.2 "Pre-existing Disease" means any condition, ailment, injury or disease that is diagnosed by a physician within 48 months prior to the effective date of the policy, or for which medical advice or treatment was recommended by or received from a physician within 48 months prior to the effective date.

A.3 "Co-payment" means a cost-sharing requirement under which the policyholder bears a specified percentage of the admissible claim amount. A co-payment does not reduce the sum insured.

A.4 "Grace Period" means the specified period of time immediately following the premium due date during which a payment can be made to renew or continue the policy without loss of continuity benefits. Grace period is 30 days for annual, half-yearly and quarterly modes and 15 days for monthly mode.

A.5 "Day Care Treatment" means medical treatment or surgical procedure undertaken under general or local anaesthesia in a hospital or day care centre in less than 24 hours because of technological advancement.

SECTION B - COVERAGE

B.1 In-patient Hospitalisation: reasonable and customary charges for room, boarding, nursing, ICU, surgeon, anaesthetist, consultants, operation theatre, medicines, diagnostics, and implants, for hospitalisation of at least 24 consecutive hours.

B.2 Pre-hospitalisation medical expenses incurred up to 60 days before admission and Post-hospitalisation expenses up to 90 days after discharge, related to the same illness.

B.3 Day Care Treatment: all day care procedures are covered.

B.4 Road Ambulance: up to Rs 3,000 per hospitalisation.

B.5 AYUSH Treatment: in-patient treatment under Ayurveda, Yoga, Unani, Siddha and Homeopathy at a government hospital or an institute recognised by the government, up to the sum insured.

B.6 Restoration of Sum Insured: if the sum insured and accrued no-claim bonus are exhausted during a policy year, 100% of the base sum insured is restored once in that year, usable only for an illness unrelated to those for which claims were already paid. Restored amount cannot be carried forward.

B.7 No-Claim Bonus: 10% of base sum insured for every claim-free policy year, cumulative to a maximum of 50%. In a year with a claim the bonus reduces by 10%, never below zero.

B.8 Maternity: delivery expenses including pre-natal and post-natal expenses up to Rs 50,000 per delivery, maximum two deliveries during the lifetime of the policy, available after 24 months of continuous coverage of both the mother and the father. Newborn is covered under this limit from birth until 90 days, and may be added as an insured member from day 91.

B.9 Annual Health Check-up: one preventive check-up per insured adult per policy year after the first year, at Sentinel network diagnostic centres.

SECTION C - WAITING PERIODS

C.1 Initial waiting period: 30 days from the first policy start date for any illness. Not applicable to accidental injuries.

C.2 Pre-existing Disease waiting period: 36 months of continuous coverage from the first policy start date.

C.3 Specific illness waiting period: 24 months for cataract, hernia, hydrocele, piles, fissure, fistula, sinusitis, benign prostatic hypertrophy, joint replacement unless due to accident, uterine fibroids, kidney stones, gall bladder stones, varicose veins, and tonsillectomy.

C.4 Maternity waiting period: 24 months.

C.5 Waiting periods already served under a previous indemnity health policy are credited on portability as per IRDAI guidelines.

SECTION D - EXCLUSIONS

D.1 Cosmetic or plastic surgery unless for reconstruction following an accident, burn or cancer.
D.2 Dental treatment unless necessitated by an accident requiring hospitalisation.
D.3 Infertility, sterility and assisted reproduction including IVF.
D.4 Treatment of alcoholism, drug or substance abuse, and consequences thereof.
D.5 Intentional self-injury, attempted suicide.
D.6 War, invasion, nuclear, chemical or biological attack.
D.7 Unproven or experimental treatments.
D.8 Treatment taken outside India.
D.9 Obesity and weight-control treatment unless BMI >= 40 or >= 35 with co-morbidities.
D.10 Hazardous or adventure sports as a professional.
D.11 Non-medical items as listed in Annexure II (toiletries, admission kit, telephone charges, etc.).

SECTION E - CLAIMS

E.1 Cashless: present the health card at a network hospital. Pre-authorisation decision within 2 hours of receipt of complete documents for planned admission, and within 60 minutes for emergency admission.

E.2 Reimbursement: submit the claim form, discharge summary, original bills and receipts, prescriptions and investigation reports within 30 days of discharge. The company shall settle or reject within 30 days of receipt of the last necessary document. Interest at bank rate + 2% is payable for delays beyond 30 days.

E.3 Notification: planned hospitalisation to be intimated at least 48 hours in advance; emergency hospitalisation within 24 hours of admission.

SECTION F - GENERAL CONDITIONS

F.1 Free Look: the policyholder may return the policy within 30 days of receipt stating reasons, and receive a refund of premium less proportionate risk premium, medical examination costs and stamp duty.

F.2 Renewal: lifelong renewability. The company shall not deny renewal except on grounds of fraud, misrepresentation or non-disclosure.

F.3 Premium revision: premiums may be revised with prior approval of IRDAI with a notice of 90 days to policyholders.

F.4 Cancellation: the policyholder may cancel at any time by giving 15 days written notice; refund is on a short-period scale. The company may cancel on grounds of misrepresentation, fraud or non-disclosure with 15 days notice and no refund.

F.5 Grievance: write to grievance@sentinelhealth.example or call 1800-200-7788. If unresolved within 15 days, approach the Insurance Ombudsman.

F.6 Nomination: the policyholder must nominate a person to receive claim amounts in the event of the policyholder's death.

Disclaimer: Insurance is the subject matter of solicitation. Sentinel Health Insurance Company Ltd. IRDAI Reg. No. 162.
"""


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(path: Path, text: str, lines_per_page: int = 56, width: int = 95) -> None:
    lines: list[str] = []
    for para in text.strip("\n").split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=width) or [""])

    pages = [lines[i : i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    objects: list[bytes] = []

    def add(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)

    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []
    pages_id_placeholder = len(objects) + 1 + 2 * len(pages)  # computed after pages/contents

    for page_lines in pages:
        content = ["BT", "/F1 10 Tf", "12 TL", "40 800 Td"]
        for ln in page_lines:
            content.append(f"({_escape(ln)}) Tj T*")
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", "replace")
        c_id = add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
        p_id = add(
            f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {c_id} 0 R >>".encode()
        )
        page_ids.append(p_id)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_id = add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode())
    assert pages_id == pages_id_placeholder
    catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    write_pdf(HERE / "policy_wording_family_shield.pdf", POLICY_WORDING)
    # A deliberately corrupted file: valid header, truncated body -> parser must fail gracefully
    (HERE / "corrupted_scan.pdf").write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\n" + b"\x00" * 200)
    print("PDF sources written to", HERE)


if __name__ == "__main__":
    main()
