"""Provider-agnostic vision LLM client.

Both Anthropic (Claude) and OpenAI (GPT-4o family) implement the same
`analyze_image` / `analyze_text` interface. The right backend is chosen at
construction time based on the env vars that are set:

    * ANTHROPIC_API_KEY -> Anthropic (preferred when both are present)
    * OPENAI_API_KEY    -> OpenAI

All calls return *parsed JSON*. We re-prompt once if the model emits anything
that isn't valid JSON, and surface a clean error if the second attempt fails.

Retry / rate-limit handling
---------------------------
The SDK-internal retry loops are disabled (`max_retries=0`) and replaced with
a single 429-aware loop here so the policy lives in one place:

  * On any 429 we parse the response headers and body for a `Retry-After`
    hint and use it as the **floor** for the next sleep (plus small jitter).
  * If no usable header is present we fall back to exponential backoff
    starting at 2s, doubling, capped at 60s.
  * The retry budget is 12 attempts per call AND a hard 5-minute wall-clock
    ceiling, whichever comes first.
  * Every retry is logged at INFO so calibration runs can attribute time
    loss to retries instead of staring at silent SDK behaviour.
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)

# 429 retry policy (see module docstring).
MAX_RETRY_ATTEMPTS = 12
WALL_CLOCK_BUDGET_S = 300.0
FALLBACK_BACKOFF_INITIAL_S = 2.0
FALLBACK_BACKOFF_CAP_S = 60.0
RETRY_JITTER_S = 0.2          # +/- this many seconds added to every sleep

T = TypeVar("T")


def _strip_json(raw: str) -> str:
    """Pull a JSON object/array out of a chatty LLM response."""
    raw = raw.strip()
    m = JSON_BLOCK_RE.search(raw)
    if m:
        return m.group(1)
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        end = raw.rfind(closer)
        if start != -1 and end != -1 and end > start:
            return raw[start : end + 1]
    return raw


def _encode_image(path: str) -> tuple[str, str]:
    """Return (mime_type, base64_data) for an image file."""
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    data = Path(path).read_bytes()
    return mime, base64.standard_b64encode(data).decode("ascii")


@dataclass
class LLMResponse:
    text: str
    parsed: Any
    provider: str
    model: str


# ---------------------------------------------------------------------------
# 429 handling — header parsing + retry loop
# ---------------------------------------------------------------------------


_TRY_AGAIN_RE = re.compile(r"try\s+again\s+in\s+([0-9]*\.?[0-9]+)\s*(ms|s)", re.IGNORECASE)


def _maybe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < 0 or f != f:  # reject negatives and NaN
        return None
    return f


def _parse_iso_seconds_until(value: Any) -> Optional[float]:
    """Parse `x-ratelimit-reset-*` style values.

    These appear in two flavours in the wild:
      * a duration suffixed with `s` / `ms` (e.g. ``"31.5s"`` or ``"450ms"``)
      * an ISO-8601 timestamp (e.g. ``"2026-05-21T23:10:33Z"``)

    Either way we return *seconds until reset* relative to wall-clock now,
    or None when we can't make sense of it.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    m = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*(ms|s)?", s, re.IGNORECASE)
    if m:
        num = float(m.group(1))
        if (m.group(2) or "s").lower() == "ms":
            num /= 1000.0
        return num

    # ISO-8601 timestamp: convert to seconds-until.
    try:
        # `fromisoformat` doesn't accept the trailing `Z` until 3.11; coerce.
        s_norm = s.replace("Z", "+00:00")
        ts = datetime.fromisoformat(s_norm)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = (ts - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, delta)
    except ValueError:
        return None


def _extract_retry_after_seconds(exc: Exception, provider: str) -> Optional[float]:
    """Best-effort: pull a server-suggested wait (in seconds) from a 429.

    Looks at, in priority order:

      OpenAI:
        1. ``retry-after-ms`` header (more precise than the seconds one)
        2. ``Retry-After`` header (RFC 7231: integer seconds OR HTTP-date)
        3. ``x-ratelimit-reset-tokens`` header
        4. ``try again in Xs`` / ``Xms`` substring in the error body

      Anthropic:
        1. ``retry-after`` header (RFC 7231: integer seconds OR HTTP-date)
        2. ``anthropic-ratelimit-tokens-reset`` header (ISO timestamp)
        3. ``try again in Xs`` substring in the error body
    """
    response = getattr(exc, "response", None)
    headers: dict = {}
    if response is not None:
        raw_headers = getattr(response, "headers", None)
        if raw_headers:
            try:
                headers = {str(k).lower(): str(v) for k, v in raw_headers.items()}
            except Exception:
                headers = {}

    candidates: list[float] = []

    if provider == "openai":
        ms = _maybe_float(headers.get("retry-after-ms"))
        if ms is not None:
            candidates.append(ms / 1000.0)
        retry_after = _parse_iso_seconds_until(headers.get("retry-after"))
        if retry_after is not None:
            candidates.append(retry_after)
        reset_tokens = _parse_iso_seconds_until(headers.get("x-ratelimit-reset-tokens"))
        if reset_tokens is not None:
            candidates.append(reset_tokens)
    elif provider == "anthropic":
        retry_after = _parse_iso_seconds_until(headers.get("retry-after"))
        if retry_after is not None:
            candidates.append(retry_after)
        anth_reset = _parse_iso_seconds_until(headers.get("anthropic-ratelimit-tokens-reset"))
        if anth_reset is not None:
            candidates.append(anth_reset)

    # Body-text fallback: openai's 429s include "Please try again in 32.203s"
    body_text = ""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") if isinstance(body.get("error"), dict) else body
        body_text = str(err.get("message", "")) if isinstance(err, dict) else ""
    if not body_text:
        body_text = str(exc)
    m = _TRY_AGAIN_RE.search(body_text)
    if m:
        num = float(m.group(1))
        if m.group(2).lower() == "ms":
            num /= 1000.0
        candidates.append(num)

    if not candidates:
        return None
    # Prefer the smallest *positive, non-trivial* hint: a 0-second value is
    # almost always a header artefact (token-bucket already reset by the
    # time we read it) and would defeat the back-off.
    positives = [c for c in candidates if c > 0]
    return min(positives) if positives else None


def _is_429(exc: Exception, provider: str) -> bool:
    """Return True if `exc` represents a 429 from the active provider."""
    # Status code on the exception (works for openai 2.x and anthropic 0.x).
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True

    # Status code on the underlying response.
    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) == 429:
        return True

    # Provider-specific exception types (avoid hard import at module top so a
    # missing SDK doesn't break the other backend).
    try:
        if provider == "openai":
            import openai
            if isinstance(exc, openai.RateLimitError):
                return True
        elif provider == "anthropic":
            import anthropic
            if isinstance(exc, anthropic.RateLimitError):
                return True
    except ImportError:
        pass

    return False


def _retry_with_backoff(
    fn: Callable[[], T],
    provider: str,
    description: str,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    wall_clock_budget_s: float = WALL_CLOCK_BUDGET_S,
    sleep_fn: Callable[[float], None] = time.sleep,
    log: logging.Logger = logger,
) -> T:
    """Run `fn`, retrying on provider 429s with header-aware backoff.

    Non-429 exceptions are reraised immediately. After `max_attempts` or
    `wall_clock_budget_s`, the most recent 429 is reraised.
    """
    start = time.monotonic()
    fallback = FALLBACK_BACKOFF_INITIAL_S
    last_exc: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if not _is_429(exc, provider):
                raise
            last_exc = exc

            elapsed = time.monotonic() - start
            remaining_budget = wall_clock_budget_s - elapsed
            if attempt >= max_attempts or remaining_budget <= 0:
                log.warning(
                    "%s: 429 budget exhausted after %d attempt(s) / %.1fs; giving up.",
                    description, attempt, elapsed,
                )
                raise

            hint = _extract_retry_after_seconds(exc, provider)
            if hint is None:
                sleep_s = fallback
                source = f"exp backoff {fallback:.1f}s"
                fallback = min(fallback * 2, FALLBACK_BACKOFF_CAP_S)
            else:
                # Header is a *floor*: don't go below it, and grow the
                # fallback so a subsequent 429 without a header doesn't
                # immediately undercut the server's guidance.
                sleep_s = max(hint, fallback)
                source = (
                    f"server hint {hint:.1f}s"
                    if sleep_s == hint
                    else f"server hint {hint:.1f}s floored to fallback {fallback:.1f}s"
                )
                fallback = min(max(fallback, hint) * 2, FALLBACK_BACKOFF_CAP_S)

            sleep_s += random.uniform(-RETRY_JITTER_S, RETRY_JITTER_S)
            sleep_s = max(0.05, sleep_s)
            # Don't sleep past the wall-clock budget; just take what we have.
            sleep_s = min(sleep_s, max(0.05, remaining_budget))

            log.info(
                "%s: 429 on attempt %d/%d, sleeping %.2fs (%s).",
                description, attempt, max_attempts, sleep_s, source,
            )
            sleep_fn(sleep_s)

    # The loop above either returns, raises, or falls through after the last
    # iteration's raise. This is defensive — typing requires a return.
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Retry loop exited without result")


class LLMClient:
    """One client, two backends. Pick automatically or force via `provider=`."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ):
        self.max_tokens = max_tokens
        self.temperature = temperature

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if provider is None:
            if anthropic_key:
                provider = "anthropic"
            elif openai_key:
                provider = "openai"
            else:
                raise RuntimeError(
                    "No LLM provider configured. Set ANTHROPIC_API_KEY or "
                    "OPENAI_API_KEY in your .env file."
                )

        self.provider = provider

        if provider == "anthropic":
            if not anthropic_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not set.")
            import anthropic
            # max_retries=0: we own the retry loop. See module docstring.
            self.client = anthropic.Anthropic(api_key=anthropic_key, max_retries=0)
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        elif provider == "openai":
            if not openai_key:
                raise RuntimeError("OPENAI_API_KEY is not set.")
            import openai
            self.client = openai.OpenAI(api_key=openai_key, max_retries=0)
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: str,
        extra_context: str = "",
    ) -> LLMResponse:
        """Send one image plus instructions; expect JSON back."""
        full_user = user_prompt
        if extra_context:
            full_user = f"{user_prompt}\n\n--- ADDITIONAL CONTEXT ---\n{extra_context}"

        return self._call(system_prompt, full_user, image_path=image_path)

    def analyze_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        """Text-only call; still expects JSON back."""
        return self._call(system_prompt, user_prompt, image_path=None)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _call(
        self,
        system_prompt: str,
        user_prompt: str,
        image_path: Optional[str],
    ) -> LLMResponse:
        description = f"{self.provider}:{self.model}"

        def _do_call(prompt: str) -> str:
            if self.provider == "anthropic":
                fn = lambda: self._call_anthropic(system_prompt, prompt, image_path)  # noqa: E731
            else:
                fn = lambda: self._call_openai(system_prompt, prompt, image_path)  # noqa: E731
            return _retry_with_backoff(fn, self.provider, description)

        text = _do_call(user_prompt)

        # Try parsing JSON; one repair attempt if needed.
        parsed = self._safe_json(text)
        if parsed is None:
            repair_prompt = (
                "Your previous response was not valid JSON. "
                "Re-emit ONLY the JSON value, with no commentary, no markdown "
                "fences, and no leading/trailing text."
            )
            text = _do_call(repair_prompt + "\n\n" + user_prompt)
            parsed = self._safe_json(text)
            if parsed is None:
                raise ValueError(
                    f"LLM did not return JSON. First 400 chars:\n{text[:400]}"
                )

        return LLMResponse(text=text, parsed=parsed, provider=self.provider, model=self.model)

    @staticmethod
    def _safe_json(raw: str) -> Any:
        try:
            return json.loads(_strip_json(raw))
        except json.JSONDecodeError:
            return None

    # --- Anthropic --------------------------------------------------------

    def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        image_path: Optional[str],
    ) -> str:
        content: list[dict] = []
        if image_path:
            mime, b64 = _encode_image(image_path)
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": b64,
                    },
                }
            )
        content.append({"type": "text", "text": user_prompt})

        msg = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        return "".join(
            block.text for block in msg.content if getattr(block, "type", None) == "text"
        )

    # --- OpenAI -----------------------------------------------------------

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        image_path: Optional[str],
    ) -> str:
        user_content: list[dict] = [{"type": "text", "text": user_prompt}]
        if image_path:
            mime, b64 = _encode_image(image_path)
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                }
            )

        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"} if not image_path else None,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return completion.choices[0].message.content or ""
