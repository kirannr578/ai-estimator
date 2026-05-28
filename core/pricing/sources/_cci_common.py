"""Shared helpers for Construction Cost Index (CCI) adapters — Phase C.

The three CCI source adapters (``enr_cci``, ``agc_cci``, ``turner_cci``)
all need to:

1. Fetch an HTML page (not JSON). The base class's ``http_get`` /
   ``http_post_json`` are JSON-only because every Phase A / B source returns
   JSON; CCI publishers do not. We add a separate text-mode fetcher here so
   ``base.py`` and the frozen Phase A / B adapters remain untouched.
2. Reuse base.py's polite User-Agent, TLS verification, 24h disk cache, and
   ``httpx.MockTransport``-friendly client construction — by accepting an
   ``httpx.Client`` argument the test suite can inject offline.
3. Search the response text for an index value + a reporting period using a
   small set of configurable anchor strings + lightweight regex.

This module deliberately ships as ``_cci_common`` (leading underscore) to
signal that it is private to the three CCI adapters and not part of the
public ``PricingSource`` contract.

License + scrape posture
------------------------
Each of the three CCI publishers (ENR, AGC, Turner) places attribution
requirements on the index values they publish. The per-adapter module
docstrings cite the source URL in each PricingSnapshot; this helper only
provides the plumbing. No HTML is ever persisted into a PricingSnapshot —
the raw response stays in the 24h disk cache under
``config/pricing_snapshots/_http_cache/<source>/`` (gitignored), and only
the parsed numeric value + period + source URL reach the snapshot JSON.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

import httpx

from core.pricing.sources.base import CACHE_TTL_SECONDS, _is_fresh

LOG = logging.getLogger(__name__)


class PricingSourceUnavailable(RuntimeError):
    """Raised by a CCI adapter when the public source page can't be parsed.

    The Phase A / B adapters generally swallow upstream failures and return
    an empty list so the refresh runner keeps going. The CCI adapters
    expose this exception on the ``fetch_latest()`` happy-path entry point
    for callers that want hard failure (e.g. the escalation engine), and
    still return an empty list from the abstract-class ``fetch()`` method
    so ``scripts/refresh_pricing.py`` is unaffected.
    """


def _cache_path(cache_root: Path, source_name: str, url: str) -> Path:
    """Stable cache filename for a GET of ``url`` under ``cache_root``."""
    digest = hashlib.sha256(f"GET\n{url}".encode("utf-8")).hexdigest()
    return cache_root / source_name / f"{digest}.txt"


def http_get_text(
    client: httpx.Client,
    cache_root: Path,
    source_name: str,
    url: str,
    *,
    ttl_seconds: int = CACHE_TTL_SECONDS,
) -> str:
    """GET ``url`` and return the response body as text.

    Cached on disk for ``ttl_seconds`` seconds (default 24h, mirroring
    ``base.py``'s CACHE_TTL_SECONDS). Raises ``httpx.HTTPStatusError`` on
    4xx / 5xx so callers can decide whether to log + swallow or propagate.
    """
    path = _cache_path(cache_root, source_name, url)
    if _is_fresh(path, ttl_seconds):
        try:
            LOG.debug("%s text-cache HIT %s", source_name, url)
            return path.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            # Cache file corrupt or unreadable: fall through to live fetch
            # rather than crashing the refresh runner.
            pass

    LOG.debug("%s text-cache MISS %s", source_name, url)
    resp = client.get(url)
    resp.raise_for_status()
    text = resp.text or ""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError:
        # A read-only cache_root (CI sandbox, immutable container layer) is
        # acceptable; the fetch already succeeded, the next call will just
        # re-fetch instead of cache-hitting.
        LOG.debug("%s text-cache write failed at %s (read-only?)", source_name, path)

    return text


# Number patterns. CCI index values are typically four-to-five digits (ENR ~
# 14000, Turner BCI ~ 1500), but AGC's PPI-style headline can also include
# small decimals like "8.2%" YoY changes. We match both shapes and let the
# caller's plausibility filter (``min_value``) discriminate.
_NUM_RE = re.compile(
    r"\b(\d{1,3}(?:,\d{3})*(?:\.\d{1,3})?|\d{1,5}(?:\.\d{1,3})?)\b"
)


def find_index_value(
    text: str,
    anchors: list[str],
    *,
    window: int = 600,
    min_value: float = 50.0,
    max_value: float = 1_000_000.0,
    exclude_year_range: tuple[int, int] = (1900, 2100),
) -> Optional[float]:
    """Locate a plausible index value near one of the ``anchors``.

    Walks ``text`` left-to-right and, for each anchor, searches the next
    ``window`` characters for a number in ``[min_value, max_value]``. The
    first such number wins.

    ``min_value`` defaults to 50 to filter out percent-change figures and
    table headers like "1" / "20-city"; tune downward in adapters that
    legitimately publish small values (none of ENR / AGC / Turner do for
    their headline index, but AGC's percent-change figures would need a
    different anchor + a smaller min_value if we ever needed them).

    ``exclude_year_range`` skips bare integers that look like years (default
    1900–2100). Without this filter ENR's "Construction Cost Index for
    April 2026 was 14021.34" would return 2026 — the first number found
    after the anchor — instead of 14021.34. Set to ``(0, 0)`` to disable
    the filter if a real index value ever lands in the year range.
    """
    if not text:
        return None
    y_lo, y_hi = exclude_year_range
    lower = text.lower()
    for anchor in anchors:
        a_low = anchor.lower()
        idx = lower.find(a_low)
        while idx != -1:
            snippet = text[idx + len(anchor) : idx + len(anchor) + window]
            for m in _NUM_RE.finditer(snippet):
                num_str = m.group(1).replace(",", "")
                try:
                    val = float(num_str)
                except ValueError:
                    continue
                if not (min_value <= val <= max_value):
                    continue
                # Skip bare integers that look like a year (4-digit, in
                # the configured exclusion range, no decimal point). A
                # value like 14021.34 has a decimal and is not a year;
                # a value like 1532 (Turner TBCI) is below 1900 and is
                # not flagged either.
                if (
                    y_lo <= val <= y_hi
                    and val == int(val)
                    and "." not in num_str
                    and y_lo > 0
                ):
                    continue
                return val
            idx = lower.find(a_low, idx + 1)
    return None


_MONTH_FULL = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
_MONTH_ABBREV = {k[:3]: v for k, v in _MONTH_FULL.items()}

_WORD_QUARTERS = {"first": 1, "second": 2, "third": 3, "fourth": 4}

_QUARTER_RE = re.compile(
    r"(?:"
    r"q([1-4])\s+(\d{4})"
    r"|([1-4])q\s+(\d{4})"
    r"|([1-4])(?:st|nd|rd|th)\s+quarter[,\s]+(\d{4})"
    r"|(first|second|third|fourth)\s+quarter[,\s]+(\d{4})"
    r")",
    re.IGNORECASE,
)
_MONTH_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"[,\.\s]+(\d{4})\b",
    re.IGNORECASE,
)
_ISO_RE = re.compile(r"\b(\d{4})-(0[1-9]|1[0-2])\b")


def _quarter_match_to_period(match: re.Match) -> Optional[str]:
    for q_grp, y_grp in ((1, 2), (3, 4), (5, 6), (7, 8)):
        q_val = match.group(q_grp)
        y_val = match.group(y_grp)
        if q_val and y_val:
            qkey = q_val.lower()
            q_num = _WORD_QUARTERS.get(qkey)
            if q_num is None:
                try:
                    q_num = int(q_val)
                except ValueError:
                    return None
            return f"{y_val}-Q{q_num}"
    return None


def parse_period(
    text: str, *, prefer_quarterly: bool = False
) -> Optional[str]:
    """Search ``text`` for the most recent reporting period referenced.

    Returns "YYYY-MM" for monthly references and "YYYY-QN" for quarterly.
    The first matching period encountered (top-to-bottom of the page) wins,
    because article pages typically lead with the latest figure.

    ``prefer_quarterly=True`` tips the order: if both a month and a quarter
    are present (e.g. "Q1 2026 cost report ... released in April 2026") the
    quarterly form is returned.
    """
    if not text:
        return None

    q_match = _QUARTER_RE.search(text)
    m_match = _MONTH_RE.search(text)
    iso_match = _ISO_RE.search(text)

    if prefer_quarterly and q_match:
        period = _quarter_match_to_period(q_match)
        if period:
            return period

    if m_match:
        name = m_match.group(1).lower()
        mo = _MONTH_FULL.get(name)
        if mo is None:
            mo = _MONTH_ABBREV.get(name[:3])
        year = m_match.group(2)
        if mo:
            return f"{year}-{mo:02d}"

    if iso_match:
        return f"{iso_match.group(1)}-{iso_match.group(2)}"

    if q_match:
        return _quarter_match_to_period(q_match)

    return None


def fallback_period_monthly(now=None) -> str:
    """Best-effort current-month period for adapters that have no published date."""
    from datetime import datetime, timezone
    n = now or datetime.now(timezone.utc)
    return f"{n.year}-{n.month:02d}"


def fallback_period_quarterly(now=None) -> str:
    """Best-effort current-quarter period for adapters that have no published date."""
    from datetime import datetime, timezone
    n = now or datetime.now(timezone.utc)
    q = (n.month - 1) // 3 + 1
    return f"{n.year}-Q{q}"
