"""Pricing snapshot data model + file-system persistence.

A `PricingSnapshot` is the canonical record produced by every external pricing
source adapter under `core/pricing/sources/`. Snapshots are written to disk so
estimates remain reproducible even when an upstream API rate-limits us or
removes a series.

Layout on disk (rooted at ``config/pricing_snapshots/``)::

    <source>/<series_id>/<period>.json   # one record per observation
    <source>/<series_id>/latest.json     # mirror of newest period

A separate ``_http_cache/`` sibling directory holds raw upstream HTTP
responses with a 24h TTL and is gitignored; see `core/pricing/sources/base.py`.

No PII, no credentials, no customer data is ever persisted in a snapshot.
``raw`` carries the upstream response *only*, and any source adapter that
would otherwise include caller-identifying data MUST scrub it before storing.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


_REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS_ROOT = _REPO_ROOT / "config" / "pricing_snapshots"

_SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9._\-]+")


def _safe(token: str) -> str:
    """Sanitize a path component so a malformed series id can never escape the
    snapshots directory tree."""
    if not token:
        raise ValueError("path token must be non-empty")
    cleaned = _SAFE_TOKEN_RE.sub("_", token.strip())
    if cleaned in {"", ".", ".."}:
        raise ValueError(f"invalid path token: {token!r}")
    return cleaned


class PricingSnapshot(BaseModel):
    """A single observation from an external pricing source.

    Fields mirror the brief: each adapter populates whichever optional fields
    apply to its source. ``raw`` is a full passthrough of the upstream response
    object for traceability — kept as untyped ``dict`` because each source's
    shape is different.
    """

    source: str = Field(
        ..., description="Adapter name, e.g. 'bls_ppi', 'fred', 'eia'."
    )
    series_id: str = Field(..., description="Source-specific series identifier.")
    label: str = Field(..., description="Human-readable description of the series.")
    unit: str = Field(
        ..., description="USD/CY, USD/MBF, USD/SF, USD/hr, USD/gallon, etc."
    )
    value: float
    region: Optional[str] = Field(
        default=None,
        description="State abbreviation, MSA code, or BLS region code. "
        "None means national.",
    )
    csi_division: Optional[str] = None
    naics: Optional[str] = None
    soc_code: Optional[str] = None
    period: str = Field(
        ...,
        description='Reporting period, e.g. "2026-04" / "2026-Q1" / "2026-05-27".',
    )
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    license: str = Field(..., description="License / attribution string.")
    source_url: str = Field(..., description="Canonical URL for traceability.")
    raw: Optional[dict] = None

    def path(self, root: Path = SNAPSHOTS_ROOT) -> Path:
        """Return the on-disk path for this snapshot."""
        return root / _safe(self.source) / _safe(self.series_id) / f"{_safe(self.period)}.json"

    def latest_path(self, root: Path = SNAPSHOTS_ROOT) -> Path:
        """Return the ``latest.json`` mirror path for this (source, series)."""
        return root / _safe(self.source) / _safe(self.series_id) / "latest.json"

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, blob: str) -> "PricingSnapshot":
        return cls.model_validate_json(blob)


def write_snapshot(
    snapshot: PricingSnapshot, *, root: Path = SNAPSHOTS_ROOT
) -> Path:
    """Persist ``snapshot`` to disk and update the ``latest.json`` mirror.

    Returns the path the period-specific record was written to.
    """
    target = snapshot.path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(snapshot.to_json(), encoding="utf-8")
    # The latest mirror is overwritten on every write. We don't compare
    # `period` strings to choose newest because period formats vary by source
    # ("2026-04" vs "2026-Q1" vs "2026-05-27"); we instead pick the snapshot
    # with the greatest `fetched_at` from the full series history.
    history = load_history(snapshot.source, snapshot.series_id, root=root)
    newest = max(history, key=lambda s: s.fetched_at)
    snapshot.latest_path(root).write_text(newest.to_json(), encoding="utf-8")
    return target


def write_snapshots(
    snapshots: list[PricingSnapshot], *, root: Path = SNAPSHOTS_ROOT
) -> list[Path]:
    """Persist multiple snapshots; returns list of written period-specific paths."""
    return [write_snapshot(s, root=root) for s in snapshots]


def load_latest(
    source: str, series_id: str, *, root: Path = SNAPSHOTS_ROOT
) -> Optional[PricingSnapshot]:
    """Load the newest snapshot for a given (source, series_id) pair, or None."""
    latest = root / _safe(source) / _safe(series_id) / "latest.json"
    if not latest.exists():
        return None
    return PricingSnapshot.from_json(latest.read_text(encoding="utf-8"))


def load_history(
    source: str, series_id: str, *, root: Path = SNAPSHOTS_ROOT
) -> list[PricingSnapshot]:
    """Load every persisted snapshot for a given (source, series_id) pair.

    Excludes the ``latest.json`` mirror (which is always a duplicate of one of
    the period-specific files). Sorted by ``fetched_at`` ascending so callers
    can pluck `[-1]` for the most recent.
    """
    series_dir = root / _safe(source) / _safe(series_id)
    if not series_dir.exists():
        return []
    out: list[PricingSnapshot] = []
    for p in sorted(series_dir.glob("*.json")):
        if p.name == "latest.json":
            continue
        try:
            out.append(PricingSnapshot.from_json(p.read_text(encoding="utf-8")))
        except Exception:
            # Corrupt snapshot file: skip rather than break the whole pipeline.
            # The refresh runner will overwrite on next successful fetch.
            continue
    out.sort(key=lambda s: s.fetched_at)
    return out


def list_sources(*, root: Path = SNAPSHOTS_ROOT) -> list[str]:
    """Return sorted list of source names that have at least one snapshot on disk."""
    if not root.exists():
        return []
    return sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


def list_series(source: str, *, root: Path = SNAPSHOTS_ROOT) -> list[str]:
    """Return sorted list of series ids that have snapshots on disk for ``source``."""
    src_dir = root / _safe(source)
    if not src_dir.exists():
        return []
    return sorted(p.name for p in src_dir.iterdir() if p.is_dir())


def write_text_record(
    *, source: str, series_id: str, period: str, payload: dict[str, Any],
    root: Path = SNAPSHOTS_ROOT,
) -> Path:
    """Helper for adapters that need to persist auxiliary records that aren't
    `PricingSnapshot`s — e.g. Davis-Bacon raw WD pointers.
    """
    target = root / _safe(source) / _safe(series_id) / f"{_safe(period)}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return target
