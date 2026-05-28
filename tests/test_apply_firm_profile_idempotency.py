"""Tests for `firm/_scripts/apply_firm_profile.py` Layer 3 idempotency.

The Day-1 regression: on a re-run, Layer 3 was re-filling Optional
Project Reference #4 / #5 with `picks[0]` / `picks[1]` even when those
projects were already filled into the primary #1 / #2 / #3 slots
earlier in the document. The scaffold worker had to manually revert
`bids/angelo-state-carr-efa-26-007/proposal/04-past-performance.md`
because of this.

These tests pin the fix:

1. First run on an empty template fills slots #1 / #2 / #3 with the
   picks in order.
2. Re-run on the already-filled document is a no-op (no diff).
3. `--force` bypasses the idempotency guard and refills the optional
   slots from the picks (the old, intentional-overwrite behavior).

All tests run on synthesized temp directories so they're independent
of the live `bids/` workspaces, and run offline.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EM_DASH = "\u2014"


@pytest.fixture()
def apply_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Load `firm/_scripts/apply_firm_profile.py` as a module, with its
    `ROOT` / `BIDS` pinned to a temp tree containing one workspace
    matching one of the known `past_project_selection_rules` entries.

    We pin to `angelo-state-carr-efa-26-007` because that workspace's
    pick list is well-defined in the live `firm-profile.json` and is
    the workspace the Day-1 regression actually hit.
    """
    spec = importlib.util.spec_from_file_location(
        "_apply_firm_profile_under_test",
        REPO_ROOT / "firm" / "_scripts" / "apply_firm_profile.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    bids_root = tmp_path / "bids"
    workspace = bids_root / "angelo-state-carr-efa-26-007"
    (workspace / "proposal").mkdir(parents=True)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "BIDS", bids_root)
    return mod, workspace


def _empty_past_perf_template() -> str:
    """Minimal past-performance template matching the live
    `bids/angelo-state-carr-efa-26-007/proposal/04-past-performance.md`
    shape: three primary headers + two optional headers, all with
    `[USER TO FILL: project name]` markers."""
    return (
        "# Past performance \u2014 synthetic\n"
        "\n"
        "> Strategy note.\n"
        "\n"
        "---\n"
        "\n"
        "## At-a-glance summary table\n"
        "\n"
        "| # | Project name | Owner | Contract value | Completion year | Same-team? | Why relevant |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 1 | `[USER TO FILL]` | `[USER TO FILL]` | `$[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` |\n"
        "| 2 | `[USER TO FILL]` | `[USER TO FILL]` | `$[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` |\n"
        "| 3 | `[USER TO FILL]` | `[USER TO FILL]` | `$[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` |\n"
        "| 4 (opt) | `[USER TO FILL]` | `[USER TO FILL]` | `$[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` |\n"
        "| 5 (opt) | `[USER TO FILL]` | `[USER TO FILL]` | `$[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL]` |\n"
        "\n"
        "---\n"
        "\n"
        "## Project Reference #1 \u2014 `[USER TO FILL: project name]`\n"
        "\n"
        "`[USER TO FILL: full template if 1st project surfaced]`\n"
        "\n"
        "## Project Reference #2 \u2014 `[USER TO FILL: project name]`\n"
        "\n"
        "`[USER TO FILL: full template if 2nd project surfaced]`\n"
        "\n"
        "## Project Reference #3 \u2014 `[USER TO FILL: project name]`\n"
        "\n"
        "`[USER TO FILL: full template if 3rd project surfaced]`\n"
        "\n"
        "## Optional Project Reference #4 \u2014 `[USER TO FILL: project name]`\n"
        "\n"
        "`[USER TO FILL: full template if 4th project surfaced]`\n"
        "\n"
        "## Optional Project Reference #5 \u2014 `[USER TO FILL: project name]`\n"
        "\n"
        "`[USER TO FILL: full template if 5th project surfaced]`\n"
    )


def test_first_run_fills_primary_three_slots(apply_module) -> None:
    """First run on an empty template fills #1 / #2 / #3 with the picks
    in order. Optional #4 / #5 are also filled in lock-step but with
    NO LEFTOVER picks (the workspace's pick list has only 3 entries),
    so they keep their original `[USER TO FILL: project name]` markers."""
    mod, workspace = apply_module
    pp_path = workspace / "proposal" / "04-past-performance.md"
    pp_path.write_text(_empty_past_perf_template(), encoding="utf-8")

    picks = mod.picks_for(workspace.name)
    assert len(picks) == 3, picks

    result = mod.process_file(pp_path, workspace.name)
    assert result["changed"] is True
    assert result["L3"] > 0, result

    rendered = pp_path.read_text(encoding="utf-8")
    for i, project in enumerate(picks, start=1):
        marker = f"Project Reference #{i} {EM_DASH} {project}"
        assert marker in rendered, (
            f"primary slot #{i} did not get pick {project!r}; first 2k:\n"
            f"{rendered[:2000]}"
        )
    assert (
        f"## Optional Project Reference #4 {EM_DASH} `[USER TO FILL"
        in rendered
    ), "optional #4 should stay empty when picks list is exhausted"
    assert (
        f"## Optional Project Reference #5 {EM_DASH} `[USER TO FILL"
        in rendered
    ), "optional #5 should stay empty when picks list is exhausted"


def test_rerun_on_filled_doc_is_no_op(apply_module) -> None:
    """The regression we are fixing: re-running on a doc that already
    has the three primary slots filled must NOT re-fill the optional
    slots #4 / #5 with `picks[0]` / `picks[1]`."""
    mod, workspace = apply_module
    pp_path = workspace / "proposal" / "04-past-performance.md"
    pp_path.write_text(_empty_past_perf_template(), encoding="utf-8")

    mod.process_file(pp_path, workspace.name)
    snapshot = pp_path.read_text(encoding="utf-8")

    result = mod.process_file(pp_path, workspace.name)
    rendered = pp_path.read_text(encoding="utf-8")

    assert rendered == snapshot, (
        "re-run wrote a diff into the past-performance file; idempotency "
        "guard failed.\n=== snapshot tail ===\n"
        f"{snapshot[-1200:]}\n=== rendered tail ===\n{rendered[-1200:]}"
    )
    assert result["changed"] is False, result
    picks = mod.picks_for(workspace.name)
    opt4_section_tail = rendered.split(
        "## Optional Project Reference #4", 1
    )[1]
    opt4_body = opt4_section_tail.split("## ", 1)[0]
    for project in picks:
        assert project not in opt4_body, (
            f"pick {project!r} leaked into Optional Project Reference #4 "
            f"section on re-run."
        )


def test_force_flag_refills_optional_slots(apply_module) -> None:
    """`--force` bypasses the idempotency guard \u2014 re-running with
    `force=True` on a filled doc re-applies picks[0] / picks[1] into
    the optional slots #4 / #5 (the old, intentional-overwrite
    behavior)."""
    mod, workspace = apply_module
    pp_path = workspace / "proposal" / "04-past-performance.md"
    pp_path.write_text(_empty_past_perf_template(), encoding="utf-8")

    mod.process_file(pp_path, workspace.name)
    pre_force = pp_path.read_text(encoding="utf-8")

    result = mod.process_file(pp_path, workspace.name, force=True)
    rendered = pp_path.read_text(encoding="utf-8")

    assert rendered != pre_force, (
        "`--force` did not change the rendered file even though picks "
        "should re-fill the optional slots."
    )
    assert result["changed"] is True
    picks = mod.picks_for(workspace.name)
    after_opt4 = rendered.split(
        "## Optional Project Reference #4", 1
    )[1]
    opt4_body, after_opt5_marker = (
        after_opt4.split("## Optional Project Reference #5", 1)
        if "## Optional Project Reference #5" in after_opt4
        else (after_opt4, "")
    )
    opt5_body = after_opt5_marker
    assert picks[0] in opt4_body, (
        f"--force did not refill Optional #4 with picks[0]={picks[0]!r}: "
        f"{opt4_body!r}"
    )
    assert picks[1] in opt5_body, (
        f"--force did not refill Optional #5 with picks[1]={picks[1]!r}: "
        f"{opt5_body[:400]!r}"
    )


# ---------------------------------------------------------------------------
# Pair-12 cleanup: additional regression tests covering edge cases of the
# idempotency guard that the original 3 tests don't exercise.
# ---------------------------------------------------------------------------


def test_five_picks_fill_all_five_slots_then_rerun_is_noop(
    apply_module, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the workspace's pick list has 5 entries (vs. the 3 we ship by
    default in `firm-profile.json`), slots #1-#5 all fill on the first
    run and a second run is a no-op.

    The selection dict is monkeypatched onto the loaded module rather
    than touching the live `firm-profile.json`, so the test is hermetic.
    """
    mod, workspace = apply_module
    pp_path = workspace / "proposal" / "04-past-performance.md"
    pp_path.write_text(_empty_past_perf_template(), encoding="utf-8")

    extra_picks = [
        "Hindu Temple of Southlake",
        "Holiday Inn (Hall Park)",
        "250-500+ single-family-home portfolio",
        "Lavon RV Park",
        "Test Project X (synthetic)",
    ]
    monkeypatch.setitem(
        mod.SELECTION, workspace.name,
        {"rationale": "test", "picks": extra_picks},
    )
    monkeypatch.setitem(
        mod.PAST_PROJECT_BLURBS,
        "Test Project X (synthetic)",
        "**Test Project X (synthetic)** \u2014 synthesised for the "
        "5-picks regression test; never appears in production picks.",
    )

    result = mod.process_file(pp_path, workspace.name)
    assert result["changed"] is True
    rendered = pp_path.read_text(encoding="utf-8")

    for i, project in enumerate(extra_picks, start=1):
        marker = f"Project Reference #{i} {EM_DASH} {project}"
        assert marker in rendered, (
            f"slot #{i} did not get pick {project!r}; first 2k:\n"
            f"{rendered[:2000]}"
        )

    rerun_snapshot = rendered
    rerun_result = mod.process_file(pp_path, workspace.name)
    rerun_rendered = pp_path.read_text(encoding="utf-8")
    assert rerun_rendered == rerun_snapshot, (
        "second run on a fully-filled doc must be a no-op."
    )
    assert rerun_result["changed"] is False


def test_pick_list_evolves_between_runs_no_duplicates(
    apply_module, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When a slot-1-3 default is removed AND a new pick is appended
    between two runs, the second run must:

    1. Leave the already-filled primary slots untouched (they reference
       projects that are still on the live `picks` list).
    2. NOT re-fill optional slots #4 / #5 with picks that are already
       on the doc (the idempotency guard).
    3. Only newly-introduced picks land in still-open `[USER TO FILL]`
       optional slots.
    """
    mod, workspace = apply_module
    pp_path = workspace / "proposal" / "04-past-performance.md"
    pp_path.write_text(_empty_past_perf_template(), encoding="utf-8")

    initial_picks = [
        "Hindu Temple of Southlake",
        "Holiday Inn (Hall Park)",
        "250-500+ single-family-home portfolio",
    ]
    monkeypatch.setitem(
        mod.SELECTION, workspace.name,
        {"rationale": "test", "picks": list(initial_picks)},
    )
    mod.process_file(pp_path, workspace.name)
    after_first = pp_path.read_text(encoding="utf-8")
    for project in initial_picks:
        assert project in after_first

    evolved_picks = [
        "Hindu Temple of Southlake",
        "250-500+ single-family-home portfolio",
        "Lavon RV Park",
        "Test Project Y (synthetic)",
    ]
    monkeypatch.setitem(
        mod.SELECTION, workspace.name,
        {"rationale": "test", "picks": list(evolved_picks)},
    )
    monkeypatch.setitem(
        mod.PAST_PROJECT_BLURBS,
        "Test Project Y (synthetic)",
        "**Test Project Y (synthetic)** \u2014 synthesised for the "
        "evolved-picks regression test.",
    )

    mod.process_file(pp_path, workspace.name)
    after_second = pp_path.read_text(encoding="utf-8")

    primary_block = after_second.split(
        "## Optional Project Reference #4", 1
    )[0]
    for project in initial_picks:
        assert primary_block.count(
            f"Project Reference #{1 if project == initial_picks[0] else 2 if project == initial_picks[1] else 3} {EM_DASH} {project}"
        ) >= 1, (
            f"primary slot for {project!r} was disturbed by the second "
            f"run; primary block tail:\n{primary_block[-1500:]}"
        )

    optional_block = after_second.split(
        "## Optional Project Reference #4", 1
    )[1]
    assert "Hindu Temple of Southlake" not in optional_block.split(
        "## Optional Project Reference #5", 1
    )[0], (
        "pick already on the document leaked into Optional #4 on the "
        "evolved-picks rerun."
    )
    assert "Lavon RV Park" in optional_block, (
        "newly-added pick 'Lavon RV Park' did not land in any optional "
        "slot on the evolved-picks rerun."
    )


def test_already_filled_doc_skips_picks_that_appear_in_blurb_body(
    apply_module,
) -> None:
    """Defense-in-depth: if a pick name appears verbatim in the body
    of an already-filled section header (the blurb), the idempotency
    guard must recognise it as already-present and skip re-filling
    that pick into a later optional slot \u2014 even when the prior fill
    came from a different code path (e.g. a manual paste by the user).

    This pins the `_pick_already_present` substring scan: it sees the
    pick name anywhere in the document outside the picks-banner block,
    not just on the header line itself.
    """
    mod, workspace = apply_module
    pp_path = workspace / "proposal" / "04-past-performance.md"

    picks = mod.picks_for(workspace.name)
    assert picks, "fixture workspace must have non-empty picks"

    template = _empty_past_perf_template()
    template = template.replace(
        "## Project Reference #1 \u2014 `[USER TO FILL: project name]`\n"
        "\n"
        "`[USER TO FILL: full template if 1st project surfaced]`",
        f"## Project Reference #1 \u2014 {picks[0]}\n"
        f"\n"
        f"User-pasted blurb describing **{picks[0]}** with relevant "
        f"context already in place.",
    )
    pp_path.write_text(template, encoding="utf-8")

    mod.process_file(pp_path, workspace.name)
    rendered = pp_path.read_text(encoding="utf-8")

    optional_4 = rendered.split(
        "## Optional Project Reference #4", 1
    )[1].split("## ", 1)[0]
    assert picks[0] not in optional_4, (
        f"pick {picks[0]!r} (already in body of Reference #1 from a "
        f"manual paste) leaked into Optional #4 \u2014 the idempotency "
        f"guard's substring scan should have caught it."
    )
