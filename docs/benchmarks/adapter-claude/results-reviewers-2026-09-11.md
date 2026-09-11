# Reviewer qualification on planted code defects: Fable 5.1 medium against Opus 5 high — 11 September 2026

**Opus 5 `high` caught all three planted defects for $0.32; Fable 5.1 `medium` caught all three for $0.80. On the clean submission Opus returned `correct` with two findings that Fable had accepted; checked afterwards against the Codex team's reference implementation, neither is confirmed: one is a reading of a clause the contract does not settle, the other a point where the reference itself departs from the contract's letter. Neither counts as a catch, and only the first counts as a false alarm; the second needs adjudication.** This is the first cheap reviewer to qualify on anything in these trials, and it did so on code, where the prose verifiers all failed. One run per cell.

| Submission | Reviewer | Decision | Planted defects found | Other findings | Cost | Time |
| --- | --- | --- | --- | --- | ---: | ---: |
| Clean F | Fable 5.1 `medium` (as run) | accept | — | field-size limit note | $1.068 | 93 s |
| Clean F | Fable 5.1 `medium` (trimmed tools) | accept | — | field-size limit; Unicode-whitespace line "defensible" | $0.982 | 105 s |
| Clean F | Opus 5 `high` | correct | — | 2 findings, both shared by the reference (see below) | **$0.572** | 126 s |
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

Both reproduce. But reproducing a behaviour is not the same as showing it breaks the contract, and the Codex team's reference implementation, the fixture's definition of correct, does the same in both cases:

| Input | F submission | Reference |
| --- | --- | --- |
| NBSP as root text outside memo | 1 record | 1 record |
| U+2028 as entry tail | 1 record | 1 record |
| NBSP as entry text before memo | 1 record | 1 record |
| NBSP-only line in JSONL | skipped | skipped |
| `"[" * 200000` to batch_json | RecursionError | RecursionError |

The contract says "non-whitespace text outside memo" is invalid and that "other Unicode whitespace within a memo is data", but never says which characters count as whitespace outside one; the reference reads it as Python does. So the first finding is a reading the contract does not settle, and Fable's "defensible" was the fixture-consistent call. The second is different: the contract's letter ("invalid documents ... must raise `ValueError`") is on the reviewer's side and the reference departs from it. Matching the reference does not make a finding wrong, since the reference can be wrong; it makes it a reference/contract discrepancy that someone has to adjudicate, and until then it cannot be scored as a catch or a false alarm. Neither finding should have produced a `correct` decision on its own; both are worth a line in the report. On the ledger the Codex team asked for: one false alarm on an unsettled clause, one discrepancy awaiting adjudication, and in arm G the unsettled one cost a $0.17 correction round.

The lesson is about the acceptance contract, not the model: a reviewer that finds a behaviour the contract does not settle should report it as a judgment call, not a defect, and the acceptance prompt now says so.

## Where the money went

| Reviewer, submission | Cache write | Cache read | Output (thinking) | Cost |
| --- | ---: | ---: | ---: | ---: |
| Fable medium, clean (trimmed) | 42,193 | 81,985 | 8,512 (3,716) | $0.974 |
| Opus high, clean | 40,395 | 122,907 | 10,007 (6,667) | $0.565 |
| Fable medium, planted | 37,831 | 81,893 | 6,028 | $0.796 |
| Opus high, planted | 25,093 | 86,412 | 4,435 | $0.311 |

Opus at `high` thinks more than Fable at `medium` (6.7 k thinking tokens against 3.7 k on the clean run) and still costs about half, because its token prices are lower. Haiku helper ($0.007) included in the table totals above.

## What this changes

With Opus 5 `high` as the acceptance reviewer, arm G measured $1.24 including a correction round; the reviewer's session cost has ranged $0.32 to $1.00 on this task depending on how much it chose to probe. It has caught every planted defect; on the clean submission it raised one false alarm on an unsettled clause and one reference/contract discrepancy still to be adjudicated.

The prose verifier diagnostic still stands: on the inverted-proposal task no reviewer at any price found the planted error, Opus 5 `low` included. The two results are not in conflict. Code defects here were reproducible by running the code, and both reviewers found them by writing probes; the prose defect required rereading fifty threads against a summary. Cheap review qualifies where the reviewer can execute the claim.

Skill change applied the same day: Opus 5 `high` is the default reviewer of delegated code with executable checks, Fable when the user asks for it or the claim cannot be executed; and a finding that rests on a reading the contract does not settle is a judgment call to record, not a defect to send back.

## Same day, second round: cheaper efforts, and defects the runner had not seen

Two follow-ups, both read-only acceptance sessions under the amended prompt (`correct` only where TASK.md settles the behaviour; the rest reported as judgment calls).

### Opus 5 at `medium` and `low` on the known mutant and the clean control

| Reviewer | Known mutant (3 planted) | Clean control | Output tokens (thinking) |
| --- | --- | --- | --- |
| Opus 5 `high` (earlier, old prompt) | 3/3, $0.32 | 2 findings sent back, $0.57 | 4,435 / 10,007 (6,667) |
| Opus 5 `medium` | 3/3, $0.26 | accept, judgment calls reported, $0.29 | 1,861 (352) / 4,051 (1,594) |
| Opus 5 `low` | 2/3, $0.16 (missed the stripped currency) | accept, $0.23 | 1,419 (206) / 2,559 (871) |

`medium` holds the catch rate at about 80% of `high`'s cost on the mutant and half on the clean run; `low` drops a defect. The clean-control comparison with `high` crosses the prompt change, so the "sent back" difference is partly the prompt: under the new wording both `medium` and `low` reported the same Unicode-whitespace observations as judgment calls and accepted.

### Sealed-key test: three defects unknown to the person running the reviews

To get closer to unseen defects without a new fixture, a separate agent planted three defects in a copy of the F submission, screened them against the 146-case checker and the worker's tests, wrote the key to a file, and reported back only the file's SHA-256 (`a0dee34b…`). The reviews ran before the key was opened; the hash matched afterwards. This is a procedural seal (the key sat on disk unread), not a cryptographic one, and the planting agent was told which defect kinds to avoid (the three known ones and the two disputed Unicode/recursion cases), so the defects are independent of the runner but not of the instructions.

The planted defects: `fixed_width` rejects a line of exactly 30 characters (`<=` for `<`; contract says "at least 30 characters", memo may be empty); `statement_xml` no longer checks `memo.tail`, so text after `</memo>` inside an entry is accepted; `batch_json` no longer checks that `items` is a list, so `"items": {}` returns `[]` and `"items": 5` raises `TypeError`. All three pass the 146 visible cases and the tests.

| Reviewer | Found | Sent back beyond the three | Cost | Time | Output (thinking) |
| --- | --- | --- | ---: | ---: | ---: |
| Opus 5 `high` | 3/3 | none; 3 judgment calls reported | $0.365 | 83 s | 6,523 (3,652) |
| Opus 5 `medium` | 3/3 | none; 2 judgment calls reported | $0.222 | 34 s | 2,387 (923) |
| Fable 5.1 `medium` | 3/3 | none; 2 judgment calls reported | $1.094 | 127 s | 10,543 (6,224) |

Every reviewer gave the line, a reproducing input and the fix for each defect, and each noticed on its own that `"items": 5` raises the wrong exception type. Opus `medium` did it in 34 seconds for 22 cents. The judgment calls reported were the same three each time (Unicode-only lines skipped, strict CSV quote handling, XML comments and PIs rejected), all matching the worker's own declarations or the contract's "outside the input domain" clause; none was sent back.

Across both mutants that is 6/6 for Opus 5 `high` and `medium` and 6/6 for Fable `medium`, at roughly $0.35, $0.25 and $0.95 per review. Opus 5 `medium` is now the cheapest configuration that has caught every planted defect, and the skill's Reviewer row should say so once a second task confirms it; this is still one fixture.

## Limits

One run per cell, on one fixture, with three defects I planted knowing what the checker covers. A reviewer that catches three planted defects is not proven on the next task; the defects were of a kind (a stripped field, a missing call, a case fold) that a careful read of a 1,500-character file finds. Neither reviewer was tested on a defect spread across files or one that needs the fixture data to see. The clean-run findings were not planted; checked against the reference neither is confirmed, so the clean submission stays a clean control pending adjudication of the RecursionError point; the reviewer's findings on it are one false alarm and one open discrepancy. Our three planted defects are now known to both teams and cannot serve as unseen defects again; they remain useful as a shared cross-vendor comparison. Opus did not re-run the checker; it trusted the runner's observed results, which is what the runner is for, but it means a wrong runner would not be caught by this reviewer.

## Identities

- Skill SHA-256: `272a647921b7e67818a68c0bfadef7f49711ae346a52addb33154b84fb21ac12`
- Sessions: Fable trimmed clean `6d60d569-a352-43e2-8e5a-4b0e52dc8f8a`; Opus clean `opus-clean-1`; Fable planted `mutant-fable-1`; Opus planted `mutant-opus-1` (receipts under `private/software/`, each with the session id)
- Planted checkout `%LOCALAPPDATA%\Temp\claude-adapters-software-1e8874b5\F-mutant`; the three edits and the eleven-candidate screen in `private/software/mutate.py`
