"""CWICR open cost-dataset matcher (F1).

Layered cost-lookup primary source for `core.estimator`. Two-stage matching:

  1. TF-IDF over the full description corpus (top 200 candidates).
  2. Re-rank the top 200 with `sentence-transformers/all-MiniLM-L6-v2`
     cosine similarity (top K returned).

Unit-aware (penalises mismatches but does not exclude them — the upstream
unit-mismatch suppressor in `core.estimator` makes the final call) and
CSI-hint-aware (small boost when the dataset row's category text overlaps
with the takeoff's CSI division's keyword bag).

The 55k-row CWICR open dataset (CC-BY-4.0, datadrivenconstruction/
OpenConstructionEstimate-DDC-CWICR) is downloaded once on first use to
`~/.cache/cwicr/` and cached. The embedding index (~80 MB compressed +
55k×384 float32 NumPy array ≈ 80 MB on disk) is also cached and re-used
on every subsequent run.

**Schema note** — the spec described an idealised CSI-coded US schema
(``code, description, unit, unit_price, labor_cost, ..., category_l1``).
The actual dataset uses an 85-field schema with its own classification
(``rate_code``, ``rate_original_name``, ``rate_unit``,
``total_cost_per_position``, ``department_name``, …) and is metric-unit
based. We normalise the relevant columns into the spec-shaped
``CwicrCandidate`` at load time; CSI hints are matched against the
``department_name`` + ``section_name`` + ``category_type`` text bag
via a small keyword bridge keyed by 2-digit division.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import re
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CwicrCandidate:
    """One ranked row returned by `CwicrMatcher.match()`.

    `similarity` is in [0, 1] (cosine on L2-normalised MiniLM embeddings,
    plus the unit/CSI heuristic adjustments). `source_row_id` is the
    integer row index in the loaded dataset and is what the estimator
    embeds into `CostLine.cost_source` as `cwicr:<id>` for traceability.
    """

    code: str
    description: str
    unit: str
    unit_price: float
    labor_cost: float
    material_cost: float
    equipment_cost: float
    region: str
    year: int
    similarity: float
    source_row_id: int


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "cwicr"

# GitHub raw URL for the USA_USD variant (CC-BY-4.0). ~41 MB Parquet.
# The HuggingFace mirror referenced in the original F1 spec does not exist;
# the dataset is distributed via this GitHub repo and its release tarballs.
_DATASET_URL = (
    "https://raw.githubusercontent.com/"
    "datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR/"
    "main/US___DDC_CWICR/USA_USD_workitems_costs_resources_DDC_CWICR.parquet"
)
# Fallback: codeload.github.com serves the whole-repo zip and is not subject to
# the same corporate-proxy rules that throttle raw.githubusercontent.com.
# We extract just the parquet entry, then discard the rest. Slower (~780 MB
# zip vs ~41 MB direct) but reliable when the raw URL is unreachable.
_DATASET_ZIP_URL = (
    "https://codeload.github.com/"
    "datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR/"
    "zip/refs/heads/main"
)
_DATASET_ZIP_ENTRY = (
    "OpenConstructionEstimate-DDC-CWICR-main/"
    "US___DDC_CWICR/USA_USD_workitems_costs_resources_DDC_CWICR.parquet"
)
_DATASET_FILENAME = "USA_USD_workitems_costs_resources_DDC_CWICR.parquet"
_DATASET_REGION = "usa_usd"  # the dataset variant has no sub-region

# Embedding model + index file. Bumping `_INDEX_VERSION` invalidates all
# previously-cached embedding indices.
_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_INDEX_VERSION = 1

_TFIDF_TOPK = 200       # how many TF-IDF candidates re-ranked by embeddings
_EMBED_BATCH = 64

# Phase T6.1 — minimum CWICR similarity required for a candidate to be
# considered (the upstream estimator falls through to seed DB / no-match
# below this threshold). Bumped from the original 0.55 to 0.75 in T6.1
# to align with the Phase T7 ``CATEGORY_MATCH`` boundary
# (``COST_TIER_CATEGORY_THRESHOLD``): any CWICR hit that makes it
# through is now AT LEAST CATEGORY_MATCH-tier on the T7 axis, never
# INTERPOLATED. Worker BB's calibration math: at the prior 0.55
# threshold, a barely-above-threshold CWICR hit landed in
# ``INTERPOLATED @ price_conf=0.65`` which combined with default
# qty 0.7 produced 0.455 → ``HAND_TAKEOFF`` — the brief called this
# out as a Phase T6.1 follow-up. Tests that need the legacy 0.55
# floor (e.g. exercising the INTERPOLATED branch end-to-end) set
# ``CWICR_MIN_SIMILARITY=0.55`` via env var explicitly.
_MIN_SIMILARITY_FALLBACK = 0.75


# ---------------------------------------------------------------------------
# Unit synonyms
# ---------------------------------------------------------------------------


# Canonical → set of accepted synonyms. Comparison is case-insensitive and
# whitespace-tolerant. The dataset uses metric units (m, m2, m3, t, kg);
# US takeoffs use imperial (LF, SF, CY, TON, LB). We do NOT convert prices
# across families — same-family unit aliases just get a similarity boost,
# cross-family stays "loosely related" with a smaller penalty. The estimator's
# strict unit-mismatch suppressor remains the final arbiter.
_UNIT_SYNONYMS: dict[str, set[str]] = {
    "ea":  {"ea", "each", "nr", "no", "pc", "pce", "pcs", "unit"},
    "lf":  {"lf", "lin ft", "linear ft", "linft", "linear foot"},
    "m":   {"m", "meter", "metre", "lm", "100 m", "1000 m"},
    "sf":  {"sf", "sq ft", "sqft", "square foot", "square feet"},
    "m2":  {"m2", "sqm", "sq m", "100 m2", "1000 m2", "square meter", "square metre"},
    "cy":  {"cy", "cu yd", "cuyd", "cubic yard"},
    "m3":  {"m3", "cu m", "cum", "cubic meter", "cubic metre", "100 m3"},
    "lb":  {"lb", "lbs", "pound"},
    "kg":  {"kg", "kilogram", "100 kg", "1000 kg"},
    "ton": {"ton", "tons", "short ton"},
    "t":   {"t", "tonne", "metric ton", "tonnes"},
    "hr":  {"hr", "hour", "hours", "labor hour", "labour hour"},
    "ls":  {"ls", "lump sum", "lump"},
}

# Same-family loose groupings — used to give a smaller penalty when units
# are in the same dimensional family (length / area / volume / mass) but
# different unit systems. The upstream estimator still suppresses these.
_UNIT_FAMILY: dict[str, str] = {
    "lf": "length", "m": "length",
    "sf": "area",   "m2": "area",
    "cy": "volume", "m3": "volume",
    "lb": "mass",   "kg": "mass", "ton": "mass", "t": "mass",
    "ea": "count",
    "hr": "time",
    "ls": "lump",
}


def _normalise_unit(unit: str | None) -> str:
    """Return the canonical family key for a free-form unit string, or ""."""
    if not unit:
        return ""
    raw = re.sub(r"\s+", " ", unit.strip().lower())
    # Strip leading multipliers like "100 ", "1000 " before lookup.
    raw_stripped = re.sub(r"^\d+\s*", "", raw)
    for canon, aliases in _UNIT_SYNONYMS.items():
        if raw in aliases or raw_stripped in aliases:
            return canon
    return raw_stripped  # last-ditch — return the cleaned token


def _unit_similarity(takeoff_unit: str | None, candidate_unit: str | None) -> float:
    """Return a multiplicative similarity adjustment in [0.55, 1.10].

    Exact synonym match → 1.10 (boost). Same dimensional family but
    different system → 0.85. Different family → 0.55.
    """
    a = _normalise_unit(takeoff_unit)
    b = _normalise_unit(candidate_unit)
    if not a or not b:
        return 1.0
    if a == b:
        return 1.10
    fam_a, fam_b = _UNIT_FAMILY.get(a), _UNIT_FAMILY.get(b)
    if fam_a and fam_b and fam_a == fam_b:
        return 0.85
    return 0.55


# ---------------------------------------------------------------------------
# CSI division ↔ keyword bridge
# ---------------------------------------------------------------------------


# Minimal mapping from 2-digit CSI MasterFormat division to keyword bag we
# use to *boost* (not filter) candidates whose CWICR category text overlaps.
# Keys are 2-digit division strings; values are lowercase keyword tokens.
_CSI_DIVISION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "01": ("general", "supervision", "temporary", "site management"),
    "02": ("demolition", "site preparation", "remediation"),
    "03": ("concrete", "reinforced", "rebar", "formwork", "slab", "footing"),
    "04": ("masonry", "cmu", "brick", "block"),
    "05": ("steel", "metal", "structural steel", "rebar"),
    "06": ("wood", "carpentry", "framing", "lumber", "plastic"),
    "07": ("thermal", "moisture", "insulation", "roofing", "membrane", "sealant"),
    "08": ("door", "window", "opening", "glazing", "hardware"),
    "09": ("finishes", "drywall", "gypsum", "plaster", "tile", "flooring", "paint", "ceiling"),
    "10": ("specialties", "signage", "partition", "toilet accessory"),
    "11": ("equipment", "appliance", "fixture"),
    "12": ("furnishings", "casework"),
    "13": ("special construction",),
    "14": ("conveying", "elevator", "escalator"),
    "21": ("fire", "sprinkler", "suppression"),
    "22": ("plumbing", "water", "sewer", "fixture", "pipe"),
    "23": ("hvac", "heating", "ventilation", "ductwork", "air handler"),
    "26": ("electrical", "wiring", "conduit", "luminaire", "panel"),
    "27": ("communications", "data", "cable", "fiber"),
    "28": ("security", "fire alarm", "intrusion"),
    "31": ("earthwork", "excavation", "grading", "backfill"),
    "32": ("exterior", "paving", "landscaping", "sidewalk"),
    "33": ("utilities", "water main", "sewer line", "gas line"),
}


def _csi_hint_bonus(csi_hint: str | None, category_text: str) -> float:
    """Return a small additive bonus in [0, 0.05] when CSI keywords appear."""
    if not csi_hint:
        return 0.0
    digits = "".join(ch for ch in csi_hint if ch.isdigit())[:2]
    keywords = _CSI_DIVISION_KEYWORDS.get(digits, ())
    if not keywords:
        return 0.0
    text = category_text.lower()
    hits = sum(1 for kw in keywords if kw in text)
    if hits == 0:
        return 0.0
    return min(0.05, 0.015 * hits)


# ---------------------------------------------------------------------------
# Default dataset loader
# ---------------------------------------------------------------------------


def _ensure_cache_dir(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _stream_to_partial(
    url: str,
    partial: Path,
    *,
    label: str,
    timeout: int = 180,
) -> int:
    """Stream `url` into `partial`. Returns bytes written. Logs progress."""
    chunk = 1 << 20  # 1 MiB
    written = 0
    last_log = 0.0
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 — well-known public URL
        size = int(resp.headers.get("Content-Length") or 0)
        with partial.open("wb") as fh:
            while True:
                buf = resp.read(chunk)
                if not buf:
                    break
                fh.write(buf)
                written += len(buf)
                now = time.monotonic()
                if (now - last_log) > 3.0:
                    if size:
                        pct = written * 100.0 / size
                        logger.info(
                            "%s progress: %5.1f%% (%.1f MB / %.1f MB)",
                            label, pct, written / 1e6, size / 1e6,
                        )
                    else:
                        logger.info(
                            "%s progress: %.1f MB (no Content-Length)",
                            label, written / 1e6,
                        )
                    last_log = now
    return written


def _download_parquet(target: Path) -> None:
    """One-shot HTTPS download of the CWICR Parquet to `target`.

    Streams to a `.partial` sidecar and atomically renames on success so
    a half-downloaded file never wins on a retry. Verbose at INFO so the
    first run isn't mysteriously silent for 30+ seconds.

    If the direct ``raw.githubusercontent.com`` URL is unreachable (common
    behind corporate proxies that allow ``codeload.github.com`` but not
    ``raw.``), falls back to fetching the whole-repo zip from
    ``codeload.github.com`` and extracting just the parquet entry.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".partial")
    if partial.exists():
        partial.unlink()

    direct_err: Exception | None = None
    logger.info(
        "downloading CWICR dataset (~41 MB) from %s — one-time operation, "
        "cached at %s on success",
        _DATASET_URL,
        target,
    )
    t0 = time.monotonic()
    try:
        _stream_to_partial(
            _DATASET_URL,
            partial,
            label="CWICR direct download",
            timeout=120,
        )
        partial.replace(target)
    except Exception as err:  # noqa: BLE001 — every network failure routes to fallback
        direct_err = err
        if partial.exists():
            partial.unlink()
        logger.warning(
            "direct CWICR download failed (%s: %s); falling back to "
            "codeload.github.com zip — ~780 MB transient transfer, ~41 MB "
            "extracted parquet",
            type(err).__name__, err,
        )
        zip_partial = partial.with_suffix(partial.suffix + ".zip")
        if zip_partial.exists():
            zip_partial.unlink()
        try:
            _stream_to_partial(
                _DATASET_ZIP_URL,
                zip_partial,
                label="CWICR codeload zip",
                timeout=600,
            )
            logger.info("extracting %s from codeload zip", _DATASET_ZIP_ENTRY)
            with zipfile.ZipFile(zip_partial) as zf:
                # Locate the target entry by canonical path; tolerate a leading
                # branch-prefix variation should the repo ever rename.
                names = zf.namelist()
                candidates = [n for n in names if n.endswith(
                    "USA_USD_workitems_costs_resources_DDC_CWICR.parquet"
                )]
                if not candidates:
                    raise RuntimeError(
                        "CWICR codeload zip is missing the USA_USD parquet entry"
                    )
                with zf.open(candidates[0]) as src, partial.open("wb") as dst:
                    while True:
                        chunk = src.read(1 << 20)
                        if not chunk:
                            break
                        dst.write(chunk)
            partial.replace(target)
        finally:
            if zip_partial.exists():
                zip_partial.unlink()

    logger.info(
        "CWICR dataset ready: %.1f MB in %.1fs%s",
        target.stat().st_size / 1e6,
        time.monotonic() - t0,
        " (via codeload fallback)" if direct_err is not None else "",
    )


def _load_cwicr_parquet(cache_dir: Path) -> Any:
    """Default loader — downloads the dataset on first call, returns DataFrame.

    Returns a pandas DataFrame with the **raw** CWICR schema; normalisation
    into the spec-shaped fields happens inside `_normalise_rows`.
    """
    import pandas as pd  # local import — pandas is already in the venv

    parquet_path = cache_dir / _DATASET_FILENAME
    if not parquet_path.is_file():
        _download_parquet(parquet_path)
    logger.info("loading CWICR parquet from %s", parquet_path)
    df = pd.read_parquet(parquet_path)
    return df


# ---------------------------------------------------------------------------
# Row normalisation
# ---------------------------------------------------------------------------


# Columns we want. Each entry: (canonical name, list of candidate raw columns
# tried in order). The first one present wins. This lets us survive minor
# schema renames upstream without breaking the matcher.
_COLUMN_MAP: dict[str, tuple[str, ...]] = {
    "code":           ("rate_code",),
    "description":    ("rate_original_name", "rate_final_name", "section_name"),
    "unit":           ("rate_unit", "rate_unit_of_measure"),
    "unit_price":     ("total_cost_per_position", "total_resource_cost_per_position", "rate_unit_price_eur_current"),
    "labor_cost":     ("cost_of_working_hours", "labor_total_cost"),
    "material_cost":  ("total_material_cost_per_position", "materials_resource_cost_eur"),
    "equipment_cost": ("total_value_machinery_equipment",),
    "category_l1":    ("category_type",),
    "category_l2":    ("department_name", "collection_name"),
    "category_l3":    ("section_name",),
}


def _pick_col(df_columns: Iterable[str], candidates: tuple[str, ...]) -> str | None:
    cols = set(df_columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def _normalise_rows(df: Any) -> Any:
    """Project the raw 85-column CWICR DataFrame down to what the matcher needs.

    Drops rows with no `description` (essential for embedding / TF-IDF) and
    coerces price columns to float. Returns a DataFrame with these columns:

      code, description, unit, unit_price, labor_cost, material_cost,
      equipment_cost, category_l1, category_l2, category_l3,
      _category_text (concatenated lower-cased classification bag),
      _row_id (stable index for source_row_id).
    """
    import pandas as pd

    cols = list(df.columns)
    picks: dict[str, str | None] = {
        canonical: _pick_col(cols, candidates)
        for canonical, candidates in _COLUMN_MAP.items()
    }

    if not picks["description"]:
        raise ValueError(
            "CWICR loader: no description-like column found in dataset; "
            f"available columns sample: {cols[:10]}"
        )

    out = pd.DataFrame({
        "code":           df[picks["code"]].astype(str)        if picks["code"]           else "",
        "description":    df[picks["description"]].astype(str),
        "unit":           df[picks["unit"]].astype(str)        if picks["unit"]           else "",
        "unit_price":     pd.to_numeric(df[picks["unit_price"]], errors="coerce")     if picks["unit_price"]     else 0.0,
        "labor_cost":     pd.to_numeric(df[picks["labor_cost"]], errors="coerce")     if picks["labor_cost"]     else 0.0,
        "material_cost":  pd.to_numeric(df[picks["material_cost"]], errors="coerce")  if picks["material_cost"]  else 0.0,
        "equipment_cost": pd.to_numeric(df[picks["equipment_cost"]], errors="coerce") if picks["equipment_cost"] else 0.0,
        "category_l1":    df[picks["category_l1"]].astype(str) if picks["category_l1"] else "",
        "category_l2":    df[picks["category_l2"]].astype(str) if picks["category_l2"] else "",
        "category_l3":    df[picks["category_l3"]].astype(str) if picks["category_l3"] else "",
    })

    # Drop rows with empty / NaN descriptions or descriptions that are
    # just a few placeholder chars — they're noise that TF-IDF will rank
    # spuriously high on short queries.
    out["description"] = out["description"].fillna("").str.strip()
    out = out[out["description"].str.len() >= 5].copy()

    out["unit_price"]     = out["unit_price"].fillna(0.0).astype(float)
    out["labor_cost"]     = out["labor_cost"].fillna(0.0).astype(float)
    out["material_cost"]  = out["material_cost"].fillna(0.0).astype(float)
    out["equipment_cost"] = out["equipment_cost"].fillna(0.0).astype(float)

    out["_category_text"] = (
        out["category_l1"].fillna("").astype(str) + " | " +
        out["category_l2"].fillna("").astype(str) + " | " +
        out["category_l3"].fillna("").astype(str)
    ).str.lower()

    out = out.reset_index(drop=True)
    out["_row_id"] = out.index.astype(int)
    return out


# ---------------------------------------------------------------------------
# CwicrMatcher
# ---------------------------------------------------------------------------


class CwicrMatcher:
    """Two-stage (TF-IDF → semantic) matcher over the CWICR open dataset.

    Construction is cheap; `warm()` (or the first `match()` call) does the
    heavy lifting: downloads the dataset on first run, fits TF-IDF, encodes
    descriptions with a sentence-transformer, and caches the embedding
    index to `~/.cache/cwicr/embeddings_v{N}.npy`.
    """

    def __init__(
        self,
        region: str | None = None,
        year: int | None = None,
        cache_dir: Path | None = None,
        *,
        _dataset_loader: Callable[[Path], Any] | None = None,
        _embedder: Callable[[list[str]], np.ndarray] | None = None,
    ) -> None:
        self.region = (region or os.environ.get("CWICR_REGION") or _DATASET_REGION).strip().lower()
        self.year = year if year is not None else _coerce_int_env("CWICR_YEAR")
        self.cache_dir = _ensure_cache_dir(cache_dir or _DEFAULT_CACHE_DIR)

        # Hooks for tests: tests inject fixtures via `_dataset_loader` and
        # a deterministic `_embedder` to keep the unit-test suite offline.
        self._dataset_loader = _dataset_loader or _load_cwicr_parquet
        self._embedder = _embedder

        self._df: Any | None = None                  # pandas DataFrame (normalised)
        self._tfidf = None                           # fitted TfidfVectorizer
        self._tfidf_matrix = None                    # sparse [N, F] TF-IDF features
        self._embeddings: np.ndarray | None = None   # [N, D] L2-normalised
        self._warm = False

    # ------------------------------------------------------------------
    # Warm-up
    # ------------------------------------------------------------------

    def warm(self) -> None:
        """Ensure the dataset + embedding index are loaded. Idempotent."""
        if self._warm:
            return

        t_total = time.monotonic()
        logger.info("CWICR matcher: warming up (cache dir: %s)", self.cache_dir)

        # ---- dataset ----
        raw = self._dataset_loader(self.cache_dir)
        df = _normalise_rows(raw)
        logger.info("CWICR matcher: normalised %d rows", len(df))
        self._df = df

        # ---- TF-IDF ----
        from sklearn.feature_extraction.text import TfidfVectorizer  # local import

        t0 = time.monotonic()
        self._tfidf = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=50_000,
            min_df=1,
            lowercase=True,
            strip_accents="unicode",
        )
        self._tfidf_matrix = self._tfidf.fit_transform(df["description"].tolist())
        logger.info(
            "CWICR matcher: TF-IDF fit in %.2fs (features=%d)",
            time.monotonic() - t0, self._tfidf_matrix.shape[1],
        )

        # ---- embeddings (with disk cache) ----
        self._embeddings = self._load_or_build_embeddings(df["description"].tolist())

        self._warm = True
        logger.info("CWICR matcher: warm-up complete in %.1fs", time.monotonic() - t_total)

    def _embedding_cache_path(self, n_rows: int) -> Path:
        """Cache key by dataset row count + index version, to invalidate
        cleanly when the upstream dataset adds / removes rows."""
        h = hashlib.sha1(f"{n_rows}:{_INDEX_VERSION}".encode()).hexdigest()[:12]
        return self.cache_dir / f"embeddings_v{_INDEX_VERSION}_{h}.npy"

    def _load_or_build_embeddings(self, descriptions: list[str]) -> np.ndarray:
        cache_path = self._embedding_cache_path(len(descriptions))
        if cache_path.is_file():
            logger.info("CWICR matcher: loading cached embeddings from %s", cache_path)
            arr = np.load(cache_path)
            if arr.shape[0] == len(descriptions):
                return arr.astype(np.float32, copy=False)
            logger.warning(
                "CWICR matcher: cached embedding row-count mismatch (%d vs %d); rebuilding",
                arr.shape[0], len(descriptions),
            )

        logger.info(
            "CWICR matcher: building embedding index for %d rows "
            "(this is a one-time operation, ~60-120 s on CPU)",
            len(descriptions),
        )
        t0 = time.monotonic()

        if self._embedder is not None:
            arr = self._embedder(descriptions)
        else:
            from sentence_transformers import SentenceTransformer  # local import — heavy
            model = SentenceTransformer(_EMBED_MODEL)
            arr = model.encode(
                descriptions,
                batch_size=_EMBED_BATCH,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

        arr = np.asarray(arr, dtype=np.float32)
        # Defensive L2-normalise (sentence-transformers does this with
        # normalize_embeddings=True, but a custom embedder may not).
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms

        try:
            np.save(cache_path, arr)
            logger.info(
                "CWICR matcher: embedding index built in %.1fs, cached at %s (%d bytes)",
                time.monotonic() - t0, cache_path, cache_path.stat().st_size,
            )
        except OSError as exc:
            logger.warning("CWICR matcher: could not write embedding cache: %s", exc)

        return arr

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def match(
        self,
        description: str,
        unit_hint: str | None = None,
        csi_hint: str | None = None,
        top_k: int = 5,
    ) -> list[CwicrCandidate]:
        """Return up to `top_k` ranked candidates for the given description.

        Returns an empty list if `description` is empty.
        """
        if not description or not description.strip():
            return []

        self.warm()
        assert self._df is not None and self._tfidf is not None and self._embeddings is not None

        # --- Stage 1: TF-IDF top-K candidates ---
        from sklearn.metrics.pairwise import cosine_similarity  # local import

        query_vec = self._tfidf.transform([description])
        # cosine_similarity returns dense [1, N]
        tfidf_scores = cosine_similarity(query_vec, self._tfidf_matrix).ravel()

        n_rows = len(self._df)
        tfidf_topk = min(_TFIDF_TOPK, n_rows)
        # argpartition is O(N), then we sort the smaller slice O(k log k)
        cand_idx = np.argpartition(-tfidf_scores, tfidf_topk - 1)[:tfidf_topk]

        # --- Stage 2: semantic re-rank ---
        if self._embedder is not None:
            q_emb = self._embedder([description])
        else:
            from sentence_transformers import SentenceTransformer
            # Re-loading the model on every query would be silly — cache it.
            if not hasattr(self, "_model"):
                self._model = SentenceTransformer(_EMBED_MODEL)
            q_emb = self._model.encode(
                [description],
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        q_emb = np.asarray(q_emb, dtype=np.float32)
        q_norm = np.linalg.norm(q_emb, axis=1, keepdims=True)
        q_norm[q_norm == 0] = 1.0
        q_emb = q_emb / q_norm

        cand_embeddings = self._embeddings[cand_idx]
        # Cosine similarity between query and candidates: shape (n_cand,)
        emb_scores = (cand_embeddings @ q_emb.T).ravel()

        # --- Heuristic adjustments (unit, CSI hint) ---
        df = self._df
        col_loc = df.columns.get_loc
        col_unit_idx = col_loc("unit")
        col_cat_idx  = col_loc("_category_text")
        col_code_idx = col_loc("code")
        col_desc_idx = col_loc("description")
        col_up_idx   = col_loc("unit_price")
        col_lc_idx   = col_loc("labor_cost")
        col_mc_idx   = col_loc("material_cost")
        col_ec_idx   = col_loc("equipment_cost")
        col_rid_idx  = col_loc("_row_id")

        adjusted: list[tuple[int, float]] = []
        for local_i, row_idx in enumerate(cand_idx):
            base = float(emb_scores[local_i])
            cand_unit = str(df.iat[int(row_idx), col_unit_idx])
            unit_mult = _unit_similarity(unit_hint, cand_unit)
            category_text = str(df.iat[int(row_idx), col_cat_idx])
            csi_bonus = _csi_hint_bonus(csi_hint, category_text)
            # Clamp to [0, 1] after the adjustments.
            adj = max(0.0, min(1.0, base * unit_mult + csi_bonus))
            adjusted.append((int(row_idx), adj))

        adjusted.sort(key=lambda x: -x[1])

        # The upstream dataset contains many near-duplicate rows (same
        # code / unit / description repeated per region or variant). Keep
        # only the highest-scoring row for each (code, unit, description)
        # triple so the user sees distinct candidates in the top-K.
        seen: set[tuple[str, str, str]] = set()
        deduped: list[tuple[int, float]] = []
        for row_idx, sim in adjusted:
            key = (
                str(df.iat[row_idx, col_code_idx]),
                str(df.iat[row_idx, col_unit_idx]),
                str(df.iat[row_idx, col_desc_idx]),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append((row_idx, sim))
            if len(deduped) >= max(1, top_k):
                break
        top = deduped

        out: list[CwicrCandidate] = []
        for row_idx, sim in top:
            out.append(CwicrCandidate(
                code=str(df.iat[row_idx, col_code_idx]),
                description=str(df.iat[row_idx, col_desc_idx]),
                unit=str(df.iat[row_idx, col_unit_idx]),
                unit_price=float(df.iat[row_idx, col_up_idx] or 0.0),
                labor_cost=float(df.iat[row_idx, col_lc_idx] or 0.0),
                material_cost=float(df.iat[row_idx, col_mc_idx] or 0.0),
                equipment_cost=float(df.iat[row_idx, col_ec_idx] or 0.0),
                region=self.region,
                year=int(self.year or 0),
                similarity=round(float(sim), 4),
                source_row_id=int(df.iat[row_idx, col_rid_idx]),
            ))

        if logger.isEnabledFor(logging.DEBUG):
            for c in out:
                logger.debug(
                    "CWICR match: sim=%.3f code=%s unit=%s price=%.2f desc=%s",
                    c.similarity, c.code, c.unit, c.unit_price, c.description[:80],
                )

        return out


# ---------------------------------------------------------------------------
# Module-level cache (so analyze.py and app.py don't reload per call)
# ---------------------------------------------------------------------------


_DEFAULT_MATCHER: CwicrMatcher | None = None
_DEFAULT_MATCHER_KEY: tuple[str, int | None, str] | None = None


def get_default_matcher(
    region: str | None = None,
    year: int | None = None,
    cache_dir: Path | None = None,
) -> CwicrMatcher:
    """Return a process-wide matcher singleton keyed by (region, year, cache_dir).

    Lazy: the matcher is constructed cheaply; `warm()` only runs on the
    first `.match()` call. Re-using the singleton avoids re-loading the
    parquet + rebuilding the embedding index across pricing runs in the
    same process (matters for the Streamlit app's `Recalculate` button).
    """
    global _DEFAULT_MATCHER, _DEFAULT_MATCHER_KEY
    cache_dir_resolved = cache_dir or _DEFAULT_CACHE_DIR
    key = (
        (region or os.environ.get("CWICR_REGION") or _DATASET_REGION).strip().lower(),
        year if year is not None else _coerce_int_env("CWICR_YEAR"),
        str(cache_dir_resolved),
    )
    if _DEFAULT_MATCHER is None or _DEFAULT_MATCHER_KEY != key:
        _DEFAULT_MATCHER = CwicrMatcher(region=region, year=year, cache_dir=cache_dir_resolved)
        _DEFAULT_MATCHER_KEY = key
    return _DEFAULT_MATCHER


def reset_default_matcher() -> None:
    """Drop the cached singleton — used by tests."""
    global _DEFAULT_MATCHER, _DEFAULT_MATCHER_KEY
    _DEFAULT_MATCHER = None
    _DEFAULT_MATCHER_KEY = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coerce_int_env(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("env %s=%r is not an integer; ignoring", name, raw)
        return None


def is_cwicr_disabled() -> bool:
    """`CWICR_DISABLED=true|1|yes` short-circuits CWICR resolution."""
    return os.environ.get("CWICR_DISABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def min_similarity_threshold() -> float:
    """Read `CWICR_MIN_SIMILARITY` from env, falling back to the T6.1 default.

    The T6.1 default (``_MIN_SIMILARITY_FALLBACK = 0.75``) aligns the
    minimum CWICR similarity with the Phase T7 ``CATEGORY_MATCH``
    boundary so any CWICR hit that passes is AT LEAST CATEGORY_MATCH
    on the T7 axis, never INTERPOLATED. Tests that need to exercise
    the INTERPOLATED / PARAMETRIC branches end-to-end set
    ``CWICR_MIN_SIMILARITY`` to a lower value explicitly via env.
    """
    raw = os.environ.get("CWICR_MIN_SIMILARITY", "").strip()
    if not raw:
        return _MIN_SIMILARITY_FALLBACK
    try:
        v = float(raw)
    except ValueError:
        logger.warning("CWICR_MIN_SIMILARITY=%r is not a float; using %s",
                       raw, _MIN_SIMILARITY_FALLBACK)
        return _MIN_SIMILARITY_FALLBACK
    return max(0.0, min(1.0, v))
