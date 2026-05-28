# `ppq/` — federal Past-Performance Questionnaire collection

This sub-library is the source of truth for **Past-Performance Questionnaire (PPQ)** content used in federal RFP responses. PPQs are how the Government collects past-performance evidence directly from BPC's prior owners/clients to inform the **Confidence Assessment** under FAR 15.305(a)(2)(i) — Substantial / Satisfactory / Limited / No / Unknown Confidence.

## What a PPQ is

A PPQ is a short questionnaire (typically 10–15 questions, 5-point Likert scale + narrative space) the federal Government sends to a past client of an offeror to evaluate the offeror's performance on a prior contract. The PPQ asks the past client to rate the offeror on quality, cost control, schedule control, management responsiveness, regulatory compliance, customer satisfaction, and similar dimensions, with optional narrative.

> **Critical procedural point** — the offeror **never sees the completed PPQ**. The past client returns the completed PPQ **directly to the federal Contracting Officer or Source Selection Authority** by email or upload to the agency portal. The offeror's role is to (a) identify the past clients to be surveyed, (b) provide each past client with the agency's PPQ form (or BPC's standard federal form if the agency does not provide one) plus a cover letter explaining the request, and (c) follow up to ensure completion.

## When PPQs are required

Federal construction RFPs over the simplified-acquisition threshold (currently $250K), particularly best-value tradeoff source selections (FAR 15.101-1) and IDIQ task-order competitions, frequently require past-performance questionnaires from a specified number of past projects (typically 3–5).

The RFP's Section L will specify:

- Number of PPQs required
- Whether the agency provides its own PPQ form or accepts a "generic" form
- The specific evaluation period (typically 3 or 5 years lookback)
- The submission method for the past client (typically email to the CO; sometimes upload to the agency portal)
- The deadline (sometimes the proposal due date; sometimes a separate deadline 7–14 days post-proposal)

## BPC's PPQ workflow

1. **At RFP issuance (Day 0)** — Capture team identifies the cited past projects per [`firm/firm-profile.json → past_project_selection_rules`](../../firm-profile.json) and confirms each owner-side reference contact is current and reachable.
2. **Day 0–2** — BPC PM issues the PPQ cover-letter package ([`ppq-cover-letter-to-client.md`](ppq-cover-letter-to-client.md)) to each cited owner reference, with the agency-provided PPQ form **or** [`ppq-standard-federal-form.md`](ppq-standard-federal-form.md) as fallback, plus the BPC-supplied project-fact reminder card.
3. **Day 7** — first follow-up by email if PPQ has not been confirmed-returned.
4. **Day 14** — escalation to BPC PIC; PIC calls reference directly.
5. **Day 21** — final follow-up; document non-response explicitly if PPQ still not returned.
6. **At proposal submission** — completed PPQs returned **directly from owner reference to `{{AGENCY}}` Contracting Officer** per Section L instructions; BPC tracks status only via [`ppq-tracking-log.md`](ppq-tracking-log.md), not the content.

## Files in this directory

| File | Purpose |
|---|---|
| [`README.md`](README.md) | This index |
| [`ppq-cover-letter-to-client.md`](ppq-cover-letter-to-client.md) | Template letter from BPC to the cited owner reference, requesting PPQ completion. Specifies the 3-page response window, return method to the federal CO, and BPC POC for clarifications. |
| [`ppq-standard-federal-form.md`](ppq-standard-federal-form.md) | Generic 12–15 question federal PPQ template — used when the agency RFP does not provide its own form. Aligned with the typical Likert-plus-narrative federal model (cost, schedule, technical, management, customer satisfaction). |
| [`ppq-tracking-log.md`](ppq-tracking-log.md) | Internal BPC tracking template — per-project PPQ status (requested-date, sent-to, return-to-CO method, returned-date, score summary if shared). Internal-only; not submitted with the proposal. |

## How to use

1. At RFP issuance, read Section L for the PPQ requirement (number, form, deadline, return method).
2. Use the **agency-provided PPQ form** if the RFP includes one. If not, use [`ppq-standard-federal-form.md`](ppq-standard-federal-form.md). Do not substitute BPC's generic form for an agency-mandated form.
3. Generate cover letters from [`ppq-cover-letter-to-client.md`](ppq-cover-letter-to-client.md) — one per cited owner reference. Personalize per project.
4. Email the package (cover letter + PPQ form + project fact-reminder card) to each cited owner reference within 48 hours of RFP issuance. Copy BPC PM and PIC.
5. Track in [`ppq-tracking-log.md`](ppq-tracking-log.md). Follow up at Day 7, escalate at Day 14, final at Day 21.
6. **Do not** request a copy of the completed PPQ from the past client. The PPQ goes directly from past client → federal CO. If a client volunteers a copy, do not include it in the proposal — that compromises the assessment integrity and can flag the proposal for rejection.

## Cross-references

- Cited past projects + relevance per bid type: [`firm/firm-profile.json → past_project_selection_rules`](../../firm-profile.json)
- Past-performance writeups (paste-ready content for the proposal volume): [`../past-performance/`](../past-performance/)
- Federal RFP Volume III (cites the projects + tracks PPQ coordination): [`../federal-volumes/volume-iii-past-performance.md`](../federal-volumes/volume-iii-past-performance.md)
- Compliance posture (firm-level past-performance gaps): [`../../compliance/README.md`](../../compliance/README.md)

## Firm-data flags that affect PPQ completeness

Per `firm-profile.json`:

- **All three primary past-performance projects** (Lavon RV Park, Hindu Temple of Southlake, Holiday Inn Hall Park) currently have **`[USER TO FILL]` reference contacts** — owner-side names, emails, and phones must be confirmed as live and reachable before the cover letter goes out. A PPQ sent to a stale POC is wasted and damages the score.
- **Lavon RV Park is in execution.** The owner-side reference can speak to BPC's project posture and bondability, but cannot speak to a delivered project. Adjust the cover letter and form to reflect "in-progress" status.
- **Hindu Temple of Southlake is in execution.** Same caveat.
- **Holiday Inn (Hall Park) — completion date and contract value are not in source files.** Confirm both before requesting a PPQ.

## Placeholder convention

Same as the rest of the capability library:

- `{{UPPER_SNAKE}}` — project-specific facts (RFP-derived or per-PPQ)
- `[USER TO FILL]` — firm-internal data not in `firm-profile.json` (especially owner-reference contact info)
- `[TEMPLATE]` — structural skeletons / illustrative examples
