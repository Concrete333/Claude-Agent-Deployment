---
name: claude-agent-deployment
description: Route authorized subagent work to Opus 5 Low for evidence and retrieval, Fable 5.1 Medium or High for implementation and diagnosis, or Opus 4.8 Max for factual verification. Use when planning, executing, or auditing delegated work.
---

# Claude Agent Deployment

Minimize the total cost of reaching an accepted result, counting coordination, review, and
corrections, while meeting correctness requirements.

This skill does not authorize delegation or expand scope. Higher-priority instructions and new
explicit user choices take precedence.

## Dispatch

Effort values are `low`, `medium`, `high`, `xhigh`, `max`. Use these exact strings.

| Role | Model | Effort |
|---|---|---|
| Orchestrator | Fable 5.1 | `medium`, or `high` when requirements are ambiguous, the work spans several files with shared design, or acceptance itself needs judgment |
| Scout | Opus 5 | `low` |
| Builder | Fable 5.1 | `medium`, or `high` for non-mechanical implementation |
| Diagnostician | Fable 5.1 | `high` |
| Reviewer | Fable 5.1 | `high`, or `medium` when reviewing mechanical work |
| Verifier | Opus 4.8 | `max` |

Set model and effort explicitly when you dispatch. If your dispatch mechanism cannot set effort,
report that limitation before delegating and choose from this list only: Opus 5 for retrieval,
Fable 5.1 for implementation, diagnosis, and review, Opus 4.8 for verification. Never substitute
Sonnet for a Scout, and never substitute `max` for `high`.

Keep work local when delegation costs more than it saves. Delegate when the assignment needs more
than a few tool calls of independent work, or when it can run while you do something else.

The orchestrator owns routing, integration, escalation, and final acceptance. Workers return
results or blockers, and redelegate only with assigned permission.

Fable 5.1 Low and Opus 5 Medium hold no role here. Use them only when the user names them.

## Choose the role

### Scout: evidence, retrieval, repetitive edits

Opus 5 at `low`. Use it for bounded retrieval, repository mapping, reading large document or code
sets, extraction, and repetitive edits with objective checks.

Require exact file and symbol references, explicit coverage gaps, and observations kept separate
from hypotheses.

Repetitive edits are writes. Before running Scouts in parallel on them, settle the shared behavior
and interfaces yourself, or keep the edits sequential.

**Do not give a Scout non-mechanical implementation or design judgment.** Delegate exploration only
when it reduces downstream work, and skip it when you already hold adequate evidence. Repository
size alone does not justify routing hard reasoning to a Scout.

### Builder: implementation

Fable 5.1 at `medium` by default. Move to `high` when the work is non-mechanical, spans interacting
files, or carries compatibility constraints. Supply expected behavior, interfaces, constraints to
preserve, and acceptance checks.

Keep a coupled implementation with one Builder through its fixes and focused checks. Handing each
step to a fresh agent loses context and buys nothing.

### Diagnostician: uncertain cause or design

Fable 5.1 at `high`. Use it when the cause or the right design is unclear. Require a reproduction
or a discriminating check, an evidence-backed explanation, the uncertainty that remains, and an
implementation contract.

Diagnosis is read-only, except for scratch or test edits you explicitly assign to reproduce the
problem. General permission to fix a project does not grant the diagnostician production-write
ownership.

### Reviewer: material correctness

Fable 5.1 at `high`, or `medium` for mechanical work. Use a Reviewer when the change touches
behavior a user relies on, or when the implementer wrote its own acceptance checks. An orchestrator
reviewing at its own effort covers ordinary work, and a second reviewer should not repeat it.

### Verifier: claims, facts, citations

Opus 4.8 at `max`. Use it when a confident wrong statement is the expensive failure: checking
factual claims, citations, API and version assertions, or a summary against its sources.

Do not use it to review code. Route material-correctness review of code to a Reviewer.

## Never assign these

| Configuration | Use instead | Failure to expect |
|---|---|---|
| Sonnet 5, any effort | Opus 5 Low | Breaks down in agentic loops and asserts wrong answers on knowledge questions. The saving over Opus 5 Low is small enough to be erased by one correction. |
| Opus 5 High, Xhigh, Max | Fable 5.1 Medium or High | Costs more than the Fable 5.1 setting that does the job better. |
| Fable 5 | Fable 5.1 High | Costs more for weaker work. |
| Opus 4.8 Max, outside verification | Opus 5 Medium | Slow, expensive, and weak on agentic work. Its only strength is declining to answer. |

Sonnet 5 stays acceptable for single-shot, non-agentic text work when the user asks for it. Do not
substitute it for a Scout.

## Escalation ceiling

Reach for Fable 5.1 `xhigh` only when you can name an unresolved reasoning need, or the user asks
for it.

Fable 5.1 `max` is not an implementation upgrade and is no better than `high` at agentic coding.
Reserve it for tasks where breadth of recalled knowledge is the binding constraint, such as
questions spanning many unfamiliar libraries or domains. Never reach for it as a reflex after a
failure.

Raise effort only for a demonstrated reasoning limitation. Do not raise effort to compensate for
missing evidence, an unclear specification, or a tooling problem.

## Effort and fabrication

Raising Fable 5.1's effort increases both how much it gets right and how often it asserts something
it does not know.

When a plausible wrong answer entering the work is the risk you care about, prefer lower effort, an
Opus 5 worker at `low`, or a Verifier pass. Raising effort moves that risk the wrong way.

State in the assignment when "unknown" or "not found" is a legitimate result. Workers assert more
when the packet implies an answer must exist.

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

Pass the working trace, not just a task summary. Inherit minimal history while preserving user
constraints, permissions, and the decisions above. Reuse suitable workers for in-scope
continuations. Keep handoffs near 200 words, linking longer evidence without dropping
decision-critical detail.

## Fan-out

Keep tightly coupled implementation with one owner, carried through its fixes and focused checks.

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

Reviews are read-only. Inspect the requirements, the diff, relevant source, and the checks yourself
instead of trusting the implementer's summary. Findings need location, triggering condition,
impact, and evidence. Rank by impact and credible exposure rather than by count. A review that
finds defects has succeeded.

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

A Scout that fails on non-trivial work has usually hit a judgment problem. Send it to a
Diagnostician when the cause or design is unclear, and to a Builder when the requirement was clear
and only the execution fell short.

A Diagnostician that fails substantively keeps its model and effort but changes footing: hand the
next attempt a narrowed scope, the evidence already gathered, and write ownership if implementation
is now the point. Preserve partial work, and do not restart discovery or cycle through the failed
role.

If a Builder at `high` fails, separate evidence, environment, specification, and capability
problems before continuing. Do not repeat unchanged attempts or raise effort without a concrete
reason.

## Waiting and health

Use runtime event waits when no useful independent orchestrator work remains, and do not duplicate
worker work. Wait across active workers together where your runtime supports it. An empty timeout
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

Compare against a single-agent baseline on the same tasks and acceptance criteria, counting
coordination, review, and correction costs. A team finishing sooner does not show that it cost
less.

Compare total accepted-task cost, elapsed time, corrections, and missed defects on like-for-like
work. Keep API list prices separate from subscription allowance telemetry.

When asked for a deployment plan, state roles, models, efforts, scope, dependencies, and acceptance
checks, and justify any extra worker or review pass.
