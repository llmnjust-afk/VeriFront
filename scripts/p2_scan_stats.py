#!/usr/bin/env python3
"""P2b: full-step scan inferential statistics (plan §5.1 completion).

Outputs reports/pilot/p2_scan_stats.md:
  T1 per-step per-arm SR with Wilson CI + Fisher p vs resample + BH-FDR q
  T2 task-structural vs capability-dependent step classification (resample baseline health)
  T3 signal-step replication check (P1 vs scan ΔSR sign agreement)
"""
import json, glob, os, collections, itertools
import numpy as np
from math import sqrt
from scipy.stats import fisher_exact

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SCANNED = {'305791': ('40', 5), '321913': ('60', 9)}


def collect():
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
        if stamp[-6:] not in SCANNED: continue
        tr = os.path.join(os.path.dirname(f), 'trace.jsonl')
        if os.path.exists(tr) and 'SANDBOX ERROR' in open(tr, errors='ignore').read():
            continue
        task = SCANNED[stamp[-6:]][0]
        rows.append({'task': task, 'step': int(m['edit_step']), 'arm': arm,
                     'Y': r['eval_success'], 'stamp6': stamp[-6:]})
    return rows


def wilson(x, n, z=1.96):
    if n == 0: return (float('nan'), float('nan'))
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def bh_fdr(pvals):
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    qs = [0.0] * n
    prev = 1.0
    for rank, i in enumerate(reversed(order)):
        k = n - rank
        prev = min(prev, pvals[i] * n / k)
        qs[i] = prev
    return qs


def cmh_pool(rows):
    """Pooled Mantel-Haenszel test across capability-dependent steps."""
    from statsmodels.stats.contingency_tables import StratifiedTable
    import collections
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    classes = {}
    a = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        a[(r['task'], r['step'])][r['arm']].append(r['Y'])
    for (t, s), cells in a.items():
        v = cells.get('resample', [])
        if v and sum(v) / len(v) >= 0.5:
            classes[(t, s)] = 'cap'
    out = []
    for arm in ['mini', 'ds', 'qwen']:
        tables = []
        for (t, s) in sorted(classes):
            cells = a[(t, s)]
            mv, rv = cells.get(arm, []), cells.get('resample', [])
            if not mv or not rv: continue
            tables.append([[sum(mv), len(mv) - sum(mv)],
                           [sum(rv), len(rv) - sum(rv)]])
        if len(tables) < 2: continue
        arr = np.array(tables)
        st = StratifiedTable(arr.transpose(1, 2, 0))
        p = st.test_null_odds(correction=False).pvalue
        orr = st.oddsratio_pooled
        out.append((arm, len(tables), orr, p))
    return out

def main():
    rows = collect()
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        agg[(r['task'], r['step'])][r['arm']].append(r['Y'])

    L = ['# P2b full-step scan: inferential statistics\n']
    L.append(f"- scanned runs (sandbox-valid): {len(rows)}")

    # T1: per-step per-arm with CI + Fisher vs resample + BH-FDR
    L.append('\n## T1 Per-step per-arm SR [Wilson 95% CI], Fisher p vs same-step resample, BH-FDR q\n')
    tests = []  # (task, step, arm, p, x, n, rx, rn)
    for task, nsteps in [('40', 5), ('60', 9)]:
        L.append(f"\n### t{task}\n")
        L.append('| step | resample | mini | ds | qwen |')
        L.append('|---|---|---|---|---|')
        for t in range(1, nsteps + 1):
            cells = agg[(task, t)]
            rx, rn = (sum(cells.get('resample', [0])), len(cells.get('resample', []))) if cells.get('resample') else (0, 0)
            line = [f'| {t} ']
            for arm in ['resample', 'mini', 'ds', 'qwen']:
                v = cells.get(arm, [])
                if not v:
                    line.append('| - ')
                    continue
                x, n = sum(v), len(v)
                lo, hi = wilson(x, n)
                if arm == 'resample':
                    line.append(f'| {x}/{n} ({x/n:.2f} [{lo:.2f},{hi:.2f}]) ')
                else:
                    p = fisher_exact([[x, n - x], [rx, rn - rx]])[1] if (rx + rn) else 1.0
                    tests.append((task, t, arm, p, x, n, rx, rn))
                    line.append(f'| {x}/{n} ({x/n:.2f} [{lo:.2f},{hi:.2f}]) p={p:.3f} ')
            line.append('|')
            L.append(''.join(line))
    ps = [t[3] for t in tests]
    qs = bh_fdr(ps)
    sig_cells = [(t, q) for t, q in zip(tests, qs) if q < 0.10]
    L.append(f"\n- {len(tests)} step-arm tests; BH-FDR q<0.10: **{len(sig_cells)}**")
    for (task, t, arm, p, x, n, rx, rn), q in sig_cells:
        L.append(f"  - t{task}s{t} {arm}: {x}/{n} vs resample {rx}/{rn}, raw p={p:.4f}, q={q:.3f}")

    # T2: task-structural vs capability-dependent steps
    L.append('\n## T2 Step classification by resample baseline health\n')
    L.append('| task-step | resample SR | class |')
    L.append('|---|---|---|')
    classes = {}
    for task, nsteps in [('40', 5), ('60', 9)]:
        for t in range(1, nsteps + 1):
            v = agg[(task, t)].get('resample', [])
            if not v: continue
            sr = sum(v) / len(v)
            cls = 'task-structural (resample weak)' if sr < 0.5 else 'capability-dependent (resample healthy)'
            classes[(task, t)] = cls
            L.append(f"| t{task}s{t} | {sum(v)}/{len(v)} ({sr:.2f}) | {cls} |")
    L.append('\n### Per-class mean ΔSR (arm minus resample, pooled within class)\n')
    L.append('| class | arm | pooled ΔSR |')
    L.append('|---|---|---|')
    for cls_name in ['task-structural (resample weak)', 'capability-dependent (resample healthy)']:
        cls_steps = {k for k, v in classes.items() if v == cls_name}
        for arm in ['mini', 'ds', 'qwen']:
            ax_ = an = 0; rx = rn = 0
            for (task, t) in cls_steps:
                v = agg[(task, t)].get(arm, [])
                b = agg[(task, t)].get('resample', [])
                ax_ += sum(v); an += len(v); rx += sum(b); rn += len(b)
            if an and rn:
                L.append(f"| {cls_name} | {arm} | {ax_/an - rx/rn:+.2f} |")

    # T3: signal-step replication
    L.append('\n## T3 P1 signal-step replication inside the scan (same parent)\n')
    L.append('| point | P1 ΔSR(mini vs res) | scan ΔSR(mini vs res) | sign agree |')
    L.append('|---|---|---|---|')
    p1 = {('40', 4): -0.50, ('60', 4): -0.38}
    for (t, s), p1v in p1.items():
        cells = agg[(t, s)]
        mv = cells.get('mini', []); rv = cells.get('resample', [])
        if mv and rv:
            scan_d = sum(mv) / len(mv) - sum(rv) / len(rv)
            L.append(f"| t{t}s{s} | {p1v:+.2f} | {scan_d:+.2f} | {'YES' if scan_d < 0 else 'NO'} |")
    L.append('\n## T4 Pooled CMH test across capability-dependent steps\n')
    try:
        pool = cmh_pool(rows)
        L.append('| arm | steps pooled | pooled OR | CMH p |')
        L.append('|---|---|---|---|')
        for arm, k, orr, p in pool:
            L.append(f"| {arm} | {k} | {orr:.2f} | {p:.4f} |")
    except Exception as e:
        L.append(f"(CMH unavailable: {e})")
    open('reports/pilot/p2_scan_stats.md', 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:6]))
    print(f"... written reports/pilot/p2_scan_stats.md ({len(L)} lines)")


if __name__ == '__main__':
    main()


    main()

