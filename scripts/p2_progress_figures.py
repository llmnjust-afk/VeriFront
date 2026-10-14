#!/usr/bin/env python3
"""Generate progress-summary figures from P1/P2 data (colorblind-safe Okabe-Ito)."""
import json, glob, os, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

C = {'resample': '#555555', 'mini': '#E69F00', 'ds': '#56B4E9', 'qwen': '#009E73'}

def collect():
    pts = {}
    for p in json.load(open('reports/annotation/cf_points.json'))['points']:
        pts[(str(p['task_id']), int(p['step_no']), p['parent_stamp'])] = p
    agg = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    crash = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    sig = {('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)}
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f)); m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f: arm = 'resample'
        elif 'mini' in em: arm = 'mini'
        elif 'Qwen' in em: arm = 'qwen'
        else: arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        if k not in pts: continue
        tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
        if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
            continue
        grp = 'sig' if (k[0], k[1]) in sig else 'ctl'
        c = agg[arm][grp]; c[0] += r['eval_success']; c[1] += 1
        cc = crash[arm][grp]; cc[1] += 1
    return pts, agg, crash

def fig_signal_points(pts):
    sig6 = [('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)]
    labels, data = [], {a: [] for a in C}
    for t, s in sig6:
        # merge dual instances of (40,2)
        ks = [k for k in pts if k[0] == t and k[1] == s]
        if not ks: continue
        labels.append(f"t{t}s{s}")
    arms_x = {a: [] for a in C}
    # recompute per point from result files
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f)); m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f: arm = 'resample'
        elif 'mini' in em: arm = 'mini'
        elif 'Qwen' in em: arm = 'qwen'
        else: arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        if k not in pts: continue
        if (k[0], k[1]) not in {tuple(x) for x in sig6}: continue
        tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
        if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
            continue
        per[(k[0], k[1])][arm].append(r['eval_success'])
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    W = 0.2
    xs = np.arange(len(labels))
    for i, (arm, color) in enumerate(C.items()):
        vals = []
        for lb in labels:
            t, s = lb[1:].split('s')
            v = per[(t, int(s))].get(arm, [])
            vals.append(sum(v) / len(v) if v else np.nan)
        bars = ax.bar(xs + (i - 1.5) * W, vals, W, color=color, label=arm, edgecolor='white', lw=0.4)
    ax.set_xticks(xs); ax.set_xticklabels(labels)
    ax.set_ylabel('success rate'); ax.set_ylim(0, 1.08)
    ax.set_title('Six signal points: four-arm success rates (P1 + P2 replication, sandbox-valid runs)')
    ax.legend(ncol=4, fontsize=9, loc='upper right')
    ax.grid(axis='y', alpha=0.3, lw=0.5)
    fig.tight_layout(); fig.savefig('figures/p2_fig_signal_points.png', dpi=200); plt.close(fig)

def fig_did(agg):
    ctl10 = {('18', 1), ('18', 2), ('18', 3), ('35', 1), ('37', 10),
             ('44', 4), ('58', 2), ('60', 8), ('85', 1), ('45', 1)}
    sig = {('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)}
    a2 = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    pts = {}
    for p in json.load(open('reports/annotation/cf_points.json'))['points']:
        pts[(str(p['task_id']), int(p['step_no']), p['parent_stamp'])] = p
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f)); m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f: arm = 'resample'
        elif 'mini' in em: arm = 'mini'
        elif 'Qwen' in em: arm = 'qwen'
        else: arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        if k not in pts: continue
        grp = 'sig' if (k[0], k[1]) in sig else ('ctl10' if (k[0], k[1]) in ctl10 else None)
        if grp is None: continue
        tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
        if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
            continue
        c = a2[arm][grp]; c[0] += r['eval_success']; c[1] += 1
    arms = ['mini', 'ds', 'qwen']
    dids, srs, crs = [], [], []
    for a in arms:
        s_, c_ = a2[a]['sig'], a2[a]['ctl10']
        bs, bc = a2['resample']['sig'], a2['resample']['ctl10']
        d_s = s_[0] / s_[1] - bs[0] / bs[1]
        d_c = c_[0] / c_[1] - bc[0] / bc[1]
        dids.append(d_s - d_c); srs.append(d_s); crs.append(d_c)
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    y = np.arange(len(arms))
    colors = [C[a] for a in arms]
    ax.barh(y, dids, 0.55, color=colors)
    for i, (d, s, c) in enumerate(zip(dids, srs, crs)):
        ax.text(d - 0.02 if d < 0 else d + 0.02, i, f"{d:+.2f}", va='center',
                ha='right' if d < 0 else 'left', fontsize=10, fontweight='bold')
        ax.text(0.02, i + 0.28, f"dSR_sig={s:+.2f}, dSR_ctl={c:+.2f}", fontsize=7.5, color='#333')
    ax.set_yticks(y); ax.set_yticklabels(arms)
    ax.axvline(0, color='k', lw=0.8)
    ax.set_xlabel('DiD_common = dSR(signal steps) - dSR(control steps)')
    ax.set_title('Step-specific extra damage per replacement model\n(common 10 control points; more negative = stronger step-specific dependence)')
    ax.set_xlim(-0.75, 0.45)
    ax.grid(axis='x', alpha=0.3, lw=0.5)
    fig.tight_layout(); fig.savefig('figures/p2_fig_did.png', dpi=200); plt.close(fig)

def fig_tiers(crash):
    arms = ['resample', 'mini', 'ds', 'qwen']
    # edit-step crash rate from mechanism annotations
    rows = list(csv.DictReader(open('reports/pilot/p2_mechanism_annotations.csv')))
    sig = {('60', '6'), ('85', '2'), ('40', '4'), ('92', '1'), ('60', '4'), ('40', '2')}
    cnt = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for r in rows:
        grp = 'sig' if (r['task'], r['edit_step']) in sig else 'ctl'
        c = cnt[r['arm']][grp]; c[1] += 1
        if r['edit_error_type'] not in ('none', 'no_code', 'sandbox_invalid'):
            c[0] += 1
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = np.arange(len(arms)); W = 0.35
    sig_rates = [cnt[a]['sig'][0] / cnt[a]['sig'][1] if cnt[a]['sig'][1] else 0 for a in arms]
    ctl_rates = [cnt[a]['ctl'][0] / cnt[a]['ctl'][1] if cnt[a]['ctl'][1] else 0 for a in arms]
    ax.bar(x - W / 2, sig_rates, W, color='#0072B2', label='signal points')
    ax.bar(x + W / 2, ctl_rates, W, color='#CC79A7', label='control points')
    for i, (s, c) in enumerate(zip(sig_rates, ctl_rates)):
        ax.text(i - W / 2, s + 0.02, f"{s:.0%}", ha='center', fontsize=9)
        ax.text(i + W / 2, c + 0.02, f"{c:.0%}", ha='center', fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(arms)
    ax.set_ylabel('edit-step execution crash rate'); ax.set_ylim(0, 0.72)
    ax.set_title('Three-tier failure structure: qwen fails at execution level everywhere;\nmini/ds fail semantically (code runs, output wrong)')
    ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3, lw=0.5)
    fig.tight_layout(); fig.savefig('figures/p2_fig_tiers.png', dpi=200); plt.close(fig)

import csv
pts, agg, crash = collect()
fig_signal_points(pts)
fig_did(agg)
fig_tiers(crash)
print('figures written')
