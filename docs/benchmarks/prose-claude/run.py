"""Claude-native prose migration trial: A (solo, no skill) and D (skill + one forced Opus 5 low worker).

Runs on the machine where Claude Code is installed and logged in. Usage:

  python -B -X utf8 run.py prepare            # build isolated checkouts, write manifest (no model calls)
  python -B -X utf8 run.py preflight          # grader/checker on reference and mutants, leakage print (no model calls)
  python -B -X utf8 run.py smoke              # one tiny paid session ($2 cap) proving agent dispatch and receipts
  python -B -X utf8 run.py run A|D            # one paid session, once; refuses to rerun
  python -B -X utf8 run.py summarize          # grade, check, cost table

Every paid mode writes a receipt beside the checkout. Nothing here retries.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'local-fixture.json'
SKILL_PATH = HERE.parent.parent.parent / 'SKILL.md'
ORCHESTRATOR = ('claude-fable-5-1', 'medium')
WORKER = ('claude-opus-5', 'low')
BUDGET_USD = 8.0
TIMEOUT_S = 2700
COMMON_TOOLS = ['Read', 'Glob', 'Grep', 'Edit', 'Write', 'Bash', 'PowerShell']

TASK_PROMPT = (
    'Complete the task described in TASK.md in the current directory. '
    'Before finishing, run `python -B check.py .` and include its output verbatim in your final message. '
    'Do not use distill or any external service. Keep the final message short: answer path, check output, unresolved work.'
)
FORCED_D = (
    ' Required execution: read SKILL.md in this directory first and follow it. '
    'Delegate the complete TASK.md deliverable to exactly one `scout` subagent (Opus 5, low effort); '
    'the worker owns reading the discussions, writing answer.json and running check.py. '
    'Keep the assignment brief. Retain final verification yourself. Do not launch any other worker.'
)
SCOUT_PROMPT = (
    'You are a worker completing one bounded assignment inside the current directory. '
    'Work only from the files you are pointed at. Do not edit TASK.md, check.py or anything under threads/. '
    'Finish by reporting: complete, partial or blocked; files written; the verbatim output of any check you ran; '
    'and unresolved risks. Do not weaken or rewrite any supplied check.'
)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(Path(p).read_bytes())


def source_text(case):
    return f"# {case['id']}: {case['title']}\n\nQuestion: {case['question']}\n\n{case['text'].strip()}\n"


def load_fixture():
    if not FIXTURE.is_file():
        raise SystemExit('run prepare first')
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


def render_checkout(root, cases, with_skill):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / 'threads').mkdir(exist_ok=True)
    frozen = {}
    (root / 'TASK.md').write_bytes((HERE / 'TASK.md').read_bytes())
    frozen['TASK.md'] = sha_file(root / 'TASK.md')
    for case in cases:
        p = root / 'threads' / (case['id'] + '.md')
        p.write_text(source_text(case), encoding='utf-8', newline='\n')
        frozen['threads/' + p.name] = sha_file(p)
    checker = (HERE / 'check.py').read_text(encoding='utf-8')
    checker = checker.replace('FROZEN = None', 'FROZEN = ' + json.dumps(frozen, sort_keys=True), 1)
    (root / 'check.py').write_text(checker, encoding='utf-8', newline='\n')
    if with_skill:
        (root / 'SKILL.md').write_bytes(SKILL_PATH.read_bytes())
    return {rel: sha_file(root / rel) for rel in sorted(
        [*frozen, 'check.py'] + (['SKILL.md'] if with_skill else []))}


def prepare():
    if FIXTURE.is_file():
        raise SystemExit('fixture exists; refusing to overwrite an experiment root')
    cases = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))
    root = Path(tempfile.mkdtemp(prefix='claude-prose-'))
    manifest = {'root': str(root), 'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'orchestrator': ORCHESTRATOR, 'worker': WORKER, 'budget_usd': BUDGET_USD,
                'cases_sha256': sha_file(HERE / 'cases.json'), 'grader_sha256': sha_file(HERE / 'grade.py'),
                'checker_template_sha256': sha_file(HERE / 'check.py'), 'skill_sha256': sha_file(SKILL_PATH),
                'runner_sha256': sha_file(__file__), 'arms': {}}
    for arm in ('A', 'D'):
        manifest['arms'][arm] = {'path': str(root / arm), 'files': render_checkout(root / arm, cases, arm == 'D')}
    b = shutil.which('claude.exe') or shutil.which('claude')
    manifest['claude_version'] = subprocess.run([b, '--version'], capture_output=True, text=True).stdout.strip() if b else 'claude not on PATH'
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    FIXTURE.write_text(json.dumps({'root': str(root)}, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


def claude_bin():
    b = shutil.which('claude.exe') or shutil.which('claude')
    if not b:
        raise SystemExit('claude not found on PATH')
    return b


def base_args(model, effort, budget, extra_tools_disallowed, allowed=None, tools=None):
    # --safe-mode is not used: it disables custom agents passed via --agents (smoke test, 10 Sep 2026).
    # Consequence: the user's global ~/.claude/CLAUDE.md is loaded in every arm; the prompt forbids distill.
    args = [claude_bin(), '-p', '--output-format', 'json', '--setting-sources', '',
            '--strict-mcp-config', '--disable-slash-commands', '--permission-mode', 'dontAsk',
            '--permission-prompts', 'none', '--max-budget-usd', str(budget),
            '--model', model, '--effort', effort,
            '--disallowedTools', ','.join(['WebSearch', 'WebFetch', 'NotebookEdit'] + extra_tools_disallowed),
            # dontAsk denies anything not explicitly allowed; A attempt 2 (10 Sep) was blocked on Write/Bash without this.
            '--allowedTools', ','.join(allowed or COMMON_TOOLS)]
    if tools is not None:
        # --disallowedTools only denies a call; the denied tools' definitions are still sent with every request
        # (Haiku probe, 11 Sep 2026: 24.1k fixed tokens with the default tool list, 15.0k with --tools naming the
        # five the session may call). --tools removes the definitions. Structured output still works under it.
        args += ['--tools', ','.join(tools)]
    return args


def agents_json():
    return json.dumps({'scout': {'description': 'Bounded worker: reads supplied discussions, writes answer.json, runs check.py.',
                                 'prompt': SCOUT_PROMPT, 'model': WORKER[0], 'effort': WORKER[1],
                                 'tools': COMMON_TOOLS}})


def child_env():
    env = dict(os.environ)
    for k in list(env):
        if k.startswith('ANTHROPIC_') or k in ('CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX'):
            env.pop(k)
    env['FORCE_PROMPT_CACHING_5M'] = '1'  # match the Codex-side Claude runs; default writes were 1-hour in the first smoke
    return env


def launch(cwd, args, prompt, receipt_path, timeout):
    started = time.time()
    try:
        # Prompt goes on stdin: variadic options such as --disallowedTools would otherwise swallow a trailing positional.
        proc = subprocess.run(args, input=prompt, cwd=cwd, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, env=child_env())
        timed_out, rc, out, err = False, proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out, rc = True, None
        out = exc.stdout.decode('utf-8', 'replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        err = exc.stderr.decode('utf-8', 'replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
    duration = time.time() - started
    try:
        data = json.loads(out) if out.strip() else None
    except ValueError:
        data = None
    receipt = {'command': args, 'prompt': prompt, 'prompt_sha256': sha_bytes(prompt.encode()), 'cwd': str(cwd),
               'started': started, 'duration_s': duration, 'timed_out': timed_out, 'returncode': rc,
               'stdout_raw': out, 'stderr': err, 'result': data}
    Path(receipt_path).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def smoke():
    fx = load_fixture()
    root = Path(fx['root']) / 'smoke'
    if (root / 'receipt.json').exists():
        raise SystemExit('smoke receipt exists; not repeating a paid call')
    root.mkdir(parents=True, exist_ok=True)
    (root / 'hello.txt').write_text('harbor-smoke-7731\n', encoding='utf-8')
    args = base_args(*ORCHESTRATOR, 2.0, [], COMMON_TOOLS + ['Agent']) + ['--agents', agents_json()]
    prompt = ('Use the `scout` subagent to read hello.txt and return its exact contents. Do nothing else yourself. '
              'Reply with only what the subagent returned.')
    r = launch(root, args, prompt, root / 'receipt.json', 600)
    print(json.dumps({k: r.get(k) for k in ('duration_s', 'timed_out', 'returncode')}, indent=2))
    d = r['result'] or {}
    print(json.dumps({k: d.get(k) for k in ('subtype', 'is_error', 'result', 'total_cost_usd', 'usage', 'modelUsage',
                                            'session_id', 'num_turns', 'permission_denials')}, indent=2))
    if r['stderr']:
        print('STDERR:', r['stderr'][:2000])


def run(arm):
    fx = load_fixture()
    root = Path(fx['root'])
    cwd = root / arm
    receipt = root / f'receipt-{arm}.json'
    if receipt.exists():
        raise SystemExit(f'{receipt} exists; refusing a second paid run for arm {arm}')
    if (cwd / 'answer.json').exists():
        raise SystemExit('answer.json already present in checkout; not a fresh start')
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    for rel, digest in manifest['arms'][arm]['files'].items():
        if sha_file(cwd / rel) != digest:
            raise SystemExit(f'{rel} changed since prepare')
    if arm == 'A':
        args = base_args(*ORCHESTRATOR, BUDGET_USD, ['Agent', 'Task'])
        prompt = TASK_PROMPT
    elif arm == 'D':
        args = base_args(*ORCHESTRATOR, BUDGET_USD, [], COMMON_TOOLS + ['Agent']) + ['--agents', agents_json()]
        prompt = TASK_PROMPT + FORCED_D
    else:
        raise SystemExit('arm must be A or D')
    print('launching', arm, 'in', cwd)
    r = launch(cwd, args, prompt, receipt, TIMEOUT_S)
    d = r['result'] or {}
    print(json.dumps({'duration_s': r['duration_s'], 'timed_out': r['timed_out'], 'returncode': r['returncode'],
                      'subtype': d.get('subtype'), 'is_error': d.get('is_error'), 'total_cost_usd': d.get('total_cost_usd'),
                      'session_id': d.get('session_id'), 'num_turns': d.get('num_turns'),
                      'modelUsage': d.get('modelUsage'), 'answer_present': (cwd / 'answer.json').exists()}, indent=2))
    if r['stderr']:
        print('STDERR:', r['stderr'][:2000])


def summarize():
    fx = load_fixture()
    root = Path(fx['root'])
    out = {}
    for arm in ('A', 'D'):
        rp = root / f'receipt-{arm}.json'
        if not rp.exists():
            out[arm] = 'no receipt'
            continue
        r = json.loads(rp.read_text(encoding='utf-8'))
        d = r['result'] or {}
        cwd = root / arm
        entry = {'duration_s': r['duration_s'], 'timed_out': r['timed_out'], 'subtype': d.get('subtype'),
                 'total_cost_usd': d.get('total_cost_usd'), 'usage': d.get('usage'), 'modelUsage': d.get('modelUsage'),
                 'session_id': d.get('session_id'), 'num_turns': d.get('num_turns')}
        if (cwd / 'answer.json').exists():
            entry['answer_sha256'] = sha_file(cwd / 'answer.json')
            g = subprocess.run([sys.executable, '-B', str(HERE / 'grade.py'), str(cwd)], capture_output=True, text=True)
            entry['grade'] = json.loads(g.stdout) if g.stdout.strip() else g.stderr
            c = subprocess.run([sys.executable, '-B', str(cwd / 'check.py'), str(cwd)], capture_output=True, text=True)
            entry['check'] = json.loads(c.stdout) if c.stdout.strip() else c.stderr
        else:
            entry['answer_sha256'] = None
        out[arm] = entry
    (root / 'summary.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


def preflight():
    fx = load_fixture()
    root = Path(fx['root'])
    cases = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))
    ref = root / 'preflight-ref'
    shutil.rmtree(ref, ignore_errors=True)
    render_checkout(ref, cases, False)

    def norm(t):
        return ' '.join(t.split())

    recs = []
    for c in cases:
        lines = source_text(c).splitlines()
        ev = []
        for q in c['decisive_evidence']:
            hit = [i for i, l in enumerate(lines, 1) if norm(q) in norm(l)]
            ev.append({'line_start': hit[0], 'line_end': hit[0], 'quote': q})
        recs.append({'id': c['id'], 'disposition': c['expected_disposition'],
                     'explanation': c['rationale'] + ' This reference explanation is padded to satisfy the minimum length rule of the checker.',
                     'evidence': ev})
    base = {'release': '4.0', 'assessed_at': '2031-06-30', 'records': recs}

    def trial(name, mutate, expect_grade, expect_check):
        d = root / ('preflight-' + name)
        shutil.rmtree(d, ignore_errors=True)
        render_checkout(d, cases, False)
        a = json.loads(json.dumps(base))
        mutate(a, d)
        (d / 'answer.json').write_text(json.dumps(a, indent=1), encoding='utf-8')
        g = json.loads(subprocess.run([sys.executable, '-B', str(HERE / 'grade.py'), str(d)], capture_output=True, text=True).stdout)
        c = json.loads(subprocess.run([sys.executable, '-B', str(d / 'check.py'), str(d)], capture_output=True, text=True).stdout)
        ok = (g['automated_pass'] == expect_grade) and (c['pass'] == expect_check)
        print(f"{name:26} grader={g['automated_pass']!s:5} checker={c['pass']!s:5} {'ok' if ok else 'UNEXPECTED'}")
        return ok

    def ellipsis(a, _):
        q = a['records'][0]['evidence'][0]['quote'].split()
        a['records'][0]['evidence'][0]['quote'] = ' '.join(q[:3]) + ' ... ' + ' '.join(q[-3:])

    def oneword(a, _):
        for r in a['records']:
            r['evidence'] = [{'line_start': 1, 'line_end': 1, 'quote': r['id']}]

    def wholefile(a, d):
        a['records'][0]['evidence'][0]['line_start'] = 1
        a['records'][0]['evidence'][0]['line_end'] = len((d / 'threads' / 'ISSUE-001.md').read_text(encoding='utf-8').splitlines())

    def shortexpl(a, _):
        a['records'][0]['explanation'] = 'ok'

    def wrongdisp(a, _):
        r = a['records'][0]
        r['disposition'] = 'none' if r['disposition'] != 'none' else 'required'

    def fabricated(a, _):
        a['records'][0]['evidence'][0]['quote'] = 'this sentence does not appear in any supplied discussion at all'

    def missing(a, _):
        a['records'].pop()

    def changed_source(a, d):
        p = d / 'threads' / 'ISSUE-001.md'
        p.write_text(p.read_text(encoding='utf-8') + '\nextra\n', encoding='utf-8')

    results = [trial('reference', lambda a, d: None, True, True),
               trial('ellipsis', ellipsis, False, False),
               trial('one-word-id-quote', oneword, True, False),
               trial('whole-file-span', wholefile, True, False),
               trial('two-word-explanation', shortexpl, True, False),
               trial('wrong-disposition', wrongdisp, False, True),
               trial('fabricated-quote', fabricated, False, False),
               trial('missing-record', missing, False, False),
               trial('changed-source', changed_source, False, False)]
    for arm in ('A', 'D'):
        cwd = root / arm
        print(arm, 'answer.json present:', (cwd / 'answer.json').exists(), '| SKILL.md present:', (cwd / 'SKILL.md').exists())
    print('Prompt A:', TASK_PROMPT)
    print('Prompt D:', TASK_PROMPT + FORCED_D)
    print('Scout prompt:', SCOUT_PROMPT)
    print('ALL EXPECTED' if all(results) else 'PREFLIGHT FAILED')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'prepare':
        prepare()
    elif mode == 'preflight':
        preflight()
    elif mode == 'smoke':
        smoke()
    elif mode == 'run':
        run(sys.argv[2])
    elif mode == 'summarize':
        summarize()
    else:
        raise SystemExit(__doc__)
