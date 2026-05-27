#!/usr/bin/env bash
# build_reference_report.sh — Regenerate docs/reference-ea/REPORT.md from a freshly
# scaffolded reference EA. Numbers reported here are honest, reproducible measurements
# from this kit's own gates — not claims about live-trading performance.
#
# Run:  bash scripts/tools/build_reference_report.sh
# Output: runtime/reference-ea/SampleEA/  (gitignored build artefact)
#         docs/reference-ea/REPORT.md     (committed honest snapshot)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

REF_DIR="runtime/reference-ea"
REF_EA="$REF_DIR/SampleEA/SampleEA.mq5"
REPORT="docs/reference-ea/REPORT.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. Scaffold reference EA fresh
rm -rf "$REF_DIR"
mkdir -p "$REF_DIR"
mql5-build stdlib --name SampleEA --symbol EURUSD --tf H1 --out "$REF_DIR/SampleEA" >/dev/null

# 2. Run gates and capture raw output
mql5-lint              "$REF_EA"                              >"$TMP/lint.txt"           2>&1 || true
mql5-lint              "$REF_EA"                  --json      >"$TMP/lint.json"          2>&1 || true
mql5-trader-check      "$REF_EA"                              >"$TMP/trader17.txt"       2>&1 || true
mql5-trader-check      "$REF_EA"                  --json      >"$TMP/trader17.json"      2>&1 || true
mql5-permission --mode personal    "$REF_EA"      --json      >"$TMP/perm-personal.json" 2>&1 || true
mql5-permission --mode team        "$REF_EA"      --json      >"$TMP/perm-team.json"     2>&1 || true
mql5-permission --mode enterprise  "$REF_EA"      --json      >"$TMP/perm-enterprise.json" 2>&1 || true
mql5-matrix --mode TEAM --html "$TMP/matrix.html"             2>&1 \
    | sed "s|$TMP|<tmp>|g" >"$TMP/matrix.txt" || true
python -m vibecodekit_mql5.rri.matrix --audit                 >"$TMP/matrix-audit.json"  2>&1 || true

# 3. Extract structured numbers
python3 - "$TMP" >"$TMP/numbers.json" <<'PY'
import json, re, sys
from pathlib import Path
tmp = Path(sys.argv[1])

def read(name):
    return (tmp / name).read_text(encoding="utf-8", errors="replace")

def load(name):
    try:
        return json.loads(read(name))
    except Exception:
        return {}

lint_env = load("lint.json")
trader_env = load("trader17.json")
perm_personal = load("perm-personal.json")
perm_team = load("perm-team.json")
perm_ent = load("perm-enterprise.json")
matrix_audit = load("matrix-audit.json")

trader_summary = trader_env.get("summary", "")
m = re.search(r"(\d+)/(\d+)\s+PASS,\s*(\d+)\s+WARN,\s*(\d+)\s+N/A,\s*(\d+)\s+FAIL", trader_summary)
if m:
    t17_pass = int(m.group(1))
    t17_total = int(m.group(2))
    t17_warn = int(m.group(3))
    t17_na = int(m.group(4))
    t17_fail = int(m.group(5))
else:
    t17_pass = t17_total = t17_warn = t17_na = t17_fail = 0

def first_fail_layer(env):
    layers = env.get("data", {}).get("layers", [])
    for L in layers:
        if not L.get("ok"):
            return L.get("layer"), L.get("errors", [None])[0] if L.get("errors") else "(no detail)"
    return None, None

p_layer, p_err = first_fail_layer(perm_personal)
t_layer, t_err = first_fail_layer(perm_team)
e_layer, e_err = first_fail_layer(perm_ent)

matrix_txt = read("matrix.txt").strip()
mm = re.search(r"(\d+)/(\d+)\s+PASS\s*\(threshold:\s*(\d+),\s*gate:\s*(\w+)\)", matrix_txt)
if mm:
    mat_pass = int(mm.group(1))
    mat_total = int(mm.group(2))
    mat_threshold = int(mm.group(3))
    mat_gate = mm.group(4)
else:
    mat_pass = mat_total = mat_threshold = 0
    mat_gate = "?"

counts = matrix_audit.get("counts", {}) if isinstance(matrix_audit, dict) else {}
mat_gate_auto = counts.get("gate_auto", "?")
mat_rri_broadcast = counts.get("rri_broadcast", "?")
mat_manual = counts.get("manual", "?")

out = {
    "lint": {
        "errors": lint_env.get("data", {}).get("error_count", 0),
        "warnings": lint_env.get("data", {}).get("warn_count", 0),
        "findings": lint_env.get("data", {}).get("findings", []),
        "summary": lint_env.get("summary", ""),
    },
    "trader17": {
        "pass": t17_pass,
        "warn": t17_warn,
        "na": t17_na,
        "fail": t17_fail,
        "total": t17_total or 17,
        "gate_pass": t17_pass >= 15,
        "summary": trader_summary,
        "raw": read("trader17.txt").strip(),
    },
    "permission": {
        "personal":   {"ok": perm_personal.get("ok"), "fail_layer": p_layer, "error": p_err, "summary": perm_personal.get("summary", "")},
        "team":       {"ok": perm_team.get("ok"),     "fail_layer": t_layer, "error": t_err, "summary": perm_team.get("summary", "")},
        "enterprise": {"ok": perm_ent.get("ok"),      "fail_layer": e_layer, "error": e_err, "summary": perm_ent.get("summary", "")},
    },
    "matrix_cli": {
        "pass": mat_pass,
        "total": mat_total,
        "threshold": mat_threshold,
        "gate": mat_gate,
        "raw": matrix_txt,
    },
    "matrix_audit": {
        "gate_auto": mat_gate_auto,
        "rri_broadcast": mat_rri_broadcast,
        "manual": mat_manual,
    },
}
print(json.dumps(out, indent=2))
PY

NUMBERS_FILE="$TMP/numbers.json"

# 4. Render Markdown report
python3 - "$NUMBERS_FILE" "$REPORT" <<'PY'
import json, sys, datetime
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
out_path = Path(sys.argv[2])

lint = data["lint"]
t17 = data["trader17"]
perm = data["permission"]
matrix_cli = data["matrix_cli"]
matrix_audit = data["matrix_audit"]

def perm_row(mode, p):
    if p.get("ok"):
        verdict = "PASS"
    else:
        verdict = f"FAIL at layer {p.get('fail_layer')}"
    return f"| `--mode {mode}` | {verdict} | {p.get('summary', '').strip()} |"

lint_findings_block = "\n".join(
    f"- `{f['code']}` ({f['severity']}) at line {f['line']}: {f['message']}"
    for f in lint.get("findings", [])
) or "_(no findings)_"

md = f"""<!-- Generated by scripts/tools/build_reference_report.sh — do not hand-edit. -->
# Reference EA gate report — honest empirical numbers

> **What this is.** A reproducible snapshot of what this kit's own gates report when
> run against a freshly scaffolded EA (`mql5-build stdlib --name SampleEA --symbol
> EURUSD --tf H1`). Numbers below are real outputs from the CLI tools shipped in
> this repo. They describe **how the gates score this kit's own scaffold output**,
> not whether the resulting EA is profitable in live trading — those are different
> questions.
>
> **Heuristic disclosure.** `Trader-17`, the `8×8 quality matrix`, the `AP-XX`
> anti-pattern IDs, and the `RRI` personas are project-defined heuristics designed
> by this kit. They are opinionated guardrails, **not industry standards or
> certifications**. Treat them accordingly.
>
> **Regenerate with:**
> ```bash
> bash scripts/tools/build_reference_report.sh
> ```

## Setup

```bash
mql5-build stdlib --name SampleEA --symbol EURUSD --tf H1 \\
    --out runtime/reference-ea/SampleEA
```

Produces a minimal stdlib/netting scaffold. The signal in `OnTick` is a
placeholder — it never reaches a trade-placing call — so the gates below are
scoring **only the skeleton**, not a working strategy.

---

## 1. `mql5-lint` — anti-pattern detection

```
{lint['summary']}
```

{lint_findings_block}

> Lint passes ({lint['errors']} ERROR) — but the WARN finding (`AP-22`) reminds you
> that the bare scaffold has no order-placing call. That's the intended starting
> point; you wire `trade.Buy(...)` / `trade.Sell(...)` after editing the signal.

---

## 2. `mql5-trader-check` — Trader-17 readiness

```
{t17['summary']}
```

- **PASS:** {t17['pass']} / {t17['total']}
- **WARN:** {t17['warn']}
- **N/A:**  {t17['na']}
- **FAIL:** {t17['fail']}
- **Gate verdict:** {'PASS' if t17['gate_pass'] else 'FAIL'} (gate threshold ≥ 15 / 17 PASS)

The N/A items are items that need **external evidence** before they can score —
walk-forward XML, Monte-Carlo report, multi-broker comparison, overfit report,
VPS deployment, news-session policy, etc. A bare scaffold has none of these,
so several items are reported as N/A. The gate is **fail-closed**: until you
supply the evidence, it does not pass.

Full raw output:

```
{t17['raw']}
```

---

## 3. `mql5-permission` — 7-layer fail-fast pipeline

| Mode | Verdict | Summary |
|---|---|---|
{perm_row('personal',   perm['personal'])}
{perm_row('team',       perm['team'])}
{perm_row('enterprise', perm['enterprise'])}

Layer ordering (this repo): L1 source-lint → L2 compile → L3 AP-lint → L4
checklist (Trader-17) → L5 methodology → L6 quality-matrix → L7 broker-safety.

`personal` runs L1, L2, L3, L4, L7. `team` adds L5. `enterprise` runs all 7.

On this machine (no Wine + MetaEditor installed), L2 (compile) is the first
to fail-fast — that is the *correct* behaviour: compile is part of the contract,
and the gate refuses to silently skip it. To clear L2, run:

```bash
./scripts/setup-wine-metaeditor.sh   # Linux only, ~3 min
```

Even with a green L2, a bare scaffold is expected to fail later at L4 (Trader-17)
because no real strategy is wired yet. That's the gate **doing its job**, not a
defect.

---

## 4. `mql5-matrix` — 8×8 quality matrix CLI (standalone, no inputs)

```
{matrix_cli['raw']}
```

- **Passed cells:** {matrix_cli['pass']} / {matrix_cli['total']}
- **Threshold for TEAM:** {matrix_cli['threshold']}
- **Gate verdict:** {matrix_cli['gate']}

The 0/{matrix_cli['total']} number is the **CLI floor**, not a measurement.
`mql5-matrix` with no `--collect` argument has no evidence to look at, so
every cell defaults to N/A and therefore zero are PASS. To get a real
measurement, run the gates first with `--gate-report <file>`, then point
`python -m vibecodekit_mql5.rri.matrix --collect <dir>` at the artefact
directory.

### Honest cell-coverage audit (Wave 4.3)

Of the 64 matrix cells:

- **{matrix_audit['gate_auto']} cells** are *gate-auto* — discriminative,
  auto-fillable from `--gate-report` artefacts (e.g. lint, trader-check,
  backtest, walk-forward, multibroker, broker-safety).
- **{matrix_audit['rri_broadcast']} cells** are *RRI-broadcast* — filled from
  manual RRI persona reviews; one persona verdict broadcasts across multiple
  axes of the same dimension.
- **{matrix_audit['manual']} cells** are *manual-only* (`d_inference` × 8 axes)
  — the kit explicitly does not auto-fill them.

This means the legacy "56/64 threshold" used by the matrix gate is only
attainable when RRI broadcasts + manual reviews are filled in alongside the
gate-auto cells. The CLI gate alone cannot get there on its own — and that is
honest by design.

Run the audit yourself:

```bash
python -m vibecodekit_mql5.rri.matrix --audit
```

---

## What this report is and is not

- ✅ **Is:** a snapshot of what the gates currently report for a bare scaffold.
- ✅ **Is:** reproducible — re-run the script and these numbers don't move.
- ❌ **Is not:** a claim that the scaffold is profitable, safe to live-trade,
  or production-ready.
- ❌ **Is not:** a measurement of "8×8 = 64" achievement. The matrix is the
  CLI floor when no evidence is provided. Real measurements only come from
  feeding real backtest / walk-forward / multibroker reports through the gate.

Generated on {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')} (UTC).
"""

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(md, encoding="utf-8")
print(f"wrote {out_path}")
PY

echo "Done: $REPORT"
