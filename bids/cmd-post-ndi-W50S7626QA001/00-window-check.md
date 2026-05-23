# Phase 1 — Bid window verification

**Solicitation:** W50S7626QA001 — Alter Command Post and Nondestructive Inspection (NDI) Room
**Triage date:** Saturday, 2026-05-23
**Decision:** **OPEN — proceed to Phase 2 (full bid-prep + proposal package).**

---

## 1. Closing date and time

| Field | Value | Source (verbatim where possible) |
|---|---|---|
| Date offers are due (Block 13 of SF 1442) | **04 JUN 2026** | `Solicitation - W50S7626QA001 Cmd Post and NDI.pdf`, SF 1442 cover page form-field value (PDF object stream — `/V (04 JUN 2026)` and rendered text `(04 JUN 2026) Tj`). The PDF rendered cover page exposes Block 13 as a PDF AcroForm field that does not extract to flat text via the standard text-layer; the value was confirmed by direct inspection of the PDF object/content streams. |
| Hour offers are due (Block 13) | **\[VERIFY VS SOL COVER PAGE BLOCK 13 — local time, almost certainly 1500 or 1600 local (CDT)\]** — typical FAR Part 13 SAP closings on this contracting office are 1500 CDT; user must visually confirm by opening the cover page in a PDF reader that renders form fields. |
| Solicitation issue date (Block 3 of SF 1442) | **03 MAY 2026** | Same PDF object-stream inspection — `/V (03 MAY 2026)` and `(03 MAY 2026) Tj`. |
| Time zone (place of performance) | **Central (CDT)** | Place of performance is NAS/JRB Fort Worth, TX 76127 (Tarrant County) — Central Time. |

**Method note.** The SF 1442 cover-page text layer is dominated by static form labels (e.g., "DATE ISSUED PAGE OF PAGES") with the actual values stored as AcroForm field values (`/V`) and rendered through PDF content-stream `Tj` (show-text) operators. A vanilla text extractor strips the form-field values and returns the static template text only. The values above were read directly from the underlying PDF object/content streams and cross-referenced — both methods produce the same dates, so the values are reliable.

## 2. Is it past today's date (Sat 2026-05-23)?

**No.** Today is 2026-05-23. Closing is 2026-06-04. **12 calendar days / ~9 business days remain** (excluding Memorial Day Mon 2026-05-26).

## 3. Did Amendment 0001 (SF 30) change the closing date?

**No — closing date was NOT moved.**

The SF 30 amendment `Solicitation Amendment W50S7626QA0010001 SF 30.pdf` Block 11 contains the standard SF 30 fillable language *"The hour and date specified for receipt of Offers \[ \] is extended. \[ \] is not extended."* The checkbox state is rendered as a PDF AcroForm field that does not extract to text; both possible values are present in the static template. However, **Block 14 ("Description of Amendment / Modification") is the controlling source**, and it lists the actual changes made. Verbatim from the amendment Block 14 SUMMARY OF CHANGES:

> SECTION SF 30 BLOCK 14 CONTINUATION PAGE
> SUMMARY OF CHANGES
> Section I - Contract Clauses
> Additional Information/Notes
> The following clauses were modified:
> 252.236-7001 Contract Drawings and Specifications. Aug 2000 hereby reads as follows: \[full clause text follows...\]
> The work shall conform to the specifications and the contract drawings identified on the following index of drawings:
> Title File
> Statement of Work (SOW) — DDPM262101-Alter CP and NDI-SOW (05032026)
> Drawings — DDPM262101_Alter CP and NDI_Plans (20260512)
> DDPM262101_Alter CP and NDI_Plans (03272026)

The amendment's only substantive change is to the DFARS 252.236-7001 (Contract Drawings and Specifications) clause, updating the index of drawings to add the **2026-05-12 plan set** alongside the original 2026-03-27 plan set (per `Deleted Attachments.txt`, the 03-27 plan set has since been removed and the 05-12 set is the operative drawing set). **There is no mention of any modification to Block 13 of the SF 1442, no extension of the offer due date, and no change to the place / method of submission.** Per FAR 43.103 and the SF 30 instructions, an extension of the offer due date — if it had been made — would have been called out explicitly in the Block 14 summary as a change to Block 13 of the SF 1442.

**Conclusion:** The closing date in Block 13 of the SF 1442 stands. **Offers due 04 JUN 2026, time TBD-by-cover-page.**

> ⚠️ **\[VERIFY\]** before submitting: Open the Solicitation PDF in Adobe Reader (or any PDF reader that renders AcroForm fields), confirm Block 13 of the SF 1442 reads "04 JUN 2026" with the local-time hour, and confirm the SF 30 Block 11 checkbox is marked **"is not extended"**. The data extraction here is reliable but a 5-minute visual confirmation eliminates the residual risk that the SF 30 silently moved the date in a way the Block 14 summary failed to enumerate.

## 4. Solicitation type — FAR Part / procedure

**FAR Part 13 Simplified Acquisition Procedure using FAR Part 12 Commercial Item procedures, with comparative-evaluation award authority under FAR 12.203(c)(2).** Mixed-form solicitation:

- **Cover form**: SF 1442 (Solicitation, Offer, and Award — Construction, Alteration, or Repair) — Type-of-Solicitation block is *Negotiated (RFP) / Request for Proposal* per FAR 13.500 SAP-with-commercial-procedures usage.
- **Section L addendum**: explicitly invokes FAR 52.212-1 *Instructions to Offerors — Commercial Products and Services (Deviation 2026-O0038)* and uses RFO ("Request for Offer") nomenclature. The phrase used throughout is "quote".
- **Section M evaluation**: *FAR 52.212-2 (Deviation 2026-O0038) (Tailored)* with Section M paragraph (a)(ii): "Quotes meeting the requirements of para (i) will be evaluated in pursuit of the **best value** for the Government, price and any factors of the solicitation considered. **In accordance with RFO FAR 12.203(c)(2), a comparative evaluation, without objective standards, of the quotes will be conducted.**" (verbatim, p.49)
- **Award decision**: paragraph (a)(v): "The Government intends to award a contract, without negotiating, to the quote that **represents the best value to the Government**; however, the Government reserves the right to negotiate if deemed in its best interest." (verbatim, p.50)

This is **NOT** a sealed-bid IFB (FAR Part 14), **NOT** a true negotiated FAR Part 15 RFP, and **NOT** LPTA. It is the FAR 12.203(c)(2) *comparative evaluation* mechanism — best-value-tradeoff between past performance, technical, and price, with no formal objective standards and no formal discussion phase guaranteed. The CO can award without negotiating to the quote that "represents the best value", or can negotiate with a single offeror if their quote is otherwise the most attractive.

**Implication for our offer**: Past performance and technical (the 2 subfactors — equipment/materials/labor list and project schedule) are evaluated alongside price, with the CO using subjective judgment. Pricing alone does not win; submission discipline + proven similar past performance + a credible schedule + a competitive (not necessarily lowest) price wins.

## 5. Set-aside status

**100% Total Small Business Set-Aside.** Per FAR 52.219-6 (*Notice of Total Small Business Set-Aside (Deviation 2026-O0038)*) at Section I (verbatim title in the FAR Clauses Incorporated by Reference list, p.14). Not 8(a) / HUBZone / WOSB / SDVOSB sub-set-aside; standard SBSA only.

## 6. NAICS code

**\[VERIFY VS SOL COVER PAGE — likely 236220 — Commercial and Institutional Building Construction, $45.0M small-business size standard\]**. The NAICS code field on the SF 1442 cover page is also a PDF AcroForm field that did not extract to flat text. The Product Service Code (Z2AA — *Maintenance, Repair, and Alteration of Office Buildings*) listed at Section A page 3 is consistent with NAICS 236220, and 236220 is the standard NAICS for federal building-renovation procurements at this size and scope. The user must visually confirm the NAICS in the cover page block before final SAM.gov reps & certs verification.

---

## Decision branch taken

> Open with ≥10 calendar days remaining → **proceed to Phase 2 full bid-prep + proposal package.**

Although 12 calendar days is just barely above the threshold, the schedule is **viable but tight**. Specific risk-mitigation flags carried forward into Phase 2:

1. **Bonding-agent lead time is the binding gate.** Order bid-bond + P&P bond commitment letter on the surety the day the no-go branch is closed (i.e., today / Mon 2026-05-26 at the latest). Treasury Circular 570 sureties typically issue inside 3–5 business days for known clients, but a new-client underwriting cycle can run 10–15 business days — too long.
2. **Site access — 14 BUSINESS days advance request — is the second binding gate.** Per SOW §7, base-access requests must be submitted to the Government POC "no less than fourteen (14) business days prior to the required access date." That means **a contractor wishing to attend a site visit on 2026-06-02 (Tue, the day before close — last possible site visit before close) would have needed to submit names by 2026-05-13 — already past.** A site visit BEFORE bid-close is therefore **not possible** without an immediate exception from the 136 CES POC. Phase 2 must (a) request a site-visit RSVP including an exception-from-the-14-day rule, and (b) build the offer on field-verified-after-award assumptions, with risk premium adjusted accordingly.
3. **SAM.gov registration must be active.** Standard FAR 52.204-7 hurdle.
4. **NAICS 236220 small-business size assertion must be active in SAM.** Required for set-aside eligibility.

Phase 2 carries forward as **"OPEN with binding-gate risk"** — Memo flagged in `README.md` § PROPOSAL STATUS.

---

## Audit trail — files read for this decision

| File | Pages read | Purpose |
|---|---|---|
| `Solicitation - W50S7626QA001 Cmd Post and NDI.pdf` | All 50 pages (text layer); object stream + content stream for cover-page form fields | Cover SF 1442; Sections A–M including L addendum (FAR 52.212-1) and M (FAR 52.212-2 Tailored) |
| `Solicitation Amendment W50S7626QA0010001 SF 30.pdf` | All 3 pages | SF 30 Block 14 summary (drawings clause modification only); confirmed no Block 13 / closing date change |
| `DDPM262101-Alter CP and NDI-SOW (05032026).pdf` | All 4 pages | SOW for context — Place of Performance, POCs, base access, P/P timing |
| `Deleted Attachments.txt` | 1 line | Confirmed prior-version drawings (03272026) was superseded |
| `DDPM262101_Alter CP and NDI_Plans (20260512).pdf` | Sheet A-1 of 2 (text layer) | Drawing set existence + sheet count + scope confirmation |

---

**End Phase 1 finding. Phase 2 deliverables produced in this same workspace.**
