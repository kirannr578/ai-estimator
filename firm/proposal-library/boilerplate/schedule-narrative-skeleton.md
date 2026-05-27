# Boilerplate — Schedule Narrative Skeleton

> **Source mined:** [`bids/tamu-harrington-2025-06813/proposal/05-schedule-narrative.md`](../../../bids/tamu-harrington-2025-06813/proposal/05-schedule-narrative.md). Pattern is generic to multi-trade interior renovation; refine the durations + long-lead items per project.
>
> **Use:** Schedule narrative companion to a CPM Gantt — typically a sub-section of "Technical Approach" or "Schedule" in a state CSP. On federal LPTA, the baseline schedule is submitted post-award (typically NTP+14 days per RFP § F).

---

# Schedule Narrative — {{PROJECT_NAME}}

## 1. Overall duration

Blue Print Constructs proposes:

- **Notice to Proceed (NTP):** `{{NTP_TARGET_DATE}}`
- **Substantial Completion:** `{{SC_DAYS}}` calendar days from NTP → `{{SUBSTANTIAL_COMPLETION_DATE}}`
- **Final Completion:** `{{FC_DAYS}}` calendar days from NTP → `{{FINAL_COMPLETION_DATE}}`

The schedule is built bottom-up from approved unit-rate productivities + verified sub commitments, with float distributed to non-critical paths. The CPM schedule (`MS Project` / `P6` per `{{AGENCY}}` preference) accompanies this narrative.

## 2. Critical path

The critical-path activities, in sequence, are:

1. **Submittals + long-lead procurement** (Week 1–6)
2. `[USER TO FILL — Critical-path activity 2; e.g. "Selective demolition + abatement (if triggered)"]`
3. `[USER TO FILL — Critical-path activity 3; e.g. "Casework + door / frame / hardware fabrication"]`
4. `[USER TO FILL — Critical-path activity 4; e.g. "Rough MEP + in-wall inspection"]`
5. `[USER TO FILL — Critical-path activity 5; e.g. "Drywall close, paint, casework install"]`
6. `[USER TO FILL — Critical-path activity 6; e.g. "MEP trim + commissioning"]`
7. **Substantial Completion + owner punch + closeout** (final 2–4 weeks)

The most-likely critical-path squeeze is `{{LIKELY_CRITICAL_PATH_RISK}}` — `[e.g. casework lead time, lab-equipment OFOI hand-off, AHJ inspection scheduling]`. Mitigation discussed in §5.

## 3. Long-lead items + procurement timeline

Issued at NTP+1; tracked weekly:

| Item | Lead time (weeks) | Order by NTP+ | Need on site NTP+ |
|---|---|---|---|
| `{{LONG_LEAD_ITEM_1}}` | `{{LEAD_WEEKS_1}}` | `{{ORDER_BY_NTP_1}}` | `{{ON_SITE_NTP_1}}` |
| `{{LONG_LEAD_ITEM_2}}` | `{{LEAD_WEEKS_2}}` | `{{ORDER_BY_NTP_2}}` | `{{ON_SITE_NTP_2}}` |
| `{{LONG_LEAD_ITEM_3}}` | `{{LEAD_WEEKS_3}}` | `{{ORDER_BY_NTP_3}}` | `{{ON_SITE_NTP_3}}` |

**Typical long-lead items by project archetype:**

- **Office / lab renovation:** Casework (8–12 wk), HM doors / frames / hardware (6–10 wk), LED troffers (6–8 wk), VFD / VAV boxes (10–14 wk)
- **Dressing-room reno:** Lockers (8–14 wk), toilet partitions (4–8 wk)
- **Steel-building rehab:** OH doors + operators (6–10 wk), insulated steel man doors (6–10 wk), aluminum-clad windows (8–14 wk), metal panel + flashing replacement material (4–8 wk)

## 4. Phasing + trade sequencing

The work is sequenced to maintain `{{OCCUPANCY_CONSTRAINT}}` — `[e.g. "academic-calendar windows" / "active hospitality operations" / "minimum-disruption requirements per the SOW"]`.

**Phase 1 — Mobilization + protection** (`{{PHASE_1_DURATION}}` cal days from NTP)
Setup of dust-tight barricades, temp protection, lay-down, project signage, key-card access coordination.

**Phase 2 — Selective demolition** (`{{PHASE_2_DURATION}}` cal days)
Demo per drawings, abatement coordination (if triggered), haul-off. In-wall + as-built verification.

**Phase 3 — Rough MEP** (`{{PHASE_3_DURATION}}` cal days, parallel trades)
Plumbing rough, electrical rough, HVAC rough, fire-sprinkler mods. Concludes with in-wall + above-ceiling inspections.

**Phase 4 — Walls + ceilings + casework** (`{{PHASE_4_DURATION}}` cal days)
Drywall close, tape + texture + prime, casework install, ACT grid + tile, hard-lid GWB where called for.

**Phase 5 — Finishes** (`{{PHASE_5_DURATION}}` cal days)
Flooring, paint, tile (wet rooms), accessories.

**Phase 6 — MEP trim + commissioning** (`{{PHASE_6_DURATION}}` cal days)
Devices, fixtures, plumbing trim, sprinkler heads, HVAC air balance, electrical megger.

**Phase 7 — Punch + closeout** (`{{PHASE_7_DURATION}}` cal days)
Internal punch, owner punch, AHJ final, closeout deliverables (as-builts, O&M, warranties, training).

## 5. Schedule risks + mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Long-lead item delayed | Medium | High | Order at NTP+1; expedite-freight contingency; identify alternates pre-bid |
| Submittal rejection round-trip | Medium | Medium | BPC submittal review before transmittal; pre-coordinate spec interpretation with A/E |
| Hidden conditions on demo (concealed structural / MEP / hazmat) | Medium | High | Full investigative pre-demo walk with A/E + owner; immediate RFI on discovery; back-up demo scope if findings deeper |
| Concurrent owner / occupant disruption | High | Medium | Daily owner walk; weekly OAC; after-hours / weekend window if scope-critical |
| Adverse weather (outdoor scope) | Low–Medium | Low–High | Buffer days in CPM; covered staging |
| AHJ inspection scheduling lag | Medium | Medium | Schedule inspections 5+ working days in advance; back-up dates in CPM |
| Sub crew sickness / absenteeism | Low | Low | Sub commitment with crew-replacement clause; back-up sub identified for each critical trade |

## 6. Owner-side coordination dependencies

The schedule depends on the following owner-side commitments — any slippage drives equivalent BPC schedule slippage:

- `[USER TO FILL — Owner-supplied equipment delivery dates (OFOI), e.g. fume hoods, lab equipment, lockers if OFCI / OFOI ambiguous]`
- `[USER TO FILL — Owner-supplied access (keys, badges, escort)]`
- `[USER TO FILL — Owner-supplied utility shutdowns / energy releases]`
- `[USER TO FILL — Owner / A/E response time per RFI / submittal per spec]`
- `[USER TO FILL — Owner punch-list response time]`
- `[USER TO FILL — Owner-controlled inspection windows if AHJ is owner-internal (TAMU SSC, ASU FP&C, USACE QA office)]`

## 7. Schedule update + reporting

- CPM updated weekly; published every Monday by 5:00 PM
- 3-week look-ahead published with weekly CPM update
- Schedule narrative refreshed at each monthly progress meeting
- Schedule recovery plan (in writing) any time slippage exceeds 5 working days against baseline
