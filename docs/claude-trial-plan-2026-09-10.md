# Bounded trial plan for the Claude skill

Companion to the [audit](claude-audit-2026-09-10.md). Nothing here is authorized to run; each stage needs an explicit go and a budget figure before a paid session starts. Prices below are placeholders to be filled from the official pricing page at freeze time and recorded in the run plan.

## Objective

Lower total cost to an accepted result without reducing required accuracy. Two questions, in order, because the first decides whether the second can succeed on this task class.

Question 1. Can a Claude verifier, reading the sources, catch a meaning reversal in a delegated answer? If no Claude configuration cheaper than the orchestrator does, delegation cannot reduce cost on read-dominated work and the skill should say so.

Question 2. With the current Claude skill and native delegation, what does the orchestrator do on the prose task, and what does it cost against solo?

## Stage 0: freeze and preflight (no model calls)

Confirm runtime support before anything else. The Claude skill's own rule says that if effort cannot be set for a worker, keep the work local; if that rule fires, arm C is solo by construction and the trial measures nothing about delegation.

Check and record, with CLI version: whether a native subagent definition can pin model and effort, and whether the parent transcript records each subagent's model, effort, and usage buckets separately (uncached, cache write, cache read, output, helper models). If per-child usage is not recoverable from the transcript, use the `-p --output-format json` receipts per session and treat parent-plus-children as one bucket, stating that limitation.

Freeze and hash: the orchestrator (Fable 5.1 `medium`, per the skill's table), the allowed worker configurations (Opus 5 `low` Scout; Fable 5.1 `medium`/`high` Builder and Reviewer; Opus 4.8 `max` Verifier), the skill snapshot (`SKILL.md` at commit `231fc6b`), the task and corpus (`9ce6813c…`), the participant-visible checker, the external grader, the pricing table, cache TTL, permissions and tool lists per arm.

Participant-visible checker. Derive from `TASK.md` only. Rules: schema, every ID once in order, release and date, explanation 15 to 80 words, each quote 6 to 100 words with no `...`, `…` or bracketed text, quote found verbatim (whitespace-normalized) inside the cited lines, cited span at most 3 lines, per-record quote budget 160 words, source files and `TASK.md` unchanged. Preflight it on the rebuilt author reference and on the mutants from the audit; it must reject the one-word-ID, whole-file-span and two-word-explanation mutants that the frozen grader accepts. Run the preflight through the actual permission route the participants will use. Hash it and include it, unmodified, in every arm's checkout.

Leakage check. Inspect the effective system prompt for each arm (user and project `CLAUDE.md`, settings sources, memory, installed skills). A and B must contain no deployment policy text; C contains only the frozen skill. Record the inspection.

Fixture for Question 1. Reconstruct the initial Luna answer (hash `8842b97a…`) from the private `forced-luna` receipts. It stays outside participant context except as the review input.

## Stage 1: verifier diagnostic (Question 1)

Three fresh, isolated read-only sessions, each given the original task, all 50 sources, the initial Luna answer and a 160-word review assignment matching the Sol assignment in substance: full coverage, evidence-backed material findings, no hint that defects exist, no finding count. Tools: Read, Glob, Grep, plus the checker executable. Delegation off.

| Session | Configuration | Why |
|---|---|---|
| V1 | Opus 4.8 `max` | The skill's Verifier role, untested on source checking |
| V2 | Fable 5.1 `high` | The skill's Reviewer effort |
| V3 | Opus 5 `low` | Already run through the Codex wrapper; repeat natively for a matched tool set |

Score against the source, not against the three comparison findings alone. Report per session: ISSUE-040 caught or missed; 045 and 048 as advisory; any additional valid finding; false positives; the cost buckets; cache write share; requested versus verified effort.

Decision rule, agreed before running: if no session catches ISSUE-040, record that the Claude skill has no qualified cheap verifier for source-fidelity work and skip Stage 2's D arm; Stage 2 still runs A, B and C. If V1 or V2 catches it, D delegates verification to that configuration.

Bound: one run per session, cap each at $5 API-equivalent and 30 minutes, no retry. Expected total under $10.

## Stage 2: matched conditions on the prose task (Question 2)

Same frozen corpus, fresh checkouts, orchestrator fixed at Fable 5.1 `medium`.

| Arm | Skill | Delegation | Purpose |
|---|---|---|---|
| A | none | disabled (no Agent tool) | Solo baseline |
| B | none | native subagents available with the frozen worker definitions | Tool exposure without policy |
| C | frozen `SKILL.md` | as B | Skill's spontaneous routing |
| D (only if Stage 1 qualifies a verifier) | frozen `SKILL.md` plus one sentence requiring one Opus 5 `low` Scout to own reading and writing and the qualified configuration to own verification | as B | Tests the mechanism; reported as forced, never as routing |

Run A, B, C sequentially, then D. One run each in the pilot. If C stays solo, report that as the result and do not enlarge the task.

Repairs. Predefine now: after external grading and semantic review, each arm receives exactly one correction request naming the affected record IDs and the contract clause, sent to the same session, and its cost is added to that arm. Every arm is repaired the same way, or none is. This is what the Codex A/C pair lacked.

Accounting. For every session, parent and each child: uncached input, cache creation, cache read, output (thinking included, not added again), helper models, per-request maximum input. Preparation, semantic review and supervision are reported separately. API-equivalent only; never subscription allowance.

Evaluation. Frozen external grader first. Then semantic review of all explanations against source, blinded to arm by shuffling answer files under random names before review. Severity reported per finding as material, completeness, or wording, using the audit's classification.

Bounds: cap each arm at $8 API-equivalent and 45 minutes; a timeout is partial work. Pilot total under $35 for four arms. No automatic retry; a failed run is reported, not rerun.

## Stage 3: only if the pilot warrants it

Repeat Stage 2 twice more with counterbalanced order, on the same corpus, within an agreed budget, before drawing any policy conclusion. Then a held-out task authored by a model that was not a participant, with less conspicuous decisive evidence than the Harbor corpus, and the same protocol. The short-entrypoint restructure of the skill is a separate condition against C, on the three small revision-ab tasks, where declining delegation is the expected path.

## Deliverables

For each stage: a dated results report in `docs/benchmarks/` in the Claude repository with whole-workflow cost, acceptance, actual routing, limitations and immutable identities (hashes, session IDs, private receipt basenames). Raw receipts stay private. Negative results are reported with the same care as positive ones.
