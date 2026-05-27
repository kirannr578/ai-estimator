"""Home Depot Pro / Lowe's for Pros public-catalog scraper — Phase C STUB.

Source:     Home Depot Pro Xtra (https://www.homedepot.com/c/Pro_Xtra) and
            Lowe's for Pros (https://www.lowesforpros.com/) public-facing
            catalog pages.
License:    Retailer-proprietary content. **PUBLIC PRICES ONLY.** Do not
            scrape MAP-protected prices, member-only pricing, or anything
            behind a login wall. Each retailer's ToS forbids automated
            scraping of logged-in content; honoring that is non-negotiable.

[Phase C — NOT YET IMPLEMENTED — stub only]

Why deferred:

- Public catalog pages render server-side but use anti-bot measures that
  trigger reliably against any scraper that doesn't carefully mimic browser
  behavior. A polite scraper would need:
    - Strict rate limit (≤ 1 req / 5 sec / SKU)
    - Real-browser User-Agent rotation
    - Backoff on 429 / 503
    - A list of pre-approved SKUs (NOT category-wide crawling)
    - A `robots.txt` honor check

- The estimating value-add is modest: the cost-DB seed + BLS PPI escalation
  cover the same commodity-class signals at the same precision.

Pre-approved SKU shortlist for v1 (~50 high-volume building-material SKUs)
is captured here as a TODO so the eventual implementation has a starting
scope and doesn't drift into broad catalog crawling.
"""

from __future__ import annotations

import logging
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


# TODO — for the eventual implementation, scope to ≤ 50 SKUs from this list.
# Categories aligned to BPC's most-used commodity classes.
_SHORTLIST_SKU_CATEGORIES: tuple[str, ...] = (
    "2x4 SPF stud (8' / 9' / 10')",
    "2x6 SPF stud (8' / 9' / 10')",
    "7/16\" OSB sheathing (4x8)",
    "1/2\" CDX plywood (4x8)",
    "1/2\" + 5/8\" Type X drywall (4x8 / 4x12)",
    "R-13 / R-19 fiberglass batts",
    "R-30 attic blanket / blown insulation",
    "Asphalt shingles — 3-tab + architectural (per square)",
    "Standing-seam metal panel — 24-ga (per LF)",
    "1/2\" copper Type-L tube (per 10' length)",
    "1/2\" + 3/4\" PEX tubing (per 100' coil)",
    "PVC SCH40 — 3\" / 4\" / 6\" (per 10' length)",
    "EMT conduit — 1/2\" / 3/4\" / 1\" (per 10' length)",
    "Romex 14/2 + 12/2 (per 250' coil)",
    "100A + 200A residential panelboard",
    "Single-pole + 3-way decora switches",
    "20A duplex receptacle, decora",
    "GFCI receptacle, 20A",
    "Recessed-can LED 6\" downlight",
    "ENERGY STAR exterior LED fixture",
    "0.05 lpm chrome lavatory faucet",
    "1.28 GPF elongated water closet",
    "Stainless undermount kitchen sink, 18-ga",
    "Premium interior latex paint (5-gal)",
    "Premium exterior acrylic paint (5-gal)",
    "Polyurethane caulk (10-oz tube)",
    "Self-leveling concrete patch (50-lb bag)",
    "Quikrete 80-lb concrete bag",
    "Rebar #4 (per 20' bar)",
    "Welded-wire mesh, 6x6 W1.4xW1.4 (per 5x10 sheet)",
    "Tapcon 1/4\" x 2 3/4\" (per 100-ct)",
    "GRK RSS 5/16\" x 3 1/8\" (per 100-ct)",
    "Galvanized joist hangers — LUS24 / LUS26",
    "Hurricane-tie clip H1 / H2.5A",
    "Vinyl double-hung window 36x60",
    "Hollow-metal door 3-0 x 7-0 (HM 16-ga frame)",
    "Solid-core wood door 3-0 x 7-0 (paint-grade)",
    "Schlage commercial lever lockset, Storeroom",
    "Closer LCN 4040XP",
    "T-bar acoustic ceiling grid (15/16\" main)",
    "Armstrong 2x4 ACT lay-in (Fissured)",
    "LVT 6\" x 36\" plank — commercial",
    "Carpet tile, 24x24 — commercial nylon",
    "4\" rubber base, per 4' piece",
    "Schluter trim — 1/2\" Schiene",
    "EJOT bituminous expansion joint",
    "Diesel #2 (PADD3 retail) — see EIA",  # cross-ref EIA source
)


class HDProCatalogSource(PricingSource):
    name = "hd_pro_catalog"
    requires_env_vars: list[str] = []
    license_str = "Retailer-proprietary content (public prices only)"
    homepage_url = "https://www.homedepot.com/c/Pro_Xtra"

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        # [Phase C — NOT YET IMPLEMENTED]
        # See module docstring for ToS / scope / shortlist rationale.
        LOG.info("HDProCatalogSource.fetch is a stub. See module docstring.")
        return []
