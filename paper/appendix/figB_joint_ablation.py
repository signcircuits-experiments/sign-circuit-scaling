"""Regenerates figB_joint_ablation.pdf/.png (paper/figures/).

Data (read in place, fresh from GITHUB UPLOADS — no copies):
- GITHUB UPLOADS/{Llama,Qwen}/heldout_{4x4_DET,IBP}/s05_ablations/
    {det_4x4,ibp}_error_joint_ablation.json

Method: per held-out error question, target_delta = change in the written-sign
logit lead after jointly mean-ablating the identified 5-layer target set;
null_deltas[40] = the same joint ablation for 40 random 5-layer sets.
Per cell: red bar = mean target_delta (±95% CI across questions); gray bar =
mean of the 40 random-set means, whisker = full range of the 40 set means;
navy tag = average reference logit (mean baseline_ld) before -> after the
target ablation. Every number in the figure is a mean across that cell.

Expected (mean delta / n / baseline -> after):
  Llama det  -4.25 / 192 / +7.05 -> +2.80     Llama IBP -7.09 / 21 / +14.61 -> +7.52
  Qwen  det  -2.52 / 147 / +5.19 -> +2.67     Qwen  IBP -0.98 /  26 / +10.44 -> +9.47
Random-set means all sit in [-1.5, +0.7]. Qwen IBP is the weakest cell:
point estimate -0.98 is below its random-set means, but the 95% CI (+-0.90,
n=26) spans the random range and the cell has no frozen bar - descriptive.
Target sets: Llama det {61,69,77,78,79}, Llama IBP {64,66,77,78,79},
Qwen {71,74,75,77,78} both tasks.
"""
import json, math, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
G = HERE.parent.parent          # .../GITHUB UPLOADS
OUT = HERE.parent / 'figures' / 'figB_joint_ablation'

cells = {('Llama', 'det'): G / 'Llama/heldout_4x4_DET/s05_ablations/det_4x4_error_joint_ablation.json',
         ('Llama', 'ibp'): G / 'Llama/heldout_IBP/s05_ablations/ibp_error_joint_ablation.json',
         ('Qwen', 'det'): G / 'Qwen/heldout_4x4_DET/s05_ablations/det_4x4_error_joint_ablation.json',
         ('Qwen', 'ibp'): G / 'Qwen/heldout_IBP/s05_ablations/ibp_error_joint_ablation.json'}
tsets = {('Llama', 'det'): 'L61,69,77,78,79', ('Llama', 'ibp'): 'L64,66,77,78,79',
         ('Qwen', 'det'): 'L71,74,75,77,78', ('Qwen', 'ibp'): 'L71,74,75,77,78'}

D = {}
for k, p in cells.items():
    d = json.load(open(p))
    recs = [v for kk, v in d.items() if kk != '__summary__']
    tgt = [r['target_delta'] for r in recs]
    nn = min(len(r['null_deltas']) for r in recs)
    nullmeans = [st.mean(r['null_deltas'][i] for r in recs) for i in range(nn)]
    m = st.mean(tgt); h = 1.96 * st.stdev(tgt) / math.sqrt(len(tgt))
    b = st.mean(r['baseline_ld'] for r in recs)
    D[k] = dict(n=len(recs), m=m, h=h, nm=st.mean(nullmeans),
                nmin=min(nullmeans), nmax=max(nullmeans), b=b)

RED = '#C0392B'; GRAY = '#B8B8B8'; DGRAY = '#7a7a7a'; NAVY = '#1E2761'
fig, axes = plt.subplots(1, 2, figsize=(10.0, 5.4), sharey=True)
w = 0.36
for ax, model in zip(axes, ['Llama', 'Qwen']):
    for xi, task in enumerate(['det', 'ibp']):
        c = D[(model, task)]
        ax.bar(xi - w/2, c['m'], width=w, color=RED, zorder=2,
               label='identified 5-layer set' if (xi == 0 and model == 'Qwen') else None)
        ax.errorbar(xi - w/2, c['m'], yerr=c['h'], fmt='none', ecolor='#7a1f16', elinewidth=1.2, capsize=3, zorder=3)
        ax.bar(xi + w/2, c['nm'], width=w, color=GRAY, zorder=2,
               label='40 random 5-layer sets (mean)' if (xi == 0 and model == 'Qwen') else None)
        ax.errorbar(xi + w/2, (c['nmin'] + c['nmax'])/2, yerr=(c['nmax'] - c['nmin'])/2, fmt='none',
                    ecolor=DGRAY, elinewidth=1.2, capsize=3, zorder=3)
        ax.annotate(f"mean {c['m']:+.2f}", xy=(xi - w/2, c['m']), xytext=(xi - w/2 - 0.05, c['m'] - c['h'] - 0.32),
                    ha='center', fontsize=10, fontweight='bold', color=RED)
        ax.annotate(f"mean {c['nm']:+.2f}", xy=(xi + w/2, c['nm']), xytext=(xi + w/2 + 0.02, c['nmin'] - 0.32),
                    ha='center', fontsize=8.5, color=DGRAY)
        ax.annotate(f"average reference logit\n{c['b']:+.2f} → {c['b'] + c['m']:+.2f}",
                    xy=(xi, 0), xytext=(xi, 0.55), ha='center', fontsize=9, color=NAVY, fontweight='bold')
    ax.axhline(0, color='k', lw=0.9)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"determinant (n={D[(model, 'det')]['n']})\n{tsets[(model, 'det')]}",
                        f"integration (n={D[(model, 'ibp')]['n']})\n{tsets[(model, 'ibp')]}"], fontsize=9)
    ax.set_title('Llama-70B' if model == 'Llama' else 'Qwen-72B', fontsize=13)
    ax.set_xlim(-0.65, 1.65)
    ax.yaxis.grid(True, color='#E5E5E5', lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].set_ylim(-10.4, 2.2)
axes[0].set_ylabel("Mean Δ written-sign logit lead after joint mean-ablation\n(negative = wrong sign weakens)")
axes[1].legend(loc='lower left', frameon=False, fontsize=9.5)
fig.suptitle("Ablating the five identified layers together collapses the written sign;\nrandom five-layer sets do almost nothing", fontsize=13.5)
# footers removed (review feedback): all details live in the paper's Figure F1 caption
fig.tight_layout(rect=[0, 0, 1, 0.895])
fig.savefig(f'{OUT}.pdf'); fig.savefig(f'{OUT}.png', dpi=200)
print('saved', OUT)
for k, c in D.items():
    print(k, f"n={c['n']} mean {c['m']:+.2f} baseline {c['b']:+.2f} -> {c['b'] + c['m']:+.2f} "
          f"null mean {c['nm']:+.2f} range [{c['nmin']:+.2f}, {c['nmax']:+.2f}]")
