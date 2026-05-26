---
id: commands
title: Command catalog (59 commands — 49 standalone + 10 Wave-3 aliases)
applicable_phase: E
---

# Command catalog

All commands callable directly via `python -m vibecodekit_mql5.<name>`.
No master `/mql5` router — every command stands alone.

**Wave 3 (v1.1) consolidated 10 commands into 2 umbrellas**:

* The five review CLIs (`mql5-review`, `mql5-eng-review`, `mql5-ceo-review`,
  `mql5-cso`, `mql5-investigate`) now share `mql5-review`'s umbrella — pick
  a preset via `--lens {eng,ceo,cso,investigate}`. The four lens-named
  console scripts remain as 1-line aliases so existing operator habits
  keep working.
* The four RRI CLIs (`mql5-rri`, `mql5-rri-bt`, `mql5-rri-rr`,
  `mql5-rri-chart`) now share `mql5-rri`'s umbrella — pick a matrix
  flavour via subcommand `mql5-rri {template,bt,rr,chart}`. The three
  matrix-named console scripts remain as 1-line aliases.

The pyproject `[project.scripts]` entry list is unchanged (59 entries
post-Wave-3) — every alias still resolves to its existing console-script
name. Wave 3 only consolidated the *implementation*, not the surface.

## Agent contracts (Wave 1)

Twelve gates accept a standardised `--json` flag that emits a stable
envelope (`schema_version=1`) on stdout instead of pretty text — see
`scripts/vibecodekit_mql5/_agent_io.py`. The same gates also accept
`--gate-report <path>` to additionally write the envelope to disk; the
matrix collector picks them up:

```bash
mql5-lint EA.mq5 --json
mql5-lint EA.mq5 --format sarif                # SARIF 2.1.0
mql5-walkforward is.xml oos.xml --gate-report gate-report-wf.json
mql5-rri-matrix --collect ./reports/ --output matrix.html
```

Tools with `--json`: `mql5-lint`, `mql5-trader-check`, `mql5-broker-safety`,
`mql5-permission`, `mql5-backtest`, `mql5-walkforward`, `mql5-monte-carlo`,
`mql5-multibroker`, `mql5-overfit-check`, `mql5-mfe-mae`, `mql5-doctor`,
`mql5-audit`, `mql5-fixture`, `mql5-init`, `mql5-forge-loop`.

Tools with `--format sarif`: `mql5-lint`, `mql5-method-hiding-check`.

`mql5-manifest` is the discovery tool itself — it has its own
`--emit` / `--validate` surface and does NOT participate in the
`--json` envelope contract. `mql5-compile` carries a *legacy*
`--json` flag (emits `CompileResult` directly, not the Wave-1
envelope) and is therefore also kept out of the table above.

Run `mql5-manifest --emit > manifest.json` for a machine-readable
catalogue of every command (capability flags + module path).

## Draft mode (Wave 2)

Four gates accept the new `--draft` flag, which downgrades errors to
non-blocking warnings and forces exit 0 — useful inside the
chat-driven build loop where the EA is still half-written:

```bash
mql5-lint EA.mq5 --draft
mql5-trader-check EA.mq5 --draft
mql5-permission --mode personal EA.mq5 --draft
mql5-auto-build --spec ea-spec.yaml --draft       # implies --no-compile --no-gate --no-docs
```

The JSON envelope still records the original verdict under
`data.original_ok` so downstream tooling can see what would have
blocked in non-draft mode. Draft is distinct from `--soft` (used by
`mql5-doctor` to relax *environment* probes); both flags can coexist.

## Discovery (5)
- `/mql5-scan`     — survey project tree, classify artefacts
- `/mql5-survey`   — match free-text strategy → scaffold archetype
- `/mql5-doctor`   — installation + environment health check (use `--soft` for docs/lint-only CI without Wine: Wine/MetaEditor/terminal probes become warnings, exit 0)
- `/mql5-audit`    — run 70-test conformance battery
- `/mql5-init`     — interactive 5-question bootstrap wizard → `ea-spec.yaml` (Wave 2). Use `--non-interactive` / `--from-answers <yaml>` in CI.

## Plan (4)
- `/mql5-rri`       — open Step 2 RRI template
- `/mql5-vision`    — open Step 3 VISION template
- `/mql5-blueprint` — open Step 4 BLUEPRINT template
- `/mql5-tip`       — open Step 5 TIP template

## Build (15)
- `/mql5-build`             — render a scaffold
- `/mql5-auto-build`        — single-shot spec → scan → build → lint → compile → gate → dashboard → docs
- `/mql5-auto-fix`          — close 8 critical anti-patterns automatically
- `/mql5-spec-from-prompt`  — free-text description → `ea-spec.yaml` (chat-driven build)
- `/mql5-dashboard`         — render + publish the quality-matrix HTML
- `/mql5-ea-docs`           — render end-user EA documentation (`.docs.html` + `.docs.md` + optional `.docs.pdf`) with per-input semantic deep-dive cards + per-archetype FLOW narrative (OnInit / OnTick / OnDeinit). Vietnamese by default; `--lang en` for English.
- `/mql5-docs-bundle`       — emit `docs-context.json` + `docs-prompt.md` so an external LLM agent can author the EA user-guide markdown (Pattern A — kit-light `.docx` ship). Bundles spec + parsed inputs (semantic-library enriched) + scaffold FLOW + build/lint metrics. Auto-runs inside `mql5-auto-build`.
- `/mql5-docs-assemble`     — convert the LLM-authored `guide.md` → Word `<EA>.docs.docx` (embedded images from `images/`, F9-refreshable ToC, Vietnamese diacritics). Auto-runs inside `mql5-auto-build` when `guide.md` is present in the build dir.
- `/mql5-wizard`            — render the wizard-composable scaffold
- `/mql5-pip-normalize`     — patch a .mq5 to use `CPipNormalizer`
- `/mql5-async-build`       — render the hft-async scaffold
- `/mql5-onnx-export`       — PyTorch/TF → ONNX (opset ≥ 14)
- `/mql5-onnx-embed`        — embed an `.onnx` into an `.mq5` via `#resource`
- `/mql5-llm-context`       — wire an LLM bridge into an existing EA
- `/mql5-forge-init`        — initialise an Algo Forge repo

## Verify (12)
- `/mql5-compile`             — MetaEditor build (Wine on Linux)
- `/mql5-lint`                — 8 critical anti-pattern detectors
- `/mql5-method-hiding-check` — build-aware method-hiding detector (ERROR on build ≥ 5260, WARN below)
- `/mql5-backtest`            — parse Strategy Tester XML → 14 metrics JSON (you run the tester)
- `/mql5-tester-run`          — drive `terminal64.exe` (Wine or native) with a rendered `tester.ini` and parse the XML end-to-end
- `/mql5-optimize-run`        — drive `terminal64.exe` in optimization mode (slow/genetic), parse the SpreadsheetML report into top-N parameter sets (`--from-xml` for hermetic CI)
- `/mql5-walkforward`         — IS/OOS Sharpe correlation (takes 2 positional XML reports)
- `/mql5-monte-carlo`         — bootstrap DD from returns CSV (positional `returns_csv --reported-dd ...`)
- `/mql5-overfit-check`       — OOS/IS Sharpe sanity (takes 2 positional XML reports)
- `/mql5-multibroker`         — N-broker stability orchestrator (`--reports a.xml,b.xml,c.xml`)
- `/mql5-fitness`             — OnTester custom fitness template (positional name; omit to list)
- `/mql5-mfe-mae`             — per-trade MFE/MAE CSV analyser (8-col schema; see USAGE)

## RRI methodology (4 — 1 umbrella + 3 Wave-3 aliases)
- `/mql5-rri` — umbrella CLI. Subcommands (alias to the entry points below):
  - `/mql5-rri` *(no subcommand)* / `/mql5-rri template` — print the Step-2 RRI markdown template (legacy default).
  - `/mql5-rri bt --metrics bt.json [--mode personal] [--output rri-bt.html]` — Backtest review (5 personas × 7 dim × 8 axis).
  - `/mql5-rri rr --trader-check tc.json --walkforward wf.json --monte-carlo mc.json --overfit of.json [--output rri-rr.html]` — Risk & Robustness review.
  - `/mql5-rri chart --metrics chart.json [--output rri-chart.html]` — Optional indicator-dev RRI.
- `/mql5-rri-bt`, `/mql5-rri-rr`, `/mql5-rri-chart` — kept as **Wave-3 aliases** for back-compat; each is a 1-line forward to the umbrella subcommand above. Use the umbrella for new code.

## Review (6 — 1 umbrella + 4 Wave-3 aliases + 1 standalone)
- `/mql5-review` — umbrella CLI. Either `--lens <eng|ceo|cso|investigate>` (multi-persona preset) **or** the legacy `--persona <id> --step <id>` single-persona path:
  - `mql5-review --lens eng    [--mode personal] [--output eng-review.md]` → broker-engineer + devops, steps BUILD + VERIFY.
  - `mql5-review --lens ceo    [--mode personal] [--output ceo-review.md]` → trader + strategy-architect, steps VISION + REFINE.
  - `mql5-review --lens cso    [--mode personal] [--output cso-review.md]` → risk-auditor, steps RRI + VERIFY.
  - `mql5-review --lens investigate [--mode personal] [--output investigate.md]` → perf-analyst + strategy-architect + Hypotheses worksheet.
  - `mql5-review --persona trader --step verify --mode personal --output review.md` → legacy single-persona dispatch (unchanged).
- `/mql5-eng-review`, `/mql5-ceo-review`, `/mql5-cso`, `/mql5-investigate` — kept as **Wave-3 aliases** for back-compat; each forwards to the matching `--lens` on the umbrella. Use the umbrella for new code.
- `/mql5-second-opinion` — standalone lint + Trader-17 fast pass on a `.mq5`; NOT a lens (not consolidated).

## Deploy (3)
- `/mql5-deploy-vps`     — emit a MIGRATE-VPS.md checklist
- `/mql5-cloud-optimize` — emit a tester.ini for Cloud Network
- `/mql5-canary`         — 30-min post-deploy live monitor

## Ship (4)
- `/mql5-forge-pr` — push a PR to Algo Forge
- `/mql5-package`  — produce `manifest.json` (SHA-256 inventory) + `<name>-ship.zip` from an `mql5-auto-build` output dir; same step runs inline when `mql5-auto-build --package` is set
- `/mql5-ship`     — `git tag` + push
- `/mql5-refine`   — classify a diff as tweak/patch/rework

## Other (4)
- `/mql5-broker-safety`   — verify pip-norm + multi-broker
- `/mql5-trader-check`    — Trader-17 checklist (positional `.mq5` path; outputs JSON verdict 6+/17 PASS threshold)
- `/mql5-permission`      — 7-layer permission gate orchestrator (positional `.mq5` source; `--mode {personal,team,enterprise}` selects gate set: PERSONAL=1/2/3/4/7, TEAM=1-5/7, ENTERPRISE=1-7)
- `/mql5-install`         — reconcile-install kit overlay

## Agent contracts (3)
- `/mql5-manifest`     — emit (or validate) a machine-readable catalogue of every CLI: `--emit [--output manifest.json]`, `--validate manifest.json`
- `/mql5-fixture`      — generate hermetic MT5 Strategy Tester fixtures so the BT/WF/MC/MB pipeline runs on Linux without Wine: `--type {backtest,walkforward,monte-carlo,multibroker} --strategy {random,trend,mean-rev} --seed N --out <dir>`
- `/mql5-forge-loop`   — **Wave 3**: closed forge iteration loop. Chains `mql5-fixture --type backtest` into `mql5-backtest` parsing for `N` deterministic iterations (`--iterations 3 --strategy trend --base-seed 100 [--pf-floor F] [--sharpe-floor F] [--max-dd-ceiling F]`). No Wine, no MetaTester. Emits a per-iter `forge-loop-report.json` + Wave-1 `--json` envelope so the matrix collector consumes it unchanged.
