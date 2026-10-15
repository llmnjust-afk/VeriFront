#!/usr/bin/env python3
"""Runs from the repository root; writes figures/*.png.

Publication-grade Fig 2/3/4 for VeriFront paper. Okabe-Ito palette, Wilson CIs."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from math import sqrt

C = {'resample': '#0072B2', 'mini': '#E69F00', 'ds': '#009E73', 'qwen': '#D55E00'}
plt.rcParams.update({'font.size': 8.5, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.dpi': 200, 'savefig.bbox': 'tight'})

def wilson(x, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = x / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0, c-h), min(1, c+h))

def fig2():
    inv = pd.read_csv('reports/pilot/p2_run_inventory.csv')
    inv = inv[(inv.sandbox_invalid == 0) & (inv.status == 'completed')]
    inv['p6'] = inv.parent_stamp.astype(str).str[-6:]
    scans = {'305791': ('t40', 5), '321913': ('t60', 9)}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    for ax, (p6, (tname, nsteps)) in zip(axes, scans.items()):
        sub = inv[(inv.p6 == p6) & (inv.edit_step <= nsteps)]
        g = sub.groupby(['edit_step', 'arm']).Y.agg(['sum', 'count']).reset_index()
        for arm in ['resample', 'mini', 'ds', 'qwen']:
            s = g[g.arm == arm]
            if s.empty: continue
            lo, hi = zip(*[wilson(r['sum'], r['count']) for _, r in s.iterrows()])
            sr = s['sum']/s['count']
            yerr = np.maximum([np.array(sr)-lo, hi-np.array(sr)], 0)
            ax.errorbar(s.edit_step, sr, yerr=yerr,
                        fmt='o-', ms=3.5, lw=1.3,
                        alpha=1.0 if arm == 'resample' else 0.85,
                        color=C[arm], capsize=2, label=arm, zorder=3 if arm == 'resample' else 2)
        # step classification band by resample baseline
        rs = g[g.arm == 'resample'].set_index('edit_step')
        for t, row in rs.iterrows():
            sr = row['sum']/row['count']
            col = '#F6D8C3' if sr == 0 else ('#DDEBDD' if sr < 1 else '#FFFFFF')
            ax.axvspan(t-0.5, t+0.5, color=col, zorder=0)
        ax.set_title(f'{tname} (parent {"305791" if p6=="305791" else "321913"})', fontsize=9)
        ax.set_xlabel('step'); ax.set_ylim(-0.03, 1.06); ax.set_xticks(range(1, nsteps+1))
    axes[0].set_ylabel('step success rate')
    handles, labels = axes[0].get_legend_handles_labels()
    handles += [mpatches.Patch(color='#FFFFFF', ec='#BBB', label='healthy (res=1)'),
                mpatches.Patch(color='#DDEBDD', label='capability-dep.'),
                mpatches.Patch(color='#F6D8C3', label='cliff (res=0)')]
    fig.legend(handles=handles, frameon=False, fontsize=6.8, ncol=7,
               loc='upper center', bbox_to_anchor=(0.5, 1.06))
    fig.savefig('figures/fig2_scan_profile.png'); plt.close(fig)
    print('fig2 done')

def fig3():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
    # (a) DiD bars, two calibres
    ax = axes[0]
    arms = ['mini', 'ds', 'qwen']; pooled = [-0.21, -0.25, -0.71]; common = [-0.24, -0.27, -0.63]
    x = np.arange(3); w = 0.38
    ax.bar(x-w/2, pooled, w, color='#56B4E9', label='pooled ctl')
    ax.bar(x+w/2, common, w, color='#0072B2', label='common ctl (10)')
    ax.set_xticks(x); ax.set_xticklabels(arms); ax.axhline(0, color='k', lw=0.6)
    ax.set_ylabel('DiD: extra damage at signal steps'); ax.legend(frameon=False, fontsize=6.5)
    ax.set_title('(a) step-specific damage', fontsize=9)
    # (b) error types at signal points
    ax = axes[1]
    types = ['ok', 'sem.', 'idio.', 'no\ncode']
    mat = {'resample': [38, 0, 0, 0], 'mini': [30, 2, 1, 2], 'ds': [30, 2, 0, 6], 'qwen': [22, 5, 25, 0]}
    bottom = np.zeros(4)
    for arm in ['resample', 'mini', 'ds', 'qwen']:
        vals = np.array(mat[arm], float)
        ax.bar(types, vals, bottom=bottom, color=C[arm], label=arm, width=0.62)
        bottom += vals
    ax.set_ylabel('signal-point runs'); ax.legend(frameon=False, fontsize=6.5, loc='upper right')
    ax.set_title('(b) edit-step error families', fontsize=9)
    # (c) intervention effects forest
    ax = axes[2]
    items = [('structured feedback\n(frontier)', 0.21), ('structured feedback\n(mini)', 0.09),
             ('suffix takeover\n(t40s4, mini)', -0.19), ('suffix takeover\n(t60s4, mini)', -0.38),
             ('8B$\\to$14B pooled', 0.08)]
    ys = np.arange(len(items))
    for y, (lab, d) in zip(ys, items):
        col = '#009E73' if d > 0 else '#D55E00'
        ax.plot([d], [y], 'o', color=col, ms=5)
        ax.plot([0, d], [y, y], color=col, lw=1)
    ax.axvline(0, color='k', lw=0.6, ls=':')
    ax.set_yticks(ys); ax.set_yticklabels([i[0] for i in items], fontsize=6.5)
    ax.set_xlabel('$\\Delta$SR vs baseline'); ax.set_title('(c) interventions', fontsize=9)
    fig.tight_layout(); fig.savefig('figures/fig3_mechanisms.png'); plt.close(fig)
    print('fig3 done')

def fig4():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
    fp = pd.read_csv('reports/pilot/p2c_fold_predictions.csv')
    # (a) M0 vs M1 abs error by observation, paired
    ax = axes[0]
    e0 = (fp.p0 - fp.Y).abs(); e1 = (fp.p1 - fp.Y).abs()
    ax.scatter(e0 + np.random.uniform(-.012, .012, len(fp)), e1 + np.random.uniform(-.012, .012, len(fp)),
               s=7, alpha=0.45, color='#0072B2', edgecolor='none')
    lim = [0, max(e0.max(), e1.max())*1.02]; ax.plot(lim, lim, 'k--', lw=0.7)
    ax.set_xlabel('|error| M0 (controls only)'); ax.set_ylabel('|error| M1 (V+C)')
    ax.set_title('(a) paired fold errors (LOTO)', fontsize=9)
    # (b) per-arm improvement bars
    ax = axes[1]
    imp = fp.groupby('arm').apply(lambda g: ((g.p0-g.Y).abs()-(g.p1-g.Y).abs()).mean(), include_groups=False)
    imp = imp.reindex(['resample', 'mini', 'ds', 'qwen'])
    n = fp.arm.value_counts()
    ax.bar(imp.index, imp.values, color=[C[a] for a in imp.index])
    ax.axhline(0, color='k', lw=0.6); ax.set_ylim(-0.008, 0.042)
    for i, a in enumerate(imp.index):
        va = 'bottom' if imp[a] >= 0 else 'top'
        off = 0.0008 if imp[a] >= 0 else -0.0008
        ax.text(i, imp[a]+off, f'n={n[a]}', ha='center', va=va, fontsize=6.5)
    ax.set_ylabel('|error| improvement (M1$-$M0)'); ax.set_title('(b) gain by arm', fontsize=9)
    # (c) ridge coefficients
    ax = axes[2]
    names = ['stratum: cliff', 'role: critical', 'F3 feedback', 'F1 objective', 'F2 artifact',
             'F4 budget', 'F5 state-dep.', 'F6 recover.', 'arm: qwen', 'step no.']
    vals = [-0.411, 0.295, -0.540, -0.292, 0.252, 0.275, -0.166, 0.032, 0.029, -0.005]
    order = np.argsort(np.abs(vals))
    ax.barh([names[i] for i in order], [vals[i] for i in order],
            color=['#0072B2' if vals[i] > 0 else '#D55E00' for i in order])
    ax.axvline(0, color='k', lw=0.6); ax.set_xlabel('Ridge coefficient (full-data fit)')
    ax.set_title('(c) M1 coefficients', fontsize=9)
    fig.tight_layout(); fig.savefig('figures/fig4_prediction.png'); plt.close(fig)
    print('fig4 done')

if __name__ == '__main__':
    fig2(); fig3(); fig4()
