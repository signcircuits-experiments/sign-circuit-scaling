#!/usr/bin/env python3
"""Figure B1: layer-0 lean is a probe-token lookup (Qwen, 288 held-out det cases).
Top: the real tokens of NC_4x4_det_201 around the probe position.
Bottom: mean layer-0 lead grouped by probe token, vs embedding-table prediction.
Regenerates from qwen_probe_token_lean_results.json (lean_tests)."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

res = json.load(open('/sessions/admiring-lucid-turing/mnt/ICML_paper/lean_tests/qwen_probe_token_lean_results.json'))
gt = {g['probe_token']: g for g in res['group_table']}

# combine digit groups like the original figure
digits = [gt[d] for d in ('1','2','8','3','9') if d in gt]
dn = sum(g['n'] for g in digits)
dvals = []
for g in digits: dvals += [g['mean_L0_lead']]*g['n']
digit = {'n': dn, 'mean_L0_lead': sum(g['mean_L0_lead']*g['n'] for g in digits)/dn,
         'min': min(g['min'] for g in digits), 'max': max(g['max'] for g in digits),
         'embedding_diff_norm': None}

order = [('"})"', gt['})']), ('digit', digit), ('")"', gt[')']), ('"="', gt['Ġ=']),
         ('"}\\n"', gt['}Ċ']), ('"}"', gt['}']), ('"\\n"', gt['ĠĊ'])]

fig = plt.figure(figsize=(7.6, 5.4))
gs = fig.add_gridspec(2, 1, height_ratios=[1.05, 3.1], hspace=0.42)

# ---- top panel: the real example ----
ax0 = fig.add_subplot(gs[0]); ax0.set_axis_off()
ax0.set_xlim(0, 100); ax0.set_ylim(0, 10)
toks = [' -', ' (-', '4', ')', ' \\', 'cdot', ' \\', 'det', '(A', '_{', '1', '2', '})']
ax0.text(1, 9.3, 'Held-out case NC_4x4_det_201 — the model is writing its cofactor expansion:',
         fontsize=8.6, fontweight='bold', va='top')
x = 2.0; y = 3.6; h = 3.4
for i, t in enumerate(toks):
    w = 2.6 + 1.35*len(t)
    probe = (i == len(toks)-1)
    fc = '#c23b22' if probe else '#f2e4d5'
    tc = 'white' if probe else '#333333'
    ax0.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.12',
                  fc=fc, ec='#b0a090', lw=0.7))
    ax0.text(x+w/2, y+h/2, t.replace(' ', '␣'), ha='center', va='center',
             fontsize=8, family='monospace', color=tc)
    x += w + 0.55
ax0.annotate('', xy=(x+3.6, y+h/2), xytext=(x+0.4, y+h/2),
             arrowprops=dict(arrowstyle='->', lw=1.4, color='#c23b22'))
w = 12.5
ax0.add_patch(mpatches.FancyBboxPatch((x+4.2, y), w, h, boxstyle='round,pad=0.12',
              fc='white', ec='#c23b22', lw=1.4, linestyle='--'))
ax0.text(x+4.2+w/2, y+h/2, 'next: ␣−', ha='center', va='center',
         fontsize=8.2, family='monospace', color='#c23b22')
ax0.text(x+4.2+w/2, y-1.0, 'written − (true sign +)', ha='center', va='top',
         fontsize=7.2, color='#c23b22')
ax0.text(2.0, y-1.0, 'probe token "})" — its layer-0 lead: +4.82', ha='left', va='top',
         fontsize=7.2, color='#333333')

# ---- bottom panel: bars ----
ax = fig.add_subplot(gs[1])
labels = [k for k,_ in order]
means  = [g['mean_L0_lead'] for _,g in order]
mins   = [g['min'] for _,g in order]
maxs   = [g['max'] for _,g in order]
ns     = [g['n'] for _,g in order]
colors = ['#c23b22'] + ['#d9b8a3']*(len(order)-1)
xpos = range(len(order))
ax.axhspan(-2, 2, color='#eeeeee', zorder=0)
ax.bar(xpos, means, color=colors, zorder=2, width=0.62)
ax.errorbar(xpos, means, yerr=[[m-lo for m,lo in zip(means,mins)],
                               [hi-m for m,hi in zip(means,maxs)]],
            fmt='none', ecolor='#555555', capsize=3, lw=1, zorder=3)
for i,(m,n) in enumerate(zip(means,ns)):
    ax.text(i, 0.25 if m>0 else m-0.35, f'n={n}', ha='center', fontsize=7.3,
            color='white' if i==0 else '#555555', zorder=4)
# embedding predictions (green diamonds)
for i,(_,g) in enumerate(order):
    e = g['embedding_diff_norm']
    if e is not None:
        ax.plot(i, e, marker='D', ms=6, color='#2e7d32', zorder=5)
ax.axhline(4.5, ls='--', lw=0.9, color='#888888')
ax.text(3.05, 4.62, 'observed dataset mean +4.5', ha='left', fontsize=7.2, color='#666666')
# the example's own dot on the '})' bar
ax.plot(-0.24, 4.8203, marker='*', ms=13, color='#1a1a1a', zorder=6)
ax.annotate('NC_4x4_det_201 (+4.82)\nthe case shown above', xy=(-0.2, 4.9), xytext=(0.85, 5.55),
            fontsize=7.4, ha='left', va='center',
            arrowprops=dict(arrowstyle='->', lw=0.9, color='#1a1a1a'))
ax.plot([], [], marker='D', ms=6, color='#2e7d32', ls='none', label='embedding-table prediction')
ax.legend(loc='upper right', bbox_to_anchor=(1.0, 0.86), fontsize=7.2, frameon=False)
ax.set_xticks(list(xpos)); ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylim(-2.6, 6.1)
ax.set_xlabel('token at the probe position', fontsize=9)
ax.set_ylabel('layer-0 lead of written sign\n("−" over "+", logits)', fontsize=8.5)
ax.set_title('Qwen-72B: the layer-0 "−" lean is set by the probe token', fontsize=10, pad=8)
ax.spines[['top','right']].set_visible(False)
fig.savefig('layer0_lean_probe_token.png', dpi=200, bbox_inches='tight')
print('saved')
