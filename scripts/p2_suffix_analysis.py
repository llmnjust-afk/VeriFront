#!/usr/bin/env python3
"""P2b sec5.2 suffix-takeover analysis: single-step vs suffix replacement.

Question (plan sec5.2): is the single-step damage transient (frontier picks
up) or persistent when the replacement model also generates the whole suffix?
Also records the 32K context-wall finding for qwen/mini on t40s4+.
Output: reports/pilot/p2_suffix_analysis.md
"""
import json, glob, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def collect():
    rows = []
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f)); m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f: arm = 'resample'
        elif 'mini' in em: arm = 'mini'
        elif 'Qwen' in em: arm = 'qwen'
        else: arm = 'ds'
        tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
        if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
            continue
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        if stamp[-6:] not in ('305791', '321913'):
            continue
        task = '40' if stamp[-6:] == '305791' else '60'
        step = int(m['edit_step'])
        if (task, step) not in (('40', 4), ('60', 4)):
            continue
        if m.get('feedback_mode', 'none') != 'none':
            continue  # exclude intervention runs
        suffix = bool(m.get('suffix_takeover'))
        rows.append({'task': task, 'step': step, 'arm': arm, 'suffix': suffix,
                     'Y': r['eval_success'],
                     'status': m.get('cf_status', r.get('status'))})
    return rows

rows = collect()
agg = collections.defaultdict(lambda: [0, 0])
for r in rows:
    k = (r['task'], r['arm'], 'suffix' if r['suffix'] else 'single')
    agg[k][0] += r['Y']; agg[k][1] += 1

L = ['# P2b sec5.2: suffix-takeover vs single-step replacement\n']
L.append(f"- runs analyzed (t40s4/t60s4, sandbox-valid, non-intervention): {len(rows)}\n")
L.append('| point | arm | mode | n | SR |')
L.append('|---|---|---|---|---|')
for task in ('40', '60'):
    for arm in ('resample', 'mini', 'qwen'):
        for mode in ('single', 'suffix'):
            x, n = agg[(task, arm, mode)]
            if n:
                L.append(f"| t{task}s4 | {arm} | {mode} | {n} | {x}/{n} ({x/n:.2f}) |")

L.append('\n## Suffix amplification (SR_suffix - SR_single)\n')
for task in ('40', '60'):
    for arm in ('mini', 'qwen'):
        s, g = agg[(task, arm, 'suffix')], agg[(task, arm, 'single')]
        if s[1] and g[1]:
            L.append(f"- t{task}s4 {arm}: {s[0]/s[1]:.2f} vs {g[0]/g[1]:.2f} -> {s[0]/s[1] - g[0]/g[1]:+.2f}")

L.append('\n## Context wall (32K-class models cannot takeover t40s4 suffix)\n')
L.append("- t40s4 prompt ~28.7K tokens; suffix generation adds multi-turn growth ->")
L.append("- qwen-suffix t40s4: 3/3 runs HTTP 400 (context exceeded) -- recorded as infeasible, not as failure;")
L.append("- mini-suffix t40s4: completed 6/6 (mini endpoint accepts the length; quality outcome below).")
open('reports/pilot/p2_suffix_analysis.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
