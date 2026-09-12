"""Arm F: software-managed dispatch. A script runs one Luna Max worker via `codex exec`, runs the declared checks,
and hands a compact packet to a single Fable 5.1 acceptance session. The orchestrator never waits, so its prompt
cache is written once. At most one correction round (Luna resume + one more acceptance turn), no automatic retries.

The codex exec invocation and config overrides follow the Codex team's deployment_runner.py (uncommitted draft,
11 September 2026), which we could not reuse whole because it is mid-change. Usage:

  python -B -X utf8 software.py prepare
  python -B -X utf8 software.py run          # one paid workflow, once
  python -B -X utf8 software.py summarize
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANT = os.environ.get('SOFTWARE_VARIANT', '')  # '' = arm F root; e.g. 'opus' = arm G root (Opus 5 high acceptance)
FIXTURE = HERE / ('local-fixture-software' + (f'-{VARIANT}' if VARIANT else '') + '.json')
spec = importlib.util.spec_from_file_location('adapters', HERE / 'adapters.py')
adapters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapters)
harness = adapters.harness
spec2 = importlib.util.spec_from_file_location('luna', HERE / 'luna.py')
luna = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(luna)

WORKER = ('gpt-5.6-luna', 'max')
ORCH = adapters.ORCHESTRATOR
# Acceptance reviewer. Opus 5 high qualified on planted defects (results-reviewers-2026-09-11); Fable was arm F's.
REVIEWER = tuple(os.environ.get('SOFTWARE_REVIEWER', 'claude-opus-5,high').split(','))
WORKER_TIMEOUT = 1500
ACCEPT_BUDGET = 4.0
FORMATS = None

SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['status', 'summary', 'files_changed', 'checks_run', 'unresolved_risks', 'judgment_calls'],
          'properties': {'status': {'type': 'string', 'enum': ['complete', 'partial', 'blocked']}, 'summary': {'type': 'string'},
                         'files_changed': {'type': 'array', 'items': {'type': 'string'}}, 'checks_run': {'type': 'string'},
                         'unresolved_risks': {'type': 'array', 'items': {'type': 'string'}},
                         'judgment_calls': {'type': 'array', 'items': {'type': 'string'}}}}

WORKER_PROMPT = (
    'Complete the task described in TASK.md in this directory. Own the implementation of the six adapter modules, any '
    '`imports/adapters/_shared.py`, added `test_*.py` files, local checks and your own corrections. Do not edit protected '
    'files (TASK.md, check_contract.py, fixtures.json, boundaries_visible.py, protected_hashes.json, imports/__init__.py, '
    'imports/common.py, imports/adapters/__init__.py, imports/adapters/canonical_json.py). Run `python -B check_contract.py` '
    'and your tests before finishing. Do not delegate or leave background commands running. Return JSON matching the '
    'supplied schema: status, a concise summary, files changed, the checks you ran with their results, unresolved risks, '
    'and judgment calls you made where the contract was ambiguous. Completion is your report, not acceptance.'
)
ACCEPT_SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['decision', 'findings', 'what_you_inspected'],
                 'properties': {'decision': {'type': 'string', 'enum': ['accept', 'correct', 'reject']},
                                'findings': {'type': 'array', 'items': {'type': 'string'}},
                                'what_you_inspected': {'type': 'string'}}}


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def codex_bin():
    found = shutil.which('codex.exe') or shutil.which('codex')
    # prefer the native exe bundled with the npm package, as the Codex runner requires
    npm = Path(os.environ.get('APPDATA', '')) / 'npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor'
    exes = list(npm.rglob('codex.exe')) if npm.exists() else []
    return str(exes[0]) if exes else found


def prepare():
    if FIXTURE.exists():
        raise SystemExit('fixture exists; preserve it')
    codex = json.loads(adapters.CODEX_FIXTURE.read_text(encoding='utf-8'))
    src, ref, held = Path(codex['source']), Path(codex['reference']), Path(codex['root']) / 'held-out.json'
    root = Path(codex['root']).parent / ('claude-adapters-software-' + (f'{VARIANT}-' if VARIANT else '') + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8])
    root.mkdir()
    shutil.copy2(held, root / 'held-out.json')
    checkout = root / 'F'
    shutil.copytree(src, checkout, ignore=shutil.ignore_patterns('__pycache__'))
    (root / 'handoff-schema.json').write_text(json.dumps(SCHEMA, indent=2), encoding='utf-8')
    manifest = {'root': str(root), 'checkout': str(checkout), 'codex_source': str(src), 'formats': codex['formats'],
                'codex_bin': codex_bin(), 'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'orchestrator': ORCH, 'worker': WORKER, 'reviewer': REVIEWER,
                'skill_sha256': sha_file(adapters.SKILL_PATH), 'files': adapters.tree_hashes(checkout),
                'protected': json.loads((src / 'protected_hashes.json').read_text(encoding='utf-8'))}
    qual = adapters.grade(ref, src, root / 'held-out.json', codex['formats'])
    stub = adapters.grade(checkout, src, root / 'held-out.json', codex['formats'])
    manifest['reference_qualification'], manifest['stub_rejection'] = qual['passed'], not stub['passed']
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    FIXTURE.write_text(json.dumps({'root': str(root)}, indent=2), encoding='utf-8')
    v = subprocess.run([manifest['codex_bin'], '--version'], capture_output=True, text=True)
    s = subprocess.run([manifest['codex_bin'], 'login', 'status'], capture_output=True, text=True)
    print(json.dumps({'root': str(root), 'codex_bin': manifest['codex_bin'], 'version': v.stdout.strip(),
                      'login': (s.stdout + s.stderr).strip(), 'reference': qual['passed'], 'stub_rejected': not stub['passed']}, indent=2))
    assert qual['passed'] and not stub['passed']


def load():
    root = Path(json.loads(FIXTURE.read_text(encoding='utf-8'))['root'])
    return root, json.loads((root / 'manifest.json').read_text(encoding='utf-8'))


def codex_args(manifest, out_dir, resume=None):
    args = [manifest['codex_bin'], 'exec']
    if resume:
        args += ['resume', resume]
    args += ['--ignore-user-config', '--ignore-rules', '--strict-config', '--skip-git-repo-check', '--json', '--color', 'never',
             '--sandbox', 'workspace-write', '--model', WORKER[0], '--cd', manifest['checkout'],
             '--output-schema', str(Path(manifest['root']) / 'handoff-schema.json'),
             '--output-last-message', str(out_dir / 'handoff.json')]
    config = {'model_provider': 'openai', 'model_reasoning_effort': WORKER[1], 'approval_policy': 'never',
              'agents.enabled': False, 'features.multi_agent': False, 'features.multi_agent_v2.enabled': False,
              'features.plugins': False, 'features.remote_plugin': False, 'features.memories': False,
              'memories.use_memories': False, 'memories.generate_memories': False, 'web_search': 'disabled',
              'mcp_servers': {}, 'windows.sandbox': 'elevated', 'project_doc_max_bytes': 0}
    for k, v in config.items():
        args += ['-c', f'{k}={json.dumps(v)}']
    return args + ['-']


def run_worker(manifest, out_dir, prompt, resume=None):
    out_dir.mkdir(exist_ok=True)
    started = time.time()
    with (out_dir / 'events.jsonl').open('w', encoding='utf-8') as ev, (out_dir / 'stderr.log').open('w', encoding='utf-8') as er:
        try:
            proc = subprocess.run(codex_args(manifest, out_dir, resume), input=prompt, stdout=ev, stderr=er, text=True,
                                  encoding='utf-8', cwd=manifest['checkout'], timeout=WORKER_TIMEOUT)
            rc, timed_out = proc.returncode, False
        except subprocess.TimeoutExpired:
            rc, timed_out = None, True
    thread_id = None
    for line in (out_dir / 'events.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get('type') == 'thread.started':
            thread_id = e.get('thread_id')
    handoff = None
    if (out_dir / 'handoff.json').exists():
        try:
            handoff = json.loads((out_dir / 'handoff.json').read_text(encoding='utf-8'))
        except ValueError:
            handoff = {'raw': (out_dir / 'handoff.json').read_text(encoding='utf-8')[:2000]}
    return {'returncode': rc, 'timed_out': timed_out, 'duration_s': time.time() - started, 'thread_id': thread_id, 'handoff': handoff}


def run_checks(manifest):
    cwd = manifest['checkout']
    checker = subprocess.run([sys.executable, '-B', '-X', 'utf8', 'check_contract.py'], cwd=cwd, capture_output=True, text=True, timeout=120)
    tests = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-q'], cwd=cwd, capture_output=True, text=True, timeout=120)
    changed = [n for n, d in manifest['protected'].items() if sha_file(Path(cwd) / n) != d]
    return {'check_contract': checker.stdout.strip()[-1500:] or checker.stderr[-800:], 'unittest': tests.stderr.strip()[-800:],
            'protected_files_changed': changed}


def diff_text(manifest):
    cwd = Path(manifest['checkout'])
    parts = []
    for rel in sorted(k for k in adapters.tree_hashes(cwd) if k.startswith('imports/adapters/') or k.startswith('test_')):
        if rel in manifest['files'] and manifest['files'][rel] == sha_file(cwd / rel):
            continue
        parts.append(f'===== {rel} =====\n' + (cwd / rel).read_text(encoding='utf-8'))
    return '\n'.join(parts)


def acceptance_prompt(packet):
    return (
        'You are the orchestrator accepting delegated work. Read SKILL.md in this directory and follow its review and '
        'acceptance guidance. A software runner dispatched one Luna Max worker to complete TASK.md, then ran the declared '
        'checks. Everything you need is below; the files are also on disk if you want to read them or run anything. '
        'Decide: accept, correct (give the exact findings the worker must fix), or reject. Do not fix code yourself. '
        'Return correct only for findings where TASK.md settles the behaviour and the code contradicts it; a behaviour '
        'that turns on a reading TASK.md does not fix is a judgment call: report it in findings and do not send it back. '
        'Return JSON matching the schema: decision, findings, what_you_inspected.\n\n'
        '## Worker assignment\n' + WORKER_PROMPT + '\n\n## Worker handoff (JSON)\n' + json.dumps(packet['handoff'], indent=1) +
        '\n\n## Runner checks (observed, not worker-reported)\n' + json.dumps(packet['checks'], indent=1) +
        '\n\n## Delivered files\n' + packet['diff']
    )


ACCEPT_TOOLS = ['Read', 'Glob', 'Grep', 'Bash', 'PowerShell']  # what an acceptance session may do: read, search, run. Not edit.


def accept(manifest, packet, out_dir, resume_session=None, name='accept', reviewer=None):
    args = harness.base_args(*(reviewer or REVIEWER), ACCEPT_BUDGET, ['Agent', 'Task', 'Edit', 'Write'], ACCEPT_TOOLS, tools=ACCEPT_TOOLS)
    args += ['--json-schema', json.dumps(ACCEPT_SCHEMA)]
    if resume_session:
        args += ['--resume', resume_session]
    prompt = acceptance_prompt(packet) if not resume_session else (
        'The worker has returned a correction. Updated runner checks and delivered files follow. Decide again: accept, correct, or reject.\n\n'
        '## Worker handoff (JSON)\n' + json.dumps(packet['handoff'], indent=1) + '\n\n## Runner checks\n' + json.dumps(packet['checks'], indent=1)
        + '\n\n## Delivered files\n' + packet['diff'])
    r = harness.launch(manifest['checkout'], args, prompt, out_dir / (f'{name}-2.json' if resume_session else f'{name}-1.json'), 1200)
    d = r['result'] or {}
    decision = d.get('structured_output') or {}
    if not decision:
        try:
            decision = json.loads(d.get('result') or '{}')
        except ValueError:
            decision = {'decision': 'unparsed', 'findings': [], 'what_you_inspected': (d.get('result') or '')[:1000]}
    return {'decision': decision, 'cost_usd': d.get('total_cost_usd'), 'modelUsage': d.get('modelUsage'), 'usage': d.get('usage'),
            'session_id': d.get('session_id'), 'num_turns': d.get('num_turns'), 'duration_s': r['duration_s'], 'subtype': d.get('subtype')}


def handoff_problems(worker, manifest):
    """Every reason a worker round must not proceed to a paid acceptance session. Checked on every round,
    corrections included. An empty list means the handoff is complete and its claimed artifacts exist."""
    problems = []
    if worker['returncode'] != 0:
        problems.append(f'codex exec exit code {worker["returncode"]}')
    if worker['timed_out']:
        problems.append('worker timed out')
    h = worker['handoff']
    if not isinstance(h, dict):
        return problems + ['no handoff object']
    for key, typ in (('status', str), ('summary', str), ('files_changed', list), ('checks_run', str),
                     ('unresolved_risks', list), ('judgment_calls', list)):
        if not isinstance(h.get(key), typ):
            problems.append(f'handoff.{key} missing or not {typ.__name__}')
    if set(h) - set(SCHEMA['properties']):
        problems.append('handoff has keys outside the schema')
    if h.get('status') not in SCHEMA['properties']['status']['enum']:
        problems.append(f'handoff.status {h.get("status")!r} not in schema')
    elif h['status'] != 'complete':
        problems.append(f'worker reported status {h["status"]}')
    cwd = Path(manifest['checkout'])
    for rel in h.get('files_changed') or []:
        if not isinstance(rel, str) or not (cwd / rel).is_file():
            problems.append(f'claimed file missing: {rel!r}')
    if isinstance(h.get('files_changed'), list) and not any(isinstance(r, str) and r.startswith('imports/adapters/') for r in h['files_changed']):
        problems.append('no adapter module listed in files_changed')
    return problems


def abort(root, rounds, t0, worker_dir, problems):
    receipt = {'rounds': rounds, 'wall_s': time.time() - t0, 'aborted': 'handoff failed validation; no acceptance session spent', 'problems': problems}
    (root / 'receipt-F.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps({'aborted': receipt['aborted'], 'problems': problems,
                      'stderr_tail': (worker_dir / 'stderr.log').read_text(encoding='utf-8')[-600:] if (worker_dir / 'stderr.log').exists() else ''}, indent=2))


def run():
    root, manifest = load()
    if (root / 'receipt-F.json').exists():
        raise SystemExit('receipt-F exists; refusing a second paid workflow')
    if adapters.tree_hashes(Path(manifest['checkout'])) != manifest['files']:
        raise SystemExit('checkout changed since prepare')
    t0 = time.time()
    worker1 = run_worker(manifest, root / 'worker-1', WORKER_PROMPT)
    problems = handoff_problems(worker1, manifest)
    if problems:
        # No automatic retry: the repair path is a person reading the receipt. The worker's spend is in its rollout.
        abort(root, [{'worker': worker1}], t0, root / 'worker-1', problems)
        return
    checks1 = run_checks(manifest)
    skill = Path(manifest['checkout']) / 'SKILL.md'
    shutil.copy2(adapters.SKILL_PATH, skill)
    packet = {'handoff': worker1['handoff'], 'checks': checks1, 'diff': diff_text(manifest)}
    acc1 = accept(manifest, packet, root)
    rounds = [{'worker': worker1, 'checks': checks1, 'acceptance': acc1}]
    if acc1['decision'].get('decision') == 'correct' and acc1['decision'].get('findings'):
        fix_prompt = ('The orchestrator reviewed your work and requires these corrections before acceptance:\n- ' +
                      '\n- '.join(acc1['decision']['findings']) + '\n\nApply them, rerun your checks, and return JSON matching the schema.')
        fix_prompt = ('Your earlier implementation of TASK.md is already in this checkout (adapters, _shared.py, tests). ' + fix_prompt)
        skill.unlink()
        worker2 = run_worker(manifest, root / 'worker-2', fix_prompt)
        problems = handoff_problems(worker2, manifest)
        if problems:
            abort(root, rounds + [{'worker': worker2}], t0, root / 'worker-2', problems)
            return
        checks2 = run_checks(manifest)
        shutil.copy2(adapters.SKILL_PATH, skill)
        packet2 = {'handoff': worker2['handoff'], 'checks': checks2, 'diff': diff_text(manifest)}
        acc2 = accept(manifest, packet2, root, resume_session=acc1['session_id'])
        rounds.append({'worker': worker2, 'checks': checks2, 'acceptance': acc2})
    receipt = {'rounds': rounds, 'wall_s': time.time() - t0}
    (root / 'receipt-F.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps({'rounds': len(rounds), 'wall_s': round(receipt['wall_s']),
                      'final_decision': rounds[-1]['acceptance']['decision'],
                      'worker_threads': [r['worker']['thread_id'] for r in rounds],
                      'accept_costs': [r['acceptance']['cost_usd'] for r in rounds]}, indent=2))


def reaccept(argv):
    """Rerun only the acceptance session on the saved worker-1 submission (same prompt, same files), to measure a
    change to the acceptance session's configuration. One session per call; receipt-F.json is not touched.

      reaccept [--reviewer MODEL EFFORT] [--checkout DIR] [--label NAME]

    --checkout points the session at a copy of the F checkout (for example one with planted defects); the runner
    checks are re-run there and the worker's saved handoff is presented unchanged, as a real worker would have."""
    root, manifest = load()
    reviewer, label = None, 'reaccept'
    i = 0
    while i < len(argv):
        if argv[i] == '--reviewer':
            reviewer = (argv[i + 1], argv[i + 2]); i += 3
        elif argv[i] == '--checkout':
            manifest = dict(manifest, checkout=str(Path(argv[i + 1]).resolve())); i += 2
        elif argv[i] == '--label':
            label = argv[i + 1]; i += 2
        else:
            raise SystemExit(f'unknown argument {argv[i]}')
    summary = json.loads((root / 'summary-F.json').read_text(encoding='utf-8'))
    cwd = Path(manifest['checkout'])
    owned = {k: v for k, v in adapters.tree_hashes(cwd).items() if k.startswith('imports/adapters/') or k.startswith('test_')}
    if label == 'reaccept' and owned != summary['owned_file_hashes']:
        raise SystemExit('checkout differs from the graded F submission; refusing (use --label for a variant checkout)')
    handoff = json.loads((root / 'worker-1' / 'handoff.json').read_text(encoding='utf-8'))
    n = 1 + len(list(root.glob(f'{label}-*')))
    out_dir = root / f'{label}-{n}'
    out_dir.mkdir()
    shutil.copy2(adapters.SKILL_PATH, cwd / 'SKILL.md')
    packet = {'handoff': handoff, 'checks': run_checks(manifest), 'diff': diff_text(manifest)}
    acc = accept(manifest, packet, out_dir, name='accept', reviewer=reviewer)
    acc['configuration'] = {'tools': ACCEPT_TOOLS, 'reviewer': list(reviewer or REVIEWER), 'budget': ACCEPT_BUDGET,
                            'checkout': manifest['checkout'], 'owned_file_hashes': owned}
    (out_dir / 'receipt-reaccept.json').write_text(json.dumps(acc, indent=2), encoding='utf-8')
    print(json.dumps({label: n, 'decision': acc['decision'], 'cost_usd': acc['cost_usd'], 'turns': acc['num_turns'],
                      'duration_s': round(acc['duration_s']), 'usage': acc['usage'],
                      'modelUsage': {m: {k: u[k] for k in ('cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens', 'costUSD')}
                                     for m, u in (acc['modelUsage'] or {}).items()}}, indent=2))


def correct(argv):
    """Run one correction round from a saved acceptance: `correct --from <label-dir>`. Fresh Luna session with the
    reviewer's findings, handoff guard, runner checks, then the same reviewer session resumed. Used when an acceptance
    was run through `reaccept` (for example after an interrupted `run`) and returned `correct`."""
    root, manifest = load()
    src = Path(argv[argv.index('--from') + 1])
    if not src.is_absolute():
        src = root / src
    acc1 = json.loads((src / 'receipt-reaccept.json').read_text(encoding='utf-8'))
    if acc1['decision'].get('decision') != 'correct' or not acc1['decision'].get('findings'):
        raise SystemExit('saved acceptance is not a correct decision with findings')
    if (src / 'receipt-correct.json').exists():
        raise SystemExit('correction already run for this acceptance')
    reviewer = tuple(acc1['configuration']['reviewer'])
    cwd = Path(manifest['checkout'])
    t0 = time.time()
    fix_prompt = ('Your earlier implementation of TASK.md is already in this checkout (adapters, _shared.py, tests). '
                  'The orchestrator reviewed your work and requires these corrections before acceptance:\n- ' +
                  '\n- '.join(acc1['decision']['findings']) + '\n\nApply them, rerun your checks, and return JSON matching the schema.')
    skill = cwd / 'SKILL.md'
    if skill.exists():
        skill.unlink()
    n = 1 + len(list(root.glob('worker-*')))
    worker2 = run_worker(manifest, root / f'worker-{n}', fix_prompt)
    problems = handoff_problems(worker2, manifest)
    if problems:
        (src / 'receipt-correct.json').write_text(json.dumps({'worker': worker2, 'aborted': problems}, indent=2), encoding='utf-8')
        print(json.dumps({'aborted': problems}, indent=2))
        return
    checks2 = run_checks(manifest)
    shutil.copy2(adapters.SKILL_PATH, skill)
    packet2 = {'handoff': worker2['handoff'], 'checks': checks2, 'diff': diff_text(manifest)}
    acc2 = accept(manifest, packet2, src, resume_session=acc1['session_id'], name='accept', reviewer=reviewer)
    out = {'worker': worker2, 'checks': checks2, 'acceptance': acc2, 'wall_s': time.time() - t0, 'from': str(src)}
    (src / 'receipt-correct.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps({'decision': acc2['decision'], 'accept_cost_usd': acc2['cost_usd'], 'worker_thread': worker2['thread_id'],
                      'worker_dur_s': round(worker2['duration_s']), 'checks': checks2}, indent=2))


def luna_accounting(thread_ids):
    out = []
    for path in (Path.home() / '.codex/sessions').glob('*/*/*/rollout-*.jsonl'):
        try:
            meta = json.loads(path.open(encoding='utf-8').readline())
        except (OSError, ValueError):
            continue
        if meta.get('type') != 'session_meta' or meta['payload'].get('id') not in thread_ids:
            continue
        rows = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
        tid = meta['payload']['id']
        contexts = {r['payload'].get('turn_id'): r['payload'] for r in rows if r.get('type') == 'turn_context'}
        records = {r['payload']['response_id']: r['payload'] for r in rows if r.get('type') == 'token_usage_record' and r['payload'].get('thread_id') == tid}
        totals, cost, configs = Counter(), 0.0, set()
        for rec in records.values():
            u, ctx = rec['usage'], contexts.get(rec['turn_id'], {})
            configs.add((ctx.get('model'), ctx.get('effort')))
            totals.update({f: u.get(f, 0) for f in luna.FIELDS})
            inp, cached, written, outp = (u.get(f, 0) for f in luna.FIELDS[:4])
            ri, rc, rw, ro = luna.RATES['gpt-5.6-luna']
            cost += ((inp - cached - written) * ri + cached * rc + written * rw + outp * ro) / 1e6
        out.append({'thread_id': tid, 'rollout': str(path), 'configurations': sorted(configs, key=str), 'responses': len(records),
                    'usage': dict(totals), 'api_equivalent_usd': round(cost, 6)})
    return out


def summarize():
    root, manifest = load()
    receipt = json.loads((root / 'receipt-F.json').read_text(encoding='utf-8'))
    threads = [r['worker']['thread_id'] for r in receipt['rounds'] if r['worker']['thread_id']]
    lunas = luna_accounting(set(threads))
    grade = adapters.grade(manifest['checkout'], manifest['codex_source'], root / 'held-out.json', manifest['formats'])
    claude_cost = sum(r['acceptance']['cost_usd'] or 0 for r in receipt['rounds'])
    luna_cost = sum(l['api_equivalent_usd'] for l in lunas)
    out = {'grade': grade, 'claude_cost_usd': claude_cost, 'luna_cost_usd': luna_cost, 'total_usd': claude_cost + luna_cost,
           'rounds': receipt['rounds'], 'luna': lunas, 'wall_s': receipt['wall_s'],
           'owned_file_hashes': {k: v for k, v in adapters.tree_hashes(Path(manifest['checkout'])).items() if k.startswith('imports/adapters/') or k.startswith('test_')}}
    (root / 'summary-F.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    g = grade
    print('F total', round(out['total_usd'], 4), 'claude', round(claude_cost, 4), 'luna', round(luna_cost, 4), 'wall', round(out['wall_s']), 'passed', g['passed'],
          [(c['check'], c.get('summary', {}).get('passed'), c.get('summary', {}).get('cases'), c.get('exit_code')) for c in g.get('checks', [])],
          g.get('changed_protected_files'), g.get('unexpected_python_files'))
    for i, r in enumerate(receipt['rounds'], 1):
        a = r['acceptance']
        print(f' round {i}: worker rc={r["worker"]["returncode"]} timed_out={r["worker"]["timed_out"]} dur={round(r["worker"]["duration_s"])}s status={((r["worker"]["handoff"] or {}).get("status"))}'
              f' | accept decision={a["decision"].get("decision")} turns={a["num_turns"]} cost={a["cost_usd"]} dur={round(a["duration_s"])}s')
        for m, u in (a['modelUsage'] or {}).items():
            print('   ', m, {k: u[k] for k in ('inputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens', 'thinkingTokens', 'costUSD')})
    for l in lunas:
        print('   luna', l['thread_id'], l['configurations'], l['responses'], l['usage'], l['api_equivalent_usd'])


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'reaccept':
        reaccept(sys.argv[2:])
    elif mode == 'correct':
        correct(sys.argv[2:])
    else:
        {'prepare': prepare, 'run': run, 'summarize': summarize}.get(mode, lambda: print(__doc__))()
