#!/usr/bin/env python3
"""P2c: M0 vs M1 per preregistered protocol (prediction_protocol sec3-4).

Unit of observation: (point, arm). Y = success rate of that arm on that point
(mean over reps). M0 = ridge on controls C only; M1 = ridge on V + C.
Leave-one-task-out CV (14 tasks); same parent never crosses folds (task-level
split satisfies this). Fixed hyperparameters (alpha=1.0) -> no tuning leakage.
Metrics: pooled RMSE, Spearman rho, AUROC on binarised success (Y>=0.5).
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score

INV = 'p2_run_inventory.csv'
MERGED = 'p2_annotation_merged.csv'
POINTS = 'cf_points.json'


def build():
    inv = pd.read_csv(INV)
    merged = pd.read_csv(MERGED)
    pts = json.load(open(POINTS))['points']
    meta = {(str(p['task_id']), int(p['step_no']), p['parent_stamp']): p for p in pts}
    inv = inv[inv.arm.isin(['resample', 'mini', 'ds', 'qwen'])]
    g = inv.groupby(['task', 'edit_step', 'parent_stamp', 'arm']).agg(
        Y=('Y', 'mean'), n=('Y', 'size')).reset_index()
    rows = []
    for _, r in g.iterrows():
        key = (str(r['task']), int(r['edit_step']), r['parent_stamp'])
        if key not in meta:
            continue
        m = merged[merged.point_id == f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}"]
        if m.empty:
            continue
        m = m.iloc[0]
        p = meta[key]
        row = {'key': '|'.join(map(str, key)), 'task': str(r['task']), 'arm': r['arm'],
               'step_no': int(r['edit_step']), 'remaining': 12 - int(r['edit_step']) + 1,
               'stratum': p.get('stratum', ''), 'role': p.get('role', ''),
               'Y': r['Y'], 'n': r['n']}
        for f in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']:
            row[f] = float(m[f])
        rows.append(row)
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


def main():
    df = build()
    print(f"observations: {len(df)} | points: {df.key.nunique()} | tasks: {df.task.nunique()}")
    print(df.groupby('arm').Y.agg(['count', 'mean']).round(3))
    tasks = sorted(df.task.unique())
    res = {'M0': {'y': [], 'p': []}, 'M1': {'y': [], 'p': []}}
    for t in tasks:
        te = df.task == t
        tr = ~te
        for name, use_V in [('M0', False), ('M1', True)]:
            Xtr = design(df[tr], use_V)
            Xte = design(df[te], use_V)
            mdl = Ridge(alpha=1.0).fit(Xtr, df.loc[tr, 'Y'])
            res[name]['y'] += df.loc[te, 'Y'].tolist()
            res[name]['p'] += mdl.predict(Xte).tolist()
    out = {}
    for name in ['M0', 'M1']:
        y, p = np.array(res[name]['y']), np.clip(res[name]['p'], 0, 1)
        rmse = float(np.sqrt(np.mean((y - p) ** 2)))
        rho = float(spearmanr(y, p).statistic)
        try:
            auc = float(roc_auc_score((y >= 0.5).astype(int), p))
        except ValueError:
            auc = float('nan')
        out[name] = {'rmse': rmse, 'rho': rho, 'auroc': auc}
        print(f"{name}: RMSE={rmse:.4f} rho={rho:.4f} AUROC={auc:.4f}")
    d_rmse = out['M1']['rmse'] - out['M0']['rmse']
    d_rho = out['M1']['rho'] - out['M0']['rho']
    verdict = 'SUPPORT H2' if (d_rmse <= 0 and d_rho >= 0.1) else 'DO NOT SUPPORT H2 (criteria: dRMSE<=0 and dRho>=0.1)'
    print(f"\ndRMSE={d_rmse:+.4f} dRho={d_rho:+.4f} -> {verdict}")
    with open('p2c_m0m1_results.json', 'w') as f:
        json.dump({'metrics': out, 'd_rmse': d_rmse, 'd_rho': d_rho, 'verdict': verdict,
                   'n_obs': len(df), 'n_points': int(df.key.nunique()), 'n_tasks': len(tasks)}, f, indent=1)


if __name__ == '__main__':
    main()
