# Held-out pre-registration — Phi-4 (sign-flip circuit)

> **STATUS: APPROVED 2026-09-15 — pass bars signed off by the PI. Committed before any held-out measurement.**

All tests, pass bars, and exclusions: **`PREREGISTRATION.md`** (the binding document).

## Files

| File | Rows | What it is |
|---|---|---|
| `PREREGISTRATION.md` | — | Binding analysis plan: criteria table (§3), exclusions, data |
| `phi_det4x4_error_validation_heldout_n150.csv` | 150 | 4x4 determinant, wrong-sign responses |
| `phi_ibp_error_validation_heldout_n77.csv` | 77 | Integration-by-parts, wrong-sign responses |
| `phi_det4x4_correct_validation_heldout_n149.csv` | 149 | 4x4 determinant, correct responses |
| `phi_det4x4_correct_validation_heldout_n149_deepsign_rolematched.csv` | 149 | Det correct deepsign sidecar (1:1 join by id) |
| `phi_ibp_correct_validation_heldout_n146.csv` | 146 | Integration-by-parts, correct responses |
| `phi_ibp_correct_validation_heldout_n146_deepsign_rolematched.csv` | 146 | IBP correct deepsign sidecar (1:1 join by id) |
| `data/phi/targets_frozen_phi.json` | — | Frozen master targets (habit [37,39], check L38, ctrls [15,25]), PI-reviewed 2026-09-11 |

## Data counts

| File | Kept | Split (+ / −) |
|---|---|---|
| det errors | 150 | TBD at pre-flight |
| IBP errors | 77 | TBD at pre-flight |
| det corrects (deepsign) | 149 | TBD at pre-flight |
| IBP corrects (deepsign) | 146 | TBD at pre-flight |

Error splits by written sign; correct splits by `wrong_sign_deep`. The M2 first-wrong-sign
rule applies at pre-flight to **error files only**; any exclusion logged by id before measurement.

## Phi-specific notes

- Model: `microsoft/phi-4` (14B parameters, 40 layers, 40 attention heads).
- Tok-12 exclusion: error domains expected 100% tok-482; correct domains require tok-12
  audit before any causal stage. See §1 of `PREREGISTRATION.md`.
- Phi is the "unsteerable at calibrated dose" model in the paper: bars are lead-reduction
  and specificity, not flip-rate. Null and backfire causal results are expected and
  pre-registered as such (§P4, §P5, §P6).
- No pass bar for s09 (no discovery judge anchor for Phi error domains).
- Arm 2 (deepsign corrects): no pass bars, descriptive only.
