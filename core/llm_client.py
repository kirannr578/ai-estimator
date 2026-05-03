"""Provider-agnostic vision LLM client.

Both Anthropic (Claude) and OpenAI (GPT-4o family) implement the same
`analyze_image` / `analyze_text` interface. The right backend is chosen at
construction time based on the env vars that are set:

    * ANTHROPIC_API_KEY -> Anthropic (preferred when both are present)
    * OPENAI_API_KEY    -> OpenAI

All calls return *parsed JSON*. We re-prompt once if the model emits anything
that isn't valid JSON, and surface a clean error if the second attempt fails.
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


def _strip_json(raw: str) -> str:
    """Pull a JSON object/array out of a chatty LLM response."""
    raw = raw.strip()
    # Fenced block first.
    m = JSON_BLOCK_RE.search(raw)
    if m:
        return m.group(1)
    # Otherwise grab from the first { or [ to the matching last } or ].
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
            self.client = anthropic.Anthropic(api_key=anthropic_key)
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        elif provider == "openai":
            if not openai_key:
                raise RuntimeError("OPENAI_API_KEY is not set.")
            import openai
            self.client = openai.OpenAI(api_key=openai_key)
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

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
    )
    def _call(
        self,
        system_prompt: str,
        user_prompt: str,
        image_path: Optional[str],
    ) -> LLMResponse:
        if self.provider == "anthropic":
            text = self._call_anthropic(system_prompt, user_prompt, image_path)
        else:
            text = self._call_openai(system_prompt, user_prompt, image_path)

        # Try parsing JSON; one repair attempt if needed.
        parsed = self._safe_json(text)
        if parsed is None:
            repair_prompt = (
                "Your previous response was not valid JSON. "
                "Re-emit ONLY the JSON value, with no commentary, no markdown "
                "fences, and no leading/trailing text."
            )
            if self.provider == "anthropic":
                text = self._call_anthropic(system_prompt, repair_prompt + "\n\n" + user_prompt, image_path)
            else:
                text = self._call_openai(system_prompt, repair_prompt + "\n\n" + user_prompt, image_path)
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
        # Concatenate all text blocks (model usually returns one).
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
