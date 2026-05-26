"""Wave 4.3 — `mql5-rri-matrix` cell-coverage audit.

The 8×8 matrix has 64 cells but only 6 of those cells have a
discriminative gate-report auto-filler (Wave-1 W1.4 collector).  This
test suite pins the coverage classification so that:

* every gate-report-emitting tool's ``matrix_dim/matrix_axis`` lands
  on a ``CELL_COVERAGE`` entry tagged ``gate_auto``;
* the ``d_inference`` row stays ``manual`` (no automation today);
* the new ``--audit`` mode prints a stable JSON payload;
* the new gate-only threshold helpers correctly ignore non-gate cells.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from vibecodekit_mql5.rri import matrix as mtx


# ─────────────────────────────────────────────────────────────────────────────
# CELL_COVERAGE consistency
# ─────────────────────────────────────────────────────────────────────────────


def test_cell_coverage_covers_all_64_cells():
    """Every (dim, axis) pair must be classified — no omissions."""
    assert len(mtx.CELL_COVERAGE) == len(mtx.DIMS) * len(mtx.AXES) == 64
    for d in mtx.DIMS:
        for a in mtx.AXES:
            assert (d, a) in mtx.CELL_COVERAGE
            assert mtx.CELL_COVERAGE[(d, a)] in mtx.COVERAGE_CLASSES


def test_cell_coverage_counts_match_audit_summary():
    audit = mtx.audit_coverage()
    assert audit["total_cells"] == 64
    # gate_auto is exactly the cells declared in GATE_AUTO_CELLS.
    assert audit["counts"]["gate_auto"] == len(mtx.GATE_AUTO_CELLS) == 6
    # manual is exactly d_inference × all 8 axes.
    assert audit["counts"]["manual"] == 8
    # rri_broadcast fills everything else.
    assert audit["counts"]["rri_broadcast"] == 64 - 6 - 8
    assert sum(audit["counts"].values()) == 64


def test_d_inference_row_is_strictly_manual():
    """Whole d_inference row stays manual — no RRI review touches it."""
    for axis in mtx.AXES:
        assert mtx.CELL_COVERAGE[("d_inference", axis)] == "manual"


def test_gate_auto_cells_are_disjoint_from_manual():
    """A gate_auto cell can never also be classified manual / rri_broadcast."""
    for cell in mtx.GATE_AUTO_CELLS:
        assert mtx.CELL_COVERAGE[cell] == "gate_auto"


# ─────────────────────────────────────────────────────────────────────────────
# CELL_COVERAGE matches what gate-report tools actually emit
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def gate_report_emissions() -> dict[tuple[str, str], list[str]]:
    """Grep the source tree for every ``matrix_dim=`` / ``matrix_axis=``
    pair an ``emit_envelope`` call uses, and group by (dim, axis).
    """
    src_root = Path(__file__).resolve().parents[3] / "scripts" / "vibecodekit_mql5"
    pattern = re.compile(
        r"matrix_dim=\"([a-z_]+)\",\s*matrix_axis=\"([a-z_]+)\"",
        re.MULTILINE,
    )
    emissions: dict[tuple[str, str], list[str]] = {}
    for py_path in src_root.rglob("*.py"):
        if py_path.name == "matrix.py":
            continue  # the constants live here
        text = py_path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            cell = (match.group(1), match.group(2))
            emissions.setdefault(cell, []).append(py_path.stem)
    return emissions


def test_every_gate_report_tool_lands_on_a_gate_auto_cell(gate_report_emissions):
    """Tools that emit ``matrix_dim/matrix_axis`` must land on a
    ``gate_auto`` cell — otherwise the W1.4 collector would fill a
    cell the audit table says is manual / rri_broadcast.
    """
    for cell, tools in gate_report_emissions.items():
        assert mtx.CELL_COVERAGE.get(cell) == "gate_auto", (
            f"Tools {tools} emit gate-report into {cell}, "
            f"but CELL_COVERAGE says {mtx.CELL_COVERAGE.get(cell)!r}."
        )


def test_every_gate_auto_cell_has_at_least_one_emitting_tool(gate_report_emissions):
    """Every cell declared ``gate_auto`` must be backed by at least
    one real source-tree emitter — no phantom gate-auto entries.
    """
    for cell in mtx.GATE_AUTO_CELLS:
        assert cell in gate_report_emissions, (
            f"Cell {cell} is declared gate_auto but no source file "
            f"emits matrix_dim/matrix_axis matching it."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Coverage-aware counts + gate-only thresholds
# ─────────────────────────────────────────────────────────────────────────────


def test_counts_by_coverage_sums_to_64():
    m = mtx.MatrixReport()
    mtx.populate_full(m, "PASS")
    bucket = m.counts_by_coverage()
    total = sum(sum(b.values()) for b in bucket.values())
    assert total == 64
    assert sum(bucket["gate_auto"].values()) == 6
    assert sum(bucket["manual"].values()) == 8


def test_gate_only_thresholds_ignore_manual_and_rri_cells():
    """The d_inference row staying N/A must not affect the gate-only verdict."""
    m = mtx.MatrixReport()
    # Fill every gate_auto cell PASS, leave everything else N/A.
    for cell in mtx.GATE_AUTO_CELLS:
        m.set(*cell, "PASS")
    # 58 cells stay N/A → legacy threshold fails.
    assert not m.passes_personal()
    assert not m.passes_enterprise()
    # But gate-only thresholds succeed.
    assert m.passes_personal_gate_only()
    assert m.passes_enterprise_gate_only()


def test_gate_only_personal_allows_one_warn():
    m = mtx.MatrixReport()
    for cell in mtx.GATE_AUTO_CELLS:
        m.set(*cell, "PASS")
    # Down-grade one gate cell to WARN.
    first_cell = next(iter(mtx.GATE_AUTO_CELLS))
    m.set(*first_cell, "WARN")
    assert m.passes_personal_gate_only()
    # Enterprise is strict: zero WARN.
    assert not m.passes_enterprise_gate_only()


def test_gate_only_personal_fails_on_two_warn():
    m = mtx.MatrixReport()
    for cell in mtx.GATE_AUTO_CELLS:
        m.set(*cell, "PASS")
    warn_cells = list(mtx.GATE_AUTO_CELLS)[:2]
    for cell in warn_cells:
        m.set(*cell, "WARN")
    assert not m.passes_personal_gate_only()
    assert not m.passes_enterprise_gate_only()


def test_gate_only_fails_on_any_gate_fail():
    m = mtx.MatrixReport()
    for cell in mtx.GATE_AUTO_CELLS:
        m.set(*cell, "PASS")
    first_cell = next(iter(mtx.GATE_AUTO_CELLS))
    m.set(*first_cell, "FAIL")
    assert not m.passes_personal_gate_only()
    assert not m.passes_enterprise_gate_only()


# ─────────────────────────────────────────────────────────────────────────────
# CLI --audit mode
# ─────────────────────────────────────────────────────────────────────────────


def test_audit_cli_prints_stable_json(tmp_path: Path):
    """``mql5-rri-matrix --audit`` must emit JSON describing all 64 cells."""
    saved = sys.argv
    sys.argv = ["mql5-rri-matrix", "--audit"]
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                mtx.main()
            except SystemExit:
                pass
        payload = json.loads(buf.getvalue())
    finally:
        sys.argv = saved

    assert payload["total_cells"] == 64
    assert set(payload["counts"]) == {"gate_auto", "rri_broadcast", "manual"}
    assert payload["counts"]["gate_auto"] == 6
    # The cells list must include the tool names for gate_auto entries.
    gate_entries = payload["cells"]["gate_auto"]
    assert len(gate_entries) == 6
    for entry in gate_entries:
        assert "tools" in entry and entry["tools"]


def test_audit_cli_via_python_module(tmp_path: Path):
    """Run ``python -m vibecodekit_mql5.rri.matrix --audit`` end-to-end.

    The matrix CLI is exposed as a Python module rather than an
    installed console script (the rest of the kit uses
    ``python -m vibecodekit_mql5.rri.matrix --collect`` in CI), so we
    test the module-invocation path here.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "vibecodekit_mql5.rri.matrix", "--audit"],
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["total_cells"] == 64
    assert payload["counts"]["gate_auto"] == 6


# ─────────────────────────────────────────────────────────────────────────────
# Collector + new envelope fields
# ─────────────────────────────────────────────────────────────────────────────


def test_collector_envelope_exposes_coverage_breakdown(tmp_path: Path):
    """After Wave 4.3 the CLI envelope must include
    ``counts_by_coverage`` and the gate-only verdicts.
    """
    gate_dir = tmp_path / "gates"
    gate_dir.mkdir()
    for cell, tools in mtx.GATE_AUTO_CELLS.items():
        (gate_dir / f"gate-report-{tools[0]}.json").write_text(json.dumps({
            "schema_version": "1",
            "tool": tools[0],
            "ok": True,
            "exit_code": 0,
            "summary": "",
            "data": {},
            "evidence": [],
            "matrix": {"dim": cell[0], "axis": cell[1], "status": "PASS"},
        }), encoding="utf-8")
    html_out = tmp_path / "matrix.html"
    saved = sys.argv
    sys.argv = [
        "mql5-rri-matrix",
        "--collect", str(gate_dir),
        "--output", str(html_out),
    ]
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                mtx.main()
            except SystemExit:
                pass
        payload = json.loads(buf.getvalue())
    finally:
        sys.argv = saved
    assert payload["counts_by_coverage"]["gate_auto"]["PASS"] == 6
    assert payload["passes_personal_gate_only"] is True
    assert payload["passes_enterprise_gate_only"] is True
    # Legacy verdicts still reported (so consumers can decide which to read).
    assert "passes_personal" in payload and payload["passes_personal"] is False


def test_html_render_carries_coverage_metadata():
    m = mtx.MatrixReport()
    mtx.populate_full(m, "PASS")
    html = mtx.render_html(m)
    # Coverage classes must appear as data attributes on every cell.
    assert html.count('data-coverage="gate_auto"') == 6
    assert html.count('data-coverage="manual"') == 8
    assert html.count('data-coverage="rri_broadcast"') == 64 - 6 - 8
    # Legend block must mention all three classes + their counts.
    assert "gate_auto=6" in html
    assert "manual=8" in html
    assert "rri_broadcast=" in html
