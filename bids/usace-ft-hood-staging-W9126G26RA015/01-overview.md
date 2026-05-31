# USACE Fort Hood Staging / Marshalling Area — Overview

> **Source playbook:** [`firm/playbooks/federal-rfp-best-value-tradeoff.md`](../../firm/playbooks/federal-rfp-best-value-tradeoff.md) — **first BPC exemplar** for this archetype
> **Source document:** `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\W9126G26RA015_Compiled.pdf` — 1,835-page compiled RFP (12.65 MiB)

## Solicitation identity

| Field | Value |
|---|---|
| Solicitation # | **`W9126G26RA015`** |
| USACE District prefix | **W9126G** = USACE Fort Worth District |
| Project name | Staging / Marshalling Area |
| Project short code | **FH26SMA** (cover code) |
| Installation | **Fort Hood, Texas** (formerly Fort Cavazos — the RFP uses both names; Fort Hood is current per recent congressional restoration) |
| Procurement type | **Federal RFP, Design-Bid-Build, Best-Value Tradeoff** under **FAR Part 15** Source Selection |
| Acquisition method | "Total Small Business Set-Aside" per **FAR 19.104-1** |
| Contract type | Firm Fixed Price (typical for federal vertical construction) |
| Primary NAICS | **236220** — Commercial and Institutional Building Construction |
| Size standard | **$45 million** |
| SBA Case Number | **347768** |
| Issue date | SF 1442 generated **2026-05-21 13:56 CDT**; cover page says **MAY 2026** |
| Magnitude band | **Target Price Range: $5,000,000 – $10,000,000** ⚠️ |
| Bid bond | **Required** per FAR 52.228-1 — 20% of bid OR $1M (whichever less) |
| Performance bond | **Required** post-award per FAR 52.228-15 — 100% of contract price |
| Payment bond | **Required** post-award per FAR 52.228-15 — 100% of contract price |
| Insurance | Per FAR 52.228-5 — Insurance Work on a Government Installation |
| Period of performance | `[NEEDS DEEPER READ — Section F or Section 01 00 00.00 44 CONSTRUCTION SCHEDULE]` |
| Offer due date | `[NEEDS DEEPER READ — SF 1442 Item 13c; not captured in extracted pages 1-50]` |
| Section L (Instructions to Offerors) | Section 00 21 16 — Instructions, Conditions and Notices to Offerors |
| Section M (Evaluation Factors) | `[NEEDS DEEPER READ — typically Section 00 22 16 Design-Bid-Build Selection Procedures]` |

## Place of performance

| Field | Value |
|---|---|
| Installation | Fort Hood, Texas |
| Counties | **Bell County** (most of cantonment) + **Coryell County** (training areas) — confirm exact site at site visit |
| Davis-Bacon WD | `[NEEDS DEEPER READ — Section 00 73 00 Supplementary Conditions; pull WD from SAM.gov attached to W9126G26RA015]` |
| Site access | Active U.S. Army installation — base access (DoD CAC or visitor pass) required |
| Operational sensitivity | AT/OPSEC (Anti-Terrorism / Operational Security) requirements per Section 01 01 10.00 44 |

## Key dates

| Milestone | Date |
|---|---|
| Solicitation issued (SF 1442) | 2026-05-21 13:56 CDT |
| **Offer due date** | `[NEEDS DEEPER READ — SF 1442 Item 13c]` |
| Pre-proposal conference (if any) | `[NEEDS DEEPER READ — Section 00 21 00 / 00 22 00]` |
| Site visit | `[NEEDS DEEPER READ — Section 00 21 00 / 00 22 00]` |
| Question deadline | `[NEEDS DEEPER READ — Section 00 21 16]` |

## CLIN schedule (transcribed from Section 00 10 00)

| CLIN | Description | Qty | Unit |
|---|---|---|---|
| 0001 | All work required to construct the **primary facility inside the 5 ft line** | 1 | JA (Job/Lump) |
| 0002 | All work required to construct **outside the 5 ft line** of the facility exclusive of work identified separately | 1 | JA |
| 0003 | **Option 1**: Security fence & Gate | 1 | JA |
| 0004 | **Option 2**: Tree replacement 1 | 1 | JA |
| 0005 | **Option 3**: Tree replacement 2 | 1 | JA |
| 0006 | **Option 4**: Tree replacement 3 | 1 | JA |
| 0007 | **Option 5**: Tree replacement 4 | 1 | JA |

**Notes (from Section 00 10 00):**
- All offerors must price *every* numbered line item (Note 2); skipping lines may render the offer unacceptable.
- Options may be exercised at the Government's discretion subject to availability of funds.
- Contract duration in calendar days after NTP is offerer-stated (Note 4 cross-references Section 01 00 00.00 44).

## Scope summary (from Method of Acquisition section)

> "Construct a **staging/marshalling area with container loading aprons for line haul operations**. Primary facilities include staging/marshalling area, operations building, loading/unloading docks and ramps, non-organizational..." (truncated at scaffold-time extraction)

See [`06-scope-outline.md`](./06-scope-outline.md) for the spec-book Divisions and inferred trade scope.

## Federal compliance posture (provisional)

| Item | Status |
|---|---|
| **SAM.gov active registration** | ⚠️ — verify current and not expiring before bid + award (`firm/firm-profile.json`) |
| **UEI + CAGE current** | ⚠️ — verify |
| **Reps & Certs ≤ 12 months old** | ⚠️ — verify; refresh if needed |
| **FAR 52.219-1 small-business size assertion (NAICS 236220 @ $45M)** | ⚠️ — verify firm-profile annual receipts trailing 5-year average is below $45M |
| **FAR 52.204-21 Basic Safeguarding** | ⚠️ — implementation status to verify; required for any FCI-handling contractor |
| **FAR 52.204-29 FASCSA rep** | ⚠️ — verify |
| **FAR 52.204-24 / 52.204-25 / 52.204-26 Section 889 reps** | ⚠️ — verify |
| **Buy American reps** | ⚠️ — verify |
| **DBA / certified-payroll readiness** | ⚠️ — confirm BPC has WH-347 + Form WH-347 workflow ready |
| **AT/OPSEC** (Section 01 01 10.00 44) | 🔴 — likely requires personnel screening (NACI / NACLC for badge access); plan early |
| **DPAS rating** | `[NEEDS DEEPER READ — Block in Section L provision near 52.214-34]` |

## Bid posture (BPC quick read)

| Question | Answer |
|---|---|
| BPC SBA size at NAICS 236220 ($45M) | ✅ — BPC well within $45M size standard |
| BPC bondable at $5M–$10M bid? | 🔴 — **EXPLICIT CAPACITY CHECK NEEDED** — bid bond up to $1M (cap), P&P 100/100 = up to $10M each. Compare against BPC's current surety floor of $1M single-project per `firm/firm-profile.json`. |
| Past-performance at $5M+ federal scale? | 🔴 — **GAP** — BPC has no shipped federal-construction prior at this magnitude |
| Internal capacity for $5M+ design-bid-build with operations building + civil + MEP + options? | 🔴 — **GAP** — needs PM bench check |
| Estimating effort for 1,835-page spec book | ~200-400 hours of takeoff + pricing |
| Sub network for fall-protection, BACnet HVAC controls, cyber-for-FRCS, AT/OPSEC fencing | 🔴 — **GAP** — BPC has not engaged these specialty trades before |
| Federal RFP Volume I-IV experience? | ⚠️ — `firm/proposal-library/federal-volumes/` has the boilerplate; no shipped exemplar at scale |
| **Go / No-go recommendation** | **NO-GO BIAS** — capacity, bonding, past-performance, and specialty-sub gaps all point toward a no-go. However, the playbook value of even running the go/no-go analysis is real. **Decision document at [`go-no-go-decision.md`](./go-no-go-decision.md).** |

## Cross-references

- Playbook: [`firm/playbooks/federal-rfp-best-value-tradeoff.md`](../../firm/playbooks/federal-rfp-best-value-tradeoff.md)
- Triage batch: [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) (G5)
- Compliance check: [`firm/compliance/README.md`](../../firm/compliance/README.md)
- Federal volumes: [`firm/proposal-library/federal-volumes/`](../../firm/proposal-library/federal-volumes/)
- Reference workspace at smaller scale: [`bids/cmd-post-ndi-W50S7626QA001/`](../cmd-post-ndi-W50S7626QA001/) (DLA-DDPM SAP scale; very different acquisition method)
