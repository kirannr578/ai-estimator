# {{PROJECT_NAME}} — Deliverables (SAP Best-Value Quote Package)

> **Source:** RFQ Section L (Instructions to Quoters) + Section M or SAP-equivalent "Basis for Award" (Evaluation Factors) + Section J (List of Attachments).
> Federal SAP best-value convention: **single combined PDF "QUOTE PACKAGE"** with 4 substantive sections — NOT multi-volume.

## Quote package contents

The deliverable is one PDF. Section assembly per `09-proposal-draft.md`. Compliance items:

### Front matter

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| Section L checklist (if RFQ provides) | RFQ attachment | 1 | First page of package |
| Cover note | BPC template — see `09-proposal-draft.md` §1 | ½ – 1 | No exceptions; lists package sections |
| **SF-18** Request for Quotation — signed | RFQ attachment | 2 | Default SAP form. Use SF-1449 if RFQ uses commercial-item integrated form per FAR 13.500. **NOT SF-1442.** |
| SF-30 amendment acknowledgments | per amendment | n/a | List on signature; attach signed pages |

### Reps & Certs

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| SAM Reps & Certs incorporation page | FAR 52.204-8(d) — or FAR 52.212-3(b) if commercial-item | 1 | If SAM Reps current ≤ 12 months |
| Section K provisions | RFQ attachment | per RFQ | Completed as applicable |
| Buy American Certificate (FAR 52.225-4) — signed | per template in `05-bid-form-prep.md` | 1 | If RFQ triggers FAR 52.225-9 / -11 |

### Price section

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| Schedule of Prices — every CLIN + every priced option priced (unit, extended, grand total) | RFQ Section B | n/a | **Every** CLIN priced — non-responsive if blank |
| Surety commitment letter | Surety | 1 | For **post-award** P&P or FAR 52.228-13 Alternative Payment Protections; typically NOT bid bond at submission |

### Technical capability narrative — REQUIRED (5–15 pp typical; this is the SAP differentiator)

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| Project understanding | `09-proposal-draft.md` §2.1 | 1 | Demonstrate thorough understanding of SOW |
| Proposed schedule | `09-proposal-draft.md` §2.2 | 1 | Major milestones + critical path |
| Phasing + site logistics | `09-proposal-draft.md` §2.3 | 1–2 | Site access, badging, lay-down, dumpster, coordination |
| Trade-by-trade approach | `09-proposal-draft.md` §2.4 | 3–8 | Per major trade: scope, materials, sub/self, sequencing, QC |
| QC + safety summary | `09-proposal-draft.md` §2.5 | 1 | Reference post-award submittals; do not paste full plans |

### Key personnel — short-form (½ page per role)

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| Project Manager | `09-proposal-draft.md` §3.1; [`firm/proposal-library/key-personnel/`](../../../firm/proposal-library/key-personnel/) trimmed to ½ page | ½ | Required |
| Superintendent | `09-proposal-draft.md` §3.2 (same source) | ½ | Required; OSHA 30 mandatory |
| QC Manager | `09-proposal-draft.md` §3.3 (same source) | ½ | Required |
| Principal in Charge | `09-proposal-draft.md` §3.4 (same source) | ½ | If RFQ asks |
| Safety Officer | `09-proposal-draft.md` §3.5 (same source) | ½ | If RFQ asks |

### Prior experience — REQUIRED ({{PAST_PERF_COUNT}} references, ½ page each)

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| 3–5 prior-experience references (per RFQ Section L — verify the **count**: typ "minimum 3, maximum 5") | Picks per [`firm/firm-profile.json → past_project_selection_rules`](../../../firm/firm-profile.json) + short-form blocks from [`firm/proposal-library/past-performance/`](../../../firm/proposal-library/past-performance/) | ½ each | Each: owner / value / contact / dates / scope / completion + 2-sentence relevance statement. Submit at RFQ's stated **maximum**. |

### Contractor core data

| Deliverable | Source / form | Page limit | Notes |
|---|---|---|---|
| Company name, UEI, CAGE, EIN, POC | `09-proposal-draft.md` §6 | ½ | Standard block |

## What NOT to submit (SAP discipline)

Distinct from LPTA, which prohibits all narrative, SAP allows and rewards substantive narrative — but with limits. **Do NOT** include:

- 4-volume FAR Part 15 structure (Volume I/II/III/IV) — SAP is single-package
- Formal source-selection narrative (SSP, SSDD references, adjectival-rating cross-walks)
- Oral-presentation slide deck — SAP does not use orals
- CPARS printouts or PPQs — SAP relies on prior-experience reference contacts
- Full safety plan, full QC plan, full schedule narrative — those are **post-award** submittals (FAR 52.236-13, spec QC, FAR 52.236-15)
- Subcontractor management plan — post-award submittal
- Closeout plan — post-award submittal
- "Why us" marketing pitch beyond what the cover note and technical narrative carry
- Unsolicited alternates not invited by RFQ Section L
- Exceptions to the priced quote (state assumptions in technical narrative if needed; do NOT attach exceptions to the priced quote)

## File naming + transmittal

Single combined PDF:

| File | Name |
|---|---|
| Quote package | `{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - QUOTE PACKAGE.pdf` |
| If > 25 MB (or per Section L email size limit) | Split + number `email N of M` in subject line |

Email subject: per Section L exact format — commonly `{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - email N of M`.

## Post-award deliverables (for awareness, not for quote)

The following are due **after award** and should be priced into General Conditions but **not included in the quote**:

- NTP+5: Preconstruction conference attendance per FAR 52.236-26
- NTP+10: Initial baseline CPM schedule (per FAR 52.236-15 / spec)
- **Within 10 calendar days of award:** Performance + Payment Bonds (or FAR 52.228-13 Alternative Payment Protections) at 100% of contract value
- NTP+14: Site-specific safety plan (per FAR 52.236-13)
- NTP+14: QC Plan (per spec)
- Weekly: WH-347 Certified Payroll (prime + every sub tier) if DBA applies
- Monthly: Pay app + lien waivers
- Substantial completion: closeout package per FAR 52.246-12 / spec
