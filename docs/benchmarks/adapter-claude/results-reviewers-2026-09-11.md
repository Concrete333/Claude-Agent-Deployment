# Reviewer qualification on planted code defects: Fable 5.1 medium against Opus 5 high — 11 September 2026

**Opus 5 `high` caught all three planted defects for $0.32; Fable 5.1 `medium` caught all three for $0.80. On the clean submission Opus also found two real contract violations that Fable had accepted twice.** This is the first cheap reviewer to qualify on anything in these trials, and it did so on code, where the prose verifiers all failed. One run per cell.

| Submission | Reviewer | Decision | Planted defects found | Other findings | Cost | Time |
| --- | --- | --- | --- | --- | ---: | ---: |
| Clean F | Fable 5.1 `medium` (as run) | accept | — | field-size limit note | $1.068 | 93 s |
| Clean F | Fable 5.1 `medium` (trimmed tools) | accept | — | field-size limit; Unicode-whitespace line "defensible" | $0.982 | 105 s |
| Clean F | Opus 5 `high` | correct | — | XML non-XML whitespace accepted; RecursionError escapes | **$0.572** | 126 s |
| Planted | Fable 5.1 `medium` | correct | 3 / 3 | — | $0.803 | 82 s |
| Planted | Opus 5 `high` | correct | 3 / 3 | — | **$0.319** | 56 s |

Same acceptance session as arm F (`software.py reaccept`): same prompt, the worker's real handoff presented unchanged, runner checks re-run on the checkout under review, tools limited to Read, Glob, Grep, Bash and PowerShell, SKILL.md on disk. The reviewer was not told anything had been planted.

## The planted defects

Three edits to the accepted F submission, chosen from eleven candidates by screening each one alone: it had to pass the 146-case visible checker and the worker's eight tests unchanged, and demonstrably violate a sentence of TASK.md. Eight candidates were caught by the checker or the tests and discarded.

1. `bank_csv.py`: `currency=row[...].strip()`. The contract says currency has no surrounding whitespace; `" usd "` is now accepted.
2. `events_jsonl.py`: `return records` instead of `return common.finish(records)`. Duplicate posted IDs are no longer rejected, and the contract's instruction to use `common.finish` is broken.
3. `batch_json.py`: `direction.lower() not in {"in", "out"}`. `"OUT"` is accepted, and because the sign flip still tests `direction == "out"`, it is booked positive.

For the record, the 98 held-out cases catch only the second (`events_jsonl/duplicate-normalized-id`); the first and third pass every frozen check in the fixture. Source review was the only thing standing between them and acceptance.

## What each reviewer did

Both reviewers read every delivered file and the helpers, both wrote their own probe scripts, and both reported all three defects with a reproduction and a fix. Both noticed the sign inversion behind the third. Fable re-ran the checker and tests itself and grepped the fixtures to confirm nothing covered the cases; Opus took the runner's observed check results as given and spent its turns on probes instead. Fable's report asked for regression tests; Opus's ranked the sign inversion as the most serious.

On the clean submission Opus returned `correct` with two findings, both reproduced afterwards:

- `statement_xml.py` tests "whitespace only" with `str.strip()`, which treats NBSP, U+2028 and U+3000 as whitespace. XML whitespace is space, tab, CR and LF, so non-whitespace text outside a memo made of those characters is silently accepted and dropped. The contract forbids silently skipping malformed data. Fable's trimmed run had noticed the same pattern in `events_jsonl` and called it defensible.
- `events_jsonl` and `batch_json` let `RecursionError` escape on `"[" * 200000`. The contract says invalid documents must raise `ValueError`. `common.strict_json_loads` is protected, so the fix belongs in the adapters.

Both are real contract violations, the second unambiguously. Fable accepted the same code twice. Whether they are worth a $0.11 Luna correction round is a judgment; that the reviewer found them at half Fable's cost is the point.

## Where the money went

| Reviewer, submission | Cache write | Cache read | Output (thinking) | Cost |
| --- | ---: | ---: | ---: | ---: |
| Fable medium, clean (trimmed) | 42,193 | 81,985 | 8,512 (3,716) | $0.974 |
| Opus high, clean | 40,395 | 122,907 | 10,007 (6,667) | $0.565 |
| Fable medium, planted | 37,831 | 81,893 | 6,028 | $0.796 |
| Opus high, planted | 25,093 | 86,412 | 4,435 | $0.311 |

Opus at `high` thinks more than Fable at `medium` (6.7 k thinking tokens against 3.7 k on the clean run) and still costs about half, because its token prices are lower. Haiku helper ($0.007) included in the table totals above.

## What this changes

With Opus 5 `high` as the acceptance reviewer the F workflow would cost about $0.43 for a clean pass ($0.32 to $0.57 review plus $0.11 worker), or about $0.55 to $0.70 with one correction round. Against solo Fable at $1.90 that is a 63% to 77% saving, with a reviewer that has now caught every planted defect and two real ones.

The prose verifier diagnostic still stands: on the inverted-proposal task no reviewer at any price found the planted error, Opus 5 `low` included. The two results are not in conflict. Code defects here were reproducible by running the code, and both reviewers found them by writing probes; the prose defect required rereading fifty threads against a summary. Cheap review qualifies where the reviewer can execute the claim.

Suggested skill change, not yet applied: when acceptance is a separate session from orchestration, name Opus 5 `high` as the default reviewer of delegated code, with Fable when the user asks for it; keep Fable-level review for claims the reviewer cannot execute.

## Limits

One run per cell, on one fixture, with three defects I planted knowing what the checker covers. A reviewer that catches three planted defects is not proven on the next task; the defects were of a kind (a stripped field, a missing call, a case fold) that a careful read of a 1,500-character file finds. Neither reviewer was tested on a defect spread across files or one that needs the fixture data to see. The clean-run findings were not planted and were confirmed after the fact, so they count as real, but their severity is a judgment. Opus did not re-run the checker; it trusted the runner's observed results, which is what the runner is for, but it means a wrong runner would not be caught by this reviewer.

## Identities

- Skill SHA-256: `272a647921b7e67818a68c0bfadef7f49711ae346a52addb33154b84fb21ac12`
- Sessions: Fable trimmed clean `6d60d569-a352-43e2-8e5a-4b0e52dc8f8a`; Opus clean `opus-clean-1`; Fable planted `mutant-fable-1`; Opus planted `mutant-opus-1` (receipts under `private/software/`, each with the session id)
- Planted checkout `%LOCALAPPDATA%\Temp\claude-adapters-software-1e8874b5\F-mutant`; the three edits and the eleven-candidate screen in `private/software/mutate.py`
