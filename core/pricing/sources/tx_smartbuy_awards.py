"""TX SmartBuy / ESBD historical-awards scraper — Phase C (shipped 2026-05-28).

Source:     Electronic State Business Daily (ESBD), Texas Comptroller of
            Public Accounts.
            - https://www.txsmartbuy.gov/esbd                   (listing)
            - https://www.txsmartbuy.gov/esbd/<SOLICITATION>     (detail)
License:    State of Texas public record (Tex. Gov't Code Ch. 2155 et seq.,
            posted-bid-history is public information under the Texas Public
            Information Act, Tex. Gov't Code Ch. 552).
ToS:        https://comptroller.texas.gov/about/policies/website-policy.php
            Polite read-only use; no bulk download attempts; no aggressive
            parallel fetching. The 24h disk cache in ``_cci_common`` keeps
            our footprint minimal and is the canonical politeness control
            for this adapter.

What this adapter does
----------------------

The Comptroller publishes a public-record listing of every solicitation
issued by a Texas state agency over the procurement threshold. Once a
solicitation is awarded, the detail page is updated with a
"Solicitation Awards" / "Notice of Award" section listing the winning
vendor(s), award amount(s), award date, and contract performance period.

This adapter scrapes those award postings and emits one
``PricingSnapshot`` per (solicitation, awarded-vendor) pair. The dollar
amount is the award value (lump-sum total), NOT an index. Snapshots use
``unit="USD"`` so they are clearly distinguishable from the
ENR/AGC/Turner CCI macro index adapters that also live in this package.

This is **competitive intelligence**: a real prior-bid value for a Texas
state-agency contract with a known scope and NAICS, complementing the
macro CCI/PPI escalators (which tell you *trend*, not *level*).

Access posture (verified 2026-05-28)
------------------------------------

- Public, no auth required (the brief confirmed the verified-working
  ``26-007RFCSP`` detail-page URL earlier in this project).
- Polite ``User-Agent`` (inherited from ``base.build_client``).
- 24h disk cache (via ``_cci_common.http_get_text``); the cache lives
  under ``config/pricing_snapshots/_http_cache/tx_smartbuy_awards/``
  (gitignored).
- No bulk download: ``fetch_recent_awards()`` walks the first listing
  page only by default and is intended for batched periodic refreshes,
  not continuous polling. The ``limit`` argument caps the per-call work.

Snapshot shape
--------------
- source:        "tx_smartbuy_awards"
- series_id:     "<solicitation>" for single-vendor awards
                 "<solicitation>--<vendor_index>" for multi-vendor awards
                 (double-hyphen separator so single-hyphen sol numbers
                 like "26-007RFCSP" are unambiguously distinguishable
                 from the multi-vendor suffix)
- label:         "ESBD <sol> awarded to <vendor>"
- unit:          "USD"                # absolute dollars, not an index
- value:         <awarded amount>     # lump-sum award total
- region:        "TX"
- csi_division:  None                 # not derived (per brief)
- naics:         from the page, or None when absent
- period:        award month "YYYY-MM" (or "YYYY" if month unknown)
- license:       per ``license_str`` below; cite at every use
- source_url:    https://www.txsmartbuy.gov/esbd/<sol>
- raw:           {vendor, amount, award_date, sol_number, agency,
                  naics, performance_period} — small audit payload, no
                  raw HTML

Structural-fragility notes
--------------------------
ESBD HTML labels are not part of a stable API — the Comptroller has
historically tweaked the layout of the detail page without notice. The
adapter defends against this by:

1. Trying multiple label spellings per field (``Awarded Vendor:`` vs
   ``Vendor:`` vs ``Awardee:``; ``Award Amount:`` vs ``Awarded Amount:``
   vs ``Contract Amount:``) and accepting the first hit.
2. Stripping HTML tags before parsing so the regex anchors operate on
   rendered text — making the parser insensitive to whitespace, table
   vs. definition-list layout, and inline emphasis tags.
3. Skipping solicitations whose status is not "Awarded".
4. Skipping solicitations that have no parseable dollar amount (logs +
   omits, doesn't raise).
5. Returning an empty list from the abstract ``fetch()`` method on any
   HTTP error so ``scripts/refresh_pricing.py`` is never crashed. The
   explicit per-solicitation ``fetch_award()`` entry point DOES raise
   ``PricingSourceUnavailable`` on 4xx/5xx so callers that want hard
   failure (e.g. a one-off CLI lookup) can detect it.

If the ESBD HTML changes structurally — e.g. labels are renamed,
solicitation IDs move out of href slugs — the per-page parse will return
empty and the refresh runner will log a warning. Operators then look up
the award manually on ESBD and decide whether to extend the anchor
lists below or open a parser-fix branch. **No silent partial parsing**:
the adapter prefers returning nothing for a malformed page over emitting
a snapshot with a wrong vendor or amount.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import (
    PricingSourceUnavailable,
    http_get_text,
)
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


# --- URLs --------------------------------------------------------------

ESBD_BASE_URL = "https://www.txsmartbuy.gov/esbd"


def detail_url(solicitation_number: str) -> str:
    """Canonical ESBD detail-page URL for ``solicitation_number``.

    ESBD slugs are alphanumeric with dashes; we URL-quote defensively in
    case a future solicitation introduces an unsafe character but in
    practice every ID seen on the site is already URL-safe.
    """
    from urllib.parse import quote
    return f"{ESBD_BASE_URL}/{quote(str(solicitation_number).strip(), safe='-_./')}"


def listing_url(*, status: str = "Awarded", naics: Optional[str] = None) -> str:
    """Canonical ESBD listing-page URL filtered by status (+ optional NAICS).

    ESBD's listing page accepts ``?status=<value>`` and ``?naics=<code>``
    query parameters; tests assert the rendered URL shape. Both values
    are inserted verbatim — they are not user input but configured
    filter constants from the adapter call site.
    """
    from urllib.parse import urlencode
    params = {"status": status}
    if naics:
        params["naics"] = str(naics)
    return f"{ESBD_BASE_URL}?{urlencode(params)}"


# --- Label anchors -----------------------------------------------------

# Each list is ordered most-specific first. ``_find_after_label`` returns
# the first hit, so a "Awarded Vendor:" match wins over the looser
# "Vendor:" fallback when both are present.

VENDOR_LABELS = [
    "Awarded Vendor:",
    "Awarded Vendor",
    "Awardee:",
    "Awardee",
    "Awarded To:",
    "Awarded to:",
    "Awarded to",
    "Vendor Awarded:",
    "Vendor:",
]

AMOUNT_LABELS = [
    "Award Amount:",
    "Awarded Amount:",
    "Contract Amount:",
    "Award Total:",
    "Total Award:",
    "Amount:",
]

AWARD_DATE_LABELS = [
    "Award Date:",
    "Awarded Date:",
    "Date Awarded:",
    "Notice of Award Date:",
]

PERFORMANCE_LABELS = [
    "Performance Period:",
    "Contract Period:",
    "Contract Term:",
    "Term:",
]

NAICS_LABELS = [
    "NAICS Code:",
    "NAICS:",
]

AGENCY_LABELS = [
    "Issuing Agency:",
    "Agency:",
    "Agency/Texas SmartBuy Member Number:",
]

STATUS_LABELS = [
    "Status:",
    "Solicitation Status:",
]

SOLICITATION_ID_LABELS = [
    "Solicitation ID:",
    "Solicitation Number:",
    "Solicitation #:",
]

# Statuses other than "awarded" are filtered out — defensive even though
# the listing-page query usually does this for us.
NON_AWARDED_STATUSES = {
    "posted",
    "no award",
    "no-award",
    "closed",
    "posting cancelled",
    "cancelled",
    "canceled",
    "withdrawn",
}


# --- Dollar / date / NAICS parsers -------------------------------------

# Matches dollar amounts. Three shapes:
#   1) $1,234,567.89        comma-grouped with optional decimals
#   2) $1.23M / $1.5B       short-scale suffix
#   3) 1,234,567(.89)       bare number (no $ sign) — only accepted when
#                           the value passes the plausibility filter.
_DOLLAR_GROUPED_RE = re.compile(
    r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d{4,12}(?:\.\d{1,2})?)\b"
)
_DOLLAR_SHORTSCALE_RE = re.compile(
    r"\$\s?(\d+(?:\.\d+)?)\s?([MBK])\b",
    re.IGNORECASE,
)
_BARE_GROUPED_RE = re.compile(
    r"\b(\d{1,3}(?:,\d{3}){2,}(?:\.\d{1,2})?)\b"
)
_NAICS_RE = re.compile(r"\b(\d{6})\b")

# Plausibility window for a single TX state-agency award. The smallest
# practical award on ESBD is ~$25k (the posting threshold); we set the
# floor lower at $5k to comfortably admit smaller line items, and the
# ceiling at $5B to cover statewide multi-vendor IT contracts. Numbers
# outside this window are rejected as parser noise.
MIN_PLAUSIBLE_AWARD = 5_000.0
MAX_PLAUSIBLE_AWARD = 5_000_000_000.0


def parse_dollar_amount(text: str) -> Optional[float]:
    """Parse the first plausible dollar amount in ``text``.

    Order of preference (the first that succeeds wins):
      1. ``$1,234,567.89`` — explicit $-prefixed comma-grouped.
      2. ``$1.23M`` / ``$1.5B`` / ``$500K`` — short-scale suffix.
      3. ``1,234,567`` — bare comma-grouped number (requires at least
         two comma groups to avoid matching a quantity / count like
         ``1,200`` or a four-digit year). Must pass plausibility.

    Returns ``None`` if no match passes the plausibility filter.
    """
    if not text:
        return None

    m = _DOLLAR_GROUPED_RE.search(text)
    if m:
        try:
            val = float(m.group(1).replace(",", ""))
        except ValueError:
            val = None
        if val is not None and MIN_PLAUSIBLE_AWARD <= val <= MAX_PLAUSIBLE_AWARD:
            return val

    m = _DOLLAR_SHORTSCALE_RE.search(text)
    if m:
        try:
            base = float(m.group(1))
        except ValueError:
            base = None
        if base is not None:
            mult = {"k": 1_000.0, "m": 1_000_000.0, "b": 1_000_000_000.0}[m.group(2).lower()]
            val = base * mult
            if MIN_PLAUSIBLE_AWARD <= val <= MAX_PLAUSIBLE_AWARD:
                return val

    m = _BARE_GROUPED_RE.search(text)
    if m:
        try:
            val = float(m.group(1).replace(",", ""))
        except ValueError:
            val = None
        if val is not None and MIN_PLAUSIBLE_AWARD <= val <= MAX_PLAUSIBLE_AWARD:
            return val

    return None


_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_DATE_LONG_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"[,\.\s]+(\d{1,2})?[,\.\s]+(\d{4})\b",
    re.IGNORECASE,
)
_DATE_SLASH_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_DATE_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DATE_MONTH_YEAR_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"[,\.\s]+(\d{4})\b",
    re.IGNORECASE,
)


def parse_award_period(text: str) -> Optional[str]:
    """Parse an award date out of ``text`` and return "YYYY-MM" or "YYYY".

    Supported input shapes (first match wins):
      - ``December 15, 2025`` / ``Dec 15 2025``
      - ``12/15/2025``
      - ``2025-12-15``
      - ``December 2025`` (month + year only, no day)
      - bare 4-digit year as last resort

    Returns ``None`` if no date-like token is found.
    """
    if not text:
        return None

    m = _DATE_LONG_RE.search(text)
    if m:
        name = m.group(1).lower()
        mo = _MONTH_NAMES.get(name) or _MONTH_NAMES.get(name[:3])
        year = m.group(3)
        if mo:
            return f"{year}-{mo:02d}"

    m = _DATE_SLASH_RE.search(text)
    if m:
        try:
            mo = int(m.group(1))
            year = m.group(3)
            if 1 <= mo <= 12:
                return f"{year}-{mo:02d}"
        except ValueError:
            pass

    m = _DATE_ISO_RE.search(text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    m = _DATE_MONTH_YEAR_RE.search(text)
    if m:
        name = m.group(1).lower()
        mo = _MONTH_NAMES.get(name) or _MONTH_NAMES.get(name[:3])
        year = m.group(2)
        if mo:
            return f"{year}-{mo:02d}"

    # Bare year fallback.
    bare = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if bare:
        return bare.group(1)

    return None


# --- HTML helpers ------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_ENTITY_RE = re.compile(r"&(amp|lt|gt|quot|apos|nbsp|#\d+);")
_WS_RE = re.compile(r"[ \t]+")
_NL_RE = re.compile(r"\s*\n\s*")
_ENTITY_MAP = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&apos;": "'", "&nbsp;": " ",
}


def html_to_text(html: str) -> str:
    """Strip HTML tags and decode the common entities to a flat text blob.

    We deliberately do not pull in BeautifulSoup or lxml — per the
    project's no-new-deps constraint. The label-anchor regex parser
    downstream is whitespace-tolerant, so a naive tag-strip + entity
    decode is sufficient.
    """
    if not html:
        return ""
    # Strip script/style blocks entirely so their contents don't bleed
    # into the parsed text.
    cleaned = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    cleaned = _HTML_ENTITY_RE.sub(
        lambda m: _ENTITY_MAP.get(m.group(0), " "), cleaned,
    )
    cleaned = _WS_RE.sub(" ", cleaned)
    cleaned = _NL_RE.sub("\n", cleaned)
    return cleaned.strip()


def _find_after_label(
    text: str,
    labels: list[str],
    *,
    window: int = 200,
) -> Optional[str]:
    """Return the substring immediately following the first matched label.

    Searches ``text`` case-insensitively for each label in ``labels`` (in
    order, most-specific first). Returns the ``window`` characters that
    follow the first hit, lightly trimmed. Returns ``None`` if no label
    appears in ``text``.
    """
    if not text:
        return None
    lower = text.lower()
    for label in labels:
        idx = lower.find(label.lower())
        if idx != -1:
            after = text[idx + len(label) : idx + len(label) + window]
            # Trim line-breaks so the snippet stays focused on the
            # immediately-following field value.
            after = after.strip()
            return after
    return None


def _find_all_label_positions(text: str, labels: list[str]) -> list[int]:
    """Return every start index in ``text`` where any of ``labels`` appears.

    Overlap-safe: a short alias ("Vendor:") will NOT double-count a
    position already covered by a longer label ("Awarded Vendor:")
    because labels are processed longest-first and any subsequent match
    whose start falls inside an already-consumed [start,end) range is
    dropped. This is critical for the block-splitting algorithm — a
    single-vendor page must produce exactly one award block.
    """
    if not text:
        return []
    lower = text.lower()
    sorted_labels = sorted(labels, key=lambda x: -len(x))
    consumed: list[tuple[int, int]] = []
    out: list[int] = []
    for label in sorted_labels:
        ll = label.lower()
        start = 0
        while True:
            idx = lower.find(ll, start)
            if idx == -1:
                break
            end = idx + len(ll)
            inside_existing = any(
                cs <= idx < ce for cs, ce in consumed
            )
            if not inside_existing:
                out.append(idx)
                consumed.append((idx, end))
            start = idx + 1
    return sorted(set(out))


# --- Listing-page parsing ---------------------------------------------

# Detail-page links on the listing have the shape href="/esbd/<id>" or
# href="https://www.txsmartbuy.gov/esbd/<id>". We capture both.
_DETAIL_HREF_RE = re.compile(
    r"""href\s*=\s*["'](?:https?://www\.txsmartbuy\.gov)?/esbd/([^"'?#/\s][^"'?#\s]*)["']""",
    re.IGNORECASE,
)


def parse_listing_for_solicitation_numbers(
    html: str, *, limit: Optional[int] = None,
) -> list[str]:
    """Pull solicitation IDs from a listing-page HTML response.

    Two extraction methods, used in order:
      1. ``href="/esbd/<id>"`` links.
      2. ``Solicitation ID:`` labels in the rendered text.

    De-duplicated; order is preserved. Stops at ``limit`` solicitations
    if ``limit`` is given.
    """
    if not html:
        return []

    seen: set[str] = set()
    out: list[str] = []

    for m in _DETAIL_HREF_RE.finditer(html):
        sol = m.group(1).strip().rstrip("/")
        if not sol or sol in seen:
            continue
        # Skip non-solicitation paths that happen to live under /esbd/
        # (e.g. /esbd/help, /esbd/about). Solicitation IDs typically
        # contain a digit; pure-letter paths are page navigation.
        if not any(c.isdigit() for c in sol):
            continue
        seen.add(sol)
        out.append(sol)
        if limit and len(out) >= limit:
            return out

    text = html_to_text(html)
    for pos in _find_all_label_positions(text, SOLICITATION_ID_LABELS):
        snippet = text[pos : pos + 200]
        # Everything after the colon, first token.
        after = snippet.split(":", 1)[-1].strip()
        # First whitespace-bounded token that contains a digit.
        for tok in after.split():
            tok = tok.strip(",.;")
            if tok and any(c.isdigit() for c in tok):
                if tok not in seen:
                    seen.add(tok)
                    out.append(tok)
                break
        if limit and len(out) >= limit:
            return out

    return out


# --- Detail-page parsing ----------------------------------------------

def _split_into_award_blocks(text: str) -> list[str]:
    """Partition ``text`` into one block per (vendor) award.

    Strategy: locate every vendor-label position, then carve the text
    between consecutive vendor anchors. Each resulting block contains
    one vendor's award details (vendor name + nearest forward amount +
    nearest forward date). Leading-pre-first-vendor text is discarded.

    Single-vendor pages produce a single block; multi-vendor pages
    produce N blocks.
    """
    positions = _find_all_label_positions(text, VENDOR_LABELS)
    if not positions:
        return []
    out: list[str] = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        out.append(text[pos:end])
    return out


def _extract_value_after_label(block: str, labels: list[str]) -> Optional[str]:
    """Inside ``block``, return the value text after the first matched label.

    Strips the label itself + the colon + any leading punctuation. The
    returned value is bounded by the next label, the next newline, or
    100 chars — whichever comes first — so a vendor name like
    "ABC Construction LLC" doesn't accidentally absorb the next field.
    """
    if not block:
        return None
    lower = block.lower()
    for label in labels:
        idx = lower.find(label.lower())
        if idx == -1:
            continue
        after_label = block[idx + len(label) :]
        # Trim leading ":" and whitespace.
        after_label = after_label.lstrip(" :\t\r\n")
        # Stop at the next label boundary. We scan a fixed window for
        # the next label-y token.
        window = after_label[:300]
        stop = len(window)
        for next_lab in (
            VENDOR_LABELS + AMOUNT_LABELS + AWARD_DATE_LABELS +
            PERFORMANCE_LABELS + NAICS_LABELS + AGENCY_LABELS +
            STATUS_LABELS + SOLICITATION_ID_LABELS
        ):
            if next_lab.lower() == label.lower():
                continue
            ix = window.lower().find(next_lab.lower())
            if ix != -1 and ix < stop:
                stop = ix
        # Also stop at the first newline.
        nl = window.find("\n")
        if nl != -1 and nl < stop:
            stop = nl
        value = window[:stop].strip().strip(",;")
        # Collapse internal whitespace.
        value = _WS_RE.sub(" ", value).strip()
        return value or None
    return None


def parse_award_detail_page(
    html: str,
    solicitation_number: str,
    *,
    source_url: str,
    license_str: str,
    adapter_name: str,
) -> list[PricingSnapshot]:
    """Parse an ESBD detail-page HTML response into snapshots.

    Returns one ``PricingSnapshot`` per awarded vendor. Returns ``[]`` if
    the page does not represent an awarded solicitation, or if no
    award block can be parsed.
    """
    if not html:
        return []
    text = html_to_text(html)
    if not text:
        return []

    # Status filter — defensive, in case a non-awarded solicitation
    # slips through the listing-page query.
    status_value = _find_after_label(text, STATUS_LABELS, window=60)
    if status_value:
        normalized = status_value.strip().lower()
        # Trim trailing fields/punctuation that came along with the
        # status token.
        normalized = normalized.split("\n")[0].strip(" .,;:")
        for bad in NON_AWARDED_STATUSES:
            if normalized.startswith(bad):
                LOG.debug(
                    "TX SmartBuy: solicitation %s status %r is not awarded; "
                    "skipping",
                    solicitation_number, status_value,
                )
                return []

    naics = None
    naics_text = _find_after_label(text, NAICS_LABELS, window=20)
    if naics_text:
        m = _NAICS_RE.search(naics_text)
        if m:
            naics = m.group(1)

    agency = _find_after_label(text, AGENCY_LABELS, window=120)
    if agency:
        agency = agency.split("\n")[0].strip()
        # Strip trailing follow-on field labels that may have been
        # captured in the window.
        agency = re.split(
            r"\b(Status|NAICS|Solicitation|Award)\b", agency, maxsplit=1,
        )[0].strip(" -:,")
    performance_period = _find_after_label(
        text, PERFORMANCE_LABELS, window=120,
    )
    if performance_period:
        performance_period = performance_period.split("\n")[0].strip()

    blocks = _split_into_award_blocks(text)
    if not blocks:
        LOG.debug(
            "TX SmartBuy: no vendor-award block found on %s — skipping",
            source_url,
        )
        return []

    snapshots: list[PricingSnapshot] = []
    fetched_at = datetime.now(timezone.utc)

    for i, block in enumerate(blocks):
        vendor = _extract_value_after_label(block, VENDOR_LABELS)
        if not vendor:
            continue
        amount_str = _extract_value_after_label(block, AMOUNT_LABELS)
        if not amount_str:
            LOG.info(
                "TX SmartBuy: solicitation %s vendor %r has no parseable "
                "award amount — skipping vendor",
                solicitation_number, vendor,
            )
            continue
        amount = parse_dollar_amount(amount_str)
        if amount is None:
            LOG.info(
                "TX SmartBuy: solicitation %s vendor %r amount text %r "
                "did not pass plausibility filter — skipping vendor",
                solicitation_number, vendor, amount_str,
            )
            continue

        date_str = _extract_value_after_label(block, AWARD_DATE_LABELS)
        period = parse_award_period(date_str) if date_str else None
        if period is None:
            period = parse_award_period(text) or f"{fetched_at.year}"

        suffix = "" if len(blocks) == 1 else f"--{i + 1}"
        series_id = f"{solicitation_number}{suffix}"
        label = f"ESBD {solicitation_number} awarded to {vendor}"

        snapshots.append(
            PricingSnapshot(
                source=adapter_name,
                series_id=series_id,
                label=label,
                unit="USD",
                value=float(amount),
                region="TX",
                csi_division=None,
                naics=naics,
                period=period,
                fetched_at=fetched_at,
                license=license_str,
                source_url=source_url,
                raw={
                    "solicitation_number": solicitation_number,
                    "vendor": vendor,
                    "award_amount_usd": float(amount),
                    "award_amount_raw": amount_str,
                    "award_date_raw": date_str,
                    "agency": agency,
                    "naics": naics,
                    "performance_period": performance_period,
                    "vendor_index": i + 1,
                    "vendor_count": len(blocks),
                },
            )
        )

    return snapshots


# --- Adapter -----------------------------------------------------------


class TXSmartBuyAwardsSource(PricingSource):
    """TX SmartBuy / ESBD historical-awards adapter.

    The award postings are competitive intelligence — one snapshot per
    (solicitation, awarded-vendor) pair, ``unit="USD"``, the lump-sum
    award value. See the module docstring for the full contract.
    """

    name = "tx_smartbuy_awards"
    requires_env_vars: list[str] = []
    license_str = "State of Texas public record — TX SmartBuy / ESBD"
    homepage_url = ESBD_BASE_URL

    # Default recent-awards batch size for ``fetch()`` and the refresh
    # script. The brief calls for 50 as a reasonable per-refresh batch.
    DEFAULT_RECENT_LIMIT = 50

    def default_series(self) -> list[str]:
        # ESBD is awards-driven, not series-driven: there is no curated
        # canonical list of solicitation numbers. The refresh runner
        # pulls the most recent N awarded solicitations via
        # ``fetch_recent_awards()`` instead.
        return []

    # --- public entry points -----------------------------------------

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        """Generic-shape entry point used by ``scripts/refresh_pricing.py``.

        Behavior:
          - If ``series_ids`` is non-empty, each id is treated as an
            explicit solicitation number and fetched via
            ``fetch_award()``. Per-solicitation HTTP errors are
            swallowed and logged.
          - If ``series_ids`` is empty, walks the listing page filtered
            by status=Awarded and returns the most-recent
            ``limit`` (default ``DEFAULT_RECENT_LIMIT``) solicitations.

        Never raises; the refresh runner is never crashed by this
        adapter. Filters honored:
          - ``limit`` (int): cap on the recent-awards scan.
          - ``naics`` (str): NAICS filter passed to the listing page.
        """
        snapshots: list[PricingSnapshot] = []
        if series_ids:
            for sol in series_ids:
                try:
                    snapshots.extend(self.fetch_award(sol))
                except PricingSourceUnavailable as exc:
                    LOG.warning(
                        "TX SmartBuy fetch_award(%r) failed: %s",
                        sol, exc,
                    )
                except Exception as exc:  # noqa: BLE001
                    LOG.warning(
                        "TX SmartBuy fetch_award(%r) unexpected error: %s",
                        sol, exc,
                    )
            return snapshots

        # No explicit series — scan recent awards.
        limit_raw = filters.get("limit", self.DEFAULT_RECENT_LIMIT)
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError):
            limit = self.DEFAULT_RECENT_LIMIT
        naics = filters.get("naics")
        try:
            return self.fetch_recent_awards(limit=limit, naics=naics)
        except PricingSourceUnavailable as exc:
            LOG.warning("TX SmartBuy fetch_recent_awards failed: %s", exc)
            return []
        except Exception as exc:  # noqa: BLE001
            LOG.warning(
                "TX SmartBuy fetch_recent_awards unexpected error: %s", exc,
            )
            return []

    def fetch_latest(self) -> list[PricingSnapshot]:
        """Return the most-recent batch of awarded snapshots.

        Defaults to ``fetch_recent_awards(limit=25)``. Returns ``[]`` on
        any HTTP error.
        """
        try:
            return self.fetch_recent_awards(limit=25)
        except PricingSourceUnavailable as exc:
            LOG.warning("TX SmartBuy fetch_latest failed: %s", exc)
            return []

    def fetch_award(self, solicitation_number: str) -> list[PricingSnapshot]:
        """Fetch + parse a single ESBD detail page.

        Returns one snapshot per awarded vendor (empty if the page
        cannot be parsed into at least one valid (vendor, amount)
        pair).

        Raises ``PricingSourceUnavailable`` on HTTP 4xx/5xx. This is
        the explicit per-solicitation entry point — callers that want a
        non-raising version should go through ``fetch([sol])``.
        """
        sol = str(solicitation_number).strip()
        if not sol:
            raise PricingSourceUnavailable(
                "TX SmartBuy: empty solicitation_number"
            )
        url = detail_url(sol)
        try:
            html = http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            raise PricingSourceUnavailable(
                f"TX SmartBuy: HTTP error fetching {url}: {exc}"
            ) from exc

        return parse_award_detail_page(
            html,
            solicitation_number=sol,
            source_url=url,
            license_str=self.license_str,
            adapter_name=self.name,
        )

    def fetch_recent_awards(
        self,
        limit: int = DEFAULT_RECENT_LIMIT,
        *,
        naics: Optional[str] = None,
    ) -> list[PricingSnapshot]:
        """Scan the ESBD listing page for awarded solicitations.

        Walks the first listing page only — no pagination. For each
        solicitation found, calls ``fetch_award()``. Per-solicitation
        HTTP errors are swallowed and logged so a single broken detail
        page does not abort the scan.

        Raises ``PricingSourceUnavailable`` if the listing page itself
        cannot be fetched. NAICS filter (when supplied) is passed
        through to the listing URL.
        """
        url = listing_url(status="Awarded", naics=naics)
        try:
            html = http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            raise PricingSourceUnavailable(
                f"TX SmartBuy: HTTP error fetching listing {url}: {exc}"
            ) from exc

        sol_numbers = parse_listing_for_solicitation_numbers(
            html, limit=max(0, int(limit)),
        )
        out: list[PricingSnapshot] = []
        for sol in sol_numbers:
            try:
                out.extend(self.fetch_award(sol))
            except PricingSourceUnavailable as exc:
                LOG.info(
                    "TX SmartBuy: skipping solicitation %s (%s)", sol, exc,
                )
            except Exception as exc:  # noqa: BLE001
                LOG.info(
                    "TX SmartBuy: skipping solicitation %s (unexpected: %s)",
                    sol, exc,
                )
        return out
