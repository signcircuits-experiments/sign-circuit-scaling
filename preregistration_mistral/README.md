# Held-out pre-registration — Mistral-Small-3.2-24B (sign-flip circuit)

> **STATUS: DRAFT — awaiting PI pass-bar sign-off. To be committed before any held-out measurement.**

All tests, pass bars, and exclusions: **`PREREGISTRATION.md`** (the binding
document once approved and committed). File provenance and process history:
`PROVENANCE_NOTES.md`.

## Files

| File | Rows | What it is |
|---|---|---|
| `PREREGISTRATION.md` | — | Binding analysis plan: criteria tables (§3a errors, §3b corrects), exclusions, run mapping |
| `PROVENANCE_NOTES.md` | — | File provenance and housekeeping notes (non-binding) |
| `mistral_det4x4_error_validation_heldout_n142.csv` | 142 | 4x4 determinant, wrong-sign responses |
| `mistral_ibp_error_validation_heldout_n70.csv` | 70 | Integration-by-parts, wrong-sign responses |
| `mistral_det4x4_correct_validation_heldout_n122_deepsign_rolematched.csv` | 122 | 4x4 determinant, correct responses, deep-sign role-matched |
| `mistral_ibp_correct_validation_heldout_n156_deepsign_rolematched.csv` | 156 | Integration-by-parts, correct responses, deep-sign role-matched |
| `targets_frozen_mistral.json` | — | Frozen master targets (habit [37,38,39], check L32 exploratory, ctrls [15,25]), PI-reviewed 2026-09-11, from discovery data only |
| `sites_det_4x4_error.json` | — | Frozen s05b head sites (det, error domain only), from discovery only |
| `sites_ibp_error.json` | — | Frozen s05b head sites (IBP, error domain only), from discovery only |

## Data counts

| File | Kept | Split (+ / −) |
|---|---|---|
| det errors | 142 | 18 / 124 |
| IBP errors | 70 | 11 / 59 |
| det corrects (deepsign) | 122 | 32 / 90 |
| IBP corrects (deepsign) | 156 | 65 / 91 |

Error splits by written sign; correct splits by `wrong_sign_deep` (label
inversion — see §1 of `PREREGISTRATION.md`). The M2 first-wrong-sign rule
applies at pre-flight to **error files only** (as in discovery, which dropped
2 det rows); any exclusion is logged by id before measurement.

## Per-arm discovery n's

| Arms | det err | ibp err | det corr | ibp corr |
|---|---|---|---|---|
| s01, s02 | 95 | 39 | 78 | 43 |
| s05 (expD′), s05b | 93 | 39 | 78 (no s05b) | 43 (no s05b) |
| s05 (expE′), s06, s08, s09 | 91 | 35 | 78 | 43 (42 in expG′/s09) |

Errors: D′ = M2-only (n95→93 for det); E′ = D′ + emb-peak exclusions.
Corrects: no emb-peak exclusions; 1 ibp `embedding_bias` case excluded from
habit-layer arms (n=42 where noted). s08 on corrects runs on the error-cases
subset (baseline_ld > 0: det 71, ibp 41).

## Scope

**One confirmatory battery, four domains** — both error domains (§3a) and
both correct deepsign domains (§3b), all untouched by any causal measurement.
There is no second confirmatory phase; any post-verdict re-mining is
exploratory (§7 of `PREREGISTRATION.md`).

## Key Mistral-specific facts

Det error probe token sits early in the text (rel-depth 0.33) while layer
peaks are late (51.6% ≥ L30); no checker layer exists (L32 exploratory); ibp
error discovery is minus-dominated; on correct cases the wrong sign leads at
the deep position for most cases (det 71/78, ibp 41/43) — the phenomenon
under test; s05b never ran on corrects or the E4 battery; attention at L38
carries a correctness gap that MLP-only ablation understates (stated
limitation). Full list: §6 of `PREREGISTRATION.md` (11 disclosures).
