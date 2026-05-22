# Bid prep — TAMU Harrington Education Center, Lab 303 Renovation

**Solicitation:** 2025-06813
**Agency:** SSC Services for Education (on behalf of Texas A&M University, Part 02)
**Project:** Harrington Education Center, Bldg 0435 — Lab 303 (Science Education Classroom/Lab) renovation
**Location:** College Station, TX 77843
**Status:** **DRAFT — BLOCKED ON CSP PACKAGE** (we only have the public Notice of Project; full CSP construction documents have not been pulled from the e-Builder portal yet)

---

## Headline numbers

| Item | Value | Source |
|---|---|---|
| Estimated budget range | $115K – $310K (single-room lab reno; see `price-references.md`) | Inferred — no published owner budget |
| Estimated total contract value (target) | ~$200K–$250K likely | Inferred from typical TAMU System single-room lab modernization |
| CSP RFP + HSP due | **2026-06-10, 2:00 PM CT** | Notice of Project |
| Public proposal opening | 2026-06-10, 2:30 PM CT — SSC Facilities Services Conf Rm 204 (+ Teams) | Notice of Project |
| Period of performance | TBD (project start TBD, finish TBD) | Notice of Project |
| Set-aside / HUB | HSP **required**; monthly HUB Progress Assessment Reports (PARs) tied to pay apps | Notice of Project |
| Contract type | Competitive Sealed Proposal (CSP) under TAMU System UGSC | Notice of Project + Texas Education Code Ch. 51 / Gov't Code 2269 |
| NAICS (inferred, not stated in Notice) | 236220 — Commercial & Institutional Building Construction | Inferred from work scope |

---

## What's complete in this workspace

- [x] `01-overview.md` — solicitation, location, dates, contacts, scope summary
- [x] `02-bid-prep-checklist.md` — every form / registration / insurance / bonding line we need
- [x] `03-missing-documents.md` — authoritative list of what we still need from SSC / Patterson / e-Builder
- [x] `04-scope-of-work.md` — trade-by-trade scope draft with "[TBD from drawings]" placeholders
- [x] `05-hsp-plan.md` — HUB Subcontracting Plan strategy + outreach playbook
- [x] `06-evaluation-strategy.md` — how TAMU CSPs score and what we should emphasize
- [x] `07-risk-register.md` — bid-specific risks with mitigations
- [x] `takeoff-template.json` — empty `Estimate`-shaped skeleton (per `core/schemas.py`) keyed to scope items
- [x] `price-references.md` — $/SF benchmarks for institutional classroom / lab reno
- [x] `contacts.md` — all POCs from the Notice + suggested outreach plan
- [x] `timeline.md` — backwards-planned schedule from June 10 due date

## What's blocked

- [ ] Real takeoff quantities — need the architectural / MEP drawings from the e-Builder portal
- [ ] Final HSP form completion — need TAMU's specific HSP template (and likely Brazos County HUB target %s) from the CSP package
- [ ] Insurance limit confirmation — need TAMU System Supplementary General Conditions to confirm Article 5 limits (the 2010 UGSC baseline gives the floor; TAMU SGC may raise it)
- [ ] Bonding commitment letters — bonding agent needs a real total bid number, which needs takeoff, which needs drawings
- [ ] Pricing proposal form — comes with the CSP package; format varies by SSC PM
- [ ] Sub quotes — can't solicit until we have drawings to send out
- [ ] Pre-proposal meeting record — we **missed** the 5/14/2026 pre-proposal meeting (today is 2026-05-22). Need to ask Joelle for the sign-in sheet, recording, and any pre-proposal RFI responses

---

## Tomorrow's actions (top 5)

1. **Email Joelle Shidemantle (SSC PM)** today / first thing tomorrow — confirm CSP package availability on the e-Builder / Trimble Unity Construct portal (link is in the Notice); ask her to forward the pre-proposal meeting sign-in / recording / Q&A since we missed the 5/14 meeting; confirm whether late-arrivers can still bid.
2. **Register / log in to the e-Builder Public Landing page** at `https://app.e-builder.net/public/publicLanding.aspx?QS=323d686fd1304ccbb2a0ee7d143af64b` and pull the full CSP construction documents, drawings, specs, HSP form, pricing form, and any addenda already issued.
3. **Email Fred Patterson (Patterson Architects)** to introduce ourselves as a prospective bidder and request a site walk of Lab 303 (state existing-conditions risk is high on a lab reno; ask whether site access can be arranged through Joelle).
4. **Email Patty Winkler (TAMU HUB Operations)** asking for the TAMU-specific HSP template version and any project-specific HUB subcontracting goals — also confirm that statewide Texas HUB goals (currently ~21.1% for special trade construction) apply unless TAMU specifies a project goal.
5. **Notify bonding agent** of the upcoming submission (5% bid bond required by TAMU System pattern, plus 100% Payment & Performance bond commitment) so capacity is reserved against an estimated ~$250K bid envelope; provide updated final number after takeoff.

---

## Hard rules respected in this workspace

- All work product lives under `bids/tamu-harrington-2025-06813/`. No edits to `core/`, `app.py`, `analyze.py`, `prompts/`, `tests/`, `requirements.txt`, repo-root `README.md`, or any other code path that F1 (CWICR cost-DB) or F3 (drawing pre-pass) might rebase over.
- `analyze.py` was **not** run. The takeoff template is a hand-built skeleton intended to be filled in once F1 / F3 land and drawings arrive.
- `.env` and any API keys were **not** read, printed, or referenced.
- `inbox/` source PDFs were read (via the `Read` tool) but not copied or committed; the `inbox/` tree remains untracked per repo convention.
- No fictional internal data — every place that needs the firm's own data (named insurance carrier, exact bonding capacity, specific past projects, named HUB subs) carries a `[USER TO FILL]` marker.

---

## File map

```
bids/tamu-harrington-2025-06813/
├─ README.md                          ← you are here
├─ 01-overview.md
├─ 02-bid-prep-checklist.md
├─ 03-missing-documents.md
├─ 04-scope-of-work.md
├─ 05-hsp-plan.md
├─ 06-evaluation-strategy.md
├─ 07-risk-register.md
├─ takeoff-template.json
├─ price-references.md
├─ contacts.md
└─ timeline.md
```

`local/` — if you create a sibling `bids/tamu-harrington-2025-06813/local/` folder for sub-quote PDFs, bonding-agent paperwork, scratch spreadsheets, or anything else that shouldn't be committed, it is gitignored via the workspace `.gitignore` rule `bids/*/local/`.
