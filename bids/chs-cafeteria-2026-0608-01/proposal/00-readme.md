# {{AGENCY_SHORT}} {{PROJECT_NAME}} — Proposal package

> **Solicitation:** {{SOLICITATION_NUMBER}} — {{PROJECT_NAME}}
> **Owner:** {{AGENCY}} (administered by {{ISSUING_OFFICE}} on {{AGENCY_SHORT}}'s behalf)
> **A/E:** {{AE_FIRM_NAME}} ({{AE_POC_NAME}})
> **Submission deadline:** **{{DUE_DATE}}, {{DUE_TIME}} {{DUE_TIMEZONE}}** (T-19 calendar days from {{NOP_REFERENCE_DATE}})
> **Public opening:** {{DUE_DATE}}, {{OPENING_TIME}} {{DUE_TIMEZONE}} — {{ISSUING_OFFICE}} public-opening room + Teams link in the Notice
> **Submission address:** {{ISSUING_OFFICE}} delivery desk — {{SUBMISSION_DELIVERY_ADDRESS}}
>
> **STATUS — DRAFT, BLOCKED ON eBUILDER ACCESS + ELIGIBILITY CONFIRMATION.** This package is a scaffold built off the only document we have (the public Notice of Project, `inbox/.../ESBD_514190_..._{{SOLICITATION_NUMBER}}_Notice of Project-CS_26.05.08.pdf`). The full CSP construction document set lives behind the e-Builder Public Landing page at `{{SUBMISSION_PORTAL_URL}}` and has **not yet been downloaded**. Every section flagged `[PENDING e-BUILDER ACCESS]` needs to be re-walked once the CSP package is in hand.

---

## 1. Why this draft is mostly scaffold, not content

We are the **most source-poor** of the three active bids in this estimator workspace:

| Bid | Source material in hand |
|---|---|
| Angelo State Carr EFA (`bids/angelo-state-carr-efa-26-007/`) | Full CSP + 5 attachments (A: Bid Form, B.2: Sample CSA, C: 2010 UGSC + SGC, D: HSP form, E: Tax Exempt, F.1: Prevailing Wage) |
| USFWS San Marcos (`bids/usfws-san-marcos-140FC126R0017/`) | Full SF-1442 solicitation, attachments 1–3 (Specs, Drawings, DOL Wage Determination), SOW, and amendment |
| **{{AGENCY_SHORT}} {{PROJECT_NAME}} (this)** | **Only the public Notice of Project.** Drawings, specs, sample CSA, {{AGENCY_SHORT}} SGC, HSP form, pricing form, evaluation matrix — all behind the e-Builder portal. |

The Notice itself says only: *"This notification is the only documentation that will be posted to the Electronic State Business Daily (ESBD). Please refer to Trimble Unity Construct Bid Package at the above link for all documentation for this solicitation."* So the next 19 days hinge on pulling that bid package on Monday morning.

The honest consequence: this draft has **more `[USER TO FILL]` and `[PENDING e-BUILDER ACCESS]` markers** than its Angelo State and USFWS siblings will. That is correct and expected. **Do not invent {{AGENCY_SHORT}}-specific values where the source material is missing.** Where we've used a stand-in (e.g. citing the TTU-System 2010 UGSC from the Angelo State packet as a clause-shape proxy for the {{AGENCY_SHORT}} SGC), it is explicitly labeled.

---

## 2. THE BIG MISSING ITEMS (read this before scoring the draft)

These five gaps are the difference between "review-ready scaffold" and "submitable proposal":

1. **e-Builder CSP package** — drawings, specs, sample CSA, {{AGENCY_SHORT}} SGC, pricing form, HSP form, evaluation matrix, any addenda, RFI cutoff date. Everything quantitative depends on this. Owner: bid-prep lead. ETA: Monday 5/24 EOD.
2. **Eligibility confirmation post-missed pre-proposal meeting** — the the pre-proposal meeting was missed. The Notice does not state whether it was mandatory. {{PM_NAME}} ({{ISSUING_OFFICE}} PM) must confirm in writing that a non-attending firm can still submit a responsive proposal. If mandatory, we walk. Owner: bid-prep lead. ETA: Monday 5/24 EOD via `outreach/01-email-pm-eligibility.md`.
3. **{{AGENCY_SHORT}}-specific HSP form** — {{HUB_POC_NAME}} ({{AGENCY_SHORT}} HUB Operations) must provide the {{AGENCY_SHORT}}-branded HSP template or confirm we use the State of Texas standard form with a {{AGENCY_SHORT}} header. The HSP good-faith-effort outreach must start the same day; the form itself can wait 24-48 hours. Owner: bid-prep lead → HUB outreach. ETA: {{G2_DEADLINE_DATE_LABEL}}.
4. **Lab utility scope clarification** — the Notice describes "303 Science Education Classroom/Lab Renovation" with no MEP detail. The room could be a finishes-only classroom refresh ($95–$140/SF), a light science classroom-lab ($140–$210/SF), or a heavy wet lab with fume hood / DI water / lab gas / acid waste ($210–$310/SF). Until Fred {{AE_FIRM_NAME}} confirms the lab program from the drawings, the bid envelope is uncertain to roughly 2×. See `10-price-proposal.md` §B for the implied range. Owner: estimator. ETA: pending site walk + MEP drawings.
5. **Insurance + bonding limits per {{AGENCY_SHORT}} SGC** — the {{AGENCY_SHORT}} SGC will overwrite the 2010 UGSC baseline. We are carrying the TTU System SGC limits ($1M / $2M GL, $1M Auto, $5M Umbrella) as a floor expectation pending confirmation. Insurance broker and bonding agent need the final {{AGENCY_SHORT}} number to size policies. Owner: insurance/bonding broker. ETA: {{G2_WALK_AWAY_DATE_LABEL}}.

---

## 3. Go / no-go gate — three rows, sequential

The bid is not viable unless all three gates close green:

| Gate | Trigger | Deadline | If miss |
|---|---|---|---|
| **G1 — Eligibility confirmed** | {{PM_NAME}} confirms in writing we can still bid after missing the pre-proposal meeting | **EOD {{G1_DEADLINE_DATE_LABEL}}** | If pre-proposal was mandatory and no late-arriver accommodation: **walk away.** |
| **G2 — e-Builder package downloaded + scanned** | Full CSP package pulled, drawings sheet count > 0, specs CSI sections enumerated, pricing form and HSP form identified | **Within 24 hrs of G1 close (i.e. EOD {{G2_DEADLINE_DATE_LABEL}})** | If portal still gated or package not posted by Wed 5/27, escalate to {{AGENCY_SHORT}} System Office of Facilities Planning & Construction; if no path by Thu 5/28, **walk away.** |
| **G3 — Internal go/no-go meeting** | PM + estimator + safety lead review the now-known scope, lab-utility extent, schedule constraints, and HSP feasibility; deliver go/no-go decision | **EOD {{G2_DEADLINE_DATE_LABEL}}** | If no-go, archive this folder under `local/` and notify {{PM_NAME}} as a no-bid courtesy. |

**If all three gates close green, the rest of the proposal completes on the schedule in `../timeline.md` — submission Wed {{DUE_DATE}}, {{DUE_TIME}} {{DUE_TIMEZONE}}.**

---

## 4. Proposal package contents (this folder)

| # | File | Purpose | Draftable now? |
|---|---|---|---|
| 00 | `00-readme.md` | (this file) Submission overview, missing items, go/no-go gate | Yes |
| 01 | `01-executive-summary.md` | 1-page firm intro + project understanding + why-us | Mostly yes; project-understanding has `[PENDING e-BUILDER ACCESS]` on scope specifics |
| 02 | `02-technical-approach.md` | Phased work plan, demo sequencing, lab-utility coordination, finish schedule, university-calendar coordination | Structure yes; lab-utility specifics blocked |
| 03 | `03-project-team.md` | Org chart + key personnel | Template ready; needs `[USER TO FILL]` data |
| 04 | `04-past-performance.md` | 3 similar projects | Template ready; needs `[USER TO FILL]` data |
| 05 | `05-schedule-narrative.md` | Backwards-planned schedule, critical path, long-lead items | Yes (with assumed substantial-completion placeholder) |
| 06 | `06-quality-control-plan.md` | 3-phase inspection per {{AGENCY_SHORT}} UGSC | Yes (clause references `[TBD per CSP package]`) |
| 07 | `07-safety-plan.md` | OSHA 1926 + {{AGENCY_SHORT}} EHS coordination + lab-specific hazards | Yes |
| 08 | `08-csp-proposal-form-fill-guide.md` | Anticipated fields for the {{AGENCY_SHORT}} CSP Proposal Form | Placeholder pending CSP package |
| 09 | `09-hsp-form-fill-guide.md` | Placeholder guide for {{AGENCY_SHORT}} HSP form | Placeholder pending {{HUB_POC_NAME}} / CSP package |
| 10 | `10-price-proposal.md` | Base bid + unit prices + alternates summary | Formulas yes; values pending final takeoff |
| 11 | `11-submission-checklist.md` | Submission shape — copies, sealing, signatures, deadline | Yes (anticipated; verify against CSP package) |
| 12 | `12-bid-bond-letter-template.md` | Bonding-agent request letter template | Yes |

---

## 5. Sibling-bid cross-reference (for the reviewer)

If you've already reviewed the Angelo State Carr EFA proposal draft in `bids/angelo-state-carr-efa-26-007/proposal/`, the parts that should look familiar (state-RFCSP shape, three-phase QC, OSHA 1926 baseline, HSP outreach playbook) are reusable across both bids. The parts that are {{AGENCY_SHORT}}-specific ({{AGENCY_SHORT}} System UGSC + SGC, {{AGENCY_SHORT}} EHS coordination, {{AGENCY_SHORT}} Tech Services low-voltage scope split, {{AGENCY_SHORT}} HUB Operations contact, {{COUNTY}} County prevailing wage, e-Builder portal) are noted with {{AGENCY_SHORT}}-specific markers throughout.

We deliberately did **not** copy specifics from the Angelo State package — {{AGENCY_SHORT}}'s contract clauses, LD rates, insurance limits, and HUB form are not assumed to match Angelo State even though both are Texas state-higher-ed CSPs.

---

## 6. What the reviewer should look at first

1. Section 2 above — the five missing items. If any of these can be unblocked Friday afternoon (before Monday), please escalate.
2. `../outreach/01-email-joelle-shidemantle-eligibility.md` — the single most important email to send Monday 8 AM. Confirm the firm signature block + the "from" address before send.
3. `10-price-proposal.md` § B — the implied bid envelope and the sensitivity to lab-utility scope. Decide whether the envelope is in our wheelhouse before we sink more estimator hours.
4. `08-csp-proposal-form-fill-guide.md` and `09-hsp-form-fill-guide.md` — these are deliberately thin until the CSP package and the {{AGENCY_SHORT}} HSP form land. They will need to be filled in immediately on G2 close.
