#!/usr/bin/env python3
"""Fig 1: VeriFront framework overview (step-level counterfactual replacement)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OK = '#0072B2'; OR = '#D55E00'; GR = '#009E73'; GY = '#7F7F7F'; BG = '#F5F5F5'
plt.rcParams.update({'font.size': 8, 'figure.dpi': 200, 'savefig.bbox': 'tight'})
fig, ax = plt.subplots(figsize=(10.0, 3.8))
ax.set_xlim(0, 104); ax.set_ylim(0, 40); ax.axis('off')


def box(x, y, w, h, fc, ec='none', lw=1.0, r=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.3,rounding_size={r}',
                                fc=fc, ec=ec, lw=lw))


def arrow(x1, y1, x2, y2, col=GY, lw=1.2, style='-'):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                 mutation_scale=9, color=col, lw=lw, linestyle=style))


def txt(x, y, s, size=8, ha='center', va='center', weight='normal', col='k'):
    ax.text(x, y, s, size=size, ha=ha, va=va, weight=weight, color=col)


# ---- Stage A: parent trajectory (left, x 2..20) ----
txt(11, 37, 'A | Frozen parent\ntrajectory', 8.5, weight='bold')
box(3.5, 7.5, 15, 25.5, BG, ec=GY, lw=0.8)
ys = [31, 28.6, 26.2, 23.8, 21.4, 19.0, 16.6, 14.2, 11.8, 9.6]
labels = ['setup', 'inspect', 'features', 'fit', 'diagnose', 'revise', 'predict', 'validate', 'write', 'report']
hot = {1, 6}
for i, y in enumerate(ys):
    col = OK if i in hot else 'white'
    ec = OK if i in hot else GY
    ax.add_patch(Circle((6.2, y), 0.85, fc=col, ec=ec, lw=1.0, zorder=3))
    if i < len(ys) - 1:
        ax.plot([6.2, 6.2], [y-0.85, ys[i+1]+0.85], color=GY, lw=0.8, zorder=1)
    txt(8.0, y, f't{i+1}  {labels[i]}', 6.0, ha='left',
        col=OK if i in hot else '#333333', weight='bold' if i in hot else 'normal')
txt(11, 4.6, 'frontier model runs full task;\ncontext + tool state frozen', 6.6)

# ---- Stage B: counterfactual replacement (x 24..45) ----
txt(34.5, 37, 'B | Step-level\ncounterfactual', 8.5, weight='bold')
box(24, 21.5, 21, 11.5, '#EAF2F8', ec=OK, lw=1.0)
txt(34.5, 30.4, 'surgical replacement of step t', 7.0)
txt(34.5, 25.6, 'context, tools, budget kept fixed;\nreplay remainder of trajectory', 6.4)
box(24, 7.0, 21, 11.5, BG, ec=GY, lw=0.8)
txt(34.5, 16.4, '4 edit models \u00d7 n reps', 7.0, weight='bold')
for i, (arm, col) in enumerate([('frontier resample', OK), ('API tier (mini)', '#E69F00'),
                                ('API tier (deepseek)', GR), ('open 14B (qwen)', OR)]):
    txt(25.8, 13.6 - 2.1*i, '\u25CF', 6.0, ha='left', col=col)
    txt(27.4, 13.6 - 2.1*i, arm, 6.4, ha='left')
arrow(20.0, 30.0, 23.6, 27.5)
arrow(20.0, 20.0, 23.6, 13.0)

# ---- Stage C: outcomes (x 49..70) ----
txt(59.5, 37, 'C | Objective outcomes\n& mechanisms', 8.5, weight='bold')
box(49, 21.5, 21, 11.5, BG, ec=GY, lw=0.8)
txt(59.5, 30.4, 'step success rate per arm', 7.0)
txt(59.5, 25.6, 'exit code + deliverable check;\nno LLM judge, temp 0, sandboxed', 6.4)
box(49, 7.0, 21, 11.5, '#FBEDE4', ec=OR, lw=1.0)
txt(59.5, 16.4, 'failure mechanism coding', 7.0, col=OR, weight='bold')
txt(59.5, 11.6, 'no-code / semantic /\nmodel-idiosyncratic families', 6.4)
arrow(45.6, 27.0, 48.6, 27.0)
arrow(45.6, 12.5, 48.6, 12.5)

# ---- Stage D: blind annotation + prediction (x 74..102) ----
txt(88, 37, 'D | Blind annotation\n& prediction', 8.5, weight='bold')
box(74, 21.5, 28, 11.5, BG, ec=GY, lw=0.8)
txt(88, 30.6, '7 verifiability features (F1\u2013F7)', 7.0, weight='bold')
feats = ['F1 objective checkability', 'F2 artifact / deliverable', 'F3 task-specific feedback',
         'F4 execution feedback', 'F5 state dependence', 'F6 recoverability']
for i, f in enumerate(feats):
    txt(75.6, 27.8 - 1.5*i, f, 5.8, ha='left')
box(74, 7.0, 28, 11.5, '#EAF2F8', ec=OK, lw=1.0)
txt(88, 15.8, 'M1 (V+C) vs M0 (controls)', 7.0, col=OK, weight='bold')
txt(88, 12.8, '\u0394RMSE \u22120.04,  \u0394\u03C1 +0.17  (pre-registered)', 6.4, col=OK)
txt(88, 9.8, 'task-level leave-one-out CV;\ndouble-blind codebook', 6.4)
arrow(70.6, 27.0, 73.6, 27.0)
arrow(70.6, 12.5, 73.6, 12.5)
arrow(88, 21.1, 88, 18.9)

# ---- bottom takeaway strip ----
box(24, 0.8, 78, 3.8, '#FFFFFF', ec=GY, lw=0.7, r=0.8)
txt(63, 2.7, 'Takeaway: frontier dependence concentrates at a minority of steps and is partially predictable\n'
             'from blind-coded verifiability features \u2014 a measurable design principle for model allocation', 6.8)
arrow(11, 7.1, 11, 5.4, col=GY)

fig.savefig('figures/fig1_framework.png')
print('fig1 done')
