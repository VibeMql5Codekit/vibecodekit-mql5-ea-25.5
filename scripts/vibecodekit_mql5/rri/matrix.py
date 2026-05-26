"""mql5-rri-matrix — 8 quality dim × 8 axis = 64-cell audit matrix.

Each cell is one of PASS / WARN / FAIL / N/A. Per Plan v5 §10:

    EA ships v1.0 when ≥ 56/64 PASS, 0 FAIL, ≤ 8 WARN.
    Enterprise compliance when ≥ 60/64 PASS, 0 FAIL, ≤ 4 WARN.

This module fills the matrix from a JSON inputs payload (so the same
populator is reusable by `rri_bt.py` and `layer6_quality_matrix.py`)
and emits an HTML report with color-coded cells.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

DIMS: tuple[str, ...] = (
    "d_correctness",
    "d_risk",
    "d_robustness",
    "d_perf",
    "d_maintainability",
    "d_observability",
    "d_broker_safety",
    "d_inference",
)

AXES: tuple[str, ...] = (
    "design",
    "implement",
    "unit_test",
    "integration",
    "backtest",
    "walk_forward",
    "multi_broker",
    "live_canary",
)

STATUSES: tuple[str, ...] = ("PASS", "WARN", "FAIL", "N/A")

_STATUS_COLORS: dict[str, str] = {
    "PASS": "#2e7d32",
    "WARN": "#ed6c02",
    "FAIL": "#c62828",
    "N/A": "#9e9e9e",
}


@dataclass(frozen=True)
class CellResult:
    dim: str
    axis: str
    status: str
    note: str = ""


@dataclass
class MatrixReport:
    cells: dict[tuple[str, str], CellResult] = field(default_factory=dict)

    def set(self, dim: str, axis: str, status: str, note: str = "") -> None:
        if dim not in DIMS:
            raise ValueError(f"unknown dim: {dim!r}")
        if axis not in AXES:
            raise ValueError(f"unknown axis: {axis!r}")
        if status not in STATUSES:
            raise ValueError(f"unknown status: {status!r}")
        self.cells[(dim, axis)] = CellResult(dim, axis, status, note)

    def get(self, dim: str, axis: str) -> CellResult:
        return self.cells.get((dim, axis), CellResult(dim, axis, "N/A"))

    def counts(self) -> dict[str, int]:
        counts = {s: 0 for s in STATUSES}
        for d in DIMS:
            for a in AXES:
                counts[self.get(d, a).status] += 1
        return counts

    def passes_personal(self) -> bool:
        c = self.counts()
        return c["PASS"] >= 56 and c["FAIL"] == 0 and c["WARN"] <= 8

    def passes_enterprise(self) -> bool:
        c = self.counts()
        return c["PASS"] >= 60 and c["FAIL"] == 0 and c["WARN"] <= 4


def populate_full(matrix: MatrixReport, status: str, note: str = "") -> MatrixReport:
    """Initialise every cell. Useful test helper."""
    for d in DIMS:
        for a in AXES:
            matrix.set(d, a, status, note)
    return matrix


def populate_from_inputs(inputs: dict) -> MatrixReport:
    """Build a matrix from a structured inputs JSON payload.

    The payload is a dict keyed by ``"<dim>/<axis>"`` with values
    ``{"status": "PASS|WARN|FAIL|N/A", "note": "..."}``. Missing cells stay
    N/A.
    """
    matrix = MatrixReport()
    for key, payload in inputs.items():
        if "/" not in key:
            raise ValueError(f"matrix key must be 'dim/axis', got {key!r}")
        dim, axis = key.split("/", 1)
        matrix.set(dim, axis, payload.get("status", "N/A"), payload.get("note", ""))
    return matrix


def populate_from_gate_reports(report_dir: Path) -> tuple[MatrixReport, list[str]]:
    """Build a matrix by scanning ``--gate-report`` envelopes in a directory.

    Every file matching ``gate-report-*.json`` is read and its top-level
    ``matrix`` block (``{dim, axis, status}``) determines which cell to
    fill. The optional ``summary`` from the envelope becomes the cell
    ``note`` so reviewers can hover-trace the verdict.

    Returns ``(matrix, evidence_paths)`` where ``evidence_paths`` is the
    sorted list of report files that contributed at least one cell.

    Files lacking a ``matrix`` block are silently ignored — they're
    typically tools whose output doesn't map to one of the 8 dimensions
    (e.g. ``mql5-doctor``).
    """

    matrix = MatrixReport()
    evidence: list[str] = []
    for path in sorted(report_dir.rglob("gate-report-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cell = payload.get("matrix")
        if not isinstance(cell, dict):
            continue
        dim = cell.get("dim")
        axis = cell.get("axis")
        status = cell.get("status", "N/A")
        if not dim or not axis:
            continue
        if dim not in DIMS or axis not in AXES:
            continue
        if status not in STATUSES:
            continue
        note = str(payload.get("summary", "")).strip()
        matrix.set(dim, axis, status, note)
        evidence.append(str(path))
    return matrix, evidence


def render_html(matrix: MatrixReport) -> str:
    head_cells = "".join(f"<th>{escape(a)}</th>" for a in AXES)
    body_rows = []
    for d in DIMS:
        row_cells = [f"<th>{escape(d)}</th>"]
        for a in AXES:
            cell = matrix.get(d, a)
            color = _STATUS_COLORS[cell.status]
            title = escape(cell.note) if cell.note else ""
            row_cells.append(
                f'<td style="background:{color};color:white" title="{title}">'
                f"{escape(cell.status)}</td>"
            )
        body_rows.append("<tr>" + "".join(row_cells) + "</tr>")
    counts = matrix.counts()
    summary = (
        f"PASS={counts['PASS']} WARN={counts['WARN']} "
        f"FAIL={counts['FAIL']} N/A={counts['N/A']}"
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>mql5 quality matrix</title>"
        "<style>table{border-collapse:collapse}th,td{border:1px solid #444;"
        "padding:6px;font-family:monospace;text-align:center}</style>"
        f"</head><body><h1>mql5 quality matrix</h1><p>{escape(summary)}</p>"
        f"<table><thead><tr><th></th>{head_cells}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table></body></html>"
    )


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="mql5-rri-matrix")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--inputs", type=Path, default=None,
                     help="JSON file mapping 'dim/axis' to {status, note}")
    src.add_argument("--collect", type=Path, default=None,
                     help="Directory of gate-report-*.json envelopes; "
                          "each envelope's `matrix` block fills one cell.")
    ap.add_argument("--output", type=Path, default=Path("quality-matrix.html"))
    args = ap.parse_args()

    evidence: list[str] = []
    if args.inputs and args.inputs.exists():
        payload = json.loads(args.inputs.read_text(encoding="utf-8"))
        matrix = populate_from_inputs(payload)
        evidence.append(str(args.inputs))
    elif args.collect and args.collect.exists():
        matrix, evidence = populate_from_gate_reports(args.collect)
    else:
        matrix = MatrixReport()  # all N/A
    args.output.write_text(render_html(matrix), encoding="utf-8")

    counts = matrix.counts()
    print(json.dumps({
        "output": str(args.output),
        "counts": counts,
        "passes_personal": matrix.passes_personal(),
        "passes_enterprise": matrix.passes_enterprise(),
        "evidence": evidence,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
