"""Smoke checks for the tx_agency_wd placeholder module.

Guards the structural-discovery documentation: the stub must raise
``NotImplementedError`` and its docstring must cite Tex. Gov't Code Ch. 2258
so future readers find the rationale.
"""

from __future__ import annotations

import pytest

from core.pricing.sources import tx_agency_wd


def test_harvest_recent_wds_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        tx_agency_wd.harvest_recent_wds()


def test_module_docstring_cites_ch_2258() -> None:
    doc = tx_agency_wd.__doc__ or ""
    assert "Ch. 2258" in doc, "module docstring must cite Tex. Gov't Code Ch. 2258"
    assert "pricing-data-sources.md" in doc, "module must point to the playbook"


def test_target_agencies_lists_core_tx_procurers() -> None:
    agencies = " ".join(tx_agency_wd.TARGET_AGENCIES)
    for needle in ("TxDOT", "TFC", "TWDB", "TDCJ"):
        assert needle in agencies, f"expected {needle} in TARGET_AGENCIES"
