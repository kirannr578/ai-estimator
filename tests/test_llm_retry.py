"""Regression tests for `core.llm_client` 429 / Retry-After handling.

Calibration v2 found two of the most important documents in the input
folder (Carr EFA RFCSP, USFWS Sol 140FC126R0017) silently dropped because
the SDK's stock retry stack ignored the `Retry-After` hint on the 429
response and gave up after 8 attempts well before the org's 30 K-TPM
ceiling reset.

These tests lock in:

  * the header-parsing helpers (OpenAI flavour)
  * that the retry loop respects a `Retry-After` floor
  * that on success the result is returned without sleeping past budget
  * that the wall-clock ceiling kicks in if the server keeps replying 429

They are pure-Python — no live HTTP, no API key, no SDK clients. We build
synthetic exception objects that look enough like `openai.RateLimitError`
to satisfy `_is_429` and the header reader.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from core.llm_client import (
    _extract_retry_after_seconds,
    _is_429,
    _parse_iso_seconds_until,
    _retry_with_backoff,
)


class _FakeResponse:
    def __init__(self, headers: dict[str, str], status_code: int = 429):
        self.headers = dict(headers)
        self.status_code = status_code


class _Fake429(Exception):
    """Duck-typed openai.RateLimitError surrogate.

    Carries `response`, `status_code` and `body` attributes — the same shape
    `core.llm_client` reads from.
    """

    def __init__(self, message: str, headers: dict[str, str] | None = None, body=None):
        super().__init__(message)
        self.response = _FakeResponse(headers or {})
        self.status_code = 429
        self.body = body


# ---- helper-level tests ----------------------------------------------------


def test_parse_iso_seconds_until_seconds_suffix() -> None:
    assert _parse_iso_seconds_until("32.203s") == pytest.approx(32.203)


def test_parse_iso_seconds_until_milliseconds_suffix() -> None:
    assert _parse_iso_seconds_until("450ms") == pytest.approx(0.45)


def test_parse_iso_seconds_until_bare_number_assumed_seconds() -> None:
    assert _parse_iso_seconds_until("5") == pytest.approx(5.0)


def test_parse_iso_seconds_until_garbage_returns_none() -> None:
    assert _parse_iso_seconds_until("never") is None
    assert _parse_iso_seconds_until("") is None
    assert _parse_iso_seconds_until(None) is None


def test_extract_retry_after_prefers_ms_header_over_seconds() -> None:
    exc = _Fake429("rate limited", {"Retry-After": "5", "retry-after-ms": "450"})
    # ms header is more precise; smaller value should win when both present.
    assert _extract_retry_after_seconds(exc, "openai") == pytest.approx(0.45)


def test_extract_retry_after_falls_back_to_body_message() -> None:
    body = {"error": {"message": "Rate limit reached. Please try again in 32.203s."}}
    exc = _Fake429("rate limited", {}, body=body)
    assert _extract_retry_after_seconds(exc, "openai") == pytest.approx(32.203)


def test_extract_retry_after_reads_anthropic_header() -> None:
    exc = _Fake429("rate limited", {"retry-after": "12"})
    assert _extract_retry_after_seconds(exc, "anthropic") == pytest.approx(12.0)


def test_is_429_recognizes_status_code() -> None:
    assert _is_429(_Fake429("rate limited"), "openai") is True
    assert _is_429(ValueError("not a rate limit"), "openai") is False


# ---- retry loop tests ------------------------------------------------------


class _Spy:
    """Records arguments passed to a stand-in `time.sleep`."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def test_retry_loop_respects_retry_after_floor(caplog) -> None:
    """First call 429s with `Retry-After: 5`; second call succeeds.

    The wrapper must:
      * sleep at least 5s (the server hint, as a floor)
      * return the second-call's value
      * log an INFO-level `attempt N/M, sleeping Xs` line
    """
    caplog.set_level(logging.INFO, logger="core.llm_client")
    sleep_spy = _Spy()

    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise _Fake429("rate limited", {"Retry-After": "5"})
        return SimpleNamespace(text="ok", parsed={"x": 1})

    result = _retry_with_backoff(
        fn,
        provider="openai",
        description="test:gpt-4o",
        max_attempts=4,
        wall_clock_budget_s=60.0,
        sleep_fn=sleep_spy,
    )

    assert result.parsed == {"x": 1}
    assert calls["n"] == 2
    assert len(sleep_spy.calls) == 1
    # Floor is 5s; jitter band is ±0.2s. Should sleep ≥ 4.8s.
    assert sleep_spy.calls[0] >= 4.8, sleep_spy.calls
    assert any(
        "attempt 1/4" in rec.message and "sleeping" in rec.message
        for rec in caplog.records
    ), [rec.message for rec in caplog.records]


def test_retry_loop_uses_fallback_when_no_header(caplog) -> None:
    """No header / no body hint -> exponential 2s, 4s, 8s, ... with cap."""
    caplog.set_level(logging.INFO, logger="core.llm_client")
    sleep_spy = _Spy()

    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _Fake429("rate limited", {})
        return "done"

    result = _retry_with_backoff(
        fn,
        provider="openai",
        description="test",
        max_attempts=5,
        wall_clock_budget_s=60.0,
        sleep_fn=sleep_spy,
    )

    assert result == "done"
    assert calls["n"] == 3
    assert len(sleep_spy.calls) == 2
    # First fallback ~2s ±jitter, second ~4s ±jitter.
    assert 1.5 <= sleep_spy.calls[0] <= 2.5
    assert 3.5 <= sleep_spy.calls[1] <= 4.5


def test_retry_loop_gives_up_after_max_attempts() -> None:
    """All attempts 429 -> the last 429 is raised to the caller."""
    sleep_spy = _Spy()

    def fn():
        raise _Fake429("rate limited", {"Retry-After": "0.1"})

    with pytest.raises(_Fake429):
        _retry_with_backoff(
            fn,
            provider="openai",
            description="test",
            max_attempts=3,
            wall_clock_budget_s=60.0,
            sleep_fn=sleep_spy,
        )
    # Two sleeps for three attempts (no sleep after the final failure).
    assert len(sleep_spy.calls) == 2


def test_retry_loop_does_not_retry_non_429() -> None:
    """A non-429 exception is reraised on the first try."""
    sleep_spy = _Spy()

    def fn():
        raise ValueError("schema problem")

    with pytest.raises(ValueError):
        _retry_with_backoff(
            fn,
            provider="openai",
            description="test",
            max_attempts=8,
            wall_clock_budget_s=60.0,
            sleep_fn=sleep_spy,
        )
    assert sleep_spy.calls == []
