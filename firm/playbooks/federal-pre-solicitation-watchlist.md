# Playbook — Federal Pre-Solicitation Watchlist

> **Exemplar opportunities being tracked:** PAIS Backcountry Cabin (NPS solicitation `140P6026Q0029` referenced in [`firm/firm-profile.json → notes`](../firm-profile.json)); SAAN San Juan Restrooms (NPS solicitation `140P1226Q0025`); future USFWS / USACE / GSA upcoming notices.
>
> **Matching workspace location:** [`bids/_WATCHLIST/`](../../bids/_WATCHLIST/README.md) — each watched opportunity gets a `<slug>.md` file.

## 1. Procurement description

Pre-solicitation tracking is the **upstream half of every federal bid pipeline**. The window between an opportunity first surfacing (sources-sought, RFI, pre-solicitation notice, industry day, draft RFP) and the formal solicitation drop typically runs **30–120 days**, sometimes longer for major projects. Firms that engage during this window have measurable advantages:

- **Capability statement on file** with the agency's small-business specialist or contracting team before the solicitation is built — gets the firm on the "I know who can do this" mental map
- **RFI responses that shape Section L/M** — agencies sometimes literally lift past-performance criteria language from a strong RFI response
- **Site-visit attendance** at an industry day or planning meeting before the solicitation drops, giving real measurements + scope intuition before the rest of the field
- **Posting cadence intuition** — knowing that an NPS region drops Backcountry Cabin Q-series notices in Q1 each year lets BPC plan capacity for Q4 of the prior year

Pre-solicitation work is **not** the same as live bidding — it's market intelligence + relationship building. It produces no submission and no award; the deliverable is **opportunity awareness + a populated `bids/_WATCHLIST/` entry** that can be flipped to `bids/<slug>/` the day the formal RFP drops.

When you'll see it:

- **Sources-sought notices on SAM.gov (FAR 5.205)** — agency surveys the market to gauge whether enough small-business / SDVOSB / WOSB / HUBZone offerors exist to justify a set-aside; respond with a capability statement + project examples within 7–14 calendar days
- **RFI responses (FAR 15.201)** — agency asks specific scope / pricing / scheduling questions to refine the SOW; responses help the agency draft Section L/M; non-binding for both sides
- **Pre-solicitation notices** — formal SAM.gov posting that an RFP is coming, with intended issue date + magnitude band + NAICS; sets the calendar
- **Synopses** — pre-award notice of intent to award, typically post-source-selection — too late to bid but useful for competitive intelligence
- **Industry days + site visits** — typically 30–60 days before the formal RFP; agencies prefer in-person but most run hybrid Teams since 2020
- **Draft RFP for industry comment** — major DoD / VA / GSA programs sometimes drop a draft for 30-day comment period before the final RFP

## 2. Sources to monitor (BPC daily / weekly sweep)

| Source | Type | Cadence | Filter | Subscription mechanism |
|---|---|---|---|---|
| SAM.gov sources-sought (`Notice Type: Sources Sought`) | Sources-sought | Daily | NAICS 236220 + 236118 + 238 trades; set-aside any; state Texas + region (Region 7 GSA / NPS South + Intermountain + Pacific West) | SAM.gov "Saved Searches" feature; email alert daily |
| SAM.gov pre-solicitation (`Notice Type: Presolicitation`) | Pre-sol notice | Daily | Same filter | Same saved-search email alert |
| SAM.gov RFP / RFQ (`Notice Type: Solicitation`) | Live solicitation | Daily | Same filter | Same saved-search email alert |
| NPS regional procurement pages (Intermountain, Pacific West, South, Northeast, Midwest, Alaska) | NPS sources | Weekly | Park-unit construction notices | Manual; calendar reminder weekly |
| USFWS Region 2 + 4 + 6 contracting | USFWS sources | Weekly | NWR construction notices | Manual |
| USACE district pages (Fort Worth, Galveston, New Orleans, Tulsa) | USACE sources | Weekly | Civil works + military construction sub-$10M | Manual |
| GSA Federal Acquisition Service `https://buy.gsa.gov/` | GSA IDIQ + task orders | Weekly | GSA Schedule 36 (construction); Multiple Award Schedule 03FAC (facilities) | Manual |
| TXANG / DoD Region contracting (Camp Mabry, Camp Swift, Camp Bullis) | DoD sources | Weekly | Texas-based federal facilities | Manual |
| TXSmartBuy ESBD | TX state sources | Daily | Agency 715 (PVAMU), 711 (TAMU), 730 (UT System), 750 (TTU System), 766 (TFC), 802 (USACE TX), 802 (GSA TX) | ESBD email alerts |
| GovWin IQ (paid) — if subscription warranted | Aggregated federal sources + agency forecasts | Daily | Texas-aware, NAICS 236220 | Paid tier; revisit subscription each fiscal year |

## 3. BPC posture for pre-solicitation engagement

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Requirement | BPC value | Status |
|---|---|---|
| SAM.gov saved searches configured under the BPC account | Yes (target: 6 saved searches, daily emails) | 🔴 — verify; document each saved search's query string in `firm/_scripts/` |
| Capability statement (1-page PDF, federal format) | `[USER TO FILL — Day-3 priority]` | 🔴 — needed before responding to first sources-sought |
| RFI response template (3–5 page narrative + appendix with project facts) | `[USER TO FILL — Day-3 priority]` | 🔴 |
| Industry-day attendance tracking (date, agency, opportunity, attendee, notes) | `[USER TO FILL]` | ⚠️ — start log on first industry day |
| Site-visit attendance roster (for sources-sought leading to mandatory pre-bid) | n/a until first attendance | — |
| Past-performance summary appendix (1-page per project) | Partial — see [`firm/proposal-library/past-performance/`](../proposal-library/past-performance/) | ⚠️ — formalize before next sources-sought |
| Watchlist schema (this file's §4) | This file | ✅ |
| Watchlist file template | `bids/_WATCHLIST/<slug>.md` per [`bids/_WATCHLIST/README.md`](../../bids/_WATCHLIST/README.md) | ✅ (already exists) |

## 4. Watchlist data model (schema for `bids/_WATCHLIST/<slug>.md`)

Each watched opportunity is a single markdown file with the following sections. The schema is intentionally narrow so the file stays scannable as the watchlist grows.

```
# Watchlist — <project name>

## Identifying facts
- Slug: <slug>
- Sol number (predicted or assigned): <number>
- Agency: <full name + acronym>
- Issuing office: <office + address>
- Forecast posting date: <YYYY-MM-DD or "Q-N FY-YY">
- Magnitude band (forecast): $<low> – $<high>
- NAICS: <code>
- Set-aside (forecast): <SBA / SDVOSB / WOSB / HUBZone / 8(a) / Full & Open / TBD>
- Procurement type (forecast): <LPTA / Tradeoff / JOC / IDIQ task / Brooks A/E>
- Source: <where BPC heard about it — sources-sought, industry day, networking>

## Why this matters to BPC
- Strategic fit: <1-2 sentences>
- Past-performance picks if won: <pick from firm-profile.json>
- Geographic fit: <drive time from Frisco, TX 75033>
- Sub bench: <known subs in region for the scope; gaps>
- Compliance posture: <any prep needed before bid: HUB recert, surety capacity, COI renewal>

## Tracking signals (monitor weekly)
- SAM.gov posting status: <Not yet posted / Sources-sought open / Pre-sol posted / RFP active / Award notified>
- Last SAM.gov check date: <YYYY-MM-DD>
- Last agency contact: <date + person + summary>
- Next milestone: <industry day / RFI cutoff / formal RFP drop>
- Trigger to flip to active workspace: <e.g. "Formal RFP posted with NAICS 236220 small set-aside">

## Open actions
- [ ] <task>
- [ ] <task>

## Source-document inventory
- <file path on disk OR url>
```

A watchlist entry stays in `bids/_WATCHLIST/` until **one of three terminal events**:

1. **Formal solicitation posts** → flip to `bids/<slug>/` and remove the watchlist entry (link from the new workspace's `01-overview.md` to the prior watchlist for context)
2. **Opportunity confirmed dead** (canceled, awarded to other, scope mismatch confirmed) → move to `bids/_NO_GO/<date>-<slug>.md` with a one-paragraph rationale
3. **Watchlist entry > 12 months stale and no posting** → archive to `bids/_NO_GO/` with rationale "stale; no posting after 12 months of tracking"

## 5. BPC pre-solicitation workflow

### 5.1 Sources-sought response (7–14 day window)

When a sources-sought notice matches BPC's filters:

1. **Triage within 24 hours.** Read the notice. Confirm BPC has SAM + Reps & Certs current. Confirm NAICS + size + set-aside fits.
2. **Add to `bids/_WATCHLIST/<slug>.md`** with the slug pattern matching the eventual solicitation number prediction.
3. **Draft response** using the capability-statement + RFI-response templates from `firm/proposal-library/`:
   - Cover page: firm legal name, UEI, CAGE, NAICS, size assertion, point of contact
   - Project examples: 3 examples that match the agency's stated scope as closely as possible — pull from `firm/firm-profile.json → past_projects`
   - Bonding capacity statement: single-project + aggregate from surety letter
   - Direct response to each question the sources-sought asks (often: "Can your firm self-perform 15% of this work?"; "What's your typical lead time on similar work?"; "Identify any specialty trades you would subcontract.")
4. **Send to the SAM.gov-listed POC** within the cutoff. Keep the email — agencies sometimes circulate sources-sought respondents internally as the eventual offeror pool.
5. **Log in `local/sources-sought-log.csv`** (outside git): date, agency, notice #, scope, BPC response sent, ack received Y/N, posting outcome.

### 5.2 RFI response (typically 14–30 day window)

When the agency posts an RFI with specific questions:

1. Re-read every question and identify which ones BPC can credibly answer with experience-backed detail (vs which require speculation — skip those).
2. Draft a per-question response, citing past-project facts where applicable.
3. If BPC's answer would reshape the SOW (e.g. "Owner-supplied lockers will create coordination overhead — recommend either CFCI or splitting the lockers into a separate procurement"), say so plainly. Many agencies welcome the reshape.
4. Send to the RFI-response email POC within the cutoff. RFI responses are typically not made public, but **they should be assumed FOIA-discoverable** — write them like you'd want them read at a debriefing.

### 5.3 Pre-solicitation notice → active tracking

When a formal pre-solicitation notice posts (FAR 5.204):

1. Update the watchlist entry's "Tracking signals" section
2. Calendar the forecast posting date + 14 days as a check-in milestone
3. If the pre-sol names an industry day: **attend** (in person if practical; Teams otherwise). Take notes — site address, attendees, scope clarifications, schedule signals.
4. If the pre-sol names a site visit: **attend with measurement tools**. The site visit is where 80% of takeoff uncertainty resolves.

### 5.4 Industry day attendance

For each industry day attended:

1. Add a row to `local/industry-day-log.csv` (outside git): date, agency, notice #, attendee, format (in-person/Teams), takeaways.
2. Drop a one-paragraph summary into the watchlist entry's "Tracking signals" section.
3. If specific subs / partners were also present, log the interaction — these become teaming opportunities later.

### 5.5 Capability statement positioning

The **capability statement** is BPC's 1-page federal-format leave-behind. Send it:

- With every sources-sought response (attached PDF)
- After every industry-day attendance (follow-up email to the agency POC)
- Cold-mail to small-business specialists at NPS / USFWS / USACE / GSA regional offices BPC wants to be on the radar of (max 3 per quarter to avoid being annoying)

The capability statement lives at [`firm/proposal-library/capability-statement/bpc-capability-statement.md`](../proposal-library/capability-statement/) once authored (Day-3 priority).

## 6. Triggers to flip a watchlist entry to an active bid workspace

The watchlist → active bid conversion happens when **all four** of these are true:

1. **Formal solicitation has posted** on SAM.gov (or the agency portal). A pre-solicitation notice is not enough.
2. **Set-aside / NAICS / size matches BPC's eligible posture.** If the actual solicitation is Full & Open instead of small-business set-aside, re-triage; BPC might still bid as a teaming partner with a small-business prime.
3. **BPC's compliance posture is current** (SAM, Reps & Certs, COIs, bondability).
4. **Estimator capacity is available** for the proposal window.

Conversion steps:

1. Create `bids/<slug>/` from `bids/_TEMPLATES/<matching-type>/`
2. Copy the watchlist entry's "Identifying facts" + "Why this matters to BPC" + "Source-document inventory" into the new workspace's `01-overview.md`
3. Add a cross-reference at the top of `01-overview.md`: "Origin: tracked in `bids/_WATCHLIST/<slug>.md` from <YYYY-MM-DD>"
4. Delete the watchlist entry (or move to `bids/_WATCHLIST/_ARCHIVE/` if useful for future similar opportunities)

## 7. Triggers to move a watchlist entry to `_NO_GO/`

Move to `bids/_NO_GO/<date>-<slug>.md` when **any** of these is true:

- The solicitation posts but with a set-aside / NAICS that BPC is not eligible for, and no teaming path is viable
- The solicitation posts with a scope that's outside BPC's bid envelope (too large, too specialized, wrong geography)
- The solicitation posts but the timing collides with higher-priority work and BPC capacity won't allow a quality submission
- 12+ months pass with no posting and no agency signal that the opportunity is still alive

Each `_NO_GO/` memo follows the structure in [`bids/_NO_GO/README.md`](../../bids/_NO_GO/README.md).

## 8. Typical timeline (sources-sought → award)

| Phase | Typical days | Notes |
|---|---|---|
| Sources-sought notice posts | T-0 | 7–14 day response window |
| Sources-sought response sent | T+10 (target) | Within cutoff |
| Pre-solicitation notice posts (if it does) | T+30 to T+90 | Sometimes skipped if the agency already has enough offeror data |
| Industry day | T+45 to T+90 | Typically before draft RFP |
| Draft RFP for industry comment (if any) | T+60 to T+120 | 30-day comment window |
| Final RFP posts | T+90 to T+180 | This is the flip-to-active-workspace trigger |
| Proposal due (LPTA) | RFP + 30–45 days | See [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) §8 |
| Proposal due (tradeoff) | RFP + 45–90 days | See [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md) §8 |

## 9. Common pitfalls

1. **Skipping the sources-sought response** because it "isn't a bid." Sources-sought is where the agency builds the eventual offeror pool's mental map. Skipping it costs zero hours of pricing work and is the cheapest market-positioning move in federal procurement.
2. **Generic capability statement.** Sending the same 1-pager for every notice signals "we'll bid anything." Tailor at least the project-examples section to the agency + scope.
3. **Late RFI response.** RFI responses received after cutoff are typically not incorporated. Calendar the cutoff the day the RFI posts.
4. **Industry day no-show.** When the agency hosts an industry day specifically for the opportunity, attendance is a tracked signal. Non-attendance reduces the agency's confidence the firm is serious.
5. **Watchlist sprawl.** More than ~20 active watchlist entries is unmanageable. Aggressively prune to `_NO_GO/` or `_WATCHLIST/_ARCHIVE/`.
6. **Forgetting to flip to active workspace.** A live solicitation that sits in `_WATCHLIST/` past the RFI cutoff is a missed bid. Add a weekly sweep: any watchlist entry whose forecast posting date has passed gets a SAM.gov status check.
7. **RFI response gives away pricing intuition.** RFI responses are not binding but agencies may use them to set the price-realism floor at evaluation. Don't anchor pricing in an RFI unless you're committed to defending it later.
8. **Sub-disclosure in RFI response.** Naming subs by name in an RFI response can lock BPC into a teaming arrangement (the agency may expect the same subs at bid time). Stay general unless the teaming is intentional.
9. **No log of contact attempts.** Cold-mailing a small-business specialist 3 times in a quarter is professional outreach; cold-mailing 12 times is harassment. Track outreach cadence in `local/agency-outreach-log.csv`.
10. **Confusing pre-solicitation with debriefing.** A pre-solicitation notice is upstream of the RFP; a debriefing is downstream of an award (FAR 15.506). Different cycles, different artifacts.

## 10. Capability-statement positioning (Day-3+ priority)

Reference content for the BPC capability statement (to live at `firm/proposal-library/capability-statement/bpc-capability-statement.md`):

| Section | Content (Day-3 build target) |
|---|---|
| Header | Blueprint Constructs, LLC dba Blueprint Constructs / UEI LM4YHVQ71QG7 / CAGE 9LET0 / NAICS 236220 (size: small) / DUNS (retired) |
| Tagline | One-sentence summary of BPC's federal niche (e.g. "Small-business institutional renovation contractor, Texas-domiciled, $1M+ bonding floor, USFWS / NPS / USACE small-construction track") |
| Core capabilities | Institutional interior renovation; minor new construction; site work; selective demo; HVAC + electrical + plumbing renovation; ADA compliance retrofits |
| Differentiators | Bonded to $1M+ per project; TX HUB-certified (per current status); SAM registration active; CMBL active; bilingual field supervision; Frisco-based with Texas-statewide reach |
| Past performance highlights | 3 project blurbs (Lavon RV Park; Hindu Temple of Southlake; Holiday Inn Hall Park) — 2 sentences each, with owner + $ + completion year |
| Contact | Ravikiran (Rocky) Nudurupati, Principal in Charge; rocky@blueprintconstructs.com; (469) 213-1838 |

## 11. Cross-references

- **Pre-solicitation workspace location:** [`bids/_WATCHLIST/`](../../bids/_WATCHLIST/README.md)
- **Live federal LPTA playbook:** [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md)
- **Live federal tradeoff playbook:** [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md)
- **Federal JOC task playbook:** [`federal-joc-task.md`](federal-joc-task.md)
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **Capability statement (under build):** [`firm/proposal-library/capability-statement/`](../proposal-library/capability-statement/)
- **NO-GO memos:** [`bids/_NO_GO/README.md`](../../bids/_NO_GO/README.md)
- **Current watched opportunities (per firm-profile.json):** `PAIS Backcountry Cabin 140P6026Q0029`, `SAAN San Juan Restrooms 140P1226Q0025`
