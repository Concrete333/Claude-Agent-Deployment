# Arm E: Fable 5.1 orchestrator with a Luna Max worker through the Codex plugin — 11 September 2026

**Cross-vendor delegation was the cheapest accepted result so far on this task: $1.38 against $1.55 for the Opus 5 worker and $1.90 solo, all 244 checks passing, with the orchestrator reviewing the code.** Luna's share was 4% of the cost. Most of the remaining cost was Fable, and a third of Fable's cost was a prompt-cache miss caused by waiting ten minutes for Luna. One run.

| Arm | Configuration | Total | Orchestrator | Worker | Visible | Held-out | Added tests | Probes | Time |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| A | Fable 5.1 `medium` solo | $1.896 | $1.895 | — | 146/146 | 98/98 | 17 | 4/4 | 203 s |
| D | Fable + Opus 5 `low` builder | $1.549 | $0.784 | $0.763 | 146/146 | 98/98 | 39 | 4/4 | 225 s |
| E | Fable + Luna `max` via Codex plugin | **$1.379** | $1.270 (+$0.053 Sonnet forwarder) | $0.056 | 146/146 | 98/98 | 7 | 4/4 | 651 s |

E is 11.0% below D and 27.3% below A. Claude costs are provider list-price equivalents from the CLI receipt; Luna's is own-thread usage from the isolated Codex rollout priced at the Codex team's rates ($0.20 uncached, $0.02 cached, $1.20 output per million; no cache writes reported). Same qualified version-two fixture, grader and post-hoc probes as the A/D trial. Protected files unchanged; no unexpected files.

## How the run went

The orchestrator read `SKILL.md` and `TASK.md`, listed the tree and read the example adapter and helpers, then dispatched once through `codex:codex-rescue`, a Sonnet forwarder that made a single `node codex-companion.mjs task --wait --write --model gpt-5.6-luna` call. The Codex rollout confirms `gpt-5.6-luna` at effort `max`, workspace-write sandbox, approvals never: 11 responses, 414k input tokens (86% cached), 31k output (19k reasoning). Luna wrote `_shared.py`, the six adapters and seven tests in one pass; no correction was requested.

After the return Fable ran the checker and the tests, re-hashed every protected file, read all seven delivered files in one Bash call, and accepted. It reported no unresolved risks; unlike the D orchestrator it did not mention the process-global CSV field limit (this submission also raises and restores it).

## Where the money went

| Agent | Uncached in | Cache write (5 m) | Cache read | Output (thinking) | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fable 5.1 orchestrator | 162 | 83,532 | 142,727 | 3,770 (1,026) | $1.270 |
| Sonnet forwarder | 4 | 14,563 | 5,898 | 1,516 | $0.053 |
| Luna `max` (Codex) | 57,801 | 0 | 356,608 | 31,345 (18,678) | $0.056 |

Fable's cache writes are nearly double D's (83.5k against 44.6k) for less work. The transcript shows why: the request after the ten-minute Agent call has `cache_read 0, cache_creation 39,434`. The five-minute cache had expired while Luna worked, so the whole context was written again, at 1.25× input price, about $0.49. A three-minute Opus worker never triggered this. Had the cache survived, E would have been roughly $0.90, about 42% below D. Under a one-hour cache the writes cost 60% more (2× base input against 1.25×) but survive the wait; whether that nets out depends on how many turns follow the wait. This is a real structural cost of pairing a fast orchestrator with a slow cheap worker under short caching, and it is not in any benchmark price table.

## Runtime findings

- The plugin drives `codex app-server`, not `codex exec`. Its `--effort` validator refuses `max`; leaving `--effort` unset and putting `model_reasoning_effort = "max"` in the Codex config gives Luna Max, confirmed in the rollout's turn context.
- An isolated `CODEX_HOME` (own config, copied auth, no memories, plugins, agents, MCP servers or web) keeps the user's global Codex setup (Astra xhigh, a dozen MCP servers) out of Luna's context. Copy `auth.json` in, delete it afterwards.
- `windows.sandbox = "elevated"` in a fresh home hangs: the sandbox setup helper needs the admin-provisioned secrets that live only in the real `~/.codex`. Luna's first shell command never returned and it sat polling a stuck cell (first smoke attempt, about half a cent). `unelevated` works without setup.
- The plugin reports no usage; per-response usage with model and effort is in `CODEX_HOME/sessions/**/rollout-*.jsonl`, the same source the Codex team's accounting reads.
- Bash timeouts must be raised (`BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS`) so the forwarder waits rather than times out at two minutes.

## Limits

One run; a fixture both worker vendors have now solved several times; no correction loop exercised; Luna wrote 7 tests where Opus wrote 39 and Fable 17, which the fixture does not score. Costs mix two subscriptions and are API-equivalent estimates on both sides, not bills. The Sonnet forwarder is part of the plugin's design and was counted; the plugin's Stop and SessionStart hooks ran but made no model calls. Three of the four smoke and diagnostic sessions before this run cost about $0.03 combined and are excluded.

## Identities

- Skill SHA-256: `272a647921b7e67818a68c0bfadef7f49711ae346a52addb33154b84fb21ac12`
- Claude session `7a8b1417-bd6a-4c35-b33e-7f7c01bf7746`; Codex thread `01a08db9-f793-7441-a417-42eb905d5e21`; Codex CLI 0.153.4; plugin `codex@openai-codex` 1.0.6 (file hashes in the manifest)
- Root `%LOCALAPPDATA%\Temp\claude-adapters-luna-d442ba61` (temporary; auth copy removed); manifest, receipts, summary and the three Codex rollouts under `private/luna/`
