#!/usr/bin/env python3
"""P2b sec5.5 v2 analysis: validator-triggered retry on t40s4 (exit_or_validator).

Compares trigger rates and outcomes across the 2x2 grid under the v2 trigger,
against the v1 (exit_code) trigger on the same step.
Output: reports/pilot/p2_feedback_intervention_v2.md
"""
import json, glob, os, collections
from scipy.stats import fisher_exact

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

rows = []
for f in (glob.glob('runs/sab_40/cf_frontier_resample/*/result.json')
          + glob.glob('runs/sab_40/cf_local_replace/*/result.json')):
    r = json.load(open(f)); m = r['cf_meta']
    if m['edit_step'] != 4 or str(r['instance_id']) != '40':
        continue
    tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
    if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
        continue
    fb = m.get('feedback_mode', 'none')
    em = m.get('edit_model') or ''
    if fb == 'none':
        continue  # P1/scan data, not intervention
    arm = 'resample' if m['arm'] == 'cf_frontier_resample' else ('mini' if 'mini' in em else 'qwen')
    cell = {('resample', 'original_retry'): 'A', ('resample', 'structured'): 'B',
            ('mini', 'original_retry'): 'C', ('mini', 'structured'): 'D',
            ('qwen', 'structured'): 'Qs', ('qwen', 'original_retry'): 'Qo'}[(arm, fb)]
    trig = m.get('trigger', 'exit_code')
    rows.append({'cell': cell, 'trig': trig, 'Y': r['eval_success'],
                 'retry': bool(m.get('retry_used')),
                 'vrep_ok': (m.get('validator_report') or {}).get('ok')})

L = ['# P2b sec5.5 v2: validator-triggered retry on t40s4\n']

for trig in ['exit_code', 'exit_or_validator']:
    sub = [r for r in rows if r['trig'] == trig]
    L.append(f"\n## Trigger = {trig} (n={len(sub)} runs)\n")
    L.append('| cell | n | SR | retry fired | validator-fail at takeover |')
    L.append('|---|---|---|---|---|')
    for c in ['A', 'B', 'C', 'D', 'Qs', 'Qo']:
        s = [r for r in sub if r['cell'] == c]
        if not s: continue
        n = len(s); x = sum(r['Y'] for r in s); rt = sum(r['retry'] for r in s)
        # validator-fail: retry fired without exec error OR report ok False present
        vf = sum(1 for r in s if r['retry'] and r['vrep_ok'] is False)
        L.append(f"| {c} | {n} | {x}/{n} ({x/n:.2f}) | {rt}/{n} | {vf}/{n} |")

v1 = {(r['cell']): [r for r in rows if r['trig'] == 'exit_code' and r['cell'] == r['cell']] for r in rows}
v2c = {c: [r for r in rows if r['trig'] == 'exit_or_validator' and r['cell'] == c] for c in 'ABCD'}
L.append('\n## v2 vs v1 comparison (same step t40s4)\n')
L.append('| cell | v1 trigger rate | v2 trigger rate | v1 SR | v2 SR |')
L.append('|---|---|---|---|---|')
for c in 'ABCD':
    v1s = [r for r in rows if r['trig'] == 'exit_code' and r['cell'] == c]
    v2s = v2c[c]
    t1 = f"{sum(r['retry'] for r in v1s)}/{len(v1s)}" if v1s else '-'
    t2 = f"{sum(r['retry'] for r in v2s)}/{len(v2s)}" if v2s else '-'
    s1 = f"{sum(r['Y'] for r in v1s)}/{len(v1s)}" if v1s else '-'
    s2 = f"{sum(r['Y'] for r in v2s)}/{len(v2s)}" if v2s else '-'
    L.append(f"| {c} | {t1} | {t2} | {s1} | {s2} |")

# mini focus: rescue analysis
mini_v2 = v2c['C'] + v2c['D']
triggered = [r for r in mini_v2 if r['retry']]
L.append(f"\n## mini rescue analysis (v2)\n")
L.append(f"- mini v2 runs: {len(mini_v2)}; retry fired: {len(triggered)}; of those eventually succeeded: {sum(r['Y'] for r in triggered)}")
cd = [r for r in v2c['C']]; dd = [r for r in v2c['D']]
if cd and dd:
    p = fisher_exact([[sum(r['Y'] for r in dd), len(dd) - sum(r['Y'] for r in dd)],
                      [sum(r['Y'] for r in cd), len(cd) - sum(r['Y'] for r in cd)]])[1]
    L.append(f"- D vs C (v2): {sum(r['Y'] for r in dd)}/{len(dd)} vs {sum(r['Y'] for r in cd)}/{len(cd)}, Fisher p={p:.3f}")

open('reports/pilot/p2_feedback_intervention_v2.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
