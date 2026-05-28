"""Per-agency Texas wage-determination harvester — PLACEHOLDER (future work).

Under **Tex. Gov't Code Ch. 2258**, each TX procuring agency sets and
publishes its own prevailing-wage schedule on a per-project basis as part
of every solicitation. There is no centralized TWC per-county WD repository
to fetch from (an earlier roadmap entry that assumed one was based on a
faulty premise — see ``firm/playbooks/pricing-data-sources.md`` →
"Structural Note — Texas Prevailing Wage").

This module is the placeholder for the **future per-agency harvester** that
would scrape the active-solicitation pages of the major TX procuring
agencies and extract the WD PDFs they attach. It is documentation-as-code:
no third-party imports, no HTTP fetching, no real implementation. It exists
so the future shape is explicit and easy to find.

The right time to build the harvester is when there is concrete demand from
> 3 active TX state-agency bids per quarter, not before.
"""

from __future__ import annotations

ABSTRACT_REASON: str = (
    "Stub only. Tex. Gov't Code Ch. 2258 places prevailing-wage publication "
    "on the individual procuring agency per-solicitation, not on TWC "
    "centrally. See firm/playbooks/pricing-data-sources.md -> 'Structural "
    "Note - Texas Prevailing Wage' for the full rationale. The per-project "
    "parser in core/pricing/sources/tx_prevailing_wage.py handles WD PDFs "
    "that arrive with each TX state-agency solicitation."
)

TARGET_AGENCIES: list[str] = [
    "TxDOT - Texas Department of Transportation",
    "TFC - Texas Facilities Commission",
    "TBPC - Texas Building & Procurement Commission (historical)",
    "TWDB - Texas Water Development Board",
    "UT System - Office of Facilities Planning & Construction",
    "Texas A&M System - Facilities Planning, Design & Construction",
    "Texas Tech System - Facilities Planning & Construction",
    "UH System - Office of Facilities Planning & Construction",
    "City of Houston / Dallas / San Antonio / Austin / Fort Worth / El Paso",
    "Harris / Dallas / Bexar / Travis / Tarrant Counties (incl. jail authorities)",
    "TDCJ - Texas Department of Criminal Justice",
    "HHSC - Health and Human Services Commission",
]


def harvest_recent_wds(*_args: object, **_kwargs: object) -> list[object]:
    """Future entry point — currently a deliberate ``NotImplementedError``."""
    raise NotImplementedError(ABSTRACT_REASON)


if __name__ == "__main__":
    print("core.pricing.sources.tx_agency_wd - PLACEHOLDER (future work)")
    print("=" * 72)
    print(ABSTRACT_REASON)
    print()
    print("Candidate target agencies for the future harvester:")
    for agency in TARGET_AGENCIES:
        print(f"  - {agency}")
