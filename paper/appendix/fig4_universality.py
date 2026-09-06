"""Regenerates fig4_universality.pdf/.png (paper/figures/).

Five models (, uniform inclusion rule; Mistral-Large-675B
dropped as FAILED-TECHNICAL — its lens hook captured per-layer MLP deltas, not
the residual stream, so its column was noise on a late-heavy layer grid; see
fig4_universality.md).

Data (read in place):
- Small Models/{Phi,Mistral,Gemma}/determinant/expA_logit_lens.json
- {Llama,Qwen}/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json

Inclusion rule (uniform, all models): keep a case only if the lens clearly
shows the written sign at the output — final-layer lead >= +2 logits. Cases
below that have no readable decision, so their peak depth is meaningless
(this also removes the 10 Mistral-S probe-placement failures, which have
negative final leads). Open gray circles (definition changed from
"<12.5% depth" to the mechanism-based early-lean site of Appendix B):
a rule-passing case peaking at its model's early-lean site — Qwen layer 0
(embedding lookup), Gemma layers 8-13 (self-copying). Shown but excluded
from medians. Other models have no early site.

Expected: used-for-median/total = Phi 26/39, Mistral-S 13/39, Gemma 15/37
(+3 open circles), Llama 138/192, Qwen 74/147 (+20 open circles).
Medians: 85.0 / 95.0 / 88.7 / 98.8 / 96.2 % (Gemma unchanged by the switch).
"""
import json, statistics as st, random
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
G = HERE.parent.parent          # .../GITHUB UPLOADS
OUT = HERE.parent / 'figures' / 'fig4_universality'

# (name, data path, early-lean site predicate on peak_layer — Appendix B)
models = [('Phi\n14B', G / 'Small Models/Phi/determinant/expA_logit_lens.json', lambda pk: False),
          ('Mistral-S\n24B', G / 'Small Models/Mistral/determinant/expA_logit_lens.json', lambda pk: False),
          ('Gemma-3\n27B', G / 'Small Models/Gemma/determinant/expA_logit_lens.json', lambda pk: 8 <= pk <= 13),
          ('Llama-3.3\n70B', G / 'Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json', lambda pk: False),
          ('Qwen\n72B', G / 'Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json', lambda pk: pk == 0)]

def load(p):
    d = json.load(open(p))
    if isinstance(d, dict) and 'results' in d: d = d['results']
    return list(d.values()) if isinstance(d, dict) else d

data = []
for name, p, early in models:
    kept, art, excl = [], [], 0
    for r in load(p):
        ld = r['layer_diffs']; L = sorted(ld, key=int)
        fin = ld[L[-1]]; dp = r['peak_depth_pct']
        if fin < 2: excl += 1
        elif early(r['peak_layer']): art.append(dp)
        else: kept.append(dp)
    data.append((name, kept, art, excl))

BLUE = '#4C709B'; RED = '#C0392B'
random.seed(1)
fig, ax = plt.subplots(figsize=(6.4, 3.4))
ax.axhspan(75, 100, color='#F6E8E4', zorder=0)
ax.text(len(data) - 0.52, 78, 'late zone', color=RED, fontsize=11)
for i, (name, kept, art, excl) in enumerate(data):
    ax.scatter([i + random.uniform(-0.16, 0.16) for _ in kept], kept,
               s=20, color=BLUE, alpha=0.55, edgecolors='none', zorder=2)
    if art:
        ax.scatter([i + random.uniform(-0.16, 0.16) for _ in art], art,
                   s=20, facecolors='none', edgecolors='#999999', linewidths=1.2, zorder=2)
    med = st.median(kept)
    ax.plot([i - 0.26, i + 0.26], [med, med], color=RED, lw=3, zorder=3)
ax.set_xticks(range(len(data)))
ax.set_xticklabels([f"{name}\nn={len(kept)}" for name, kept, art, excl in data], fontsize=11)
ax.set_ylabel("Depth where the wrong sign's\nadvantage peaks (% of layers)", fontsize=11.5)
ax.set_ylim(-3, 103)
ax.set_xlim(-0.6, len(data) - 0.4)
ax.spines[['top', 'right']].set_visible(False)
meds = [st.median(k) for _, k, _, _ in data]
ax.set_title(f"Five models, 14B → 72B: the wrong sign peaks late\n(medians {min(meds):.0f}–{max(meds):.0f}%)",
             fontsize=12.5, fontweight='bold', pad=10)
# footers removed (review feedback): all details live in the paper's Figure D1 caption
fig.tight_layout()
fig.savefig(f'{OUT}.pdf'); fig.savefig(f'{OUT}.png', dpi=200)
print('saved', OUT)
for name, kept, art, excl in data:
    print(name.replace(chr(10), ' '), f"kept {len(kept)} art {len(art)} excl {excl} median {st.median(kept):.1f}%")
