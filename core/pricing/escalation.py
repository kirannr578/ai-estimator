"""Escalation engine.

Reads ``config/cost_database.json`` (the BPC seed cost DB), applies PPI deltas
commodity-by-commodity using a CSI-division-aware mapping, and writes the
result to ``config/cost_database_escalated.json`` (or wherever the caller
points). The original input file is never modified.

PPI series for each cost-DB entry are picked in the following priority:

  1. Exact CSI-section override in `_CSI_SECTION_TO_PPI`.
  2. Keyword match against `_KEYWORD_TO_PPI` (longest-keyword-first).
  3. CSI-division fallback in `_CSI_DIVISION_TO_PPI`.
  4. Generic "inputs to construction industries" PPI (`WPUSI012011`).

When ``base_period == target_period`` the escalation factor is 1.0 and the
output entries are unchanged save for the bookkeeping fields.

Output entries gain three fields:

    "escalated_from_period": "<base_period>",
    "escalation_factor":     <ratio>,
    "ppi_series_used":       "<series_id>",

Macro CCI multiplier (Phase C closing hook)
-------------------------------------------
``apply_macro_cci_multiplier(...)`` layers a single uniform multiplier on
top of an already per-CSI-escalated DB. It reads ENR / AGC / Turner CCI
snapshots (produced by ``core/pricing/sources/{enr,agc,turner}_cci.py``)
and scales every cost-DB entry's unit cost by

    multiplier = latest_cci_value / baseline_cci_value

This composes with — does NOT replace — the per-CSI PPI escalation.
Use it when a per-bid total-cost cross-check vs the published macro
construction-cost indices is needed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable, Optional

from core.pricing.snapshots import PricingSnapshot, load_history, load_latest
from core.pricing.sources._cci_common import PricingSourceUnavailable

LOG = logging.getLogger(__name__)


class EscalationMissingBaseline(RuntimeError):
    """Raised when the CCI baseline period snapshot can't be located.

    Distinct from ``PricingSourceUnavailable``: the latter signals that
    we couldn't pull a *latest* value at all (network down, page
    unparseable, etc.). ``EscalationMissingBaseline`` signals that we
    have at least one snapshot but none of them match the configured
    base period, which is a calibration problem, not an availability
    problem. The caller's fix is usually to broaden the base_period
    or refresh the source so a baseline-period snapshot exists.
    """


# Exact CSI section overrides (most specific). Keys are 6-character section
# codes that appear in `config/cost_database.json`.
_CSI_SECTION_TO_PPI: dict[str, str] = {
    "06 10 00": "WPU0811",      # rough carpentry → softwood lumber
    "06 16 00": "WPU0814",      # sheathing       → plywood
    "06 41 00": "WPU0812",      # millwork        → hardwood lumber
    "09 29 00": "WPU102201",    # gypsum board
    "09 91 23": "WPU065",       # interior paint
    "07 31 13": "WPU1351",      # asphalt shingles
    "07 41 13": "WPU1017",      # standing-seam metal roofing
    "05 12 00": "WPU101707",    # structural steel framing → fabricated
    "05 31 00": "WPU1017",      # steel deck → steel mill products
    "26 05 00": "WPU102301",    # branch wiring → copper wire & cable
    "26 24 16": "WPU102301",    # panelboard → copper wire & cable proxy
    "22 11 00": "WPU062",       # domestic water piping → plastics / PVC
    "22 40 00": "WPU2025201",   # plumbing fixtures
    "03 30 00": "WPU132",       # SOG → ready-mix concrete
    "03 31 00": "WPU132",       # footings → ready-mix concrete
    "03 35 00": "WPU132",       # finishing → ready-mix concrete
    "04 22 00": "WPU132",       # CMU wall (concrete masonry block)
    "32 12 16": "WPU1351",      # asphalt paving
    "32 13 13": "WPU132",       # concrete sidewalk
}


# Keyword fallbacks (case-insensitive). Order matters — longest first.
_KEYWORD_TO_PPI: list[tuple[str, str]] = [
    ("concrete masonry", "WPU132"),
    ("ready-mix concrete", "WPU132"),
    ("structural steel", "WPU101707"),
    ("plywood", "WPU0814"),
    ("hardwood", "WPU0812"),
    ("softwood", "WPU0811"),
    ("lumber", "WPU0811"),
    ("framing", "WPU0811"),
    ("drywall", "WPU102201"),
    ("gypsum", "WPU102201"),
    ("paint", "WPU065"),
    ("coatings", "WPU065"),
    ("wire", "WPU102301"),
    ("conduit", "WPU102301"),
    ("electrical", "WPU102301"),
    ("plumbing", "WPU2025201"),
    ("pvc", "WPU062"),
    ("asphalt shingle", "WPU1351"),
    ("asphalt", "WPU1351"),
    ("metal roof", "WPU1017"),
    ("metal deck", "WPU1017"),
    ("steel", "WPU1017"),
    ("diesel", "WPU057303"),
    ("fuel", "WPU057303"),
    ("sidewalk", "WPU132"),
    ("concrete", "WPU132"),
    ("insulation", "WPUSI012011"),
    ("hardware", "WPU2025201"),
]


# CSI division fallback (first two digits of the section).
_CSI_DIVISION_TO_PPI: dict[str, str] = {
    "01": "WPUSI012011",   # General requirements -> construction inputs
    "02": "WPUSI012011",   # Existing conditions / demo
    "03": "WPU132",        # Concrete
    "04": "WPU132",        # Masonry (concrete proxy)
    "05": "WPU1017",       # Metals
    "06": "WPU0811",       # Wood / plastics / composites
    "07": "WPU1351",       # Thermal & moisture protection
    "08": "WPU2025201",    # Openings (fixtures proxy)
    "09": "WPU102201",     # Finishes (gypsum proxy)
    "10": "WPUSI012011",   # Specialties
    "11": "WPUSI012011",   # Equipment
    "12": "WPUSI012011",   # Furnishings
    "13": "WPUSI012011",   # Special construction
    "14": "WPUSI012011",   # Conveying equipment
    "21": "WPU102301",     # Fire suppression (steel + copper proxy)
    "22": "WPU2025201",    # Plumbing
    "23": "WPUSI012011",   # HVAC
    "26": "WPU102301",     # Electrical
    "27": "WPU102301",     # Communications
    "28": "WPU102301",     # Electronic safety / security
    "31": "WPU132",        # Earthwork (concrete proxy for site)
    "32": "WPU132",        # Exterior improvements
    "33": "WPU062",        # Utilities (PVC pipe proxy)
}


GENERIC_FALLBACK = "WPUSI012011"


def pick_ppi_series(csi_section: str, description: str | None = None) -> str:
    """Return the PPI series id we should use to escalate this entry."""
    if csi_section in _CSI_SECTION_TO_PPI:
        return _CSI_SECTION_TO_PPI[csi_section]
    if description:
        desc_low = description.lower()
        for kw, sid in _KEYWORD_TO_PPI:
            if kw in desc_low:
                return sid
    division = csi_section[:2] if csi_section else ""
    if division in _CSI_DIVISION_TO_PPI:
        return _CSI_DIVISION_TO_PPI[division]
    return GENERIC_FALLBACK


def _snapshot_for_period(
    series_id: str,
    period: str,
    available: dict[str, list[PricingSnapshot]],
) -> Optional[PricingSnapshot]:
    """Find the snapshot for ``series_id`` whose ``period`` matches.

    If no exact match is found, the most recent snapshot with a period
    lexicographically less-than-or-equal-to ``period`` is returned (PPI
    period strings sort correctly: "2026-01" < "2026-02" etc.).
    Returns None if the series has no usable snapshot.
    """
    snaps = available.get(series_id, [])
    if not snaps:
        return None
    # exact match
    for s in snaps:
        if s.period == period:
            return s
    # most-recent-on-or-before
    candidates = sorted(
        (s for s in snaps if s.period <= period),
        key=lambda s: s.period,
    )
    if candidates:
        return candidates[-1]
    # last resort: oldest available
    return sorted(snaps, key=lambda s: s.period)[0]


def compute_escalation_factor(
    series_id: str,
    base_period: str,
    target_period: str,
    available: dict[str, list[PricingSnapshot]],
) -> tuple[float, str]:
    """Return ``(factor, series_id_used)`` for a given series + periods.

    Falls back to ``GENERIC_FALLBACK`` if the requested series has no data.
    Returns 1.0 if base==target or if a usable factor cannot be computed.
    """
    if base_period == target_period:
        return 1.0, series_id

    base = _snapshot_for_period(series_id, base_period, available)
    target = _snapshot_for_period(series_id, target_period, available)

    if base is None or target is None:
        # Try the generic fallback if we weren't already on it.
        if series_id != GENERIC_FALLBACK:
            base_g = _snapshot_for_period(GENERIC_FALLBACK, base_period, available)
            target_g = _snapshot_for_period(GENERIC_FALLBACK, target_period, available)
            if base_g is not None and target_g is not None and base_g.value > 0:
                return target_g.value / base_g.value, GENERIC_FALLBACK
        return 1.0, series_id

    if base.value <= 0:
        return 1.0, series_id
    return target.value / base.value, series_id


def _index_snapshots(
    snapshots: Iterable[PricingSnapshot],
) -> dict[str, list[PricingSnapshot]]:
    out: dict[str, list[PricingSnapshot]] = {}
    for s in snapshots:
        out.setdefault(s.series_id, []).append(s)
    return out


def _load_snapshots_from_disk(series_ids: Iterable[str]) -> list[PricingSnapshot]:
    """Helper: load `latest.json` for each requested series id (bls_ppi only).

    The escalation engine only ever reads from the ``bls_ppi`` source for now,
    because the FRED / EIA / OEWS adapters track different concepts (fuel,
    wages, indexes) and aren't a clean swap for commodity-PPI escalation.
    Future iteration can broaden this if/when we want wage-driven escalation.
    """
    out: list[PricingSnapshot] = []
    for sid in series_ids:
        snap = load_latest("bls_ppi", sid)
        if snap is not None:
            out.append(snap)
    return out


def escalate_cost_database(
    input_path: Path,
    output_path: Path,
    *,
    base_period: str,
    target_period: str,
    ppi_snapshots: Optional[Iterable[PricingSnapshot]] = None,
) -> dict[str, Any]:
    """Read the seed cost DB, escalate per-entry, write the escalated DB.

    Returns the written database dict for caller inspection.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    raw = json.loads(input_path.read_text(encoding="utf-8"))

    # Figure out which PPI series we'll need; load whatever isn't supplied.
    requested_series: set[str] = set()
    for section, entry in raw.items():
        if section.startswith("_"):
            continue
        sid = pick_ppi_series(section, entry.get("description"))
        requested_series.add(sid)
    requested_series.add(GENERIC_FALLBACK)

    if ppi_snapshots is None:
        ppi_snapshots = _load_snapshots_from_disk(requested_series)

    available = _index_snapshots(ppi_snapshots)

    out: dict[str, Any] = {}
    for section, entry in raw.items():
        if section.startswith("_"):
            out[section] = entry
            continue
        if not isinstance(entry, dict):
            out[section] = entry
            continue
        sid = pick_ppi_series(section, entry.get("description"))
        factor, used_sid = compute_escalation_factor(
            sid, base_period, target_period, available,
        )
        original_cost = float(entry.get("unit_cost", 0) or 0)
        new_entry = dict(entry)
        new_entry["unit_cost"] = round(original_cost * factor, 4)
        new_entry["escalated_from_period"] = base_period
        new_entry["escalation_factor"] = round(factor, 6)
        new_entry["ppi_series_used"] = used_sid
        out[section] = new_entry

    meta = dict(out.get("_meta") or {})
    meta["escalated_at"] = f"{base_period} -> {target_period}"
    meta["escalation_source"] = "core/pricing/escalation.py (BLS PPI)"
    out["_meta"] = meta

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    LOG.info(
        "Escalated %d entries %s -> %s, wrote %s",
        sum(1 for k in out if not k.startswith("_")),
        base_period, target_period, output_path,
    )
    return out


# --- Macro CCI multiplier hook (Phase C closing slice) ------------------

# Per-source default series_id for the macro CCI sources. Mirrors the
# ``default_series()`` of each adapter under ``core/pricing/sources/``.
# Kept here (not imported from the adapters) to avoid a cyclic-import
# risk: the adapters depend on snapshots.py + base.py; the engine
# depends on snapshots.py + the lightweight ``_cci_common`` exception
# class; layering this constants table in the engine module is cheaper
# than reaching into each adapter at import time.
_CCI_DEFAULT_SERIES_ID: dict[str, str] = {
    "enr_cci": "national-20city",
    "agc_cci": "national",
    "turner_cci": "national",
}


def _cci_snapshot_for_baseline(
    snapshots: list[PricingSnapshot],
    base_period: str,
) -> Optional[PricingSnapshot]:
    """Locate the baseline snapshot for ``base_period`` in ``snapshots``.

    Tries exact period match first, then the most-recent snapshot whose
    period is lexicographically less-than-or-equal-to ``base_period``.
    Returns None if no usable baseline is found.

    Period format note: ENR / AGC publish ``YYYY-MM``; Turner publishes
    ``YYYY-QN``. Lexicographic comparison is safe within a single
    source's period format because all three are zero-padded. Cross-
    format comparison ("2024-01" vs "2024-Q1") is NOT done here — the
    caller must pass a ``base_period`` that matches the chosen source's
    cadence (e.g. "2024-Q1" for Turner, "2024-01" for ENR / AGC).
    """
    if not snapshots:
        return None
    for s in snapshots:
        if s.period == base_period:
            return s
    candidates = sorted(
        (s for s in snapshots if s.period <= base_period),
        key=lambda s: s.period,
    )
    if candidates:
        return candidates[-1]
    return None


def _cci_snapshot_latest(
    snapshots: list[PricingSnapshot],
) -> Optional[PricingSnapshot]:
    """Pick the latest snapshot from ``snapshots`` (by period, ascending)."""
    if not snapshots:
        return None
    return sorted(snapshots, key=lambda s: s.period)[-1]


def _load_cci_history(source: str, *, series_id: Optional[str] = None) -> list[PricingSnapshot]:
    """Load all on-disk snapshots for ``source`` (default series id).

    Wrapped so tests can patch a single function. Returns [] if the
    source has nothing on disk.
    """
    sid = series_id or _CCI_DEFAULT_SERIES_ID.get(source)
    if sid is None:
        return []
    history = load_history(source, sid)
    if history:
        return history
    # `load_history` may miss the latest.json mirror when no
    # period-specific files have been written yet (e.g. a fresh refresh
    # that only persisted the latest). Fall back to load_latest as a
    # safety net so we don't false-negative.
    latest = load_latest(source, sid)
    return [latest] if latest is not None else []


def apply_macro_cci_multiplier(
    escalated_db_path: Path | str,
    *,
    base_period: str,
    cci_source: str = "enr_cci",
    cci_series_id: Optional[str] = None,
    fallback_sources: tuple[str, ...] = ("agc_cci", "turner_cci"),
    out_path: Optional[Path | str] = None,
    snapshots_by_source: Optional[dict[str, list[PricingSnapshot]]] = None,
) -> dict[str, Any]:
    """Apply a uniform macro CCI multiplier to an already-escalated DB.

    Reads the latest CCI snapshot from ``cci_source`` (default
    ``enr_cci``), falls back through ``fallback_sources`` if the
    configured source has no usable snapshot on disk, computes
    ``multiplier = latest_cci_value / baseline_cci_value``, multiplies
    every cost-DB entry's ``unit_cost`` by that multiplier, and writes
    the result to ``out_path`` (default:
    ``<input_dir>/<input_stem>_with_cci.json``).

    The input DB is NOT modified — both the per-CSI escalated DB and the
    macro-CCI-multiplied DB are kept side-by-side for comparison + audit.

    Raises:
      - ``PricingSourceUnavailable`` if every source in
        ``[cci_source, *fallback_sources]`` has zero snapshots on disk
        (or in the injected ``snapshots_by_source`` for tests).
      - ``EscalationMissingBaseline`` if the chosen source has snapshots
        but none of them are usable as a baseline at ``base_period``
        (i.e. there is no snapshot with period ≤ ``base_period``).

    ``snapshots_by_source`` is a test-injection point that bypasses the
    on-disk snapshot store. Keys are source names (``enr_cci``,
    ``agc_cci``, ``turner_cci``); values are the list of snapshots to
    consider for that source. When omitted, snapshots are loaded from
    ``config/pricing_snapshots/`` on disk.
    """
    escalated_db_path = Path(escalated_db_path)
    if out_path is None:
        out_path = escalated_db_path.with_name(
            f"{escalated_db_path.stem}_with_cci{escalated_db_path.suffix}"
        )
    out_path = Path(out_path)

    raw = json.loads(escalated_db_path.read_text(encoding="utf-8"))

    sources_to_try = [cci_source, *(s for s in fallback_sources if s != cci_source)]

    selected_source: Optional[str] = None
    selected_snapshots: list[PricingSnapshot] = []
    for src in sources_to_try:
        if snapshots_by_source is not None:
            history = snapshots_by_source.get(src, [])
        else:
            history = _load_cci_history(src, series_id=cci_series_id if src == cci_source else None)
        if history:
            selected_source = src
            selected_snapshots = history
            break

    if selected_source is None:
        raise PricingSourceUnavailable(
            f"apply_macro_cci_multiplier: no snapshots available for any "
            f"of {sources_to_try}. Run "
            f"`python scripts/refresh_pricing.py --phase c` to populate."
        )

    baseline = _cci_snapshot_for_baseline(selected_snapshots, base_period)
    if baseline is None:
        raise EscalationMissingBaseline(
            f"apply_macro_cci_multiplier: source {selected_source!r} has "
            f"{len(selected_snapshots)} snapshot(s) but none usable as "
            f"baseline at {base_period!r}. Available periods: "
            f"{sorted({s.period for s in selected_snapshots})!r}."
        )

    latest = _cci_snapshot_latest(selected_snapshots)
    if latest is None or latest.value <= 0 or baseline.value <= 0:
        raise EscalationMissingBaseline(
            f"apply_macro_cci_multiplier: source {selected_source!r} "
            f"baseline or latest snapshot has non-positive value "
            f"(baseline={baseline.value!r}, latest="
            f"{latest.value if latest else None!r}); cannot compute "
            f"multiplier."
        )

    multiplier = latest.value / baseline.value

    out: dict[str, Any] = {}
    entry_count = 0
    for section, entry in raw.items():
        if section.startswith("_"):
            out[section] = entry
            continue
        if not isinstance(entry, dict):
            out[section] = entry
            continue
        new_entry = dict(entry)
        original_cost = float(new_entry.get("unit_cost", 0) or 0)
        new_entry["unit_cost"] = round(original_cost * multiplier, 4)
        new_entry["macro_cci_multiplier"] = round(multiplier, 6)
        new_entry["macro_cci_source"] = selected_source
        new_entry["macro_cci_baseline_period"] = baseline.period
        new_entry["macro_cci_latest_period"] = latest.period
        out[section] = new_entry
        entry_count += 1

    meta = dict(out.get("_meta") or {})
    meta["macro_cci_applied_at"] = (
        f"{baseline.period} -> {latest.period} via {selected_source}"
    )
    meta["macro_cci_multiplier"] = round(multiplier, 6)
    meta["macro_cci_source"] = selected_source
    meta["macro_cci_baseline_value"] = baseline.value
    meta["macro_cci_latest_value"] = latest.value
    out["_meta"] = meta

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    LOG.info(
        "Applied macro CCI multiplier %.6f (%s %s -> %s) to %d entries, wrote %s",
        multiplier, selected_source, baseline.period, latest.period,
        entry_count, out_path,
    )
    return out
