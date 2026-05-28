# {{PROJECT_NAME}} — Missing Documents + RFI Candidates

> **Use:** Tracking what the RFQ package is missing / ambiguous, and what BPC needs to raise as RFIs before the cutoff. Federal RFIs after the cutoff "may not be received" per RFQ Section L.

## 0. Form-and-procurement disambiguation (do this first)

Before scoping anything else, lock in **which RFQ form and which FAR Part(s)** apply. This template assumes FAR Part 13 simplified acquisition (often + Part 12 commercial-item) on **SF-18** or, less commonly, **SF-1449** for commercial-item under FAR 13.500. If the form on the RFQ cover is **SF-1442**, this is NOT a SAP — switch templates to `bids/_TEMPLATES/federal-sba-rfq-lpta/` (LPTA) or revisit playbook decision matrix in [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../../firm/playbooks/federal-simplified-acquisition-best-value.md) §1.

| Question | Answer (verify against RFQ cover page) |
|---|---|
| Form on RFQ cover | ☐ SF-18 ☐ SF-1449 ☐ SF-1442 (wrong template — stop) |
| FAR Part cited on cover | ☐ Part 13 only ☐ Part 13 + Part 12 (commercial-item) ☐ Part 14 / 15 (wrong template — stop) |
| Section M (or SAP "Basis for Award") language | ☐ Comparative trade-off — best value ☐ "Groups of 3 lowest priced" language present ☐ LPTA (wrong template — stop) |
| Bid bond required at submission? | ☐ Yes (FAR 52.228-1 cited) ☐ **No** (typical SAP; FAR 52.228-13 Alternative Payment Protections cited or no bond clause) |
| Section I clause family | ☐ 52.213 series (SAP) ☐ 52.212 series (commercial-item) ☐ 52.215 series (wrong template — stop) |
| Quote due format | ☐ Email only ☐ SAM.gov portal ☐ PIEE ☐ Other |
| Acceptance period stated on RFQ | `{{ACCEPTANCE_PERIOD_DAYS}}` cal days (typ 60 on SAP, vs. 90 on LPTA, vs. 120 on FAR 15 tradeoff) |

If any answer above doesn't match the SAP best-value pattern, **stop and re-confirm the template archetype before pricing**.

## 1. Document inventory — what we have

| RFQ attachment | Filename / source | Reviewed | Notes |
|---|---|---|---|
| RFQ cover (SF-18 / SF-1449) | `{{FILE}}` | ☐ | |
| Section B — Schedule of Prices (CLINs) | `{{FILE}}` | ☐ | |
| Section C — Statement of Work | `{{FILE}}` | ☐ | |
| Section F — Period of Performance | `{{FILE}}` | ☐ | |
| Section H — Special Contract Requirements | `{{FILE}}` | ☐ | |
| Section I — Contract Clauses (52.213 / 52.212 series typical) | `{{FILE}}` | ☐ | |
| Section J — List of Attachments | `{{FILE}}` | ☐ | |
| Section K / 52.212-3 — Reps & Certs | `{{FILE}}` | ☐ | |
| Section L — Instructions to Quoters | `{{FILE}}` | ☐ | |
| Section M (or SAP-equivalent "Basis for Award") — Evaluation Factors | `{{FILE}}` | ☐ | Confirm "comparative trade-off" + "groups of 3 (or 5)" language |
| Drawings (architectural, structural, MEP) | `{{FILE}}` | ☐ | |
| Spec book / Project Manual | `{{FILE}}` | ☐ | |
| Wage Determination (Davis-Bacon) | `{{FILE}}` — `{{WD_NUMBER}}` `{{WD_DATE}}` | ☐ | DBA applies regardless of SAT/SAP status if construction labor on site |
| Past-performance / prior-experience reference template (if provided) | `{{FILE}}` | ☐ | |
| Amendments (SF-30) | `{{ADDENDA_LIST}}` | ☐ | Subscribe to SAM.gov amendment notifications — SAP RFQs frequently amend mid-window |

## 2. Documents requested / pending

| Document | Why needed | How to obtain | Owner | Due |
|---|---|---|---|---|
| `{{DOC}}` | `{{WHY}}` | `{{HOW}}` | `{{OWNER}}` | `{{DUE}}` |

## 3. Ambiguities / boilerplate-leakage flags

Federal SAP RFQs frequently carry stale boilerplate from prior solicitations (mis-named locations, stale POP dates, wrong project names). Flag every inconsistency and either RFI or document the operative source in the quote's cover note:

| Page / section | Ambiguity | Operative source (per SOW + CLINs) | Action |
|---|---|---|---|
| `{{PAGE}}` | `{{ISSUE}}` | `{{AUTH}}` | `[RFI / cover-letter clarification / accept silently]` |

## 4. RFI candidates (draft before cutoff)

| # | Topic | RFQ reference | Question | Impact on price | Status |
|---|---|---|---|---|---|
| `{{NUM}}` | `{{TOPIC}}` | `{{REF}}` | `{{QUESTION}}` | `{{IMPACT}}` | `[Draft / Sent / Answered]` |

## 5. Draft RFI cover letter

```
Subject: RFI — {{SOLICITATION_NUMBER}} — {{PROJECT_NAME}}

Dear {{CS_NAME}}:

In accordance with Section L of {{SOLICITATION_NUMBER}}, Blue Print Constructs
respectfully submits the following Request for Information regarding the
above-referenced solicitation. We request a response by the RFI cutoff
({{RFI_CUTOFF_DATE}}) to enable accurate pricing.

[Number] RFI items follow:

  RFI #1: <topic>
    Reference: <Section + paragraph + page>
    Question: <question>
    Reason: <why it affects price or technical acceptability>

  RFI #2: ...

Thank you,

[USER TO FILL — signer name + title]
Blue Print Constructs, LLC dba Blueprint Constructs
UEI LM4YHVQ71QG7  •  CAGE 9LET0
(469) 213-1838  •  contactus@blueprintconstructs.com
```

## 6. Stand-in assumptions (if RFI not answered)

If an RFI is not answered before the quote due date, BPC will:

- Quote the most-conservative interpretation in the priced quote
- Document the assumption in `08-pricing-strategy.md` (internal)
- **Optionally** state the assumption in the technical-capability narrative as a documented design assumption — SAP best-value tolerates a small number of clearly-flagged assumptions, unlike pure LPTA. **Do not** state assumptions as exceptions or substitutions to the priced quote unless explicitly invited by Section L
- File the unanswered RFI as a post-award clarification request via the post-award preconstruction conference
