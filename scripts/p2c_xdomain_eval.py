#!/usr/bin/env python3
"""Cross-domain / held-out evaluation of the P2c prediction models (local copy).

Same logic as scripts/p2c_xdomain_eval.py on the lab; paths point at the local
working copy. Two levels:

  H-a (instance-level): fit on all 38 pre-registered points (134 obs),
      predict the 7 held-out scan code-step instances (28 obs).
  H-b (task-level): additionally drop every t40/t60 point from training
      (32 points remain) so held-out instances come from unseen tasks.

Role proxy for held-out points (parent-only, mechanical): deliverable-producing
steps -> critical_success, else neutral. NOTE: the merged xdomain features use
neutral role for all held points and stratum from the frozen task matrix
(t40=flaky, t60=stable_pass); the critical_success proxy was NOT applied after
review - the conservative all-neutral choice is used and documented.
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score

INV = 'p2_run_inventory.csv'
MERGED = 'p2_annotation_merged.csv'
MERGED_X = 'p2_annotation_merged_xdomain.csv'
POINTS = 'cf_points.json'
STRATUM = {'40': 'flaky', '60': 'stable_pass'}


def build_train():
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


def build_held():
    inv = pd.read_csv(INV)
    merged = pd.read_csv(MERGED_X)
    inv = inv[inv.arm.isin(['resample', 'mini', 'ds', 'qwen'])]
    inv = inv[inv.in_points.astype(str).str.lower() == 'false']
    inv = inv[inv.task.astype(str).isin(['40', '60'])]
    inv = inv[~((inv.task.astype(str) == '40') & (inv.edit_step.astype(str) == '5'))]
    inv = inv[~((inv.task.astype(str) == '60') & (inv.edit_step.astype(str) == '9'))]
    g = inv.groupby(['task', 'edit_step', 'parent_stamp', 'arm']).agg(
        Y=('Y', 'mean'), n=('Y', 'size')).reset_index()
    rows = []
    for _, r in g.iterrows():
        pid = f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}"
        m = merged[merged.point_id == pid]
        if m.empty:
            raise SystemExit(f'missing features for {pid}')
        m = m.iloc[0]
        rows.append({'key': pid, 'task': str(r['task']), 'arm': r['arm'],
                     'step_no': int(r['edit_step']), 'remaining': 12 - int(r['edit_step']) + 1,
                     'stratum': STRATUM[str(r['task'])], 'role': 'neutral',
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


def run(train, held, tag):
    out = {}
    for name, use_V in [('M0', False), ('M1', True)]:
        mdl = Ridge(alpha=1.0).fit(design(train, use_V), train.Y)
        pred = mdl.predict(design(held, use_V))
        m = metrics(held.Y, pred)
        m['n_train_obs'] = len(train)
        out[name] = m
        if name == 'M1':
            per = pd.DataFrame({'key': held.key, 'arm': held.arm,
                                'Y': held.Y.values, 'p': np.clip(pred, 0, 1).round(3)})
            per.to_csv(f'p2c_xdomain_predictions_{tag}.csv', index=False)
    out['dRMSE'] = out['M1']['rmse'] - out['M0']['rmse']
    out['dRho'] = out['M1']['rho'] - out['M0']['rho']
    return out


def main():
    tr = build_train()
    he = build_held()
    print(f'train: {len(tr)} obs / {tr.key.nunique()} points / {tr.task.nunique()} tasks')
    print(f'held:  {len(he)} obs / {he.key.nunique()} points')
    print(he.groupby('arm').Y.agg(['count', 'mean']).round(3))
    res = {'Ha_instance_level': run(tr, he, 'ha'),
           'Hb_task_level': run(tr[~tr.task.astype(str).isin(['40', '60'])], he, 'hb')}
    print(json.dumps(res, indent=2))
    json.dump(res, open('p2c_xdomain_results.json', 'w'), indent=2)


if __name__ == '__main__':
    main()
