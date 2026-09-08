# References

Sources behind the routing policy in `SKILL.md`. Each entry gives the premise and what was taken
from it. The skill itself carries no citations; this file is where they live.

## Model capability and cost

**Artificial Analysis Intelligence Index v4.3**
<https://artificialanalysis.ai/models>
*Premise:* Independent benchmarking of models and reasoning-effort settings on a composite of ten
evaluations, with per-task cost and token use.
*Taken:* The role assignments. Which Claude configuration goes to retrieval, implementation,
diagnosis, and verification, which configurations are beaten outright by a cheaper option, and
where raising effort stops paying. Captured 8 September 2026 across 16 Claude configurations.

**Kapoor, Stroebl, Siegel, Nadgir, Narayanan: "AI Agents That Matter"** (TMLR 2025)
<https://arxiv.org/abs/2407.01502>
*Premise:* Agent benchmarks report accuracy and ignore cost, so published architectures are more
complex and expensive than the results justify.
*Taken:* Evaluate against a baseline, not against another team design. On HumanEval a simple
warming baseline beat LATS on accuracy at a fraction of the cost, and the paper reports that for
similar accuracy "the cost can differ by almost two orders of magnitude". This is why the skill
asks for a single-agent baseline including coordination and correction costs.

## When to run more than one agent

**Anthropic: "How we built our multi-agent research system"** (June 2025)
<https://www.anthropic.com/engineering/multi-agent-research-system>
*Premise:* A lead agent with parallel subagents for open-ended research, reported as a large gain
over a single agent on their internal research evaluation.
*Taken:* Fan out for breadth-first work whose information exceeds one context, and keep synthesis
with one agent. Anthropic states the pattern suits most coding tasks poorly and suits work with
dependencies between agents poorly. Their token multiples compare agents against chat, not
multi-agent against single-agent, so they do not size fan-out overhead.

**Chase (LangChain): "How and when to build multi-agent systems"** (June 2025)
<https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems>
*Premise:* Reconciles the Anthropic and Cognition positions by asking what the subagents do rather
than how many there are.
*Taken:* Reads parallelize more readily than writes. Parallel writing is workable, but only with
context each worker can act on independently.

**Zhang, Zhu, Bansal, Fourney, Mozannar, Gerrits: "Optimizing Sequential Multi-Step Tasks with
Parallel LLM Agents"** <https://arxiv.org/html/2507.08944v1>
*Premise:* Run several multi-agent teams on the same task and either stop at the first success or
aggregate answers.
*Taken:* Do not prompt workers for deliberately different approaches. Diversity instructions
produced worse plans than plain repeated sampling.

## When not to

**Cemri et al. (UC Berkeley), "Why Do Multi-Agent LLM Systems Fail?" (MAST)** (NeurIPS 2025)
<https://arxiv.org/abs/2503.13657> · repo <https://github.com/multi-agent-systems-failure-taxonomy/MAST>
*Premise:* Failure taxonomy built from 1,600+ traces across seven multi-agent frameworks, with
reported failure rates from 41% to 86.7%.
*Taken:* Most failures are design and coordination faults rather than model limits, and targeted
fixes improved results without resolving them. This is why the skill puts specification, ownership,
and acceptance in the assignment packet rather than relying on the workers to coordinate.

**Yan (Cognition): "Don't Build Multi-Agents"** (June 2025)
<https://cognition.com/blog/dont-build-multi-agents>
*Premise:* Parallel workers holding partial context make conflicting implicit decisions that
collide when their work is merged.
*Taken:* Two rules. Share full traces rather than task summaries, and treat every action as
carrying a decision. This produced the packet line asking workers to preserve settled decisions and
report contradictory evidence instead of quietly changing course.

**Neubig (OpenHands): "Don't Sleep on Single-agent Systems"** (September 2024)
<https://www.openhands.dev/blog/dont-sleep-on-single-agent-systems>
*Premise:* One strong generalist agent with a full action space covers most of what people build
multi-agent systems for.
*Taken:* Keep coupled implementation with one owner. Handoffs lose context in the summary, and a
specialist that needs a tool outside its role cannot reach it. Multi-agent earns its place when a
worker holds privileged information or acts for a different principal.

**Tran, Kiela (Stanford): "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop
Reasoning Under Equal Thinking-Token Budgets"** (April 2026) <https://arxiv.org/abs/2604.02460>
*Premise:* Hold the thinking-token budget constant and compare a single agent against sequential,
parallel-role, debate, and ensemble teams.
*Taken:* Do not convene workers to supply more opinions. The single agent matched or beat every
team arrangement except at the smallest budget, and teams only pulled ahead when the single agent's
context was heavily degraded. The study caps budgets rather than actual spend and excludes
tool-based coding, so it argues against reasoning committees rather than for always raising effort.

**Kim, Gu, Park et al.: "Capable language models can outgrow the benefits of collaboration"**
Nature Machine Intelligence, July 2026 <https://www.nature.com/articles/s42256-026-01268-y>
*Premise:* 260 configurations across six agentic benchmarks and four architectures, testing when
adding agents helps.
*Taken:* Added agents stop helping once the single agent already succeeds at a task most of the
time. Treat this as a reason to start with one worker, not as a routing cutoff: the software and
terminal benchmarks used 20 tasks with wide confidence intervals, and the threshold is baseline
success on the task in front of you, not a model's published score.

## Context handling

**Xu, Zheng, Long, Cai, Wang: "Self-Manager: Parallel Agent Loop for Long-form Deep Research"**
<https://arxiv.org/html/2601.17879v1>
*Premise:* Concurrent threads with isolated contexts inside one agent framework, measured on
long-form research benchmarks.
*Taken:* Isolating a worker's context reduces information loss, at higher latency and tool-call
cost. Isolation is the benefit; running workers at the same time is a separate decision that this
work does not justify on its own.
