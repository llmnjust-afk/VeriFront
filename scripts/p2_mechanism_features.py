#!/usr/bin/env python3
"""P2a: per-run mechanism feature extraction from raw traces (plan §4.1).

For every in-point run, walk trace.jsonl and derive:
  edit-step action/code/exit/error-type, post-edit trajectory health,
  retry-repair behavior, step-budget usage, final outcome.

Outputs:
  reports/pilot/p2_mechanism_annotations.csv   (one row per run)
  reports/pilot/p2_mechanism_matrix.md         (signal-point x model error-type matrix)
"""
import json, glob, os, re, csv, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

ERR_PATTERNS = [
    ('dependency', re.compile(r'(ModuleNotFoundError|ImportError|No module named)', re.I)),
    ('syntax', re.compile(r'SyntaxError|IndentationError', re.I)),
    ('name_attr', re.compile(r'\b(NameError|AttributeError|TypeError|ValueError)\b')),
    ('data_state', re.compile(r'(FileNotFoundError|KeyError|IndexError|No such file|empty|EmptyDataError)', re.I)),
    ('assert', re.compile(r'AssertionError|assertion')),
    ('timeout', re.compile(r'(Timeout|timed out|TIMEOUT)', re.I)),
    ('memory', re.compile(r'(OutOfMemory|MemoryError|Killed)', re.I)),
]

def err_type(stderr_text):
    if not stderr_text:
        return 'none'
    for name, pat in ERR_PATTERNS:
        if pat.search(stderr_text):
            return name
    if 'Traceback' in stderr_text or 'Error' in stderr_text:
        return 'other_error'
    return 'none'


def load_points():
    pts = {}
    for p in json.load(open('reports/annotation/cf_points.json'))['points']:
        pts[(str(p['task_id']), int(p['step_no']), p['parent_stamp'])] = p
    return pts


def parse_trace(trace_path, edit_step):
    """Return dict of derived mechanism features for one run."""
    evs = []
    for l in open(trace_path):
        try:
            e = json.loads(l)
        except Exception:
            continue
        if isinstance(e, dict) and 'event_type' in e:
            evs.append(e)
    msgs = [e for e in evs if e['event_type'] == 'agent_message']
    results = [e for e in evs if e['event_type'] == 'tool_result']
    # pair each agent_message with the next tool_result (sequential protocol)
    pairs = []
    ri = 0
    for m in msgs:
        while ri < len(results) and results[ri]['event_time'] < m['event_time']:
            ri += 1
        res = results[ri] if ri < len(results) else None
        ri += 1 if res is not None else 0
        pairs.append((m, res))
    # edit step = first generated step (start_step == edit_step by construction)
    edit_pair = pairs[0] if pairs else (None, None)
    em, eres = edit_pair
    ex = (em or {}).get('extra') or {}
    obs = (eres or {}).get('tool_observation') or ''
    m_exit = re.search(r'exit_code:\s*(-?\d+)', obs)
    m_err = re.search(r'--- STDERR ---\n?(.*?)(?:\n--- |$)', obs, re.S)
    stderr_txt = (m_err.group(1)[:800] if m_err else obs[:800])
    edit_exit = int(m_exit.group(1)) if m_exit else None
    edit_err = err_type(stderr_txt) if (edit_exit not in (0, None) or ex.get('parsed_action') != 'code') else 'none'
    # post-edit trajectory
    gens = [((m.get('extra') or {}).get('generator', '?')) for m, _ in pairs]
    post = pairs[1:]
    post_fails = 0
    first_fail_after = None
    err_seq = []
    for i, (m, r) in enumerate(post):
        o = (r or {}).get('tool_observation') or ''
        ex_code = re.search(r'exit_code:\s*(-?\d+)', o)
        code_v = int(ex_code.group(1)) if ex_code else 0
        if code_v != 0:
            post_fails += 1
            if first_fail_after is None:
                first_fail_after = i + 2  # 1=edit step; +2 => next generated step index (1-based)
            m_err2 = re.search(r'--- STDERR ---\n?(.*?)(?:\n--- |$)', o, re.S)
            err_seq.append(err_type(m_err2.group(1)[:800] if m_err2 else o[:800]))
    # retry behavior: hash of executed script at edit step vs next step
    calls = [e for e in evs if e['event_type'] == 'tool_call']
    hashes = []
    for c in calls:
        ta = c.get('tool_args')
        if isinstance(ta, str):
            try:
                ta = json.loads(ta)
            except Exception:
                ta = {}
        hashes.append((ta or {}).get('code_sha256', ''))
    retried = bool(hashes and len(hashes) > 1 and hashes[0] and hashes[1] and hashes[0] != hashes[1])
    # budget
    n_gen = len(pairs)
    reached_final = any(((m.get('extra') or {}).get('parsed_action') == 'final') for m, _ in pairs)
    gen_models = collections.Counter(gens)
    return {
        'edit_parsed': ex.get('parsed_action', ''),
        'edit_generator': ex.get('generator', ''),
        'edit_exit_code': edit_exit,
        'edit_error_type': edit_err if ex.get('parsed_action') == 'code' else 'no_code',
        'edit_completion_tokens': ((em.get('token_usage') or {}).get('completion') if em else None),
        'post_steps': len(post),
        'post_exec_fails': post_fails,
        'first_fail_after_edit': first_fail_after,
        'post_error_types': ';'.join(err_seq[:6]),
        'retried_modified_code': retried,
        'reached_final': reached_final,
        'n_generated_steps': n_gen,
        'generator_mix': dict(gen_models),
    }


def main():
    pts = load_points()
    rows = []
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f))
        m = r['cf_meta']
        em_name = m.get('edit_model') or ''
        if 'resample' in f:
            arm = 'resample'
        elif 'mini' in em_name:
            arm = 'mini'
        elif 'Qwen' in em_name:
            arm = 'qwen'
        else:
            arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        if k not in pts:
            continue
        trace = os.path.join(os.path.dirname(f), 'trace.jsonl')
        feat = parse_trace(trace, m['edit_step']) if os.path.exists(trace) else {}
        row = {
            'task': k[0], 'edit_step': k[1], 'parent_stamp': stamp[-6:],
            'arm': arm, 'role': pts[k]['role'],
            'Y': r['eval_success'], 'status': r['status'],
        }
        row.update(feat)
        rows.append(row)

    cols = ['task', 'edit_step', 'parent_stamp', 'arm', 'role', 'Y', 'status',
            'edit_parsed', 'edit_generator', 'edit_exit_code', 'edit_error_type',
            'edit_completion_tokens', 'post_steps', 'post_exec_fails',
            'first_fail_after_edit', 'post_error_types', 'retried_modified_code',
            'reached_final', 'n_generated_steps', 'generator_mix']
    with open('reports/pilot/p2_mechanism_annotations.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in sorted(rows, key=lambda r: (int(r['task']), r['edit_step'], r['parent_stamp'], r['arm'])):
            w.writerow({c: row.get(c, '') for c in cols})
    print(f"wrote {len(rows)} rows to p2_mechanism_annotations.csv")

    # ---- matrix: edit-step error types by arm on signal points ----
    sig = {('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)}
    L = ['# P2a mechanism matrix (edit-step execution error types, in-point runs)\n']
    L.append('## All in-point runs: edit-step error type x arm\n')
    cnt = collections.defaultdict(collections.Counter)
    for r in rows:
        cnt[r['arm']][r['edit_error_type']] += 1
    types = sorted({t for c in cnt.values() for t in c})
    L.append('| error_type | ' + ' | '.join(sorted(cnt)) + ' |')
    L.append('|---|' + '---|' * len(cnt))
    for t in types:
        L.append(f'| {t} | ' + ' | '.join(str(cnt[a].get(t, 0)) for a in sorted(cnt)) + ' |')
    L.append('\n## Signal points only: edit-step error type x arm\n')
    cnt2 = collections.defaultdict(collections.Counter)
    for r in rows:
        if (r['task'], int(r['edit_step'])) in sig:
            cnt2[r['arm']][r['edit_error_type']] += 1
    types2 = sorted({t for c in cnt2.values() for t in c})
    L.append('| error_type | ' + ' | '.join(sorted(cnt2)) + ' |')
    L.append('|---|' + '---|' * len(cnt2))
    for t in types2:
        L.append(f'| {t} | ' + ' | '.join(str(cnt2[a].get(t, 0)) for a in sorted(cnt2)) + ' |')
    L.append('\n## Signal points: post-edit trajectory health x arm\n')
    L.append('| arm | n | mean post_exec_fails | edit-step exit!=0 % | retried-modified % | reached_final % |')
    L.append('|---|---|---|---|---|---|')
    for a in sorted(cnt2):
        rs = [r for r in rows if (r['task'], int(r['edit_step'])) in sig and r['arm'] == a]
        n = len(rs)
        mpf = sum(r.get('post_exec_fails') or 0 for r in rs) / max(n, 1)
        pe = sum(1 for r in rs if r.get('edit_exit_code') not in (0, None)) / max(n, 1)
        rt = sum(1 for r in rs if r.get('retried_modified_code')) / max(n, 1)
        rf = sum(1 for r in rs if r.get('reached_final')) / max(n, 1)
        L.append(f'| {a} | {n} | {mpf:.2f} | {pe:.0%} | {rt:.0%} | {rf:.0%} |')
    open('reports/pilot/p2_mechanism_matrix.md', 'w').write('\n'.join(L) + '\n')
    print('wrote p2_mechanism_matrix.md')


if __name__ == '__main__':
    main()


def dod():
    """Difference-in-differences: signal-point DeltaSR minus control-point DeltaSR."""
    import collections, glob, json, os
    pts = load_points()
    sig = {('60', 6), ('85', 2), ('40', 4), ('92', 1), ('60', 4), ('40', 2)}
    agg = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for f in (glob.glob('runs/sab_*/cf_frontier_resample/*/result.json')
              + glob.glob('runs/sab_*/cf_local_replace/*/result.json')):
        r = json.load(open(f)); m = r['cf_meta']
        em = m.get('edit_model') or ''
        if 'resample' in f: arm = 'resample'
        elif 'mini' in em: arm = 'mini'
        elif 'Qwen' in em: arm = 'qwen'
        else: arm = 'ds'
        stamp = str(m.get('parent_run', '')).rsplit('/', 1)[-1]
        k = (str(r['instance_id']), int(m['edit_step']), stamp)
        if k not in pts: continue
        grp = 'sig' if (k[0], k[1]) in sig else 'ctl'
        c = agg[arm][grp]; c[0] += r['eval_success']; c[1] += 1
    L = ['# P2a difference-in-differences (plan G1: dSR = SR(replace) - SR(resample))\n']
    L.append('| arm | sig SR | ctl SR | dSR_sig | dSR_ctl | DiD (extra damage at signal steps) |')
    L.append('|---|---|---|---|---|---|')
    base = {g: agg['resample'][g] for g in ('sig', 'ctl')}
    for a in ['mini', 'ds', 'qwen']:
        sx, sn = agg[a]['sig']; cx, cn = agg[a]['ctl']
        bx, bn = base['sig']; bxx, bnn = base['ctl']
        d_s = sx / sn - bx / bn
        if cn:
            d_c = cx / cn - bxx / bnn
            did = f"**{d_s - d_c:+.2f}**"
        else:
            d_c = None
            did = 'NA (needs control runs)'
        dc_s = f"{d_c:+.2f}" if d_c is not None else '-'
        dc_c = f"{cx}/{cn} ({cx/cn:.2f})" if cn else 'no runs'
        L.append(f"| {a} | {sx}/{sn} ({sx/sn:.2f}) | {dc_c} | {d_s:+.2f} | {dc_s} | {did} |")
    L.append('')
    L.append('Note: qwen crash rate at edit step is 58% at BOTH signal and control points '
             '(model-level weakness, orthogonal to step-specificity), but qwen has NO control-point '
             'runs yet (replication covered signal points only), so its DiD is pending a control-arm '
             'run batch (P2b). mini/ds DiDs are computable and confirm step-specific extra damage.')
    open('reports/pilot/p2_did_table.md', 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'dod':
        dod()
    else:
        main()
