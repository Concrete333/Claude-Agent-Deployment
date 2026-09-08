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
subscription is not billed per token**, and nothing here establishes how API cost maps to
subscription allowance consumption. Treat the cost columns as a capability-per-price ranking under
one pricing model, not as a prediction of what any given workload will draw down.

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

| Configuration | Non-hallucination rate | Answer accuracy | Wrong answers, all questions |
|---|---:|---:|---:|
| **Opus 4.8 Max** | 60.7% | 48.8% | **20.1%** |
| Fable 5.1 Max | 27.4% | 67.2% | 23.8% |
| Fable 5.1 Xhigh | 29.5% | 66.2% | 23.8% |
| Fable 5.1 High | 31.2% | 64.9% | 24.1% |
| Fable 5.1 Medium | 30.9% | 63.1% | 25.5% |
| Fable 5.1 Low | 34.4% | 60.2% | 26.1% |
| Opus 5 Medium | 39.3% | 57.1% | 26.1% |
| Opus 5 Low | 37.8% | 56.0% | 27.4% |

Artificial Analysis defines the non-hallucination rate as one minus the hallucination rate, and
that hallucination rate is conditional on the questions the model did not answer correctly, not on
all questions. The third column converts it: wrong answers over all questions equals
(1 − non-hallucination rate) × (1 − accuracy). That identity reproduces the published Omniscience
Index exactly, to two decimal places, for every configuration in the workbook, which is what
confirms the conditional reading.

Opus 4.8 Max trades answer coverage for reliability and produces the fewest wrong answers overall.
When a confident wrong claim is the expensive outcome, such as a fabricated API, a mis-cited
source, or an invented version number, that is the trade to make. It is otherwise superseded, so
confirm it earns the cost on a sample of your own verification work.

## Lower effort does not buy caution

The falling non-hallucination rate as Fable 5.1 effort rises is easy to misread as more fabrication
at higher effort. It is not. That rate is conditional on the questions the model got wrong, and
raising effort shrinks the pool of questions it gets wrong. Converted to a share of all questions,
wrong answers fall from 26.1% at low effort to 23.8% at max.

So dropping to a lower effort to reduce fabrication makes it slightly worse, not better. Opus 5 Low
is the weakest of the non-Sonnet configurations on this measure at 27.4%.

Control wrong answers through the assignment instead: require citations for non-obvious claims,
ask for remaining uncertainty separately from findings, say when "unknown" is a valid result, and
add a Verifier pass when a wrong claim would be expensive to find later. `SKILL.md` states all four.

## Fable 5.1 Max is not the escalation target

| | Fable 5.1 High | Fable 5.1 Xhigh | Fable 5.1 Max |
|---|---:|---:|---:|
| Agentic coding (Terminal-Bench) | 52.0% | **55.1%** | 52.0% |
| Intelligence Index | 51.2 | 53.2 | 53.4 |
| Cost per task | $3.91 | $5.98 | $7.63 |

Max costs 28% more than Xhigh and matches High on agentic coding. Escalating to Max after a failure
costs about twice High and buys nothing for implementation work. Xhigh is the real ceiling, and
reach for it only when you can name the unresolved reasoning need.

## Routing retrieval to an implementation model

An audit that reads twelve modules looking for one defect class is retrieval-shaped work. Sending
it to Builders at Fable 5.1 High pays implementation-grade rates for reading, several times what
Scouts at Opus 5 Low cost per task, and the Scout role exists so that does not happen.

The comparison stops there. Per-task benchmark costs are averages over an evaluation harness, not
a forecast for a repository, and multiplying them by a worker count would not predict what either
arrangement actually costs. Context size, cache behavior, retries, and parent re-entry dominate
real orchestration cost and appear nowhere in these figures.

What does carry over is the direction: Scouts read, Builders build, and the gap between them on
agentic coding is wide enough that asking Scouts to write the fixes returns as corrections and
rework.

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
