# Arm F: software-dispatched Luna worker, Fable 5.1 acceptance only — 11 September 2026

**Taking the wait out of the orchestrator worked: $1.18 for an accepted result, 15% below arm E ($1.38), 24% below the Opus 5 worker (D, $1.55) and 38% below solo Fable (A, $1.90), all 244 frozen checks and all four post-hoc probes passing.** The cache-miss cost that inflated E is gone. The saving is smaller than the ~$0.55 predicted because the Fable acceptance session did far more of its own testing than expected, and because a Fable session costs about $0.40 before it does anything. One run.

| Arm | Configuration | Total | Orchestrator / acceptance | Worker | Visible | Held-out | Probes | Time |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| A | Fable 5.1 `medium` solo | $1.896 | $1.895 | — | 146/146 | 98/98 | 4/4 | 203 s |
| D | Fable + Opus 5 `low` builder | $1.549 | $0.784 | $0.763 | 146/146 | 98/98 | 4/4 | 225 s |
| E | Fable + Luna `max` via Codex plugin | $1.379 | $1.270 (+$0.053 Sonnet) | $0.056 | 146/146 | 98/98 | 4/4 | 651 s |
| F | script runs Luna `max`, then one Fable 5.1 `medium` acceptance session | **$1.177** | $1.068 | $0.109 | 146/146 | 98/98 | 4/4 | 1,091 s |
| G | same script, Opus 5 `high` acceptance; one correction round | $1.244 | $1.165 | $0.080 | 146/146 | 98/98 | 4/4 | 996 s |

Same qualified version-two fixture, grader, protected-hash check and post-hoc probes (JSONL whitespace-only line with CR, CR as JSON whitespace inside a line, CR-separated objects must fail, 150,000-character CSV memo). Protected files unchanged; no unexpected files. Claude costs are list-price equivalents from the CLI receipt, Luna's from its Codex rollout at the Codex team's rates. Not subscription bills.

## What F does

`software.py run` replaces the orchestrator's waiting with a script. It runs `codex exec` (Luna `max`, workspace-write sandbox, approvals never, no plugins, memories, agents, MCP servers or web) against the checkout with a handoff schema, then runs the contract checker, the worker's tests and the protected-file hashes itself, and only then starts one Fable 5.1 session with the handoff and the check results, asking for a structured decision: accept, correct, or reject. A `correct` decision would resume the same Fable session after one fresh Luna round with its findings; this run did not need it. No model waits for another model; there is no plugin, no forwarder, and no Agent tool.

Luna: `gpt-5.6-luna` at effort `max` confirmed in the rollout, 28 responses over 997 s, 1.52 M input tokens (90% cached), 41 k output (26 k reasoning), $0.109. It wrote `_shared.py`, the six adapters and eight tests, reported 146/146 and 8/8, and flagged two judgment calls (bare CR kept as memo data; raw quotes in unquoted CSV fields and XML comments, processing instructions and namespaces rejected). No unresolved risks.

Fable acceptance: 4 requests, 8 turns, 93 s, $1.061 (plus $0.007 Haiku). It read `SKILL.md`, `TASK.md`, the helpers and all eight delivered files, re-ran the checker and tests, then wrote and ran an edge-case script of about fifty probes of its own across the six formats (6 k output tokens in one turn), checked the two flagged judgment calls against the contract text, and accepted. It noted the process-global `csv.field_size_limit` change and that the worker restores it in a `finally` block.

## Where the money went

| Agent | Uncached in | Cache write (5 m) | Cache read | Output (thinking) | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fable 5.1 acceptance | 98 | 51,637 | 117,551 | 7,705 (3,501) | $1.061 |
| Haiku helper | 7,297 | 0 | 0 | 12 | $0.007 |
| Luna `max` (Codex) | 158,376 | 0 | 1,365,504 | 41,363 (25,820) | $0.109 |

Two things explain the gap between the ~$0.55 prediction and $1.07 for acceptance. First, the fixed cost of a Fable session: the first request wrote 32 k tokens to cache (the CLI's system prompt and tool definitions plus the acceptance prompt), about $0.40 before any file was read. Second, Fable chose to test rather than only read: its probe script was 6 k output tokens, about $0.30, and the file reads added 19 k of cache writes. That is the skill's "a clean report is weak evidence" rule being followed, and it is the part of the cost that buys confidence. Compared with E, Fable's cache writes fell from 83.5 k to 51.6 k while its output doubled: the wait-induced rewrite is gone and the money moved into review.

Luna cost twice E's Luna ($0.109 against $0.056): 28 responses against 11, because `codex exec` with a handoff contract had it run the checker and tests and write the handoff itself, where the plugin path had Fable do those. Still 9% of the total.

## What this means for the next lever

The worker is now nearly free; the remaining cost is almost all the acceptance session, and about 40% of that is the fixed cost of starting a Fable session under the CLI. Three ways down, in order of how much evidence supports them:

1. Keep Fable on acceptance and trim its starting context (a leaner tool set, a shorter prompt). Safe; small.
2. Let Fable's own probe script be the expensive part and stop it re-reading files the checker already covers. Risky: the reads are where a coordinator catches what a checker cannot.
3. Move acceptance to a cheaper model. The verifier diagnostic showed Opus 5 `low`, Fable `high` and Opus 4.8 `max` all missing a planted prose defect, so this needs a held-out task with planted code defects before it can be trusted, not another clean pass on this fixture.

## Follow-up the same day: trimming the acceptance session's fixed context

The system prompt text is small (about 12,000 characters, 3 k tokens). The fixed cost is the tool definitions. A Haiku probe of a one-word session showed 24.1 k fixed tokens with the flags as run and 15.0 k with `--tools Read,Glob,Grep,Bash,PowerShell`: `--disallowedTools` only denies a call, and the denied tools' definitions (Write, Edit, Agent, web, plan mode, todo list, and so on) were still sent with every request. `--tools` removes them; structured output still works under it. Excluding the dynamic system-prompt sections saved 100 tokens, not worth it.

This is not tailoring to the task. The five tools are what an acceptance session may do on any task, read, search and run, and the skill already forbids it to edit. The session was paying for definitions of tools the runner had already forbidden it to call.

Rerun of the acceptance session alone on the same saved F submission, same prompt, only the tool list changed (`software.py reaccept`):

| | As run | Trimmed |
| --- | ---: | ---: |
| First request (cache write) | 32,167 | 20,183 |
| Cache writes, total | 51,637 | 42,193 |
| Cache reads, total | 117,551 | 81,985 |
| Output (thinking) | 7,705 (3,501) | 8,512 (3,716) |
| Fable cost | $1.061 | $0.974 |
| Session cost with Haiku | $1.068 | $0.982 |
| Decision | accept | accept |

Both sessions accepted, re-ran the checks and hashes, read every delivered file, wrote a probe script (about 50 cases, then about 70) and flagged the process-global `csv.field_size_limit`; the second also noted that a line of non-ASCII Unicode whitespace is skipped rather than rejected, and called it defensible. The fixed saving is 12 k tokens on the first request and the same 12 k on every cache read after it, about $0.16; the extra 800 output tokens of probing took back $0.04. With the trimmed acceptance the F workflow would have cost about $1.09, 42% below solo Fable. One run each, and the probe count shows the acceptance session's own choices move the cost by a few cents either way.

The change is in the shared harness (`run.py base_args(..., tools=)`) and applies to the acceptance session only; the A, D and E receipts were taken with the default tool list and are left as they were.

## Arm G, same day: Opus 5 `high` as the acceptance session, correction loop exercised

Fresh checkout, same fixture, same runner, reviewer changed to Opus 5 `high` (the skill's new Reviewer row) after it qualified on planted defects. **$1.24 to an accepted result, all 244 checks and four probes passing, and for the first time the correction loop ran: the reviewer sent back one finding, Luna fixed it for a cent, and the resumed reviewer accepted. The finding turned out to be a reading of the contract the reference does not share.**

| Round | Step | Model | Time | Cost |
| --- | --- | --- | ---: | ---: |
| 1 | Worker writes six adapters, `_shared.py`, 7 tests | Luna `max`, 19 responses | 635 s | $0.069 |
| 1 | Runner checks: 146/146, tests pass, hashes unchanged | — | — | — |
| 1 | Acceptance: `correct`, one finding | Opus 5 `high`, 7 turns, ~90 probes | 256 s | $1.002 |
| 2 | Worker applies the fix, adds 4 regression cases | Luna `max`, 6 responses | 87 s | $0.011 |
| 2 | Resumed acceptance: `accept` | Opus 5 `high`, 3 turns | 18 s | $0.163 |
| | Total | | 996 s | **$1.244** |

The finding was the same class Opus raised on the F submission: `statement_xml` tested "whitespace only" with `str.isspace()`, so NBSP, U+0085 or U+3000 outside a memo were silently dropped instead of rejected. It gave the reproduction, the fix (`strip(' \t\r\n')`) and the regression cases to add. Luna's second session changed one function and the tests; the resumed Opus session diffed the correction, re-ran the checks, probed the fix at every position, confirmed memo contents still pass through unchanged, and accepted. This submission raises `ValueError` on deeply nested JSON, so the RecursionError finding from the F review did not apply.

Checked afterwards against the Codex team's reference implementation (the fixture's definition of correct), the finding is not a defect: the reference also accepts NBSP outside a memo, and the contract never says which characters count as whitespace there. G therefore paid a $0.17 correction round, plus Luna's cent, for a behaviour stricter than the reference on a point the contract does not settle. Cost against F ($1.18): about the same money for the same accepted quality by the fixture's standard, with the correction machinery proven to work. The reviewer was not cheaper this time: Opus's first session cost $1.00, not the $0.32 to $0.57 seen on the F submission, because it wrote 22.9 k output tokens (9.8 k thinking, about 90 probes) against 4.4 k to 10 k before. Across four Opus 5 `high` acceptance sessions the cost has ranged $0.32 to $1.00 on the same task; the reviewer's own choice of how much to probe moves the bill more than the model price does. The resumed round was cheap ($0.16) because the context was already cached and the diff was small.

Planted-defect and clean-submission results for this reviewer are in [results-reviewers-2026-09-11.md](results-reviewers-2026-09-11.md).

## Limits

One run per arm; a fixture both worker vendors have solved several times; F's correction loop was not exercised (G's was, once); the worker took 17 minutes, which does not matter for cost but would for anyone waiting. The acceptance session is not an orchestrator: the script chose the worker and the checks, so F measures a fixed pipeline, not a coordinator's routing. Luna's own-thread usage may not be what a Codex subscription bills. The first F attempt aborted before any model spend on the worker (`codex exec` refused an untrusted directory; the runner then spent $0.46 on a Fable session that correctly rejected the empty handoff). That attempt is excluded from the table; including it, the F experiment cost $1.64, and the two figures are kept apart on purpose: $1.18 is what the workflow costs when it works, $1.64 is what this experiment cost. The runner now validates the whole handoff (schema, `complete` status, every claimed file present, at least one adapter listed) on every round, corrections included, and aborts with a receipt rather than spending on acceptance; there is still no automatic retry.

## Identities

- Skill SHA-256: `272a647921b7e67818a68c0bfadef7f49711ae346a52addb33154b84fb21ac12`
- Fable session `06cd74b3-4365-4580-87de-e81db1b6c2ca`; Codex thread `01a09072-dd3c-76f1-be2a-64846e3a428d`; Codex CLI 0.153.4 via `codex exec`
- Trimmed-context acceptance rerun: Fable session `6d60d569-a352-43e2-8e5a-4b0e52dc8f8a`
- Arm G: Codex threads `01a090ce-2ca1-7142-a6e5-d50c6e8bc2d4` and `01a090db-c64f-7ef0-9708-26c86070c0e3`; root `%LOCALAPPDATA%\Temp\claude-adapters-software-opus-506c7815`; skill SHA-256 `e45f2809298a41d17d400138bdb5e2e6a51f09335c1c1a443e7210763792a741`; receipts under `private/software/G/`
- Root `%LOCALAPPDATA%\Temp\claude-adapters-software-1e8874b5`; receipts, acceptance results, handoff, summary and the Codex rollout under `private/software/`
