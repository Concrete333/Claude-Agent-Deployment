"""Arm E: Fable 5.1 medium orchestrator + one Luna Max worker reached through OpenAI's Codex plugin for Claude Code.

Same adapter fixture, grader and acceptance as adapters.py. The Codex side runs in an isolated CODEX_HOME
(own config, copied auth, no personal skills/plugins/MCP servers) so Luna's context matches the Codex team's
suppressed runs and its rollouts can be accounted separately. Usage:

  python -B -X utf8 luna.py prepare      # checkout + isolated CODEX_HOME (copies auth.json; deleted by `cleanup`)
  python -B -X utf8 luna.py smoke        # Haiku orchestrator asks Codex to write one file; verifies model/effort/cost
  python -B -X utf8 luna.py run          # one paid session, once
  python -B -X utf8 luna.py summarize    # grade + Claude receipts + Luna rollout accounting
  python -B -X utf8 luna.py cleanup      # remove the copied auth.json
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
FIXTURE = HERE / 'local-fixture-luna.json'
spec = importlib.util.spec_from_file_location('adapters', HERE / 'adapters.py')
adapters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapters)
harness = adapters.harness

PLUGIN_DIR = Path.home() / '.claude/plugins/cache/openai-codex/codex/1.0.6'
WORKER = ('gpt-5.6-luna', 'max')
BUDGET_USD = 8.0
TIMEOUT_S = 1800
TOOLS = ['Read', 'Glob', 'Grep', 'Edit', 'Write', 'Bash', 'PowerShell', 'Agent']
RATES = {'gpt-5.6-luna': (.2, .02, .25, 1.2)}  # per million: uncached input, cached input, cache write, output (Codex team's table)
FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens')

FORCED_E = (
    ' Required execution: read SKILL.md in this directory first and follow it. Delegate the complete adapter batch to '
    'Codex through the `codex:codex-rescue` subagent (Agent tool, subagent_type "codex:codex-rescue"), exactly once to '
    'start. The request you forward must begin with `--wait --fresh --model gpt-5.6-luna --write` followed by a brief '
    'assignment; do not set --effort, the Codex runtime is preconfigured. The worker owns implementation, local checks, '
    'added tests and corrections. If you need a correction, forward one more request beginning '
    '`--wait --resume --model gpt-5.6-luna --write`. Retain final acceptance yourself. Do not use any other worker.'
)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def codex_config(checkout):
    return f'''model = "{WORKER[0]}"
model_reasoning_effort = "{WORKER[1]}"
approval_policy = "never"
project_doc_max_bytes = 0
web_search = "disabled"

[windows]
sandbox = "elevated"

[features]
memories = false
plugins = false
remote_plugin = false

[memories]
use_memories = false
generate_memories = false

[agents]
enabled = false

[projects.'{checkout}']
trust_level = "trusted"
'''


def child_env(codex_home):
    env = harness.child_env()
    env['CODEX_HOME'] = str(codex_home)
    env['BASH_DEFAULT_TIMEOUT_MS'] = '1500000'
    env['BASH_MAX_TIMEOUT_MS'] = '1500000'
    return env


def prepare():
    if FIXTURE.exists():
        raise SystemExit('fixture exists; preserve it')
    assert (PLUGIN_DIR / 'agents/codex-rescue.md').is_file(), 'Codex plugin 1.0.6 not installed'
    codex = json.loads(adapters.CODEX_FIXTURE.read_text(encoding='utf-8'))
    src, ref, held = Path(codex['source']), Path(codex['reference']), Path(codex['root']) / 'held-out.json'
    root = Path(codex['root']).parent / ('claude-adapters-luna-' + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8])
    root.mkdir()
    shutil.copy2(held, root / 'held-out.json')
    checkout = root / 'E'
    shutil.copytree(src, checkout, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(adapters.SKILL_PATH, checkout / 'SKILL.md')
    home = root / 'codex-home'
    home.mkdir()
    (home / 'config.toml').write_text(codex_config(str(checkout)), encoding='utf-8')  # TOML literal string: no escaping
    shutil.copy2(Path.home() / '.codex/auth.json', home / 'auth.json')
    smoke = root / 'smoke'
    smoke.mkdir()
    (home / 'config.toml').write_text((home / 'config.toml').read_text(encoding='utf-8')
                                      + f"\n[projects.'{smoke}']\ntrust_level = \"trusted\"\n", encoding='utf-8')
    manifest = {'root': str(root), 'checkout': str(checkout), 'codex_home': str(home), 'plugin_dir': str(PLUGIN_DIR),
                'plugin_hashes': {p.relative_to(PLUGIN_DIR).as_posix(): sha_file(p) for p in PLUGIN_DIR.rglob('*') if p.is_file()},
                'codex_source': str(src), 'formats': codex['formats'], 'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'orchestrator': adapters.ORCHESTRATOR, 'worker': WORKER, 'budget_usd': BUDGET_USD, 'timeout_s': TIMEOUT_S,
                'skill_sha256': sha_file(adapters.SKILL_PATH), 'files': adapters.tree_hashes(checkout),
                'codex_config_sha256': sha_file(home / 'config.toml'),
                'codex_version': subprocess.run(['codex', '--version'], capture_output=True, text=True, shell=True).stdout.strip()}
    qual = adapters.grade(ref, src, root / 'held-out.json', codex['formats'])
    stub = adapters.grade(checkout, src, root / 'held-out.json', codex['formats'])
    manifest['reference_qualification'] = qual['passed']
    manifest['stub_rejection'] = not stub['passed']
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    FIXTURE.write_text(json.dumps({'root': str(root)}, indent=2), encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('root', 'checkout', 'codex_home', 'codex_version', 'reference_qualification', 'stub_rejection')}, indent=2))
    assert qual['passed'] and not stub['passed']


def load():
    root = Path(json.loads(FIXTURE.read_text(encoding='utf-8'))['root'])
    return root, json.loads((root / 'manifest.json').read_text(encoding='utf-8'))


def base_args(model, effort, budget):
    return harness.base_args(model, effort, budget, [], TOOLS) + ['--plugin-dir', str(PLUGIN_DIR)]


def smoke():
    root, manifest = load()
    d = root / 'smoke'
    if (d / 'receipt.json').exists():
        raise SystemExit('smoke receipt exists')
    args = base_args('claude-haiku-4-5', 'medium', 1.0)
    prompt = ('Use the codex:codex-rescue subagent (Agent tool, subagent_type "codex:codex-rescue") exactly once with this '
              'request: `--wait --fresh --model gpt-5.6-luna --write Create a file named hello.txt in the current directory '
              'containing exactly the line luna-smoke-4419 and nothing else.` Then reply with the subagent output verbatim.')
    r = launch(d, args, prompt, d / 'receipt.json', 900, manifest)
    report(r, d / 'hello.txt', manifest)


def launch(cwd, args, prompt, receipt_path, timeout, manifest):
    started = time.time()
    try:
        proc = subprocess.run(args, input=prompt, cwd=cwd, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, env=child_env(manifest['codex_home']))
        timed_out, rc, out, err = False, proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out, rc = True, None
        out = (exc.stdout or b'').decode('utf-8', 'replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        err = (exc.stderr or b'').decode('utf-8', 'replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
    try:
        data = json.loads(out) if out.strip() else None
    except ValueError:
        data = None
    receipt = {'command': args, 'prompt': prompt, 'cwd': str(cwd), 'started': started, 'duration_s': time.time() - started,
               'timed_out': timed_out, 'returncode': rc, 'stdout_raw': out, 'stderr': err, 'result': data}
    Path(receipt_path).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def codex_accounting(codex_home):
    """Own-thread usage per Codex rollout under the isolated CODEX_HOME, priced with the Codex team's rates."""
    out = []
    for path in sorted(Path(codex_home).glob('sessions/**/rollout-*.jsonl')):
        rows = []
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
        meta = next((r['payload'] for r in rows if r.get('type') == 'session_meta'), {})
        contexts = {r['payload'].get('turn_id'): r['payload'] for r in rows if r.get('type') == 'turn_context'}
        records = {r['payload']['response_id']: r['payload'] for r in rows
                   if r.get('type') == 'token_usage_record' and r['payload'].get('thread_id') == meta.get('id')}
        totals, configs, cost, max_input = Counter(), set(), 0.0, 0
        for rec in records.values():
            usage, ctx = rec['usage'], contexts.get(rec['turn_id'], {})
            configs.add((ctx.get('model'), ctx.get('effort')))
            totals.update({f: usage.get(f, 0) for f in FIELDS})
            inp, cached, written, outp = (usage.get(f, 0) for f in FIELDS[:4])
            ri, rc, rw, ro = RATES.get(ctx.get('model'), (None,) * 4)
            if ri is None:
                cost = None
                break
            cost += ((inp - cached - written) * ri + cached * rc + written * rw + outp * ro) / 1e6
            max_input = max(max_input, inp)
        out.append({'rollout': str(path), 'thread_id': meta.get('id'), 'cli_version': meta.get('cli_version'),
                    'configurations': sorted(configs, key=str), 'responses': len(records), 'usage': dict(totals),
                    'max_input': max_input, 'api_equivalent_usd': None if cost is None else round(cost, 6)})
    return out


def report(r, artifact, manifest):
    d = r['result'] or {}
    codex = codex_accounting(manifest['codex_home'])
    print(json.dumps({'duration_s': r['duration_s'], 'timed_out': r['timed_out'], 'returncode': r['returncode'],
                      'subtype': d.get('subtype'), 'is_error': d.get('is_error'), 'claude_cost_usd': d.get('total_cost_usd'),
                      'claude_modelUsage': {k: {kk: v[kk] for kk in ('inputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens', 'costUSD')}
                                            for k, v in (d.get('modelUsage') or {}).items()},
                      'session_id': d.get('session_id'), 'num_turns': d.get('num_turns'),
                      'artifact_present': Path(artifact).exists(), 'codex_rollouts': codex}, indent=2))
    print('RESULT:', (d.get('result') or '')[:3000])
    if r['stderr']:
        print('STDERR:', r['stderr'][:1500])


def run():
    root, manifest = load()
    cwd = Path(manifest['checkout'])
    receipt = root / 'receipt-E.json'
    if receipt.exists():
        raise SystemExit('receipt-E exists; refusing a second paid run')
    if adapters.tree_hashes(cwd) != manifest['files']:
        raise SystemExit('checkout changed since prepare')
    args = base_args(*adapters.ORCHESTRATOR, BUDGET_USD)
    prompt = adapters.TASK_PROMPT + FORCED_E
    print('launching E in', cwd)
    r = launch(cwd, args, prompt, receipt, TIMEOUT_S, manifest)
    report(r, cwd / 'imports/adapters/_shared.py', manifest)


def summarize():
    root, manifest = load()
    cwd = Path(manifest['checkout'])
    r = json.loads((root / 'receipt-E.json').read_text(encoding='utf-8'))
    d = r['result'] or {}
    codex = codex_accounting(manifest['codex_home'])
    luna = sum(c['api_equivalent_usd'] or 0 for c in codex if c['thread_id'] and 'smoke' not in c['rollout'])
    out = {'duration_s': r['duration_s'], 'timed_out': r['timed_out'], 'subtype': d.get('subtype'),
           'claude_cost_usd': d.get('total_cost_usd'), 'claude_modelUsage': d.get('modelUsage'), 'usage': d.get('usage'),
           'session_id': d.get('session_id'), 'num_turns': d.get('num_turns'), 'codex_rollouts': codex,
           'grade': adapters.grade(cwd, manifest['codex_source'], root / 'held-out.json', manifest['formats']),
           'owned_file_hashes': {k: v for k, v in adapters.tree_hashes(cwd).items() if k.startswith('imports/adapters/') or k.startswith('test_')}}
    (root / 'summary-E.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    g = out['grade']
    print('E claude', out['claude_cost_usd'], 'turns', out['num_turns'], 'dur', round(out['duration_s']), 'passed', g['passed'],
          [(c['check'], c.get('summary', {}).get('passed'), c.get('summary', {}).get('cases'), c.get('exit_code')) for c in g.get('checks', [])],
          g.get('changed_protected_files'), g.get('unexpected_python_files'))
    for m, u in (out['claude_modelUsage'] or {}).items():
        print('   ', m, {k: u[k] for k in ('inputTokens', 'cacheCreationInputTokens', 'cacheReadInputTokens', 'outputTokens', 'thinkingTokens', 'costUSD')})
    for c in codex:
        print('   codex', c['thread_id'], c['configurations'], c['responses'], c['usage'], c['api_equivalent_usd'])


def cleanup():
    root, manifest = load()
    auth = Path(manifest['codex_home']) / 'auth.json'
    if auth.exists():
        auth.unlink()
        print('removed', auth)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    {'prepare': prepare, 'smoke': smoke, 'run': run, 'summarize': summarize, 'cleanup': cleanup}.get(mode, lambda: print(__doc__))()
