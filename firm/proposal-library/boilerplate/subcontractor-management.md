# Boilerplate — Subcontractor Management

> **Use:** Sub Plan section + HSP narrative in TX state CSP; sub management approach narrative for federal-LPTA submittals. On LPTA, do not include in proposal unless explicitly requested.

---

# Subcontractor Management Plan — {{PROJECT_NAME}}

## 1. Sub procurement philosophy

Blue Print Constructs uses a **vetted, repeat-business** sub pool. Subs on `{{PROJECT_NAME}}` are selected against four criteria, in order:

1. **Capability + capacity** for the specific scope at the specific site
2. **Past-performance record with BPC** (or, for new subs, equivalent verifiable record)
3. **Compliance** — TX HUB cert if claimed for HSP credit; insurance + bonding meeting `{{AGENCY}}` / TX UGC requirements; license currency; OSHA training; W-9; non-debarment (SAM exclusion check for federal)
4. **Competitive price** — minimum **3 quotes per scope item** unless single-source justified in writing

## 2. Sub vetting checklist (per sub, before contract)

- [ ] W-9 current
- [ ] COI naming BPC as Additional Insured + meeting `{{AGENCY}}` flow-down limits
- [ ] OSHA 10 (craft) + OSHA 30 (foreman) cards
- [ ] Trade license current (TX plumbing, electrical, HVAC, fire-sprinkler, etc. as applicable)
- [ ] EPA RRP cert if pre-1978 construction touched
- [ ] EMR + OSHA 300 prior 3 years
- [ ] Past performance — 3 references for similar scope
- [ ] HUB cert (TX HUB VID + expiration) if claiming HSP credit
- [ ] SAM.gov exclusion check (federal projects)
- [ ] Subcontract executed with BPC standard flow-down terms

## 3. Subcontract terms — BPC standard flow-down

- Flow-down of `{{AGENCY}}` insurance + bonding requirements per TX UGC Article 5 / `{{AGENCY}}` SGC
- Flow-down of `{{AGENCY}}` safety requirements + AHA participation
- Flow-down of QC requirements (Preparatory + Initial + Follow-up participation per [`firm/proposal-library/boilerplate/qa-qc-plan-one-pager.md`](qa-qc-plan-one-pager.md))
- Pay-when-paid (pay-app cycle aligns with BPC's prime pay cycle to `{{AGENCY}}`)
- Lien waivers conditional + unconditional with each pay request
- Buy American flow-down (federal projects)
- Davis-Bacon + certified-payroll flow-down (federal projects)
- TX prevailing-wage flow-down (TX state-funded projects per Tex. Gov't Code Ch. 2258)
- HSP commitment flow-down (TX state CSPs) — HSP sub commits to scope + $ value as listed in BPC's HSP
- Schedule + look-ahead participation (weekly sub-foreman meeting)

## 4. HUB Subcontracting Plan (HSP) — sub-side mechanics

> Full HSP playbook in [`firm/playbooks/texas-state-csp-hsp.md → §6`](../../playbooks/texas-state-csp-hsp.md).

For this project, BPC's HSP commitment is **{{HUB_COMMIT_PCT}}%** of subcontracted Work — exceeds the statewide **{{APPLICABLE_HUB_GOAL_LABEL}}** goal of **{{STATEWIDE_HUB_GOAL_PCT}}%** per 34 TAC §20.284.

Per-trade HSP allocation (template; refine per project):

| Trade | % of contract | Plan | Target HUB share |
|---|---|---|---|
| Demolition | `{{DEMO_PCT}}%` | Sub | 100% |
| Drywall + framing | `{{DRYWALL_PCT}}%` | Sub | 50% |
| Casework / millwork | `{{CASEWORK_PCT}}%` | Sub | 25% |
| Doors / frames / hardware | `{{DOORS_PCT}}%` | Material-only or sub | per-sub |
| Flooring | `{{FLOORING_PCT}}%` | Sub | 50% |
| Paint | `{{PAINT_PCT}}%` | Sub | 100% |
| Ceilings | `{{CEILING_PCT}}%` | Sub | 50% |
| Electrical | `{{ELEC_PCT}}%` | Sub | 50% |
| HVAC | `{{HVAC_PCT}}%` | Sub | 25% |
| Plumbing | `{{PLUMB_PCT}}%` | Sub | 50% |
| Fire sprinkler | `{{SPRINK_PCT}}%` | Sub | 25% |
| Self-perform (GC + supervision + selective demo) | `{{SELF_PCT}}%` | Self | n/a (excluded from HUB denominator) |

HSP outreach methodology, GFE documentation, and post-award PAR reporting per the playbook.

## 5. Sub management cadence (during execution)

- **Weekly sub-foreman coordination meeting** (day before OAC) — all active sub foremen + BPC PM + Super
- **Daily 7:00 AM tailgate / safety brief** — sub crews + BPC Super
- **Per-scope-item Preparatory Phase Inspection** — sub foreman + crew + BPC QC + BPC Super (per QC plan)
- **Daily** sub crew check-in + daily report contribution
- **Monthly** sub performance review — quality, safety, schedule, pay-app + lien-waiver currency

## 6. Sub performance management

Sub performance tracked monthly against:

- Schedule adherence vs sub-specific milestones
- Quality (NCR count, rework hours)
- Safety (near-miss, recordable, OSHA inspection)
- Coordination (RFI responsiveness, look-ahead participation)
- Pay-app accuracy + lien-waiver currency

**Probation / replacement:** any sub on probation for cause (quality / safety / schedule) gets written notice + 5-working-day cure period. Failure to cure → BPC right to terminate the sub (subject to the executed sub agreement) and bring in the back-up sub identified during procurement.

## 7. Post-award sub reporting

| Report | Cadence | Audience |
|---|---|---|
| HSP Progress Assessment Report (PAR) — TX state CSPs | Monthly with pay app | `{{AGENCY}}` HUB Office |
| Certified payroll (WH-347) for each sub tier — federal | Weekly | DOL via WHD |
| TX prevailing-wage compliance statement — TX state | Per `{{AGENCY}}` requirement | `{{AGENCY}}` |
| OSHA 300/300A for each sub | Annually + on request | `{{AGENCY}}` EHS |
