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

## What actually happened (real run, `gpt-5`, `--variant full`)

| | Baseline | Agent |
|---|---|---|
| `build_status` | `unknown` (correctly abstains — never ran anything) | `passed` (really ran `pip install`) |
| `test_status` | `unknown` | `failed`, `test_pass_rate: 0.667` (really ran `pytest`: 2 passed, 1 failed) |
| `vulnerability_summary` | `null` | `{low: 29}` (really ran `pip-audit`) |
| `risk_score` / `go_no_go` | 72 / `go_with_conditions` | 75 / `go_with_conditions` |

The agent's final `red_flags` covered #2-6, #8-10, #12-14 from the table above directly — hardcoded
password/API key/`SECRET_KEY` (#2-4), the committed private key (#5, rated `critical`), `debug=True`
bound to `0.0.0.0` (#6), the real pip-audit result (#7), the Python 2 syntax file (#8), the god-file
(#9) and its exact highest-complexity function (#10, `calculate_discount`, complexity 18 — found via
`run_linter_or_complexity`, not guessed), the dead Travis config (#12, via reasoning — confirming the
`has_ci_config` structural signal alone would have missed this), the missing `LICENSE` (#13), and the
README-vs-code scope mismatch (#14).

**One honest miss on a first run, not reproduced on a second:** on the first real run, `scan_secrets`'s
`git_history_findings` *did* come back with the AKIA key from commit `dd446ba` (confirmed by reading
the raw tool result in `agent_trajectory.jsonl`) — but the agent's final report didn't surface it as
its own distinct red flag alongside the working-tree secrets. On a second independent run, it *did*
surface it, as "AWS access key ID pattern found in git history," correctly cited to the
`scan_secrets` tool call. Same repo, same prompt, different outcome — that's real, observed
non-determinism, not a fixed bug to "fix" and declare solved. Worth pointing out on camera rather
than papering over: a tool producing evidence is necessary but not sufficient for an agent to
reliably surface it every time, and a single successful run is not proof the gap is closed.

## What the baseline structurally cannot do

The zero-tool baseline never runs anything, so — as shown above — it correctly reports `unknown`/`null`
for build, test, and vulnerability status rather than guessing, and has no way to ever surface the
git-history secret (#1) since it never sees `git log` at all. Comparing baseline vs. agent on this one
repo is the clearest possible demonstration of what verification actually buys you: same model, same
repo, very different ability to answer the questions a freelancer actually needs answered.
