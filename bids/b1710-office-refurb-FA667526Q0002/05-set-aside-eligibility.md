# Set-aside eligibility — B1710 Office Refurbishment

This RFQ is a **100% Total Small Business Set-Aside** under NAICS 236220 ($45M size standard). Only firms representing as Small under 236220 in SAM.gov may receive award.

> This is the federal equivalent of the HSP (HUB Subcontracting Plan) file used in TAMU/TX state bids. Federal RFQs at SAP scale do not require a subcontracting plan to be submitted — small-business set-aside means the prime is the small business, and there is no flow-down subcontracting plan obligation under FAR 19.7 for primes that are themselves small.

## 1. BPC's eligibility — affirmative

| Test | Status | Evidence |
|---|---|---|
| Active SAM.gov registration | **Active** | Confirmed by user 2026-05-23 (`firm/firm-profile.json → sam_status = active`). User to re-verify expiration date before Fri 17:00 submission. |
| NAICS 236220 registered in SAM | **Yes** | `firm/firm-profile.json → naics_codes` includes 236220 (primary for renovation bids per `naics_primary_for_renovation_bids`). |
| Size representation at 236220: Small under $45M | **Yes** | DFW MSDC SBE certificate `DL09279` attests size as Small under SBA 13 CFR Part 121. BPC annual revenue is materially under $45M per the firm profile. (Specific revenue figures not in `firm/firm-profile.json → annual_financials` — that's a separate gap; the small-status assertion does not require revenue disclosure on this offer.) |
| Reps & Certs current in SAM (FAR 52.204-7 / 52.204-19) | **TBD** | User to verify last refresh date is within 12 months. **Critical: Wed 2026-05-27 PM task.** |
| Excluded Parties List (debarment/suspension) | **Not excluded** | Per firm-profile audit, no known exclusions. CO will run automated check via SAM Exclusions search. |

## 2. Small business affirmation language for the offer cover

The signed SF 1449 (Block 17 + 30) does not require a separate small-business size affirmation — that's handled by reference through FAR 52.204-19 (Incorporation by Reference of Reps & Certs) which incorporates the SAM-posted reps. **No extra paperwork needed**.

If a separate affirmation paragraph is desired for the offer cover letter, use:

> *Blue Print Constructs (RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs, UEI LM4YHVQ71QG7, CAGE 9LET0) represents as a Small Business concern under NAICS 236220 (Commercial and Institutional Building Construction, $45M size standard) per its current System for Award Management (SAM) registration and certifications. Blue Print Constructs is fully eligible to receive award under this 100% Small Business Set-Aside.*

## 3. Other socioeconomic categories — informational only (no benefit on this RFQ)

This RFQ has only one set-aside: 100% Small Business. Sub-categories (WOSB, EDWOSB, HUBZone, SDVOSB, 8(a)) are not separately set aside and confer no price preference here. However, the offer can still note for color in the cover letter:

| Socioeconomic | BPC status | Source |
|---|---|---|
| Minority-Owned Business Enterprise (MBE) | **Yes — DFW MSDC certified** (cert DL09279, ✅ renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]`; prior cycle expired 2024-08-31 per source file) | `firm/firm-profile.json → set_aside_eligibility.mbe_status` |
| Small Business | **Yes** | Same |
| TX HUB (state-only, not federal) | **Active** (VID 1874292998900, ✅ renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]`; prior cycle expired 2024-08-31) | Same |
| SBA 8(a) / SDVOSB / WOSB / HUBZone | **Not held / not applicable** | Same |

For this federal RFQ, the only directly-impactful entry is Small Business + active SAM. MBE/HUB status is informational color.

## 4. Subcontracting flowdown (if any) — FAR 19.7

Because this is a **100% Small Business set-aside** with prime contract value almost certainly **under $750,000** (SAP threshold; this RFQ is in the $25K-$100K band), **FAR 52.219-9** (Small Business Subcontracting Plan) does NOT apply (52.219-9 thresholds out at $750K for commercial items). The clause is also **not cited** in this RFQ.

**Conclusion:** No subcontracting plan to draft, no flow-down obligations to track. If BPC subs out the flooring install (per the strategic option in `04-evaluation-strategy.md` §6), the sub must independently be a small business under its own NAICS to maintain the small-business set-aside posture of the prime contract.

## 5. Action items for the user

- [ ] **Wed 2026-05-27 PM** — Rocky verifies SAM.gov entity registration shows green-active, expiration ≥ 2026-05-29, last reps & certs refresh within 12 months. Print page to PDF for offer packet.
- [ ] **Optional** — Include the small-business affirmation paragraph above in the offer cover letter.
- [ ] **Soft** — Recertify TX HUB (VID 1874292998900) and DFW MSDC MBE (DL09279) before the next TAMU / TX state bid. These do not affect this federal RFQ.
