"""Regenerates figA_stamper_vs_adaptive.pdf/.png (paper/figures/).

Data (read in place, no copies needed — same tree):
- GITHUB UPLOADS/{Llama,Qwen}/heldout_4x4_DET/s01_logit_lens/
    det_4x4_{correct,error}_expA_logit_lens.json

Method: for each question, layer_diffs[L] IS the written-sign lead (do NOT flip
for '+' writers). Convert to the plus frame (negate minus-writers), take per-layer
steps pl[i]-pl[i-1] = that layer's push toward "+", pool correct+error, split by
written sign. The FIGURE is drawn in the WRITTEN-SIGN frame (minus-writers' steps
negated back), so positive always means "helps the answer":
- adaptive layer -> both bars positive (Llama L77/L79)
- minus stamper  -> minus-writers positive but PLUS-writers NEGATIVE (Qwen L75/L78)

Expected: Llama n=122 '+'/200 '-'; Qwen 92/196.
Key steps, plus-writers (stamp test): Llama L77 +1.4, L79 +4.8; Qwen L75 -1.6, L78 -5.4.
Minus-writers (written frame): Llama L77 +3.7, L79 +3.8; Qwen L75 +2.9, L78 +1.3.
All key layers: plus-vs-0 and plus-vs-minus t-tests p<1e-7 except Llama L78
(near zero, not a key layer here); survives Bonferroni over L70-79.
Pattern holds in correct and error subsets separately.
"""
import json, math, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
G = HERE.parent.parent          # .../GITHUB UPLOADS
OUT = HERE.parent / 'figures' / 'figA_stamper_vs_adaptive'

def load(p):
    d = json.load(open(p)); d = d.get('results', d)
    return list(d.values()) if isinstance(d, dict) else d

data = {}
for model in ['Llama', 'Qwen']:
    steps = {'+': {}, '-': {}}
    for tag in ['correct', 'error']:
        f = G / model / 'heldout_4x4_DET' / 's01_logit_lens' / f'det_4x4_{tag}_expA_logit_lens.json'
        for r in load(f):
            ws = r.get('written_sign') or r.get('sign')
            ld = r['layer_diffs']; L = sorted(ld, key=int)
            pl = [ld[l] if ws == '+' else -ld[l] for l in L]   # plus frame
            for i in range(1, len(pl)):
                steps[ws].setdefault(i, []).append(pl[i] - pl[i - 1])
    data[model] = steps

def mci(v):
    m = st.mean(v); h = 1.96 * st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else 0
    return m, h

BLUE = '#2C7BB6'; ORNG = '#B85042'; RED = '#C0392B'
key = {'Llama': [77, 79], 'Qwen': [75, 78]}
Ls = list(range(70, 80))
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.7))
for ax, model in zip(axes, ['Llama', 'Qwen']):
    steps = data[model]
    P = [mci(steps['+'][L]) for L in Ls]                      # plus-writers (frame identical)
    M = [mci([-v for v in steps['-'][L]]) for L in Ls]        # minus-writers -> written frame
    x = list(range(len(Ls))); w = 0.38
    for L in key[model]:
        i = Ls.index(L)
        ax.axvspan(i - 0.5, i + 0.5, color='#F2E9E4', zorder=0)
    ax.bar([i - w/2 for i in x], [m for m, _ in P], width=w, color=BLUE, label='when model writes «+»', zorder=2)
    ax.bar([i + w/2 for i in x], [m for m, _ in M], width=w, color=ORNG, label='when model writes «−»', zorder=2)
    ax.errorbar([i - w/2 for i in x], [m for m, _ in P], yerr=[h for _, h in P], fmt='none', ecolor='#1a4a70', elinewidth=1, zorder=3)
    ax.errorbar([i + w/2 for i in x], [m for m, _ in M], yerr=[h for _, h in M], fmt='none', ecolor='#6e2f26', elinewidth=1, zorder=3)
    ax.axhline(0, color='k', lw=0.9)
    for L in key[model]:
        i = Ls.index(L)
        pv, ph = P[i]; mv, mh = M[i]
        if pv > 0 and mv > 0:
            ax.annotate(f"L{L}", xy=(i, 0), xytext=(i - 0.30, max(pv + ph, mv + mh) + 0.35), color=RED, fontweight='bold', fontsize=12)
        else:
            ax.annotate(f"L{L}", xy=(i, 0), xytext=(i + 0.35, min(pv - ph, mv - mh) - 0.15), color=RED, fontweight='bold', fontsize=12)
    lo = min(min(m - h for m, h in P), min(m - h for m, h in M))
    hi = max(max(m + h for m, h in P), max(m + h for m, h in M))
    ax.set_ylim(lo - 1.6, hi + 0.6)
    ax.set_xticks(x); ax.set_xticklabels([str(L) for L in Ls])
    ax.set_xlabel("MLP layer")
    ax.set_title('Llama-70B' if model == 'Llama' else 'Qwen-72B', fontsize=13)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_xlim(-0.8, len(Ls) - 1 + 1.6)
axes[0].set_ylabel("Push toward the WRITTEN sign (lens step)")
axes[0].legend(loc='upper left', frameon=False, fontsize=9.5)
axes[0].text(0.38, 0.03, "both bars UP at L77/L79:\nsupports the answer, either sign",
             transform=axes[0].transAxes, ha='center', va='bottom', fontsize=9.5, color='#1a4a70', style='italic')
axes[1].text(0.40, 0.03, "blue DOWN at L75/L78: fights the\nwritten «+» → fixed «−» stamp",
             transform=axes[1].transAxes, ha='center', va='bottom', fontsize=9.5, color=RED, style='italic')
# suptitle removed (moved into main text as Fig 2 left; captions carry the takeaway)
# footer removed (review feedback): all details live in the paper's Figure C1 caption
fig.tight_layout()
fig.savefig(f'{OUT}.pdf'); fig.savefig(f'{OUT}.png', dpi=200)
print('saved', OUT)
for model in data:
    steps = data[model]
    print(f"{model}: n+={len(steps['+'][79])} n-={len(steps['-'][79])}", end='  ')
    for L in key[model]:
        mp, _ = mci(steps['+'][L]); mm, _ = mci([-v for v in steps['-'][L]])
        print(f"L{L}: +writers {mp:+.1f}, -writers(written frame) {mm:+.1f}", end='  ')
    print()
