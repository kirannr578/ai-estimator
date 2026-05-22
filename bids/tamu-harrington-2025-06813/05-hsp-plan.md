# 05 — HUB Subcontracting Plan (HSP) strategy

> The Notice is explicit: "**HUB Subcontracting Plan Required: Yes ☒**". Failure on HSP is the most common reason TAMU System CSP proposals are deemed non-responsive. Start the good-faith-effort (GFE) clock today.
>
> This document is a **strategy** draft. The final HSP must be on TAMU's specific HSP form (Priority-1 item #6 in `03-missing-documents.md`).

---

## A. The rules of the game (Texas HUB Program, in force as of 2024 amendment to 34 TAC §20.281–.298)

- A "HUB" is a Texas-certified Historically Underutilized Business — generally minority-, woman-, or service-disabled-veteran-owned, certified through the TX Comptroller's CMBL/HUB program.
- TAMU and other state agencies are required to make a good-faith effort to meet the **statewide HUB participation goals** when subcontracting opportunities exist:
  - **Heavy construction** (other than building) — 11.2%
  - **Building construction**, including general contractors and operative builders — 32.7% — *most often quoted for whole-building work*
  - **Special trade construction** — 21.1% — *typically applies to renovation work like Lab 303*
  - Professional services — 23.7%; other services — 26.0%; commodities — 21.1%
- TAMU may set a **project-specific HUB goal** that overrides the statewide goal. Until confirmed, assume the **statewide 21.1% special-trade goal applies** to the Lab 303 reno.
- The prime is allowed to **self-perform** any portion of the work as long as the self-performed scope is justified and documented in the "Self-Performing Justification" section of the HSP. The HUB goal applies only to the **subcontracted** portion.
- A prime that does NOT meet the HUB goal can still be responsive if it documents **good faith effort** (GFE) — see § E below.
- After award, monthly **HUB Progress Assessment Reports (PARs)** must be filed with each pay application. The Notice confirms this.

---

## B. Self-performing justification (template)

`[USER TO FILL]` — list the scopes the firm will self-perform (typically GCs, supervision, demo if in-house, possibly carpentry/casework if in-house). For each:

- Scope (e.g. "Project supervision and general conditions")
- Estimated dollar value
- Reason for self-performance (capability, cost control, schedule risk, etc.)

Self-performed dollars are removed from the denominator before computing the HUB target percentage. If the firm subcontracts 75% of the work, the HUB target applies to that 75% only.

---

## C. Per-trade subcontracting plan — target HUB allocation

Based on the trade list from `04-scope-of-work.md`, and a working assumption that roughly 75% of the contract value will be subcontracted (typical for a small GC on a single-room reno), here is a draft trade-by-trade plan. Percentages are share-of-trade-subbed dollars going to HUB-certified subs.

| Trade | Approx % of contract | Plan | Target HUB share within trade | Notes |
|---|---|---|---|---|
| Demolition | 5–8% | Subcontract | **100%** (small-dollar; HUB demo subs abundant in TX) | Many HUB-certified demo subs in Brazos County and greater Houston |
| Drywall / metal-stud framing | 3–6% | Subcontract | 50% target | HUB-certified drywall subs common |
| Doors / frames / hardware | 1–3% | Material-only buy + self-installed, OR sub | 0–100% depending on buy/sub mix | If material-only, check HUB-certified door distributors |
| Flooring (LVT, sheet vinyl, base) | 4–7% | Subcontract | 50% target | HUB flooring subs available in central TX |
| Painting | 2–4% | Subcontract | **100%** target (small-dollar, easy HUB win) | HUB paint subs abundant |
| Acoustic ceilings | 2–3% | Subcontract | 50% | |
| Casework / lab-grade millwork | 7–12% | Subcontract | 25% (specialty; HUB availability thinner) | Document GFE if no HUB casework sub bids |
| Electrical | 10–15% | Subcontract | 50% target | HUB electrical subs available; lab-experienced HUB subs thinner |
| HVAC | 6–10% | Subcontract | 25% target | Lab-experienced HVAC subs are mostly mid-size, fewer HUB |
| Plumbing | 5–8% | Subcontract | 50% | |
| Fire suppression mods | 1–3% | Subcontract | 25% | NICET requirement may narrow the pool |
| Low-voltage pathway | 1–2% | Subcontract OR self-perform | 50% | |
| Lab utilities specialty | 2–4% | Subcontract | 0% if specialty unavailable in HUB; document GFE | |
| **General conditions / supervision (self)** | 8–12% | Self-perform | n/a — excluded from HUB calculation | |
| **OH + profit + bond** | 12–18% | Self | n/a — excluded | |

**Roll-up target — HUB share of subcontracted dollars: ≥ 21.1%** (statewide special-trade goal).
Plug-in: if total bid lands at ~$250K and ~$190K of that is subbed out, the HUB allocation target is ~$40K.

> ⚠️ The above is **planning** math. The actual HSP form requires per-vendor specifics (name, HUB certification number, scope, dollar value), not aggregate percentages. The aggregate plan is what the form rolls up TO; the line items are what we have to fill in.

---

## D. HUB sub outreach plan — solicit ≥3 HUB subs per trade

**Lookup:** Texas CMBL Search at `https://comptroller.texas.gov/purchasing/vendor/hub/search.php`.
- Filter by HUB-certified
- Filter by NIGP / NAICS code matching the trade
- Filter geographic region (Brazos County, Bryan/College Station, plus greater Houston / Austin radius for specialty work)

**Process per trade:**
1. Pull the top 5–10 candidate HUB subs from CMBL search
2. Email a standardized solicitation packet:
   - Project name + number
   - Scope summary for that trade
   - Bid due date (back-timed from June 10 → sub quote needed by June 1)
   - Plans / specs (attached or linked)
   - Required certifications (TX W-9, HUB certification cert, insurance)
   - GC contact for questions
3. Log every outreach: date, method (email / fax / certified mail), recipient, response (or non-response)
4. If a HUB sub bids and is selected → include in HSP with vendor #
5. If a HUB sub bids and is NOT selected (price, schedule, qualification) → document the reason
6. If a HUB sub does NOT respond → that's part of GFE evidence; document the attempt

**Suggested log format** (use a `local/hub-outreach-log.csv` outside git):
```
date,trade,sub_name,hub_cert_number,contact_email,method,outcome,bid_amount,notes
```

`[USER TO FILL: specific HUB sub names. Do NOT populate without actually contacting them.]`

---

## E. Good-faith-effort documentation (the make-or-break)

Texas HSP rules require at least **two of the following** when the HUB goal is not met. To be safe, do all four:

1. **Divide the scope into reasonable HUB-sized portions** — the per-trade table in § C is the seed for this; package small enough that a HUB sub can handle each chunk.
2. **Advertise the subcontracting opportunity** in at least two of:
   - The TX Comptroller's HUB News
   - A trade publication serving HUBs (e.g. Texas Construction News, the Greater Houston Black Chamber publication, the Asian American Chamber of Commerce Texas list, the Hispanic Contractors Association of Texas, the National Association of Women in Construction Texas chapter)
   - Posting on the firm's own subcontractor-bid portal with a HUB notice
3. **Send written notice to a representative sample of HUB subcontractors** for each subcontracting opportunity (the per-trade outreach in § D satisfies this).
4. **Attend HUB outreach events** the agency hosts (TAMU System runs periodic HUB events through the HUB Operations office).
5. **Contact a HUB Discretionary Contracting Forum** participant — for TAMU specifically, contact Patty Winkler (HUB Ops) to ask whether TAMU has a current discretionary contracting forum we should engage.

---

## F. Reporting cadence post-award

- **Monthly Progress Assessment Reports (PARs)** filed with each pay application — confirmed by the Notice
- TAMU HUB Operations (Patty Winkler) is the recipient
- Use the State of Texas Comptroller PAR form
- If actual HUB participation falls short of the HSP commitment, the prime must either revise the HSP (with TAMU concurrence) or document the reason and continue GFE

---

## G. Timeline for HSP work (mirrors `timeline.md`)

| Date | HSP milestone |
|---|---|
| 2026-05-22 | Pull CMBL HUB sub list per trade; start outreach emails. Email Patty Winkler for project-specific HUB goal. |
| 2026-05-23–26 | Send HUB outreach emails; log every response |
| 2026-05-27–28 | Publish ad in 2+ HUB publications |
| 2026-05-29 | Collect HUB sub quotes |
| 2026-06-01 | Lock HUB allocations; finalize HSP draft |
| 2026-06-03 | Internal HSP review; verify GFE backup binder is complete |
| 2026-06-08 | Final HSP signed; bound with proposal |
| 2026-06-10 | Submit |

---

## H. Risk callouts on HSP specifically

- **Lab specialty trades have thin HUB representation.** Lab casework, lab utilities, lab-experienced HVAC and plumbing — these scopes will struggle to meet the 21.1% target. Carry written GFE documentation for any trade where no HUB sub was responsive.
- **Patterson Architects's drawing turnaround** affects how fast we can package the per-trade scope packets for HUB outreach. If we don't have drawings by 2026-05-25, the outreach packets go out without drawings and explicit "drawings to follow" notes — acceptable for GFE but inferior for actual quote quality.
- **HUB certifications expire.** Before listing a HUB sub on the final HSP, re-verify their cert number on the CMBL search; expired certs get the HSP kicked back.
