---
name: claude-agent-deployment
description: Route authorized subagent work to Opus 5 Low for evidence, retrieval and source checking, or Fable 5.1 Medium or High for implementation and diagnosis. Use when planning, executing, or auditing delegated work.
---

# Claude Agent Deployment

Minimize the total cost of reaching an accepted result, counting coordination, review, and
corrections, while meeting correctness requirements.

This skill does not authorize delegation or expand scope. Higher-priority instructions and new
explicit user choices take precedence.

The skill is self-contained. Do not load reference material from the repository it ships from
during operational use.

## Dispatch

Effort values are `low`, `medium`, `high`, `xhigh`, `max`. Use these exact strings.

| Role | Model | Effort |
|---|---|---|
| Orchestrator | Fable 5.1 | `medium`, or `high` when requirements are ambiguous, the work spans several files with shared design, or acceptance itself needs judgment |
| Scout | Opus 5 | `low` |
| Builder | Fable 5.1 | `medium`, or `high` for non-mechanical implementation |
| Diagnostician | Fable 5.1 | `high` |
| Reviewer | Fable 5.1 | `high`, or `medium` when reviewing mechanical work |
| Verifier (provisional, see below) | Opus 5 | `low` |

Set model and effort explicitly when you dispatch, then confirm the worker's effective
configuration matches what you asked for. A generic fork is not a cheaper-model dispatch: it can
carry the parent's model and effort, so a worker meant to be cheap silently costs orchestrator
rates. Fork deliberately, when the worker needs the parent's context and its cache, and dispatch a
defined worker when you want a different model.

Keep the orchestrator's own model stable through a coherent task and delegate instead of switching
it, which preserves the conversation's cache. This is a preference, not a rule: a warm cache does
not by itself make the expensive model the cheaper choice. If it does not match, or your dispatch mechanism cannot
set effort at all, do not delegate on an inherited setting: report the limitation and keep the work
local. An unintended effort defeats the cost control this table exists for. Never substitute Sonnet
for a Scout, and never substitute `max` for `high`. If the worker type you were told to use is not
available, stop and report it; a built-in agent type is not a substitute, because it carries its
own model and effort.

Keep work local when delegation costs more than it saves. Delegate when you can name the benefit:
the work would otherwise load your context with material you do not need to keep, or it is
genuinely independent and can run while you do something else. Volume of tool calls alone is not a
reason.

Before delegating, name the work you will stop doing and the check you will use that does not redo
it. If acceptance requires you to read the same sources the worker reads, delegating the writing
does not reduce cost; keep it local, or delegate verification only where a checker adequate for
that kind of error has already been shown.

Four things decide where work goes, and no single one settles it: how ambiguous the requirement is,
how tightly the work couples to other work, what a wrong result costs, and whether correctness can
be checked independently of the worker that produced it. Settle the check before choosing a cheaper
worker. A large mechanical change with an exhaustive check suits one; a small change with unclear
consequences does not, however small it looks.

The orchestrator owns routing, integration, escalation, and final acceptance. Workers return
results or blockers, and redelegate only with assigned permission.

Fable 5.1 Low and Opus 5 Medium hold no role here. Use them only when the user names them.

## Choose the role

### Scout: evidence, retrieval, repetitive edits

Opus 5 at `low`. Use it for bounded retrieval, repository mapping, reading large document or code
sets, extraction, and repetitive edits with objective checks.

Require exact file and symbol references, explicit coverage gaps, and observations kept separate
from hypotheses.

A claim that something is absent needs the search that establishes it. "No other callers", "nothing
else uses this", "all records processed" are only usable with the scope and method that produced
them. Without that, treat the claim as unchecked.

Repetitive edits are writes. Before running Scouts in parallel on them, settle the shared behavior
and interfaces yourself, or keep the edits sequential.

**Do not give a Scout non-mechanical implementation or design judgment.** Delegate exploration only
when it reduces downstream work, and skip it when you already hold adequate evidence. Repository
size alone does not justify routing hard reasoning to a Scout.

### Builder: implementation

Supply expected behavior, interfaces, constraints to preserve, and acceptance checks. Then pick the
effort by the shape of the work:

- `medium` for bounded, well-specified implementation that follows an established pattern in the
  codebase.
- `high` for substantial interacting logic, compatibility risk, or subtle correctness requirements.
- `xhigh` or `max` only for a demonstrated unresolved reasoning need, per the escalation ceiling.

This split is a routing hypothesis worth measuring, not a settled result. If Medium work keeps
coming back with corrections, move the boundary rather than defaulting everything to High.

One Builder keeps a coupled implementation through its fixes and focused checks.

### Diagnostician: uncertain cause or design

Fable 5.1 at `high`. Use it when the cause or the right design is unclear. Require a reproduction
or a discriminating check, an evidence-backed explanation, the uncertainty that remains, and an
implementation contract.

Diagnosis is read-only, except for scratch or test edits you explicitly assign to reproduce the
problem. General permission to fix a project does not grant the diagnostician production-write
ownership.

### Reviewer: material correctness

Fable 5.1 at `high`, or `medium` for mechanical work. Use a Reviewer when independence from the
implementer would materially change what gets caught: the change touches behavior a user relies on,
or the implementer both wrote the code and defined the checks that pass it. An orchestrator
reviewing at its own effort covers ordinary work, and a second reviewer should not repeat it.

### Verifier: claims, facts, citations

Opus 5 at `low` for checking a deliverable against supplied sources; Opus 4.8 at `max` only when
the user names it or the failure is a confident wrong claim about the world rather than about the
sources (facts, API and version assertions). On the one source-fidelity test run so far, Opus 4.8
`max`, Fable 5.1 `high` and Opus 5 `low` all returned clean full-coverage reports on an answer with
a known inverted proposal, at four, three and one units of cost. A clean review report is weak
evidence; a review that returns findings has done more work than one that returns none. Where a
mechanical checker can enforce part of the contract, run it first and give the Verifier only what
remains.

Do not use it to review code. Route material-correctness review of code to a Reviewer.

## Never assign these

| Configuration | Use instead | Failure to expect |
|---|---|---|
| Sonnet 5, any effort | Opus 5 Low | Breaks down in agentic loops and asserts wrong answers on knowledge questions. The saving over Opus 5 Low is small enough to be erased by one correction. |
| Opus 5 High, Xhigh, Max | Fable 5.1 Medium or High | Costs more than the Fable 5.1 setting that does the job better. |
| Fable 5 | Fable 5.1 High | Costs more for weaker work. |
| Opus 4.8 Max, unless the user names it | The role that fits the work: Scout, Builder, Diagnostician, or Opus 5 Low as Verifier | Slow, expensive, and weak on agentic work. Its only measured strength is answering knowledge questions wrongly less often; on source checking it cost four times Opus 5 Low and caught nothing more. |

Sonnet 5 stays acceptable for single-shot, non-agentic text work when the user asks for it. Do not
substitute it for a Scout.

## Escalation ceiling

Reach for Fable 5.1 `xhigh` only when you can name an unresolved reasoning need, or the user asks
for it.

`xhigh` is the default escalation. Do not reach for Fable 5.1 `max` as a reflex after a failure:
it costs more than `xhigh` and has not shown a matching gain on implementation work. Use it when
you can name the reason, such as a task whose binding constraint is breadth of recalled knowledge
across many unfamiliar libraries or domains, or when task-level evidence favours it.

Raise effort only for a demonstrated reasoning limitation. Do not raise effort to compensate for
missing evidence, an unclear specification, or a tooling problem.

## Wrong answers

Lowering effort does not make a worker more cautious. Across Fable 5.1's effort range the share of
questions answered wrongly falls as effort rises, so do not drop to a lower effort hoping for fewer
fabrications.

When a plausible wrong answer entering the work is the risk you care about, control it through the
assignment rather than the dial:

- Require every non-obvious claim to cite the file, symbol, or source it came from, and treat an
  uncited claim as unverified.
- Ask for remaining uncertainty to be stated explicitly, separately from findings.
- State when "unknown" or "not found" is a legitimate result. Workers assert more when the packet
  implies an answer must exist.
- Check claims against their sources, and add a separate Verifier when independence from the
  author would change what gets caught.

## Assignment packet

Send a self-contained packet, normally under 500 words:

```text
Role, outcome, and scope:
Owned files; read/write permissions; dependencies and interfaces:
Relevant instructions, evidence paths, and search entry points:
Constraints and behavior to preserve:
Decisions and rationale to preserve; report contradictory evidence before changing them:
What "unknown" or "not found" looks like, if that is a valid result:
Acceptance checks:
Expected duration; checkpoint or work budget; blocker reporting:
Return: results, exact failures/checks, artifacts, and unresolved risks.
```

Pass the relevant decisions and the exact decision-critical evidence, not a bare task summary and
not the entire history. Preserve user constraints, permissions, and the decisions above. Reuse suitable workers for in-scope
continuations. Keep handoffs near 200 words, linking longer evidence without dropping
decision-critical detail.

## Fan-out

Scoping and concurrency are different levers. One scoped Scout can gather evidence and return it
before implementation starts, which keeps the orchestrator's context clean without running anything
at the same time. Reach for concurrency when the work is genuinely independent and the wait matters,
not to buy context isolation you could have had sequentially.

Retrieval and read-only checks parallelize readily, though they can still duplicate each other's
work if you do not divide them. Parallel writing needs agreed interfaces and behavior settled
before the workers start. Separate files alone do not establish independence: shared behavior,
schemas, mutable state, or a common API can require sequential work even when no two workers touch
the same path.

Start with one worker and justify each additional one. Do not add workers to supply more opinions,
and do not instruct workers to take deliberately different approaches. Each added worker brings
coordination and integration cost that the model price never shows, and two workers who must agree
usually cost more than one worker doing both parts.

## Review and acceptance

Mechanical edits with strong objective checks need no extra reviewer.

Supply the checker; do not accept one the worker wrote. A worker that reports passing its own check
has reported completion, not acceptance. Passing a mechanical checker is not verification of
meaning: when you keep final verification of a deliverable whose correctness depends on its
sources, read the sources for the records you accept, or give that reading to a Verifier and
inspect its findings. A worker's flagged judgment calls are yours to check, not to pass on.

Reviews are read-only. Inspect the requirements, the diff, relevant source, and the checks yourself
instead of trusting the implementer's summary. Findings need location, triggering condition,
impact, and evidence. Rank by impact and credible exposure rather than by count. A review that
finds defects has succeeded.

Acceptance criteria are fixed for the worker. A worker that cannot pass them reports a blocker; it
does not relax a check, narrow the requirement, or edit the test to fit the implementation. Only the
orchestrator revises them, and only within what the user actually asked for.

Once you delegate implementation, verify the deliverable rather than reproducing it. Inspect the
acceptance evidence and the changes; do not re-run every search and edit to stay busy.

Workers run focused acceptance checks. The orchestrator integrates results and runs broader checks
when the changes or unresolved risks justify them. Route fixes to the implementation owner and
recheck the affected risks without repeating the whole review.

## Attempts and escalation

Judge failure at assignment acceptance, not at each tool call or failing test. Allow corrections
within the agreed budget. An expected failing regression test before a fix is not a failure. Stop
repeating an approach that is not working until you have new evidence.

- **Accepted:** checks or evidence support the outcome. Reopen only for new evidence, changed
  dependencies, or required review.
- **Blocked:** access, dependencies, or tool failures prevent progress. Resolve within existing
  authority. Switching models is not the default remedy, and identifying an external root cause
  can be a successful diagnosis.
- **Incomplete at checkpoint:** return progress and remaining work. Demonstrated progress can
  justify a revised checkpoint within user limits.
- **Substantive failure:** an acceptance failure, wrong core assumption, or missed requirement
  survives the bounded attempt.

A worker that runs out of turns has returned partial work, not a completed task, whatever its
closing message says. It is also not evidence of a reasoning limit. Read the evidence it returned
and what remains before deciding whether to continue it, narrow the scope, or move to a stronger
worker.

A Scout that fails on non-trivial work has usually hit a judgment problem. Send it to a
Diagnostician when the cause or design is unclear, and to a Builder when the requirement was clear
and only the execution fell short.

A Diagnostician that fails substantively changes footing rather than repeating: hand the next
attempt a narrowed scope, the evidence already gathered, and write ownership if implementation is
now the point. Narrow the scope when the failure came from missing evidence or an unclear
requirement. Raise effort when the failure showed a reasoning limit you can name. Preserve partial
work, and do not restart discovery or cycle through the failed role.

If a Builder at `high` fails, separate evidence, environment, specification, and capability
problems before continuing. Do not repeat unchanged attempts or raise effort without a concrete
reason.

## Waiting and health

Use runtime event waits when no useful independent orchestrator work remains. Wait across active
workers together where your runtime supports it. An empty timeout
proves neither failure nor health. Resume waiting unless a blocker, a due checkpoint, or an
exhausted budget requires action. Do not poll after each timeout or add "still running" checks.

At a due checkpoint without evidence, make one compact non-interrupting status check if your
runtime offers one. Judge progress from milestones rather than from a running flag. If progress
stays unobservable, spend the budget deciding whether to continue, narrow, or stop.

## Transfer ownership

Confirm the prior worker and its writing commands have stopped before a successor edits the same
files. Preserve partial work and unrelated user edits. Transfer owned files, the current diff and
artifacts, exact failures, checks, and open questions. If you cannot confirm the previous writer
stopped, keep the successor read-only or on non-overlapping work.

## Evaluate the policy

Compare against a single-agent baseline on the same tasks and acceptance criteria: total
accepted-task cost, elapsed time, corrections, and missed defects, counting coordination and
review. A team finishing sooner does not show that it cost less. Keep API list prices separate from
subscription allowance telemetry.

When asked for a deployment plan, state roles, models, efforts, scope, dependencies, and acceptance
checks, and justify any extra worker or review pass.
