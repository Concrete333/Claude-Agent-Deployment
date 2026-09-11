# Arm F: software-dispatched Luna worker, Fable 5.1 acceptance only — 11 September 2026

**Taking the wait out of the orchestrator worked: $1.18 for an accepted result, 15% below arm E ($1.38), 24% below the Opus 5 worker (D, $1.55) and 38% below solo Fable (A, $1.90), all 244 frozen checks and all four post-hoc probes passing.** The cache-miss cost that inflated E is gone. The saving is smaller than the ~$0.55 predicted because the Fable acceptance session did far more of its own testing than expected, and because a Fable session costs about $0.40 before it does anything. One run.

| Arm | Configuration | Total | Orchestrator / acceptance | Worker | Visible | Held-out | Probes | Time |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| A | Fable 5.1 `medium` solo | $1.896 | $1.895 | — | 146/146 | 98/98 | 4/4 | 203 s |
| D | Fable + Opus 5 `low` builder | $1.549 | $0.784 | $0.763 | 146/146 | 98/98 | 4/4 | 225 s |
| E | Fable + Luna `max` via Codex plugin | $1.379 | $1.270 (+$0.053 Sonnet) | $0.056 | 146/146 | 98/98 | 4/4 | 651 s |
| F | script runs Luna `max`, then one Fable 5.1 `medium` acceptance session | **$1.177** | $1.068 | $0.109 | 146/146 | 98/98 | 4/4 | 1,091 s |

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

## Limits

One run; a fixture both worker vendors have solved several times; the correction loop was not exercised; the worker took 17 minutes, which does not matter for cost but would for anyone waiting. The acceptance session is not an orchestrator: the script chose the worker and the checks, so F measures a fixed pipeline, not a coordinator's routing. Luna's own-thread usage may not be what a Codex subscription bills. The first F attempt aborted before any model spend on the worker (`codex exec` refused an untrusted directory; the runner then spent $0.46 on a Fable session that correctly rejected the empty handoff); that attempt is excluded from the table and the runner now aborts before acceptance when the worker fails.

## Identities

- Skill SHA-256: `272a647921b7e67818a68c0bfadef7f49711ae346a52addb33154b84fb21ac12`
- Fable session `06cd74b3-4365-4580-87de-e81db1b6c2ca`; Codex thread `01a09072-dd3c-76f1-be2a-64846e3a428d`; Codex CLI 0.153.4 via `codex exec`
- Root `%LOCALAPPDATA%\Temp\claude-adapters-software-1e8874b5`; receipts, acceptance result, handoff, summary and the Codex rollout under `private/software/`
