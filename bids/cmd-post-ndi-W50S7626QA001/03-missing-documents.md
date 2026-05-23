# Missing documents — what's still needed

A list of documents we DO NOT have but need (or should ask for) before final pricing.

## A. Likely-missing solicitation attachments (request via RFI)

| # | Document | Why we need it | Source / how to get |
|---:|---|---|---|
| 1 | **Drawing sheet 2 of 2** — NDI Room renovation (B1675) | We have only Sheet A-1 (CP renovation in B1672) extracted from the plan-set PDF. Sheet 2 of 2 — NDI Room renovation — is in the same plan-set PDF (`DDPM262101_Alter CP and NDI_Plans (20260512).pdf`) but did not yield extractable text in our pass. **Open the PDF in Adobe Reader to confirm what's on Sheet 2** — partition layout, electrical, mech, finishes for the NDI room conversion. | Already in hand — re-open visually |
| 2 | **AF 66 Submittal Register** | SOW §5.2: contractor delivers AF 3000 Material Approval Submittals "for each item listed on the AF 66 Submittal Register, as applicable." The AF 66 itself was not in the attachment package; either the Government issues it post-award, or it's missing from the bid package. | RFI to CO — `proposal/11-rfi-cover-letter.md` Q\#7 |
| 3 | **Existing-conditions architectural / electrical / mechanical as-builts for B1672 and B1675** | SOW §4.4 says "Government-provided drawings and as-builts are for reference only" — implying as-builts may exist. We have new-construction drawings only (Sheet A-1 + Sheet 2 of 2) and reference photos. As-builts would help with electrical / mechanical takeoff (existing panel capacity, existing ductwork sizing, existing fire-alarm panel manufacturer). | RFI / site visit; if no as-builts exist, flag in offer technical narrative |
| 4 | **Existing fire-suppression and fire-alarm system documentation** | Drawing General Note 9: *"All rooms shall have adequate fire suppression installed. Modify the current system to sufficiently encompass all newly constructed areas."* Without a copy of the existing system diagram + manufacturer / model, the fire-protection sub cannot quote modification scope to the partition layout in the new CP without a field walk. | RFI to CO and/or post-award field-walk; price contingency carries this risk |
| 5 | **Existing HVAC system documentation** (zoning + controls type + balance report) | Drawing General Note 10 + Construct Note items HVAC.A–C: split off ducting, add diffuser, install return grates, install in-room override button, balance system. Existing controls platform (BACnet / Trane Tracer / Honeywell / etc.) drives the override-button integration cost. | RFI to CO and/or site visit |
| 6 | **AFFF decommissioning evidence** for B1675 | SOW §1.2 says room is "decommissioned" but does not specify whether AFFF-impacted-substrate (concrete coatings, sumps, piping) was remediated. PFAS impact would shift demolition scope to TCEQ-permitted PFAS-waste handling. | RFI \#5 in `proposal/11-rfi-cover-letter.md` |
| 7 | **Cabinet / casework selection sheet** | Drawing Construct Note: *"Remove and replace all cabinets, overhead cabinets, counters, and the sink in the new dimensions and configuration. Cabinets must be approved by government."* — without a manufacturer / line / finish standard, the casework sub will price to a wide variance | RFI; post-award submittal review may also resolve, but pricing now needs an assumption |
| 8 | **Photo backdrop bracket fabrication detail** for relocation to B1669 Rm 112 | Drawing Construct Note 12: relocation to B1669, top of bracket 11 ft AFF, "back-brace fabrication may be required" — back-brace detail not on the drawing. | Site visit / field-verify |

## B. Cover-page form-field values (visual confirmation only — no third-party request needed)

These are values stored as PDF AcroForm fields on the SF 1442 / SF 30 that did not extract via our text pipeline. **Open the PDFs in Adobe Reader and read the values directly:**

| Form field | Where | Value extracted | Action |
|---|---|---|---|
| SF 1442 Block 1 — Solicitation Number | Cover | `W50S7626QA001` | ✅ confirmed in PDF text |
| SF 1442 Block 3 — Date Issued | Cover | `03 MAY 2026` (extracted from PDF object stream) | \[VERIFY visually\] |
| SF 1442 Block 7 — Issued By + CODE | Cover | DoDAAC `W50S76` (extracted from G-section routing) | \[VERIFY block 7 visually\] |
| SF 1442 Block 8 — Address Offer To | Cover | \[VERIFY — likely same as Section L email `136.AW.MSC@us.af.mil`\] | Visual |
| SF 1442 Block 9 — For Information Call | Cover | \[VERIFY — likely Capt Crabtree per SOW §13.1\] | Visual |
| SF 1442 Block 13 — Date / Hour Offers Due | Cover | Date `04 JUN 2026`, **HOUR \[VERIFY\]** | Visual |
| SF 1442 Block 13 — Sealed Bid OR Negotiated checkbox | Cover | **\[VERIFY — likely "Negotiated (RFP)"\]** | Visual |
| SF 1442 Block 13a — Number of copies | Cover | \[VERIFY\] | Visual |
| SF 1442 Block 13B — Offer guarantee required Y/N | Cover | **\[VERIFY — likely YES\]** because Section L paragraph (a)(2) NOTE says "If a bid bond is required (SF1442, Page 1, Block 13B), scanned copies must be submitted with submission of the quote" | Visual |
| SF 1442 Block 13d — Min acceptance period | Cover | \[VERIFY — likely 90 calendar days\] | Visual |
| SF 1442 NAICS field | Cover | **\[VERIFY — likely 236220\]** | Visual |
| SF 1442 Item 11 — Performance period start clause | Cover | \[VERIFY — should align with SOW §11 90-day POP\] | Visual |
| SF 1442 Item 12a / 12b — Performance + Payment Bonds required and # cal days after award | Cover | **\[VERIFY — likely YES + 10 cal days\]** | Visual |
| SF 30 Block 11 — Receipt of Offers extended Y/N checkbox | SF 30 cover | **\[VERIFY — Block 14 summary makes "is not extended" the only consistent answer\]** | Visual |
| SF 30 Block 16C — CO signature date / effective date of amendment | SF 30 cover | \[VERIFY — likely on/about 2026-05-12\] | Visual |

> ⚠️ **All form-field values must be visually confirmed before final SF 1442 fill.** A 5-minute walkthrough of the cover page in Adobe Reader resolves all of the above.

## C. SAM.gov-side verification (firm-internal — no procurement document needed)

These are firm-internal data points the user must verify; they are NOT documents the CO holds.

| # | Item | Where to verify |
|---:|---|---|
| 1 | UEI active | SAM.gov entity profile |
| 2 | NAICS 236220 registered + small at $45M | SAM.gov "Goods and Services" + "Size Metrics" |
| 3 | Reps & Certs current within 12 months | SAM.gov "Reps & Certs" |
| 4 | CAGE active | SAM.gov entity profile |
| 5 | EFT current | SAM.gov financial info |
| 6 | TIN matches IRS | SAM.gov entity profile |
| 7 | DFARS 252.204-7016 covered-defense-telecom rep on file | SAM.gov reps |
| 8 | NIST 800-171 Basic Assessment in SPRS | `https://www.sprs.csd.disa.mil/` |
| 9 | No active exclusions | SAM.gov exclusions search on entity name + UEI + key principals |

## D. Sub-quote-side gaps

See `outreach/04-`, `05-`, `06-`. The four sub categories that need named-vendor pricing before final bid are:

| Sub | Reason for outreach |
|---|---|
| Electrical (DoD-experienced) | UFC 3-501-01 compliance; secure-area conduit + comm-box rough-in; emergency egress + battery-backup; AF 3000 submittal cycle; coordination with 136 CES inspections |
| Mechanical / HVAC | Duct modification + diffuser + return + override button + balance-and-report (per Drawing General Note 10); coordination with existing BMS controls (manufacturer TBD) |
| Secure doors + hardware (Stanley/Best Lock-Core, steel-sheet reinforced solid-wood, anti-pin) + impact-rated mesh-reinforced 1-way credential window | Specialty hardware; lead time 4–8 weeks for Lock-Core compatible cores ordered against the firm's existing key system at NAS-JRB |
| (Optional) Fire suppression / Fire alarm modification | If electrical sub does not self-perform fire alarm + fire suppression modification, separate sub needed |

## E. Government-furnished items (per SOW §6)

These are NOT missing — confirmed available:

- Electrical power at the building (contractor responsible for any new connections / panel modifications)
- Water at the building (contractor responsible for any new connections)

Government does NOT furnish: lay-down area, fencing, dumpsters, parking, restroom facilities, security badging (contractor coordinates badging via NAS JRB Visitor Control Center).

## F. Reference-only documents (already in hand, not "missing")

| File | Use |
|---|---|
| `Alter CP and NDI_B1675 NDI Rm Photos REFERENCE ONLY.pdf` (3.5 MB) | Existing-condition photos of the AFFF room in B1675 — pre-conversion |
| `Altter CP and NDI_B1672 CP Rm Photos REFERENCE ONLY.pdf` (72.5 MB) | Existing-condition photos of B1672 — pre-renovation |

> ⚠️ The CO marked these "REFERENCE ONLY" — which under FAR 52.236-2 (Differing Site Conditions) means the contractor cannot rely on them as as-built. Field-verify all dimensions and conditions per SOW §4.4.

## G. RFI question consolidation

All of the gaps above that require CO action are consolidated into 5–6 RFI questions in `proposal/11-rfi-cover-letter.md` and `outreach/01-email-CO-rfi-consolidated.md`.
