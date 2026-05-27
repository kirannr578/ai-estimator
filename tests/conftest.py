"""Shared pytest config — registers `@pytest.mark.integration` and the
opt-in policy from the Tier 1 pricing brief:

    Integration tests are skipped by default. Run them with
    ``PYTEST_RUN_INTEGRATION=1 pytest -m integration``.

Unit tests under ``tests/`` MUST pass offline. Anything that hits a real
network endpoint is required to carry ``@pytest.mark.integration``.
"""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that hit a real network endpoint; "
        "skipped by default unless PYTEST_RUN_INTEGRATION=1",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if os.environ.get("PYTEST_RUN_INTEGRATION") == "1":
        return
    skip_integration = pytest.mark.skip(
        reason="integration test — set PYTEST_RUN_INTEGRATION=1 to enable",
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
