# Bid bond form template — FA667526Q0002 B1710 Office Refurbishment

## NOT APPLICABLE — This RFQ does NOT require a bid bond

This file is included for cross-workspace consistency (so reviewers can spot-check that bid-bond mechanics were considered). For B1710 specifically, **no bid bond is required**.

### Evidence

- **FAR 52.228-1 (Bid Bond)** is **not cited** in Section I (Contract Clauses) of `Solicitation - FA667526Q0002.pdf`. We searched the full 25-page PDF; the clause is absent.
- The form SF 1449 used here (commercial items) does not have a bid-bond block. SF 24 (Bid Bond form) is not in the package.
- **What IS required** is a *post-award* payment bond per FAR 52.228-13 Alternative Payment Protections (Section I, p.17). That is handled via `06-bondability-letter-template.md`.

### Why bid bonds aren't here

This is a Simplified Acquisition Procedure (SAP) RFQ under FAR Part 13 + Part 12 (Commercial Items), with an estimated contract value almost certainly in the $25K-$150K band. FAR 28.101-1(a) requires bid guarantees only when a performance bond or P&P bond is also required (which they aren't for this size of work — see FAR 28.102-1(a)(1) Miller Act threshold of $150,000 for P&P bonds on construction).

Instead, the CO chose the **alternative payment protection** route under FAR 28.203-3 / 52.228-13, which requires only a *payment* protection (bond OR ILC OR escrow OR tripartite agreement), valid post-award, within 10 days. No bid-time guarantee required.

### What to do

Nothing — leave bid-bond mechanics out of the offer packet. Do NOT include an SF 24 even as a "just in case" gesture; including unrequired forms can confuse the CO's compliance check.

### Cross-workspace reference

The sister `bids/cmd-post-ndi-W50S7626QA001/` workspace **does** require a bid bond (per its Section L paragraph (a)(2) NOTE — 20% of bid or $3M whichever is less). That workspace has the full bid-bond mechanics. **Do not import that complexity here.**

### If the CO surprises us with an amendment requiring a bid bond

Unlikely but possible: if the CO issues an SF 30 amendment before 29 May 17:00 that adds a bid bond requirement, we'd need to scramble to obtain an SF 24 signed by the bonding agent and the offeror. In that case:
1. Amendment SF 30 → acknowledge per FAR 52.214-3 / 52.215-1
2. Bonding agent issues SF 24 with surety's corporate seal
3. Submit SF 24 with the offer email packet

We monitor `lydia.carlton@us.af.mil` for amendments through Fri 14:00 to catch any such surprise.
