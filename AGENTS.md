# Agent Operating Guide

This file is the entrypoint for AI coding agents (Devin, Claude Code,
Codex, Cursor) working inside `vibecodekit-mql5-ea`. It tells you what
to read first, what to use, and what NOT to introduce.

## Project Snapshot

- **What it is:** a methodology kit for building production-grade MQL5
  Expert Advisors on MetaTrader 5. Router-free, fail-fast, deterministic.
- **Status:** shipped product, `v1.2.0`. 60 CLI commands (50 standalone +
  10 Wave-3 aliases delegating to 2 umbrellas: `mql5-review --lens` and
  `mql5-rri <subcommand>`), 4 MCP servers, 23 scaffold archetypes, 26
  anti-pattern detectors (25 numbered AP-1…AP-25 + 1 build-aware
  method-hiding) pinned by a 20-EA golden dataset under
  `tests/fixtures/ea-bugs/`, lightweight MQL5 AST parser POC under
  `scripts/vibecodekit_mql5/ast_parser/` retrofitting AP-1/2/7 behind
  `mql5-lint --use-ast`, in-process Python tick-bar simulator
  `mql5-bt-sim` emitting MT5-compatible XML for hermetic backtests,
  7-layer permission gate, 1190 tests across Phase 0 / A / B / C / D / E.
- **License:** MIT.

## Source Of Truth (read in this order)

1. `README.md` — feature inventory + quickstart.
2. `docs/QUICKSTART.md` — 10-minute clone-to-compile.
3. `docs/COMMANDS.md` — every CLI command (60) grouped by lifecycle stage.
4. `docs/USAGE-en.md` / `docs/USAGE-vi.md` — full per-command reference.
5. `docs/USER-GUIDE-en.md` / `docs/USER-GUIDE-vi.md` — step-by-step walkthroughs.
6. `docs/anti-patterns-AVOID.md` — architectural anti-patterns the kit avoids; technical detectors (25 numbered AP-1…AP-25 + 1 build-aware method-hiding = 26 total) live in `scripts/vibecodekit_mql5/lint.py` + `lint_best_practice.py` + `method_hiding_check.py`.
7. `docs/PLAN-v5.md` — historical plan + design principles (v5 ADD/DROP list).
8. `docs/phase-{0,A,B,C,D,E}-spec.md` — phase-by-phase delivery contract.
9. `docs/references/50-survey.md … 80-input-syntax.md` — 29 cheatsheets.
10. `docs/rri-personas/` + `docs/rri-templates/` — RRI methodology.

## What you may change directly

- New CLI commands under `scripts/vibecodekit_mql5/` with a matching
  `[project.scripts]` entry in `pyproject.toml` and tests under
  `tests/gates/phase-{0,A,B,C,D,E}/`.
- New Include headers in `Include/*.mqh` (must compile under MetaEditor
  build ≥ 5260 — see `mql5-method-hiding-check`).
- New scaffold archetypes under `scaffolds/<preset>/<stack>/` with an
  `EAName.mq5` template. `mql5-doctor` auto-discovers every
  `<preset>/<stack>` pair on disk via `discover_scaffolds()` — no
  code edit to `REQUIRED_SCAFFOLDS` is needed. Add a matching scaffold
  test under `tests/gates/phase-D/test_scaffold_*` and a
  `FLOW-vi.md` narrative for `mql5-ea-docs`.
- New anti-pattern detectors in `scripts/vibecodekit_mql5/lint.py` or
  `scripts/vibecodekit_mql5/lint_best_practice.py` with regression tests.
- Documentation under `docs/`.
- Docs templates under `docs/templates/` for the LLM-driven `.docx`
  ship pipeline (`mql5-docs-bundle` + `mql5-docs-assemble`) — these
  must stay **kit-light**: do not hardcode per-archetype chapter
  content. Variation is the LLM agent's job; the kit only emits the
  deterministic context payload.

## What you must NOT introduce

These are deliberately rejected. Adding any of them re-creates the
failure modes the kit was forked from `vibecodekit-handwritten` to fix:

- A master `/mql5` router, `query_loop.py`, `intent_router.py`, or
  `pipeline_router.py`. Every command is a flat `python -m
  vibecodekit_mql5.<name>` that stands alone.
- `OrderSend` without `CPipNormalizer`-aware pip math (broker JPY/XAU
  asymmetry breaks; see `Include/CPipNormalizer.mqh`).
- `OrderSendAsync` without `OnTradeTransaction` (AP-18 catches it).
- `WebRequest` inside `OnTick` / `OnTimer` (AP-17).
- Hardcoded magic numbers — use `CMagicRegistry.Reserve()` (Plan v5 §6
  reserves `70000–79999`).
- LLM hallucination of test results. Every "passes" claim must be
  traceable to a real Strategy Tester XML report.
- Skipping the 7-layer permission gate in TEAM / ENTERPRISE mode.
- Hardcoded per-EA chapter content inside `docs_bundle` /
  `docs_assemble`. The LLM-driven `.docx` pipeline is intentionally
  archetype-agnostic — chapter structure is decided adaptively by the
  external LLM agent based on `docs-context.json`. Per-archetype
  `STRATEGY.yaml` files, hardcoded 10-chapter templates, and embedded
  matplotlib chart generators are **out of scope** for this kit.
- An LLM API client inside the kit. `mql5-docs-bundle` emits a prompt
  and the operator's external agent (Devin / Claude / Cursor) does the
  authoring step. The kit never calls a model directly.

## Agent Contracts (Wave 1)

Twelve gates ship a stable `--json` envelope (`schema_version=1`) on
stdout — schema and helpers live in `scripts/vibecodekit_mql5/_agent_io.py`.
The same gates support `--gate-report <path>` to also persist the
envelope to disk; `mql5-rri-matrix --collect <dir>` then auto-fills the
8×8 quality matrix from those artefacts. `mql5-lint` and
`mql5-method-hiding-check` additionally accept `--format sarif` (SARIF
2.1.0). For machine-readable discovery of the full CLI surface, run
`mql5-manifest --emit > manifest.json`. The repo's checked-in
`manifest.json` is regenerated from `pyproject.toml` and pinned by
`tests/gates/phase-A/test_manifest_generation.py`.

For hermetic Phase-B testing on Linux without Wine, use
`mql5-fixture --type {backtest,walkforward,monte-carlo,multibroker}
--strategy {random,trend,mean-rev} --seed N --out <dir>` to generate
synthetic MT5 Strategy Tester XML / CSV / journal artefacts that the
backtest / walkforward / monte-carlo / multibroker parsers accept
unchanged. Tests for this loop live under
`tests/gates/phase-B/test_fixture_generator.py`.

## Agent Contracts (Wave 3)

Wave 3 consolidated the review/RRI CLI surface and added a hermetic
forge iteration loop:

* **Review umbrella** —
  `mql5-review --lens {eng,ceo,cso,investigate}` is the new canonical
  entry-point. `mql5-eng-review`, `mql5-ceo-review`, `mql5-cso`, and
  `mql5-investigate` keep working as thin aliases. Legacy
  `--persona/--step` single-persona dispatch is preserved.
* **RRI umbrella** — `mql5-rri {template,bt,rr,chart}` is the new
  canonical entry-point. `mql5-rri-bt`, `mql5-rri-rr`, `mql5-rri-chart`
  keep working as thin aliases. `mql5-rri` with no subcommand still
  prints the Step-2 template (legacy default).
* **EA-bug golden dataset** — `tests/fixtures/ea-bugs/ap_NN_*/EA.mq5`
  + `expected.json` pins the lint detector contract. The driver lives
  at `tests/gates/phase-A/test_ea_bugs_golden_dataset.py`.
* **`mql5-forge-loop`** — Wave-3 hermetic CI loop. Chains the Wave-2
  fixture generator into the Wave-1 backtest parser for N deterministic
  iterations. Emits a per-iter `forge-loop-report.json` + Wave-1
  envelope. No Wine, no MetaTester.

## Agent Contracts (Wave 2)

- `mql5-init` is a 5-question interactive bootstrap wizard that emits
  `ea-spec.yaml` (the same artefact `mql5-auto-build --spec` consumes).
  It exposes `--non-interactive`, `--from-answers <yaml>`,
  `--list-presets`, and the standard `--json` envelope. Use it as the
  one-shot newcomer entry-point; the `README.md` 30-second quickstart
  pipes its output into `mql5-auto-build --draft`.
- `--draft` is a kit-wide flag on `mql5-lint`, `mql5-trader-check`,
  `mql5-permission`, and `mql5-auto-build`. It downgrades every
  finding to a non-blocking warning and exits 0, but the JSON envelope
  still records `data.original_ok` so the chat-driven build loop can
  inspect what would have failed. Distinct from `mql5-doctor --soft`
  (which only relaxes *environment* probes). The two flags compose.

## Task Loop

For every coding task:

1. Read the relevant doc(s) from the source-of-truth list above.
2. Run `mql5-doctor` (or `mql5-doctor --soft` on docs-only environments
   without Wine) and confirm the kit imports cleanly.
3. Make the smallest change that satisfies the request. Match the
   surrounding code style.
4. Add or update tests in the matching `tests/gates/phase-*` folder.
5. Run lint + tests locally before pushing:
   ```bash
   ruff check scripts mcp
   python -m pytest tests/gates -q
   ```
6. When changing CLI behavior, update `docs/COMMANDS.md` and the
   matching USAGE section.
7. PR description must mention which anti-pattern detector(s) cover the
   change, if any.

## Build / Verify Pipeline (cheat sheet)

```bash
# Free text → ea-spec.yaml → scaffold + lint + compile + dashboard + docs
mql5-spec-from-prompt "build EA trend EURUSD H1 risk 0.5%" --out ea-spec.yaml
mql5-auto-build --spec ea-spec.yaml --out-dir build/FirstEA

# Verify-only (skip compile / gate on Linux without Wine):
mql5-auto-build --spec ea-spec.yaml --out-dir build/FirstEA --no-compile --no-gate

# Lint + Trader-17 + 7-layer permission gate:
mql5-lint FirstEA.mq5
mql5-trader-check FirstEA.mq5
mql5-permission --mode personal FirstEA.mq5
```

## Environment

- Python ≥ 3.10, `pip install -e .` (now pulls `pyyaml` by default; install
  `.[dev]` for `pytest` + `ruff`).
- Wine 8.0.2 + MetaEditor: `./scripts/setup-wine-metaeditor.sh` on Linux.
  Not required for lint / docs / unit tests.
- `MetaTrader5` Python package: Windows / Wine only. The `mt5-bridge`
  MCP server falls back to deterministic stubs on Linux without it.

---

## Tiếng Việt — tóm tắt cho agent

- `vibecodekit-mql5-ea` là kit xây EA MQL5 production-grade, `v1.2.0`,
  60 lệnh CLI (50 standalone + 10 alias Wave-3 quy về 2 umbrella:
  `mql5-review --lens` và `mql5-rri <subcommand>`), 4 MCP server, 23
  scaffold, 26 AP detector (25 đánh số AP-1…AP-25 + 1 method-hiding theo
  build) găm bởi 20-EA golden dataset, AST parser POC (`ast_parser/`,
  bật bằng `mql5-lint --use-ast`) + Python tick-bar simulator
  (`mql5-bt-sim`), 1190 test gate.
- Bắt đầu từ `README.md` → `docs/QUICKSTART.md` → `docs/COMMANDS.md`.
  Tham khảo song ngữ ở `docs/USAGE-vi.md` + `docs/USER-GUIDE-vi.md`.
- Mọi lệnh đứng độc lập (`python -m vibecodekit_mql5.<name>`). **Không**
  thêm master router, `query_loop`, `intent_router`, `pipeline_router`.
- Mọi EA bắt buộc dùng `CPipNormalizer` (broker math) + `CMagicRegistry`
  (magic 70000-79999) + stop-loss mỗi lệnh + 7-layer permission gate.
- Trước khi commit: `ruff check scripts mcp` + `pytest tests/gates -q`.
  Trên môi trường không có Wine, dùng `mql5-doctor --soft`.
