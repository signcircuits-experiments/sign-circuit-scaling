# PRE-REGISTRATION — Gemma-3-27B-it held-out validation (sign-flip circuit)

> **STATUS: APPROVED 2026-09-13 — pass bars signed off by the PI. Ready to commit (commit 1) before any held-out measurement.**

**Rules.** This file is committed **before** any held-out measurement (commit 1);
raw results are committed afterwards (commit 2); history is never rewritten. The
held-out data is touched **once** — a technical crash may be restarted, a
disliked result may not. All numbers below are FINAL at commit. Verdict
vocabulary: CONFIRMED / NEAR-MISS / NULL / MIXED / FAILED-TECHNICAL, judged only
against the table below.

**Scope.** The confirmatory battery runs on the **error domains only** (untouched
by any prior measurement). The correct-domain files were previously included in
one descriptive scan (no causal measurement); all correct-domain analyses are
therefore EXPLORATORY (§7), outside the confirmatory battery.

## 1. Data (frozen)

| File | Kept | Split (+ / −) |
|---|---|---|
| `gemma_det4x4_error_validation_heldout_n126.csv` | 126 | 85 / 41 |
| `gemma_ibp_error_validation_heldout_n73.csv` | 73 | 44 / 29 |
| `gemma_det4x4_correct_validation_heldout_n138.csv` | 138 | 45 / 93 |
| `gemma_ibp_correct_validation_heldout_n150.csv` | 150 | 0 / 150 |

Splits are by written sign (`wrong_sign` column; label-inversion convention on
corrects). One archived drop exists: 12 det-correct rows excluded before any
measurement for row-reduction contamination
(`data/gemma/raw/gemma_det4x4_correct_rowreduction_excluded_n12.csv`). Pre-flight
verifies for every row: char at `sign_char_offset` = written sign; `prefix_len` =
start of assistant turn; `full_input` = original chat prompt (teacher forcing is
exact).

The two error files are untouched by any measurement. The two correct files
were previously included in one descriptive scan (no causal measurement) and
serve only the exploratory arm (§7).

## 2. Frozen instruments (nothing tuned on held-out data)

| Domain | Habit | Check | Controls |
|---|---|---|---|
| det_4x4 (error + correct) | 58, 60 | 56 | 23, 39 |
| ibp (error + correct) | 58, 60 | 56 | 23, 39 |

- 62-layer model; late window starts L46. Correct domains inherit their paired
  error domain; all four `targets.json` `human_reviewed: true`, PI-approved
  2026-09-09, from discovery data only. s03 never runs on this data.
- **Joint TARGET_SET (expE′):** det `[55, 56, 58, 59, 60]`; ibp
  `[55, 56, 58, 60, 61]`. Deterministic from frozen discovery DLA (habit layers +
  top late-|DLA|), not tuned. Null pool `[39, 61]` (det) — a null layer in the
  TARGET_SET is excluded from its own null pool.
- L55 is documented as a plus-side pusher: **captured; not ablated singly in
  the held-out battery** (discovery expD′ did ablate it singly: det −1.64,
  ibp −0.60); in the held-out battery it participates only in the joint set.
- **Attention heads (s05b replication):** pushers L60_H5, L54_H10; corrector
  L60_H4; controls L49_H2 + L49_H5 (det), L49_H2 + L49_H4 (ibp).
- **Stratified reporting (all causal arms):** pooled / baseline_ld ≥ +2
  ("re-committer") / baseline_ld < +2, plus written-sign splits. ld =
  logit(wrong-sign token) − logit(correct-sign token) at `probe_tok`, using
  **per-case sign-token ids derived at pre-flight from each frozen row and
  logged in the pre-flight report** (this handles Gemma's merged-token mode,
  ids 236772/236862, observed in a minority of discovery cases per the run
  logs; the frozen CSVs carry the sign characters, not token ids).
- **Strict flip criterion:** baseline_ld > 0 AND edit_ld < 0 (ld crosses zero).
  Ties at exactly 0 are NOT flips.
- No repro gate anywhere: full set, ungated, every kept row measured.

## 3. Criteria (the promise)

All arms teacher-forced; **no free-text generation anywhere**. Anchors are
measured discovery outcomes from the full-set ungated runs — not `config.py`
constants. Run sizes: s01/s02/s05/s05b/s05c used det n=92 / ibp n=70; s06, s08
and s09 used det n=89 / ibp n=68 (the emb-peak cases listed in `targets.json`
were excluded by those stages).

| Stage | Test | Discovery anchor | Pass bar (held-out) | Predicted |
|---|---|---|---|---|
| s01 | Logit lens, error domains | det 60/92 (65%) peak ≥ L55; ibp 43/70 (61%) | ≥ 50% of cases `peak_layer` ≥ 55, per domain | pass |
| s02 | MLP DLA, error domains | det: L55 +2.89, L58 +1.15, L60 +0.76, L56 −1.05; ibp: L55 +2.95, L58 +2.65, L60 +0.95, L56 −1.32 (n=92/70; MLP DLA is unaffected by the eff_dir fix, which touched attention DLA only) | mean MLP DLA positive at L55 and L58 AND negative at L56, per error domain | pass |
| s04 | Projections onto d-hat | no saved discovery projection files — prediction stated explicitly here, not anchored | per error domain: minus-written mean projection < plus-written mean projection at the capture layers | pass |
| s05 | Habit-site MLP ablations (expD′), errors | det: L58 −0.79, L60 −0.25; ctrls −0.12 / −0.14. ibp: L58 −1.01, L60 −0.51; ctrls −0.11 / −0.01 | per domain: L58 and L60 mean Δld negative AND below both controls; controls \|mean\| ≤ 0.5 | pass |
| s05 | Joint TARGET_SET ablation (expE′), errors | det pooled −3.62 (≥+2: −4.41; <+2: −1.25), 47.8% beat null p5; ibp pooled −2.86 (≥+2: −3.71; <+2: +0.57), 65.7% beat null | per domain: pooled mean Δld ≤ −1.5 AND ≥ 30% beat own null p5; ≥+2 stratum mean more negative than <+2 stratum | pass |
| s05 | expE′ strict flips | det 12/92 (≥+2: 3; <+2: 9); ibp 0/70 | descriptive only — exact counts per stratum; no bar (discovery ibp had zero) | det > 0, ibp ≈ 0 |
| s05b | Single-head ablation replication | pushers det: L60_H5 −0.43, L54_H10 −0.26; ibp: −1.01, −0.70. Corrector L60_H4 positive Δld (det +0.36, ibp +1.36). Strict single-head flips rare: det 1/92 (L60_H5) and 2/92 (L54_H10); ibp 2/70 per pusher head — all weak-case (baseline ≤ 1.25) | per domain: both pusher heads mean Δld negative; corrector mean Δld positive; control heads \|mean\| ≤ 0.15; single-head flips ≤ 5% | pass |
| s05c | Joint head-group ablation (frozen groups J1–J4) | discovery (n=92/70): J1 det −0.64 (≥+2: −0.92), ibp −1.64 (≥+2: −1.93), near-additive vs single-head sums (−0.68 / −1.71); J2 det −0.24, ibp −0.54; J3 det +0.75, ibp +1.85; ctrl −0.00 / −0.01; strict flips 1 det / 3 ibp, all baseline < +2 | per domain: J1 mean Δld negative; J3 mean Δld positive; J4 ctrl \|mean\| ≤ 0.15; flips descriptive (predicted few, weak-case only, zero ≥+2 flips) | pass |
| s06 | Direction subtraction (expG′), minus errors | α=2, minus-writers: det L58 −0.87 / L60 −2.37; ibp L58 −1.40 / L60 −1.86; monotone in α at both sites; random ctrl ≈ 0; L23/L39 ctrls \|mean\| ≤ 0.1 | per domain: mean Δld at L58 and L60 negative at every α, monotone across the α grid; controls \|mean\| ≤ 0.5 | pass |
| s08 | C2 steering on errors | α=3: det −3.07, strict flips 17 (of 81 with baseline > 0; n=89); ibp −5.76, strict flips 18 (of 62 with baseline > 0; n=68). CTRL_MAG \|mean\| ≤ 0.16 | per domain: mean Δld negative at every α, monotone; strict flips at α=3 ≥ 5% of cases with baseline > 0; CTRL_MAG \|mean\| ≤ 0.5 | pass |
| s09 | Judge armB (logit boosts at check layer L56 + ctrl L23) | 0 fixes at every γ ∈ {1.5, 2, 3}, both sites, both domains (det n=89, ibp n=68) | fixes ≤ 5% per domain at every γ (repeated null = confirmed null) | **null** |

## 4. Exclusions (pre-registered)

- s00, s03 (re-derivation destroys the design); **all free-text generation**
  (s08 runs c2 arms only, s09 patch/logit arms only).
- **Depthgrid per-bin causal (G11):** reserved for a separate preregistration
  addendum carrying the DG6 per-bin predictions; committed before that run, not
  covered here.
- L55 single-site ablation (documented plus-side pusher; captured only).
- **All correct-domain analyses** — exploratory only (§7), not confirmatory.
- Any analysis whose composition cell is empty.

## 5. Small-n

Every stratum with n < 50 (det error minus-writers n=41, ibp error minus n=29
and plus n=44, all ≥+2 strata, all flip counts) is flagged small-n and reported
descriptively with exact counts (x/n) alongside the point estimate.

## 6. Additional disclosures (mandatory, Gemma-specific)

1. **Protocol redesign:** the original role-matched subset protocol was replaced
   by the stratified full-set ungated protocol before this preregistration; the
   role-matched run is archived (`ARCHIVE_gemma_rolematched_20260913`) and is
   not quoted anywhere here.
2. **s02 eff_dir bug:** attention DLA in the first s02 run used the wrong
   effective direction (o_proj vs post_attention_layernorm); MLP DLA was never
   affected. The s02 anchors above are error-domain MLP-DLA means, valid
   regardless of the fix; no attention-DLA anchor is used anywhere in this
   battery.
3. **expE′ beat-null rates** (47.8% det / 65.7% ibp) are lower than earlier
   gated-run values; the anchors quoted are the honest full-set numbers.
4. Discovery anchors' historical (superseded) workbook sheets are banner-marked
   "do NOT quote" in `Gemma_discovery_anchors.xlsx`.

## 7. Phase 2 (EXPLORATORY, only after Phase-1 verdicts lock)

The held-out set may then be re-mined as a larger discovery set (joint head
groups beyond the pre-registered J1–J4, depth-bin slices, head-level screens,
weight-space checks). The **correct-domain causal battery** (habit-site MLP
ablations at L58/L60 on the held-out correct files, deepsign discovery anchors
det L58 −1.86 / L60 −0.85, ibp −1.53 / −1.47) runs here, not in the
confirmatory battery. Everything Phase-2 is labeled EXPLORATORY in the paper and
needs its own future held-out set.

## 8. Run mapping

- Pipeline `pipeline_release`: s01, s02, s04, s05, s05b, s05c (frozen
  `groups_gemma_det.json` / `groups_gemma_ibp.json`, mean ablation, no
  fallback), s06, s08, s09. Never s00/s03.
- Config: new `MODEL_CONFIGS` entry `gemma_heldout` (exact copy of `gemma`,
  `results_name: "Gemma_heldout"`); data converted to
  `gemma_heldout_{domain}_experiment_ready.xlsx`, byte-equivalent to the frozen
  CSVs, checksummed in the pre-flight report.
- Env: `SIGN_DATA_DIR` / `SIGN_RESULTS_DIR` → held-out dirs; results archived
  under `heldout/Gemma/results/{domain}/`.
- Targets: each `targets.json` copied unmodified to
  `{results_root}/{domain}/targets.json`.
- Pre-flight: per-case sign-token ids verified (standard 900/753 vs merged
  236772/236862 modes); d-hat construction and hook capture demonstrated on 2–3
  sample cases before the battery.
