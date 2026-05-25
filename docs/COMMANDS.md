---
id: commands
title: Command catalog (57 commands)
applicable_phase: E
---

# Command catalog

All commands callable directly via `python -m vibecodekit_mql5.<name>`.
No master `/mql5` router — every command stands alone.

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
`mql5-audit`, plus the two new commands below.

Tools with `--format sarif`: `mql5-lint`, `mql5-method-hiding-check`.

Run `mql5-manifest --emit > manifest.json` for a machine-readable
catalogue of every command (capability flags + module path).

## Discovery (4)
- `/mql5-scan`     — survey project tree, classify artefacts
- `/mql5-survey`   — match free-text strategy → scaffold archetype
- `/mql5-doctor`   — installation + environment health check (use `--soft` for docs/lint-only CI without Wine: Wine/MetaEditor/terminal probes become warnings, exit 0)
- `/mql5-audit`    — run 70-test conformance battery

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

## RRI methodology (3)
- `/mql5-rri-bt`     — Backtest review (5 personas × 7 dim × 8 axis)
- `/mql5-rri-rr`     — Risk & Robustness review
- `/mql5-rri-chart`  — Optional indicator-dev RRI

## Review (5)
- `/mql5-review`        — generic review opener
- `/mql5-eng-review`    — engineering review opener
- `/mql5-ceo-review`    — leadership review opener
- `/mql5-cso`           — strategy review opener
- `/mql5-investigate`   — incident investigation opener

## Deploy (3)
- `/mql5-deploy-vps`     — emit a MIGRATE-VPS.md checklist
- `/mql5-cloud-optimize` — emit a tester.ini for Cloud Network
- `/mql5-canary`         — 30-min post-deploy live monitor

## Ship (4)
- `/mql5-forge-pr` — push a PR to Algo Forge
- `/mql5-package`  — produce `manifest.json` (SHA-256 inventory) + `<name>-ship.zip` from an `mql5-auto-build` output dir; same step runs inline when `mql5-auto-build --package` is set
- `/mql5-ship`     — `git tag` + push
- `/mql5-refine`   — classify a diff as tweak/patch/rework

## Other (5)
- `/mql5-broker-safety`   — verify pip-norm + multi-broker
- `/mql5-trader-check`    — Trader-17 checklist (positional `.mq5` path; outputs JSON verdict 6+/17 PASS threshold)
- `/mql5-permission`      — 7-layer permission gate orchestrator (positional `.mq5` source; `--mode {personal,team,enterprise}` selects gate set: PERSONAL=1/2/3/4/7, TEAM=1-5/7, ENTERPRISE=1-7)
- `/mql5-install`         — reconcile-install kit overlay
- `/mql5-second-opinion`  — one-shot lint + Trader-17 (optional)

## Agent contracts (2)
- `/mql5-manifest`  — emit (or validate) a machine-readable catalogue of every CLI: `--emit [--output manifest.json]`, `--validate manifest.json`
- `/mql5-fixture`   — generate hermetic MT5 Strategy Tester fixtures so the BT/WF/MC/MB pipeline runs on Linux without Wine: `--type {backtest,walkforward,monte-carlo,multibroker} --strategy {random,trend,mean-rev} --seed N --out <dir>`
