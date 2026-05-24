# Davis-Bacon Act compliance — WD TX20260270 acknowledgment

This is a **construction contract** (not a service contract), so **Davis-Bacon Act (DBA) applies, not the Service Contract Act (SCA)**. The Wage Determination is **TX20260270, dated 01/02/2026, Tarrant County, Building Construction**, embedded in the solicitation Section J.

## A. DBA applicability

| Attribute | Value |
|---|---|
| Statute | 40 USC §3141 et seq. (Davis-Bacon Act of 1931, as amended) |
| FAR clauses | 52.222-6 (rate requirements), 52.222-7 (withholding), 52.222-8 (payrolls/records), 52.222-9 (apprentices), 52.222-10 (Copeland Act), 52.222-11 (subcontracts), 52.222-12 (debarment), 52.222-13 (compliance), 52.222-14 (disputes), 52.222-15 (eligibility) |
| Wage Determination | TX20260270 (Mod 0, dated 01/02/2026; supersedes TX20250270) |
| Construction Type | Building Construction |
| County | Tarrant County, Texas |
| Effective period | From the date the contract is awarded, through completion of work |

## B. Acknowledgment language (for the offer)

Include a 1-paragraph acknowledgment in the offer (or the Schedule of Prices notes section) so the CO sees DBA literacy explicitly:

```
Davis-Bacon Wage Determination Acknowledgment:

Blue Print Constructs acknowledges that this contract is subject to the Davis-Bacon
Act and that Wage Determination TX20260270 (Modification 0, dated
01/02/2026, Tarrant County, Building Construction) applies to all on-site
trade labor under this contract. Blue Print Constructs commits to:

  1. Paying all classifications of laborers and mechanics at not less than
     the wage rates and fringe benefits listed in WD TX20260270.
  2. Posting WD TX20260270 at the jobsite in a conspicuous location
     accessible to laborers and mechanics.
  3. Submitting weekly certified payroll on Form WH-347 for both
     Blue Print Constructs and each subcontractor performing work on the contract.
  4. Maintaining payroll records for 3 years from contract completion.
  5. Flowing down DBA requirements via FAR 52.222-11 to each subcontractor
     of any tier.
  6. Requesting wage classification conformance via SF 1444 from the
     Contracting Officer if any trade classification not on WD TX20260270
     is required.
  7. Complying with the Copeland Anti-Kickback Act (FAR 52.222-10) — no
     kickbacks from contractor or subcontractor personnel.
  8. Complying with apprentice/trainee ratio requirements (FAR 52.222-9)
     — registered apprenticeship programs only.

In addition, Blue Print Constructs acknowledges and complies with all related
labor-standards FAR clauses cited in Section I of this solicitation.
```

## C. Trades expected on this project (from `04-scope-of-work.md`)

The following trade classifications from WD TX20260270 are expected on the project:

| Trade | WD listed | Notes |
|---|---|---|
| Carpenter | Yes (likely under CARP-class entries) | Framing, GWB, casework, doors |
| Drywaller / Taper | (Falls under Carpenter or has separate DRYW-class) | GWB hang/finish |
| Electrician | Yes (under ELEC-class) | UFC 3-501-01 work; sub work |
| Plumber | Yes (under PLUM-class) | Sink relocation; sprinkler-pipe coordination |
| Sheetmetal Worker | Yes (under SHEE-class) | HVAC duct mod |
| Pipefitter | Yes (under PIPE-class) | Sprinkler-piping mod |
| Painter | Yes (under PAIN-class) | Walls + doors + trim |
| Sprinkler Fitter | Yes (under SPRI-class) | Fire-suppression mod |
| Glazier | Yes (under GLAZ-class) | Credential window install |
| Laborer | Yes (multiple groups) | Demo, debris, FOD-cleanup |
| Truck Driver | Yes | Material delivery |
| Operating Engineer | Yes (under ENGI-class) | Forklift operations |
| (If insulation work needed) Asbestos Worker / Heat & Frost Insulator | Yes — listed at $33.23 + $7.52 fringe | Less likely for this project |
| (If lift work) Elevator Mechanic | Yes — listed at $51.93 + $38.435+a+b fringe | Not applicable to this project |

> ⚠️ **Re-pull the full WD from SAM.gov** for the latest rates — the version embedded in the solicitation Section J is the contract-binding version, but the full WD has 30+ trade entries that the text extractor in our pipeline did not fully capture. See `prevailing-wages.md` for the full mechanics.

## D. Conformance for missing trades

If any trade classification needed for this project is **not on WD TX20260270**, the contractor must request conformance via **SF 1444** (Conformance of Wage Rates) submitted to the CO. The CO forwards to DOL Wage and Hour Division for ruling. Conformance typically takes 2–6 weeks; conformed rate is binding from the conformance date.

For this project, the standard trades listed above should cover the entire scope. The mantrap electronic-lock kit installation is performed by Electricians + Door/Hardware specialists (no separate WD class required). The credential window glazing is performed by a Glazier (standard WD class).

## E. WH-347 weekly certified payroll mechanics

| Element | Detail |
|---|---|
| Form | WH-347 (DOL Form 1215-0149) — available at `https://www.dol.gov/agencies/whd/forms` |
| Frequency | **Weekly** for prime + each subcontractor performing on-site work |
| Submission | To the CO (or to the local DOL Wage and Hour office, if directed) |
| Statement of Compliance | WH-348 (page 2 of WH-347 form) — signed by employer or authorized representative |
| Retention | 3 years from contract completion |
| Apprentices/Trainees | Must be in registered programs; apprentice-to-journeyman ratio per FAR 52.222-9 |

## F. Reach-back to subs (FAR 52.222-11)

Every sub-tier subcontract that includes laborers or mechanics on-site must:
- Include the FAR 52.222-6 wage-rate flow-down clause
- Include the WD TX20260270 by reference (or attached)
- Include the WH-347 weekly certified payroll requirement
- Include the FAR 52.222-9 apprentice-program requirement

The prime collects WH-347 from each sub weekly and submits to the CO.

## G. Common DBA execution errors

| Error | Consequence | Mitigation |
|---|---|---|
| Wrong wage code (e.g., paying carpenter rate to a painter) | CO funds withholding; DOL investigation possible | Train PM + sub PMs on WD trade classifications |
| Apprentice-to-journeyman ratio exceeded | DOL violation finding | Track ratio per trade per pay period |
| Fringe benefit improperly handled (rolled into base rate without disclosure) | DOL violation finding | Disclose fringe separately on WH-347 |
| Late or missing WH-347 | CO funds withholding | Make payroll cycle Friday → submit Monday |
| Sub fails to submit WH-347 | Prime is responsible — sub progress payment held | Make WH-347 submission a sub-contract condition for progress payment |
| Compensation deductions not authorized by Copeland Act | DOL violation; criminal liability possible | Only authorized deductions (taxes, court orders, pre-authorized deductions) |
| Failure to post WD at jobsite | DOL violation finding | Post WD on Day 1; in conspicuous location accessible to laborers |
| Use of un-conformed trade classification | Risk of debarment | Use SF 1444 for any unique classification; do not improvise |

## H. Service Contract Act — does NOT apply

The SCA (41 USC §6701 et seq.; FAR 52.222-41 et seq.) applies to **service contracts**, not construction. This contract is a construction renovation under FAR Part 36; SCA does not apply. The WD attached is a Davis-Bacon construction WD, not an SCA service WD.

> If a future modification adds a service component (e.g., post-renovation maintenance), SCA applicability would need to be re-evaluated.

## I. Submission

The DBA acknowledgment is **NOT a separate document** — it can be:
- Included as a paragraph in the Schedule of Prices notes (preferred), OR
- Included as a standalone 1-page acknowledgment document attached to the offer (also acceptable)

Filename if standalone: `W50S7626QA001_DBA_Acknowledgment_Blue Print Constructs.pdf`

## J. Where to access the full WD

- **SAM.gov Wage Determinations** at `https://sam.gov/wage-determinations` (search TX20260270)
- **DOL WHD** at `https://www.dol.gov/agencies/whd/`
- **Embedded in this solicitation Section J** (governing version unless superseded)
