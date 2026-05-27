"""TX Workforce Commission prevailing wage adapter (Phase B — partial).

Source:     Texas Workforce Commission publishes per-county prevailing wage
            tables annually (and a state composite). Distribution is via PDF
            from https://www.twc.texas.gov/programs/wages/prevailing-wage
            and an XLSX from the TWC Labor Market Information portal.
License:    State of Texas public records — TWC Open Records policy applies.
            Tables are public-domain reference data for state-funded
            construction-prevailing-wage compliance.
ToS:        https://www.twc.texas.gov/twc-website-privacy-and-security-policy
            Polite use; cite source.

[Phase B — partial implementation]

What ships here:
- A working ``parse_wage_table_text`` that takes pre-extracted PDF text and
  returns ``PricingSnapshot``s. Driven by a per-county fixture PDF, the
  pipeline is: ``pymupdf`` -> raw text -> ``parse_wage_table_text``.
- ``fetch_from_pdf(pdf_path, *, county, year)`` wires the above to a local
  PDF file (no HTTP — TWC URLs require browsing through a search interface
  the public API does not expose cleanly).

What's NOT in scope until Phase B-full ships:
- Auto-download the per-county PDF from twc.texas.gov (their site uses a
  JavaScript search form that's not amenable to a polite HTTP fetch).
- A canonical SOC mapping for every TX trade label variant.
- A bundled offline-test fixture PDF (no public-domain TWC wage table is
  present in the repo today — see Open Item below).

TODO (Phase B-full):
- Add a bundled fixture under ``tests/fixtures/tx_twc_<county>_<year>.pdf``
  once the user provides one (or the agent extracts one from an active bid).
- Replace the brittle line-pattern parser with a `pymupdf.find_tables()`
  call once we have a fixture to verify against.
- Add a polite scraper for the TWC search results page.
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
    """Phase B partial — fetch is a no-op until auto-download lands."""

    name = "tx_prevailing_wage"
    requires_env_vars: list[str] = []
    license_str = "State of Texas public record — TWC prevailing wage"
    homepage_url = "https://www.twc.texas.gov/programs/wages/prevailing-wage"

    def default_series(self) -> list[str]:
        # Per-county PDFs aren't enumerable from a public index; callers pass
        # county names instead. Empty default list keeps the refresh runner
        # from invoking us automatically until the auto-download lands.
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        # [Phase B — not yet implemented] — auto-fetch from twc.texas.gov.
        # Use `fetch_from_pdf` for now when a local PDF is available.
        LOG.info(
            "TXPrevailingWageSource.fetch is a no-op until Phase B-full "
            "ships the TWC auto-downloader. Use fetch_from_pdf(...) directly."
        )
        return []
