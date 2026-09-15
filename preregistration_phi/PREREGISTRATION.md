# PRE-REGISTRATION — Phi-4 held-out validation (sign-flip circuit)

> **STATUS: APPROVED 2026-09-15 — pass bars signed off by the PI. No held-out measurement may run before this file is committed.**

**Rules.** This file is committed **before** any held-out measurement (commit 1);
raw results are committed afterwards (commit 2); history is never rewritten. All numbers
are FINAL at commit. Verdict vocabulary: CONFIRMED / NEAR-MISS / NULL / MIXED /
FAILED-TECHNICAL, judged only against the tables below.

**Scope.** Two arms. **Arm 1 (confirmatory)** runs on the two **error domains** and is
judged against the bars in §3. **Arm 2 (deepsign correct domains)** is measured and
reported descriptively — no bars, no verdict.

## 1. Data (frozen)

| File | Kept | Split (+ / −) |
|---|---|---|
| `phi_det4x4_error_validation_heldout_n150.csv` | 150 | TBD at pre-flight |
| `phi_ibp_error_validation_heldout_n77.csv` | 77 | TBD at pre-flight |
| `phi_det4x4_correct_validation_heldout_n149.csv` | 149 | TBD at pre-flight |
| `phi_ibp_correct_validation_heldout_n146.csv` | 146 | TBD at pre-flight |

Sidecar files (role-matched, 1:1 join by `id`): `phi_det4x4_correct_validation_heldout_n149_deepsign_rolematched.csv` (149 rows) and `phi_ibp_correct_validation_heldout_n146_deepsign_rolematched.csv` (146 rows). Sidecars under `ARCHIVE_depthmatched_deepsign/` must never be used.

Splits by written sign (`wrong_sign` column; label-inversion on corrects). The **M2 first-wrong-sign rule** applies at pre-flight to error files: any row whose flagged sign is not the first wrong sign is EXCLUDED and logged by `id` before any measurement. M2 does not apply to correct files.

**Tok-12 exclusion policy.** Error domains: expected 100% tok-482; log any tok-12 case found and stop. Correct domains: audit every row; exclude tok-12 cases from d̂ construction and all causal analyses; report exact excluded counts by domain. Pre-flight must log per-row sign-token ids and tok-12 tallies before any causal stage runs.

## 2. Frozen instruments

Master file: `data/phi/targets_frozen_phi.json` — frozen 2026-09-11, `human_reviewed: true`.

| Instrument | Value |
|---|---|
| Habit layers (s05/s06, all domains) | **37, 39** |
| Check layer | **38** |
| Controls (all domains) | 15, 25 |
| Capture layers (s04, errors) | 34, 35, 37, 38, 39, 15, 25 |
| Causal probe positions | det rel-depth 0.70; ibp rel-depth 0.60 |
| s08 steering pair | [37, 39] |
| s06 α grid | **0.5, 1.0, 2.0, 3.0** |
| Sign tokens | per-row `wrong_sign_tok` / `correct_sign_tok` ids from each case record |

**Strict flip / break criterion:** baseline_ld > 0 AND edit_ld < 0; ties at 0 are NOT flips.
**Emb-peak exclusions:** none established in Phi discovery; flag any emb-peak case at pre-flight, exclude and log by id.

## 3. Criteria — error domains (Arm 1, confirmatory)

All arms teacher-forced; no free-text generation. Anchors from `results/Phi/{domain}/` and `v2_mean_ablation/` subfolders, locally recomputed from raw JSONs. Discovery n: det n=61, ibp n=40.

| Stage | Test | Discovery anchor | Pass bar (held-out) | Predicted |
|---|---|---|---|---|
| P1 — s01 | Logit lens, late peak (≥ L30) | det 53/61 (87%); ibp 40/40 (100%) | det ≥ 80%; ibp ≥ 95% of cases peak ≥ L30 | pass |
| P2 — s02 | Habit MLP DLA > control DLA, both domains | det: L37 +1.724, L39 +0.804; ctrls L15 +0.012, L25 +0.182. ibp: L37 +2.944, L39 +2.601; ctrls L15 +0.079, L25 +0.115 | both domains: mean MLP DLA positive at L37 AND L39; both above both controls in absolute value; controls \|mean\| ≤ 0.5 | pass |
| P3 — s05 expD′ | Single-site MLP mean-ablation direction (habit ≥ control) | det/ibp: L37 and L39 DLA substantially above controls (see §2 table) | both domains: mean delta_ld at L37 and L39 more negative than at L15 and L25 (directional only) | directional pass |
| P4 — s05 expE′ | Joint TARGET_SET ablation — null/backfire expected | det (n=61): mean target_delta +0.43, beats_null 8/61 (13%). ibp (n=40): +1.61, 1/40 (3%) | both domains: mean target_delta ≥ −1.0; beats_null_p5 < 50% | null/backfire |
| P5 — s06 | Direction subtraction (expG′), α ∈ {0.5, 1, 2, 3} | det (n=57): α=3 mean Δld −7.538, flips 1/57; CTRL_RAND 0 flips. ibp (n=40): α=3 −14.578, flips 1/40; CTRL_RAND 0 flips | both domains: mean Δld at α=3 < −3.0; flips ≤ 10%; CTRL_RAND 0 strict flips; CTRL_MAG \|mean\| ≤ 0.2 | lead-reduction; near-zero flips |
| P6 — s08 | C2 steering, α ∈ {1, 2, 3} | det: α=1 −2.083, α=2 −4.605, α=3 −7.538, flips 1/57. ibp: α=1 −4.350, α=2 −9.159, α=3 −14.578, flips 1/40. CTRL_MAG \|mean\| ≤ 0.08 | both domains: mean Δld negative at every α, monotone; flips ≤ 10%; CTRL_MAG \|mean\| ≤ 0.2 and 0 strict flips | monotone lead-reduction; near-zero flips |
| P7 — s09 | Judge armB logit boosts | **NOT PREREGISTERED** — no Phi discovery judge screen exists; held-out results reported descriptively only (exact fix counts per γ, both domains) | — | — |

## 4. Arm 2 — correct (deepsign) domains (descriptive only, no pass bars)

Stages s01, s02, s04, s05 (expD′ and expE′), s06, s08 (c2_on_correct), s09 (crossdomain): run and report raw JSONs descriptively. Tok-12 exclusion applies throughout (tok-482 rows only after audit). No pass bar, no verdict.

## 5. Exclusions

- s00, s03 never run; no free-text generation anywhere.
- Correct-domain tok-12 rows: excluded from d̂ construction and all causal analyses; reported by count and id.
- ARCHIVE_depthmatched_deepsign sidecars: never use.
- s05b (single-head ablation): no frozen head sites from Phi discovery; not part of the battery.
- s07 (patching): not part of the battery.
- Any analysis whose composition cell is empty.

## 6. Small-n

Any stratum with n < 50 is flagged small-n and reported descriptively with exact counts (x/n) alongside the point estimate.
