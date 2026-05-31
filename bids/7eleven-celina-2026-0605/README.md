# 7-Eleven Celina, TX — ground-up convenience store + fueling center (Ready Construction sub-bid)

> ⚠️ **SHORT-FUSE BID** — sub pricing due to Ready Construction by **Friday, June 5, 2026 at 12:00 PM (Noon) CT**. That is **6 calendar days** from scaffold creation (2026-05-30). If BPC commits to this opportunity, sub outreach must start **today** and pricing must be locked by **2026-06-04 EOD** to leave a clean review buffer.

## Status snapshot

| Field | Value |
|---|---|
| GC issuing the bid | **Ready Construction** (private commercial GC) |
| Project | New 4,950 SF ground-up 7-Eleven convenience store + fueling center |
| Location | **Celina, TX** (Collin County) — exact street address not in digest |
| Procurement type at BPC's tier | **Subcontractor quote to a private GC** |
| Solicitation # | None (private GC sub bid; tracked internally as the **2026-06-05 noon** sub-quote due date) |
| Sub-quote due | **Friday, June 5, 2026 — 12:00 PM (Noon) CT** ⚠️ |
| Scaffold created | 2026-05-30 (deterministic ingest; no LLM calls; OpenAI quota exhausted) |
| Source | DFWMSDC Construction Members digest, 2026-05-30 (Public-class) |
| Source playbook | `[PLAYBOOK GAP]` — see [`firm/playbooks/README.md`](../../firm/playbooks/README.md) "Private commercial / institutional negotiated" row (marked "not playbook-grade; ad-hoc"); same gap as `bids/mcc-cosmetology-phase4-2026-0622/` — logged in [`firm/playbooks/_learning-log.md`](../../firm/playbooks/_learning-log.md) |

## Why this opportunity (BPC fit)

1. **Geographic fit — STRONG.** Celina is in **Collin County**, ~20 miles from BPC's Frisco / Little Elm office. Routine drive — no per-diem premium.
2. **Scope breadth.** Per the digest, the trades span: Survey, SWPPP, Erosion Control, Demo, Excavation, Termite Control, Site Utilities, Striping, Landscape/Irrigation, Concrete Paving, Concrete Foundations, Masonry (CMU/Stucco/Thin Brick/Thin Stone), Structural Steel, Miscellaneous Steel, Royston Millwork Install, Porter SIPs Panels, Roofing, Exterior Pac-Clad, Storefronts, Doors/HDW, Metal Stud Framing, Drywall, Canopy Column Wraps, Ceilings, FRP, Insulation, Flooring/Tile, Painting, Specialties, Mapes Canopies, Turnkey Equipment Install, Beverage Install, HVAC, Electrical, Plumbing, Fueling, Fueling Canopy (Jimco). BPC self-perform candidates: **Drywall, Metal Stud Framing, Painting, Flooring/Tile, FRP, Insulation, Doors/HDW install, Royston Millwork Install** (manage-via-subs candidates: Concrete, Masonry, Structural Steel, Roofing, MEP, Fueling).
3. **Past-perf fit.** Lavon RV Park (ground-up new construction with site work) is the closest exemplar; Hindu Temple of Southlake (institutional finish-out, ~10,700 SF) and Holiday Inn Hall Park (commercial finish, occupied building) round out the 3-pack.
4. **Magnitude.** 4,950 SF c-store + fueling center on a typical Texas commercial pad is roughly $1.5M – $4M total project value; BPC's sub package would be a fraction (likely $50K – $300K depending on scope chosen).

## Headline risks

- 🔴 **6-day fuse** — sub outreach must start today; full pricing must be locked by 2026-06-04 EOD.
- 🔴 **Plans portal gated (Autodesk BuildingConnected)** — cannot estimate without plans. **USER ACTION REQUIRED** to log into BuildingConnected and download plans/specs into OneDrive. See [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md).
- ⚠️ **Branded-store specifications** — 7-Eleven brand-standard specs (Royston millwork, Pac-Clad exterior, Mapes canopies, Jimco fueling canopy, Porter SIPs panels) are vendor-specific and may carry long-lead procurement. Confirm long-lead items are not on BPC's quoted scope, or accept the schedule risk.
- ⚠️ **Insurance status (COI expired per profile)** — BPC's CGL policy expired 2024-09-25 per `firm/firm-profile.json`. Ready Construction will not contract with an uninsured sub. Confirm renewal before quote submission.
- ⚠️ **No site visit listed in digest** — Either Ready Construction doesn't require one for this private project or the visit window has already happened or is implicit. Confirm with the GC contact.

## Why a thin scaffold (and not a full proposal slice)

This is a **triage scaffold only**, not a bid-prep slice. Per the user's task brief, the actual bid-prep happens later for any opportunity BPC commits to. Given the 6-day fuse, the realistic decision flow is:

1. **Today (2026-05-30 / 2026-05-31):** Confirm BPC has portal access to BuildingConnected and pull plans.
2. **By EOD 2026-05-31:** Decide go/no-go based on plans + total project magnitude. If no-go, flip this scaffold to a `bids/_NO_GO/` memo.
3. **2026-06-01 → 2026-06-04:** If go, run sub outreach + price build at maximum cadence.
4. **2026-06-05 by Noon:** Submit pricing to Brayden Florence at Ready Construction.

## Files

- [`01-overview.md`](./01-overview.md) — solicitation summary, contacts, key dates (verbatim from digest)
- [`02-bid-prep-checklist.md`](./02-bid-prep-checklist.md) — compressed sub-bid checklist for the 6-day fuse
- [`06-scope-outline.md`](./06-scope-outline.md) — trade-by-trade scope outline (annotated self-perform vs. sub)
- [`07-risk-register.md`](./07-risk-register.md) — initial risks, fuse-driven mitigations
- [`contacts.md`](./contacts.md) — Ready Construction contact (Brayden Florence)
- [`source-files-manifest.md`](./source-files-manifest.md) — what's in the digest + what's gated behind BuildingConnected
- [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md) — BuildingConnected link + USER ACTION REQUIRED marker

## What is NOT in this scaffold

- No `04-scope-of-work.md` (needs plans + specs from BuildingConnected)
- No `05-bid-form-prep.md` (Ready Construction bid form, if any, is in BuildingConnected)
- No `08-pricing-strategy.md` / `09-proposal-draft.md` (out of scope for triage slice)
- No `_meta.json` (repo convention is `01-overview.md`)

## Cross-references

- Triage source: DFWMSDC Construction Members digest, 2026-05-30
- Compliance baseline: [`firm/firm-profile.json`](../../firm/firm-profile.json)
- Reference workspace pattern: [`bids/mcc-cosmetology-phase4-2026-0622/`](../mcc-cosmetology-phase4-2026-0622/) (sibling private-GC sub-bid scaffold from same digest)
