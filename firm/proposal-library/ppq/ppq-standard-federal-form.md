# PPQ — Standard Federal Form (BPC fallback)

> **How to use this template** — Generic federal Past-Performance Questionnaire form. Use **only** when the agency RFP does not provide its own PPQ form (some federal RFPs do not). Always check Section L first; agency-provided forms (USACE PPQ, NAVFAC PPQ, AFCEC PPQ, GSA PPQ) take precedence over this generic form. The structure below mirrors the typical federal model: 5-point Likert scale per dimension + open narrative space + adverse-information capture per FAR 15.305(a)(2)(iv). The past client returns this form **directly to the agency Contracting Officer**, not to BPC.
>
> **Print orientation** — print on letter-size paper, single-sided, target 3–4 pages total. Do not exceed page count without agency permission. Search-and-replace every `{{PLACEHOLDER}}`.

---

# Past-Performance Questionnaire
## Federal Solicitation {{FEDERAL_SOLICITATION_NUMBER}} — {{FEDERAL_PROJECT_NAME}}
### Offeror: Blueprint Constructs (Blue Print Constructs, LLC dba) — UEI LM4YHVQ71QG7

> **To the past client** — Thank you for taking time to complete this questionnaire. The federal Government uses your responses to evaluate the offeror's likelihood of successful performance on the cited solicitation per FAR 15.305(a)(2). Please return the completed form **directly to the Contracting Officer** at the address on the cover letter, **not** to Blueprint Constructs. Your candid assessment is essential.

---

## Section A — Identification (completed by past client)

| Field | Value |
|---|---|
| A1. Past client name | `{{A1_PAST_CLIENT_NAME}}` |
| A2. Past client title | `{{A2_PAST_CLIENT_TITLE}}` |
| A3. Past client organization | `{{A3_PAST_CLIENT_ORGANIZATION}}` |
| A4. Past client email | `{{A4_PAST_CLIENT_EMAIL}}` |
| A5. Past client phone | `{{A5_PAST_CLIENT_PHONE}}` |
| A6. Past project name | `{{A6_PAST_PROJECT_NAME}}` |
| A7. Past project contract number | `{{A7_PAST_CONTRACT_NUMBER}}` |
| A8. Past project contract value (final) | `${{A8_PAST_CONTRACT_VALUE}}` |
| A9. Past project period of performance | `{{A9_PAST_POP_START}}` to `{{A9_PAST_POP_END}}` |
| A10. Offeror's role on the past project | `{{A10_OFFEROR_ROLE}}` (Prime / Subcontractor / JV partner) |
| A11. Past client's role on the past project | `{{A11_PAST_CLIENT_ROLE}}` (Owner / Owner-rep / COR / Project Manager / Inspector / etc.) |

## Section B — Performance Ratings

> **Rating scale:**
> - **5 = Exceptional** — Offeror's performance significantly exceeded contract requirements; very few minor issues, all resolved promptly. Strong recommendation.
> - **4 = Very Good** — Offeror's performance met all contract requirements and exceeded several to the Government's benefit. Recommendation.
> - **3 = Satisfactory** — Offeror's performance met all contract requirements; issues were minor and resolved adequately. Conditional recommendation.
> - **2 = Marginal** — Offeror's performance did not meet some contract requirements; issues caused noticeable disruption that the offeror partially addressed. Reservation.
> - **1 = Unsatisfactory** — Offeror's performance did not meet contract requirements; issues caused significant disruption that the offeror failed to address adequately. Do not recommend.
> - **N/A** — Not applicable to this contract.

| # | Performance dimension | Rating (1–5 or N/A) | Optional narrative |
|---|---|---|---|
| B1 | **Quality of work** — workmanship, conformance to specifications, accuracy of work product | `{{B1_RATING}}` | `{{B1_NARRATIVE}}` |
| B2 | **Cost control** — accuracy of cost forecasts, change-order discipline, avoidance of cost overruns, integrity of pay applications | `{{B2_RATING}}` | `{{B2_NARRATIVE}}` |
| B3 | **Schedule control** — adherence to baseline schedule, recovery from slippage, accuracy of look-ahead schedules | `{{B3_RATING}}` | `{{B3_NARRATIVE}}` |
| B4 | **Technical performance** — competence of means and methods, problem-solving on technical issues, technical innovation where appropriate | `{{B4_RATING}}` | `{{B4_NARRATIVE}}` |
| B5 | **Management responsiveness** — RFI / submittal turnaround, communication clarity, accessibility of project leadership, follow-through on commitments | `{{B5_RATING}}` | `{{B5_NARRATIVE}}` |
| B6 | **Subcontractor management** — competence in selecting + managing subs, payment discipline to subs, sub-quality oversight | `{{B6_RATING}}` | `{{B6_NARRATIVE}}` |
| B7 | **Safety** — incident rate, OSHA compliance, site-safety culture, willingness to address safety issues raised by the customer | `{{B7_RATING}}` | `{{B7_NARRATIVE}}` |
| B8 | **Regulatory + contract compliance** — adherence to FAR, Davis-Bacon (federal) or prevailing-wage (state), small-business / HUB utilization, environmental / EHS regulations | `{{B8_RATING}}` | `{{B8_NARRATIVE}}` |
| B9 | **Customer satisfaction** — overall — would you award the offeror a future similar contract? | `{{B9_RATING}}` | `{{B9_NARRATIVE}}` |
| B10 | **Closeout discipline** — punch-list completion, O&M / as-built deliverables, warranty responsiveness | `{{B10_RATING}}` | `{{B10_NARRATIVE}}` |

## Section C — Scope and Complexity

> The Government uses Section C to determine **relevance** of the past project to the cited solicitation. Please describe the past project as you experienced it.

| # | Question | Response |
|---|---|---|
| C1 | What was the scope of the past project? (Brief — 2–3 sentences) | `{{C1_SCOPE}}` |
| C2 | What was the magnitude (square footage, dollar value, duration)? | `{{C2_MAGNITUDE}}` |
| C3 | What was the delivery method (Design-Bid-Build / Design-Build / CMAR / IDIQ / lump-sum / cost-reimbursable)? | `{{C3_DELIVERY}}` |
| C4 | Were there particular complexities (active occupancy, secure facility, hazardous materials, regulatory complexity, environmental sensitivity)? | `{{C4_COMPLEXITY}}` |
| C5 | What percentage of the work did the offeror self-perform? What percentage was subcontracted? | `{{C5_SELF_PERFORM}}` |
| C6 | Did the offeror provide bonding (Performance, Payment)? At what amount? | `{{C6_BONDING}}` |

## Section D — Adverse Information (per FAR 15.305(a)(2)(iv))

> Please disclose any adverse information about the offeror's performance on this project. Adverse information includes any of the following:

| # | Item | Yes / No | If Yes, brief narrative |
|---|---|---|---|
| D1 | Cure notices issued to the offeror | `{{D1_YES_NO}}` | `{{D1_NARRATIVE}}` |
| D2 | Show-cause notices issued to the offeror | `{{D2_YES_NO}}` | `{{D2_NARRATIVE}}` |
| D3 | Termination for default or for cause | `{{D3_YES_NO}}` | `{{D3_NARRATIVE}}` |
| D4 | Liquidated damages assessed | `{{D4_YES_NO}}` | `{{D4_NARRATIVE}}` |
| D5 | Litigation or formal disputes | `{{D5_YES_NO}}` | `{{D5_NARRATIVE}}` |
| D6 | Significant safety incidents (recordable, regulatory citation, fatality) | `{{D6_YES_NO}}` | `{{D6_NARRATIVE}}` |
| D7 | Significant quality issues requiring rework or warranty intervention | `{{D7_YES_NO}}` | `{{D7_NARRATIVE}}` |
| D8 | Other adverse performance issues not captured above | `{{D8_YES_NO}}` | `{{D8_NARRATIVE}}` |

## Section E — Overall Confidence Assessment

> The Government's source-selection team uses Section E to inform the **Confidence Assessment** under FAR 15.305(a)(2)(i). Based on your experience with the offeror on this project:

| # | Question | Response |
|---|---|---|
| E1 | What is your overall confidence that this offeror will successfully perform a similar contract for the federal Government? | ☐ Substantial Confidence ☐ Satisfactory Confidence ☐ Limited Confidence ☐ No Confidence ☐ Unknown |
| E2 | Would you award this offeror a future similar contract? | ☐ Yes, without reservation ☐ Yes, with reservations (describe) ☐ No |
| E3 | If "Yes, with reservations" or "No," please describe | `{{E3_RESERVATIONS}}` |
| E4 | Anything else the Government should know about this offeror's performance? | `{{E4_ADDITIONAL}}` |

## Section F — Past Client Certification

By signing below, the past client certifies that the responses above are accurate to the best of their knowledge and reflect the offeror's performance on the cited past project.

```
Past client signature:   ______________________________________

Past client name:        {{F_PAST_CLIENT_NAME}}
Past client title:       {{F_PAST_CLIENT_TITLE}}
Past client organization:{{F_PAST_CLIENT_ORGANIZATION}}
Date:                    {{F_DATE}}

Email confirming submission:  Send the completed PPQ to
                              {{CO_NAME}}, Contracting Officer
                              {{FEDERAL_AGENCY}}
                              Email:  {{CO_EMAIL}}
                              Subject:  "{{FEDERAL_SOLICITATION_NUMBER}} —
                                         Past-Performance Questionnaire —
                                         Blueprint Constructs"

Optional courtesy copy:  Blueprint Constructs does NOT need a copy of the
                         completed PPQ. Per FAR 15.305 process integrity,
                         only the Contracting Officer should receive the
                         completed form. If you would like to confirm with
                         Blueprint Constructs that you have submitted the
                         PPQ, simply email
                         {{BPC_POC_EMAIL}} stating "PPQ submitted on {{F_DATE}}"
                         — without the form content.
```

---

## Notes for the BPC PM (delete before sending to past client)

- **Customize the Likert anchors** if the agency-provided language differs from the generic 1–5 / Exceptional–Unsatisfactory model. Some agencies use 0–4 or A–F.
- **Customize the dimensions** in Section B if the RFP specifies particular evaluation factors (e.g. small-business utilization, BIM compliance, sustainability, environmental compliance). Add agency-specific factors as B11, B12, etc.
- **Do not sign or pre-fill** any field. The past client fills the entire form. BPC's only role is to facilitate transmission and follow up on completion status (not content).
- **PPQ form versioning** — date and version this form per RFP. The BPC PM keeps a copy of the blank form sent for each PPQ in the bid workspace at `bids/{{SLUG}}/ppq/`.
- **If the past client sends BPC a copy** of the completed PPQ — do not include it in the proposal, do not store it in the bid workspace, do not reference it. PPQ content stays between the past client and the federal CO; touching it on BPC's side compromises the assessment.
