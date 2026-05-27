"""Shared base + helpers for pricing source adapters.

Design goals (per Tier 1 pricing brief):

1. Every adapter is a small subclass of ``PricingSource``. The two methods
   subclasses must implement are ``fetch(series_ids, **filters)`` and
   ``default_series()``.
2. Every adapter uses ``httpx`` (sync), TLS verified, 30s timeout, and a
   polite ``User-Agent`` so a polite operator can identify us in their logs.
3. Every successful HTTP response is cached on disk for 24h to minimize
   pressure on free public APIs. The cache is gitignored.
4. No API key, account name, or other caller-identifying detail is logged or
   persisted into snapshots.
5. The base class accepts an optional pre-built ``httpx.Client`` so tests can
   inject ``httpx.MockTransport`` and remain offline.

License + ToS for each source live in the per-adapter module docstring.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from core.pricing.snapshots import SNAPSHOTS_ROOT, PricingSnapshot

LOG = logging.getLogger(__name__)

USER_AGENT = "BPC-Estimator/1.0 (contact@blueprintconstructs.com)"
HTTP_TIMEOUT_SECONDS = 30
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h

HTTP_CACHE_ROOT = SNAPSHOTS_ROOT / "_http_cache"


def _cache_key(method: str, url: str, params: Optional[dict[str, Any]], body: Optional[Any]) -> str:
    """Stable cache key for an HTTP call.

    We deliberately hash a string that does NOT include the request headers,
    because most adapters embed the API key in the URL query string (FRED,
    EIA) or as a body field (BLS), so the key already separates per-account
    cache entries naturally. For sources that send the key in a header we
    additionally fold the env-var presence into the key (see comment below)
    via the optional ``body['_account_tag']``; adapters set that themselves
    if they need per-account isolation.
    """
    parts = [method.upper(), url]
    if params:
        parts.append(urlencode(sorted(params.items())))
    if body is not None:
        try:
            parts.append(json.dumps(body, sort_keys=True, default=str))
        except (TypeError, ValueError):
            parts.append(repr(body))
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest


def _is_fresh(path: Path, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    if not path.exists():
        return False
    age = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
    return age < ttl_seconds


def _read_cache(path: Path) -> Optional[dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, default=str), encoding="utf-8")


def build_client(transport: Optional[httpx.BaseTransport] = None) -> httpx.Client:
    """Build an `httpx.Client` configured with the polite headers, TLS verify
    on, and a 30s timeout. Tests pass `httpx.MockTransport(handler)`.
    """
    kwargs: dict[str, Any] = {
        "headers": {"User-Agent": USER_AGENT, "Accept": "application/json"},
        "timeout": HTTP_TIMEOUT_SECONDS,
        "follow_redirects": True,
        # verify defaults True; keep it explicit so a future reviewer can grep
        # for verify= in this code path and confirm we never disabled it.
        "verify": True,
    }
    if transport is not None:
        kwargs["transport"] = transport
    return httpx.Client(**kwargs)


class PricingSource(ABC):
    """Abstract base for every pricing source adapter."""

    #: Adapter identifier; persisted into ``PricingSnapshot.source``.
    name: str = "base"
    #: Names of env vars the adapter REQUIRES. Empty list means no auth.
    requires_env_vars: list[str] = []
    #: License + attribution string persisted into each snapshot.
    license_str: str = "PUBLIC DOMAIN — generic"
    #: Canonical doc / homepage URL for the source.
    homepage_url: str = ""

    def __init__(
        self,
        *,
        client: Optional[httpx.Client] = None,
        cache_root: Path = HTTP_CACHE_ROOT,
    ) -> None:
        self._owns_client = client is None
        self._client: httpx.Client = client or build_client()
        self._cache_root = cache_root

    def close(self) -> None:
        if self._owns_client:
            try:
                self._client.close()
            except Exception:  # noqa: BLE001
                pass

    def __enter__(self) -> "PricingSource":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # --- env / auth ---

    def env(self, var: str) -> Optional[str]:
        v = os.getenv(var)
        if v is None or v.strip() == "":
            return None
        return v.strip()

    def missing_env(self) -> list[str]:
        return [v for v in self.requires_env_vars if self.env(v) is None]

    def is_ready(self) -> bool:
        return not self.missing_env()

    # --- HTTP w/ cache ---

    def http_get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        *,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ) -> dict[str, Any]:
        return self._http_request("GET", url, params=params, body=None, ttl_seconds=ttl_seconds)

    def http_post_json(
        self,
        url: str,
        body: dict[str, Any],
        *,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ) -> dict[str, Any]:
        return self._http_request("POST", url, params=None, body=body, ttl_seconds=ttl_seconds)

    def _http_request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict[str, Any]],
        body: Optional[Any],
        ttl_seconds: int,
    ) -> dict[str, Any]:
        key = _cache_key(method, url, params, body)
        cache_path = self._cache_root / self.name / f"{key}.json"

        if _is_fresh(cache_path, ttl_seconds):
            cached = _read_cache(cache_path)
            if cached is not None:
                LOG.debug("%s cache HIT %s", self.name, url)
                return cached

        LOG.debug("%s cache MISS %s", self.name, url)

        if method.upper() == "GET":
            resp = self._client.get(url, params=params)
        elif method.upper() == "POST":
            resp = self._client.post(url, json=body)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        resp.raise_for_status()
        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise httpx.HTTPError(f"Non-JSON response from {url}: {exc}") from exc

        if not isinstance(payload, dict):
            payload = {"_root": payload}

        _write_cache(cache_path, payload)
        return payload

    # --- subclass contract ---

    @abstractmethod
    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        """Fetch and return ``PricingSnapshot``s for ``series_ids``."""

    @abstractmethod
    def default_series(self) -> list[str]:
        """Curated default list of series ids for a periodic refresh."""
