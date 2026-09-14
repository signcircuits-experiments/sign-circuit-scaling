# PRE-REGISTRATION — Mistral-Small-3.2-24B held-out validation (sign-flip circuit)

> **STATUS: DRAFT — awaiting PI pass-bar sign-off. Not yet committed; no held-out measurement may run before the signed-off version is committed.**

**Rules.** This file is committed **before** any held-out measurement (commit 1);
raw results are committed afterwards (commit 2); history is never rewritten. As of
this preregistration, the held-out data has not been touched by any experiment.
It will be measured exactly once, after this file is committed; only a
technical crash justifies a restart. All numbers below are FINAL at commit. Verdict
vocabulary: CONFIRMED / NEAR-MISS / NULL / MIXED / FAILED-TECHNICAL, judged only
against the tables below.

**Scope.** One confirmatory battery, four domains: the two **error domains** and
the two **correct (deepsign) domains** — all four held-out files are untouched
by any measurement. Error domains are judged against §3a; correct domains
against §3b. File provenance and housekeeping notes live in
`PROVENANCE_NOTES.md`; this file carries only what governs the held-out run.

## 1. Data (frozen)

| File | Kept | Split (+ / −) |
|---|---|---|
| `mistral_det4x4_error_validation_heldout_n142.csv` | 142 | 18 / 124 |
| `mistral_ibp_error_validation_heldout_n70.csv` | 70 | 11 / 59 |
| `mistral_det4x4_correct_validation_heldout_n122_deepsign_rolematched.csv` | 122 | 32 / 90 |
| `mistral_ibp_correct_validation_heldout_n156_deepsign_rolematched.csv` | 156 | 65 / 91 |

Error files: splits by written sign (`wrong_sign` column). Pre-flight verifies
for every row: char at `sign_char_offset` = written sign; `offset > prefix_len`;
`full_input` = original chat prompt (teacher forcing exact). The **M2
first-wrong-sign rule** applies at pre-flight exactly as in discovery: any row
whose flagged sign is not the first wrong sign is EXCLUDED and logged by id
before any measurement (discovery dropped 2 such det rows, n95→93). Rows are
never dropped for any other reason.

Correct (deepsign) files: the model wrote the correct final answer; the probe
sits at the **deep sign position** (`sign_char_offset_deep`), with per-row
`wrong_sign_deep` / `correct_sign_deep` columns (label inversion: `written_sign
= wrong_sign` in correct files, matching discovery). Splits above are by
`wrong_sign_deep`. The M2 rule does not apply to correct files; pre-flight
verifies the deep-offset char and teacher forcing exactly as for errors.

## 2. Frozen instruments (nothing tuned on held-out data)

Master file: `targets_frozen_mistral.json` — frozen 2026-09-11,
`human_reviewed: true`, PI-reviewed against raw expA/expB discovery JSONs. The
per-domain `targets.json` files inside `results/Mistral/` are PI-reviewed
picks (error domains `pi_review_date: 2026-09-14`; correct domains inherit the
frozen master, `frozen_source: mistral_targets_frozen.json`); the frozen
master governs.

| Instrument | Value |
|---|---|
| Habit layers (s05/s06, all domains) | **37, 38, 39** (40-layer model; late window starts L30) |
| Check layer | **32 — EXPLORATORY ONLY**: no checker signature exists for Mistral; any check-arm result is exploratory and never enters confirmatory claims |
| Controls (all domains) | 15, 25 |
| Capture layers (s04) | errors: 32, 36, 37, 38, 39 + ctrls 15, 25; corrects: 31, 37, 38 |
| s08 steering pair (all domains) | [38, 39] (PI ruling 2026-09-11; s08 takes exactly 2 layers) |
| expE′ TARGET_SET | errors: det `[34, 36, 37, 38, 39]`, ibp `[32, 34, 37, 38, 39]`; corrects: det `[34, 35, 37, 38, 39]`, ibp `[34, 36, 37, 38, 39]` (habit set + per-domain top-late-\|DLA\| extras, deterministic from frozen discovery DLA). Null = 40 random same-size layer sets, seeds 0–39 |
| Heads (s05b, error domains only) | det: pushers L38_H7, L38_H29; correctors L38_H5, L38_H30, L36_H30; pusher L36_H2; ctrls L32_H22, L36_H9. ibp: pushers L38_H7, L38_H6, L38_H4; correctors L38_H5, L38_H28, L38_H30; ctrls L39_H16, L32_H26 (frozen `sites_{domain}.json`, from discovery only) |
| Probe position | errors: det rel-depth 0.33 (the det error token sits early in the response text — error-matched median from deepsign sidecar); ibp 0.72. Corrects: per-row deepsign offset from the sidecar columns |
| Sign tokens | per-row `wrong_sign_tok` / `correct_sign_tok` ids from each case record (deep variants on corrects) — context-dependent token modes; **never a global sign-token id** |

- **Analysis-time exclusions (frozen from discovery `targets.json`):** error
  domains: emb-peak ids det `NC_4x4_det_1243`, `NC_4x4_det_412`; ibp
  `ibp_pts_n11_b173`, `ibp_pts_n11_b113`, `ibp_pts_n7_b37`, `ibp_pts_n7_b67`
  (s06/s08/s09 discovery n = 91 det / 35 ibp). Correct domains: no emb-peak
  exclusions in discovery (0 ids); 1 ibp discovery case is `embedding_bias`
  and was excluded from habit-layer arms (n=42 where noted). If any held-out
  row is emb-peak / embedding-bias by the same frozen rule, it is flagged and
  excluded the same way, logged by id.
- **Per-arm discovery n's:** errors — s01/s02 det 95 / ibp 39; s05 (expD′) and
  s05b det 93 / ibp 39; s05 (expE′) / s06 / s08 / s09 det 91 / ibp 35 (D′ =
  M2-only; E′ = +emb-peak exclusions). Corrects — det 78 / ibp 43 throughout
  (ibp 42 in expG′ and s09, minus the embedding-bias case).
- **Stratified reporting (all causal arms):** errors: pooled / baseline_ld ≥ +2
  / < +2, plus written-sign splits. Corrects: pooled / minus-writers /
  plus-writers (by `wrong_sign_deep`), error-cases subset (baseline_ld > 0).
  ld = logit(wrong-sign token) − logit(correct-sign token) at the probe token
  (deep wrong/correct on corrects), per-case ids from pre-flight.
- **Strict flip / break criterion (all domains):** baseline_ld > 0 AND
  edit_ld < 0; ties at 0 are NOT flips. s09 "fix" uses the same crossing.
- No repro gate anywhere: full set, ungated, every kept row measured.

## 3a. Criteria — error domains (the promise)

All arms teacher-forced; **no free-text generation anywhere**. Anchors are
measured discovery outcomes recomputed from the raw full-set JSONs staged in
`results/Mistral/{det_4x4_error,ibp_error}/` — not config constants. Run sizes:
s01/s02 det n=95 / ibp n=39; s05/s05b det n=93 (post-M2) / ibp n=39; s06/s08/s09
det n=91 / ibp n=35 (post frozen exclusions).

| Stage | Test | Discovery anchor | Pass bar (held-out) | Predicted |
|---|---|---|---|---|
| s01 | Logit lens, late peak | det 49/95 (51.6%) `peak_layer` ≥ L30; ibp 31/39 (79.5%) | det ≥ 40% and ibp ≥ 60% of cases peak ≥ L30 | pass |
| s02 | MLP DLA signs | det: L37 +0.53, L34 +0.40, L39 +0.22, L38 +0.19, **L36 −0.33**; ctrls +0.02/+0.01. ibp: L37 +1.01, L38 +0.82, L34 +0.50, L39 +0.47, L36 +0.15, L32 −0.21; L15 ctrl −0.015 (see §6.7) | det: mean MLP DLA positive at L37 AND negative at L36. ibp: positive at L37 AND L38. Ctrls \|mean\| ≤ 0.3 | pass |
| s04 | Projections onto d-hat | capture run (2026-09-13): det n=93, ibp n=39, 7 layers [32,36,37,38,39,15,25], 0 missing fields. No discovery contrast computed — prediction stated here, not anchored | per domain: minus-written mean projection < plus-written mean projection at the capture layers (plus strata are small-n: det 18, ibp 11 — descriptive alongside) | pass |
| s05 | Habit-site MLP mean-ablation (expD′) | det (n=93): L37 −0.265, L38 −0.280, L39 +0.011; ≥+2 stratum (n36): L37 −1.319, L38 −1.038; ctrls L15 −0.073 / L25 +0.144. ibp (n=39): pooled ~0 at all habit sites (L37 +0.06, L38 −0.02, L39 −0.09); ≥+2 (n29): −0.10/−0.15/−0.18; L15 ctrl +0.239 (§6.7) | det: L37 and L38 mean delta_ld negative AND ≥+2 stratum more negative than pooled AND both below both controls. **ibp: no bar — descriptive** (discovery single-site effect is null; report exact means per stratum) | det pass; ibp ~0 |
| s05 | Joint TARGET_SET ablation (expE′) | det (n91): pooled −0.753, ≥+2 −3.684 (n36), <+2 +1.166 (n55), 8 strict flips, 37.4% beat null p5. ibp (n35): pooled −0.115, ≥+2 −0.406 (n29), <+2 +1.292 (n6, small-n), 0 flips, 28.6% | det: pooled mean delta_ld ≤ −0.3 AND ≥+2 stratum ≤ −1.5 AND ≥+2 more negative than <+2 AND ≥ 20% beat own null p5. ibp: ≥+2 stratum mean delta_ld negative; rest descriptive | det pass; ibp weak |
| s05b | Single-head zero-ablation | det (n93): pushers L38_H7 −0.128, L38_H29 −0.138; correctors +0.040/+0.044; ctrls \|mean\| ≤ 0.01; 0 strict flips. ibp (n39): all sites \|mean\| ≤ 0.04 — null | det: both L38 pusher heads mean delta_ld negative; both L38 correctors ≥ 0; ctrl heads \|mean\| ≤ 0.1; flips ≤ 5%. **ibp: no bar — predicted repeat null**, descriptive | det pass; ibp null |
| s06 | Direction subtraction (expG′) | det (n91) α=2: L37 −0.297, L38 −0.253, L39 −0.384, monotone in α; flips at α=2 (L37/L38/L39): 0/2/6; ctrls \|mean\| ≤ 0.011. ibp (n35) α=2: L37 −0.309, L38 −0.733, L39 −0.826, monotone; ctrls ≤ 0.04 | per domain: mean delta_ld negative at L37, L38 and L39 at every α AND monotone across the α grid; controls \|mean\| ≤ 0.1 | pass |
| s08 | C2 steering (α grid 1/2/3) | det (n91): −0.409 / −0.990 / −1.712; strict flips 7 / 23 / 37 of 52 with baseline > 0. ibp (n35): −1.433 / −4.104 / −8.030; flips 2 / 26 / 30 of 33. CTRL_RAND/CTRL_BORING: det \|mean\| ≤ 0.01, ibp −0.015 / +0.018; CTRL_ATTN det +0.198, ibp −0.286 with 1 flip (§6.10) | per domain: mean delta_ld negative at every α, monotone; strict flips at α=3 ≥ 20% (det) / ≥ 40% (ibp) of cases with baseline > 0; CTRL_MAG \|mean\| ≤ 0.1 | pass |
| s09 | Judge armB logit boosts (L32 check + L15 ctrl; γ in {1.5, 2, 3}) | det (n91): L32 fixes 0/1/2 of 52; L15 fixes 0/1/5 of 52 (see §6.8). ibp (n35): 0 fixes everywhere | fixes ≤ 5% per domain at every γ **for L32 only** (the confirmatory null site); L15 ctrl reported descriptively (§6.8). Exploratory arm — L32 is not a validated checker (§2) | **null** |

## 3b. Criteria — correct (deepsign) domains

Anchors recomputed from the raw discovery JSONs staged in
`results/Mistral/{det_4x4_correct_deepsign,ibp_correct_deepsign}/` (folded
2026-09-14 from the sanctioned deepsign-fix run, md5-verified — see
`PROVENANCE_NOTES.md`). Discovery n: det 78 / ibp 43 (42 in expG′/s09). On
correct cases the wrong sign leads at the deep position for most cases
(discovery det 71/78, ibp 41/43 with baseline_ld > 0) — the habit fires
mid-computation; the causal arms remove it (§6.11). **ibp correct is small-n
(n=43) throughout — every ibp bar below is flagged small-n and reported with
exact counts.** "Broken" = strict crossing on a baseline_ld > 0 case.

| Stage | Test | Discovery anchor | Pass bar (held-out) | Predicted |
|---|---|---|---|---|
| c-s01 | Logit lens, late peak | det 76/78 (97.4%) peak ≥ L30; ibp 43/43 (100%) | det ≥ 80% and ibp ≥ 85% of cases peak ≥ L30 | pass |
| c-s02 | MLP DLA signs | det: L37 +1.51, L38 +1.70, L39 +0.38, L34 +0.46; ctrls ≤ 0.03. ibp: L37 +1.99, L38 +2.20, L39 +0.76; ctrls ≤ 0.01 | per domain: mean MLP DLA positive at L37 AND L38; ctrls \|mean\| ≤ 0.1 | pass |
| c-s04 | Projections onto d-hat | discovery capture: det n=78, ibp n=43, layers [31,37,38], 0 missing fields. No discovery contrast computed — prediction stated here, not anchored | per domain: minus-writer mean projection > plus-writer mean projection at L37/L38 (sign of d-hat convention fixed at pre-flight from discovery) | pass |
| c-s05 | Habit-site MLP mean-ablation (expD′) | det: L37 −0.783, L38 −0.599, L39 −0.501; ctrls L15 −0.081 / L25 −0.016. ibp: L37 −1.235, L38 −0.994, L39 −0.920; ctrls L15 −0.049 / L25 −0.158 | per domain: mean delta_ld negative at L37, L38 AND L39; det all three below −0.20, ibp all three below −0.40; ctrls \|mean\| ≤ 0.25 | pass |
| c-s05 | Joint TARGET_SET ablation (expE′) | det (n78): pooled −3.395, 39/78 (50%) beat null p5, 8 strict breaks. ibp (n43): pooled −4.616, 39/43 (90.7%) beat null p5, 1 break | det: pooled mean delta_ld ≤ −1.5 AND ≥ 35% beat own null p5. ibp: pooled ≤ −2.0 AND ≥ 70% beat null p5. Break counts descriptive | pass |
| c-s06 | Direction subtraction (expG′) | det (n78) α=2: L37 −0.575, L38 −1.412, L39 −1.266, monotone; ctrls \|mean\| ≤ 0.014. ibp (n42) α=2: L37 −1.031, L38 −2.166, L39 −2.083, monotone; ctrls ≤ 0.02 | per domain: mean delta_ld negative at L37, L38 and L39 at every α AND monotone across the α grid; controls \|mean\| ≤ 0.05 | pass |
| c-s08 | C2 steering on corrects (α grid 1/2/3, pair [38,39]) | det error-cases (n71): mean −2.29 / −6.17 / −11.53; broken 0 / 28 / 55 of 71. ibp error-cases (n41): −3.04 / −7.86 / −14.43; broken 0 / 13 / 32 of 41. CTRL_MAG \|mean\| ≤ 0.13 both domains | per domain: mean delta_ld negative at every α, monotone; broken at α=3 ≥ 40% of baseline > 0 cases; CTRL_MAG \|mean\| ≤ 0.2 | pass |
| c-s09 | Judge crossdomain (L32 + L15; γ in {1.5, 2, 3}) | det (n78): L32 fixes 0/0/1; L15 0 everywhere. ibp (n42): 0 everywhere | **no bar — descriptive null** (L32 is not a validated checker, §2); report exact counts | **null** |

## 4. Exclusions (pre-registered)

- s00, s03 (re-derivation destroys the design); **all free-text generation**
  (s08 runs the C-arm teacher-forced conditions only; no `--with-generation`).
- **s05c joint head-group ablation:** exploratory discovery result only (E4,
  §6.10; frozen groups in `pipeline_release/groups_mistral_det.json`); not part
  of the held-out battery.
- **s05b on correct domains:** never ran in discovery — no frozen anchor, not
  part of the battery (error domains only).
- **s08 C3/C4 arms (error domains):** recorded and reported descriptively but
  carry no confirmatory bar — C2 only is anchored (§6.9).
- Single-site check-layer ablation as a confirmatory claim (L32 exploratory).
- Any analysis whose composition cell is empty.

## 5. Small-n

Every stratum with n < 50 (det error plus-written n=18, ibp error plus-written
n=11, ibp error domain n=70, det correct plus-writers n=32, ibp correct
discovery anchor n=43, all ≥+2 / <+2 strata, all flip, break and fix counts)
is flagged small-n and reported descriptively with exact counts (x/n)
alongside the point estimate.

## 6. Disclosures (Mistral-specific)

1. **VLM loading:** Mistral-Small-3.2-24B is a vision-language model, loaded via
   `AutoModelForImageTextToText`; text-only path used throughout, same
   weights/dtype/revision as discovery.
2. **Det error probe position is early in the text** (median rel-depth ~0.33,
   unlike Gemma/Qwen). Layer peaks are late (51.6% ≥ L30, the s01 anchor), but
   only 38% (36/95) fall exactly in the frozen habit set {37,38,39}, and 28/95 cases
   peak at L10. The habit set was frozen from the correct-domain peak structure
   (89–95% in {37,38,39}) — a known property, not tuned around.
3. **Thin error margins:** discovery det errors mean true_ld 0.81, ibp 2.65 (vs
   6–13 on corrects) — flips are cheap; the ≥+2 strata carry the load, and both
   are small-n.
4. **Attention caveat:** attn L38 DLA is large on corrects (0.87–1.74) vs small
   on errors — attention carries its own correctness gap. MLP-only ablation
   understates the circuit; s05b covers L38 heads and was near-null on errors.
   Stated limitation.
5. **ibp error is minus-dominated:** discovery ibp errors had zero plus-writers;
   the held-out ibp error plus stratum (n=11) is exploratory/descriptive only.
6. **Targets:** per-domain `targets.json` are PI-reviewed picks (errors
   2026-09-14; corrects inherit the frozen master); the frozen master differs
   from the pod's initial auto-suggestions in habit, check, and capture layers
   (details in `PROVENANCE_NOTES.md`).
7. **expD′ ibp error L15 control anomaly:** L15 ctrl mean +0.239 (causal
   delta_ld from zeroing the L15 residual stream, ibp n=39) exceeds every ibp
   error habit-site effect — it is why ibp error s05 carries no confirmatory
   bar. Distinct from the s02 ibp L15 MLP DLA anchor of −0.015; the two
   measure different things. (The correct-domain expD′ shows no such anomaly.)
8. **s09 det error control anomaly:** at γ=3 the L15 control fixes more cases
   (5/52 = 9.6%) than the L32 check (2/52 = 3.8%) — consistent with "no checker
   exists". The confirmatory ≤5% bar covers L32 only; L15 is descriptive.
9. **s08 C3/C4 (error domains):** C3 (amp 0.5) and C4 (amp 0.0) produce
   distinct per-case results from C2 (only 6 det / 1 ibp coincide at α=2);
   recorded, no bar, C2 is the sole anchored arm.
10. **Control-arm flips in discovery (disclosed, not expected):** E4 joint-head
    ablation — 0 strict flips in any arm under §2's criterion; the run's looser
    flip flag marked 1 tie each (edit_ld exactly 0) in J1_pushers and J4_ctrl
    (L32_H22, L36_H9), disclosed here. s08 CTRL_ATTN — 1 true strict ibp flip
    (`ibp_pts_n15_b71`, delta_ld −0.5); all other control arms 0 flips.
11. **Correct-domain (deepsign) conventions:** label inversion (`written_sign =
    wrong_sign` in correct files); the wrong sign leads at the deep position on
    most correct cases in discovery (det 71/78, ibp 41/43) — this is the
    phenomenon under test, not an error. One ibp discovery case is
    `embedding_bias` (excluded from habit-layer arms, n=42 where noted).
    Correct-domain expE′ TARGET_SETs differ from the error domains' (§2 table)
    — each is deterministic from its own domain's frozen discovery DLA.

## 7. After the run

There is no second confirmatory phase. Any re-mining of the held-out data
after the Phase-1 verdicts lock (head screens, depth-bin slices, L38-attention
designs) is EXPLORATORY, labeled so in the paper, and would need its own
future held-out set.

## 8. Run mapping

- Pipeline `pipeline_release`: errors — s01, s02, s04, s05 (D′ + E′), s05b
  (frozen `sites_{domain}.json`), s06, s08 (C-arms + CTRL_MAG, no generation),
  s09 (armB only). Corrects — s01, s02, s04, s05 (D′ + E′), s06, s08
  (c2_on_correct + CTRL_MAG), s09 (judge crossdomain); no s05b. Never
  s00/s03/s05c.
- Config: new `MODEL_CONFIGS` entry `mistral_heldout` (exact copy of `mistral`,
  `results_name: "Mistral_heldout"`); data converted to
  `mistral_heldout_{domain}_experiment_ready.xlsx` (4 files),
  content-equivalent to the frozen CSVs after the pre-registered pre-flight
  (M2 rule on error files only), checksummed in the pre-flight report.
- Env: `SIGN_DATA_DIR` / `SIGN_RESULTS_DIR` → held-out dirs; results archived
  under `heldout/Mistral/results/{domain}/`.
- Targets: `targets_frozen_mistral.json` + per-domain targets + sites files
  copied unmodified; s03 never runs.
- Pre-flight: per-row sign-token ids logged (deep variants on corrects); d-hat
  construction and hook capture demonstrated on 2–3 sample cases per domain
  before the battery; counts reported before any measurement.
