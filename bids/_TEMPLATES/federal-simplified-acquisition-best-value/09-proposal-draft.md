# {{PROJECT_NAME}} — Quote Package Draft (SAP Best-Value)

> **Federal SAP best-value quote discipline:** the deliverable is a **single combined PDF "QUOTE PACKAGE"** — NOT a multi-volume proposal.
>
> - This is **not LPTA** — the technical-capability narrative is REQUIRED and is read comparatively.
> - This is **not full FAR Part 15 best-value** — there is no Volume I/II/III/IV split, no formal source-selection apparatus, no oral presentations, no FPR cycle.
> - The package has **4 substantive sections**: (1) Technical Capability narrative, (2) Key Personnel short-form, (3) Prior Experience references (3–5), (4) Price summary, plus front matter (cover note + signed SF-18/1449 + amendments + Reps & Certs incorporation + Buy American + surety letter as required).

## Package assembly order

```
{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - QUOTE PACKAGE.pdf
├── (Optional) Section L checklist — first page if RFQ provides one
├── Cover note — ½ to 1 page; "no exceptions" + package roadmap
├── Signed SF-18 (or SF-1449)
├── Signed SF-30 amendment acknowledgments ({{ADDENDA_LIST}})
├── SAM Reps & Certs incorporation page (FAR 52.204-8(d) or 52.212-3(b))
├── Buy American Certificate (FAR 52.225-4) — if RFQ triggers
├── PRICE — Schedule of Prices (every CLIN + every priced option)
├── PRICE — Surety commitment letter (post-award P&P or FAR 52.228-13 alt-payment)
├── TECHNICAL CAPABILITY — 5–15 pp narrative
├── KEY PERSONNEL — ½ page per named role
├── PRIOR EXPERIENCE — 3–5 references @ ½ page each
└── Contractor Core Data block — company name + UEI + CAGE + POC
```

## 1. Cover note (½ to 1 page)

```
{{SOLICITATION_NUMBER}}
{{PROJECT_NAME}}

QUOTE PACKAGE — SUBMITTED BY:
  Blue Print Constructs, LLC dba Blueprint Constructs
  UEI LM4YHVQ71QG7  •  CAGE 9LET0
  16283 Willowick Ln, Frisco, TX 75033
  (469) 213-1838  •  contactus@blueprintconstructs.com

Date submitted: {{SUBMISSION_DATE}}
Acceptance period: {{ACCEPTANCE_PERIOD_DAYS}} calendar days from quote receipt

Blueprint Constructs respectfully submits this Quote in response to
{{SOLICITATION_NUMBER}}, {{PROJECT_NAME}}, in accordance with the
Request for Quotation issued under FAR Part 13 (Simplified Acquisition
Procedures){{COMMERCIAL_ITEM_NOTE}}.

This Quote takes no exception to any term, condition, drawing,
specification, or amendment in {{SOLICITATION_NUMBER}}{{AMENDMENT_LIST_NOTE}}.

Package sections (single PDF):
  1. Signed SF-18 + amendment acknowledgments
  2. SAM Reps & Certs incorporation (FAR 52.204-8(d))
  3. Buy American Certificate (FAR 52.225-4) [if RFQ triggers]
  4. Price — Schedule of Prices + surety commitment letter
  5. Technical Capability narrative
  6. Key Personnel
  7. Prior Experience — {{PAST_PERF_COUNT}} reference projects
  8. Contractor Core Data

Respectfully,

[USER TO FILL — Signer Name + Title]
```

## 2. Section 1 — Technical Capability narrative (5–15 pp; REQUIRED)

> **SAP-specific discipline:** the technical narrative IS scored comparatively. Under-investing here is the #1 SAP loser pattern (see `07-risk-register.md` B12). At the same time, do NOT over-invest in FAR Part 15 4-volume structure — there is no Volume II, no SSA, no oral presentations.
> Target length: 5–15 pp (verify Section L cap). Use the skeleton below; paste from `firm/proposal-library/boilerplate/technical-approach-sap-skeleton.md` when authored.

### 2.1 Project understanding (1 pp)

`[USER TO FILL — 3–5 paragraphs demonstrating thorough understanding of the SOW, project location, agency context, and scope-of-work objectives. Quote the most-recent project name from the latest SF-30 amendment (not the original RFQ if it was renamed).]`

### 2.2 Proposed schedule (1 pp)

`[USER TO FILL — narrative summary of the proposed schedule, including: mobilization window after NTP, major milestone dates, critical-path activities, and substantial-completion target tied to NTP + {{POP_DAYS}} cal days. A Gantt thumbnail or milestone table is helpful but not required at SAP scale.]`

### 2.3 Phasing + site logistics (1–2 pp)

`[USER TO FILL — phasing approach if the work is multi-phase (e.g. CLIN 001 doors before CLIN 002 roof to minimize weather risk); site logistics specific to site access (4WD / boat / helicopter for backcountry; badging / escort for secure facilities; lay-down area + staging + dumpster + parking; coordination with site POC).]`

### 2.4 Trade-by-trade approach (3–8 pp)

`[USER TO FILL — paragraph or short section per major trade in the scope. Each entry covers: scope summary, key materials + sources, key sub or self-perform crew, sequencing dependencies, QC checkpoints. Lift directly from `01-scope.md` §3 trade-by-trade table — that table is structured to feed this section.]`

Trades to cover (refine per RFQ):

- `{{TRADE_1}}` — `[1–2 paragraph approach]`
- `{{TRADE_2}}` — `[1–2 paragraph approach]`
- `{{TRADE_3}}` — `[1–2 paragraph approach]`
- `[additional trades as scope requires]`

### 2.5 QC + safety summary (1 pp)

`[USER TO FILL — short summary of QC posture (BPC's QC program, owner/A/E coordination, in-progress inspections, closeout package), and safety posture (BPC's safety program, OSHA 10/30 supervision, site-specific hazards + mitigation). Reference post-award submittals (site-specific safety plan per FAR 52.236-13, QC plan per spec) without pasting them — those are post-award deliverables, not quote attachments.]`

## 3. Section 2 — Key Personnel (½ page per role)

> Pull short-form ½-page resumes from `firm/proposal-library/key-personnel/`. The long-form 1-page resumes in that folder are sized for FAR Part 15 — trim to ½ page for SAP packages.

### 3.1 Project Manager

| Field | Value |
|---|---|
| Name | `{{PM_NAME}}` |
| Title | Project Manager |
| Years of experience | `{{PM_YEARS}}` |
| Relevant credentials | `{{PM_CREDENTIALS}}` (e.g. OSHA 30, project-management cert, NAICS-relevant) |
| Recent relevant projects | `{{PM_PROJECT_1}}`; `{{PM_PROJECT_2}}`; `{{PM_PROJECT_3}}` |
| Role on this project | `[USER TO FILL — typical: day-to-day project execution, owner + A/E communication, sub coordination, schedule + cost management]` |

### 3.2 Superintendent

| Field | Value |
|---|---|
| Name | `{{SUPER_NAME}}` |
| Title | Superintendent |
| Years of experience | `{{SUPER_YEARS}}` |
| Relevant credentials | `{{SUPER_CREDENTIALS}}` (OSHA 30 mandatory; CPR/First Aid; trade-specific certs as relevant) |
| Recent relevant projects | `{{SUPER_PROJECT_1}}`; `{{SUPER_PROJECT_2}}`; `{{SUPER_PROJECT_3}}` |
| Role on this project | `[USER TO FILL — typical: on-site supervision, crew + sub direction, daily safety + QC, agency POC]` |

### 3.3 Quality Control (QC) Manager

| Field | Value |
|---|---|
| Name | `{{QC_NAME}}` |
| Title | QC Manager |
| Years of experience | `{{QC_YEARS}}` |
| Relevant credentials | `{{QC_CREDENTIALS}}` |
| Recent relevant projects | `{{QC_PROJECT_1}}`; `{{QC_PROJECT_2}}` |
| Role on this project | `[USER TO FILL — typical: QC plan implementation, three-phase inspection per spec, owner/A/E coordination on QC checkpoints, closeout discipline]` |

### 3.4 Principal in Charge (PIC) — add if RFQ asks

| Field | Value |
|---|---|
| Name | `{{PIC_NAME}}` |
| Title | Principal in Charge |
| Years of experience | `{{PIC_YEARS}}` |
| Role on this project | Executive oversight; binding authority; escalation point for any owner/A/E concern |

### 3.5 Safety Officer — add if RFQ asks

| Field | Value |
|---|---|
| Name | `{{SAFETY_NAME}}` |
| Title | Safety Officer |
| Years of experience | `{{SAFETY_YEARS}}` |
| Relevant credentials | `{{SAFETY_CREDENTIALS}}` (OSHA 30 mandatory; CHST / STSC / CSP if held) |
| Role on this project | Site-specific safety plan, weekly safety walks, incident reporting |

## 4. Section 3 — Prior Experience ({{PAST_PERF_COUNT}} references, ½ page each; REQUIRED)

> **Count:** Section L states the count — typically "minimum 3, maximum 5" on SAP. Submit at the maximum the RFQ allows. Submitting fewer than the minimum is non-responsive on the count check.
> **Picks:** pull from `firm/firm-profile.json → past_project_selection_rules.{{BID_KEY}}` (typ `{{PAST_PERF_PICK_LIST}}`). For each pick, lift the short-form ½-page block from `firm/proposal-library/past-performance/` (when authored) or trim the long-form entry.

### 4.1 Reference Project 1

| Field | Value |
|---|---|
| Project name | `{{PROJECT_1_NAME}}` |
| Owner | `{{PROJECT_1_OWNER}}` |
| Contract value | `${{PROJECT_1_VALUE}}` |
| Period of performance | `{{PROJECT_1_POP}}` |
| Completion status | `{{PROJECT_1_STATUS}}` (Complete / Substantial Completion / In Execution) |
| BPC role | `{{PROJECT_1_ROLE}}` |
| Owner-side reference | `{{PROJECT_1_REF_NAME}}` — `{{PROJECT_1_REF_EMAIL}}` — `{{PROJECT_1_REF_PHONE}}` |
| Scope summary | `{{PROJECT_1_SCOPE}}` |
| Relevance to this RFQ | `{{PROJECT_1_RELEVANCE}}` — 2 sentences linking the scope, magnitude, complexity, or agency-context overlap to the present RFQ |

### 4.2 Reference Project 2

Same fields, second pick.

### 4.3 Reference Project 3

Same fields, third pick.

### 4.4 Reference Project 4 — if RFQ asks for 4 or 5

Same fields.

### 4.5 Reference Project 5 — if RFQ asks for 5

Same fields.

## 5. Section 4 — Price summary

> The Schedule of Prices is in the Price section above (per `05-bid-form-prep.md`). This subsection is the price *summary* at the back of the package — a 1-page recap for the CO's evaluation table.

| Item | Amount |
|---|---|
| Base CLINs (0001 + 0002 + ...) | $`{{BASE_TOTAL}}` |
| Priced Option 0001 | $`{{OPTION_1_TOTAL}}` |
| Priced Option 0002 | $`{{OPTION_2_TOTAL}}` |
| **TOTAL EVALUATED PRICE** (base + all priced options) | **$`{{TOTAL_PRICE}}`** |

Acceptance period: `{{ACCEPTANCE_PERIOD_DAYS}}` calendar days from quote receipt.
Bonding posture: post-award P&P (or FAR 52.228-13 Alternative Payment Protections per Section I), due within 10 calendar days of award.

## 6. Contractor Core Data

```
Company name:        Blue Print Constructs, LLC dba Blueprint Constructs
UEI:                 LM4YHVQ71QG7
CAGE:                9LET0
EIN:                 87-4292998
Office address:      16283 Willowick Ln, Frisco, TX 75033
Office phone:        (469) 213-1838
Email:               contactus@blueprintconstructs.com
NAICS for this bid:  {{NAICS_CODE}}
Size assertion:      Small Business (per SAM record)
SAM expiration:      {{SAM_EXPIRATION_DATE}}
```

---

## Post-submission tracker

| Activity | Status | Date |
|---|---|---|
| Quote package final QC | ☐ | |
| `firm/_scripts/scan_placeholders.py` returns 0 hits in `bids/{{SLUG}}/` | ☐ | |
| Email transmittal drafted (subject exact per Section L) | ☐ | |
| Submitted via `{{SUBMISSION_PORTAL}}` to `{{SUBMISSION_EMAIL_1}}`{{SUBMISSION_EMAIL_2_NOTE}} | ☐ | |
| Submission timestamp recorded | ☐ | |
| Receipt confirmation from CO | ☐ | |
| Award notice monitoring (acceptance period: {{ACCEPTANCE_PERIOD_DAYS}} cal days) | ☐ | |
