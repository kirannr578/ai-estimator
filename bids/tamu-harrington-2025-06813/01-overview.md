# 01 — Project overview

> Sources: (1) `inbox/opportunities/attachments/2026-05-21/ESBD_514190_1778277018836_2025-06813_Notice of Project-CS_26.05.08.pdf` — the only public document we have; (2) `exports/calibration_v3/estimate.json` — `bid_packages[0]` (LLM extraction of the same Notice); (3) inference from sister TAMU-System / Texas higher-ed CSP solicitations (Angelo State / TTU System pattern documents in the same inbox).

---

## 1. Solicitation identity

| Field | Value |
|---|---|
| Solicitation / project number | **2025-06813** |
| Project name | **Harrington Education Center Lab 303 Renovation** |
| Issuing entity | **SSC Services for Education** (posted on behalf of **Texas A&M University, Part 02**) |
| Procurement vehicle | **Competitive Sealed Proposal (CSP)** — TAMU System procurement under Tex. Gov't Code Ch. 2269 / Tex. Educ. Code Ch. 51 |
| NAICS (inferred — not stated on the Notice) | 236220 — Commercial & Institutional Building Construction |
| Set-aside | Open competition; **HUB Subcontracting Plan required** |
| Federal funding? | Not indicated on the Notice; treat as state-funded TAMU System work until the CSP package confirms otherwise |

> ⚠️ The user's task brief asserted NAICS 236220 and "open competition." Those values are **not literally printed on the Notice of Project**. NAICS is an inference from the scope; "open competition" follows from no listed set-aside on the Notice. Confirm both when the CSP package arrives.

## 2. Location

- **Project site:** Harrington Education Center Office Tower, Bldg 0435, College Station, TX (TAMU main campus)
- **Submission delivery address:**
  - Mailing: 1371 TAMU, College Station, TX 77843
  - Physical / hand-delivery: SSC Service Solutions, Facilities Services EDCS, 600 Agronomy Road, Suite 218, College Station, TX 77843
- **Public-opening room:** SSC Facilities Services, Conf. Rm 204 (in-person) — Teams link also published in the Notice

## 3. Key dates

| Event | Date / Time | Status as of today (2026-05-22) |
|---|---|---|
| Notice of Project issued | 2026-05-08 | Issued |
| Pre-proposal meeting | 2026-05-14, 2:00 PM CT — SSC Facilities Services, Conf Rm S118 | **MISSED — already past.** Request sign-in sheet, recording, and Q&A from Joelle. Confirm we are still eligible to propose (non-mandatory pre-proposal meetings on TAMU CSPs are typical, but a few are mandatory — verify). |
| CSP RFP + HSP submissions due | **2026-06-10, 2:00 PM CT** | T-19 days. Hard deadline. |
| Public proposal opening | 2026-06-10, 2:30 PM CT — Conf Rm 204 + Teams | Plan to attend in person or virtual. |
| Project start | TBD | Listed as TBD on the Notice; CSP package may publish a target NTP date. |
| Project finish | TBD | Same — finish date will be the period-of-performance number to bid against. Until then, plan against a typical 60-120 calendar day duration for a single-room educational lab renovation. |

## 4. Scope (per the Notice + reasonable inference for a single-room science classroom / lab modernization)

The Notice itself describes the project simply as "303 Science Education Classroom/Lab Renovation." The user's task brief expands this (consistent with typical TAMU System lab modernization scopes) to:

- Interior selective demolition of existing classroom / lab finishes, casework, and MEP terminations
- New classroom / lab finishes (flooring, base, walls, ceiling, paint, signage)
- MEP modifications — lighting, HVAC adjustments, electrical for new layout / lab equipment, plumbing modifications for lab fixtures
- Painting throughout the renovated space
- Casework / lab-grade cabinetry replacement
- Lab utility coordination (deionized water, lab gas, vacuum, fume hood, eyewash / safety shower) — depending on the room's program
- Technology infrastructure coordination with TAMU IT (low-voltage rough-in for AV, data, classroom-tech)
- Coordination with TAMU EHS for any chemical / biological / radiological hazard remediation prior to demo

**None of the scope items above carries a quantity yet** — drawings are required to size SF / LF / EA / count. See `04-scope-of-work.md` for the trade-by-trade draft and `takeoff-template.json` for the structured skeleton.

## 5. Contacts (verbatim from the Notice; full plan in `contacts.md`)

| Role | Name | Email | Phone |
|---|---|---|---|
| HUB Operations (TAMU) | Patty Winkler | p-winkler@tamu.edu | 979-845-4556 |
| SSC Project Manager | Joelle Shidemantle | Joelle.Shidementle@sscserv.com ⚠️ note the misspelling **"Shidementle"** in the email vs **"Shidemantle"** in the name field — the email-as-published may be a typo. Try both `Joelle.Shidemantle@sscserv.com` and `Joelle.Shidementle@sscserv.com`; confirm the working address on first reply. | (979) 286-3497 |
| A/E (project design) | Fred Patterson, Patterson Architects | fred@patarch.com | 979-229-7790 |

## 6. Document acquisition

- **Bid documents portal:** Trimble Unity Construct / e-Builder Public Landing Page — `https://app.e-builder.net/public/publicLanding.aspx?QS=323d686fd1304ccbb2a0ee7d143af64b`
- The Notice is explicit: "This notification is the only documentation that will be posted to the Electronic State Business Daily (ESBD). Please refer to Trimble Unity Construct Bid Package at the above link for all documentation for this solicitation."
- We have **only** the Notice. Everything else — drawings, specs, contract draft, HSP form, pricing form, bid bond form, addenda — lives at the e-Builder link and must be downloaded. This is the #1 blocker for any quantitative work.

## 7. What's not in the Notice but matters

These items are not printed on the Notice and need to be pulled either from the CSP package (when downloaded) or by direct request to Joelle:

1. **Bonding requirements.** TAMU System pattern: 5% bid bond, 100% performance bond, 100% payment bond, all per Tex. Gov't Code Ch. 2253 above the statutory thresholds. Confirm on the CSP package.
2. **Insurance limits.** Per the 2010 UGSC Article 5 baseline (TAMU SGC will overwrite). The Angelo State Attachment C (sister TTU System UGSC, in our inbox) is a near-identical template; expect: GL $1M occurrence / $2M aggregate, Auto $1M, WC statutory + Employer's $1M, Umbrella likely $5M for institutional work. Confirm on the TAMU SGC.
3. **HUB subcontracting goal.** Statewide TX HUB goal for special trade construction is ~21.1% (per 34 TAC §20.284). TAMU may set a higher project-specific goal — ask Patty Winkler.
4. **Prevailing wage.** Brazos County prevailing wage determination is required (Tex. Gov't Code Ch. 2258). Either published with the CSP package or referenced to TAMU's standing rate file.
5. **Evaluation criteria + weights.** CSPs publish a scoring matrix (price + technical + past performance + HUB + schedule, weighted). The Notice doesn't include weights; the CSP package will.
6. **Sample contract (TAMU System UGSC).** TAMU uses a near-identical template to the TTU System "2010 Uniform General Conditions and Supplementary General Conditions" we have in the Angelo State packet. Use that template as a stand-in for clause-reading until the TAMU version is in hand.
7. **Liquidated damages rate.** TAMU SGC sets a $-per-calendar-day LD rate; the ASU sample CSA has it as a placeholder ("$###.00 per calendar day"). Confirm when the CSP package arrives.

## 8. Calibration v3 extraction — what was already pulled

The LLM extracted these fields from the Notice and they are reproduced here verbatim from `exports/calibration_v3/estimate.json` `bid_packages[0]`:

```
project_name     : Harrington Education Center Lab 303 Renovation
project_number   : 2025-06813
project_location : College Station, TX, Harrington Education Center Office Towe, 0435   ← truncation: "Tower" was clipped
bid_due          : 6/10/2026 2:00 PM
contractor       : SSC Services for Education                                            ← actually the issuing facilities-services contractor, not the GC
contact          : Joelle Shidemantle Joelle.Shidementle@sscserv.com                     ← email reproduces source typo
summary          : The project involves the renovation of the 303 Science Education
                   Classroom/Lab at the Harrington Education Center. The bid is managed
                   by SSC Services for Education, with submissions due by June 10, 2026.
```

Three known issues in the extraction (not blocking, but flagging):
- `project_location` is truncated mid-word ("Office Towe, 0435" → "Office Tower, Bldg 0435"). Cosmetic.
- `contractor` field on TAMU's NOP is the **facilities services contractor (SSC)** — there is no GC yet (we, the bidder, are the GC candidate). This is the same owner-vs-GC conflation called out in `exports/calibration_v3/CALIBRATION_REPORT.md` § "Net new issues v3 surfaced" item #2.
- Calibration v3 didn't pull the e-Builder portal URL, the HSP-required flag, the pre-proposal meeting date, the A/E contact, or the HUB POC — all of which are in the Notice and would be valuable downstream. Backlog item for `extract_bundle` on NOP-class documents.

---

## Refresh Log

### 2026-05-28 — e-Builder portal re-probe + contacts/outreach verification

**e-Builder Access Attempt** — `https://app.e-builder.net/public/publicLanding.aspx?QS=323d686fd1304ccbb2a0ee7d143af64b`

- **Outcome:** ✅ **Public landing page is openly accessible — no login required.** The page renders the "Bid Package" file grid directly. The same QS-token URL that was used for the 2026-05-23 portal pull still resolves; access has not been gated since.
- **Files enumerated on the portal (5 total, all version 1, all PDF):**

  | # | Filename | Size | Uploaded by | Company |
  |---|---|---:|---|---|
  | 1 | `2025-06813 - Harrington Education Center Lab 303 Renovation Drawing Set.pdf` | 5.6 MB | Shawna Kennedy | SSC |
  | 2 | `2025-06813 - Harrington Education Center Lab 303 Renovation Specifications.pdf` | 5.3 MB | Shawna Kennedy | SSC |
  | 3 | `2025-06813 Pre-Bid Attendance.pdf` | 162.5 KB | Joelle Shidemantle | SSC College Station |
  | 4 | `2025-06813_Notice of Project-CS_26.05.08.pdf` | 264.3 KB | Shawna Kennedy | SSC |
  | 5 | `H2I casework - TAMU Harrington Room 303 - SUB-06 - 05-13-26,ad.pdf` | 8.1 MB | Joelle Shidemantle | SSC College Station |

- **Reconciliation against existing workspace:** All 5 files match the package the 2026-05-23 ingest already cataloged (see `source-files-manifest.md` and `README.md` § ingest). **No new addenda** have been posted since the original pull. The H2I Sub-06 PDF (file #5) — previously captured only as a Zscaler-blocked `*.FAILED.html` shell per `README.md` line 21 — is **still present on the portal** at the same 8.1 MB size; the `,ad` suffix in its filename is preserved from the SSC-side upload (not a new "addendum" version — same file as before, no v2). Manual browser download by the user remains the path to retrieve the binary; we do not pull 8 MB PDFs through the agent fetch path.
- **Uploader name confirms spelling:** the portal grid lists the SSC PM as `Joelle Shidemantle` (the in-workspace canonical spelling). This independently re-confirms the CSP package's §00 21 00 ¶3.1 listing and is a third source agreeing with the corrected spelling. The Notice's `Shidementle` typo remains the only place the wrong spelling appears.

**Workspace cleanup verifications**

- **Cherise Toler — TAMU Procurement contact:** ✅ already present in `contacts.md` row 17 (table § A) with full details (`ctoler@tamu.edu`, (979) 845-5887, role described as "TAMU Procurement (solicitation officer)" — the official TAMU-system procurement contact for this solicitation per ESBD; positioned as the parallel-path escalation when the SSC channel is non-responsive). She is also already cited across `outreach/01-...md`, `outreach/07-call-script-joelle-shidemantle.md` § Fallback, `proposal/05-schedule-narrative.md` R-12, and `README.md` G1. **No edit required** — confirmed correct as of this refresh.
- **Joelle email spelling:** ✅ all live outreach drafts (`outreach/01`, `outreach/02`, `outreach/07`, `proposal/02-technical-approach.md`) use `Joelle.Shidemantle@sscserv.com` — the spelling confirmed by (a) CSP §00 21 00 ¶3.1, (b) the e-Builder portal uploader name (above), and (c) `contacts.md` § A row 16. The two remaining `Shidementle` strings in this file (lines 60 and 91) are intentional historical annotations documenting the original Notice typo and the calibration-v3 verbatim extract — they are not live email addresses and should not be "fixed." **No edit required** in outreach drafts.

**Other findings**

- **No new addenda or Q&A** posted to the e-Builder portal between the 2026-05-23 original pull and this 2026-05-28 re-probe. The bid envelope, key dates, and deliverable list in `01-overview.md` § 3 stand unchanged. Continue executing per the README G1–G3 plan.
- **No contact or scope drift** detected on the portal landing — same uploader names (Shawna Kennedy and Joelle Shidemantle), same SSC-side org affiliations, same file inventory.
