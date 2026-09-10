# Audit of the Codex delegation experiments, and what to carry into the Claude skill

Prepared 10 September 2026 from the [Codex handoff](https://github.com/Concrete333/Codex-Agent-Deployment) (`docs/claude-audit-and-benchmark-handoff-2026-09-10.md`), the Codex working tree at that time, and the Claude skill at commit `231fc6b`. This is maintenance material. Ordinary skill use should not load it. No paid runs were made; no skill file was edited. The companion [trial plan](claude-trial-plan-2026-09-10.md) sets out the next measured step.

## Short version

The Codex team's narrow conclusion holds: across every comparison they ran, delegation has not produced a cheaper accepted result. Their evidence is careful about what it does not show, and most of the cautions in the handoff are warranted. Three things deserve correction or sharper statement before the Claude skill borrows from them.

First, the three "comparison findings" used to score the Sol and Opus reviewers are not equally weighty, and one of them is doubtful. ISSUE-040 is a real meaning reversal. ISSUE-045 is a completeness nit. ISSUE-048, the one Sol caught, uses the same wording as the author's own answer key. Both reviewers missing 040 is the result that matters; the "1 of 3" and "0 of 3" tallies overstate the spread.

Second, the reason delegation lost on the prose task is arithmetic, not orchestration overhead. Solo Astra spent $0.48 of $1.30 on output. Handing the writing to Luna can save at most that much. Any verifier that rereads the corpus at coordinator prices costs about $0.80. Delegating the writing while keeping full-read verification cannot win on a read-dominated task, whatever the worker costs. It can only win if verification is delegated too, and the two cheap reviewers tested did not preserve accuracy.

Third, the frozen grader's "valid citation" check is weaker than the reports imply. A one-word quote of the record's own ID, cited against the whole file, passes all 50 records. Automated 50/50 citation scores should be read as "no fabricated text", not "supported claims".

The Claude skill has the same structural exposure: its Scout role (Opus 5 Low) is the configuration the Opus builder diagnostic tested, and its Verifier role (Opus 4.8 Max) is untested on exactly the task a verifier performs. The proposed edits below are small. The trial plan tests the verifier question first, because it is cheap and decides whether delegation can pay on this task class at all.

## Answers to the seven audit questions

### 1. Acceptance: are the semantic findings valid and proportionate?

I read the five contested source discussions in `cases.json` against the findings. The Luna initial answer itself is private, so I assessed the findings as described, not the answer text.

| Finding | Source check | Severity under the contract |
|---|---|---|
| ISSUE-040, restart described as a requirement to finish | Line 11 of the source: "Restarting a batch is safe if the remote source keeps stable object versions." Describing that proposal as requiring completion reverses it. | Material explanation error. It does not change the operator action, because the record is correctly `unresolved`, but the contract requires faithful explanations and this one misstates a live proposal. Valid. |
| ISSUE-045, procedure and deadline not explicit | Source line 9 gives the condition and "before completing the upgrade"; line 11 gives the re-enrollment steps. | Completeness. The contract asks for "the precise action and affected scope"; the deadline is arguably scope, the steps are not. Minor. Treat as advisory, not blocking. |
| ISSUE-048, "policy change" instead of "configuration change" | Source line 9 says "after its final 3.x configuration change". But the author's own `rationale` field in `cases.json` says "after the last 3.x policy change". Line 11 frames the practical risk as "later policy edits". | Doubtful. The export records policy assignments, so a non-policy configuration change would not alter its contents. If this is a defect, the answer key has it too. At most a wording preference. |
| ISSUE-016 in A and C, "synchronous or failover replicas" | That phrase is the 13 May decisive quote; the 5 June clarification says eligibility for failover decides, not transport. A synchronous replica that is not failover-eligible is the only case where the answers are overbroad, and the source never mentions one. | Same class as 048: precision of wording, not action or scope error. Valid but minor. |
| ISSUE-015 in the Opus builder answer, opt-in deadline attached to the wrong subject | Source line 11: the receiver must accept v4 "before Harbor sends the next event"; the opt-in is the operator's earlier choice. | Real but minor; the operator action and its timing are still recoverable from the cited sentence. |

Consequences. The A and C answers needed one minor correction; the Luna initial answer had one material error and two minor ones; the Opus builder answer had five mechanical quote failures and one minor wording issue. Ranking by what matters, only Luna's initial ISSUE-040 was a meaning error, and Luna's own correction pass fixed it for $0.015. The evaluator's severity ordering in the reports is right; the summary tables flatten it.

No additional errors were found in the five records I checked. I did not re-review all 150 explanations; that would repeat unblinded model review with the same limits the reports already state.

### 2. Comparison boundary: which costs end with accepted work?

Only D ($1.66) ends with an answer the evaluator accepted. A and C ($1.30, $1.33) each need one minor wording correction that was never requested or priced. The gap is $0.36. A single-record correction to A, requested the way D's corrections were requested, would cost a fraction of that (D's Luna correction pass cost $0.015; an Astra correction turn on one record would be perhaps $0.05 to $0.10 given its cached context). So the accepted-result gap is smaller than reported but is very unlikely to close. The handoff's phrasing, "not a comparison of equally accepted final results", is correct and should stay.

Every other figure in the handoff is an attempt or a review-only cost, and the reports say so. The cattrs C figure is a lower bound from a timed-out run. The Sol and Opus review costs exclude the coordinator work that would surround them.

### 3. Verification ownership: can one substantive owner avoid duplicate review without accepting incomplete reviews?

Not on the evidence. The dilemma is exact: if the coordinator is the substantive owner, it rereads the corpus and the D result follows; if a cheaper reviewer is the owner, both tested candidates read every file, reported full coverage, and missed the meaning reversal. Coverage evidence did not predict catch rate. The current Codex policy sentence, "that owner checks original evidence; the coordinator checks the resulting evidence, gaps and unresolved findings without automatically repeating the full review", is a reasonable design, but it was written before the diagnostics and is not validated by them. The honest operational statement is narrower: for deliverables whose acceptance requires reading the sources, a cheaper verification owner is a candidate to qualify per task class, and until qualified the coordinator's own full check is the only method shown to catch the errors observed.

The Claude skill should say that plainly. Its Verifier role is defined for "a summary against its sources", which is this task, and it has no evidence yet.

### 4. Checker independence: can a small trusted checker enforce mechanical requirements without exposing gold?

Yes for the mechanics that failed, with caveats about what "valid" means. I rebuilt an author reference from `cases.json` (all 50 records, decisive quotes cited by line) and ran the frozen `grade.py` against it and eight new mutants.

| Mutant | Frozen grader |
|---|---|
| Ellipsis inserted into one quote (the Opus builder failure) | Rejected |
| Quote budget over 160 words | Rejected |
| Duplicate ID | Rejected |
| Extra record key | Rejected |
| 81-word explanation | Rejected |
| Every record cites only its own ID as a one-word quote from the header line | **Passed**, 50/50 valid citations, 0/50 anchors |
| Correct quote cited against the whole file (lines 1 to N) | **Passed** |
| Two-word explanation | **Passed** |

The grader is sound as a fabrication and schema gate and would have caught the Opus builder's quotes. It does not enforce that citations support anything. For the Claude trial, the participant-visible checker should add contract-derived tightness rules that need no gold: a minimum quote length, a maximum cited line span (or the quote must cover most of the cited span), a minimum explanation length, and rejection of ellipsis and bracketed insertions. Freeze those assertions and put the checker in every arm. Keep `expected_disposition`, `decisive_evidence` and `rationale` out of it entirely; only the external grader sees those.

Workers must not be able to weaken it. The Opus builder did not weaken anything; it wrote its own checker with a looser rule and reported success. The fix is to supply the checker and require its unmodified output in the return, with a hash the coordinator verifies.

### 5. Context and cost: do the receipts support the claims?

The published decompositions reconcile. A's $1.30 splits into $0.478 output, $0.464 uncached input, $0.358 cached input; D's parent $1.56 splits into $0.145, $0.970, $0.446. The Opus figures reconcile to Opus 5 list prices of $5 uncached, $6.25 cache write, $0.50 cache read and $25 output per million, with the Haiku helper added. Two points for the Claude trial follow from the Opus receipts rather than from any Codex claim.

Cache writes dominated short Claude sessions. The Opus reviewer's 69-second run spent 67% of its cost on cache creation. Five-minute caching is right for a worker that will re-enter; for a single-pass reader it is mostly a tax. Record the TTL and the write share per session.

Effective effort was requested, not verified, for Claude workers. The wrapper says so. Native Claude Code subagents have the same gap unless the transcript records it. Treat this as a preflight item, not an assumption.

### 6. Experimental validity

The handoff's list is complete and I would add one item. The skill arm in every comparison also changes tool exposure and inherited authorization text, so "skill overhead" and "delegation tooling overhead" are confounded; a B arm (tools, no skill) is the only way to separate them, and the prose task never had one. The trial plan includes B.

Two of the handoff's cautions deserve more weight than they get. One run per cell means the 2% A-versus-C difference on the prose task is inside sampling noise; only the 25% to 110% differences are large enough to read. And the corpus is regular: 47 of 50 author anchors were reproduced verbatim by two independent solo runs, which suggests the decisive sentences are conspicuous. A held-out task with less conspicuous evidence is needed before any general claim.

### 7. Operational bloat

The revision-ab runs put the skill arm 19% to 31% above solo on three small tasks where the skill correctly chose solo, with tool exposure confounded. The Codex core is 9 KB; the Claude `SKILL.md` is 15 KB and loads whole. Claude Code has no conditional loading inside one skill file, so the mechanism is a short `SKILL.md` that ends with "if staying local, stop here", and role, packet, fan-out, escalation and waiting guidance moved to `references/`. That is a measurable change and should be a separate condition, not folded into the first trial.

## Where the Codex mechanisms fit the Claude skill

Worth adopting: the local-or-delegate gate that requires naming the work the coordinator will stop doing and a check that does not repeat it; the explicit statement that a cheap worker plus full coordinator reread cannot save money on read-dominated work; the frozen-checker-in-every-arm rule; the receipt discipline (separate uncached, cache write, cache read and output buckets, helper models included, effort recorded as requested unless verified).

Not to adopt: the GPT worker list, the Luna one-failure rule, and any effort values. The Claude skill's model table stands or falls on Claude evidence.

Already present and consistent with the evidence: the Claude skill's insistence on confirming effective effort, its refusal to add a standing review stage, and its "acceptance criteria are fixed for the worker" rule, which is exactly the rule the Opus builder's self-written checker broke.

## Proposed edits to the Claude `SKILL.md`

Three edits, all short. Rationale is in this document; the skill text should carry none of it. These are proposals for a new measured condition; the current file is the frozen baseline for arm C.

Edit 1, in "Dispatch", after "Volume of tool calls alone is not a reason." Add:

> Before delegating, name the work you will stop doing and the check you will use that does not redo it. If acceptance requires you to read the same sources the worker reads, delegating the writing does not reduce cost; keep it local, or delegate verification only where a checker adequate for that kind of error has already been shown.

Edit 2, in "Verifier", replace the paragraph starting "Opus 4.8 at `max`" with:

> Opus 4.8 at `max`, provisionally. Use it when a confident wrong statement is the expensive failure: factual claims, citations, API and version assertions, or a summary against its sources. Its catch rate on source-fidelity errors is unmeasured; do not treat its report of full coverage as evidence of correctness. Where a mechanical checker can enforce part of the contract, run it first and give the Verifier only what remains.

Edit 3, in "Review and acceptance", after "Mechanical edits with strong objective checks need no extra reviewer." Add:

> Supply the checker; do not accept one the worker wrote. A worker that reports passing its own check has reported completion, not acceptance.

A fourth change, the short-entrypoint restructure described under question 7, is recommended but is a separate condition with its own measurement.

## What this audit did not do

It did not re-review every explanation in the four saved answers, run any model, or verify the private receipts beyond the published decompositions. It read the five contested sources, rebuilt the reference, and probed the grader. The Codex installed-skill synchronization mentioned in the handoff was not checked.
