# No-go memo — TMD Camp Mabry Temporary Modular Office (RFI TMD26-CFMO-RFI001)

**Decision date:** 2026-05-30
**Decision by:** Cursor agent triage of OneDrive `Landmark/05272026` batch (deterministic ingest; no LLM calls)
**Solicitation status:** Pre-solicitation **Request for Information (RFI)** — not a contract opportunity. Response deadline 2026-07-14 16:00 CT.

## 1. What it was

The Texas Military Department (TMD) issued an **RFI (TMD26-CFMO-RFI001)** on **2026-05-26** seeking market information from qualified vendors of **prefabricated temporary modular office buildings**. Purpose: support temporary office needs at Camp Mabry, Austin, TX during upcoming building renovations estimated March 2027 – March 2030. Capacity: up to 150 personnel. NIGP codes **971-08** (Pre-Fab Building Rental/Lease) and **971-40** (Mobile Office Rental/Lease).

This RFI is explicitly **for information gathering and planning purposes** — it is not a solicitation, will not result in a contract, and responses inform future procurements that may or may not happen.

| Field | Value |
|---|---|
| Solicitation # | TMD26-CFMO-RFI001 |
| ESBD posting | 520356 |
| Issuing agency | Texas Military Department (TMD) — Contract Management Branch, CFMO |
| POC | Tom Picazo, CTCD — `FY26RFIPORT@cfmo.mil.texas.gov` |
| Procurement vehicle | RFI (Request for Information) — pre-solicitation only |
| Response deadline | 2026-07-14 16:00 CT |
| Site visits | 2026-06-09 13:00 CT (1st) / 2026-06-10 10:00 CT (2nd) |
| Future window | March 2027 – March 2030 renovations |
| Capacity sought | ≤ 150 personnel |

## 2. Why no-go

**Scope mismatch — primary reason.**

BPC is a **general contractor under NAICS 236220** (Commercial and Institutional Building Construction). The TMD RFI is seeking responses from **modular-office leasors / resellers** under NIGP 971-08 and 971-40 — a fundamentally different business model (rental/lease of prefabricated buildings, not new construction). BPC does not maintain a modular-office inventory, has no manufacturer relationship for prefab modulars, and has no rental/lease infrastructure (insurance, transport, setup-and-strike crew, monthly billing).

Secondary reasons:

- **RFI ≠ contract** — even an excellent RFI response generates no direct revenue. The RFI's purpose is to inform TMD's eventual specification of a future procurement that BPC could not credibly bid on without acquiring a modular-office product line.
- **Information-asymmetric** — a credible RFI response in this space requires deep product knowledge (insulation R-values for modulars, ADA-compliant modular configurations, electrical-load capacities, HVAC tonnage sizing for prefab envelope, transport permitting, foundation systems for temporary modulars, etc.) that BPC cannot bluff.
- **Long horizon** — even if TMD eventually issues a procurement, it's gated on completion of "upcoming building renovations" projected March 2027 – March 2030. The procurement may not appear for 12-18 months and may be re-scoped.

## 3. Did this fit BPC?

**No.** This is a clean scope-mismatch no-go — BPC's NAICS lane and acquired competencies do not overlap with the modular-office product/lease market. Not a "we'd love to but the window closed" — a "this isn't BPC's business."

## 4. If a similar opportunity arises, what to track differently

- **Tag NIGP 971-08 and 971-40 (and similar prefab/modular codes) as DISQUALIFYING in BPC's ESBD watchlist filters.** When an ESBD posting carries these codes, the triage decision is automatic: no-go on scope alone.
- **Distinguish RFI from solicitation in batch triage.** This batch's OneDrive folder included the TMD RFI alongside actual IFBs and an RFP. A clean intake convention is to separate `*_RFI_*` filenames into a sub-tracker (`bids/_WATCHLIST/`) automatically rather than treating them as candidate solicitations.
- **TMD Camp Mabry is real and active.** Even though this specific RFI isn't BPC's, TMD is a TX state agency that *does* let construction contracts on Camp Mabry (and other TX National Guard facilities). If a future TMD IFB/CSP at NAICS 236220 lands — *Building Construction*, not *Modular Office Rental* — that's a legitimate BPC opportunity. Add `Camp Mabry` + `Texas Military Department` to BPC's ESBD-watch keyword list.

## 5. Source

- OneDrive: `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\ESBD_520356_1779824305593_Camp Mabry Temporary Modular Office RFI 5.26.26.pdf`
- ESBD posting: 520356
- Batch triage: [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) (G3)
- Captured in [`firm/playbooks/_learning-log.md`](../../firm/playbooks/_learning-log.md) item #6 (modular-office NIGP codes as a disqualifying filter)
