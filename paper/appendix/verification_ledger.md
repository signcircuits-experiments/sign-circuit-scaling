# Verification ledger — every number the paper claims

Companion script: `verify_all.py` (this folder) — re-derives
every AUTO entry fresh from the GITHUB UPLOADS held-out JSONs and prints
PASS/FAIL. Current status: **17/17 AUTO checks pass.**

Entry types:
- **AUTO** — recomputed by `verify_all.py` from raw JSONs on every run.
- **MANUAL** — verdict read from a git-frozen preregistration or FINDINGS
  document (source given); not recomputable from JSONs alone.
- **FLAGGED** — known open item; do not write into the paper until resolved.

## fig1 — late decision (2 panels, det errors + corrects)

| entry | value | type | source |
|---|---|---|---|
| n dots: Llama 192+130, Qwen 147+141 | as stated | AUTO | s01 lens JSONs |
| Qwen open circles n=33 (18 err + 15 corr), layer-0 peaks | 33 | FLAGGED | fig1_late_decision.md (locked) |
| Llama mid-committers n=11 (8 err + 3 corr) | 11 | FLAGGED | fig1_late_decision.md |

**FLAG:** fig1 has **no saved regeneration script** — the figure was locked
but only the pdf/png survive. Plain-rule reconstruction (peak_layer=0,
|final lead| ≥ 2 band) gives 20+17=37 circles and 9+3=12 mid-committers, not
the locked caption's 33 and 11 — the locked build used slightly different
rules that cannot be confirmed without the script. RESOLUTION NEEDED: rebuild
fig1 with a saved script (like fig4/fig5/figA/figB) so its caption counts
become AUTO.

## fig2 — habit/sign-writing layers

No entries yet — fig2 also has no regeneration script in appendix/. Caption
fix pending (must_add file: "habit layers" → "sign-writing layers" for Llama).
FLAGGED until scripted.

## fig3 — steering

| entry | value | type | source |
|---|---|---|---|
| Llama det flips 42/121 (Δ −4.5); Llama IBP 13/14 (Δ −20.7) | as stated | MANUAL | steering_plus_minus_asymmetry.md; s06/s08 JSONs |
| Specificity: breaks minus-corrects Llama 97% / Qwen 40%; plus-corrects harmed 0% | as stated | MANUAL | must_add specificity paragraph sources |
| Random directions flip nothing | as stated | MANUAL | same |

MANUAL for now: computable in principle from s06/s08 held-out JSONs — promote
to AUTO before submission if time allows.

## fig4 — universality (five models) — all AUTO

| entry | value |
|---|---|
| kept / circles / excluded | Phi 26/0/13, Mistral-S 13/0/26, Gemma 18/0/19, Llama 138/0/54, Qwen 74/20/53 |
| medians | 85.0 / 95.0 / 88.7 / 98.8 / 96.2 % |
| rule | keep iff final-layer lead ≥ +2; open circle iff peak < 12.5% depth |
| Mistral-Large-675B dropped | FAILED-TECHNICAL (hook captured MLP deltas; see fig4_universality.md) — MANUAL |

## fig5 — scorecard (6 predictions × 4 cells, 22/24)

| entry | value | type | source |
|---|---|---|---|
| P1 late rates: Llama det 152/192, Llama IBP 18/21, Qwen det 90/147, Qwen IBP 25/26 (peak ≥ L60) | pass ×4 | AUTO | s01 lens JSONs |
| P2 DLA > 0 (4 cells) | pass ×4 | MANUAL | FINDINGS docs, s02 workbooks |
| P3 direction separation | pass ×3, fail Qwen det | MANUAL | preregs + FINDINGS |
| P4 dose-response | pass ×4 | MANUAL | s06 JSONs, FINDINGS |
| P5 injected error signal | pass ×3, fail Qwen IBP (50/50 reversed) | MANUAL | FINDINGS_ibp.md §4 |
| P6 steering corrects + control | pass ×4 | MANUAL | s08 JSONs, FINDINGS |
| cell-specific checks (6 claims, 13 checks, 12 pass) | see fig5_scorecard.md | MANUAL | preregs + FINDINGS |

## figA — stamper vs adaptive

Regeneration script exists (`figA_stamper_vs_adaptive.py`) with expected
values in its docstring — re-running it is the check. MANUAL in verify_all.

## figB — joint ablation (4 cells) — all AUTO

| entry | value |
|---|---|
| mean Δ / baseline → after | Llama det −4.25, +7.05→+2.80; Llama IBP −7.09, +14.61→+7.52; Qwen det −2.52, +5.19→+2.67; Qwen IBP −0.98, +10.44→+9.47 |
| null means / ranges | −0.67 [−1.42,+0.16]; −0.29 [−0.96,+0.69]; −0.42 [−1.47,+0.17]; −0.11 [−0.70,+0.66] |

## Text-block numbers (paper text blocks)

| entry | value | type | source |
|---|---|---|---|
| Qwen L78 pushes −5.4 on plus-writers; L79 leads ±4.8/−3.8 (Llama) | as stated | MANUAL | figA_stamper_vs_adaptive.md |
| Llama L79 ablation on errors: −4.08 (5×5) / −2.64 (4×4) / −1.91 (IBP); check ablations \|Δ\| ≤ 0.21 | as stated | MANUAL | judge-vs-amplifier sources |
| Qwen writes correct "+" on 18/141 corrects | as stated | AUTO-able | s01 correct JSON (promote before submission) |
| task asymmetry: −20.7 (13/14) vs −4.5 (42/121) | as stated | MANUAL | steering docs |
| early "−" lean table (Qwen 98%, Gemma 95%, …) | as stated | MANUAL | fig1_late_decision.md + lean_tests/ |

## Open items before writing (the FLAG list)

1. **fig1 script missing** — rebuild with saved script; reconcile circle count
   (33 vs 37) and mid-committer count (11 vs 12).
2. **fig2 script missing** — same treatment; apply the caption fix.
3. Promote fig3/P6 steering numbers and the 18/141 behavior line to AUTO.

**One-line summary:** every figB/fig4/fig5-P1 number now re-derives from raw
data on one command (17/17 pass); fig1 and fig2 lack regeneration scripts and
carry two small count discrepancies to resolve before the paper is written.
