"""verify_all.py — re-derives every checkable paper number fresh from the
GITHUB UPLOADS held-out JSONs and prints PASS/FAIL per ledger entry.

Companion to verification_ledger.md (this folder). Run:
    python3 verify_all.py
Exit code 0 only if every check passes. Entries the ledger marks MANUAL
(verdicts read from git-frozen preregistration/FINDINGS documents) are not
recomputed here; entries marked FLAGGED are known open items (see ledger).


"""
import json, math, statistics as st, sys
from pathlib import Path

G = Path(__file__).parent.parent.parent      # .../GITHUB UPLOADS

def load(p):
    d = json.load(open(G / p))
    if isinstance(d, dict) and 'results' in d: d = d['results']
    return list(d.values()) if isinstance(d, dict) else d

def fin(r):
    ld = r['layer_diffs']; return ld[sorted(ld, key=int)[-1]]

results = []
def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: expected {expected}, got {got}")

# ---------- fig4 (five models, uniform rule: keep iff final lead >= +2; open circle iff peak < 12.5%) ----------
FIG4 = [('Phi',      'Small Models/Phi/determinant/expA_logit_lens.json',      (26, 0, 13, 85.0)),
        ('Mistral-S','Small Models/Mistral/determinant/expA_logit_lens.json',  (13, 0, 26, 95.0)),
        ('Gemma',    'Small Models/Gemma/determinant/expA_logit_lens.json',    (18, 0, 19, 88.7)),
        ('Llama',    'Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json', (138, 0, 54, 98.8)),
        ('Qwen',     'Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json',  (74, 20, 53, 96.2))]
for name, p, exp in FIG4:
    kept, art, excl = [], 0, 0
    for r in load(p):
        f = fin(r); dp = r['peak_depth_pct']
        if f < 2: excl += 1
        elif dp < 12.5: art += 1
        else: kept.append(dp)
    check(f"fig4 {name} (kept, circles, excluded, median%)", exp,
          (len(kept), art, excl, round(st.median(kept), 1)))

# ---------- figB (joint ablation, 4 cells) ----------
FIGB = [('Llama det', 'Llama/heldout_4x4_DET/s05_ablations/det_4x4_error_joint_ablation.json', (192, -4.25, 7.05, -0.67, -1.42, 0.16)),
        ('Llama IBP', 'Llama/heldout_IBP/s05_ablations/ibp_error_joint_ablation.json',         (21, -7.09, 14.61, -0.29, -0.96, 0.69)),
        ('Qwen det',  'Qwen/heldout_4x4_DET/s05_ablations/det_4x4_error_joint_ablation.json',  (147, -2.52, 5.19, -0.42, -1.47, 0.17)),
        ('Qwen IBP',  'Qwen/heldout_IBP/s05_ablations/ibp_error_joint_ablation.json',          (26, -0.98, 10.44, -0.11, -0.70, 0.66))]
for name, p, exp in FIGB:
    d = json.load(open(G / p))
    recs = [v for k, v in d.items() if k != '__summary__']
    tgt = [r['target_delta'] for r in recs]
    nn = min(len(r['null_deltas']) for r in recs)
    nullmeans = [st.mean(r['null_deltas'][i] for r in recs) for i in range(nn)]
    got = (len(recs), round(st.mean(tgt), 2), round(st.mean(r['baseline_ld'] for r in recs), 2),
           round(st.mean(nullmeans), 2), round(min(nullmeans), 2), round(max(nullmeans), 2))
    check(f"figB {name} (n, mean d, baseline, null mean, null min, null max)", exp, got)

# ---------- fig5 P1 (errors decided late: peak_layer >= 60) ----------
P1 = [('Llama det', 'Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json', (152, 192)),
      ('Llama IBP', 'Llama/heldout_IBP/s01_logit_lens/ibp_error_expA_logit_lens.json',         (18, 21)),
      ('Qwen det',  'Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json',  (90, 147)),
      ('Qwen IBP',  'Qwen/heldout_IBP/s01_logit_lens/ibp_error_expA_logit_lens.json',          (25, 26))]
for name, p, exp in P1:
    r = load(p)
    check(f"fig5 P1 {name} (late/n)", exp, (sum(1 for x in r if x.get('peak_layer', 0) >= 60), len(r)))

# ---------- held-out sample sizes (fig1 and elsewhere) ----------
NS = [('Llama det errors',   'Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json',   192),
      ('Llama det corrects', 'Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_correct_expA_logit_lens.json', 130),
      ('Qwen det errors',    'Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json',    147),
      ('Qwen det corrects',  'Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_correct_expA_logit_lens.json',  141)]
for name, p, exp in NS:
    check(f"n {name}", exp, len(load(p)))

print()
n_fail = results.count(False)
print(f"{len(results)} checks, {n_fail} failed")
sys.exit(1 if n_fail else 0)
