# Verifier diagnostic — 10 September 2026

**No Claude configuration tested caught the known error.** Three fresh read-only sessions each received the original task, all 50 discussions and the Codex trial's initial Luna answer (SHA-256 `8842b97a…`), with no hint that a defect existed. All three read every thread, ran the mechanical checker, reported full coverage and returned an empty findings list. That answer's ISSUE-040 explanation lists "version-stable sources must finish" as one of three pending options; the source's third option is the opposite, restart permitted when the source is version-stable (line 11 and line 17).

| Session | Configuration | Cost | Time | Turns | Output (thinking) | Findings | ISSUE-040 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| V1 | Opus 4.8 `max` | $2.2095 | 506 s | 58 | 43,761 (36,423) | none | missed |
| V2 | Fable 5.1 `high` | $1.5839 | 96 s | 56 | 9,037 (2,358) | none | missed |
| V3 | Opus 5 `low` | $0.5553 | 35 s | 5 | 2,327 (545) | none | missed |

Costs are provider-reported list-price equivalents, 5-minute caching confirmed, Haiku helper included (about $0.001 each). Total $4.35.

V1 and V2 both noticed the ISSUE-048 wording ("policy change" for "configuration change") and judged it non-material, which agrees with the audit. Both explicitly listed ISSUE-040 among the unresolved records they had checked. V3 finished in five turns by reading the files in parallel batches; its clean report cost a fifth of V1's and was no less accurate.

Combined with the Codex-side runs, the Luna ISSUE-040 inversion has now been missed by five reviewers across two vendors: Sol `high`, Opus 5 `low` twice, Opus 4.8 `max` and Fable 5.1 `high`. Only the Astra coordinator that originally requested corrections found it. Two readings are possible and the evidence cannot separate them: the inversion is below every reviewer's detection threshold, or reviewers judge it immaterial because the record is correctly `unresolved` and the operator action is unchanged. Either way, a reviewer's clean report on this class of error is not evidence that the class is absent.

## What this changes in the skill

The Verifier row moved from Opus 4.8 `max` to Opus 5 `low`, with Opus 4.8 `max` kept for user-named use or for claims about the world rather than about supplied sources. The reason is not that Opus 5 `low` is good at this; it is that Opus 4.8 `max` cost four times more, took fifteen times longer, and caught nothing more, so the earlier default had no measured support. The skill now says outright that a clean review report is weak evidence.

The audit's structural point stands and is now sharper: on read-dominated work, the only verification shown to catch a subtle fidelity error is a coordinator-grade full reread, and no cheaper Claude configuration has qualified. The D-arm saving of 20.6% was obtained by skipping that reread.

## Limits

One run per configuration, one target error, a prompt matched to the Codex reviewer assignment, tools richer than the Codex Opus review (Bash for the checker), synthetic corpus. Reviewers were told no finding count and not told a defect existed, so the null result is at least not an artefact of suggestion. Nothing here measures precision; no reviewer produced a false positive to score.

## Identities

- Input answer SHA-256: `8842b97ada5925862d1b88d5c934199286e3c237168c0096edd8560697610d1f` (byte-identical to the Codex `sol-review/task/answer.json`)
- Prompt SHA-256: `bacde3d4ebab2391923cefb0304dfb3fff7fea554c72cfb870ffd150c7503712`
- Sessions: V1 `12eadc4e-280e-4b7d-9834-d42af0c1d45f`, V2 `06a41d40-5813-4a7d-a491-c2f83f3d6919`, V3 `c498e9ad-9180-489d-a6c2-5ca64a3a3f06`
- Runner: `verify.py`; manifest and summary copied to `private/verify-manifest.json`, `private/verify-summary.json`
- No file in any checkout changed during review (hash check after each session)
