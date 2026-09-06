"""Builds draft/numbers_ledger_redteam.md — the master numbers ledger.

Every AUTO number is recomputed here from the raw s01–s09 JSONs; no number
is typed by hand. MANUAL entries name the exact source file to open.
After computing, each key number is searched for in the draft
(paper_draft.md) and reported FOUND or MISSING.

Run:  python3 make_numbers_ledger.py   (from paper/appendix/)
"""
import json, math, statistics as st
from pathlib import Path

HERE = Path(__file__).parent
G = HERE.parent.parent                      # .../GITHUB UPLOADS
DRAFT = HERE.parent / 'draft' / 'paper_draft.md'
OUT = HERE.parent / 'draft' / 'numbers_ledger_redteam.md'

def load(p):
    d = json.load(open(p))
    if isinstance(d, dict) and 'results' in d: d = d['results']
    if isinstance(d, dict):
        return [v for k, v in d.items() if not str(k).startswith('__')]
    return d

L = []          # ledger lines
CHECKS = []     # (label, [strings to find in draft])

def sec(t): L.append(f"\n## {t}\n")
def row(t): L.append(t)
def chk(label, *strings): CHECKS.append((label, list(strings)))

cells = {('Llama', 'det'): 'Llama/heldout_4x4_DET', ('Qwen', 'det'): 'Qwen/heldout_4x4_DET',
         ('Llama', 'ibp'): 'Llama/heldout_IBP',     ('Qwen', 'ibp'): 'Qwen/heldout_IBP'}
disc  = {('Llama', 'det'): ('Llama/discovery_4x4_DET', 'llama'), ('Qwen', 'det'): ('Qwen/discovery_4x4_DET', 'det_4x4'),
         ('Llama', 'ibp'): ('Llama/discovery_IBP', 'ibp'),       ('Qwen', 'ibp'): ('Qwen/discovery_IBP', 'ibp')}

def lens_files(base, task, tag):
    stem = 'det_4x4' if task == 'det' else 'ibp'
    return G / base / 's01_logit_lens' / f'{stem}_{tag}_expA_logit_lens.json'

def ws(r): return r.get('written_sign') or r.get('sign')

# ---------- 1. Table 1 ----------
sec('1. Table 1 — held-out counts and written-sign splits  [AUTO from s01 lens JSONs]')
row('| Cell | Errors | Corrects | Total | Wrote + | Wrote − | (+ = cor-wrote-+ + err-wrote-+) |')
row('|---|---|---|---|---|---|---|')
for (m, t), base in cells.items():
    err = load(lens_files(base, t, 'error')); cor = load(lens_files(base, t, 'correct'))
    ep = sum(1 for r in err if ws(r) == '+'); cp = sum(1 for r in cor if ws(r) == '+')
    em = len(err) - ep; cm = len(cor) - cp
    plus, minus = ep + cp, em + cm
    row(f"| {m} {t} | {len(err)} | {len(cor)} | {len(err)+len(cor)} | {plus} | {minus} | {cp} + {ep} / {cm} + {em} |")
    chk(f"Table1 {m} {t} err/cor", str(len(err)), str(len(cor)))
    if t == 'det':
        chk(f"Table1 {m} {t} wrote+/-", str(plus), str(minus), f"{cp} + {ep}", f"{cm} + {em}")

sec('1b. Discovery counts  [AUTO from discovery s01 lens JSONs]')
row('| Cell | Errors | Corrects |')
row('|---|---|---|')
for (m, t), (base, stem) in disc.items():
    e = load(G / base / 's01_logit_lens' / (f'{stem}_error_logit_lens.json' if stem == 'llama' else f'{stem}_error_expA_logit_lens.json'))
    c = load(G / base / 's01_logit_lens' / (f'{stem}_correct_logit_lens.json' if stem == 'llama' else f'{stem}_correct_expA_logit_lens.json'))
    row(f"| {m} {t} | {len(e)} | {len(c)} |")
    chk(f"Discovery {m} {t}", str(len(e)), str(len(c)))

# ---------- 2. §3 late peaks ----------
sec('2. §3 / Fig 1 — errors peaking at layer >= 60 of 80  [AUTO]')
row('| Cell | Late peaks | of | % |')
row('|---|---|---|---|')
for (m, t), base in cells.items():
    err = load(lens_files(base, t, 'error'))
    late = sum(1 for r in err if r['peak_layer'] >= 60)
    row(f"| {m} {t} | {late} | {len(err)} | {100*late/len(err):.0f}% |")
    chk(f"Late peaks {m} {t}", f"{late} of {len(err)}")

# ---------- 3. Appendix B (Qwen det) ----------
sec('3. Appendix B — Qwen det layer-0 lean  [AUTO]')
qe = load(lens_files('Qwen/heldout_4x4_DET', 'det', 'error'))
l0 = [r for r in qe if r['peak_layer'] == 0]
pe = [r for r in qe if ws(r) == '+']; me = [r for r in qe if ws(r) == '-']
row(f"- layer-0 peaks among 147 held-out errors: **{len(l0)}** (all minus-writers: {sum(1 for r in l0 if ws(r)=='-')})")
row(f"- plus errors peaking late (>=60): **{sum(1 for r in pe if r['peak_layer']>=60)}/{len(pe)}**; minus errors: **{sum(1 for r in me if r['peak_layer']>=60)}/{len(me)}**")
qd = load(G / 'Qwen/discovery_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json')
row(f"- late-peak rate discovery -> held-out: **{100*sum(1 for r in qd if r['peak_layer']>=60)/len(qd):.0f}% -> {100*sum(1 for r in qe if r['peak_layer']>=60)/len(qe):.0f}%**")
row("- (the plus/minus split above is figure-level detail — the draft quotes only the pooled 90/147 = 61%, checked in §2 of this ledger)")
chk('AppB 48 layer-0', str(len(l0)))

# ---------- 4. Fig C1 key steps ----------
sec('4. Appendix C / Fig C1 — per-layer steps by written sign  [AUTO, same math as figA script]')
row('| Model | Layer | +writers (written frame) | −writers (written frame) |')
row('|---|---|---|---|')
for m, keyL in [('Llama', [77, 79]), ('Qwen', [75, 78])]:
    steps = {'+': {}, '-': {}}
    for tag in ['correct', 'error']:
        for r in load(lens_files(cells[(m, 'det')], 'det', tag)):
            s = ws(r); ld = r['layer_diffs']; Ls = sorted(ld, key=int)
            pl = [ld[l] if s == '+' else -ld[l] for l in Ls]
            for i in range(1, len(pl)): steps[s].setdefault(int(Ls[i]), []).append(pl[i] - pl[i-1])
    for lay in keyL:
        p = st.mean(steps['+'][lay]); mm = st.mean([-v for v in steps['-'][lay]])
        row(f"| {m} | L{lay} | {p:+.1f} | {mm:+.1f} |")
        # The draft quotes only three of these eight numbers, and quotes the
        # minus-writer value in the SIGN frame (pushes-minus = negative), so
        # written-frame +x appears in the draft as -x. Check only what is quoted.
        if (m, lay) == ('Llama', 79):
            chk(f"C1 {m} L{lay} (draft quotes +4.8 / -3.8, sign frame)", f"{p:+.1f}", f"{-mm:+.1f}")
        elif (m, lay) == ('Qwen', 78):
            chk(f"C1 {m} L{lay} (+writers, quoted as -5.4)", f"{p:+.1f}")
        else:
            row(f"|  |  | (L{lay} values are figure-only — not quoted in the draft text) |  |")

# ---------- 5. Table D1 / Fig D1 ----------
sec('5. Appendix D — five-model accounting  [AUTO, same rule as fig4 script]')
models = [('Phi-4 14B', G/'Small Models/Phi/determinant/expA_logit_lens.json', lambda pk: False),
          ('Mistral-Small 24B', G/'Small Models/Mistral/determinant/expA_logit_lens.json', lambda pk: False),
          ('Gemma-3 27B', G/'Small Models/Gemma/determinant/expA_logit_lens.json', lambda pk: 8 <= pk <= 13),
          ('Llama-3.3 70B', G/'Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json', lambda pk: False),
          ('Qwen 72B', G/'Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json', lambda pk: pk == 0)]
row('| Model | Total | Final lead < +2 (dropped) | Early-site (open circles) | Used | Median depth |')
row('|---|---|---|---|---|---|')
for name, p, early in models:
    kept, art, excl = [], 0, 0
    for r in load(p):
        ld = r['layer_diffs']; Ls = sorted(ld, key=int)
        if ld[Ls[-1]] < 2: excl += 1
        elif early(r['peak_layer']): art += 1
        else: kept.append(r['peak_depth_pct'])
    med = st.median(kept)
    row(f"| {name} | {len(kept)+art+excl} | {excl} | {art} | {len(kept)} | {med:.1f}% |")
    chk(f"D1 {name}", str(excl), str(len(kept)), f"{med:.1f}")

# ---------- 6. Tables E1 / E2 ----------
sec('6. Appendix E — dose-response (s06)  [AUTO]')
row('| Model | Held-out errors | peak<=5 dropped | Used (s06 n) |')
row('|---|---|---|---|')
for m in ['Llama', 'Qwen']:
    err = load(lens_files(cells[(m, 'det')], 'det', 'error'))
    low = sum(1 for r in err if r['peak_layer'] <= 5)
    s06 = load(G / cells[(m, 'det')] / 's06_direction_subtraction/det_4x4_error_direction_subtraction.json')
    row(f"| {m} | {len(err)} | {low} | {len(s06)} |")
    assert len(err) - low == len(s06), f"E1 mismatch {m}"
    chk(f"E1 {m}", str(low), str(len(s06)))
row('')
row('| Model | Layer | a0.5 | a1 | a2 | flips 0.5/1/2 |')
row('|---|---|---|---|---|---|')
for m in ['Llama', 'Qwen']:
    s06 = load(G / cells[(m, 'det')] / 's06_direction_subtraction/det_4x4_error_direction_subtraction.json')
    for lay in sorted(s06[0]['edits']):
        vals, fl = [], []
        for a in ['alpha_0.5', 'alpha_1.0', 'alpha_2.0']:
            vals.append(st.mean(r['edits'][lay][a]['delta_ld'] for r in s06))
            fl.append(sum(r['edits'][lay][a]['flipped'] for r in s06))
        row(f"| {m} | {lay} | {vals[0]:+.2f} | {vals[1]:+.2f} | {vals[2]:+.2f} | {fl[0]}/{fl[1]}/{fl[2]} |")
        if 'L7' in lay: chk(f"E2 {m} {lay}", f"{vals[0]:+.2f}", f"{vals[1]:+.2f}", f"{vals[2]:+.2f}", f"{fl[0]} / {fl[1]} / {fl[2]}")
    rc = st.mean(r['random_ctrl_delta_ld'] for r in s06 if r.get('random_ctrl_delta_ld') is not None)
    row(f"| {m} | random dir | | {rc:+.3f} | | |")
    chk(f"E2 {m} random", f"{rc:+.3f}")

# ---------- 7. Table F1 single-layer ablation ----------
sec('7. Appendix F — single-layer ablation (s05 habit_ablation)  [AUTO]')
row('| Model | Layer | mean delta |')
row('|---|---|---|')
for m in ['Qwen', 'Llama']:
    hab = load(G / cells[(m, 'det')] / 's05_ablations/det_4x4_error_habit_ablation.json')
    lays = sorted({k.split('_')[1] for k in hab[0] if k.startswith('corrector_') and k.endswith('_delta_ld')})
    for lay in lays:
        v = st.mean(r[f'corrector_{lay}_delta_ld'] for r in hab)
        row(f"| {m} | {lay} | {v:+.2f} |")
        chk(f"F1 {m} {lay}", f"{v:+.2f}")

# ---------- 8. Table F2 joint ablation ----------
sec('8. Appendix F — joint ablation (s05 joint)  [AUTO, same math as figB script]')
row('| Cell | n | targeted D | before -> after | null mean | null range | 95% CI |')
row('|---|---|---|---|---|---|---|')
jfiles = {('Llama','det'):'Llama/heldout_4x4_DET/s05_ablations/det_4x4_error_joint_ablation.json',
          ('Llama','ibp'):'Llama/heldout_IBP/s05_ablations/ibp_error_joint_ablation.json',
          ('Qwen','det'):'Qwen/heldout_4x4_DET/s05_ablations/det_4x4_error_joint_ablation.json',
          ('Qwen','ibp'):'Qwen/heldout_IBP/s05_ablations/ibp_error_joint_ablation.json'}
for (m, t), p in jfiles.items():
    recs = load(G / p)
    tgt = [r['target_delta'] for r in recs]
    nn = min(len(r['null_deltas']) for r in recs)
    nm = [st.mean(r['null_deltas'][i] for r in recs) for i in range(nn)]
    mt = st.mean(tgt); b = st.mean(r['baseline_ld'] for r in recs)
    ci = 1.96 * st.stdev(tgt) / math.sqrt(len(tgt))
    row(f"| {m} {t} | {len(recs)} | {mt:+.2f} | {b:+.2f} -> {b+mt:+.2f} | {st.mean(nm):+.2f} | [{min(nm):+.2f}, {max(nm):+.2f}] | ±{ci:.2f} |")
    chk(f"F2 {m} {t}", f"{mt:+.2f}", f"{b:+.2f}", f"{b+mt:+.2f}", f"{st.mean(nm):+.2f}", f"{min(nm):+.2f}", f"{max(nm):+.2f}")

# ---------- 9. Steering (s08, condition C2) ----------
sec('9. Steering — s08 combined_ablation, condition C2 per dose  [AUTO; compare to §5/Appendix H]')
row('| Cell | n in file | dose | mean delta | flips | flips among baseline-top1-wrong |')
row('|---|---|---|---|---|---|')
sfiles = {('Llama','det'):'Llama/heldout_4x4_DET/s08_c2_steering/det_4x4_error_combined_ablation.json',
          ('Llama','ibp'):'Llama/heldout_IBP/s08_c2_steering/ibp_error_combined_ablation.json',
          ('Qwen','det'):'Qwen/heldout_4x4_DET/s08_c2_steering/det_4x4_error_combined_ablation.json',
          ('Qwen','ibp'):'Qwen/heldout_IBP/s08_c2_steering/ibp_error_combined_ablation.json'}
for (m, t), p in sfiles.items():
    try: recs = load(G / p)
    except FileNotFoundError:
        row(f"| {m} {t} | FILE MISSING: {p} | | | | |"); continue
    wrong = [r for r in recs if r.get('baseline_top1_is_wrong_sign')]
    for a in ['a1.0', 'a2.0', 'a3.0']:
        have = [r for r in recs if 'C2' in r['conditions'] and a in r['conditions']['C2']]
        if not have: continue
        dm = st.mean(r['conditions']['C2'][a]['delta_ld'] for r in have)
        fl = sum(r['conditions']['C2'][a]['flipped'] for r in have)
        flw = sum(r['conditions']['C2'][a]['flipped'] for r in have if r.get('baseline_top1_is_wrong_sign'))
        row(f"| {m} {t} | {len(have)} | {a} | {dm:+.2f} | {fl} | {flw}/{len(wrong)} |")

# ---------- 10. MANUAL entries ----------
sec('10. MANUAL entries — open the named file to verify')
row('- Frozen target sets: Llama det L61,69,77,78,79; Llama IBP L64,66,77,78,79; Qwen L71,74,75,77,78 — source: preregistration_llama/, preregistration_qwen/ (anon repo) and paper/appendix ledgers.')
row('- Preregistration counts (24 checks / 22 passed; 37 / 34; three misses P3 Qwen det, P5 Qwen IBP, Qwen IBP ablation descriptive) — source: appendix/fig5_scorecard.md + verification_ledger.md.')
row('- Mistral-Small 26 dropped = 16 ordinary + 10 mislocated probes — source: appendix/fig1_late_decision.md (line ~63) and fig4_universality.md.')
row('- Steering headline (Llama det flips 42/121, D -4.5; Llama IBP 13/14, D -20.7) and specificity (minus-corrects broken Llama 97% / Qwen 40%; plus-corrects 0%) — source: appendix/steering_plus_minus_asymmetry.md + s08 correct-side JSONs; section 9 above gives the raw per-dose numbers to reconcile.')
row('- Qwen IBP judge P5 reversed (50/50) — source: Qwen workbooks FINDINGS_ibp.md §4.')

# ---------- draft cross-check ----------
draft = open(DRAFT, encoding='utf-8').read()
norm = (draft.replace('−', '-').replace('→', '->').replace('×', 'x')
             .replace(' ', ' ').replace(' ', ' '))
sec('11. Draft cross-check — every AUTO number searched in paper_draft.md')
missing = 0
for label, strings in CHECKS:
    bad = [s for s in strings if s not in norm]
    if bad:
        missing += 1
        row(f"- **MISSING** {label}: {bad}")
row(f"- checked {len(CHECKS)} entries ({sum(len(s) for _, s in CHECKS)} strings); "
    f"**{len(CHECKS)-missing} fully found, {missing} with missing strings** (a missing string is not always an error — formatting may differ; open the draft and look).")

OUT.write_text('# Master numbers ledger (red-team reference)\n\n'
    'Generated by appendix/make_numbers_ledger.py — DO NOT hand-edit; rerun the script instead.\n'
    'AUTO = recomputed from raw JSONs at generation time. MANUAL = open the named source.\n'
    + '\n'.join(L) + '\n')
print('wrote', OUT)
print('checks:', len(CHECKS), 'entries;', missing, 'with missing strings')
