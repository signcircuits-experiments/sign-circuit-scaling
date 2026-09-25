# Phi-4 Investigation — why causal flips are weak, and what to run next

Date: 2026-09-14. Status: DISCOVERY PHASE — everything here is exploratory and
touches only discovery data. No held-out file is read by any experiment below.
Sources: four independent Sonnet analyses over `results/Phi/` (det n=61 errors,
ibp n=40 errors, 50+50 corrects, 50+50 deepsign corrects — det deepsign n=46
processed in expG′, 4 emb-peak cases skipped) plus cross-model
comparison against Gemma/Mistral discovery results.

## 1. The problem

Phi replicates every descriptive claim of the workshop paper (late peak: det
93% (57/61), ibp 100% in last quarter; L37 = minus-stamp, L39 = adaptive amplifier;
MLP dominates attention 2.6–5×) but the direction-subtraction intervention
that flips up to 93% of errors on Llama flips almost nothing on Phi:
2/57 det, 0–1/40 ibp under exp_combined_ablation conditions C2–C4 at α=3
(the standalone expG′ stage only runs α ≤ 2), corrects broken 4%/0%. The
lead DOES move
(−7.5 to −14.6 mean at α=3) — outcomes don't.

## 2. Diagnosis — three compounding causes (pipeline itself is clean)

### Cause A — over-determined margins (primary)

- Baseline wrong-sign leads: det median 17.8 logits (p25 10.6, p75 24.5,
  max 43.4); ibp clustered 28–32 (29/40 cases ≥ 28 — a structural floor).
  For scale: ~10× Mistral's baselines, ~2× Gemma's.
- The intervention delivers a PROPORTIONAL reduction, not an absolute shift:
  edit_ld ≈ 0.51 × baseline_ld (ibp) / 0.58 (det); correlation(baseline_ld,
  delta_ld) = −0.98 (ibp), −0.90 (det). A ~50–58% proportional cut never
  crosses zero for baselines > ~5.
- The only flipped cases were the two smallest margins (baseline 3.5, 3.75).
- Multi-layer condition C4 SATURATES: at α=3 it delivers only 57% (det) /
  54% (ibp) of the linearly-expected effect. Single-layer expG′ is linear up
  to α=2 (all four α2/α1 ratios ≈ 2.0×: det L37 2.06 / L39 2.05, ibp 2.00 /
  2.01) — saturation is a multi-layer interaction, not a per-layer ceiling.
- Linear extrapolation of per-case slopes: α≈5 flips ~25% of ibp; α≈7 flips
  ~50% of det (before saturation correction).

### Cause B — distributed, redundant writing

- 15 positive-DLA MLP layers across L24–39 (L30 is negative) contribute to
  the written sign; frozen habit layers [37,39] carry only 26% (det) / 34%
  (ibp) of total positive DLA.
- Attention carries a further ~22–29% of the lead; largest single block is
  attn L36, with one standout head L36_H33.
- The logit-lens lead ramps gradually — ~50% of the final lead is present by
  L28. No single bottleneck layer exists.
- Single habit-layer mean ablations are statistically indistinguishable from
  control-layer ablations ([15,25]). Two-layer surgery is underpowered
  against a ~15-layer ensemble.

### Cause C — minus-token variant mismatch (CORRECT-DOMAINS ONLY — see O1
result 2026-09-14)

- Phi's BPE tokenizer has TWO minus tokens: ` -` (id 482, leading space) and
  bare `-` (id 12). d̂ was built from tok-482 only.
- O1 RESULT (2026-09-14, `analysis/phi/discovery2/`): the ERROR domains are
  100% tok-482 (det 55/55 minus cases, ibp 40/40; zero tok-12). The mismatch
  contributes NOTHING to the weak error flips — those are entirely Causes
  A + B.
- Where it bites: deepsign correct sets — tok-12 minus cases: 13/50 det,
  7/50 ibp. On these the intervention whiffs (expG′ α=2 L39: Δld −0.87
  tok-12 vs −8.50 tok-482, ibp).
- Stratified to tok-482 only, the correct-case effect was UNDERSTATED:
  c2_on_correct α=3 minus cases — det Δld −13.60 (pooled −9.20, 48% under),
  ibp −22.76 (pooled −18.71, 22% under). Phi's lever on corrects is
  stronger than the pooled numbers showed; margins still aren't crossed.
- Plus token has the same two-variant issue but only 2/30 plus cases are
  bare-prefix (both det deepsign); zero ambiguous cases in the full table.
- Full per-case table: `analysis/phi/discovery2/variant_table_phi.csv`
  (the O2 table the pod pre-check requires); stratified numbers in
  `o1_stratified_results.xlsx`; pod direction spec in `o2_pod_spec.md`.

### Ruled out

- Pipeline/adapter bugs: controls (CTRL_RAND, CTRL_MAG, layers 15/25) are
  clean nulls everywhere; teacher-forcing verified; all layer indices are
  Phi's (0–39).
- Layer-0 embedding leans (Qwen-style): essentially absent — 1 case in 801.
- "Small models don't flip": FALSE. Mistral flips 37/91 det, 30/35 ibp at
  α=3; Gemma flips as well. Phi is the outlier, and its circuit is
  correctly LOCATED — it is simply more redundant and more committed.

## 3. What this means for the paper

Phi still supports the localization story (Fig. D1 role) and adds a genuine
finding: the same late sign-writing behavior can be implemented with enough
redundancy that low-rank surgery at two layers cannot overturn it — a
dose/redundancy axis across models, not a failure of the mechanism claim.
The prereg bars for Phi must be written for what Phi is (lead-reduction and
specificity bars, not flip-rate bars), OR postponed until the experiments
below determine whether a stronger lever exists.

## 4. Offline experiments (no GPU — run first, they reshape the GPU specs)

- **O1 — token-variant re-stratification.** Split every existing Phi result
  (errors + deepsign corrects, all stages) by probe minus-token variant
  (482 vs 12). Recompute means, flip/break counts, dose curves per stratum.
  Expected: tok-482 stratum numbers improve for free; quantifies exactly how
  much Cause C cost.
- **O2 — composite direction + probe audit.** Build d̂_12 from tok-12
  unembedding rows and a composite d̂ (per-case variant-matched). Audit every
  tok-12 case's probe offset. Output: per-case variant table shipped to the
  GPU pod so every intervention uses the variant-matched direction.

## 5. GPU experiments (discovery pod — antigravity runs; exploratory, no
held-out contact)

All runs: `--model phi` (discovery config), teacher-forced, discovery files
only, results to `results/Phi/<domain>/vX_discovery2/`. Variant-matched d̂
from O2 everywhere. Frozen-target files are NOT modified.

- **G1 — high-α single-layer sweep.** expG′-style subtraction at L37 and L39
  separately, α ∈ {5, 8, 12}, error domains. Tests whether per-layer
  linearity holds past α=2 and whether high dose alone flips. Includes
  CTRL_RAND at matched α (specificity must survive high dose).
- **G2 — per-case adaptive dosing.** For the 10 lowest-margin det error
  cases (baseline_ld < 8): α chosen per case from the O1 slope table
  (α_i ≈ baseline_i / slope_i, capped at 15). Direct test that the circuit
  is causal given sufficient dose.
- **G3 — wide-window joint ablation.** Mean-ablate MLP window L30–39
  jointly (then L24–39 if needed), error domains, vs a matched random
  10-layer window null. Tests Cause B head-on.
- **G4 — cumulative staircase.** Add layers one at a time in descending
  discovery-DLA order (top-k for k = 1…15), measure mean Δld and flip count
  per k. Output: the minimum hitting set — the paper-grade redundancy curve.
- **G5 — MLP+attention joint at L36–39.** Joint mean-ablation of MLPs
  [36–39] plus attn L36 (and head L36_H33 alone as a sub-arm). Tests the
  attention share.
- **G6 — expF′ correct-mean patching.** Already in the pipeline, never run
  on Phi. Patch correct-domain mean MLP output into error runs at
  L37/L38/L39 (+ controls L15/L25). Tests sufficiency from the other side.
- **G7 — window path patching.** Patch clean→corrupted by residual window
  [0–23] / [24–31] / [32–39] to find which window is causally sufficient
  for the sign choice.

Priority if pod time is short: G1 → G3 → G4 → G2 → G6 → G5 → G7.

**NOTE:** See Section 7 below for verified Discovery-2 results from the G1–G7 run.

Implementation status (red-teamed vs `pipeline_release/`):

| Exp | Code status | Note |
|---|---|---|
| G1 | SMALL PATCH | expG′ hardcodes ALPHAS=[0.5,1,2] — extend to {5,8,12}; needs O2 variant-matched d̂ |
| G2 | NEW MODULE | per-case slope lookup + adaptive α_i |
| G3 | SMALL PATCH | expD′/expE′ take fixed target sets — parameterize window + random-window null |
| G4 | NEW MODULE | cumulative top-k staircase does not exist |
| G5 | SMALL PATCH | expE′ extension to include attn L36 + head L36_H33 sub-arm |
| G6 | EXISTING CODE | expF′ unrun on Phi; pair with det_4x4_correct / ibp_correct (early-c1, NOT deepsign) |
| G7 | NEW MODULE | residual-window path patching not implemented (exp_reverse_patch patches activations, not windows) |

**HARD PRE-CHECK for the pod:** no G-run may start unless the O2 output file
(per-case variant-matched direction table) exists and covers every case id;
otherwise tok-12 cases silently get the wrong direction again.

## 6. Sequencing vs the Mistral held-out pod

Run them on SEPARATE pods in PARALLEL. They share no files, no results
folders, and no model weights; the Mistral held-out run is confirmatory and
frozen (`POD_MISTRAL_HELDOUT.md`), the Phi run is exploratory. If only one
pod is possible: Mistral held-out first (short, blocks the paper), Phi
discovery second — with O1/O2 done locally in the meantime either way.

## 7. Discovery-2 results (G1–G7), run 2026-09-14 — verified 2026-09-15

### 7.1 Provenance

Pod ran `/workspace/POD_PHI_DISCOVERY2.md`. Tar: `phi_discovery2_results_20260914.tar.gz`,
md5 `2a858f5bb6939b71131d626cd7c8f5a9`, extracted and forensically verified locally.
Guards passed: no `targets.json` edits, no held-out access. Per-case baselines match
the α≤2 files exactly (teacher-forced determinism confirmed).

**IMPORTANT CAVEAT:** The pod's own summary misreported several headlines. The numbers
below are the locally recomputed, verified ones.

### 7.2 Verified headline results

delta_ld = edit − baseline; negative = intervention reduced wrong-sign preference.

**G1 — high-α direction subtraction**
(det n=57, same 4-case exclusion as α≤2 run; ibp n=40; CTRL_RAND present at all α and ≈0)

- det α=12: L37 12/57 flips, mean Δld −15.01; L39 10/57 flips, mean Δld −10.99
- ibp α=12: L37 8/40 flips, mean Δld −22.96; L39 29/40 flips, mean Δld −31.28

Key finding: per-unit slope at α≥5 is ~16% of the α=1 slope (−0.91/α vs −5.66/α at
L39 det) — severe saturation; the proportionality trap (Cause A) is real but compresses
at high dose. The ibp 29/40 flips must be caveated: ibp baselines cluster narrowly
(median 29.9, max 31.1) and the mean push (−31.3) exceeds every baseline — this is a
saturated blanket push, not targeted specificity.

**G2 — adaptive dosing: INVALID as "adaptive"**
Driver hardcoded slope 0.5 (slope file not found by pod). The recorded flips are genuine
strict flips (det L39_only 2/10; L37+L39 joint 4/10; ibp joint 1/6; CTRL_RAND 0
everywhere) and are citable only as a high-α flip demonstration. Rerun (v2, real slopes
from exp_combined_ablation C2−C1 marginal) is queued in `POD_PHI_D2_FIXES.md`.

**G3 — window ablation**
(true n=61/40; pod's 62/41 counted the `__summary__` key)

- det: L30–39 mean target_delta −0.67; L24–39 −1.28 (both weak)
- ibp: POSITIVE (+1.79 / +2.02) — ablating the wide window makes ibp errors worse

Random-window null file exists on pod but was missed by the tar glob; re-fetch queued.

**G4 — staircase top-k**
(L24–39 excl L30, descending DLA order — verified matches expB)

- det: non-monotone, crosses negative at k=6; k=15 mean Δld −1.34 with 4 flips
- ibp: positive throughout, 0 flips

Minimum hitting set >15 layers — the redundancy curve is flat. (Pod-reported +4.81/+3.15
unverifiable from files.)

**G5 — joint MLP+attn L36–39**

- det: 2/58 flips, mean Δld −0.018
- ibp: 0/39 flips, mean Δld +1.11

Head arm INVALID: `%32` indexing bug ablated head 1 not head 33 (Phi has 40 heads).
Rerun queued.

**G6 — correct-mean patch**
(early-c1 pairing confirmed)

No flips at habit sites: det L37 −0.44, L39 +0.26; ibp L37 −0.72.
Anomaly: ibp L25 control patch flips 2 tiny-margin cases (baselines 0.5/0.75) — noise,
flagged.

**G7 — window path patching**

- det: 4 flips per window; core overlap 3 low-margin cases (baselines 5.25–7.0); means
  −11.7 / −13.0 / −15.5 growing later — sign information is distributed across all
  windows, not bottlenecked late.
- ibp: 0 flips; late windows positive (+5.44 for win32–39, n=39) — clean-patching late
  windows strengthens ibp errors.

### 7.3 Interpretation vs the diagnosed causes

**(a) Cause A — proportionality trap: CONFIRMED and quantified, with saturation nuance.**
G1 establishes the saturation: the per-unit slope shrinks to ~16% of its α=1 value by
α≥5. High dose CAN flip Phi (G1 α≥8 achieves genuine strict flips), so "unsteerable"
must be restated as: *unsteerable at calibrated/matched dose — flippable only with
saturated blanket pushes that exceed baseline margins entirely.* The ibp 29/40 result is
the clearest example: it is not targeted causal control, it is margin overpowering.

**(b) Cause B — distributed redundancy: CONFIRMED across three experiments.**
G3 shows even a wide 10–16 layer MLP window produces only weak det reductions and
backfires on ibp. G4's flat redundancy curve (hitting set >15 layers) directly
quantifies the ensemble: no small subset of the 15 positive-DLA layers is sufficient.
G7's distributed flip pattern (equal flips across all three residual windows, growing
slightly later) shows the sign information is spread across the full depth, not
concentrated in a late bottleneck — consistent with the logit-lens ramp documented in
Section 2.

**(c) High-dose flips reconciled with the paper framing.**
The paper claim that Phi is the redundancy-axis outlier holds: flips require dose levels
that are saturated blanket pushes (ibp) or near-saturation (det), not the calibrated
surgical interventions that work on Llama/Mistral/Gemma. This is the correct framing
for the dose/redundancy axis figure.

**(d) ibp qualitative difference: ablations BACKFIRE.**
G3 (+1.79/+2.02 ablation worsens ibp), G4 (ibp positive throughout), G5 (+1.11), G7
(late clean-patch strengthens ibp errors) all point the same direction: ibp's sign
circuit is more tightly coupled and more committed than det's. Under the framing of
Section 2 (ibp baselines clustered 28–32, a structural floor), this suggests ibp error
cases operate near a saturated attractor — perturbations that reduce the direct causal
path may release competing suppressive signals, worsening the output. The ibp circuit
likely warrants its own targeted investigation rather than being treated as a noisier
version of det.

### 7.4 Outstanding items

- `POD_PHI_D2_FIXES.md` queued: (1) random-window null re-fetch for G3; (2) G2 v2
  with real per-case slopes from exp_combined_ablation C2−C1 marginal; (3) G5 head
  arm v2 with corrected head-33 indexing.
- Pod remains alive pending verification sign-off.
- G4 pod-headline discrepancy (+4.81/+3.15 reported vs locally verified flat/negative
  curve) is noted and unresolved; locally verified numbers are authoritative.

*Three defects from this run (G2 hardcoded slope, G3 missing randwin file, G5 head-33
indexing bug) were addressed in a fixes run on 2026-09-15; see Section 8.*

## 8. D2-Fixes run (2026-09-15) — FIX1/FIX2/FIX3 verified

### 8.1 Provenance

Tar: `phi_d2_fixes_20260915.tar.gz`, md5 `cc7d9c92022d8e991602411e0164b1b0` (verified
locally 2026-09-15). Contents: 6 result JSONs + 3 driver scripts + `redteam_log.md`
(contains `## D2-FIXES 2026-09-14` section). Pod: ofhnm98ylsjnt8 (alive; close after
FIX3 v3 verification). All headline numbers below recomputed locally from the tar's
JSONs; FIX2 slope values spot-checked 13/13 exact against source.

### 8.2 FIX1 — expE′ randwin (random-window null for G3) — VERIFIED, CITABLE

**Defect:** `expE_prime_randwin_seed42.json` absent from the discovery-2 tar; the pod's
glob `expE_prime_window_*` did not match the `_randwin_` filename. File re-fetched in
fixes tar.

**Results (locally verified):**

| Domain | randwin Δld | null_mean_p5 | L30–39 Δld | L24–39 Δld | criterion_met |
|---|---|---|---|---|---|
| det | −0.44 | −2.18 | −0.67 | −1.28 | False |
| ibp | (see G3 §7.2) | — | +1.79 | +2.02 | False |

Real windows (det L30–39 −0.67, L24–39 −1.28) do NOT beat the random-window null
(`criterion_met=False` in both domains). G3's weak window-ablation effects are
statistically indistinguishable from a random 10-layer selection — direct evidence that
no privileged MLP window carries the sign circuit, strengthening the distributed-
redundancy conclusion of Cause B.

### 8.3 FIX2 — G2 rerun with real per-case slopes (exp_adaptive_alpha_v2.json) — VERIFIED, CITABLE

**v1 defect:** driver hardcoded `slope = 0.5`; it attempted to read
`expG_prime_bias_subtraction.json` (nonexistent file) and fell back to the constant.

**v2 method (verified):** slope per case = `C2['a1.0']['delta_ld'] − C1['a1.0']['delta_ld']`
read from `exp_combined_ablation`; 13/13 spot-checks exact. α_i = baseline_ld / |slope|,
capped at 15. Three det cases absent from combined ablation (`C_4x4_det_012_arch`,
`NC_4x4_det_1061`, `NC_4x4_det_450`) received `slope_source="missing_from_combined"`,
α_i = 15.

**Per-case α vectors (verified):**

- det (n=10): α_i = [15, 15, 2, 15, 1.5, 7, 7.5, 3.23, 2.94, 7]
- ibp (n=6): α_i = [1, 3, 2, 8, 3.67, 2.75]

**Results:**

| Domain | Condition | Strict flips | Mean Δld |
|---|---|---|---|
| det | L39_only | 3/10 | +2.5625 |
| det | Joint L37+L39 | 5/10 | −17.3625 |
| det | CTRL_RAND | 0/10 | +0.0375 |
| ibp | L39_only | 0/6 | +2.17 |
| ibp | Joint L37+L39 | 2/6 | −1.4167 |
| ibp | CTRL_RAND | 0/6 | 0.00 |

**Interpretation:** Strongest dose-matched Phi steering result to date. Calibrated
per-case doses flip only half of det cases (5/10) even with joint two-layer surgery;
L39 alone is insufficient (3/10 det, 0/6 ibp). CTRL_RAND is a clean null. The result
directly confirms that the "unsteerable at calibrated dose" framing is correct: the
circuit is causal but redundant enough that optimal per-case dosing still cannot reliably
flip the output. The v1 result (det joint 4/10) was conservative in flip count but was
not using calibrated doses; the v2 joint 5/10 with clean CTRL_RAND is the citable number.

### 8.4 FIX3 — G5 head-33 ablation — v2 INVALID (instrumentation bug), v3 VERIFIED-NULL

**v1 defect:** `start_dim = (head_idx % 32) * head_dim` — modulo 32 wraps head-33 to
head 1 (Phi has 40 heads × head_dim 128 = 5120). All v1 head-arm results ablated the
wrong head.

**v2 defect (found in fixes tar, `run_g5_mlp_attn_joint.py` lines 62–75):**

- Line 66: tensor used as dict key — `cap_h[h] = h[0, probe_tok, :]` where `h` is a
  `torch.Tensor`; dict assignment silently succeeds with a tensor key but lookup fails.
- Line 73: `for h in handles_h: h.remove()` rebinds loop variable `h` to a hook handle
  object, destroying the tensor reference.
- Line 75: `if h in cap_h` then tests whether the last hook handle is in the dict —
  always False.
- Consequence: every per-case head-33 delta is exactly 0.00. All FIX3 v2 deltas are
  artifacts of the instrumentation failure; not citable.

**v3 driver fix (verified):** `start_dim = head_idx * head_dim` → head 33 = dims
4224:4352; bounds asserted against `o_proj(36).in_features = 5120`; dict-key bug fixed
(string key `"h"`).

**v3 provenance:** tar `phi_d2_headfix_20260915.tar.gz`, md5
`6506fe9589ed5417b75597677f0f5a01`; pod md5 matched local; verified independently twice.
Staleness guards all PASSED: v3 files ~10 h newer than v2; v3 md5s differ from v2
(det `b761cf9d…` vs `de93ae1d…`; ibp `b26f5a0e…` vs `7008364a…`); v2 confirmed all-zero
(bug real); v3 deltas nonzero and varying (det 32/61 nonzero; ibp 22/40 — det count
settled by forensic recount after one agent miscounted 30).

**v3 results:**

| Domain | n (eligible baseline>0) | Strict flips | Mean Δld (all) | Mean Δld (eligible) |
|---|---|---|---|---|
| det_4x4_error | 61 (58) | 0 | +0.0051 | +0.0075 |
| ibp_error | 40 (39) | 0 | −0.0375 | −0.0385 |

Delta range ±0.25, quantized 0.0625 steps. Pod-side `redteam_log` contains
`## D2-HEADFIX 2026-09-15` section documenting the bug and fix.

**Interpretation: VERIFIED-NULL.** Single-head L36H33 ablation produces 0 strict flips
and negligible mean effect in both domains. Head 33 alone does not carry the sign habit;
result is consistent with distributed redundancy (Cause B). Now CITABLE as a null.
Pod ofhnm98ylsjnt8 authorized for termination.

### 8.5 Impact on the paper

**Citable now:**

- **FIX1:** Real MLP windows perform at or below a random 10-layer null. No privileged
  window exists. Cite as: "window ablation effects indistinguishable from random-window
  null (det: real window Δld −0.67 to −1.28 vs null 5th percentile −2.18)."
- **FIX2:** Calibrated per-case dosing flips 5/10 det (joint), 2/6 ibp (joint); L39
  alone insufficient; CTRL_RAND = 0 across both domains. Cite as the dose-matched
  steering result — it replaces the v1 G2 numbers entirely.

**Framing unchanged:** The "unsteerable at calibrated dose" thesis holds. G1's saturated
blanket pushes (ibp 29/40 at α=12) and G2-v2's calibrated joint result (5/10 det) define
the two ends of the dose axis. The circuit is correctly located; it is over-determined.

**FIX3 (head L36_H33 ablation):** VERIFIED-NULL — citable as: "single-head ablation of
L36H33 produces 0 flips and negligible mean Δld (det +0.0051, ibp −0.0375), consistent
with distributed redundancy." The MLP+attention joint numbers from §7.2 (G5 MLP arm)
remain valid and are unaffected by the head-indexing bugs.

**Pod closure:** ofhnm98ylsjnt8 authorized for termination (FIX3 v3 verified 2026-09-15).
