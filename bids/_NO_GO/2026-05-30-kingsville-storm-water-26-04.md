# NO-GO Memo: City of Kingsville Storm Water Improvements (Bid 26-04 GLO SW Project 7)

**Decision date:** 2026-05-30
**Opportunity close date:** 2026-06-11 14:00 CT (open at decision time)
**Verdict:** NO-GO (scope mismatch + geographic out-of-region)

---

## 1. What it was

City of Kingsville **Bid 26-04 GLO SW Project 7 (S 6th St.) Storm Water Improvements**, funded under **CDBG-MIT GLO Contract No. 22-085-009-D237**. Sealed-bid receipt 2:00 PM Tuesday June 11, 2026 at 400 W King Ave, Kingsville TX 78363, addressed to Juan Carlos "Charlie" Cardenas, P.E. Public bid opening immediately following. MBE/SBE/WBE/Section 3/veteran-owned/labor-surplus participation encouraged.

## 2. Why no-go

**Two independent disqualifiers, either of which alone is sufficient:**

### Disqualifier A — Scope mismatch (heavy-civil storm-water utility work)

"S 6th St. Storm Water Improvements" is **storm-drainage utility construction** — typically NAICS 237110 (Water and Sewer Line and Related Structures Construction). The scope (storm sewer extension, inlets, outfalls, sometimes retention/detention) is in **regulated heavy-civil** territory:
- Buried storm-drain pipe install (RCP, HDPE)
- Inlet boxes, manholes, headwalls
- Roadway / sidewalk replacement over the trench
- TCEQ permitting + USACE coordination if outfalls touch waters of the U.S.

BPC's `firm/firm-profile.json → trade_capabilities` lists "Site work / excavation / grading" as a **managed-via-subs** capability — not a self-perform lane. BPC has no past performance in municipal storm-drainage utility construction. The closest adjacency is Lavon RV Park (storm drain + detention as a small new-build component), which is not the same as a municipal storm-water capital project.

### Disqualifier B — Out of geographic region

Kingsville, TX is in **Kleberg County**, ~360 miles south of DFW (south of Corpus Christi). BPC's service radius per `firm/firm-profile.json → trade_capabilities.service_radius` is "North Texas + central Texas; primary operations in Dallas-Fort Worth metroplex (Denton, Collin, Dallas, Tarrant counties)." Kingsville is **South Texas / Coastal Bend** — outside the service area by a wide margin. Mobilization cost alone would make BPC non-competitive vs. local contractors; ongoing supervision would be impractical.

## 3. Did this fit BPC?

**No (two independent fit problems).**

| Criterion | Match | Reasoning |
|---|:---:|---|
| Scope match | ✗ | Heavy-civil storm-drainage utility construction is outside BPC's NAICS lane |
| Scale match | ? | Magnitude not stated in digest; CDBG-MIT projects are typically $500K – $5M |
| Geographic match | ✗ | Kingsville is ~360 mi from DFW — outside BPC's service area |
| CDBG / federal-overlay readiness | ⚠️ | CDBG-MIT projects carry Davis-Bacon prevailing wage + Section 3 hiring + Buy America requirements — BPC has not exercised these on a non-Texas-state job |
| Set-aside positioning | ✓ | MBE/SBE/WBE/Section 3 participation is encouraged; BPC's MBE/SBE certs (currently expired per profile) would be relevant if BPC were in scope and region |

**Conclusion: Even a perfect MBE / Section 3 positioning doesn't compensate for being outside both the trade scope and the service area.**

## 4. If similar opportunity arises, what to track differently

### Track 1 — DFWMSDC mailing list inclusivity

The DFWMSDC mailing list is statewide and forwards opportunities far outside DFW. Recognize that **the channel ≠ the geography**. When triaging future DFWMSDC digests, screen the *site location* first — anything south of San Antonio / Bryan-College Station is presumptively out-of-region for BPC.

### Track 2 — CDBG-MIT GLO program awareness (informational)

The Texas General Land Office (GLO) administers federal CDBG-MIT (Mitigation) funds under the `22-085-...` contract numbering. CDBG-MIT projects in DFW counties (Dallas, Tarrant, Denton, Collin) **do** appear and **would** be in BPC's scope/region — track GLO's CDBG-MIT project pipeline at `https://recovery.texas.gov/` for North-Texas-region projects when the scope matches BPC's lane (residential rehab, facility renovation — not heavy-civil utility).

### Track 3 — Heavy-civil utility scope is a flag domain

Add "storm water improvements," "water and sewer line," "lift station," "manhole rehabilitation," "stormwater pollution prevention" (as a capital-construction line, not a SWPPP overlay on a building project) to the intake-flag list as **route-to-no-go without further triage**.

## 5. Source

DFWMSDC Construction Members digest, 2026-05-30, Opportunity #5.

Confirmed facts:
- Bid # 26-04
- Project: GLO SW Project 7 (S 6th St.) Storm Water Improvements
- Funding: CDBG-MIT GLO Contract No. 22-085-009-D237
- Bid receipt + opening: 2:00 PM Tuesday June 11, 2026 at 400 W King Ave, Kingsville TX 78363
- Bid addressed to: Juan Carlos "Charlie" Cardenas, P.E.
- Info: `https://www.cityofkingsville.com/departments/purchasing/rfp-bid-openings-fy-2026/`
- Contact: Ella McMahan, Administrative Assistant l Engineering, City of Kingsville, P.O. Box 1458, Kingsville TX 78363, 361-595-8007, `emcmahan@cityofkingsville.com`

## 6. Disposition

- No solicitation source files mirrored to OneDrive
- Memo entered in `bids/_NO_GO/`
- Contacts retained in this memo only (Public-class; not surfaced into firm-profile or any global file)
- Future South-Texas / Coastal-Bend opportunities will be filtered at intake
