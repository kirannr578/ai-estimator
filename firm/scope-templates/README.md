# `firm/scope-templates/` — reusable scope-of-work templates

Each scope template captures Blueprint Constructs' standard approach to a recurring project archetype: typical trade scope, takeoff items, default unit rates (pointing back to `config/cost_database.json`), typical sub trades, VE opportunities, and rough schedule durations.

When a new RFP lands, paste the matching scope template into the new workspace's `04-scope-of-work.md` (federal) or `04-scope-of-work.md` + `06-scope-outline.md` (state CSP), then refine against the project-specific SOW, drawings, and project manual.

## Index

| Template | Project archetype | Source bids mined | Typical duration | Typical contract value |
|---|---|---|---|---|
| [`office-tenant-refurb.md`](office-tenant-refurb.md) | Office / classroom / lab interior renovation; selective demo + new finishes + light MEP fit | [`bids/b1710-office-refurb-FA667526Q0002/`](../../bids/b1710-office-refurb-FA667526Q0002/) (B1710 USAF office refurbish), [`bids/tamu-harrington-2025-06813/`](../../bids/tamu-harrington-2025-06813/) (TAMU Harrington Lab 303), [`bids/tamu-wehner-finance-2025-06871/`](../../bids/tamu-wehner-finance-2025-06871/) (TAMU Wehner Finance Suite — in-flight; partial mining) | 6–16 weeks | $150K – $1.5M |
| [`dressing-room-renovation.md`](dressing-room-renovation.md) | Athletic dressing-room / locker-room renovation; lockers, durable finishes, ventilation, possible plumbing | [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/) (ASU Carr EFA dressing rooms) | 8–16 weeks | $300K – $800K |
| [`arc-rehab-steel-building.md`](arc-rehab-steel-building.md) | Existing steel-frame outbuilding rehab; envelope repair, door + window replacement, paint / coatings, light mechanical re-fit; common at USFWS / USACE / NPS sites | [`bids/usfws-san-marcos-140FC126R0017/`](../../bids/usfws-san-marcos-140FC126R0017/) (USFWS ARC Shop + 2-Stall Garage) | 8–16 weeks | $100K – $250K |

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
