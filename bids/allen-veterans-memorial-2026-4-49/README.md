# Allen Veterans Memorial Improvements — IFB 2026-4-49

**Agency:** City of Allen, Texas — Purchasing Department
**Method:** IFB (sealed bid, best-value award language) under **Tex. Local Gov't Code Ch. 252** — municipal CSP-style
**Project:** Allen Veterans Memorial — expansion of the existing memorial at **Bethany Lakes Park**
**Place of performance:** Bethany Lakes Park, Allen, TX 75013 (Collin County)
**Response deadline:** **Thursday, June 11, 2026 — 2:00 PM CT**
**Bid opening:** Same — 6/11/2026 14:00 CT
**Portal:** City of Allen IonWave — `https://allentx.ionwave.net/`

## Status

- **Source playbook:** [`firm/playbooks/texas-municipal-csp.md`](../../firm/playbooks/texas-municipal-csp.md)
- **Triage:** [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) (G1)
- **Scaffold created:** 2026-05-30 (deterministic ingest; no LLM calls; OpenAI quota exhausted)
- **First exemplar of:** `texas-municipal-csp` playbook (per `firm/playbooks/README.md`, this playbook had no shipped exemplar before this scaffold)

## Why this opportunity

1. **Scope fit.** Memorial-expansion / hardscape / site work at a city park is well within BPC's NAICS 236220 lane and a natural extension of Lavon RV Park (new-construction park amenities) and Hindu Temple of Southlake (institutional finish-out). The Bethany Lakes Park site is in-region for BPC's Frisco / Little Elm / Allen drive radius.
2. **Magnitude.** Not stated in the legal ad or event invitation. Pull the IFB packet from IonWave to read the engineer's estimate. Likely municipal-park magnitude (~$100K–$1M based on memorial-expansion scope), which lands inside BPC's recent-bid comfort zone.
3. **Process fit.** Allen IonWave is the same portal family as CISD CHS Cafeteria (already in `bids/chs-cafeteria-2026-0608-01/`); BPC's IonWave registration learning is reusable.
4. **Pipeline value.** First Allen / North-Collin-County municipal exemplar; opens future Allen, Plano, McKinney, Frisco municipal CSP work.

## Files

- [`01-overview.md`](./01-overview.md) — solicitation summary, contacts, key dates
- [`02-bid-prep-checklist.md`](./02-bid-prep-checklist.md) — gate-by-gate prep checklist (municipal-CSP variant)
- [`03-missing-documents.md`](./03-missing-documents.md) — IFB packet, bid form, Exhibit 1 insurance — referenced in the Bid Invitation but **not in the OneDrive drop**; must be pulled from IonWave
- [`06-scope-outline.md`](./06-scope-outline.md) — initial scope outline (needs IFB packet to refine)
- [`07-risk-register.md`](./07-risk-register.md) — initial risks (municipal CSP overlay: CIQ, HB 1295, local-preference, prevailing wage)
- [`contacts.md`](./contacts.md) — agency-side contacts
- [`source-files-manifest.md`](./source-files-manifest.md) — what the OneDrive drop contains + what's still missing

## What is NOT in this scaffold yet

- No `04-scope-of-work.md` (needs IFB packet from IonWave)
- No `05-bid-form-prep.md` (the bid form is a separate XLSX referenced in Bid Invitation; not in drop)
- No `08-pricing-strategy.md` / `09-proposal-draft.md` (out of scope for the ingest slice)
- No `_meta.json` (repo convention is to use `01-overview.md` for solicitation metadata; not introducing a new convention here)
- No HSP plan (municipal CSPs don't carry HUB Subcontracting Plan requirements under Ch. 252; M/WBE / local-preference overlays vary city-by-city — confirm against the IFB packet)
