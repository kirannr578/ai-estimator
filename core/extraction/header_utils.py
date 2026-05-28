"""Shared header-indexing helpers for schedule extractors (Phase T3.6).

This module is the rule-of-three promotion of ``_header_index_excluding``
out of :mod:`core.extraction.door_schedule`.  The helper has been
load-bearing across **three** independent extractors:

* :mod:`core.extraction.door_schedule` (Phase T1) — original home; used
  to keep a ``ROOM NUMBER`` header from being stolen by the substring-
  tolerant ``MARK / NUMBER`` matcher.
* :mod:`core.extraction.panel_schedule` (Phase T2.6) — first downstream
  reuse; used to keep the bare ``A`` / ``B`` / ``C`` PHASE column
  from being shadowed by the substring-tolerant ``AMPS`` matcher.
* :mod:`core.extraction.lighting_schedule` (Phase T2.7) — second
  downstream reuse; used to disambiguate ``WATTS`` / ``W``,
  ``VOLTAGE`` / ``V``, ``QUANTITY`` / ``Q`` short-vs-long header
  pairs.

Phase T2.8 (HVAC equipment schedule) is the FOURTH consumer, with its
own ``T`` / ``TONS`` and ``H`` / ``HP`` collisions, so the rule of
three is now satisfied by a comfortable margin and the helper deserves
its own module.

All five originally-importing modules continue to work unchanged: the
public name is :func:`header_index_excluding` (no leading underscore —
this is now intentionally part of the package's internal API), and
``door_schedule`` keeps an alias under the legacy ``_header_index_
excluding`` name so frozen consumers (``finish_schedule``,
``room_schedule``, ``window_schedule``) don't need a coordinated
import-site update in this commit.
"""

from __future__ import annotations

import re

__all__ = ["header_index_excluding", "normalize_header"]


def normalize_header(s: str) -> str:
    """Upper-case ``s``, strip non-letter punctuation, collapse whitespace.

    Matches the per-module ``_normalize_header`` helpers in
    :mod:`door_schedule`, :mod:`panel_schedule`, :mod:`lighting_schedule`,
    etc.  Exposed here so future extractors can reuse it without
    re-defining the same five-line snippet.
    """
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def header_index_excluding(
    headers: list[str],
    candidates: tuple[str, ...],
    *,
    exclude: set[int],
) -> int | None:
    """Find the first header column matching ``candidates`` outside ``exclude``.

    Substring-tolerant matcher with a per-call exclusion set.  Used to
    resolve short-vs-long header collisions where a generic substring
    matcher would otherwise grab the wider column for the narrower
    candidate.  Two examples driving the design:

    * ``ROOM NUMBER`` header would otherwise be stolen by a shorter
      ``NUMBER`` mark candidate.  Pin the room column first
      (word-level matcher), then re-run mark with that column excluded.
    * ``WATTAGE`` and a separate ``W`` column on the same lighting
      schedule.  Pin ``WATTAGE`` first (long form), then resolve ``W``
      with the wider index excluded so the bare letter doesn't land on
      the wider header.

    The matcher first tries word-level membership (``norm.split()``)
    then falls back to substring containment to keep the existing
    door/panel/lighting test corpora green.

    Args:
        headers: The schedule's header row, raw text.
        candidates: Header tokens to look for, e.g. ``("MARK", "TAG")``.
        exclude: Indices of header columns the caller has already
            assigned to a more-specific role.  Pass an empty set when
            no columns are reserved.

    Returns:
        The 0-based index of the first matching header column outside
        ``exclude``, or ``None`` when no header matches.

    Examples::

        >>> header_index_excluding(["ROOM NUMBER", "MARK", "TYPE"],
        ...                        ("MARK", "NUMBER"), exclude={0})
        1
        >>> header_index_excluding(["TAG", "WATTAGE", "W"],
        ...                        ("W",), exclude={1})
        2
        >>> header_index_excluding(["TAG", "DESC"], ("HARDWARE",),
        ...                        exclude=set())  # returns None
    """
    for i, h in enumerate(headers):
        if i in exclude:
            continue
        norm = normalize_header(h)
        norm_words = set(norm.split())
        if any(c in norm_words for c in candidates):
            return i
        if any(c in norm for c in candidates):
            return i
    return None
