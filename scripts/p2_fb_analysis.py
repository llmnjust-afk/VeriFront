#!/usr/bin/env python3
"""P2b sec5.5 feedback-intervention pilot analysis (2x2: arm x feedback).

Grid: A=resample+original_retry, B=resample+structured,
      C=mini+original_retry,  D=mini+structured.
Steps: t40s4@305791, t60s4@321913, t60s2@321913. Plus 2 qwen dry-runs
(t40s4, structured/original_retry) reported separately.
Output: reports/pilot/p2_feedback_intervention_results.md
"""
import json, glob, os, collections
from scipy.stats import fisher_exact

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def cell_of(m):
    fb = m.get('feedback_mode', 'none')
    if fb == 'none':
        return None
    em = m.get('edit_model') or ''
    arm = 'resample' if m['arm'] == 'cf_frontier_resample' else ('mini' if 'mini' in em else ('qwen' if 'Qwen' in em else '?'))
    if fb == 'original_retry':
        return ('A' if arm == 'resample' else ('C' if arm == 'mini' else 'Q-orig'))
    if fb == 'structured':
        return ('B' if arm == 'resample' else ('D' if arm == 'mini' else 'Q-struct'))
    return None

agg = collections.defaultdict(lambda: {'n': 0, 'succ': 0, 'retry': 0, 'retry_succ': 0, 'retry_n': 0,
                                       'per_step': collections.defaultdict(lambda: [0, 0])})
for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
          + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
    r = json.load(open(f)); m = r['cf_meta']
    c = cell_of(m)
    if c is None: continue
    tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
    if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
        continue
    a = agg[c]
    a['n'] += 1
    a['succ'] += r['eval_success']
    if m.get('retry_used'):
        a['retry'] += 1
        a['retry_n'] += 1
        a['retry_succ'] += r['eval_success']
    k = (str(r['instance_id']), m['edit_step'])
    a['per_step'][k][0] += r['eval_success']
    a['per_step'][k][1] += 1

L = ['# P2b sec5.5 feedback-intervention pilot: results\n']
L.append(f"- total intervention runs: {sum(a['n'] for a in agg.values())} (2 qwen dry-runs reported separately)\n")

L.append('## Per-cell summary (pooled over 3 steps)\n')
L.append('| cell | arm x feedback | n | SR | retry-triggered | SR|triggered |')
L.append('|---|---|---|---|---|---|')
names = {'A': 'resample x bare-retry', 'B': 'resample x structured',
         'C': 'mini x bare-retry', 'D': 'mini x structured',
         'Q-orig': 'qwen x bare-retry (dry)', 'Q-struct': 'qwen x structured (dry)'}
for c in ['A', 'B', 'C', 'D', 'Q-struct', 'Q-orig']:
    a = agg.get(c)
    if not a: continue
    sr = a['succ'] / a['n']
    rs = f"{a['retry_succ']}/{a['retry_n']}" if a['retry_n'] else '-'
    L.append(f"| {c} | {names[c]} | {a['n']} | {a['succ']}/{a['n']} ({sr:.2f}) | {a['retry']}/{a['n']} | {rs} |")

L.append('\n## Per-step detail\n')
L.append('| cell | t40s4 | t60s4 | t60s2 |')
L.append('|---|---|---|---|')
for c in ['A', 'B', 'C', 'D', 'Q-struct', 'Q-orig']:
    a = agg.get(c)
    if not a: continue
    row = [f'| {c} ']
    for k in [('40', 4), ('60', 4), ('60', 2)]:
        x, n = a['per_step'].get(k, [0, 0])
        row.append(f'| {x}/{n} ' if n else '| - ')
    row.append('|')
    L.append(''.join(row))

def fisher2(c1, c2):
    a1, a2 = agg.get(c1), agg.get(c2)
    if not a1 or not a2: return None
    p = fisher_exact([[a1['succ'], a1['n'] - a1['succ']],
                      [a2['succ'], a2['n'] - a2['succ']]])[1]
    return p

L.append('\n## Main test: feedback effect by arm (pooled)\n')
for pair, label in [(('D', 'C'), 'mini: structured vs bare-retry (D vs C)'),
                    (('B', 'A'), 'resample: structured vs bare-retry (B vs A)')]:
    a1, a2 = agg.get(pair[0]), agg.get(pair[1])
    if not a1 or not a2: continue
    d = a1['succ'] / a1['n'] - a2['succ'] / a2['n']
    p = fisher2(pair[0], pair[1])
    L.append(f"- {label}: ΔSR = {d:+.2f} (Fisher p={p:.3f})")

aA, aB, aC, aD = agg.get('A'), agg.get('B'), agg.get('C'), agg.get('D')
if all(x for x in (aA, aB, aC, aD)):
    did_fb = (aD['succ'] / aD['n'] - aC['succ'] / aC['n']) - (aB['succ'] / aB['n'] - aA['succ'] / aA['n'])
    L.append(f"\n- **Interaction (D-C) - (B-A) = {did_fb:+.2f}**")
    L.append("  - > 0 supports 'feedback-missing' component (structured feedback helps weak models more);")
    L.append("  - ~ 0 / < 0 supports 'capability-missing' component.")

L.append('\n## Retry-window mechanics\n')
for c in ['A', 'B', 'C', 'D']:
    a = agg.get(c)
    if not a: continue
    L.append(f"- {c}: retry triggered {a['retry']}/{a['n']}; post-retry step rescued to eventual success in {a['retry_succ']}/{a['retry_n']} triggered runs")

open('reports/pilot/p2_feedback_intervention_results.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
