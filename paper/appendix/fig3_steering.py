"""Regenerates fig3_steering.pdf/.png (paper/figures/).

Font-size rebuild (feedback: text too small
at 0.405\\textwidth). Layout identical to the original two-column figure:
top row = mean lead change vs dose, bottom row = flips to correct.

Data (read in place, C2 = the paper's steering arm; minus-written errors only):
- {Llama,Qwen}/heldout_4x4_DET/s08_c2_steering/det_4x4_error_combined_ablation.json
- {Llama,Qwen}/heldout_IBP/s08_c2_steering/ibp_error_combined_ablation.json
- matching *_ctrl_mag.json (CTRL_MAG = magnitude-matched random control)

Qwen det file already contains only the 99-case late-circuit subset
(25 minus-written). Published numbers are asserted before saving:
Llama det flips 4/13/42 of 121 (mean a3 -4.5), Llama IBP 2/5/13 of 14 (-20.7),
Qwen det 0/0/6 of 25 (-8.1), Qwen IBP 0/3/10 of 25 (-7.2).
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
G = HERE.parent.parent          # .../GITHUB UPLOADS
OUT = HERE.parent / 'figures' / 'fig3_steering'
ALPHAS = ['a1.0', 'a2.0', 'a3.0']
BLUE = '#4C709B'; RED = '#C0392B'; GREY = '#888888'


def minus_rows(path):
    d = json.load(open(path))
    return [r for r in d['results'].values() if r['written_sign'] == '-']


def series(rows, cond):
    means, flips = [], []
    for a in ALPHAS:
        means.append(sum(r['conditions'][cond][a]['delta_ld'] for r in rows) / len(rows))
        flips.append(sum(1 for r in rows if r['conditions'][cond][a]['flipped']))
    return means, flips


panels = []
for model, tag in [('Llama-3.3-70B', 'steer L77+L79'), ('Qwen2.5-72B', 'steer L75+L78 MLPs')]:
    m = 'Llama' if 'Llama' in model else 'Qwen'
    det = minus_rows(G / f'{m}/heldout_4x4_DET/s08_c2_steering/det_4x4_error_combined_ablation.json')
    ibp = minus_rows(G / f'{m}/heldout_IBP/s08_c2_steering/ibp_error_combined_ablation.json')
    cdet = minus_rows(G / f'{m}/heldout_4x4_DET/s08_c2_steering/det_4x4_error_ctrl_mag.json')
    cibp = minus_rows(G / f'{m}/heldout_IBP/s08_c2_steering/ibp_error_ctrl_mag.json')
    panels.append((model, tag, det, ibp, cdet, cibp))

# ---- assertions: figure must reproduce the published numbers exactly ----
chk = {}
for model, tag, det, ibp, cdet, cibp in panels:
    chk[model] = (len(det), len(ibp), series(det, 'C2'), series(ibp, 'C2'))
(mL, fL) = chk['Llama-3.3-70B'][2]; (mLi, fLi) = chk['Llama-3.3-70B'][3]
(mQ, fQ) = chk['Qwen2.5-72B'][2]; (mQi, fQi) = chk['Qwen2.5-72B'][3]
assert chk['Llama-3.3-70B'][0] == 121 and fL == [4, 13, 42] and round(mL[2], 1) == -4.5
assert chk['Llama-3.3-70B'][1] == 14 and fLi == [2, 5, 13] and round(mLi[2], 1) == -20.7
assert chk['Qwen2.5-72B'][0] == 25 and fQ == [0, 0, 6] and round(mQ[2], 1) == -8.1
assert chk['Qwen2.5-72B'][1] == 25 and fQi == [0, 3, 10] and round(mQi[2], 1) == -7.2
print('assertions passed: figure reproduces the published numbers')

# ---- plot (small canvas + full-size fonts => large print text) ----
plt.rcParams.update({'font.size': 10})
fig, axes = plt.subplots(2, 2, figsize=(7.6, 4.9), height_ratios=[1.15, 1])
X = [1, 2, 3]
for col, (model, tag, det, ibp, cdet, cibp) in enumerate(panels):
    axt, axb = axes[0][col], axes[1][col]
    mdet, fdet = series(det, 'C2'); mibp, fibp = series(ibp, 'C2')
    mcd, _ = series(cdet, 'CTRL_MAG'); mci, _ = series(cibp, 'CTRL_MAG')
    axt.plot(X, mdet, 'o-', color=BLUE, lw=2, ms=5, label=f'determinant (n={len(det)})')
    axt.plot(X, mibp, 's-', color=RED, lw=2, ms=5, label=f'integration (n={len(ibp)})')
    axt.plot(X, mcd, '--', color=GREY, lw=1.5, label='random control')
    axt.plot(X, mci, '--', color=GREY, lw=1.5)
    axt.axhline(0, color='#CCCCCC', lw=0.8, zorder=0)
    close = abs(mdet[2] - mibp[2]) < 2.5
    axt.annotate(f'{mdet[2]:.1f}', (3, mdet[2]),
                 xytext=(-32, -14 if close else (-4 if mdet[2] > mibp[2] else 8)),
                 textcoords='offset points', color=BLUE, fontsize=11, fontweight='bold')
    axt.annotate(f'{mibp[2]:.1f}', (3, mibp[2]),
                 xytext=(-14, 8) if close else ((-34, 8) if mdet[2] > mibp[2] else (-34, -12)),
                 textcoords='offset points', color=RED, fontsize=11, fontweight='bold')
    axt.set_title(f'{model} — {tag}', fontsize=12, fontweight='bold')
    axt.set_xticks(X); axt.tick_params(labelsize=10)
    axt.legend(fontsize=8.5, loc='lower left', frameon=False)
    axt.spines[['top', 'right']].set_visible(False)
    w = 0.35
    axb.bar([x - w / 2 for x in X], [f / len(det) for f in fdet], w, color=BLUE)
    axb.bar([x + w / 2 for x in X], [f / len(ibp) for f in fibp], w, color=RED)
    for x, f in zip(X, fdet):
        axb.annotate(f'{f}/{len(det)}', (x - w / 2, f / len(det)), ha='center',
                     xytext=(0, 3), textcoords='offset points', fontsize=9, color=BLUE)
    for x, f in zip(X, fibp):
        axb.annotate(f'{f}/{len(ibp)}', (x + w / 2, f / len(ibp)), ha='center',
                     xytext=(0, 3), textcoords='offset points', fontsize=9, color=RED)
    axb.set_ylim(0, 1.08); axb.set_xticks(X); axb.tick_params(labelsize=10)
    axb.set_xlabel(r'steering strength $\alpha$', fontsize=11)
    axb.spines[['top', 'right']].set_visible(False)
axes[0][0].set_ylabel("Mean shift in the wrong\nsign's lead (logits)", fontsize=11)
axes[1][0].set_ylabel("Fraction of wrong '$-$'\nflipped to correct '$+$'", fontsize=11)
fig.tight_layout()
fig.savefig(f'{OUT}.pdf'); fig.savefig(f'{OUT}.png', dpi=220)
print('saved', OUT)
