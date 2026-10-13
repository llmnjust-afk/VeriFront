#!/usr/bin/env python3
"""P2b: full-step scan profile aggregation + figure (plan §5.1)."""
import json, glob, os, csv, collections

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SCANNED = {'305791': ('40', 5), '321913': ('60', 9)}
ARMS = [('resample', '#444444', '-'), ('mini', '#E69F00', '-'),
        ('ds', '#56B4E9', '-'), ('qwen', '#009E73', '-')]

def load():
    pts = {}
    for p in json.load(open('reports/annotation/cf_points.json'))['points']:
        pts[(str(p['task_id']), int(p['step_no']), p['parent_stamp'])] = p
    rows = []
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f)); m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f: arm = 'resample'
        elif 'mini' in em: arm = 'mini'
        elif 'Qwen' in em: arm = 'qwen'
        else: arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        if stamp[-6:] not in SCANNED:
            continue
        tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
        if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
            continue
        task, nsteps = SCANNED[stamp[-6:]]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        role = pts[k]['role'] if k in pts else 'scan-only'
        rows.append({'task': task, 'step': int(m['edit_step']), 'arm': arm,
                     'Y': r['eval_success'], 'parent': stamp[-6:], 'role': role,
                     'status': r['status']})
    return rows

def main():
    rows = load()
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        agg[r['task']][ (r['step'], r['arm']) ].append(r['Y'])

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2))
    tbl = ['# P2b full-step scan profile (SR per takeover step; plan §5.1)\n']
    for ax, task in zip(axes, ['40', '60']):
        nsteps = SCANNED['305791' if task == '40' else '321913'][1]
        tbl.append(f"\n## t{task} (parent {'305791' if task=='40' else '321913'})\n")
        tbl.append('| step | ' + ' | '.join(a for a, _, _ in ARMS) + ' |')
        tbl.append('|---|' + '---|' * len(ARMS))
        for arm, color, ls in ARMS:
            xs, ys = [], []
            for t in range(1, nsteps + 1):
                v = agg[task].get((t, arm), [])
                if v:
                    xs.append(t); ys.append(sum(v) / len(v))
            if xs:
                ax.plot(xs, ys, marker='o', ms=4, lw=1.6, color=color, ls=ls,
                        label=arm if task == '40' else None)
        for t in range(1, nsteps + 1):
            line = [f'| {t} ']
            for arm, _, _ in ARMS:
                v = agg[task].get((t, arm), [])
                line.append(f'| {sum(v)}/{len(v)} ' if v else '| - ')
            tbl.append(''.join(line) + '|')
        par = '305791' if task == '40' else '321913'
        ax.set_title('task sab-' + task + ' (parent ' + par + ')', fontsize=11)
        ax.set_xlabel('takeover step t')
        ax.set_ylabel('success rate (Y=1)')
        ax.set_xticks(range(1, nsteps + 1))
        ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.3, lw=0.5)
        # mark P1 signal steps
        for t, lbl in ([(4, 'P1 sig') , (2, 'P1 sig')] if task == '40' else [(4, 'P1 sig'), (6, 'P1 sig')]):
            if t <= nsteps:
                ax.axvline(t, color='#CC79A7', ls=':', lw=1)
                ax.text(t + 0.05, 0.02, lbl, fontsize=7.5, color='#CC79A7')
    axes[0].legend(loc='lower left', fontsize=9, framealpha=0.9)
    fig.suptitle('Step-wise capability-dependence profile (full-step counterfactual scan)', fontsize=12, y=1.02)
    fig.tight_layout()
    os.makedirs('figures', exist_ok=True)
    fig.savefig('figures/p2_scan_profile.png', dpi=200, bbox_inches='tight')
    print('figure saved: figures/p2_scan_profile.png')
    n_total = len(rows)
    tbl.append(f"\n- scanned runs (sandbox-valid): {n_total}")
    with open('reports/pilot/p2_scan_profile.md', 'w') as f:
        f.write('\n'.join(tbl) + '\n')
    print('table saved: reports/pilot/p2_scan_profile.md')

if __name__ == '__main__':
    main()
