"""Construction-cost index aggregator module — historical bin / re-export.

This module previously stubbed all four Phase C cost-index adapters
(ENR / AGC / Turner / NAHB). All four now ship as dedicated modules:

- ``core/pricing/sources/enr_cci.py``                — ENR 20-City CCI
- ``core/pricing/sources/agc_cci.py``                — AGC PPI-based CCI
- ``core/pricing/sources/turner_cci.py``             — Turner Building Cost Index
- ``core/pricing/sources/nahb_construction_cost.py`` — NAHB Cost of Constructing a Home

For backward compatibility with callers that import
``NAHBCostOfConstructingAHomeSource`` from this module (notably the
Phase C stub regression tests that pre-date the dedicated module), we
re-export the real adapter here. New code should import directly from
``core.pricing.sources.nahb_construction_cost`` instead.

The stub class that previously lived here returned an empty list from
``fetch()`` to signal "wired but not implemented". With NAHB now
shipped as a real adapter, that sentinel behavior is gone. Tests that
asserted empty-fetch behavior for NAHB have been migrated to
``tests/test_pricing_sources_nahb.py`` and assert real-fetch behavior.
"""

from __future__ import annotations

from core.pricing.sources.nahb_construction_cost import (
    NAHBCostOfConstructingAHomeSource,
)

__all__ = ["NAHBCostOfConstructingAHomeSource"]
