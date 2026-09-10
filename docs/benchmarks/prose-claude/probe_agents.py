"""Cheap discovery: which way of defining a custom agent is visible to the Agent tool in this CLI.
Uses Haiku with a $0.20 cap per probe. Not part of the trial; receipts kept beside the smoke folder."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=True)
claude = shutil.which('claude.exe') or shutil.which('claude')
AGENTS = json.dumps({'scout': {'description': 'Probe agent.', 'prompt': 'You are a probe.', 'model': 'claude-opus-5', 'effort': 'low'}})
PROMPT = 'Do not call any tool. Reply with one line listing every agent type the Agent tool description says is available.'
env = dict(os.environ); env['FORCE_PROMPT_CACHING_5M'] = '1'

def probe(name, cwd, extra):
    args = [claude, '-p', '--output-format', 'json', '--model', 'claude-haiku-4-5', '--max-budget-usd', '0.2',
            '--permission-mode', 'dontAsk', '--permission-prompts', 'none', '--strict-mcp-config',
            '--disable-slash-commands'] + extra + [PROMPT]
    t = time.time()
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300, env=env)
    try:
        d = json.loads(p.stdout)
    except ValueError:
        d = {'raw': p.stdout[:500]}
    rec = {'name': name, 'args': args, 'rc': p.returncode, 'seconds': round(time.time() - t, 1),
           'result': d.get('result'), 'cost': d.get('total_cost_usd'), 'stderr': p.stderr[:500]}
    (root / f'probe-{name}.json').write_text(json.dumps(rec, indent=2), encoding='utf-8')
    print(name, '|', rec['rc'], '|', rec['cost'], '|', (rec['result'] or rec['stderr'])[:300].replace('\n', ' '))

def basic():
  d1 = root / 'p1'; d1.mkdir(exist_ok=True)
  probe('agents-flag-no-settings', d1, ['--setting-sources', '', '--agents', AGENTS])
  # 2: --agents with default setting sources
  d2 = root / 'p2'; d2.mkdir(exist_ok=True)
  probe('agents-flag-default-settings', d2, ['--agents', AGENTS])
  # 3: project .claude/agents/scout.md with project settings source only
  d3 = root / 'p3'; (d3 / '.claude' / 'agents').mkdir(parents=True, exist_ok=True)
  (d3 / '.claude' / 'agents' / 'scout.md').write_text(
      '---\nname: scout\ndescription: Probe agent.\nmodel: claude-opus-5\neffort: low\n---\nYou are a probe.\n', encoding='utf-8')
  probe('project-agent-file-project-source', d3, ['--setting-sources', 'project'])


if len(sys.argv) == 2:
    basic()

# 4/5: does a `tools` list break registration? (the trial's smoke passed tools including PowerShell)
if len(sys.argv) > 2 and sys.argv[2] == 'tools':
    for label, tools in (('tools-with-powershell', ['Read', 'Glob', 'Grep', 'Edit', 'Write', 'Bash', 'PowerShell']),
                         ('tools-without-powershell', ['Read', 'Glob', 'Grep', 'Edit', 'Write', 'Bash'])):
        dd = root / label; dd.mkdir(exist_ok=True)
        a = json.loads(AGENTS); a['scout']['tools'] = tools
        probe(label, dd, ['--setting-sources', '', '--agents', json.dumps(a)])
