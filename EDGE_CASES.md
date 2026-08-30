# Planted Edge Cases (for demoing Repo Risk Agent)

This repo is a **synthetic fixture**, not a real product. Every problem in it was planted on
purpose to exercise a specific detection path in [Repo Risk Agent](https://github.com/galaxyte/repo-risk-agent).
All secrets below are fake/example values (the AWS key pair is literally AWS's own public
documentation example — `AKIAIOSFODNN7EXAMPLE`); the private key in `certs/dev.key` was
generated locally for this repo alone and has never been used for anything.

Use this file as the answer key when reviewing the agent's output — every finding it should be
able to produce is listed below with the exact mechanism that should catch it.

| # | Planted issue | Where | Should be caught by | Category |
|---|---|---|---|---|
| 1 | Hardcoded AWS access key + secret | `legacy_config.py`, commit `dd446ba` (file later deleted in `35d9147`) | `scan_secrets` — **git history** scan (not working tree; the file no longer exists on disk) | Secrets |
| 2 | Hardcoded DB password | `config.py` → `DB_PASSWORD` | `scan_secrets` — working tree regex match | Secrets |
| 3 | Hardcoded Stripe-shaped API key | `config.py` → `STRIPE_API_KEY` | `scan_secrets` — working tree regex match | Secrets |
| 4 | Hardcoded Flask `SECRET_KEY` | `config.py` → `SECRET_KEY` | `scan_secrets` — working tree regex match | Secrets |
| 5 | Committed private key file | `certs/dev.key` | `scan_secrets` — private-key-header pattern | Secrets |
| 6 | `debug=True` + bound to `0.0.0.0` | `app.py` → `app.run(...)` | LLM reasoning over `read_file`/`list_tree` output (no dedicated tool checks this — it's a judgment call, not a regex) | Code review / reasoning |
| 7 | Pinned, multi-years-old dependencies (Flask 2.0.1, requests 2.25.1, PyYAML 6.0.1) | `requirements.txt` | `dependency_audit` (`pip-audit`) | Dependencies |
| 8 | Python 2-only syntax (`print "..."`) | `legacy_report.py` | `run_linter_or_complexity` (`ruff` fails to parse this file specifically) | Code quality |
| 9 | God-file: ~54KB, 165 near-duplicate functions | `big_utils.py` | `list_tree` structural signal (`large_files_over_50kb`) | Structure |
| 10 | Deliberately high-cyclomatic-complexity function | `big_utils.py` → `calculate_discount()` | `run_linter_or_complexity` (`radon cc`) | Code quality |
| 11 | One test intentionally asserts the wrong value | `tests/test_invoices.py` → `test_calculate_total_wrong_expectation` | Actually running `pytest` via `run_command` — a partial pass rate (2/3), not a clean pass or fail | Tests |
| 12 | CI config targets Python 2.7/3.4, on a dead CI provider | `.travis.yml` | LLM reasoning after `list_tree`/`read_file` sees it (the `has_ci_config` structured signal only checks `.github/workflows`/`.gitlab-ci.yml`/`.circleci`, so this is a case the *agent's judgment* has to catch, not a mechanical signal — a good test of whether it's actually reading, not just checking boxes) | Structure / reasoning |
| 13 | No `LICENSE` file anywhere | repo root | `list_tree` structural signal (`has_license: false`) | Structure |
| 14 | README claims PDF export, email delivery, multi-currency, and Stripe payment links | `README.md` | LLM reasoning: cross-reference README claims against `app.py`'s actual routes (none of these exist in code) | Reasoning / README-vs-code mismatch |
| 15 | No dedicated `.gitignore`, `.env.example`, or secret-management pattern at all | repo root | Implicit in the density of findings above — nothing here suggests any secret hygiene was ever in place | Structure |

## What a good agent run should produce

- **`build_status`**: likely `passed` (the pinned versions install on a modern Python) — a *bad* agent might skip installing and jump to guessing.
- **`test_status`**: `failed` (2 of 3 tests pass) — the interesting case is whether the agent reports the real pass rate (`test_pass_rate ≈ 0.67`) or just a binary pass/fail.
- **`vulnerability_summary`**: whatever `pip-audit` actually finds against these pinned versions — not asserted from memory.
- **`red_flags`**: should include at minimum the git-history AWS key (#1), the working-tree secrets (#2-5), the Python 2 syntax file (#8), the god-file (#9), and ideally the debug-mode (#6) and README-mismatch (#14) reasoning catches.
- **`go_no_go`**: `no_go` or `go_with_conditions` at best — there is no version of this repo that should read as a clean `go`.

## What the baseline should get wrong (by design)

The zero-tool baseline never runs anything, so it structurally **cannot** find #1 (git history — it never even sees the git log), #7 (dependency audit — no tool to run one), #11 (real test pass rate — it can only guess), or confirm #9/#10 with real tool output. Comparing baseline vs. agent on this repo is the clearest possible demonstration of what verification actually buys you.
