# Prose arm D under the amended skill — run 11 September 2026, interrupted

**Under the amended skill the orchestrator read sources. It had read eleven of the fifty threads, ISSUE-040 among them, when the account's session limit cut the session off, so the run answers the question it was run for and not the one after it.** Cost to the cut-off $2.22, already above the first D ($1.84) and close to solo Fable ($2.32). The worker's answer passed every automated check (50/50 decisions, valid citations). One run, incomplete.

| Run | Skill | Orchestrator | Worker (Opus 5 `low`) | Total | What the orchestrator read |
| --- | --- | ---: | ---: | ---: | --- |
| D, 10 Sep | before the review amendments | $0.54 | $1.30 | $1.84 | checker output only |
| D, 11 Sep | amended (`ba63213d…`) | $0.88 to cut-off | $1.35 | $2.22 to cut-off | SKILL.md, TASK.md, answer.json, 11 thread files, then stopped by the limit |
| A, 10 Sep | none | $2.32 | — | $2.32 | everything |

Same fixture, harness and worker definition (`PROSE_VARIANT=skill2`, fresh root, `run.py run D`). The orchestrator's transcript: read SKILL.md and TASK.md, dispatched one `scout`, ran `check.py`, read the answer, then opened ISSUE-015, 026, 013, 025, 030, 008, 037, 004, 040, 044 and 032 in turn. The next request returned "You've hit your session limit · resets 6:30pm"; the CLI reported `is_error: true` with the answer file already written. No resume was attempted: the context was about 155 k tokens and cold, so finishing would have cost about $2 of cache rewrite for a verification whose object (the worker's answer) already passes.

## What it settles

The first D run's "orchestrator read nothing" was the skill, not the task: with the amended text ("passing a mechanical checker is not verification of meaning ... read the sources for the records you accept, or give that reading to a Verifier") the same orchestrator on the same task started reading threads without being told to. The 10 September open question is closed in that direction.

## What it costs

Eleven threads cost about $0.34 of orchestrator spend beyond the first D's $0.54. Fifty at that rate is about $1.50, which would put a fully verified D near $3.30, above solo Fable at $2.32. That is the same conclusion the 10 September results drew from the other side: on read-dominated interpretation work, delegation saved money only by skipping verification, and once the coordinator verifies properly the saving is gone. A cheap verifier that qualifies on prose would change that; none has (the verifier diagnostic). The worker itself cost $1.30 to $1.35 both times, 25 k output tokens for 50 records, which is most of D's bill regardless of what the orchestrator does.

## Limits

One run, cut off by an account limit at turn 17, so whether the orchestrator would have caught anything, or would have read all fifty threads, is not observed. The worker's answer was automatically correct both times, so there was nothing for verification to catch; this run measures the cost of verifying, not its value. The cut-off session still cost $0.88 and is counted.

## Identities

- Session `28020e0d-b4bf-4a04-ab19-c219693312c7`; root `%LOCALAPPDATA%\Temp\claude-prose-skill2-lqnb2kxp`; answer SHA-256 `5d3a4839…`; receipts under `private/skill2/`
