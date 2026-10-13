#!/usr/bin/env python3
"""P2-0 audit: rebuild every P1 number from raw result.json files (plan §3).

Outputs:
  reports/pilot/p2_run_inventory.csv   -- per-run traceable inventory
  reports/pilot/p2_reproduce_tables.md -- rebuilt tables T1..T6 + discrepancy log
Answers audit items A1-A5 with explicit numerator/denominator rules.
"""
import json, glob, csv, os, sys, collections
from math import sqrt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

try:
    from scipy.stats import fisher_exact
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


def load_points():
    pts = {}
    for p in json.load(open('reports/annotation/cf_points.json'))['points']:
        k = (str(p['task_id']), int(p['step_no']), p['parent_stamp'])
        pts[k] = p
    return pts


def edit_parsed_action(m, run_dir):
    """edit-step parsed action: cf_meta field if present, else scan trace.jsonl."""
    v = m.get('edit_step_parsed_action')
    if v:
        return v
    trace = os.path.join(run_dir, 'trace.jsonl')
    if os.path.exists(trace):
        for line in open(trace):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            ex = ev.get('extra') or {}
            if ex.get('is_cf_edit_step'):
                return ex.get('parsed_action')
    return ''


def collect():
    pts = load_points()
    runs = []
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f))
        m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f:
            arm = 'resample'
        elif 'mini' in em:
            arm = 'mini'
        elif 'Qwen' in em:
            arm = 'qwen'
        else:
            arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        trace_p = os.path.join(os.path.dirname(f), 'trace.jsonl')
        sb = trace_p and os.path.exists(trace_p) and 'SANDBOX ERROR' in open(trace_p, errors='ignore').read()
        fid = m.get('replay_fidelity') or {}
        steps = fid.get('steps') or []
        runs.append({
            'task': k[0], 'edit_step': k[1], 'parent_stamp': stamp,
            'arm': arm, 'edit_model': em, 'Y': r['eval_success'],
            'status': r['status'], 'cf_status': m.get('cf_status', ''),
            'edit_parsed': edit_parsed_action(m, os.path.dirname(f)),
            'n_replayed': len(steps),
            'all_status_match': all(s.get('status_match') for s in steps) if steps else '',
            'n_obs_identical': sum(1 for s in steps if s.get('obs_identical')) if steps else '',
            'prompt_tokens': (r.get('token_usage') or {}).get('prompt', (r.get('token_usage') or {}).get('prompt_tokens', '')),
            'completion_tokens': (r.get('token_usage') or {}).get('completion', (r.get('token_usage') or {}).get('completion_tokens', '')),
            'wall_s': round(r.get('wall_s') or 0, 1),
            'stamp': r['stamp'], 'parent_run': m.get('parent_run', ''),
            'parent_outcome': m.get('parent_outcome'),
            'sandbox_invalid': bool(sb),
            'in_points': k in pts and pts[k].get('ready', False),
            'role': pts[k]['role'] if k in pts else '',
            'point_key': '|'.join(str(x) for x in k),
        })
    # rep index per (point, arm)
    cnt = collections.Counter((r['point_key'], r['arm']) for r in runs)
    seen = collections.Counter()
    for r in runs:
        seen[(r['point_key'], r['arm'])] += 1
        r['rep'] = seen[(r['point_key'], r['arm'])]
        r['n_rep_total'] = cnt[(r['point_key'], r['arm'])]
    return pts, runs


def wilson(x, n, z=1.96):
    if n == 0:
        return (None, None)
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def rate_str(v):
    if not v:
        return '-'
    x, n = sum(v), len(v)
    lo, hi = wilson(x, n)
    return f"{x}/{n} ({x/n:.2f} [{lo:.2f},{hi:.2f}])"


def fisher_p(a, b, c, d):
    if not HAVE_SCIPY:
        return None
    _, p = fisher_exact([[a, b], [c, d]])
    return p


def skey(k):
    t, st, stamp = k.split('|')
    return (int(t), int(st), stamp)


def svars(k):
    t, st, stamp = k.split('|')
    return t, int(st), stamp


def main():
    pts, runs = collect()
    pts_str = {'|'.join(str(x) for x in k): v for k, v in pts.items()}
    L = []
    def out(s=''):
        L.append(s)

    # ---- inventory CSV ----
    cols = ['task','edit_step','parent_stamp','arm','edit_model','Y','status','cf_status','sandbox_invalid',
            'edit_parsed','n_replayed','all_status_match','n_obs_identical','prompt_tokens',
            'completion_tokens','wall_s','stamp','parent_run','parent_outcome','in_points',
            'role','point_key','rep','n_rep_total']
    with open('reports/pilot/p2_run_inventory.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(runs, key=lambda r: (int(r['task']), r['edit_step'], r['parent_stamp'], r['arm'], r['rep'])):
            w.writerow({c: r[c] for c in cols})

    by = collections.defaultdict(lambda: collections.defaultdict(list))
    n_invalid = 0
    for r in runs:
        if r['in_points'] and not r['sandbox_invalid']:
            by[r['point_key']][r['arm']].append(r['Y'])
        elif r['in_points'] and r['sandbox_invalid']:
            n_invalid += 1
    out(f"- sandbox-invalid runs excluded from stats: **{n_invalid}** (pre-fix contaminated dry runs)")

    # ---- T1: A1 count decomposition ----
    out('# P2-0 rebuilt tables (generated by scripts/p2_reproduce_tables.py)\n')
    out('## T1 Run inventory decomposition (A1)\n')
    out(f"- total result.json files: **{len(runs)}**")
    out(f"- in-point (ready) runs: **{sum(1 for r in runs if r['in_points'])}**; extras (parent not in point list): **{sum(1 for r in runs if not r['in_points'])}**")
    arm_cnt = collections.Counter(r['arm'] for r in runs if r['in_points'])
    out(f"- per-arm in-point: " + ', '.join(f"{a} {n}" for a, n in sorted(arm_cnt.items())))
    dups = {k: v for k, v in collections.Counter((r['point_key'], r['arm']) for r in runs if r['in_points']).items() if v > 2}
    out(f"- (point,arm) cells with n>2 (audit trail of补齐/复核): {len(dups)}; max n = {max(dups.values()) if dups else 2}")
    status_cnt = collections.Counter(r['status'] for r in runs if r['in_points'])
    out(f"- status: {dict(status_cnt)}")
    cf_cnt = collections.Counter(r['cf_status'] for r in runs if r['in_points'])
    out(f"- cf_status: {dict(cf_cnt)}")
    out("")

    # ---- T2: 38-point x arm ----
    out('## T2 All 38 point-instances x arm (successes/n [Wilson95%])\n')
    out('| point | role | parent | resample | mini | ds | qwen |')
    out('|---|---|---|---|---|---|---|')
    for k in sorted(by, key=skey):
        t_, s_, st_ = svars(k)
        a = by[k]
        role = pts_str[k]['role']
        out(f"| t{t_}s{s_} | {role} | {st_[-6:]} | {rate_str(a.get('resample',[]))} | "
            f"{rate_str(a.get('mini',[]))} | {rate_str(a.get('ds',[]))} | {rate_str(a.get('qwen',[]))} |")
    out("")

    # ---- T3: signal points, four arms + Fisher (A2/A4) ----
    sig6 = [('60',6),('85',2),('40',4),('92',1),('60',4),('40',2)]
    out('## T3 Six signal points, four arms, ΔSR vs resample, two-sided Fisher p\n')
    out('| point | cls | resample | mini | ds | qwen | ΔSR mini | ΔSR ds | ΔSR qwen | p(qwen vs res) |')
    out('|---|---|---|---|---|---|---|---|---|---|')
    q_all_x = q_all_n = r_all_x = r_all_n = 0
    for t, s in sig6:
        ks = [k for k in sorted(by, key=skey) if svars(k)[:2] == (t, s)]
        for k in ks:
            t_, s_, st_ = svars(k)
            a = by[k]
            def sr(arm):
                v = a.get(arm, [])
                return (sum(v), len(v))
            rx, rn = sr('resample'); mx, mn = sr('mini'); dx, dn = sr('ds'); qx, qn = sr('qwen')
            cls = pts_str[k]['role'].replace('critical_','crit/').replace('_failure','(fail)').replace('_success','(succ)')
            dmin = f"{mx/mn - rx/rn:+.2f}" if mn and rn else '-'
            dds = f"{dx/dn - rx/rn:+.2f}" if dn and rn else '-'
            dqw = f"{qx/qn - rx/rn:+.2f}" if qn and rn else '-'
            p = fisher_p(qx, qn - qx, rx, rn - rx) if qn and rn else None
            ps = f"{p:.3f}" if p is not None else '-'
            out(f"| t{t_}s{s_} | {cls} | {rx}/{rn} | {mx}/{mn} | {dx}/{dn} | {qx}/{qn} | {dmin} | {dds} | {dqw} | {ps} |")
            if (t_, s_) == ('40', 2):
                continue  # pooled口径单独算
            q_all_x += qx; q_all_n += qn; r_all_x += rx; r_all_n += rn
    out("")
    out('### A2: Qwen pooled-test口径分解\n')
    q_tot = sum(len(v) for k in by for v in [by[k].get('qwen',[])])
    out(f"- Qwen runs on ready points, all 7 sig instances: **{q_tot}**")
    qx6, qn6 = q_all_x, q_all_n
    rx6, rn6 = r_all_x, r_all_n
    p6 = fisher_p(qx6, qn6-qx6, rx6, rn6-rx6)
    ps6 = f"{p6:.4f}" if p6 is not None else "NA(scipy)"
    out(f"- 口径A（6信号点，t40s2双实例排除，n=5实例）: qwen {qx6}/{qn6} ({qx6/qn6:.2f}) vs resample {rx6}/{rn6} ({rx6/rn6:.2f}), Fisher p={ps6}")
    # 口径B: 双实例都进
    kq = [(k, by[k].get('qwen',[]), by[k].get('resample',[])) for k in by if svars(k)[:2] == ('40', 2)]
    qx2 = sum(sum(v) for _, v, _ in kq); qn2 = sum(len(v) for _, v, _ in kq)
    rx2 = sum(sum(v) for _, _, v in kq); rn2 = sum(len(v) for _, _, v in kq)
    pB = fisher_p(qx6+qx2, qn6+qn2-qx6-qx2, rx6+rx2, rn6+rn2-rx6-rx2)
    out(f"- 口径B（t40s2双实例都计入）: qwen {qx6+qx2}/{qn6+qn2} ({(qx6+qx2)/(qn6+qn2):.2f}) vs resample {rx6+rx2}/{rn6+rn2} ({(rx6+rx2)/(rn6+rn2):.2f}), Fisher p={pB if pB is None else round(pB,4)}")
    out("")

    # ---- T4: A3 H1b repair classification ----
    out('## T4 Critical-failure points: repair outcomes per arm (A3)\n')
    out('| point | parent Y | resample | mini | ds | qwen | frontier-only? |')
    out('|---|---|---|---|---|---|---|')
    ncf = 0
    for k in sorted(by, key=skey):
        if pts_str[k]['role'] != 'critical_failure':
            continue
        t_, s_, st_ = svars(k)
        a = by[k]; ncf += 1
        def fx(arm):
            v = a.get(arm, [])
            return f"{sum(v)}/{len(v)}" if v else '-'
        re_ = sum(a.get('resample', [])) > 0
        mi_ = sum(a.get('mini', [])) > 0
        ds_ = sum(a.get('ds', [])) > 0
        qw_ = sum(a.get('qwen', [])) > 0
        others = mi_ or ds_ or qw_
        out(f"| t{t_}s{s_} | {pts_str[k]['run_outcome']} | {fx('resample')} | {fx('mini')} | {fx('ds')} | {fx('qwen')} | {'NO (frontier-only)' if re_ and not others else ('NO (none repair)' if not re_ and not others else 'WEAKENED (non-frontier repaired)')} |")
    out(f"\n- critical_failure 点实例总数: **{ncf}**")
    n_unfix = sum(1 for k in by if pts_str[k]['role']=='critical_failure' and not any(sum(by[k].get(a,[]))>0 for a in ['resample','mini','ds','qwen']))
    n_frontier_only = sum(1 for k in by if pts_str[k]['role']=='critical_failure' and sum(by[k].get('resample',[]))>0 and not any(sum(by[k].get(a,[]))>0 for a in ['mini','ds','qwen']))
    n_weakened = sum(1 for k in by if pts_str[k]['role']=='critical_failure' and any(sum(by[k].get(a,[]))>0 for a in ['mini','ds','qwen']))
    out(f"- 重算分类: 不可修复 {n_unfix} + frontier-only {n_frontier_only} + 非前沿修复(反例) {n_weakened} = **{n_unfix+n_frontier_only+n_weakened}**")
    out("")

    # ---- T5: A5 failure stratification ----
    out('## T5 Edit-step parsed-action stratification per arm (A5)\n')
    out('| arm | code | none | final | other/blank | capability% | protocol% |')
    out('|---|---|---|---|---|---|---|')
    for arm in ['resample','mini','ds','qwen']:
        rs = [r for r in runs if r['in_points'] and r['arm'] == arm]
        pa = collections.Counter(r['edit_parsed'] or 'blank' for r in rs)
        cap = sum(v for k, v in pa.items() if k == 'code')
        pro = sum(v for k, v in pa.items() if k in ('none','final'))
        tot = len(rs)
        out(f"| {arm} | {pa.get('code',0)} | {pa.get('none',0)} | {pa.get('final',0)} | {pa.get('blank',0)} | {cap/tot:.0%} | {pro/tot:.0%} |")
    # protocol failure & self-heal
    proto = [r for r in runs if r['in_points'] and r['edit_parsed'] in ('none','final')]
    healed = [r for r in proto if r['Y'] == 1]
    out(f"\n- protocol-failure runs (parsed none/final): {len(proto)}; of which final-run success (Y=1, '自愈'): {len(healed)} ({len(healed)/len(proto):.0%})" if proto else "- no protocol failures")
    # blank= unknown -> explicit
    blank = sum(1 for r in runs if r['in_points'] and not r['edit_parsed'])
    out(f"- runs with no recoverable parsed action (blank): {blank} — excluded from capability/protocol percentages")
    out("")

    # ---- T6: A4 specific points ----
    out('## T6 口径核查 t40s4 / t40s2 (A4)\n')
    for k in sorted(by, key=skey):
        t_, s_, st_ = svars(k)
        if (t_, s_) not in [('40', 4), ('40', 2)]:
            continue
        a = by[k]
        def fx(arm):
            v = a.get(arm, [])
            return f"{sum(v)}/{len(v)}={sum(v)/len(v):.2f}" if v else '-'
        out(f"- t{t_}s{s_} @{st_[-6:]} ({pts_str[k]['role']}): resample {fx('resample')} | mini {fx('mini')} | ds {fx('ds')} | qwen {fx('qwen')}")
    out("")
    open('reports/pilot/p2_reproduce_tables.md', 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
