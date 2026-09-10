# Prose migration trial, Claude-native

Reuses the Codex team's frozen Harbor 4.0 corpus (`cases.json`, `TASK.md`, `grade.py`, all byte-identical to `Codex-Agent-Deployment/docs/benchmarks/prose-migration/`) with a native Claude Code orchestrator and subagents. Results: [A/D trial](results-2026-09-10.md) and [verifier diagnostic](results-verifiers-2026-09-10.md), both 10 September 2026. Design and rationale: [trial plan](../../claude-trial-plan-2026-09-10.md).

`cases.json` contains the author's answer key. Never place it in a participant checkout; `run.py prepare` renders only the threads, the task and the checker.

- `check.py`: participant-visible mechanical checker derived from `TASK.md` only (schema, coverage, verbatim quotes, span and length limits, unchanged sources). Preflight it with `run.py preflight`; it must reject the mutants the frozen grader accepts.
- `run.py`: `prepare`, `preflight`, `smoke`, `run A|D`, `summarize`. Each paid mode runs once and refuses to repeat. Arms: A is Fable 5.1 `medium` solo with no skill and no Agent tool; D is the same orchestrator with the repository `SKILL.md` and a forced single Opus 5 `low` scout.
- `verify.py`: Stage 1 verifier diagnostic; three read-only reviewers of the saved Luna initial answer (`private/luna-initial-answer.json`, copied from the Codex experiment root).
- `probe_agents.py`: Haiku-priced discovery of how custom agents register in the installed CLI.
- `private/` (ignored): answers, receipts, manifest, summary from the local experiment root.

Runtime notes that cost real money to learn: do not use `--safe-mode` (it drops `--agents`); pass `--allowedTools` under `dontAsk`; send the prompt on stdin; set `FORCE_PROMPT_CACHING_5M=1` or accept one-hour cache writes.
