# Provenance and housekeeping notes — Mistral prereg package

These notes cover file provenance and process history. Nothing here governs
the held-out run; the binding plan is `PREREGISTRATION.md`.

## 1. Anchor source tars

Error-domain anchors come from two pod tars: the causal tar (s06/s08/s09;
error-domain files fresh, sequential mtimes 2026-09-12 01:10–05:13) and the
fullset tar (s01/s02/s04/s05/s05b, 2026-09-13). The causal tar's DEEPSIGN
correct-domain folders are stale (mtime 2026-09-11 16:36, pre-fix) and are
quoted nowhere; the only sanctioned correct-deepsign source is
`mistral_deepsign_fix_results_20260912.tar.gz`.

## 2. E2 projection file overwrite

`exp_capture_projections_det_4x4_error.json` and
`exp_capture_projections_ibp_error.json` are overwrites of buggy Sep 11
versions, replaced by the 2026-09-13 E2 pod run. The sidecar copies under
`{domain}/v1_zero_ablation/exp_capture_projections.json` are byte-identical to
the top-level files (MD5-verified). No Sep 11 versions remain in the staged
tree.

## 3. Targets: auto-suggestion vs frozen master

The pod's initial auto-suggestions (`*_targets_autopick.json`,
`human_reviewed: false`, kept on disk, not committed) differ from the frozen
master `targets_frozen_mistral.json`: habit layers auto det [34,37] / ibp
[37,38] → frozen [37,38,39]; capture layers expanded from [34,36,37] /
[32,37,38] to [32,36,37,38,39,15,25] for both error domains, via PI review
2026-09-11 and the E2 fresh run 2026-09-13. Per-domain error `targets.json`
files are the PI-reviewed picks (`human_reviewed: true`, `pi_review_date:
2026-09-14`); correct-domain `targets.json` files inherit the frozen master
(`frozen_source: mistral_targets_frozen.json`).

## 4. Protocol history

An earlier gated repro-gate run and a role-matched subset protocol were
replaced by the stratified full-set ungated protocol; both are archived
(`ARCHIVE_mistral_gated_20260913`) and quoted nowhere in the prereg.

## 5. s05b correct-domain numbers

s05b correct-domain numbers are early-c1, not deepsign role-matched (deepsign
s05b never ran); they are never mixed into any deep-position claim. s05b is
error-domains-only in the battery (§4 of `PREREGISTRATION.md`).

## 6. Stale cross-model naming in metadata (cosmetic)

Projection files' purpose string says "L78"; judge meta prediction says
"L77/L79/L30"; ctrl_mag case keys include `m_L75`/`m_L78` — Qwen-naming
leftovers in free-text/aux fields only. All layer indices in measured results
are Mistral's.

## 7. s02 eff_dir bug (inherited from Gemma finding)

Only MLP DLA is used as an anchor anywhere in the battery; no attention-DLA
anchor exists.

## 8. Correct-deepsign canonical fold (2026-09-14)

The canonical `results/Mistral/{det_4x4_correct_deepsign,ibp_correct_deepsign}/`
folders were missing all causal-stage files and held stale auto targets
(`human_reviewed: false`, habit [37,38], check 31). On 2026-09-14 the
sanctioned deepsign-fix tar (`mistral_deepsign_fix_results_20260912.tar.gz`)
was folded in: per domain, 5 causal JSONs added under `v2_mean_ablation/`
(expD′, expE′, expG′, c2_on_correct, judge_crossdomain), stale `targets.json`
overwritten with the frozen version (`human_reviewed: true`, habit [37,38,39],
check 32, `frozen_source: mistral_targets_frozen.json`), the auto version kept
as `targets_autopick_backup.json`, plus 2 top-level capture-projection files —
16 files total, each MD5-verified against the tar extraction. The staged repo
copies were independently MD5-matched to the same tar. All §3b anchors are
recomputed from these folded files.
