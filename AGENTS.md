# Agent Operating Guide

This file is the entrypoint for AI coding agents (Devin, Claude Code,
Codex, Cursor) working inside `vibecodekit-mql5-ea`. It tells you what
to read first, what to use, and what NOT to introduce.

## Project Snapshot

- **What it is:** a methodology kit for building production-grade MQL5
  Expert Advisors on MetaTrader 5. Router-free, fail-fast, deterministic.
- **Status:** shipped product, `v1.0.1`. 53 CLI commands, 4 MCP servers,
  23 scaffold archetypes, 25 anti-pattern detectors, 7-layer permission
  gate, 915 tests across Phase 0 / A / B / C / D / E.
- **License:** MIT.

## Source Of Truth (read in this order)

1. `README.md` — feature inventory + quickstart.
2. `docs/QUICKSTART.md` — 10-minute clone-to-compile.
3. `docs/COMMANDS.md` — every CLI command (53) grouped by lifecycle stage.
4. `docs/USAGE-en.md` / `docs/USAGE-vi.md` — full per-command reference.
5. `docs/USER-GUIDE-en.md` / `docs/USER-GUIDE-vi.md` — step-by-step walkthroughs.
6. `docs/anti-patterns-AVOID.md` — architectural anti-patterns the kit avoids; technical detectors (25 AP-N) live in `scripts/vibecodekit_mql5/lint.py` + `lint_best_practice.py`.
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
- New scaffold archetypes under `scaffolds/<preset>/<stack>/` with a
  `doctor.REQUIRED_SCAFFOLDS` entry.
- New anti-pattern detectors in `scripts/vibecodekit_mql5/lint.py` or
  `scripts/vibecodekit_mql5/lint_best_practice.py` with regression tests.
- Documentation under `docs/`.

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

- `vibecodekit-mql5-ea` là kit xây EA MQL5 production-grade, `v1.0.1`,
  53 lệnh CLI, 4 MCP server, 23 scaffold, 25 AP detector, 915 test gate.
- Bắt đầu từ `README.md` → `docs/QUICKSTART.md` → `docs/COMMANDS.md`.
  Tham khảo song ngữ ở `docs/USAGE-vi.md` + `docs/USER-GUIDE-vi.md`.
- Mọi lệnh đứng độc lập (`python -m vibecodekit_mql5.<name>`). **Không**
  thêm master router, `query_loop`, `intent_router`, `pipeline_router`.
- Mọi EA bắt buộc dùng `CPipNormalizer` (broker math) + `CMagicRegistry`
  (magic 70000-79999) + stop-loss mỗi lệnh + 7-layer permission gate.
- Trước khi commit: `ruff check scripts mcp` + `pytest tests/gates -q`.
  Trên môi trường không có Wine, dùng `mql5-doctor --soft`.
