# Firm-profile integration audit — `bids/`

This document is the **per-workspace coverage report** for the `firm/firm-profile.json` → `bids/<slug>/` substitution pass run on 2026-05-23.

The substitution script is `firm/_scripts/apply_firm_profile.py` and is **idempotent** — re-running it yields the same output. The script writes a structured report to `firm/_scripts/_apply_report.json` (gitignored under `_extracted` rules).

---

## 1. Per-workspace coverage

| Workspace | Files in scope | Files changed | Placeholders before | Placeholders after | Filled (L1+L2) | Past-perf fills (L3) | Net delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `angelo-state-carr-efa-26-007/` | 31 | 19 | 464 | 409 | 61 | 7 | -55 |
| `cmd-post-ndi-W50S7626QA001/` | 23 | 21 | 64 | 70 | 63 | 1 | +6 (see note) |
| `tamu-harrington-2025-06813/` | 30 | 13 | 422 | 397 | 40 | 4 | -25 |
| `usfws-san-marcos-140FC126R0017/` | 32 | 7 | 330 | 319 | 18 | 1 | -11 |
| **Totals** | **116** | **60** | **1,280** | **1,195** | **182** | **13** | **-85** |

> "Filled" counts the literal placeholder tokens our substitution rules removed and replaced with a real firm-profile value. The "Net delta" can be smaller than "Filled" (or even positive, as in `cmd-post-ndi`) because some Layer-3 past-performance blurbs **intentionally introduce** new annotated placeholders like `[USER TO FILL — Lavon Leisure 78 RV Park LLC owner POC]` to surface the specific data the user still needs to source. Those new annotations are higher-signal than the bare `[USER TO FILL]` they replace.

### Layer mapping

| Layer | What it substitutes | Examples |
|---|---|---|
| **L1** | Firm-identity tokens (legal name, DBA, address, UEI, CAGE, EIN, TX taxpayer ID, phone, email, website) — bulk exact-string + descriptor-regex matches, applied globally because the bracketed text uniquely names a firm-level value | `[USER TO FILL: firm legal name]`, `[USER TO FILL: UEI]`, `[Firm Name]`, `[FIRM LEGAL NAME]` |
| **L2** | Label-then-placeholder context patterns where the label disambiguates an otherwise-ambiguous bare placeholder | `Federal EIN: [USER TO FILL]`, `Taxpayer ID: [USER TO FILL]` |
| **L3** | Per-workspace past-performance fills — the 3 most-relevant past projects per `firm-profile.json → past_project_selection_rules.<workspace>` are inserted into known past-perf file shapes (TAMU/ASU pattern), and a recommended-picks banner is injected at the top of every past-performance file (including the USACE/federal templates whose body shape differs from the TAMU/ASU one) | `## A. Reference 1 — [USER TO FILL: project name]` → `## A. Reference 1 — Hindu Temple of Southlake` + full blurb |

---

## 2. Per-bid past-performance picks (from `firm-profile.json → past_project_selection_rules`)

The script auto-inserted these picks into each bid's past-performance file:

### `tamu-harrington-2025-06813/proposal/04-past-performance.md`
1. **Hindu Temple of Southlake** — institutional / nonprofit assembly-A-3 renovation, parallels TAMU's institutional-renovation profile
2. **Holiday Inn (Hall Park)** — commercial / hospitality renovation
3. **250–500+ single-family-home portfolio** — volume + GC-partner credibility

### `angelo-state-carr-efa-26-007/proposal/04-past-performance.md`
1. **Hindu Temple of Southlake** — institutional renovation
2. **Holiday Inn (Hall Park)** — commercial / hospitality
3. **250–500+ single-family-home portfolio** — volume

### `usfws-san-marcos-140FC126R0017/proposal/03-volume-III-past-performance.md`
1. **Lavon RV Park** — site work + MEP + electrical + plumbing + concrete + small-structure new-build, closest analog to the federal site/garage rehab
2. **Holiday Inn (Hall Park)** — commercial / occupied-building rehab
3. **Hindu Temple of Southlake** — institutional / nonprofit (proves general-construction depth)

### `cmd-post-ndi-W50S7626QA001/proposal/03-past-performance.md`
1. **Hindu Temple of Southlake** — institutional interior reno
2. **Holiday Inn (Hall Park)** — commercial / hospitality (closest analog to TXANG's command-post hospitality-grade finishes)
3. **Lavon RV Park** — MEP + electrical + plumbing breadth

For USACE/federal-shape past-perf files (cmd-post, usfws), the per-project blurbs ride in a banner at the top of the file. The user must manually copy the recommended-pick data into each Project N table cell below the banner; the federal-template shape differs enough from the TAMU/ASU shape that auto-fill of per-row cells would be lossy.

---

## 3. Top remaining placeholder categories (per-workspace audit)

After substitution, the placeholders still in each workspace fall into these buckets. **None of these can be filled from `firm-profile.json` because the data is not in any extracted BPC source file.**

| Category | Why we can't auto-fill | Count remaining (across all 4 workspaces) |
|---|---|---|
| **Personnel names + titles** (PM-of-record, Superintendent, Safety Lead, Estimator, Quality Manager, Signer, Bid-Prep Lead) | Rocky Nudurupati's bio is the only key-personnel bio in BPC source files. All other personnel slots need current names + credentials supplied by the user. | ~100 |
| **Personnel credentials** (OSHA 30 dates, PMP, CHST, CSP, LEED AP, etc.) | Requires individual certifications data per-person | ~60 |
| **Per-project owner contacts** (current name, current title, current phone, current email of past-project owner-side reference) | Even where the project itself is named in firm-profile (Hindu Temple, Holiday Inn, Lavon), the owner-side contact is not in BPC source files | ~50 |
| **EMR, TRIR, LTIR, OSHA citations** (3-year history) | Not in any extracted BPC file. Required by every TAMU CSP / federal solicitation with a safety questionnaire. | ~30 |
| **Annual revenue (FY-1, FY-2, FY-3) + cumulative contract value + total # of projects** | Not in any extracted BPC file. Required by every PQQ. | ~25 |
| **Bonding-agent identity** (surety name, agent name, agent phone, agent email, single-project capacity exact $, aggregate capacity exact $) | Bond Letter PDF on file is an image scan that the extraction script couldn't read. User has the letter; surface the values into `firm-profile.json → bonding` for the next bid cycle. | ~25 |
| **Insurance-broker identity + current renewed limits** | GL policy on file expired 2024-09-25; current renewed COI not in BPC folder. Workers Comp, Auto, Umbrella, Professional, Pollution carriers + limits not in any extracted file. | ~30 |
| **Bank reference** (bank name, branch, relationship manager, last reference-letter date) | Per the firm's own `BPC-Submission-Package/PLACEHOLDERS-TO-FILL.md` Section G, this is intentionally not surfaced into the corporate-profile file; bank account info is PII-class | ~15 |
| **Per-bid pricing fields** (final lump-sum, sub quotes, $/SF benchmarks for specific trades) | These are estimator output, not firm profile. Will be filled after takeoff + sub-quote receipt per each bid's own timeline. | ~150 |
| **Per-bid project-specific narrative** (executive-summary "why us" paragraph, technical-approach narrative, schedule narrative) | These are bid-specific writing tasks. Cannot be auto-filled from a firm profile; user writes per-bid. | ~50 |
| **TBD-from-spec items** | Genuinely TBD — pending CSP package access, drawings, sub quotes, owner clarification | ~20 |
| **Caller name / call-script speaker name in outreach files** | Per-call decision (who from the firm is calling); could default to Rocky for a small firm but the user should choose explicitly | ~10 |

---

## 4. Next user actions — only the user can supply these

Items below are the gap between what the firm has on file (per `firm-profile.json`) and what the active bid pipeline needs. They're ordered by **bid-pipeline urgency** — items earlier in the list block earlier bid submissions.

### Block 0 — Federal-bid prerequisites (blocks USFWS 6/22, USACE PAIS, TXANG 6/4)
- [x] ~~**SAM.gov current registration state** — verify at sam.gov; note current `Active` / `Inactive` status + last-renewal date into `firm-profile.json → sam_status`.~~ **Resolved 2026-05-23** — user confirmed SAM registration is Active. See `firm/firm-profile.json → sam_status`. The *expiration date* is still TBD — tracked separately below.
- [ ] **SAM.gov registration expiration date** — confirm with the user; SAM registrations expire annually and lapse causes immediate disqualification on any federal opportunity. Verify the next-expiration date at `https://sam.gov/` → Entity Management → Registration Status, and record it in `firm-profile.json → sam_status` (extend the schema with `sam_expiration_date` when surfaced).
- [ ] **SAM Reps & Certs (FAR 52.204-8)** — refresh within 11 months. If older, refresh **now** — updates take 3–10 business days to propagate. *(Not implied by the 2026-05-23 "active" confirmation; verify separately.)*
- [ ] **EFT (banking) info in SAM** is current per 52.232-33. *(Not implied by the 2026-05-23 "active" confirmation; verify separately.)*
- [ ] **TIN matches IRS records** — mismatch blocks IPP payment. *(Not implied by the 2026-05-23 "active" confirmation; verify separately.)*

### Block 1 — Cert / insurance renewals (blocks all 4 active bids)
- [ ] **TX HUB recertification** — VID 1874292998900, last cert expired 2024-08-31. Required for any TX state bid scoring HUB participation (TAMU, ASU).
- [ ] **DFW MSDC MBE recertification** — DL09279, last cert expired 2024-08-31. Annual cycle. MBE recognition cascades into HUB recognition under the DFW MSDC / TX Comptroller MOU.
- [ ] **DFW MSDC SBE recertification** — DL09279, expired 2024-08-31.
- [ ] **Current renewed COI** — surface the renewed Commercial GL policy + Workers Comp + Auto + Umbrella into `firm-profile.json → insurance`. Last GL on file expired 2024-09-25; nothing newer in BPC folder.
- [ ] **Insurance broker contact** — name, agency, phone, email into `firm-profile.json → insurance.insurance_broker`. Each bid's `outreach/0X-email-insurance-broker.md` assumes a broker exists.

### Block 2 — Bonding surety details (blocks all 4 active bids — every outreach/bonding-agent email and every proposal section that cites bonding)
- [ ] **Surety name + AM Best rating + Treasury Circular 570 listing** — into `firm-profile.json → bonding.surety` + `bonding.rating`.
- [ ] **Bonding agent contact** (name, agency, phone, email) — into `firm-profile.json → bonding.agent_*`.
- [ ] **Current single-project capacity ($)** + **aggregate capacity ($)** + **currently bonded backlog ($)** — into `firm-profile.json → bonding.single_project_capacity` / `aggregate_capacity`. Floor is empirically ≥ $1M per Lavon RV Park.
- [ ] **Bond letter date** — into `firm-profile.json → bonding.letter_date`.

### Block 3 — Key personnel + bios + résumés (blocks all 4 active bids' proposal/03-project-team.md files)
- [ ] **Project Manager of record** — name, years with firm, years in industry, credentials (PMP / CCM / OSHA 30 / LEED AP), 3-project portfolio with $ values and completion years.
- [ ] **Project Superintendent** — same shape; emphasize occupied-building experience for TAMU/ASU and DoD interior-renovation experience for cmd-post.
- [ ] **Safety Lead / Safety Manager** — name, OSHA 30 date, CHST/CSP credentials, firm EMR (3-year), firm OSHA citation history.
- [ ] **Estimator / Pre-Con Lead** — name, years in industry, phone, email.
- [ ] **Quality Manager** — name, phone, email, credentials.

### Block 4 — Reference contacts on existing past projects (blocks all 4 active bids' proposal/04-past-performance.md)
- [ ] **Lavon Leisure 78 RV Park LLC** owner POC — name, title, current email, current phone
- [ ] **North Texas Hindu Heritage Society** project POC — name, title, current email, current phone
- [ ] **Holiday Inn (Hall Park, Frisco)** property POC — name, title, current email, current phone
- [ ] **Named GC contact** at each of That 1 Painter / Touchmark / Bridge View Build / Hill Design Build — for the 250+ SFH portfolio reference

### Block 5 — Annual financials (blocks any TAMU CSP / federal SQS asking for revenue history; required for cmd-post past-perf "bonding capability proof")
- [ ] **Annual revenue FY-1, FY-2, FY-3** — into `firm-profile.json → annual_financials`.
- [ ] **Largest single contract completed** ($ + project name + year)
- [ ] **Cumulative contract value to date**
- [ ] **Total number of projects completed**

### Block 6 — Safety performance numbers (blocks every PQQ / TAMU CSP safety questionnaire / federal safety section)
- [ ] **EMR (current year + 2 prior years)** — request from workers-comp broker
- [ ] **TRIR + LTIR (current year)**
- [ ] **OSHA citations in last 3 years** (or "none")
- [ ] **OSHA 300 logs for last 3 years** (often required by Beck Group / large-GC pre-quals)
- [ ] **ISNetworld / Avetta / Veriforce member IDs** (or "not enrolled")

### Block 7 — Bank reference (blocks any large-GC pre-qual or PQQ asking for bank reference)
- [ ] Bank name, branch, relationship manager, phone, email
- [ ] Last bank reference letter date

### Block 8 — Address reconciliation (low-priority but affects every ACORD / SF 1442 / TX state form going out)
- [ ] Confirm current SOS-of-record address: BPC info.docx says `16283 Willowick Ln, Frisco, TX 75033`; Commercial GL policy says `16283 Willowick Ln, Little Elm, TX 75068-1210`. Same street; Frisco/Little Elm border. Pick one and update the GL policy + BPC info.docx (and `firm-profile.json`) to match.

### Block 9 — Website verification (low-priority)
- [ ] Confirm `https://www.blueprintconstructs.com` resolves. Profile has it as inferred-from-email-domain. If the live URL is different (e.g. no www, .net, etc.), update `firm-profile.json → website`.

### Block 10 — Documents missing entirely (block specific scoring elements but not the bid's responsiveness)
- [ ] **TX RCAT roofing license** — if held, supply number; if not, mark N/A on each bid's pre-qual section
- [ ] **EPA RRP Lead-Safe certification** — same
- [ ] **Municipal contractor licenses** (Frisco, Dallas, Plano, Little Elm, McKinney) — Rocky's bio mentions "preferred vendor" status with City of McKinney and City of Dallas; if specific GC license numbers exist, surface them
- [ ] **AR / billing email** for the firm — fill `[USER TO FILL]@blueprintconstructs.com` in `firm-profile.json → banking.ar_billing_email`

### Block 11 — Workspace gap
- [ ] **`bids/pais-cabin-140P6026Q0029/`** — the task brief lists this as an active workspace but it doesn't exist in the repo. Solicitation PDFs (`Sol_140P6026Q0029.pdf` + Amd 0001) are present under `inbox/opportunities/attachments/2026-05-21/`. Create the workspace from the existing scaffolds (mirror `bids/usfws-san-marcos-140FC126R0017/` structure since both are NPS Region small-construction) when ready to pursue. Default picks per `firm-profile.json → past_project_selection_rules.pais-cabin-140P6026Q0029` are Lavon RV Park, Hindu Temple of Southlake, Holiday Inn Hall Park.

---

## 5. Substitution coverage detail — files changed by workspace

This section enumerates every file the substitution script touched, so a reviewer can spot-check the result.

### angelo-state-carr-efa-26-007 (19 files changed)

`02-bid-prep-checklist.md`, `04-scope-of-work.md`, `05-hsp-plan.md`, `contacts.md`, `outreach/01-email-hannah-bignall-eligibility.md`, `outreach/01-email-samuel-guevara-eligibility.md`, `outreach/02-email-samuel-guevara-owner-furnished.md`, `outreach/03-email-bonding-agent.md`, `outreach/05-email-hub-subs-template.md`, `outreach/06-email-asu-procurement-clarifications.md`, `proposal/00-readme.md`, `proposal/01-executive-summary.md`, `proposal/03-project-team.md`, `proposal/04-past-performance.md`, `proposal/07-safety-plan.md`, `proposal/08-attachment-A-fill-guide.md`, `proposal/09-attachment-D-hsp-form-guide.md`, `proposal/10-price-proposal.md`, `proposal/12-bid-bond-letter-template.md`

### cmd-post-ndi-W50S7626QA001 (21 files changed)

Every `proposal/*.md` (12 files) + key outreach files (`02-email-136-aw-facility-poc.md`, `03-email-bonding-agent.md`, `04-…`, `05-…`, `06-…`) + `02-bid-prep-checklist.md`, `README.md`, `timeline.md`, `contacts.md`. The cmd-post workspace has the most filename-template substitutions (`[Firm Name + UEI]` in email subject lines) and the most generic-template per-file headers.

### tamu-harrington-2025-06813 (13 files changed)

`02-bid-prep-checklist.md`, `contacts.md`, `outreach/01-…eligibility.md`, `outreach/03-…drawings.md`, `outreach/05-email-bonding-agent.md`, `outreach/06-email-insurance-broker.md`, `outreach/07-call-script-joelle-shidemantle.md`, `proposal/01-executive-summary.md`, `proposal/03-project-team.md`, `proposal/04-past-performance.md`, `proposal/08-csp-proposal-form-fill-guide.md`, `proposal/09-hsp-form-fill-guide.md`, `proposal/12-bid-bond-letter-template.md`

### usfws-san-marcos-140FC126R0017 (7 files changed)

`02-bid-prep-checklist.md` (UEI + CAGE filled), `contacts.md`, `outreach/01-email-tracy-gamble-rfi-consolidated.md`, `outreach/04-email-bonding-agent.md`, `proposal/02-volume-II-technical-acceptability.md`, `proposal/03-volume-III-past-performance.md` (past-perf banner injected), `proposal/04-SF-1442-fill-guide.md`

The USFWS workspace has the lowest L1 count because its `.md` files use slightly different placeholder phrasings (e.g. `[USER TO FILL: 12-character SAM UEI]` rather than `[USER TO FILL: UEI]`) — these are caught by the BULK_REGEX layer but with fewer hits per file than the TAMU shape.

---

## 6. How to re-run

```powershell
# Reset bids/ to last commit (safe — substitution is idempotent, but a clean
# slate makes diffs easier to read)
git checkout -- bids/

# Re-apply firm-profile substitutions
.\.venv\Scripts\python.exe firm\_scripts\apply_firm_profile.py

# Audit remaining placeholders
.\.venv\Scripts\python.exe firm\_scripts\scan_placeholders.py | Out-File -Encoding utf8 firm\_scripts\_placeholders_report.json
```

If you've edited `firm/firm-profile.json` between runs (e.g. surfacing the renewed COI, the bond surety details, or a new past project), commit the JSON edit first, then re-run the apply pass and commit the bid diffs separately. Reviewers can then see "what firm-profile data changed" and "what bid-file substitutions resulted" as two distinct diffs.

---

## 7. PII landmines we deliberately avoided

The substitution script and the firm profile both honor the workspace security policy (`always_applied_workspace_rule.04-data-classification`):

- **No row data** from `Records/Blue Print Constructs Payments, Contacts, To do List.xlsx` (PII-class).
- **No row data** from `BPC/Contacts.xlsx` (PII-class third-party contact list).
- **No customer names** from `1509 Astoria Dr/` and `2056 Zander Dr/` past-project folders (homeowner PII). The two homeowner past projects appear in `firm-profile.json → past_projects` with `owner_type: homeowner_redacted` and `reference_contact: [redacted — homeowner]`; their source PDFs are noted as `[Source file omitted for privacy — contains PII]`.
- **No bank account / routing numbers** — even though one is visible in `BPC/BPC info.docx`. The bank reference section in `firm-profile.json → banking` is intentionally empty.
- **No portal passwords** — even though several (TX SOS, DFW MSDC, procurement portals) are visible in `BPC/BPC info.docx` and `BPC/RK Residential Homes and Commercial Constructions LLC.pdf`.
- **No personal cell number** — even though it's in `BPC/BPC info.docx`. Per the firm's own `BPC-Submission-Package/PLACEHOLDERS-TO-FILL.md` Section G policy, personal cell numbers are not in bid submissions.
- **No other-entity data** — Maxiple Group LLC, RK Creative Workz LLC, Buds n Petals LLC EINs (visible in `BPC/BPC info.docx`) are not surfaced. They are not Blue Print Constructs.
- **Records/* xlsx files** were inventoried by sheet name + header only — no row iteration. The script that does this is `firm/_scripts/extract_sources.py`; see its `xlsx_summary(..., body_redacted=True)` mode.

If you spot any PII in a file the substitution script created or modified, treat as a process incident and remove it before pushing. The `firm/firm-profile.json` is the propagation root — fix the JSON first, then re-run the apply script.

---

## 8. Change log

- **2026-05-23** — SAM.gov status set to active (user-confirmed). Expiration date still TBD.
- **2026-05-23** — Added `core/proposal_renderer/` (PDF + pitch-deck PPTX builder) and rendered the first set of artifacts under `bids/<slug>/proposal/exports/` for all 4 active workspaces (TAMU, Angelo State, USFWS, TXANG Cmd Post). The 8 deliverables are committed once so they ship with the feature; a follow-up commit adds `bids/*/proposal/exports/` to `.gitignore` so future renders don't churn the diff. To regenerate from source: `python scripts/render_proposals.py --all --format both`.
