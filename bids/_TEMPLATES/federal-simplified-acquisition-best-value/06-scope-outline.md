# {{PROJECT_NAME}} — Scope Outline

> **Use:** Internal estimating-side scope outline that maps each line of the SOW to a CLIN, a sub trade, and a quantity. The companion to `01-scope.md` (which is the SOW-side view) and `05-bid-form-prep.md` (the CLIN-pricing side).
> **Scope template:** paste from [`firm/scope-templates/`](../../../firm/scope-templates/README.md) matching the project archetype.
> **SAP note:** the trade-by-trade rollup below feeds the technical-capability narrative in `09-proposal-draft.md` §2.4 — keep descriptions clear enough to lift directly.

## 1. Scope-template applied

Selected: `[USER TO FILL — office-tenant-refurb / dressing-room-renovation / arc-rehab-steel-building / other]` from [`firm/scope-templates/`](../../../firm/scope-templates/README.md).

## 2. SOW → CLIN → Sub mapping

| SOW reference | Description | CLIN | Sub trade | Quantity | Self / Sub | Notes |
|---|---|---|---|---|---|---|
| §C.{{REF}} | `{{DESCRIPTION}}` | 0001 | `{{TRADE}}` | `{{QTY}} {{UNIT}}` | `{{SELF_OR_SUB}}` | `{{NOTES}}` |
| §C.{{REF}} | `{{DESCRIPTION}}` | 0002 | `{{TRADE}}` | `{{QTY}} {{UNIT}}` | `{{SELF_OR_SUB}}` | `{{NOTES}}` |
| §C.{{REF}} | `{{DESCRIPTION}}` | Option 0001 | `{{TRADE}}` | `{{QTY}} {{UNIT}}` | `{{SELF_OR_SUB}}` | Priced option |
| §C.{{REF}} | `{{DESCRIPTION}}` | Option 0002 | `{{TRADE}}` | `{{QTY}} {{UNIT}}` | `{{SELF_OR_SUB}}` | Priced option |

## 3. Trade-by-trade rollup

| Trade | CLINs covered | BPC self / sub | Estimated direct cost | % of contract |
|---|---|---|---|---|
| Selective demo | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Envelope repair | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Doors / windows / OH doors | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Insulation + drywall + paint | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Flooring | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Electrical | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| HVAC | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Plumbing | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Fire sprinkler | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Specialty (lab / locker / accessories) | `{{CLINS}}` | `{{SELF_OR_SUB}}` | `${{COST}}` | `{{PCT}}%` |
| Mob / temp protection / punch / closeout | All | Self | `${{COST}}` | `{{PCT}}%` |
| **Direct cost subtotal** | | | `${{DIRECT_TOTAL}}` | 100% |

## 4. Self-perform verification (FAR 52.236-1)

| Self-perform scope | Direct cost | % of total direct |
|---|---|---|
| GC + supervision | `${{COST}}` | `{{PCT}}%` |
| Selective demo | `${{COST}}` | `{{PCT}}%` |
| Punch + final clean | `${{COST}}` | `{{PCT}}%` |
| Closeout | `${{COST}}` | `{{PCT}}%` |
| **Total self-perform** | `${{SELF_TOTAL}}` | **`{{SELF_PCT}}%`** (must be ≥ 15%) |
