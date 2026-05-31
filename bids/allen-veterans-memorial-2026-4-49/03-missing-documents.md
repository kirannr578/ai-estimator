# Missing documents — Allen Veterans Memorial 2026-4-49

The OneDrive drop on 2026-05-27 contains only the **Legal Ad** and the **IonWave Event Invitation** (an 11-page event-metadata document that lists what's *referenced* by the IFB without including the IFB itself). The actual bid documents must be pulled from IonWave.

## Referenced in `Bid Invitation.pdf` (file #2) but NOT in the OneDrive drop

| Document | Status | Source |
|---|---|---|
| **IFB Packet — Veterans Memorial Improvements.pdf** | 🔴 Missing | IonWave `https://allentx.ionwave.net/` (View Online) |
| **Bid Form.xlsx** | 🔴 Missing | IonWave (View Online; download required for pricing build) |
| **Exhibit 1 — Contractor Insurance Requirements & Agreement.pdf** | 🔴 Missing | IonWave (View Online) |

## How to pull

1. Log in at `https://allentx.ionwave.net/` as a registered supplier.
2. Search for solicitation `2026-4-49 — Veterans Memorial Improvements`.
3. Download all three attachments above into `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\Allen\` (create the subfolder; OneDrive stays canonical).
4. Re-run `tmp_smoke/ingest_landmark_05272026.py` (point it at the new subfolder) to regenerate the inventory + first-page text.
5. Update [`01-overview.md`](./01-overview.md) and [`06-scope-outline.md`](./06-scope-outline.md) with the now-known scope, dates, magnitude.

## Other documents likely needed (not yet referenced)

| Document | Why needed |
|---|---|
| Drawings (Architectural / Civil / Site / Lighting) | Memorial expansion is hardscape-heavy; without drawings, scope cannot be priced. If drawings are bound into the IFB packet, no separate pull is needed; otherwise expect a separate `Drawings.pdf` or `Drawings.zip` on IonWave. |
| Geotechnical report | If the memorial expansion includes new foundations, slabs, or hardscape on previously unbuilt ground, the City may provide a geotech. Typically a separate attachment. |
| Existing-conditions survey | Helpful for sub-pricing of demolition + tie-in scope. |
| Davis-Bacon / Tex. Gov't Code Ch. 2258 prevailing-wage schedule for Collin County | Required for labor build-up. Allen publishes the schedule; sometimes inline in the IFB packet, sometimes as a separate attachment. |
| Addenda (if any) | None yet visible. Monitor IonWave daily through 2026-06-09. |

## Risk if not pulled

- **Cannot estimate** without the Bid Form and drawings.
- **Cannot confirm magnitude** without the IFB packet § engineer's estimate (if disclosed) or the Bid Form schedule.
- **Cannot confirm insurance posture** without Exhibit 1 (limits, additional-insured wording, umbrella threshold).
- **Cannot prep CIQ / HB 1295** confidently without knowing the contract magnitude (HB 1295 only triggers ≥ $1M).

The Path-B scaffold is a **placeholder** until these three documents are in hand. Pre-bid meeting on 2026-06-02 is the natural pull-or-bail decision point.
