# Adapter batch, Claude-native

Six transaction-import adapters, reusing the Codex team's qualified version-two fixture in place (146 visible and 98 held-out cases, corrected reference) from its private root under `Codex-Agent-Deployment/docs/benchmarks/adapter-batch/selection-ablation/local-fixture.json`. Nothing in that root is modified. Results: [A/D, 10 September 2026](results-2026-09-10.md) and [arm E with Luna Max via the Codex plugin, 11 September 2026](results-luna-2026-09-11.md).

- `adapters.py`: `prepare` (copies the fixture source into fresh A/D checkouts, qualifies the reference and rejects the stubs through this repository's grader), `run A|D` (one paid session each, refuses to repeat), `summarize` (protected-file hashes, visible and held-out conformance, added tests, per-model cost). Arms: A is Fable 5.1 `medium` solo with no skill and no Agent tool; D is the same orchestrator with the repository `SKILL.md` and one forced Opus 5 `low` builder. Imports the shared harness from `../prose-claude/run.py`.
- `luna.py`: arm E. Same fixture; Fable 5.1 orchestrator hands the batch to one Luna Max worker through OpenAI's `codex@openai-codex` plugin (1.0.6) in an isolated `CODEX_HOME`. `prepare`, `smoke`, `run`, `summarize`, `cleanup` (removes the copied `auth.json`).
- `private/` (ignored): receipts, manifest, summary; `private/luna/` holds the Codex rollouts.

The grader reimplements the Codex `grade.py` rules rather than importing it, so it runs without the Codex local fixture. Post-hoc probes (JSONL bare CR, 150k CSV memo) were run by hand and are recorded in the results.
