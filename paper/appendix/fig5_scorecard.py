"""Regenerates fig5_scorecard.pdf/.png (paper/figures/).

General version. The old scorecard showed 12 predictions
for the Llama-IBP cell only. This version shows the SIX predictions that carry
a git-frozen bar in ALL FOUR held-out cells (Llama det / Llama IBP / Qwen det /
Qwen IBP), each cell judged against its own registered criteria: 22 of 24 pass.
The two misses: P3 Qwen det (direction reversed at L75/L78) and P5 Qwen IBP
(judge responds reversed, 50/50). The other six claims were registered in only
some cells (preregs were written at different times); their numbers live in
fig5_scorecard.md and in figs 3/B.

Verdict sources (see fig5_scorecard.md for the full 12x4 table):
- ICML_paper/preregistration_{llama,qwen}/PREREGISTRATION.md (frozen bars)
- sign-circuit-anon/preregistration_llama/{PREREGISTRATION_IBP,FINDINGS_IBP}.md
- GITHUB UPLOADS/Qwen/workbooks_{4x4_DET,IBP}/FINDINGS_*.md
- GITHUB UPLOADS/{Llama,Qwen}/heldout_*/s01-s09 JSONs

This script renders the verdicts; it does not recompute them (verify_all.py
in this folder re-derives the checkable numbers from the raw JSONs).
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
OUT = HERE.parent / 'figures' / 'fig5_scorecard'

GREEN = '#2E7D32'; RED = '#C0392B'; NAVY = '#1E2761'; DGRAY = '#555555'; GRAY = '#9A9A9A'
rows = [
    ('P1', 'Errors decided late',                       'P', 'P', 'P', 'P'),
    ('P2', 'Habit layers write the sign (DLA > 0)',     'P', 'P', 'P', 'P'),
    ('P3', 'One direction separates − from +',          'P', 'P', 'F', 'P'),
    ('P4', 'Subtracting the direction: dose-response',  'P', 'P', 'P', 'P'),
    ('P5', 'Injected error signal moves corrects',      'P', 'P', 'P', 'F'),
    ('P6', 'Steering moves corrects; control doesn’t',  'P', 'P', 'P', 'P'),
]
cols = ['det 4×4', 'integration', 'det 4×4', 'integration']
tally = ['6/6', '6/6', '5/6', '5/6']

fig, ax = plt.subplots(figsize=(11.0, 4.6)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

def mark(v):
    return ('✓', GREEN, 'bold') if v == 'P' else ('✗', RED, 'bold')

ax.text(0.02, 0.945, 'Six predictions frozen in all four cells — 22 of 24 held-out checks passed',
        fontsize=16, fontweight='bold', color='k')
xs = [0.585, 0.695, 0.825, 0.935]
ax.text(0.64, 0.845, 'Llama-3.3-70B', ha='center', fontsize=11, fontweight='bold', color=NAVY)
ax.text(0.88, 0.845, 'Qwen2.5-72B', ha='center', fontsize=11, fontweight='bold', color=NAVY)
ax.plot([0.545, 0.735], [0.828, 0.828], color=NAVY, lw=1)
ax.plot([0.785, 0.975], [0.828, 0.828], color=NAVY, lw=1)
for x, c in zip(xs, cols):
    ax.text(x, 0.785, c, ha='center', fontsize=9.5, color=DGRAY)
ax.text(0.048, 0.785, 'Claim (plain words)', fontsize=10.5, fontweight='bold', color='k')

y0, dy = 0.705, 0.093
for i, (bid, claim, v1, v2, v3, v4) in enumerate(rows):
    y = y0 - i * dy
    ax.text(0.012, y, bid, fontsize=10.5, fontweight='bold', color='k')
    ax.text(0.062, y, claim, fontsize=11.5, color='k')
    for x, v in zip(xs, (v1, v2, v3, v4)):
        s, c, w = mark(v); ax.text(x, y, s, ha='center', fontsize=13, color=c, fontweight=w)
y = y0 - len(rows) * dy - 0.008
ax.plot([0.012, 0.985], [y + 0.058, y + 0.058], color='#CCCCCC', lw=1)
ax.text(0.062, y, 'held-out checks passed', fontsize=10.5, fontweight='bold', color='k')
for x, t in zip(xs, tally):
    ax.text(x, y, t, ha='center', fontsize=11.5, fontweight='bold', color=NAVY)

ax.text(0.012, 0.025, 'Bars git-frozen per cell before any held-out number existed; each cell judged only against its own registered criteria.',
        fontsize=8.5, color=GRAY)
fig.tight_layout()
fig.savefig(f'{OUT}.pdf'); fig.savefig(f'{OUT}.png', dpi=200)
print('saved', OUT)
