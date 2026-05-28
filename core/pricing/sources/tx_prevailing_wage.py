"""Texas state-agency prevailing-wage WD parser — per-project (Ch. 2258).

Statutory framework
-------------------
Under **Tex. Gov't Code Ch. 2258 ("Prevailing Wage Rates")**, the general
prevailing rate of per diem wages for a Texas public-works contract is
determined and published by the **individual procuring public body** (the
contracting state agency, university system, county jail authority, or
political subdivision) — **NOT** by the Texas Workforce Commission centrally.
Each agency must publish its wage schedule *as part of each solicitation* and
incorporate it into the resulting contract.

What this module is (and isn't)
-------------------------------
**This parser handles project-specific WD PDFs that arrive as solicitation
attachments from TX state agencies.** It is NOT a centralized TWC source —
there is no centralized TWC per-county WD repository to fetch from (and
earlier roadmap entries that assumed one were based on a faulty premise).

For federally-funded TX work (Davis-Bacon Act, McNamara-O'Hara Service
Contract Act, federal-aid highway projects, HUD-assisted projects, etc.),
use ``core/pricing/sources/davis_bacon.py`` instead — that one IS centralized
via the SAM.gov Wage Determination library.

For the full structural rationale (why TWC is not a central source, why the
per-project workflow is correct, what a future per-agency harvester would
look like, and which TX agencies it would target) see:

    firm/playbooks/pricing-data-sources.md
        ^ section "Structural Note — Texas Prevailing Wage"

And the placeholder for the future per-agency harvester:

    core/pricing/sources/tx_agency_wd.py

The expected operator workflow
------------------------------
1. WD PDF arrives with the solicitation (RFP / RFQ / CSP / RFCSP / IFB).
2. Operator drops it into ``bids/<slug>/wage-determination/``.
3. Call ``fetch_from_pdf(pdf_path, county=..., year=...)`` (or
   ``parse_wage_table_text(...)`` for pre-extracted text) to produce
   ``PricingSnapshot``s tagged with the source solicitation context.
4. Snapshots participate in the same escalation + CWICR matching workflow
   as the centralized federal Davis-Bacon snapshots.

License / source
----------------
License:    State of Texas public records — Ch. 2258 wage schedules attached
            to TX state-agency solicitations are public records under the
            Texas Public Information Act (Gov't Code Ch. 552).
ToS:        Per the issuing agency's terms when downloading from its
            solicitation portal. Polite use; cite the source solicitation.

What ships here
---------------
- ``parse_wage_table_text(text, *, county, year, source_url="")`` — takes
  pre-extracted PDF text and returns ``PricingSnapshot``s. Pipeline:
  ``pymupdf`` -> raw text -> ``parse_wage_table_text``.
- ``fetch_from_pdf(pdf_path, *, county, year)`` — wires the above to a local
  PDF file already on disk in the bid workspace.
- ``TXPrevailingWageSource`` — a ``PricingSource`` shell whose ``fetch()`` is
  a deliberate no-op because there is nothing centralized to fetch from;
  per-project use should call ``fetch_from_pdf`` directly.

Known limitations (acceptable; per-project workflow remains correct)
--------------------------------------------------------------------
- No canonical SOC mapping for every TX trade label variant; we fall back to
  the Davis-Bacon classification-to-SOC mapping in ``davis_bacon.py``.
- The line-pattern parser is intentionally permissive because each TX agency
  formats its WD attachment slightly differently. The parser drops lines it
  cannot confidently classify rather than guessing.
- No bundled fixture PDF in the repo (TX state-agency WDs are public records
  but are tied to specific solicitations; a bid-time fixture would couple
  the test suite to a specific opportunity).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource
from core.pricing.sources.davis_bacon import map_classification_to_soc

LOG = logging.getLogger(__name__)


# Match lines like "CARPENTER                28.41  4.25  32.66" — and the
# permissive variants TWC uses ("LABORER (Common)", "ELECTRICIAN, JOURNEYMAN").
# We anchor the trade name on a leading uppercase letter (to skip the
# header / footnote text) but otherwise let it be any non-digit char.
_WAGE_LINE_RE = re.compile(
    r"^(?P<trade>[A-Z][^\d\n]{3,80}?)\s{2,}"
    r"\$?(?P<base>\d{1,3}\.\d{2})"
    r"(?:\s+\$?(?P<fringe>\d{1,3}\.\d{2}))?"
    r"(?:\s+\$?(?P<total>\d{1,3}\.\d{2}))?\s*$"
)


def parse_wage_table_text(
    text: str,
    *,
    county: str,
    year: int | str,
    source_url: str = "",
) -> list[PricingSnapshot]:
    """Parse raw text extracted from a TWC wage-table PDF into snapshots.

    The parser is intentionally permissive — TWC reformats every few years,
    so we extract whatever lines match the basic "trade   $rate" pattern and
    drop the rest. Each parsed line yields one PricingSnapshot.
    """
    out: list[PricingSnapshot] = []
    fetched_at = datetime.now(timezone.utc)
    period = str(year)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = _WAGE_LINE_RE.match(line)
        if not m:
            continue
        trade = re.sub(r"\s+", " ", m.group("trade")).strip(" -,/&")
        try:
            base = float(m.group("base"))
        except (TypeError, ValueError):
            continue
        # Prefer the "total" column (base + fringe) when present.
        rate: Optional[float] = None
        if m.group("total"):
            try:
                rate = float(m.group("total"))
            except (TypeError, ValueError):
                rate = None
        if rate is None:
            fringe = m.group("fringe")
            if fringe:
                try:
                    rate = base + float(fringe)
                except (TypeError, ValueError):
                    rate = base
            else:
                rate = base
        soc = map_classification_to_soc(trade)
        county_safe = county.replace(" ", "_")
        out.append(
            PricingSnapshot(
                source="tx_prevailing_wage",
                series_id=f"{county_safe}__{trade.replace(' ', '_')}",
                label=f"{trade} — {county} County, TX (TWC)",
                unit="USD/hr",
                value=rate,
                region=f"TX-{county}",
                csi_division="01",
                soc_code=soc,
                period=period,
                fetched_at=fetched_at,
                license="State of Texas public record — TWC prevailing wage",
                source_url=source_url or "https://www.twc.texas.gov/programs/wages/prevailing-wage",
                raw={"trade": trade, "base": base,
                     "fringe": m.group("fringe"), "total": m.group("total")},
            )
        )
    return out


def fetch_from_pdf(
    pdf_path: Path, *, county: str, year: int | str,
    source_url: str = "",
) -> list[PricingSnapshot]:
    """Parse a local TWC PDF (pymupdf is already a project dep)."""
    try:
        import pymupdf  # type: ignore[import-not-found]
    except ImportError:
        try:
            import fitz as pymupdf  # type: ignore[import-not-found, no-redef]
        except ImportError:
            LOG.warning("pymupdf not installed; cannot parse TX wage PDF.")
            return []

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        LOG.warning("TX wage PDF not found: %s", pdf_path)
        return []

    text_parts: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    return parse_wage_table_text(
        "\n".join(text_parts),
        county=county, year=year,
        source_url=source_url or f"file://{pdf_path}",
    )


class TXPrevailingWageSource(PricingSource):
    """``PricingSource`` shell for TX state-agency prevailing wage.

    ``fetch()`` is a deliberate no-op: under Tex. Gov't Code Ch. 2258,
    prevailing wage on a TX public-works contract is set per-project by the
    individual procuring agency. There is no centralized TWC repository to
    pull from. Per-project use should call ``fetch_from_pdf`` directly
    against the WD PDF that arrives with each solicitation.

    See the module docstring (and the ``firm/playbooks/pricing-data-sources.md``
    "Structural Note — Texas Prevailing Wage" callout) for the full rationale.
    """

    name = "tx_prevailing_wage"
    requires_env_vars: list[str] = []
    license_str = "State of Texas public record — Ch. 2258 per-project WD"
    homepage_url = "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.2258.htm"

    def default_series(self) -> list[str]:
        # Per-project WDs aren't enumerable from any centralized public index
        # — by statute, each TX procuring agency publishes its own per
        # solicitation. Empty default list keeps the refresh runner from
        # invoking us automatically; per-project callers use fetch_from_pdf.
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        # Deliberate no-op — Ch. 2258 is per-project, not centralized.
        # Use `fetch_from_pdf(pdf_path, county=..., year=...)` against the
        # WD PDF attached to the specific TX state-agency solicitation.
        LOG.info(
            "TXPrevailingWageSource.fetch is a no-op by design: Tex. Gov't "
            "Code Ch. 2258 places prevailing-wage publication on the "
            "individual procuring agency per-solicitation, not on TWC "
            "centrally. Use fetch_from_pdf(...) against the per-project "
            "WD PDF. See firm/playbooks/pricing-data-sources.md."
        )
        return []
