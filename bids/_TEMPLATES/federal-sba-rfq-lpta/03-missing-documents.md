# {{PROJECT_NAME}} — Missing Documents + RFI Candidates

> **Use:** Tracking what the RFP package is missing / ambiguous, and what BPC needs to raise as RFIs before the cutoff. Federal RFIs after the cutoff "may not be received" per FAR L.

## 1. Document inventory — what we have

| RFP attachment | Filename / source | Reviewed | Notes |
|---|---|---|---|
| RFP cover (SF 1442) | `{{FILE}}` | ☐ | |
| Section B — Schedule of Prices (CLINs) | `{{FILE}}` | ☐ | |
| Section C — Statement of Work | `{{FILE}}` | ☐ | |
| Section F — Period of Performance | `{{FILE}}` | ☐ | |
| Section H — Special Contract Requirements | `{{FILE}}` | ☐ | |
| Section I — Contract Clauses | `{{FILE}}` | ☐ | |
| Section J — List of Attachments | `{{FILE}}` | ☐ | |
| Section K — Reps & Certs | `{{FILE}}` | ☐ | |
| Section L — Instructions to Offerors | `{{FILE}}` | ☐ | |
| Section M — Evaluation Factors | `{{FILE}}` | ☐ | |
| Drawings (architectural, structural, MEP) | `{{FILE}}` | ☐ | |
| Spec book / Project Manual | `{{FILE}}` | ☐ | |
| Wage Determination (Davis-Bacon) | `{{FILE}}` — `{{WD_NUMBER}}` `{{WD_DATE}}` | ☐ | |
| Past-performance template (if provided) | `{{FILE}}` | ☐ | |
| Amendments (SF 30) | `{{ADDENDA_LIST}}` | ☐ | |

## 2. Documents requested / pending

| Document | Why needed | How to obtain | Owner | Due |
|---|---|---|---|---|
| `{{DOC}}` | `{{WHY}}` | `{{HOW}}` | `{{OWNER}}` | `{{DUE}}` |

## 3. Ambiguities / boilerplate-leakage flags

Federal RFPs frequently carry stale boilerplate from prior solicitations. Flag every inconsistency and either RFI or document the operative source in the proposal cover letter:

| Page / section | Ambiguity | Operative source (per SOW + CLINs) | Action |
|---|---|---|---|
| `{{PAGE}}` | `{{ISSUE}}` | `{{AUTH}}` | `[RFI / cover-letter clarification / accept silently]` |

## 4. RFI candidates (draft before cutoff)

| # | Topic | RFP reference | Question | Impact on price | Status |
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

If an RFI is not answered before the proposal due date, BPC will:

- Quote the most-conservative interpretation in the priced proposal
- Document the assumption in `08-pricing-strategy.md` (internal)
- **Not** include the assumption in the proposal cover letter — exceptions in the priced proposal flip Pass → Fail under LPTA
- File the unanswered RFI as a post-award clarification request via the post-award NTP+5 preconstruction conference
