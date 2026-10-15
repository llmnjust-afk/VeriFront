import csv, math, random
import numpy as np
from scipy import stats

def spearman(a, b):
    r, _ = stats.spearmanr(a, b)
    return r

def paired_perm_p(input_csv, perms=20000, seed=20260715):
    rows = list(csv.DictReader(open(input_csv)))
    Y = np.array([float(r['Y']) for r in rows])
    p0 = np.array([float(r['p_M0']) for r in rows])
    p1 = np.array([float(r['p_M1']) for r in rows])
    d_obs = spearman(Y, p1) - spearman(Y, p0)
    rng = random.Random(seed)
    count = 0
    for _ in range(perms):
        sw = [rng.random() < 0.5 for _ in range(len(rows))]
        q0 = np.where(sw, p1, p0)
        q1 = np.where(sw, p0, p1)
        d_perm = spearman(Y, q1) - spearman(Y, q0)
        if abs(d_perm) >= abs(d_obs):
            count += 1
    p = (count + 1) / (perms + 1)
    return d_obs, p, len(rows), count

for tag, path in [
    ('A_loto49_in_dist', 'p2c_xsample_loto_a49.csv'),
    ('B_chem18_from49', 'p2c_xsample_predictions_b18.csv'),
    ('B_chem18_from39', 'p2c_xsample_predictions_b18b.csv'),
    ('C_chem18_from56', 'p2c_xsample_predictions_c56.csv'),
]:
    d, p, n, c = paired_perm_p(path)
    print(f"{tag}: dRho={d:+.4f}  n={n}  two-sided paired perm p={p:.4f}  (exceed={c})")
