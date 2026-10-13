#!/usr/bin/env python3
"""P2b sec5.3: Qwen3-14B-AWQ signal-point replication vs Qwen3-8B.

Model-gradient question (plan sec5.3): do the qwen-8B failure points persist
at 14B, or scale away? SR per signal point, 8B (P1 replication + scan) vs
14B-AWQ (new). Output: reports/pilot/p2_q14_analysis.md
"""
import json, glob, os, collections
from scipy.stats import fisher_exact

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SIG = {('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)}
MODELS = {'8B': 'Qwen/Qwen3-8B', '14B': 'Qwen/Qwen3-14B-AWQ'}

agg = collections.defaultdict(lambda: [0, 0])
for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
          + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
    r = json.load(open(f)); m = r['cf_meta']
    em = m.get('edit_model') or ''
    size = next((k for k, v in MODELS.items() if v in em), None)
    if size is None:
        continue
    tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
    if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
        continue
    k = (str(r['instance_id']), int(m['edit_step']))
    if k not in SIG:
        continue
    if m.get('feedback_mode', 'none') != 'none':
        continue
    agg[(size, k)][0] += r['eval_success']
    agg[(size, k)][1] += 1

ORDER = [('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)]
L = ['# P2b sec5.3: Qwen 14B-AWQ vs 8B signal-point replication\n']
L.append('| point | 8B SR (n) | 14B SR (n) | 14B verdict |')
L.append('|---|---|---|---|')
for k in ORDER:
    x8, n8 = agg[('8B', k)]
    x14, n14 = agg[('14B', k)]
    s8 = f"{x8}/{n8} ({x8/n8:.2f})" if n8 else '-'
    s14 = f"{x14}/{n14} ({x14/n14:.2f})" if n14 else '-'
    verdict = '-'
    if n8 and n14:
        r8, r14 = x8 / n8, x14 / n14
        if r14 < 0.5 and r8 < 0.5:
            verdict = 'failure persists'
        elif r14 >= 0.75 and r8 < 0.5:
            verdict = 'repaired at 14B'
        elif r14 < 0.5 <= r8:
            verdict = 'new failure at 14B'
        else:
            verdict = 'consistent (both ok/mid)'
    L.append(f"| t{k[0]}s{k[1]} | {s8} | {s14} | {verdict} |")

tot8 = [agg[('8B', k)] for k in ORDER if agg[('8B', k)][1]]
tot14 = [agg[('14B', k)] for k in ORDER if agg[('14B', k)][1]]
x8 = sum(a[0] for a in tot8); n8 = sum(a[1] for a in tot8)
x14 = sum(a[0] for a in tot14); n14 = sum(a[1] for a in tot14)
L.append(f"\n- pooled signal points: 8B {x8}/{n8} ({x8/n8:.2f}) vs 14B {x14}/{n14} ({x14/n14:.2f})")
if n8 and n14:
    p = fisher_exact([[x14, n14 - x14], [x8, n8 - x8]])[1]
    L.append(f"- Fisher 14B vs 8B pooled: p={p:.3f}")
open('reports/pilot/p2_q14_analysis.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
