"""QA pair 25 / worker YY-3 / subsystem 10 — analyze.py CLI QA pass.

Designed scenarios (2 POS + 2 NEG + 3 EDGE = 7 scenarios; some scenarios
exercise more than one assertion). Surface of interest: argparse
contract, ``--no-drawings`` / ``--client-pdf`` / ``--render-proposal``
flags, file / folder / zip inputs, exit codes, error handling, and
output-path semantics.

LLM-spend guardrail: the brief forbids real LLM calls in this slice.
Tests that would otherwise reach the LLM (any non-empty PDF folder)
are scoped to ``_gather_pdfs`` (which is a pure-Python helper with no
network surface) or to subprocess invocations that exit BEFORE the
LLM dispatch:

  * ``--help`` exits 0 immediately
  * missing positional → argparse exit 2 immediately
  * non-existent path → exits via ``_gather_pdfs``\\'s ``SystemExit``
  * empty folder → ``main()`` returns 2 via the
    ``if not pdf_paths: ... return 2`` branch
  * folder with only a ZIP and no PDFs → same "no PDFs found" branch

Findings discovered while writing these tests are filed as
``pytest.mark.xfail(reason="QA-3 finding #N: ...")`` per the brief — no
bug fixes ship in this slice.

Findings surfaced (cross-ref docs/QA_REPORT_EXPORTS_2026-05-28.md):

* **B3-1** — ``analyze.py._build_client_pdf`` does NOT forward the
  ``alternates_section`` block from ``config/client_quote.json`` to
  ``core.exporter_pdf.build_quote_pdf`` via the ``alternates_config``
  kwarg. Net effect: ``alternates_section.enabled = false`` in the
  config is silently ignored on the ``--client-pdf`` code path. The
  Streamlit / library callers honour the toggle correctly; only the
  CLI is missing the wiring. Severity: MEDIUM — the field exists, is
  documented, and is in the canonical config file, but has no effect
  on the CLI flow it was added for.
"""

from __future__ import annotations

import inspect
import io
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


# Resolve the absolute paths to the venv Python and analyze.py.  We
# keep the .venv\Scripts\python invocation pattern from the brief so
# the subprocess hits the same interpreter the rest of the test suite
# runs under.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYTHON = _REPO_ROOT / ".venv" / "Scripts" / "python.exe"
_ANALYZE = _REPO_ROOT / "analyze.py"


def _run_cli(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Helper: run ``python analyze.py <args>`` and capture stdout/stderr.

    Never invokes the LLM — every callsite below scopes its arguments
    so the run exits BEFORE the LLM dispatch.
    """
    cmd = [str(_PYTHON), str(_ANALYZE), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd or _REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


# ---------------------------------------------------------------------------
# Subsystem 10 — analyze.py CLI
# ---------------------------------------------------------------------------


class TestQACliPositive:
    """Scenario QA10-P-1, QA10-P-2 — argparse contract + helper coverage."""

    def test_qa_cli_p1_help_lists_required_flags_and_exits_zero(self) -> None:
        """QA10-P-1: ``analyze.py --help`` exits 0 and the help text
        advertises every documented flag mentioned in the brief."""
        result = _run_cli(["--help"])
        assert result.returncode == 0, (
            f"--help returned {result.returncode}; stderr=\n{result.stderr}"
        )
        out = result.stdout
        for flag in (
            "--recursive",
            "--limit",
            "--out",
            "--provider",
            "--model",
            "--no-drawings",
            "--client-pdf",
            "--render-proposal",
            "--cost-db",
        ):
            assert flag in out, f"--help missing flag {flag!r}"

    def test_qa_cli_p2_gather_pdfs_picks_up_pdfs_in_folder(
        self, tmp_path: Path
    ) -> None:
        """QA10-P-2: ``_gather_pdfs`` helper is the single source of truth
        for input discovery. A folder with two fake .pdf files returns
        both, sorted; recursive=False excludes sub-folders."""
        from analyze import _gather_pdfs

        (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
        sub = tmp_path / "deep"
        sub.mkdir()
        (sub / "nested.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        flat = _gather_pdfs(tmp_path, recursive=False, include_drawings=True)
        assert [p.name for p in flat] == ["a.pdf", "b.pdf"]

        recursive = _gather_pdfs(tmp_path, recursive=True, include_drawings=True)
        names = [p.name for p in recursive]
        assert "a.pdf" in names
        assert "b.pdf" in names
        assert "nested.pdf" in names


class TestQACliNegative:
    """Scenario QA10-N-1, QA10-N-2 — error paths must surface clear messages."""

    def test_qa_cli_n1_nonexistent_path_exits_nonzero(self, tmp_path: Path) -> None:
        """QA10-N-1: ``analyze.py <does-not-exist>`` exits with a non-zero
        code AND surfaces an error message naming the offending path.
        The error path is in ``_gather_pdfs`` (raises ``SystemExit``)."""
        missing = tmp_path / "no-such-folder-or-file"
        result = _run_cli([str(missing)])
        assert result.returncode != 0, (
            "expected non-zero exit; "
            f"stdout=\n{result.stdout}\nstderr=\n{result.stderr}"
        )
        combined = result.stdout + result.stderr
        # The exact phrase from _gather_pdfs.
        assert "Not a PDF or directory" in combined, (
            f"missing 'Not a PDF or directory' phrase; got\n{combined}"
        )

    def test_qa_cli_n2_empty_folder_exits_with_no_pdfs_message(
        self, tmp_path: Path
    ) -> None:
        """QA10-N-2: a folder containing no PDFs (and no relevant files)
        triggers the ``log.error('No PDFs found.'); return 2`` branch.

        The folder must EXIST (otherwise we hit the N-1 path instead)."""
        empty = tmp_path / "empty"
        empty.mkdir()
        out_dir = tmp_path / "out"
        result = _run_cli([str(empty), "--out", str(out_dir)])
        assert result.returncode == 2, (
            f"expected exit 2; got {result.returncode}\n"
            f"stdout=\n{result.stdout}\nstderr=\n{result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "No PDFs found" in combined


class TestQACliEdge:
    """Scenario QA10-E-1, QA10-E-2, QA10-E-3 — single-file input,
    zip-only folder, output-dir already exists."""

    def test_qa_cli_e1_single_pdf_file_input_accepted_by_gather_pdfs(
        self, tmp_path: Path
    ) -> None:
        """QA10-E-1: passing a single .pdf file (not a folder) is accepted
        and returns that one file as the discovery result.

        We scope the test to ``_gather_pdfs`` so we don't have to start
        the full LLM pipeline; the CLI branch ``analyze.py <file.pdf>``
        delegates straight to this function."""
        from analyze import _gather_pdfs

        only = tmp_path / "only.pdf"
        only.write_bytes(b"%PDF-1.4\n%%EOF\n")
        result = _gather_pdfs(only, recursive=False, include_drawings=True)
        assert [p.name for p in result] == ["only.pdf"]

    def test_qa_cli_e2_folder_with_only_zip_returns_no_pdfs(
        self, tmp_path: Path
    ) -> None:
        """QA10-E-2: a folder containing nothing but a .zip file (no
        loose .pdf siblings) does NOT auto-extract — the CLI emits the
        "No PDFs found." message and exits 2. This pins the current
        contract: zip auto-extraction is NOT supported; the user must
        unzip first.

        Pin this behaviour explicitly so a future "auto-extract zips"
        feature can flip the test from "exits 2" to "discovers
        contents" with a single line change."""
        zip_only = tmp_path / "zip-only"
        zip_only.mkdir()
        bundle = zip_only / "bundle.zip"
        # Build a tiny but valid zip with a single .pdf entry.
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("inside.pdf", b"%PDF-1.4\n%%EOF\n")
        bundle.write_bytes(buf.getvalue())

        out_dir = tmp_path / "out"
        result = _run_cli([str(zip_only), "--out", str(out_dir)])
        assert result.returncode == 2, (
            f"expected exit 2 (no-PDFs); got {result.returncode}\n"
            f"stdout=\n{result.stdout}\nstderr=\n{result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "No PDFs found" in combined

    def test_qa_cli_e3_existing_output_dir_does_not_crash_gather_phase(
        self, tmp_path: Path
    ) -> None:
        """QA10-E-3: ``--out`` pointing at an existing directory must not
        crash the early-exit branch. We use an empty input folder so the
        CLI exits with code 2 BEFORE any file would be written into
        ``--out`` — but the existence of the dir itself must not raise
        ``FileExistsError``.

        Note: ``args.out.mkdir(parents=True, exist_ok=True)`` runs only
        AFTER the early-exit check at line 246-247 of analyze.py. We
        guard the early-exit path here; deeper output-dir
        overwrite/append semantics live in the LLM-bearing path and are
        captured in the report as a coverage gap (no env-var LLM hook
        exists for safe deep-path testing)."""
        empty = tmp_path / "empty"
        empty.mkdir()
        # Pre-create the output directory + a file inside it so we
        # confirm exists-with-content is tolerated.
        out_dir = tmp_path / "exports_already_there"
        out_dir.mkdir()
        (out_dir / "preexisting.txt").write_text("pre-existing", encoding="utf-8")

        result = _run_cli([str(empty), "--out", str(out_dir)])
        # The early-exit happens before --out is touched; we just need
        # confirmation that the CLI didn't raise a FileExistsError or
        # similar before reaching that point.
        assert result.returncode == 2, (
            f"expected exit 2; got {result.returncode}\n"
            f"stdout=\n{result.stdout}\nstderr=\n{result.stderr}"
        )
        # Sanity: pre-existing file untouched.
        assert (out_dir / "preexisting.txt").read_text(encoding="utf-8") == "pre-existing"

    def test_qa_cli_e4_no_drawings_filters_large_pdfs_via_size_heuristic(
        self, tmp_path: Path
    ) -> None:
        """QA10-E-4 (bonus): ``--no-drawings`` ⇒ ``_gather_pdfs(include_drawings=False)``
        applies the 5 MB size heuristic from the implementation. A 6 MB
        sentinel file is filtered; a tiny sibling is kept.

        Note: the heuristic is a SIZE filter, not a content classifier.
        A small PDF that happens to be a drawing will still pass through
        — captured as a coverage gap in the report."""
        from analyze import _gather_pdfs

        small = tmp_path / "small.pdf"
        small.write_bytes(b"%PDF-1.4\n%%EOF\n")
        big = tmp_path / "big.pdf"
        # Write a file just over 5 MB. The header is a real PDF marker
        # so the .pdf extension + the contents both pass the
        # ``suffix.lower() == ".pdf"`` and ``is_file`` checks.
        big.write_bytes(b"%PDF-1.4\n" + b"\x00" * (5 * 1024 * 1024 + 1024) + b"%%EOF\n")

        with_drawings = _gather_pdfs(tmp_path, recursive=False, include_drawings=True)
        assert {p.name for p in with_drawings} == {"small.pdf", "big.pdf"}

        no_drawings = _gather_pdfs(tmp_path, recursive=False, include_drawings=False)
        assert {p.name for p in no_drawings} == {"small.pdf"}, (
            "the >5 MB heuristic should have filtered big.pdf"
        )

    @pytest.mark.xfail(
        reason=(
            "QA-3 finding B3-1: analyze.py._build_client_pdf does not "
            "forward alternates_section config from client_quote.json to "
            "build_quote_pdf via the alternates_config kwarg. Net effect: "
            "the renderer-side toggle from QA9-E-2 cannot be controlled "
            "via the CLI. Fix: thread alternates_config through "
            "_build_client_pdf (parse the alternates_section block out "
            "of the raw JSON BEFORE QuoteConfig.model_validate strips "
            "it) and forward it to build_quote_pdf."
        ),
        strict=True,
    )
    def test_qa_cli_e5_build_client_pdf_forwards_alternates_section_config(
        self,
    ) -> None:
        """QA10-E-5: ``_build_client_pdf`` must pass an ``alternates_config``
        kwarg to ``build_quote_pdf`` so the JSON config can disable the
        section on the CLI path. Currently FAILS — the source of
        ``_build_client_pdf`` does not contain ``alternates_config=``.

        We inspect the function source rather than monkey-patching
        ``build_quote_pdf`` because the function is called only from
        inside the main run pipeline (which we can't enter without an
        LLM)."""
        from analyze import _build_client_pdf

        src = inspect.getsource(_build_client_pdf)
        assert "alternates_config" in src, (
            "_build_client_pdf source does not reference 'alternates_config'; "
            "the kwarg is not being forwarded to build_quote_pdf"
        )
