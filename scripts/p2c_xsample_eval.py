#!/usr/bin/env python3
"""Scale-up evaluation (pre-registered layers 1-2, local run).

Analyse A (primary): task-level LOTO on the ENLARGED in-distribution set --
38 pre-registered points + 11 layer-1 points (6 new parents; t85 contributes a
single point) = 49 points over 22 tasks. Frozen ridge alpha=1.0, controls C,
features V; H2 supported iff dRMSE<=0 and dRho>=0.1.

Analyse B (out-of-distribution): fit on the enlarged set and predict the 18
Chemistry points (6 from the first cross-domain round + 12 new layer-2 points;
72 cells; every point has all 4 arms) with 20k permutations.

Analyse C (sensitivity): A's training set + the 7 previously held-out t40/t60
scan instances = 56 points.

Strata for layer-1 points come from the frozen task matrix (45 stable_pass,
35 stable_fail, 58 flaky, 44 stable_fail, 40 flaky, 85 stable_pass); roles
neutral (no P1 gold labels for new parents). Layer-2 points: neutral stratum
and role. t40s6 qwen is structurally unrunnable (32K-context wall, prompt
30,721 tokens) and contributes no observation.
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
MERGED_X2 = 'p2_annotation_merged_xdomain2.csv'   # 6 chemistry (round 1)
MERGED_XS = 'p2_annotation_merged_xsample.csv'    # 23 scale-up points
POINTS = 'cf_points.json'
STRATUM_7 = {'40': 'flaky', '60': 'stable_pass'}
STRATUM_L1 = {'45': 'stable_pass', '35': 'stable_fail', '58': 'flaky',
              '44': 'stable_fail', '40': 'flaky', '85': 'stable_pass'}
XSCALE_STAMPS = {'1792040426-2786793', '1792041088-3179699', '1792041127-3180245',
                 '1792041919-3213183', '1792042117-3215081', '1792042549-3237637',
                 '1792041190-3180807', '1792043204-3238759'}
ROUND1_STAMPS = {'1792027104-2691932', '1792027829-2732525'}


def load_cells():
    c = pd.read_csv(CELLS, dtype={'task': str, 'in_points': str},
                    keep_default_na=False)
    return c[c.arm.isin(['resample', 'mini', 'ds', 'qwen'])]


def feat_row(merged, pid):
    m = merged[merged.point_id == pid]
    if m.empty:
        raise SystemExit(f'missing features for {pid}')
    return m.iloc[0]


def base_row(r, stratum, role, merged, pid):
    m = feat_row(merged, pid)
    return {'key': pid, 'task': str(r['task']), 'arm': r['arm'],
            'step_no': int(r['edit_step']),
            'remaining': 12 - int(r['edit_step']) + 1,
            'stratum': stratum, 'role': role, 'Y': r['Y'], 'n': r['n'],
            **{f: float(m[f]) for f in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']}}


def build_38():
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
        p = meta[key]
        rows.append(base_row(r, p.get('stratum', ''), p.get('role', ''), merged,
                             f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}"))
    return pd.DataFrame(rows)


def build_layer1():
    cells = load_cells()
    cells = cells[cells.parent_stamp.isin(XSCALE_STAMPS)]
    cells = cells[~cells.task.isin(['51', '97'])]          # layer-1 only
    rows = [base_row(r, STRATUM_L1[str(r['task'])], 'neutral',
                     pd.read_csv(MERGED_XS),
                     f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}")
            for _, r in cells.iterrows()]
    return pd.DataFrame(rows)


def build_layer2():
    cells = load_cells()
    cells = cells[cells.parent_stamp.isin(XSCALE_STAMPS)]
    cells = cells[cells.task.isin(['51', '97'])]           # new chemistry
    rows = [base_row(r, 'stable_pass', 'neutral', pd.read_csv(MERGED_XS),
                     f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}")
            for _, r in cells.iterrows()]
    # round-1 chemistry points
    cells1 = load_cells()
    cells1 = cells1[cells1.parent_stamp.isin(ROUND1_STAMPS)]
    rows += [base_row(r, 'stable_pass', 'neutral', pd.read_csv(MERGED_X2),
                      f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}")
             for _, r in cells1.iterrows()]
    return pd.DataFrame(rows)


def build_x1():
    cells = load_cells()
    cells = cells[cells.in_points == '']
    cells = cells[cells.task.isin(['40', '60'])]
    cells = cells[~((cells.task == '40') & (cells.edit_step.astype(str) == '5'))]
    cells = cells[~((cells.task == '60') & (cells.edit_step.astype(str) == '9'))]
    cells = cells[~cells.parent_stamp.isin(ROUND1_STAMPS | XSCALE_STAMPS)]
    merged = pd.read_csv(MERGED_X1)
    rows = []
    for _, r in cells.iterrows():
        pid = f"t{r['task']}s{r['edit_step']}@{r['parent_stamp']}"
        rows.append(base_row(r, STRATUM_7[str(r['task'])], 'neutral', merged, pid))
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


def loto(df, use_V):
    """Leave-one-task-out predictions over tasks in df."""
    preds = np.full(len(df), np.nan)
    for task in sorted(df.task.unique(), key=int):
        tr = df[df.task != task]
        te = df[df.task == task]
        mdl = Ridge(alpha=1.0).fit(design(tr, use_V), tr.Y)
        preds[df.index.get_indexer(te.index)] = mdl.predict(design(te, use_V))
    return np.clip(preds, 0, 1)


def run_holdout(train, held, tag, perms=20000, seed=20260715):
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
    per.to_csv(f'p2c_xsample_predictions_{tag}.csv', index=False)
    return out


def report_loto(df, tag):
    out = {}
    for name, use_V in [('M0', False), ('M1', True)]:
        pred = loto(df, use_V)
        m = metrics(df.Y, pred)
        m['n_points'] = df.key.nunique()
        m['n_tasks'] = df.task.nunique()
        out[name] = m
    out['dRMSE'] = out['M1']['rmse'] - out['M0']['rmse']
    out['dRho'] = out['M1']['rho'] - out['M0']['rho']
    per = pd.DataFrame({'key': df.key, 'arm': df.arm, 'Y': df.Y.values,
                        'p_M0': loto(df, False).round(3), 'p_M1': loto(df, True).round(3)})
    per.to_csv(f'p2c_xsample_loto_{tag}.csv', index=False)
    return out


def main():
    p38 = build_38()
    l1 = build_layer1()
    l2 = build_layer2()
    x1 = build_x1()
    print(f'38pts: {len(p38)} obs / {p38.key.nunique()} pts / {p38.task.nunique()} tasks')
    print(f'layer1: {len(l1)} obs / {l1.key.nunique()} pts / {l1.task.nunique()} tasks')
    print(f'layer2+round1 held: {len(l2)} obs / {l2.key.nunique()} pts / {l2.task.nunique()} tasks')
    print(f'scan held: {len(x1)} obs / {x1.key.nunique()} pts')
    res = {}
    res['A_loto_49pts'] = report_loto(pd.concat([p38, l1], ignore_index=True), 'a49')
    res['A_ref_loto_38pts'] = report_loto(p38, 'a38')
    res['B_chem18_from49'] = run_holdout(pd.concat([p38, l1], ignore_index=True), l2, 'b18')
    res['B_chem18_from41'] = run_holdout(
        pd.concat([p38, l1], ignore_index=True)[
            ~pd.concat([p38, l1], ignore_index=True).task.isin(['40', '60'])], l2, 'b18b')
    res['C_chem18_from56'] = run_holdout(pd.concat([p38, l1, x1], ignore_index=True), l2, 'c56')
    print(json.dumps(res, indent=2))
    json.dump(res, open('p2c_xsample_results.json', 'w'), indent=2)


if __name__ == '__main__':
    main()
