# NO-GO Memo: Plano Legacy Trail Pond Restoration (Bid 2026-0422-B)

**Decision date:** 2026-05-30
**Opportunity close date:** 2026-07-06 14:00 CT (open at decision time)
**Verdict:** NO-GO (scope mismatch — specialty heavy-civil dredging is outside BPC's NAICS lane)

---

## 1. What it was

City of Plano Purchasing **Bid 2026-0422-B** — Legacy Trail Pond Restoration (project PKR-D-00006). Scope is **pond silt/sediment removal via hydraulic dredging and dewatering** at W.H. "Buzz" Rasor Park, with staging adjacent to an elementary school and traffic restrictions during school drop-off / pick-up. Estimated value $1,335,000. Mandatory site visit (6/11 or 6/18, 3:30 PM CT). Submission via IonWave (`https://planotx.ionwave.net`) or in-person at 1520 K Avenue, Plano TX 75074.

## 2. Why no-go

**Primary reason: scope is specialty heavy-civil (NAICS 237990 / 562910 environmental remediation), not BPC's NAICS 236220 / 236118 / 238 lane.**

- **Hydraulic dredging + dewatering** is a regulated specialty trade with its own equipment fleet (cutter-suction dredges, geotextile dewatering tubes, sediment-management trains), permitting (TCEQ + USACE 404 / 401), and operator licensing.
- BPC's `firm/firm-profile.json → trade_capabilities` does **not** include dredging, sediment management, or pond/lake restoration. The closest adjacency is "Site work / excavation / grading" (managed via subs), but that does not extend to in-water hydraulic dredging.
- BPC has **no past performance** in pond / lake / waterway restoration. The Lavon RV Park scope included storm drain + detention, not in-water work.

**Secondary reasons:**
- $1.335M estimated value is at the upper edge of BPC's recent-bid comfort zone, which is acceptable on a familiar scope but is a stacked-risk decision on a novel scope.
- Mandatory site-visit attendance is a hard responsiveness requirement, and the school-adjacent staging adds child-safety operational complexity.

## 3. Did this fit BPC?

**No (scope problem, not process problem).**

| Criterion | Match | Reasoning |
|---|:---:|---|
| Scope match | ✗ | Hydraulic dredging is outside BPC's trade list; no past performance |
| Scale match | ⚠️ | $1.335M is at upper edge of BPC's comfort zone — acceptable on familiar scope only |
| Geographic match | ✓ | Plano is in BPC's Collin County core radius |
| Procurement experience | ⚠️ | IonWave portal is familiar (CHS Cafeteria, Allen Veterans Memorial) — but procurement is not the limiting factor |
| Set-aside fit | n/a | City of Plano does not appear to set aside; HUB / M/WBE participation typically encouraged but not scored on heavy-civil bids |

**Conclusion: BPC is unequipped for the core scope. Bidding would either require partnering with a dredging specialist (where BPC adds limited value) or quoting a scope BPC cannot perform.**

## 4. If similar opportunity arises, what to track differently

### Track 1 — Recognize "pond restoration / dredging / lake rehabilitation" as a flag scope domain

When the digest scope text includes "dredging," "dewatering," "sediment removal," "pond restoration," "lake restoration," "silt removal," or "wetland mitigation," **route to no-go without further triage.** Add this trigger phrase list to the intake convention.

### Track 2 — Plano IonWave is still a useful subscription

City of Plano IonWave (`https://planotx.ionwave.net`) is BPC's first concrete Plano municipal exposure. **Subscribe to the BPC IonWave supplier profile** for City of Plano so future Plano facility-renovation / building-construction opportunities (BPC's actual lane) are caught early. Filter by NIGP commodity codes covering NAICS 236220.

### Track 3 — Heavy-civil partnership question (long-term)

If BPC wants to expand into heavy-civil partnerships (joint venture with a dredging contractor on a future opportunity), build the relationship **outside** the bid window — not under deadline pressure. No partnership decision is appropriate to make in a single-opportunity context.

## 5. Source

DFWMSDC Construction Members digest, 2026-05-30, Opportunity #4 (verbatim text quoted in [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) is *not* the source — that batch is a different ingestion).

Confirmed facts from digest:
- Bid # 2026-0422-B
- Title: Legacy Trail Pond Restoration, PKR-D-00006
- Issue Date: 5/28/2026 07:00:01 AM (CT)
- Mandatory site visit: 6/11/2026 OR 6/18/2026 3:30 PM CT
- Close: 7/6/2026 14:00 CT
- Estimated $1,335,000
- Scope: hydraulic dredging + dewatering at W.H. "Buzz" Rasor Park
- Contact: Stephanie Pearson, City of Plano, 1520 K Avenue, Plano TX 75074, `spearson@plano.gov`

## 6. Disposition

- No solicitation source files mirrored to OneDrive (not a pursue scaffold; only the digest text is on file)
- Memo entered in `bids/_NO_GO/`
- Stephanie Pearson contact retained in this memo only (Public-class; not surfaced into firm-profile or any global file per data-classification policy)
- If a future Plano facility-renovation / building-construction opportunity surfaces (BPC's actual lane), open a fresh workspace
