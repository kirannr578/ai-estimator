# Volume III — Past Performance

> **How to use this template** — Federal best-value tradeoff (FAR 15.101-1) Volume III. Target page count **3–5 pages** + appendices (Past-Performance Questionnaires, CPARS records, owner letters). Section M scores Past Performance as a **confidence assessment** per FAR 15.305(a)(2)(i): the SSEB rates BPC's likelihood of successful performance as Substantial / Satisfactory / Limited / No / Unknown Confidence based on recency, relevance, and quality of cited projects. Pick projects per [`firm/firm-profile.json → past_project_selection_rules`](../../firm-profile.json) — **3 to 5** that fit the bid, not the entire portfolio. Verify owner reference contacts are live before submission. Search-and-replace every `{{PLACEHOLDER}}`.

---

# Volume III — Past Performance
## {{PROJECT_NAME}} | Solicitation {{SOLICITATION_NUMBER}}
### Submitted by Blue Print Constructs (Blue Print Constructs, LLC dba) — UEI LM4YHVQ71QG7 • CAGE 9LET0

## 1. Corporate past-performance summary

Blue Print Constructs has delivered construction services in North Texas + central Texas continuously since January 2022 across institutional renovation, hospitality renovation, ground-up new construction with bonding, and specialty-trade subcontracting. The firm currently operates as **General Contractor (prime)** on two active institutional / new-construction projects (Hindu Temple of Southlake; Lavon RV Park, $1M performance bond) and as a **specialty-trade subcontractor** on a 250–500+ single-family-home rolling portfolio with four featured GC partners.

| Capability dimension | Demonstrated record |
|---|---|
| **Federal-construction experience** | `[USER TO FILL — confirm before claiming any federal past performance; per firm-profile.json BPC has not yet completed a federal prime contract. The Lavon RV Park $1M-bond record establishes commercial-equivalent past performance and bondability.]` |
| **Texas-state institutional experience** | Hindu Temple of Southlake (10,700 SF Assembly A-3 reno, in execution); Holiday Inn Hall Park (commercial reno) |
| **Ground-up new construction with bonding** | Lavon RV Park ($1.05M, $1M performance bond per AIA A101 Article 8) |
| **Self-perform finishes capability** | 250–500+ SFH portfolio (drywall, paint, flooring, tile, trim, roofing repairs) since 2022 |
| **GC pre-qualification** | The Beck Group sub pre-qual (Denton County, trades 152 / 154 / 172 / 174 / 175 / 176) |

## 2. Relevance-of-experience matrix

The matrix below maps BPC's projects to the evaluation criteria most likely to be in Section M for `{{PROJECT_NAME}}`. Confirm against the actual Section M language and tighten the column headers per the RFP.

| Project | Owner / Type | Contract value | Period | Role | Same-as / Similar-to / Relevant relevance | Federal ? |
|---|---|---|---|---|---|---|
| **Lavon RV Park** | Lavon Leisure 78 RV Park LLC (business) | $1,050,000 | 2025-07 → 2026-04 (in execution) | GC (prime); $1M performance bond per AIA A101 | `{{LAVON_RELEVANCE_RATING}}` (Same-as if RFP is small ground-up site/civil; Similar-to if interior reno) | No (commercial-equivalent) |
| **Hindu Temple of Southlake** | North Texas Hindu Heritage Society (nonprofit) | `{{HINDU_VALUE}}` (in execution) | 2024 → 2026 | GC (prime); negotiated lump-sum, owner-direct | `{{HINDU_RELEVANCE_RATING}}` (Same-as for institutional renovation) | No |
| **Holiday Inn (Hall Park, Frisco)** | Holiday Inn franchisee (business) | `{{HOLIDAY_VALUE}}` | `{{HOLIDAY_PERIOD}}` | GC | `{{HOLIDAY_RELEVANCE_RATING}}` (Similar-to for occupied commercial reno) | No |
| **250–500+ SFH portfolio** | Multiple (specialty-trade sub for 4 featured GCs) | `[Cumulative; per-project not aggregated]` | 2022–present (rolling) | Specialty-trade sub | `{{SFH_RELEVANCE_RATING}}` (Relevant for finishes self-perform claim) | No |
| **The Beck Group sub pre-qual** | The Beck Group (commercial GC, Dallas) | n/a (pre-qual only) | 2023-03 (pre-qual submitted) | Prospective sub | `{{BECK_RELEVANCE_RATING}}` (Relevant for pre-qual posture only) | No |

> **Definition of relevance ratings** (per FAR 15.305(a)(2)(i) and standard SSEB usage):
> - **Same-as / Very relevant** — same scope, same magnitude, same complexity, same delivery method as `{{PROJECT_NAME}}`.
> - **Similar-to / Relevant** — overlapping scope or magnitude; transferable means and methods.
> - **Relevant / Somewhat relevant** — discrete element of scope or capability common to both.
> - **Not relevant** — no meaningful overlap; do not cite.

## 3. Project writeups

For each cited project, follow the format below. Source long-form writeups in [`firm/proposal-library/past-performance/`](../past-performance/).

### 3.1 Project 1 — `{{PROJECT_1_NAME}}`

| Field | Value |
|---|---|
| Project name | `{{PROJECT_1_NAME}}` |
| Owner / Customer | `{{PROJECT_1_OWNER}}` |
| Owner type | `{{PROJECT_1_OWNER_TYPE}}` (federal / state / municipal / institutional / nonprofit / commercial) |
| Contract type | `{{PROJECT_1_CONTRACT_TYPE}}` (FFP / cost-reimbursable / IDIQ / AIA A101 / GMP / lump sum) |
| Contract number | `{{PROJECT_1_CONTRACT_NUMBER}}` |
| Contract value (original) | `${{PROJECT_1_VALUE_ORIGINAL}}` |
| Contract value (final, with mods) | `${{PROJECT_1_VALUE_FINAL}}` |
| Period of performance | `{{PROJECT_1_POP_START}}` to `{{PROJECT_1_POP_END}}` |
| BPC's role | `{{PROJECT_1_ROLE}}` (Prime / Sub / JV partner) |
| % of contract self-performed by BPC | `{{PROJECT_1_SELF_PERFORM_PCT}}%` |
| Owner-side reference — name + title | `{{PROJECT_1_REF_NAME}}`, `{{PROJECT_1_REF_TITLE}}` |
| Owner-side reference — email | `{{PROJECT_1_REF_EMAIL}}` |
| Owner-side reference — phone | `{{PROJECT_1_REF_PHONE}}` |
| Bonding | `{{PROJECT_1_BOND}}` (e.g. "$1M performance bond per AIA A101 Article 8" if applicable) |
| CPARS / PPIRS rating | `{{PROJECT_1_CPARS}}` (Exceptional / Very Good / Satisfactory / Marginal / Unsatisfactory) — federal projects only |
| PPQ on file | `{{PROJECT_1_PPQ_STATUS}}` (Yes / Pending / N/A — see Volume III Appendix) |

**Scope summary.** `{{PROJECT_1_SCOPE_SUMMARY}}` (3–5 sentences describing scope by CSI division, square footage / quantity, key trades, occupied vs unoccupied, federal vs commercial).

**Relevance to `{{PROJECT_NAME}}`.** This project is `{{PROJECT_1_RELEVANCE_RATING}}` to `{{PROJECT_NAME}}` because:

- `{{PROJECT_1_RELEVANCE_REASON_1}}` (e.g. same delivery method)
- `{{PROJECT_1_RELEVANCE_REASON_2}}` (e.g. same trade mix)
- `{{PROJECT_1_RELEVANCE_REASON_3}}` (e.g. same magnitude / occupancy / agency type)

**Outcome.** Delivered `{{PROJECT_1_OUTCOME}}` — schedule (on time / N days early / N days late with cause), budget (within original contract / +X% with owner-approved mods), quality (zero NCRs / N NCRs all closed), safety (zero recordables / N recordables — describe), customer satisfaction (`{{PROJECT_1_REF_QUOTE}}` if owner letter on file).

### 3.2 Project 2 — `{{PROJECT_2_NAME}}`

`[Repeat the table + scope summary + relevance + outcome format from Project 1, populated for the second pick.]`

### 3.3 Project 3 — `{{PROJECT_3_NAME}}`

`[Repeat for the third pick.]`

### 3.4 Project 4 — `{{PROJECT_4_NAME}}` (optional, if RFP allows 4–5)

`[Repeat for the fourth pick if RFP allows.]`

### 3.5 Project 5 — `{{PROJECT_5_NAME}}` (optional, if RFP allows 5)

`[Repeat for the fifth pick if RFP allows.]`

## 4. Past-Performance Questionnaire (PPQ) coordination

Federal RFPs typically require BPC to coordinate completion of a Past-Performance Questionnaire (PPQ) by each cited owner reference. BPC's PPQ workflow is:

1. **At RFP issuance** — BPC PM issues the PPQ cover-letter package ([`firm/proposal-library/ppq/ppq-cover-letter-to-client.md`](../ppq/ppq-cover-letter-to-client.md)) to each cited owner reference, with the agency's PPQ form (or BPC's standard federal form if the RFP does not provide one — [`firm/proposal-library/ppq/ppq-standard-federal-form.md`](../ppq/ppq-standard-federal-form.md)).
2. **At RFP issuance + 7 days** — first follow-up if PPQ not returned.
3. **At RFP issuance + 14 days** — escalation to BPC PIC; PIC calls reference directly.
4. **At submission** — completed PPQs returned **directly from owner reference to `{{AGENCY}}` Contracting Officer** per Section L instructions (BPC does not handle the completed PPQ — this preserves the integrity of the assessment).

PPQ tracking log on this submission: see [`firm/proposal-library/ppq/ppq-tracking-log.md`](../ppq/ppq-tracking-log.md). Per-project PPQ status:

| Project | PPQ requested date | PPQ sent to | PPQ status | Returned to `{{AGENCY}}` on |
|---|---|---|---|---|
| `{{PROJECT_1_NAME}}` | `{{PROJECT_1_PPQ_REQ_DATE}}` | `{{PROJECT_1_REF_NAME}}` | `{{PROJECT_1_PPQ_STATUS}}` | `{{PROJECT_1_PPQ_RETURN_DATE}}` |
| `{{PROJECT_2_NAME}}` | `{{PROJECT_2_PPQ_REQ_DATE}}` | `{{PROJECT_2_REF_NAME}}` | `{{PROJECT_2_PPQ_STATUS}}` | `{{PROJECT_2_PPQ_RETURN_DATE}}` |
| `{{PROJECT_3_NAME}}` | `{{PROJECT_3_PPQ_REQ_DATE}}` | `{{PROJECT_3_REF_NAME}}` | `{{PROJECT_3_PPQ_STATUS}}` | `{{PROJECT_3_PPQ_RETURN_DATE}}` |

## 5. CPARS / PPIRS scores summary (federal projects only)

For federal projects, the SSEB will pull CPARS records directly. BPC's known CPARS / PPIRS history:

| Project | Contract # | CPARS rating overall | Quality | Schedule | Cost control | Management | Small-business utilization | Regulatory compliance |
|---|---|---|---|---|---|---|---|---|
| `[USER TO FILL — first federal project once delivered]` | | | | | | | | |

> **Note** — per `firm/firm-profile.json`, BPC has not yet completed a federal prime contract; CPARS history therefore begins on the first federal award. For commercial-equivalent projects (Lavon RV Park, Hindu Temple, Holiday Inn), no CPARS exists; owner letters and PPQs serve as equivalent evidence.

## 6. Adverse past performance (per FAR 15.305(a)(2)(iv))

BPC has reviewed the records below for the past **three years** per FAR 15.305(a)(2)(iv) requirements:

- **Terminations for default or for cause** in the past 3 years: `{{TERMINATIONS}}` `[Confirm: per firm records, BPC has not had a termination for default or for cause; state explicitly. If any exist, describe each, root cause, corrective action.]`
- **Liquidated damages assessed** in the past 3 years: `{{LD_ASSESSED}}`
- **Cure notices / show-cause notices received** in the past 3 years: `{{CURE_NOTICES}}`
- **Litigation, claims, or disputes filed against BPC** in the past 3 years: `{{LITIGATION}}` `[Confirm: per firm records, BPC has no construction-claim or contract-dispute litigation pending or resolved against the firm in the past 3 years; state explicitly. If any exist, describe.]`
- **Negative CPARS ratings (Marginal or Unsatisfactory) in any element**: `{{NEGATIVE_CPARS}}`

If any item is non-zero, include a corrective-action narrative per FAR 15.305(a)(2)(iv) showing the underlying cause + the systemic change BPC implemented to prevent recurrence.

## 7. Appendices to Volume III

- **Appendix III-A** — Owner-reference letters (one per cited project)
- **Appendix III-B** — Completed Past-Performance Questionnaires (returned directly from references to `{{AGENCY}}` per Section L; tracking log at [`../ppq/ppq-tracking-log.md`](../ppq/ppq-tracking-log.md))
- **Appendix III-C** — CPARS / PPIRS extracts (federal projects only — `[USER TO FILL once federal award history accrues]`)
- **Appendix III-D** — Surety bondability commitment letter (cross-reference Volume IV §5)

## 8. Evaluator's perspective (delete before submission — internal-use callout)

> **What scorers weight heavily on Volume III (best-value tradeoff construction RFP):**
> 1. **Recency.** Most agencies count past performance as recent if delivered within the last 3 (sometimes 5) years. Stale projects score lower regardless of relevance.
> 2. **Relevance.** Same-as scope / magnitude / complexity beats Similar-to beats Relevant. SSEB rates each project; the volume's overall rating is a composite.
> 3. **PPQ + reference responsiveness.** A cited reference who does not return the PPQ or pick up the phone hurts the score. Live, willing-to-talk references with BPC project knowledge score high.
> 4. **CPARS history.** Federal projects with Exceptional or Very Good CPARS ratings drive a Substantial Confidence assessment. Marginal or Unsatisfactory ratings drive Limited or No Confidence — corrective-action narrative is essential if any exist.
> 5. **Adverse-information disclosure.** FAR 15.305(a)(2)(iv) requires the offeror to identify any adverse past performance the agency might independently discover. Failing to disclose and then having the SSEB find it is worse than disclosing and explaining.
> 6. **Bondability.** A current surety commitment letter on Treasury Circular 570 surety, dated within 30 days, naming the project + agency + contract value envelope, supports the past-performance narrative on financial-capacity grounds (FAR 9.104-1(a) responsibility determination).
> 7. **Self-perform attestation.** Past performance that demonstrates BPC delivered Same-as / Similar-to scope as **prime contractor** scores higher than the same scope delivered as a **subcontractor**. On tradeoff awards where the prime has accountability, sub experience is treated as supporting evidence rather than primary.
