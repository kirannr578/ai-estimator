# `capability-statement/` — federal capability statement

This sub-library is the source of truth for **BPC's federal capability statement** — the 1-page positioning document used in sources-sought responses, pre-solicitation outreach, agency capability briefings, small-business industry days, and SBA / NAICS small-business advocacy interactions.

## What a capability statement is

A federal capability statement is a **single-page** marketing-grade summary of the firm — designed to be skimmed in 30 seconds by a Contracting Officer, Small-Business Specialist, or capture lead. It answers four questions:

1. **Who is BPC?** (corporate identity, federal registrations)
2. **What does BPC do?** (core competencies + differentiators)
3. **What has BPC done?** (3 representative past-performance bullets)
4. **How do you reach BPC?** (POC block)

A capability statement is **not** a proposal — there is no priced offer, no SOW response, no schedule. It is a positioning document that gets BPC into the consideration set when a Contracting Officer is identifying small-business sources for an upcoming requirement (FAR 19.502 set-aside determination, FAR 10.001 market research).

## When to use a capability statement

| Use case | When |
|---|---|
| **Sources-sought responses** | Federal agency posts a sources-sought notice on SAM.gov to identify potential offerors before issuing a solicitation. BPC responds with the capability statement + a brief cover note connecting BPC's capabilities to the requirement. |
| **Pre-solicitation outreach to Contracting Officers** | BPC has identified an upcoming requirement; capability statement attached to introductory email. |
| **Agency capability briefings + Industry Days** | Standard handout / leave-behind. |
| **SBA Small-Business Specialist interactions** | At any agency where the SBS triages small-business outreach. |
| **GSA Schedule + IDIQ pre-qualification** | As part of the offeror's qualifications package. |
| **Networking + business-development** | Inserted into BD email signatures, business-card carriers, capability briefings. |

## Files in this directory

| File | Purpose |
|---|---|
| [`README.md`](README.md) | This index |
| [`capability-statement-1pg.md`](capability-statement-1pg.md) | BPC-specific 1-page capability statement, populated from `firm/firm-profile.json`. Compliance-flag annotations in-line per `firm/compliance/README.md` (e.g. expired HUB / MBE / SBE certifications marked for recertification). |
| [`capability-statement-design-notes.md`](capability-statement-design-notes.md) | Design / layout guidance — brand colors, font choice, margins, typography, logo placement, asset references for the print / PDF render. |

## How to use

1. Open [`capability-statement-1pg.md`](capability-statement-1pg.md). Confirm every `[USER TO VERIFY]` flag against the current state of `firm/compliance/README.md` — particularly the certification expiry status. **Do not represent an expired certification as current.**
2. Paste the content into BPC's design tool (`firm/assets/templates/` for canonical Office templates) using the layout in [`capability-statement-design-notes.md`](capability-statement-design-notes.md).
3. Render to PDF; render filename `Blueprint-Constructs-Capability-Statement-{{YYYYMMDD}}.pdf`.
4. For a sources-sought response, pair with a brief cover note that explicitly maps BPC's capabilities to the agency's requirement. Submit per the SAM.gov notice instructions.

## Cross-references

- Firm-level facts: [`firm/firm-profile.json`](../../firm-profile.json)
- Compliance posture (cert expiry, COIs, bonding): [`firm/compliance/README.md`](../../compliance/README.md)
- Past-performance writeups: [`../past-performance/`](../past-performance/) (3 picks per [`firm-profile.json → past_project_selection_rules`](../../firm-profile.json))
- Logo + brand assets: [`../../assets/`](../../assets/) (canonical PNG + AI source on OneDrive per `firm-profile.json → submission_assets`)
- Federal Volume capability summary (Volume II §1): [`../federal-volumes/volume-ii-management-approach.md`](../federal-volumes/volume-ii-management-approach.md)

## Discipline notes

- **One page, no exceptions.** A federal Contracting Officer with 50 sources-sought responses on their desk reads the first page; everything past that is wasted ink.
- **Federal registrations are the gate.** UEI + CAGE + active SAM are the first three things a CO checks; any of them stale or missing is an automatic skip.
- **Differentiators must be objective.** "Quality" and "communication" are not differentiators; they are table stakes. Real differentiators: "100% performance bond delivered on a $1.05M private project" (financial responsibility), "Texas-domiciled with continuous DFW operations since 2022" (geographic + tenure proof), "PMP + SAFe + ITIL principal" (program-management discipline).
- **No expired certifications.** If TX HUB / MBE / SBE are expired, do **not** list them as current. List active certifications only; mark expired with `[recertification pending]` only when transparency to a Small-Business Specialist serves a purpose.
