# Held-out pre-registration — Gemma-3-27B-it (sign-flip circuit)

> **STATUS: APPROVED 2026-09-13 — pass bars in `PREREGISTRATION.md` signed off by the PI.**

To be committed **before** any held-out measurement is run. All tests, pass
bars, and exclusions: **`PREREGISTRATION.md`** (the binding document).

## Files

| File | Rows | What it is |
|---|---|---|
| `PREREGISTRATION.md` | — | Binding analysis plan: criteria table, exclusions, run mapping |
| `gemma_det4x4_error_validation_heldout_n126.csv` | 126 | 4x4 determinant, wrong-sign responses |
| `gemma_det4x4_correct_validation_heldout_n138.csv` | 138 | 4x4 determinant, correct responses |
| `gemma_ibp_error_validation_heldout_n73.csv` | 73 | Integration-by-parts, wrong-sign responses |
| `gemma_ibp_correct_validation_heldout_n150.csv` | 150 | Integration-by-parts, correct responses |
| `gemma_det4x4_error_targets.json` | — | Frozen target layers (det), from discovery data only |
| `gemma_ibp_error_targets.json` | — | Frozen target layers (IBP), from discovery data only |
| `gemma_det4x4_correct_targets.json` | — | Same det layers, inherited (not re-derived) |
| `gemma_ibp_correct_targets.json` | — | Same IBP layers, inherited (not re-derived) |
| `groups_gemma_det.json` | — | Frozen s05c head groups J1–J4 (det), from discovery only |
| `groups_gemma_ibp.json` | — | Frozen s05c head groups J1–J4 (IBP), from discovery only |

## Data counts

| File | Kept | Split (+ / −) |
|---|---|---|
| det errors | 126 | 85 / 41 |
| det corrects | 138 | 45 / 93 |
| IBP errors | 73 | 44 / 29 |
| IBP corrects | 150 | 0 / 150 |

One archived pre-measurement drop: 12 det-correct rows (row-reduction
contamination), kept with reasons at
`data/gemma/raw/gemma_det4x4_correct_rowreduction_excluded_n12.csv`.

## Scope

The confirmatory battery runs on the **error domains only** — the two error
files are untouched by any measurement. The two correct files were previously
included in one descriptive scan (no causal measurement) and serve only the
exploratory arm (§7 of `PREREGISTRATION.md`).

## Targets

Both error-domain `targets.json` files are frozen from discovery data only,
`human_reviewed: true`, PI-approved 2026-09-09 (name withheld for double-blind
review). Correct domains inherit them unmodified. They are never re-derived on
this data.
