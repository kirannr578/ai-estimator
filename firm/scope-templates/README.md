# `firm/scope-templates/` — reusable scope-of-work templates

Each scope template captures Blueprint Constructs' standard approach to a recurring project archetype: typical trade scope, takeoff items, default unit rates (pointing back to `config/cost_database.json`), typical sub trades, VE opportunities, and rough schedule durations.

When a new RFP lands, paste the matching scope template into the new workspace's `04-scope-of-work.md` (federal) or `04-scope-of-work.md` + `06-scope-outline.md` (state CSP), then refine against the project-specific SOW, drawings, and project manual.

## Index

| Template | Project archetype | Source bids mined | Typical duration | Typical contract value |
|---|---|---|---|---|
| [`office-tenant-refurb.md`](office-tenant-refurb.md) | Office / classroom / lab interior renovation; selective demo + new finishes + light MEP fit | [`bids/b1710-office-refurb-FA667526Q0002/`](../../bids/b1710-office-refurb-FA667526Q0002/) (B1710 USAF office refurbish), [`bids/tamu-harrington-2025-06813/`](../../bids/tamu-harrington-2025-06813/) (TAMU Harrington Lab 303), [`bids/tamu-wehner-finance-2025-06871/`](../../bids/tamu-wehner-finance-2025-06871/) (TAMU Wehner Finance Suite — in-flight; partial mining) | 6–16 weeks | $150K – $1.5M |
| [`dressing-room-renovation.md`](dressing-room-renovation.md) | Athletic dressing-room / locker-room renovation; lockers, durable finishes, ventilation, possible plumbing | [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/) (ASU Carr EFA dressing rooms) | 8–16 weeks | $300K – $800K |
| [`arc-rehab-steel-building.md`](arc-rehab-steel-building.md) | Existing steel-frame outbuilding rehab; envelope repair, door + window replacement, paint / coatings, light mechanical re-fit; common at USFWS / USACE / NPS sites | [`bids/usfws-san-marcos-140FC126R0017/`](../../bids/usfws-san-marcos-140FC126R0017/) (USFWS ARC Shop + 2-Stall Garage) | 8–16 weeks | $100K – $250K |
| [`food-service-cafeteria.md`](food-service-cafeteria.md) | Commercial kitchen + serving-line renovation; demo + NSF stainless equipment + hood + Ansul fire-suppression + grease-waste + 208V/3-ph; ISD / university dining-hall scope | Cleburne ISD CHS Cafeteria Serving Line Renovation (RFCSP 2026-0608-01) — *workspace not yet created; template authored from source RFCSP for forward use* | 6–18 weeks | $250K – $1.2M |
| [`restroom-renovation-historic.md`](restroom-renovation-historic.md) | Period-appropriate restroom rebuild in NRHP-listed / NPS-managed structure; ADA-within-historic; SHPO / Section 106 review cycle dominates schedule | [`bids/_WATCHLIST/saan-san-juan-restrooms-140P1226Q0025.md`](../../bids/_WATCHLIST/saan-san-juan-restrooms-140P1226Q0025.md) (SAAN San Juan restrooms) + general NPS / NRHP precedent | 10–18 weeks | $150K – $600K |
| [`roof-repair-historic.md`](roof-repair-historic.md) | Historic roof tear-off + in-kind replacement (standing-seam metal, slate, cedar shake, asphalt 3-tab) per NPS Preservation Brief 4; flashing + ventilation + lightning protection | PAIS Backcountry Cabin (140P6026Q0029 anticipated) + NPS Preservation Brief 4 reference baseline | 8–14 weeks | $80K – $400K (single building); $300K – $1.5M (multi-building campus) |
| [`commercial-tpo-reroof.md`](commercial-tpo-reroof.md) | Commercial low-slope re-roof — single-ply TPO / EPDM / PVC over polyiso + HD cover board; mechanically-attached, fully-adhered, or ballasted; tear-off or recover; full perimeter sheet-metal (edge metal, coping, scuppers, drains) + RTU disconnect/reconnect | [`bids/tmd-camp-maxey-roof-2026-0626/`](../../bids/tmd-camp-maxey-roof-2026-0626/) (TMD Camp Maxey Bldg. 1 dual-roof 60-mil TPO; Buy-American + Davis-Bacon overlay) | 3–12 weeks | $80K – $1.2M (single building); $500K – $3M (multi-building campus) |
| [`security-fence-perimeter.md`](security-fence-perimeter.md) | Perimeter security fencing — chain-link → ornamental → anti-climb 358 mesh; gates (swing, cantilever slide, pedestrian); electronic access control + perimeter lighting | [`bids/_NO_GO/2026-05-22-mcfaddin-nwr-fence-140FC126Q0015.md`](../../bids/_NO_GO/2026-05-22-mcfaddin-nwr-fence-140FC126Q0015.md) (McFaddin NWR boundary fence) + federal-site-security baseline | 2–18 weeks (heavily scope-dependent) | $50K – $2M |
| [`gym-renovation-multisystem.md`](gym-renovation-multisystem.md) | Multi-system gymnasium renovation — sport flooring + HVAC RTU swap + LED high-bay lighting + paint + ADA + (optional) bleachers + scoreboard + AV; ISD bond-program or university PE-facility refresh | [`bids/leroy-moore-gym-PV-0749-PV-0753/`](../../bids/leroy-moore-gym-PV-0749-PV-0753/) (PVAMU Leroy Moore Gym — court-conversion sub-scope; bleacher / scoreboard rows generalized) | 10–20 weeks | $400K – $3M |
| [`cosmetology-classroom-reno.md`](cosmetology-classroom-reno.md) | Cosmetology / barber / esthetician / nail-tech classroom or lab renovation in a community college, trade school, or CTE high school; shampoo bowls + plam stations + mirror walls + chemical-resistant fluid-applied flooring + 200A+ panel upgrade + GFCI density + source-capture exhaust; state-board (TDLR in Texas) inspection gating + TAS / ADA discipline | [`bids/mcc-cosmetology-phase4-2026-0622/`](../../bids/mcc-cosmetology-phase4-2026-0622/) (McLennan CC CSC Module B Cosmetology Phase 4) | 10–28 weeks | $300K – $2M |

## How to use

1. Pick the template that matches the project archetype.
2. Paste into the new workspace's scope-of-work file.
3. Walk the SOW + drawings + spec book and **delete** every line that doesn't apply.
4. **Refine** quantities against takeoff (use `core/extraction/drawing_prepass.py` output as a first pass).
5. Cross-reference unit rates to `config/cost_database.json` and the firm's last-3-projects actuals.
6. Map each scope item to a CLIN (federal) or pricing-form row (state CSP).
7. Issue per-trade sub solicitations.

## Cost-database cross-reference

Default unit rates referenced in the templates point to `config/cost_database.json`. CSI Division indexing per `config/csi_divisions.json`. When the cost-database value disagrees with a recent actual, prefer the actual and update the cost-database in a separate PR.

## Placeholder convention

Same convention as the playbooks: `{{UPPER_SNAKE}}` for project-specific facts; `[USER TO FILL]` for firm-internal data; `[TEMPLATE]` for skeleton sections not yet refined by a shipped bid.
