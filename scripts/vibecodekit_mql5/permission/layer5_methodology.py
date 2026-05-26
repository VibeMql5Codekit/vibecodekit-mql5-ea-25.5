"""Permission Layer 5 — METHODOLOGY-GATE (RRI 8-step completed).

Asks :mod:`vibecodekit_mql5.rri.step_workflow` whether the steps required
by ``mode`` all have ``.done`` sentinels in the state directory.

This layer is only enforced for TEAM and ENTERPRISE modes. Personal mode
trivially passes — but we still emit a JSON report so the orchestrator
can show why the layer was skipped.

Wave 5.2 — when ``activity_threshold`` is supplied (or the mode default
in :data:`step_sentinel.DEFAULT_THRESHOLDS` is honoured via
``enforce_activities=True``), the layer additionally audits each
sentinel's companion ``step-N-<name>.md`` for ticked ``## Activities``
checkboxes and fails the gate when the ratio is below the threshold.
This prevents an operator (or LLM agent) from rubber-stamping the
methodology gate by ``touch``-ing the sentinel without filling the step
output.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..rri import step_sentinel as ss
from ..rri import step_workflow as sw


def gate(
    state_dir: Path,
    mode: str = "personal",
    *,
    enforce_activities: bool = False,
    activity_threshold: float | None = None,
) -> dict:
    """Run the methodology gate.

    Parameters
    ----------
    state_dir:
        Directory containing ``<step>.done`` sentinels (and optionally
        their companion ``step-N-<name>.md`` outputs).
    mode:
        ``personal`` / ``team`` / ``enterprise``.
    enforce_activities:
        When ``True``, additionally audit ticked ``## Activities``
        checkboxes in each step output and fail the gate if the ratio
        drops below ``activity_threshold`` (or the mode default).
    activity_threshold:
        Override the ratio used by ``enforce_activities``. Falls back to
        :data:`step_sentinel.DEFAULT_THRESHOLDS[mode]`.
    """
    if mode not in sw.MODE_REQUIRED_STEPS:
        raise ValueError(f"unknown mode: {mode!r}")
    if mode == "personal" and not enforce_activities:
        return {
            "ok": True,
            "mode": mode,
            "skipped": True,
            "reason": "personal mode does not require methodology gate",
            "state_dir": str(state_dir),
        }
    required = sw.required_steps(mode)
    completed = sw.completed_steps(state_dir) if state_dir.exists() else ()
    missing = [s for s in required if s not in completed]

    result: dict = {
        "ok": not missing,
        "mode": mode,
        "state_dir": str(state_dir),
        "required_steps": list(required),
        "completed_steps": list(completed),
        "missing_steps": missing,
    }

    if enforce_activities:
        threshold = (
            activity_threshold
            if activity_threshold is not None
            else ss.DEFAULT_THRESHOLDS.get(mode, 1.0)
        )
        audits: list[dict] = []
        under_threshold: list[str] = []
        for step in required:
            if step not in completed:
                continue
            audit = ss.audit_step_output(step, state_dir=state_dir)
            audits.append(audit.to_dict())
            if not ss.passes_threshold(audit, threshold):
                under_threshold.append(step)
        result["activity_threshold"] = threshold
        result["activity_audits"] = audits
        result["activity_under_threshold"] = under_threshold
        if under_threshold:
            result["ok"] = False

    return result


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-permission-layer5")
    ap.add_argument("--state-dir", type=Path, default=Path(".rri-state"))
    ap.add_argument("--mode", choices=tuple(sw.MODE_REQUIRED_STEPS), default="personal")
    ap.add_argument(
        "--enforce-activities", action="store_true",
        help="Audit each step output for ticked ## Activities checkboxes "
        "and fail the gate when below threshold (Wave 5.2).",
    )
    ap.add_argument(
        "--activity-threshold", type=float, default=None,
        help="Fractional activity-completion threshold (0.0..1.0). "
        "Defaults to mode-based value in step_sentinel.DEFAULT_THRESHOLDS.",
    )
    args = ap.parse_args()
    result = gate(
        args.state_dir, args.mode,
        enforce_activities=args.enforce_activities,
        activity_threshold=args.activity_threshold,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
