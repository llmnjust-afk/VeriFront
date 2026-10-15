#!/usr/bin/env python3
"""TRUE cross-domain evaluation of the P2c prediction models (local run).

Held-out set: 6 Computational Chemistry points (tasks 1 and 3 -- zero
chemistry tasks in the 14 training tasks), all 3 code steps of each parent,
4 arms x up to 2 reps (46/48 runs; ds relay timeouts left 2 cells at 1 rep).

Training variants:
  Ha  38 pre-registered points (frozen protocol training set)
  Hb  32 points: Ha minus every t40/t60 point (task-level exclusion)
  Hc  45 points: Ha plus the 7 previously held-out t40/t60 scan instances
      (sensitivity: maximal in-distribution training)

Stratum/role for the new points: tasks 1/3 are absent from the frozen
stability matrix and have no P1 gold labels -> neutral stratum (baseline
stable_pass) and neutral role, the same conservative choice as the
held-out reanalysis. Features come from the merged blind annotation
(34/36 consensus cells, 2 one-level averaged, 0 adjudications).
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score

CELLS = 'cells_all.csv'
MERGED = 'p2_annotation_merged.csv'
MERGED_X1 = 'p2_annotation_merged_xdomain.csv'    # 7 t40/t60 scan instances
MERGED_X2 = 'p2_annotation_merged_xdomain2.csv'   # 6 chemistry points
POINTS = 'cf_points.json'
STRATUM_7 = {'40': 'flaky', '60': 'stable_pass'}
NEW_STAMPS = {'1792027104-2691932', '1792027829-2732525'}


def load_cells():
    c = pd.read_csv(CELLS, dtype={'task': str, 'in_points': str},
                   keep_default_na=False)
    return c[c.arm.isin(['resample', 'mini', 'ds', 'qwen'])]


def feat_row(merged, pid):
    m = merged[merged.point_id == pid]
    if m.empty:
        raise SystemExit(f'missing features for {pid}')
    return m.iloc[0]


def build_train():
    cells = load_cells()
    cells = cells[cells.in_points == 'True']
    merged = pd.read_csv(MERGED)
    pts = json.load(open(POINTS))['points']
    meta = {(str(p['task_id']), int(p['step_no']), p['parent_stamp']): p for p in pts}
    rows = []
    for _, r in cells.iterrows():
        key = (str(r['task']), int(r['edit_step']), r['parent_stamp'])
        if key not in meta:
            continue
        m = feat_row(merged, f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}")
        p = meta[key]
        rows.append({'key': '|'.join(map(str, key)), 'task': str(r['task']),
                     'arm': r['arm'], 'step_no': int(r['edit_step']),
                     'remaining': 12 - int(r['edit_step']) + 1,
                     'stratum': p.get('stratum', ''), 'role': p.get('role', ''),
                     'Y': r['Y'], 'n': r['n'],
                     **{f: float(m[f]) for f in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']}})
    return pd.DataFrame(rows)


def build_x1():
    cells = load_cells()
    cells = cells[cells.in_points == '']
    cells = cells[cells.task.isin(['40', '60'])]
    cells = cells[~((cells.task == '40') & (cells.edit_step.astype(str) == '5'))]
    cells = cells[~((cells.task == '60') & (cells.edit_step.astype(str) == '9'))]
    merged = pd.read_csv(MERGED_X1)
    rows = []
    for _, r in cells.iterrows():
        pid = f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}"
        m = feat_row(merged, pid)
        rows.append({'key': pid, 'task': str(r['task']), 'arm': r['arm'],
                     'step_no': int(r['edit_step']),
                     'remaining': 12 - int(r['edit_step']) + 1,
                     'stratum': STRATUM_7[str(r['task'])], 'role': 'neutral',
                     'Y': r['Y'], 'n': r['n'],
                     **{f: float(m[f]) for f in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']}})
    return pd.DataFrame(rows)


def build_x2():
    cells = load_cells()
    cells = cells[cells.parent_stamp.isin(NEW_STAMPS)]
    merged = pd.read_csv(MERGED_X2)
    rows = []
    for _, r in cells.iterrows():
        pid = f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}"
        m = feat_row(merged, pid)
        rows.append({'key': pid, 'task': str(r['task']), 'arm': r['arm'],
                     'step_no': int(r['edit_step']),
                     'remaining': 12 - int(r['edit_step']) + 1,
                     'stratum': 'stable_pass', 'role': 'neutral',
                     'Y': r['Y'], 'n': r['n'],
                     **{f: float(m[f]) for f in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']}})
    return pd.DataFrame(rows)


def design(df, use_V):
    C = pd.DataFrame({
        'step_no': df.step_no, 'remaining': df.remaining,
        'stratum_fail': (df.stratum == 'stable_fail').astype(int),
        'stratum_flaky': (df.stratum == 'flaky').astype(int),
        'role_critical': (df.role == 'critical_success').astype(int),
        'arm_mini': (df.arm == 'mini').astype(int),
        'arm_ds': (df.arm == 'ds').astype(int),
        'arm_qwen': (df.arm == 'qwen').astype(int),
    })
    X = C.copy()
    if use_V:
        for f in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']:
            X[f] = df[f]
    return X.values


def metrics(y, p):
    y, p = np.asarray(y, float), np.clip(np.asarray(p, float), 0, 1)
    out = {'rmse': float(np.sqrt(np.mean((y - p) ** 2))),
           'rho': float(spearmanr(y, p).statistic)}
    try:
        out['auroc'] = float(roc_auc_score((y >= 0.5).astype(int), p))
    except ValueError:
        out['auroc'] = None
    return out


def run(train, held, tag, perms=20000, seed=20260715):
    rng = np.random.default_rng(seed)
    out = {}
    preds = {}
    for name, use_V in [('M0', False), ('M1', True)]:
        mdl = Ridge(alpha=1.0).fit(design(train, use_V), train.Y)
        pred = np.clip(mdl.predict(design(held, use_V)), 0, 1)
        preds[name] = pred
        m = metrics(held.Y, pred)
        m['n_train_obs'] = len(train)
        m['n_train_points'] = train.key.nunique()
        # one-sided permutation p: P(rho_perm >= rho_obs) under arm-label shuffle
        rho_obs = m['rho']
        cnt = 0
        for _ in range(perms):
            yp = held.Y.values[rng.permutation(len(held))]
            cnt += float(spearmanr(yp, pred).statistic) >= rho_obs
        m['perm_p_rho_ge'] = cnt / perms
        out[name] = m
    out['dRMSE'] = out['M1']['rmse'] - out['M0']['rmse']
    out['dRho'] = out['M1']['rho'] - out['M0']['rho']
    per = pd.DataFrame({'key': held.key, 'arm': held.arm, 'Y': held.Y.values,
                        'p_M0': preds['M0'].round(3), 'p_M1': preds['M1'].round(3)})
    per.to_csv(f'p2c_xdomain2_predictions_{tag}.csv', index=False)
    return out


def main():
    tr = build_train()
    x1 = build_x1()
    x2 = build_x2()
    print(f'train(38pts): {len(tr)} obs / {tr.key.nunique()} points / {tr.task.nunique()} tasks')
    print(f'held 7 t40/t60: {len(x1)} obs / {x1.key.nunique()} points')
    print(f'held 6 chemistry: {len(x2)} obs / {x2.key.nunique()} points')
    print(x2.groupby('arm').Y.agg(['count', 'mean']).round(3))
    res = {'Ha_38pts_vs_chem': run(tr, x2, 'ha'),
           'Hb_32pts_vs_chem': run(tr[~tr.task.astype(str).isin(['40', '60'])], x2, 'hb'),
           'Hc_45pts_vs_chem': run(pd.concat([tr, x1], ignore_index=True), x2, 'hc')}
    print(json.dumps(res, indent=2))
    json.dump(res, open('p2c_xdomain2_results.json', 'w'), indent=2)


if __name__ == '__main__':
    main()
