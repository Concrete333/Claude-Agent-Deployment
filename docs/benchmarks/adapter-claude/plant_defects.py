"""Plant the three known defects used in results-reviewers-2026-09-11.md into a copy of an adapter submission.

    python -B plant_defects.py <source checkout> <destination checkout>

The edits are exact string replacements; each must occur exactly once or the script stops. They were screened
so that they pass the 146-case visible checker and the F submission's tests; the held-out suite catches only the
second. Both teams know these defects, so they serve as a shared cross-model reviewer comparison, not as unseen
validation. Screening of the eleven candidates they were chosen from is in the results doc.
"""
import shutil
import sys
from pathlib import Path

EDITS = [
    ('imports/adapters/bank_csv.py',
     '                currency=row[columns["currency"]],',
     '                currency=row[columns["currency"]].strip(),',
     'contract: currency inputs have "no surrounding whitespace"'),
    ('imports/adapters/events_jsonl.py',
     '    return common.finish(records)',
     '    return records',
     'contract: duplicate normalized IDs among emitted records are errors; use common.finish'),
    ('imports/adapters/batch_json.py',
     '            if not isinstance(direction, str) or direction not in {"in", "out"}:',
     '            if not isinstance(direction, str) or direction.lower() not in {"in", "out"}:',
     'contract: direction "is exactly `in` or `out`" (and "OUT" is then booked positive)'),
]


def main(src, dst):
    src, dst = Path(src), Path(dst)
    if dst.exists():
        raise SystemExit(f'{dst} exists; refusing to overwrite')
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', 'SKILL.md'))
    for rel, old, new, clause in EDITS:
        p = dst / rel
        text = p.read_text(encoding='utf-8')
        if text.count(old) != 1:
            raise SystemExit(f'{rel}: expected exactly one occurrence of the target line, found {text.count(old)}; '
                             'this submission differs from the one the edits were written against')
        p.write_text(text.replace(old, new), encoding='utf-8', newline='')
        print(f'planted {rel}: {clause}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
