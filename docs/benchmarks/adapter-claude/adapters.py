"""Claude-native adapter-batch trial: A (Fable 5.1 medium solo, no skill) and D (skill + one forced Opus 5 low builder).

Reuses the Codex team's qualified version-two fixture (146 visible + 98 held-out cases, corrected
reference) from its private root; nothing in that root is modified. Usage:

  python -B -X utf8 adapters.py prepare      # copy source into fresh A/D checkouts, qualify reference via this grader
  python -B -X utf8 adapters.py run A|D      # one paid session each, once
  python -B -X utf8 adapters.py summarize    # grade both, cost table
"""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'local-fixture.json'
CODEX_FIXTURE = Path(r'C:\Users\cwbec\Codex-Agent-Deployment\docs\benchmarks\adapter-batch\selection-ablation\local-fixture.json')
SKILL_PATH = HERE.parent.parent.parent / 'SKILL.md'
spec = importlib.util.spec_from_file_location('prose_run', HERE.parent / 'prose-claude' / 'run.py')
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

ORCHESTRATOR = ('claude-fable-5-1', 'medium')
WORKER = ('claude-opus-5', 'low')
BUDGET_USD = 8.0
TIMEOUT_S = 1200
TOOLS = ['Read', 'Glob', 'Grep', 'Edit', 'Write', 'Bash', 'PowerShell']

TASK_PROMPT = (
    'Complete the task described in TASK.md in the current directory. Run `python -B check_contract.py` and any tests '
    'you add before finishing, and include the checker output verbatim in your final message. '
    'Do not use distill or any external service. Keep the final message short: changes, checks and results, unresolved work.'
)
FORCED_D = (
    ' Required execution: read SKILL.md in this directory first and follow it. Delegate the complete adapter batch to '
    'exactly one `builder` subagent (Opus 5, low effort); the worker owns implementation, local checks, added tests and '
    'corrections. Keep the assignment brief. Retain final acceptance yourself. Do not launch any other worker.'
)
BUILDER_PROMPT = (
    'You are a worker completing one bounded implementation assignment inside the current directory. '
    'Follow the assignment and TASK.md exactly. Do not edit protected files (TASK.md, check_contract.py, fixtures, common helpers, '
    'the example adapter, manifests). Finish by reporting: complete, partial or blocked; files changed; the verbatim output of '
    'the checks you ran; and unresolved risks. Do not weaken or rewrite any supplied check.'
)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree_hashes(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): sha_file(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts}


def grade(target, source, held_out, formats):
    """Same rules as the Codex external grader, run from this repository."""
    target, source = Path(target), Path(source)
    expected = json.loads((source / 'protected_hashes.json').read_text(encoding='utf-8'))
    expected['protected_hashes.json'] = sha_file(source / 'protected_hashes.json')
    changed = [n for n, d in expected.items() if not (target / n).is_file() or sha_file(target / n) != d]
    allowed = set(expected) | {f'imports/adapters/{f}.py' for f in formats} | {'imports/adapters/_shared.py'}
    unexpected = [p.relative_to(target).as_posix() for p in target.rglob('*.py')
                  if '__pycache__' not in p.parts and p.relative_to(target).as_posix() not in allowed
                  and not p.name.startswith('test_')]
    if changed or unexpected:
        return {'passed': False, 'changed_protected_files': changed, 'unexpected_python_files': unexpected}
    results = []
    for label, cases in (('public', source / 'fixtures.json'), ('held_out', held_out)):
        proc = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(source / 'check_contract.py'), str(target), str(cases)],
                              cwd=target, capture_output=True, text=True, encoding='utf-8', timeout=120)
        try:
            summary = json.loads(proc.stdout)
            summary.pop('failures', None) if summary.get('passed') == summary.get('cases') else None
        except ValueError:
            summary = {'stdout': proc.stdout[:2000], 'stderr': proc.stderr[:2000]}
        results.append({'check': label, 'exit_code': proc.returncode, 'summary': summary})
    tests = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-q'], cwd=target,
                           capture_output=True, text=True, encoding='utf-8', timeout=120)
    no_tests = tests.returncode == 5 and 'Ran 0 tests' in tests.stderr
    results.append({'check': 'added_tests', 'exit_code': tests.returncode, 'not_applicable': no_tests,
                    'stderr_tail': tests.stderr[-800:]})
    return {'passed': all(r['exit_code'] == 0 or r.get('not_applicable') for r in results), 'checks': results}


def prepare():
    if FIXTURE.exists():
        raise SystemExit('fixture exists; preserve it')
    codex = json.loads(CODEX_FIXTURE.read_text(encoding='utf-8'))
    src, ref, held = Path(codex['source']), Path(codex['reference']), Path(codex['root']) / 'held-out.json'
    root = Path(codex['root']).parent / ('claude-adapters-' + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8])
    root.mkdir()
    shutil.copy2(held, root / 'held-out.json')
    manifest = {'root': str(root), 'codex_source': str(src), 'codex_reference': str(ref), 'formats': codex['formats'],
                'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'orchestrator': ORCHESTRATOR, 'worker': WORKER,
                'budget_usd': BUDGET_USD, 'timeout_s': TIMEOUT_S, 'skill_sha256': sha_file(SKILL_PATH),
                'source_hashes': tree_hashes(src), 'held_out_sha256': sha_file(held), 'arms': {}}
    for arm in ('A', 'D'):
        d = root / arm
        shutil.copytree(src, d, ignore=shutil.ignore_patterns('__pycache__'))
        if arm == 'D':
            shutil.copy2(SKILL_PATH, d / 'SKILL.md')
        manifest['arms'][arm] = {'path': str(d), 'files': tree_hashes(d)}
    qual = grade(ref, src, root / 'held-out.json', codex['formats'])
    manifest['reference_qualification'] = qual
    stub = grade(root / 'A', src, root / 'held-out.json', codex['formats'])
    manifest['stub_rejection'] = {'passed': stub['passed']}
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    FIXTURE.write_text(json.dumps({'root': str(root)}, indent=2), encoding='utf-8')
    print(json.dumps({'root': str(root), 'reference_passed': qual['passed'], 'stub_passed': stub['passed'],
                      'reference_checks': [(c['check'], c.get('summary', {}).get('passed'), c.get('summary', {}).get('cases')) for c in qual.get('checks', [])]}, indent=2))
    assert qual['passed'] and not stub['passed'], 'qualification failed'


def agents_json():
    return json.dumps({'builder': {'description': 'Bounded implementer: owns the six adapters, added tests and corrections.',
                                   'prompt': BUILDER_PROMPT, 'model': WORKER[0], 'effort': WORKER[1], 'tools': TOOLS}})


def run(arm):
    root = Path(json.loads(FIXTURE.read_text(encoding='utf-8'))['root'])
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    cwd = Path(manifest['arms'][arm]['path'])
    receipt = root / f'receipt-{arm}.json'
    if receipt.exists():
        raise SystemExit(f'{receipt} exists; refusing a second paid run for arm {arm}')
    if tree_hashes(cwd) != manifest['arms'][arm]['files']:
        raise SystemExit('checkout changed since prepare')
    if arm == 'A':
        args = harness.base_args(*ORCHESTRATOR, BUDGET_USD, ['Agent', 'Task'], TOOLS)
        prompt = TASK_PROMPT
    else:
        args = harness.base_args(*ORCHESTRATOR, BUDGET_USD, [], TOOLS + ['Agent']) + ['--agents', agents_json()]
        prompt = TASK_PROMPT + FORCED_D
    print('launching', arm, 'in', cwd)
    r = harness.launch(cwd, args, prompt, receipt, TIMEOUT_S)
    d = r['result'] or {}
    print(json.dumps({'duration_s': r['duration_s'], 'timed_out': r['timed_out'], 'returncode': r['returncode'],
                      'subtype': d.get('subtype'), 'is_error': d.get('is_error'), 'total_cost_usd': d.get('total_cost_usd'),
                      'session_id': d.get('session_id'), 'num_turns': d.get('num_turns'), 'modelUsage': d.get('modelUsage')}, indent=2))
    print('RESULT:', (d.get('result') or '')[:3000])
    if r['stderr']:
        print('STDERR:', r['stderr'][:2000])


def summarize():
    root = Path(json.loads(FIXTURE.read_text(encoding='utf-8'))['root'])
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    out = {}
    for arm in ('A', 'D'):
        rp = root / f'receipt-{arm}.json'
        if not rp.exists():
            out[arm] = 'no receipt'
            continue
        r = json.loads(rp.read_text(encoding='utf-8'))
        d = r['result'] or {}
        cwd = Path(manifest['arms'][arm]['path'])
        out[arm] = {'duration_s': r['duration_s'], 'timed_out': r['timed_out'], 'subtype': d.get('subtype'),
                    'total_cost_usd': d.get('total_cost_usd'), 'usage': d.get('usage'), 'modelUsage': d.get('modelUsage'),
                    'session_id': d.get('session_id'), 'num_turns': d.get('num_turns'),
                    'grade': grade(cwd, manifest['codex_source'], root / 'held-out.json', manifest['formats']),
                    'owned_file_hashes': {k: v for k, v in tree_hashes(cwd).items() if k.startswith('imports/adapters/') or k.startswith('test_')}}
    (root / 'summary.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    for arm, e in out.items():
        if isinstance(e, dict):
            print(arm, 'cost', e['total_cost_usd'], 'turns', e['num_turns'], 'dur', round(e['duration_s']), 'passed', e['grade']['passed'],
                  [(c['check'], c.get('summary', {}).get('passed'), c.get('summary', {}).get('cases'), c.get('exit_code')) for c in e['grade'].get('checks', [])],
                  e['grade'].get('changed_protected_files'), e['grade'].get('unexpected_python_files'))
            for m, u in e['modelUsage'].items():
                print('   ', m, {k: u[k] for k in ('inputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens', 'thinkingTokens', 'costUSD')})
        else:
            print(arm, e)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    {'prepare': prepare, 'summarize': summarize}.get(mode, lambda: run(sys.argv[2]) if mode == 'run' else print(__doc__))()
