# McLennan Community College CSC Module B Cosmetology Phase 4 Renovation — HCS sub-bid

**GC issuing the bid:** **HCS Inc.** (private commercial GC, Waco TX)
**Owner:** McLennan Community College (MCC)
**Method:** **Private GC sub-bid solicitation** — HCS is collecting subcontractor pricing on the *Owner's Proposal Form* layout to roll up an MCC bid. From BPC's perspective this is a **subcontractor quote to a private GC**, not a direct public-agency bid.
**Project:** CSC Module B Cosmetology Phase 4 Renovation — interior renovations to existing first-floor classrooms in the MCC CSC Module B Cosmetology Lab
**Place of performance:** **1400 College Drive, Waco, TX 76708** (McLennan County)
**Sub-quote due to HCS:** **Monday, June 22, 2026 — 10:00 AM CT**
**Site meeting:** **June 1, 2026 — 10:00 AM CT** (3 days from scaffold creation)

## Status

- **Source playbook:** `[PLAYBOOK GAP]` — see [`firm/playbooks/README.md`](../../firm/playbooks/README.md). The current playbook index is keyed to **public-agency** procurement archetypes (federal SBA RFQ, federal simplified-acquisition, federal best-value RFP, federal pre-solicitation, federal JOC, Texas state CSP/HSP, Texas municipal CSP) plus an "ad-hoc / not playbook-grade" row for **private commercial / institutional negotiated** work. This solicitation falls in that last bucket — it is a private GC (HCS Inc.) collecting subcontractor pricing for a community-college owner. **No "GC sub-bid" playbook exists today.** The closest sibling pattern is the *Private commercial / institutional negotiated* row, but that row is explicitly labeled "not playbook-grade; ad-hoc". Captured as a learning-log gap; the [`texas-state-csp-hsp.md`](../../firm/playbooks/texas-state-csp-hsp.md) playbook is **not** appropriate (community colleges are state-funded but HCS — not MCC — is running the procurement, so the Ch. 2269 / HSP framework does not apply at BPC's tier).
- **Source:** DFWMSDC Construction Members digest, **2026-05-30** (publicly distributed mailing list; contact info Public-class).
- **Triage classification:** **Strong-fit scaffold** (multi-trade interior reno; in BPC self-perform + manage-via-subs lane; bid window ~24 days).
- **Scaffold created:** 2026-05-30 (deterministic ingest; no LLM calls; OpenAI quota exhausted).
- **Site meeting urgency:** **3 days** from scaffold creation. Decide attendance immediately.

## Why this opportunity (BPC fit)

1. **Scope fit — STRONG.** Per the digest scope list ("Casework, Door Hardware, Glazing, Drywall, Paint, Flooring, HVAC, Plumbing, Electrical"), the trades break down cleanly into BPC self-perform (drywall, paint, flooring, possibly door hardware install) and manage-via-subs (casework, glazing, HVAC, plumbing, electrical). BPC could quote either (a) a **single-trade sub package** in BPC's self-perform lane, or (b) a **multi-trade rolled-up package** if HCS allows.
2. **Past-performance fit.** Closest exemplar is **Hindu Temple of Southlake** (institutional finish-out, Assembly A-3, ~10,700 SF — interior demo + finishes + partitions on an occupied institutional building). Holiday Inn Hall Park (commercial finish) and the cumulative SFH portfolio (drywall + paint + flooring + tile production) round out a 3-pack.
3. **Magnitude — UNKNOWN, but "Phase 4" + classroom interior reno suggests $50K–$500K total project.** BPC's sub package would be a fraction of that, well inside comfort zone.
4. **Geographic stretch.** Waco is **~95 miles south of Frisco** — at the edge of BPC's "North Texas + central Texas" service radius per `firm/firm-profile.json → trade_capabilities.service_radius`. Drive time ~1.5 hr each way. Workable for a phase-of-work superintendent assignment but not for daily site-walk visits. This is a trade-off worth weighing against the value of building a relationship with HCS Inc. as a Waco-area GC.
5. **Process fit — caveat.** The Owner's Proposal Form is HCS's required pricing layout. Without seeing it (it's behind the Box link below), BPC cannot be certain the line-item structure aligns with how BPC normally builds quotes. Pull the form first, then decide whether to quote.

## Headline risks

- ⚠️ **Site-meeting window is 3 days out (2026-06-01).** Mandatory attendance status is not stated in the digest. If HCS treats it as mandatory for responsiveness, BPC must register and attend or skip the bid. **Action: contact HCS Estimating immediately to confirm attendance posture.**
- ⚠️ **Plans / specs are gated behind a Box link** (`https://hcs-gc.box.com/s/bhy2pkudhlkcgcxfo7qxdb8vcjnhfwni`). User-side action required to open the link, download the plans + specs + Owner's Proposal Form, and stage them at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\HCS\05302026-mcc-cosmetology\`. See [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md).
- ⚠️ **Playbook gap.** No "GC sub-bid" playbook exists. Treat this scaffold as a thin Path-B stand-up; the proposal-prep slice (if BPC pursues) will need to invent the playbook on the fly or borrow patterns from `firm/proposal-library/` and `firm/scope-templates/`.

## Files

- [`01-overview.md`](./01-overview.md) — solicitation summary, contacts, key dates (verbatim quotes from digest)
- [`02-bid-prep-checklist.md`](./02-bid-prep-checklist.md) — gate-by-gate sub-bid prep checklist
- [`06-scope-outline.md`](./06-scope-outline.md) — initial scope outline keyed to digest scope list
- [`07-risk-register.md`](./07-risk-register.md) — initial risks (site meeting urgency, playbook gap, geographic stretch, owner-form fit)
- [`contacts.md`](./contacts.md) — HCS Estimating contact (sole contact disclosed in digest)
- [`source-files-manifest.md`](./source-files-manifest.md) — what's in the digest + what's gated behind Box
- [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md) — Box link + USER ACTION REQUIRED marker

## What is NOT in this scaffold

- No `04-scope-of-work.md` (needs Owner's Proposal Form + plans/specs from Box)
- No `05-bid-form-prep.md` (the Owner's Proposal Form *is* the bid form; pull from Box)
- No `08-pricing-strategy.md` / `09-proposal-draft.md` (out of scope for triage slice)
- No `_meta.json` (repo convention is `01-overview.md`)
- No HSP, no FAR-clause register, no DBA wage check (private GC sub-bid; not federal, not state-funded at BPC's tier)

## Cross-references

- Triage source: DFWMSDC Construction Members digest, 2026-05-30
- Compliance baseline: [`firm/firm-profile.json`](../../firm/firm-profile.json) (NAICS 236220 primary; SBE/MBE/HUB certs and current COI status need confirmation per profile flags)
- Reference workspace pattern: [`bids/allen-veterans-memorial-2026-4-49/`](../allen-veterans-memorial-2026-4-49/) (similar thin-scaffold pattern where bid documents are gated behind a portal)
