#!/usr/bin/env python3
"""P2b sec5.4: statistical hardening + protocol-retry experiment.

Part A: signal-point arm coverage after the fill-to-8 batch.
Part B: protocol-retry experiment -- budget_exhausted runs re-executed once
(RETRY) vs completed runs re-executed once (CTRL, extra-opportunity control).
Output: reports/pilot/p2_sec54_analysis.md
"""
import json, glob, os, collections
from scipy.stats import fisher_exact

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PTS = json.load(open('reports/annotation/cf_points.json'))['points']
SIG = {('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)}
KEYS = {(str(p['task_id']), int(p['step_no']), p['parent_stamp'])
        for p in PTS if (str(p['task_id']), int(p['step_no'])) in SIG}
CUT = 1791936000  # 2026-10-14 ~00:00 UTC: only today's retry-batch runs count

# ---- parse protocol-retry command list (order = execution order) ----
want = []
for line in open('/data/lab/protretry_cmds.txt'):
    line = line.strip()
    if not line.startswith('python3'):
        continue
    parent = line.split('--parent-run ')[1].split(' --at-step')[0]
    step = int(line.split('--at-step ')[1].split(' ')[0])
    armcode = 'resample' if 'frontier_resample' in line else 'replace'
    model = line.split('--edit-model ')[1].split(' ')[0] if '--edit-model ' in line else ''
    group = 'RETRY' if 'GROUP=RETRY' in line else 'CTRL'
    want.append((parent, step, armcode, model, group))

# ---- collect candidate runs from the retry window ----
rows = []
for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
          + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
    r = json.load(open(f)); m = r['cf_meta']
    if m.get('feedback_mode', 'none') != 'none' or bool(m.get('suffix_takeover')):
        continue
    em = m.get('edit_model') or ''
    arm = 'resample' if 'resample' in f else ('mini' if 'mini' in em else ('qwen' if 'Qwen' in em else 'ds'))
    parent = str(m['parent_run']).rstrip('/')
    tag = (parent, int(m['edit_step']),
           'resample' if arm == 'resample' else 'replace', em)
    mt = os.path.getmtime(f)
    if mt > CUT:
        rows.append({'tag': tag, 'status': r['status'], 'Y': r['eval_success'],
                     'mtime': mt})
rows.sort(key=lambda x: x['mtime'])

assigned, used = [], [False] * len(rows)
for (parent, step, armcode, model, group) in want:
    for i, x in enumerate(rows):
        if not used[i] and x['tag'] == (parent, step, armcode, model):
            x2 = dict(x); x2['group'] = group
            assigned.append(x2); used[i] = True
            break
retr = [x for x in assigned if x['group'] == 'RETRY']
ctrl = [x for x in assigned if x['group'] == 'CTRL']

L = ['# P2b sec5.4: statistical hardening + protocol retry\n']

L.append('\n## Part A: signal-point arm coverage after fill-to-8\n')
agg = collections.defaultdict(lambda: [0, 0])
for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
          + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
    r = json.load(open(f)); m = r['cf_meta']
    if m.get('feedback_mode', 'none') != 'none' or bool(m.get('suffix_takeover')):
        continue
    em = m.get('edit_model') or ''
    arm = 'resample' if 'resample' in f else ('mini' if 'mini' in em else ('qwen' if 'Qwen' in em else 'ds'))
    stamp = str(m['parent_run']).rsplit('/', 1)[-1]
    k = (str(r['instance_id']), int(m['edit_step']), stamp)
    if k not in KEYS:
        continue
    tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
    if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
        continue
    g = agg[(k[0], k[1], arm)]; g[0] += r['eval_success']; g[1] += 1
L.append('| point | resample | mini | ds | qwen | cells n>=8 |')
L.append('|---|---|---|---|---|---|')
for (t, s) in sorted({(k[0], k[1]) for k in agg}):
    row = []
    cov = 0
    for arm in ('resample', 'mini', 'ds', 'qwen'):
        x, n = agg[(t, s, arm)]
        row.append(f"{x}/{n}" + ("!" if n < 8 else ""))
        cov += (n >= 8)
    L.append(f"| t{t}s{s} | " + " | ".join(row) + f" | {cov}/4 |")

L.append('\n## Part B: protocol-retry experiment (16 planned re-executions)\n')
def summarize(g, name):
    if not g:
        L.append(f"- {name}: no runs matched")
        return
    n = len(g)
    prot_ok = sum(1 for x in g if x['status'] == 'completed')
    succ = sum(x['Y'] for x in g)
    L.append(f"- {name}: n={n}; protocol completed: {prot_ok}/{n}; final task success: {succ}/{n} ({succ/n:.2f})")
summarize(retr, 'RETRY (re-executed after budget_exhausted)')
summarize(ctrl, 'CTRL (re-executed after completed)')
if retr and ctrl:
    sr = sum(x['Y'] for x in retr) / len(retr)
    sc = sum(x['Y'] for x in ctrl) / len(ctrl)
    p = fisher_exact([[sum(x['Y'] for x in retr), len(retr) - sum(x['Y'] for x in retr)],
                      [sum(x['Y'] for x in ctrl), len(ctrl) - sum(x['Y'] for x in ctrl)]])[1]
    L.append(f"- RETRY vs CTRL final success: {sr:.2f} vs {sc:.2f} (Fisher p={p:.3f})")
    L.append("- reading: gap ~ 0 -> budget exhaustion is a random draw; gap < 0 -> correlates with low-quality output.")

open('reports/pilot/p2_sec54_analysis.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
