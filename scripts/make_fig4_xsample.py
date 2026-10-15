#!/usr/bin/env python3
"""Fig 4 (scale-up edition): 49-pt LOTO panels + 18-pt chemistry OOD panel."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C = {'resample': '#0072B2', 'mini': '#E69F00', 'ds': '#009E73', 'qwen': '#D55E00'}
plt.rcParams.update({'font.size': 8.5, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.dpi': 200, 'savefig.bbox': 'tight'})

fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))

# (a) paired fold errors, 49-pt LOTO
fp = pd.read_csv('p2c_xsample_loto_a49.csv')
ax = axes[0]
e0 = (fp.p_M0 - fp.Y).abs(); e1 = (fp.p_M1 - fp.Y).abs()
ax.scatter(e0 + np.random.uniform(-.012, .012, len(fp)), e1 + np.random.uniform(-.012, .012, len(fp)),
           s=7, alpha=0.45, color='#0072B2', edgecolor='none')
lim = [0, max(e0.max(), e1.max())*1.02]; ax.plot(lim, lim, 'k--', lw=0.7)
ax.set_xlabel('|error| M0 (controls only)'); ax.set_ylabel('|error| M1 (V+C)')
ax.set_title('(a) paired fold errors (LOTO)', fontsize=9)

# (b) per-arm improvement
ax = axes[1]
imp = fp.groupby('arm').apply(lambda g: ((g.p_M0-g.Y).abs()-(g.p_M1-g.Y).abs()).mean(), include_groups=False)
imp = imp.reindex(['resample', 'mini', 'ds', 'qwen'])
n = fp.arm.value_counts()
ax.bar(imp.index, imp.values, color=[C[a] for a in imp.index])
ax.axhline(0, color='k', lw=0.6)
for i, a in enumerate(imp.index):
    va = 'bottom' if imp[a] >= 0 else 'top'
    off = 0.0008 if imp[a] >= 0 else -0.0008
    ax.text(i, imp[a]*0.5, f'n={n[a]}', ha='center', va='center', fontsize=6.5, color='white', fontweight='bold')
ax.set_ylim(-0.002, 0.042)
ax.set_ylabel('|error| improvement (M1$-$M0)'); ax.set_title('(b) gain by arm (49 pts)', fontsize=9)

# (c) chemistry OOD: predictions vs outcome (18 pts, 72 obs)
hb = pd.read_csv('p2c_xsample_predictions_b18.csv')
ax = axes[2]
rng = np.random.default_rng(0)
for arm, col in C.items():
    g = hb[hb.arm == arm]
    ax.scatter(np.full(len(g), 0) + rng.uniform(-.10, .10, len(g)), g.p_M0, s=13, color=col, alpha=0.35, marker='o', edgecolor='none')
    ax.scatter(np.full(len(g), 1) + rng.uniform(-.10, .10, len(g)), g.p_M1, s=13, color=col, alpha=0.75, marker='^', edgecolor='none')
ax.axhline(0.5, color='k', lw=0.5, ls=':')
ax.set_xticks([0, 1]); ax.set_xticklabels(['Y = 0', 'Y = 1'])
ax.set_xlim(-0.45, 1.45); ax.set_ylabel('predicted P(success)')
m0 = [hb[hb.arm == a].p_M0.mean() for a in C]
m1 = [hb[hb.arm == a].p_M1.mean() for a in C]
ax.scatter([0]*4, m0, s=70, color=[C[a] for a in C], marker='o', zorder=5, edgecolor='white', linewidth=0.6)
ax.scatter([1]*4, m1, s=70, color=[C[a] for a in C], marker='^', zorder=5, edgecolor='white', linewidth=0.6)
ax.set_title('(c) chemistry held-out: model inversion\n($\\Delta\\rho$ = $-0.26$ vs flat arm-prior control)', fontsize=9)

fig.tight_layout(w_pad=1.6); fig.savefig('paper/latex/figures/fig4_prediction.png'); plt.close(fig)
print('fig4 xsample done')
