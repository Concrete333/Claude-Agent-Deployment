# Claude Agent Deployment

A routing policy for delegating subagent work across Claude models, chosen on cost and measured
capability. `SKILL.md` holds the operational policy. This file records the evidence behind it.

A companion policy for OpenAI models lives in a separate `Codex-Agent-Deployment` repository, built
the same way from the same source so the two can be compared like for like. It is not yet public.

## Assumed setup

Fable 5.1 at medium or high effort as the orchestrator, delegating to workers whose model and
effort you set explicitly per assignment.

## Evidence base

Source: the Artificial Analysis Intelligence Index v4.3 and its component evaluations, at
<https://artificialanalysis.ai/models>. I captured 16 Claude model and reasoning-effort
configurations on 8 September 2026, reading the values behind the public charts and checking each
one against the label its chart prints. No value disagreed.

The lineup covers five Claude families: Sonnet 5, Opus 4.8, Opus 5, Fable 5, and Fable 5.1. Fable
5.1 scores highest of the five on the composite index, which is why most roles below route to it.

Cost figures are weighted USD per Intelligence Index task at API list prices. **A Claude
subscription is not billed per token**, so read cost as a proxy for how quickly work consumes an
allowance rather than as a bill. The routing in `SKILL.md` rests on relative capability and
relative burn, both of which survive that caveat.

Fifteen of the sixteen configurations have published cost data. Sonnet 5 Non-reasoning does not,
so it is absent from every cost table here.

Full workbook: `docs/benchmarks/claude-model-evidence-2026-09-08.xlsx`. Per `AGENTS.md`, it is a
human reference and should stay out of agent context.

## The full lineup

Agentic coding is Terminal-Bench v4.0; long context is AA-LCR v1.1. "Frontier" marks a
configuration that nothing else beats on both index and price.

| Configuration | Index | $/task | Agentic coding | Long context | Frontier |
|---|---:|---:|---:|---:|:--:|
| Fable 5.1 Max | 53.4 | 7.63 | 52.0% | 85.3% | yes |
| Fable 5.1 Xhigh | 53.2 | 5.98 | 55.1% | 83.0% | yes |
| Fable 5.1 High | 51.2 | 3.91 | 52.0% | 83.7% | yes |
| Opus 5 Max | 50.7 | 5.86 | 49.0% | 79.3% | no |
| Fable 5 | 49.7 | 8.75 | 42.4% | 82.3% | no |
| Opus 5 Xhigh | 49.7 | 4.88 | 46.5% | 80.3% | no |
| Fable 5.1 Medium | 49.1 | 2.98 | 44.9% | 84.7% | yes |
| Opus 5 High | 48.2 | 3.61 | 46.0% | 79.0% | no |
| Fable 5.1 Low | 47.0 | 2.37 | 40.4% | 82.3% | yes |
| Opus 5 Medium | 45.1 | 2.19 | 34.3% | 82.0% | yes |
| Opus 4.8 Max | 42.0 | 4.08 | 21.7% | 77.7% | no |
| Opus 5 Low | 39.8 | 1.10 | 26.3% | 81.3% | yes |
| Sonnet 5 Max | 38.4 | 5.09 | 14.1% | 82.0% | no |
| Sonnet 5 Medium | 28.4 | 1.00 | 2.0% | 73.7% | yes |
| Sonnet 5 Low | 24.7 | 0.51 | 2.5% | 67.3% | yes |

Nine configurations sit on the frontier. For each of the other six, something else scores at least
as high for the same money or less.

The frontier is a cost-efficiency ranking, not a recommendation set. Both Sonnet 5 rows are
Pareto-efficient and both are excluded from subagent routing, for reasons in the next section.

## Cost of moving up the frontier

Ordered cheapest first. Each step's cost per extra index point is computed from unrounded index
values, so it will not reproduce exactly from the rounded column above.

| Step | Configuration | Index | $/task | Cost per extra index point |
|---|---|---:|---:|---:|
| 1 | Sonnet 5 Low | 24.7 | 0.51 | n/a |
| 2 | Sonnet 5 Medium | 28.4 | 1.00 | 0.13 |
| 3 | **Opus 5 Low** | 39.8 | 1.10 | **0.01** |
| 4 | Opus 5 Medium | 45.1 | 2.19 | 0.21 |
| 5 | Fable 5.1 Low | 47.0 | 2.37 | 0.09 |
| 6 | **Fable 5.1 Medium** | 49.1 | 2.98 | 0.30 |
| 7 | **Fable 5.1 High** | 51.2 | 3.91 | 0.43 |
| 8 | Fable 5.1 Xhigh | 53.2 | 5.98 | 1.05 |
| 9 | Fable 5.1 Max | 53.4 | 7.63 | 8.70 † |

† The gain at step 9 is 0.19 index points, below the roughly one-point noise floor. Treat the
ratio as unstable and judge that step on its absolute cost: $1.65 more per task for a difference
the benchmark cannot reliably distinguish from zero.

Opus 5 Low is the standout. It adds 11.4 index points over Sonnet 5 Medium for ten cents, the
steepest value step in the set.

## Sonnet 5 is not a cheap worker

Sending bulk work to the cheapest model fails for anything agentic.

| | Sonnet 5 Low | Sonnet 5 Medium | Opus 5 Low |
|---|---:|---:|---:|
| Agentic coding (Terminal-Bench) | 2.5% | 2.0% | 26.3% |
| Agentic knowledge work (AA-Briefcase) | 21.4% | 27.7% | 35.8% |
| SaaS workflows (AutomationBench) | 19.9% | 27.9% | 51.8% |
| Knowledge reliability (Omniscience Index) | -8.2 | -6.9 | +28.6 |
| Cost per task | $0.51 | $1.00 | $1.10 |

Sonnet 5 at low and medium effort scores negative on knowledge reliability, giving more wrong
answers than right ones, and it barely functions in a terminal loop. Opus 5 Low costs ten cents
more than Sonnet 5 Medium and works. Sonnet 5 Max fares worse on value at $5.09, or 4.6 times Opus
5 Low, for a lower overall score and 14.1% on agentic coding.

Sonnet 5 suits single-shot, non-agentic text work. Do not route subagent work to it just because
it is cheap.

## Opus 4.8 Max earns a role despite being superseded

Opus 5 Medium beats Opus 4.8 Max on general work at roughly half the price. On one measure nothing else in
the lineup comes close.

| Configuration | Non-hallucination rate | Answer accuracy |
|---|---:|---:|
| **Opus 4.8 Max** | **60.7%** | 48.8% |
| Opus 5 Medium | 39.3% | 57.1% |
| Fable 5.1 Low | 34.4% | 60.2% |
| Fable 5.1 High | 31.2% | 64.9% |
| Fable 5.1 Medium | 30.9% | 63.1% |
| Fable 5.1 Xhigh | 29.5% | 66.2% |
| Fable 5.1 Max | 27.4% | 67.2% |

Artificial Analysis defines the non-hallucination rate as one minus the hallucination rate. It and
answer accuracy use different denominators, so the two columns do not sum to 100% and you cannot
subtract one from the other to recover a refusal rate.

Opus 4.8 Max trades answer coverage for reliability. When a confident wrong claim is the expensive
outcome, such as a fabricated API, a mis-cited source, or an invented version number, that is the
trade to make.

## Effort raises accuracy and assertion together

Reading the Fable 5.1 rows above in effort order (low, medium, high, xhigh, max): answer accuracy
climbs steadily from 60.2% to 67.2%, while the non-hallucination rate runs 34.4%, 30.9%, 31.2%,
29.5%, 27.4%. Accuracy rises monotonically and non-hallucination broadly falls, with one small
reversal at high effort. Across the full range, higher effort answers more questions correctly and
asserts wrong answers more often.

The composite Omniscience Index still improves with effort, because the accuracy gain outweighs the
hallucination cost on average. Averages are the wrong lens when one failure mode costs far more
than the other. If a plausible wrong answer entering your work is the real risk, raising effort
moves you the wrong way. Route to Opus 5 at low effort, or add a Verifier pass.

That is why every assignment packet in `SKILL.md` asks the worker what "unknown" looks like.

## Fable 5.1 Max is not the escalation target

| | Fable 5.1 High | Fable 5.1 Xhigh | Fable 5.1 Max |
|---|---:|---:|---:|
| Agentic coding (Terminal-Bench) | 52.0% | **55.1%** | 52.0% |
| Intelligence Index | 51.2 | 53.2 | 53.4 |
| Cost per task | $3.91 | $5.98 | $7.63 |

Max costs 28% more than Xhigh and matches High on agentic coding. Escalating to Max after a failure
costs about twice High and buys nothing for implementation work. Xhigh is the real ceiling, and
reach for it only when you can name the unresolved reasoning need.

## What routing retrieval to a Builder costs

Take an audit of twelve modules for one defect class, which is retrieval-shaped work. Using
per-task benchmark cost as the unit:

- Twelve Builders at Fable 5.1 High: 12 x $3.91 = **$46.92**
- Twelve Scouts at Opus 5 Low gathering evidence, one Fable 5.1 High synthesizing:
  (12 x $1.10) + $3.91 = **$17.11** across thirteen agents

The second arrangement costs about 37% as much. This is not a saving the policy delivers so much
as a mistake it prevents: nobody following `SKILL.md` would send retrieval to twelve Builders,
because the Scout role exists for exactly this shape of work. The number shows what the misroute
would cost.

The saving holds only while the Scouts do retrieval rather than judgment. Ask those same Scouts to
write the fixes and the coding gap, 26.3% against 52.0%, comes back as corrections, review passes,
and rework that the model price never showed.

Treat this as the shape of the difference rather than a forecast. Context size, cache behavior,
retries, and parent re-entry dominate real orchestration cost, and these task-level figures capture
none of them.

## What the multi-agent literature says

The published work splits less than it first appears. The strongest case for parallelism,
[Anthropic's multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
reports a 90.2% gain over a single agent on an internal research evaluation while saying multi-agent
suits "most coding tasks" poorly, and it keeps synthesis in one agent while distributing only the
reading. [Cognition](https://cognition.com/blog/dont-build-multi-agents) documents the opposite
failure: parallel workers make conflicting implicit decisions that collide at merge.
[LangChain](https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems) names the axis
both are describing, that reads parallelize and writes do not. That asymmetry, rather than a verdict
on parallelism, is what shapes the Fan-out section of `SKILL.md`.

On cost, [AI Agents That Matter](https://arxiv.org/abs/2407.01502) is the sharpest result: on
HumanEval, LATS cost $134.50 against $2.45 for a simple warming baseline, over fifty times more, and
scored lower (88.0% against 93.2%). Across the wider set the paper reports that "for substantially
similar accuracy, the cost can differ by almost two orders of magnitude", and that simple baselines
Pareto-dominated the complex architectures. That is the reason the evaluation section asks for a
single-agent baseline rather than a comparison between two team designs.

[MAST](https://arxiv.org/abs/2503.13657) catalogues 14 failure modes across 1,600+ traces from seven
frameworks, most of them coordination and verification faults rather than model limits. Targeted
interventions helped without resolving the problem: better role specifications added 9.4% and
stronger verification 15.6% on ChatDev, with completion rates still low. Its reported failure rates
run from 41% to 86.7% across the frameworks surveyed.

Two results are easy to over-read in our favour. The
[equal-budget study](https://arxiv.org/abs/2604.02460) caps thinking tokens rather than actual
consumption or spend, and excludes tool-based coding, so it argues against convening reasoning
committees by default rather than showing that more effort always wins.
[Self-Manager](https://arxiv.org/html/2601.17879v1) shows isolated contexts cut information loss,
at higher latency and tool-call counts, and it does not show that concurrent scouts save money on a
repository. Isolation is what helps; running the scouts at the same time is a separate decision.

Two findings are quoted more broadly than they support. The
[Nature study](https://www.nature.com/articles/s42256-026-01268-y) reports a capability-saturation
threshold near 45% baseline task success, above which extra agents tend to hurt, but its SWE-bench
and Terminal-Bench cells run 20 tasks with confidence intervals near 20 percentage points. It is a
reason for restraint, not a dispatch cutoff. Anthropic's token multiples compare agents against
chat, not multi-agent against single-agent coding, so they do not size the overhead of the fan-out
described here.

## Limits

- Index points are not units of useful work. They do not measure task success or cost per
  completed job.
- Differences under about one index point sit inside measurement noise. The step 9 row in the
  frontier table is the one place that floor bites, and it is marked.
- These are benchmark-harness figures, not agent loops carrying large tool-call contexts.
- Several evaluations cover only part of the lineup. Every figure quoted in this README comes from
  an evaluation covering at least 15 of the 16 configurations.
- None of this justifies a routing change on its own. Test bounded tasks, review outcomes, and
  compare total accepted-task cost before adopting or amending the policy.
