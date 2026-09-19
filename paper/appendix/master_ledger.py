#!/usr/bin/env python3
"""MASTER DATA LEDGER — sign-flip circuit paper (ICLR 2027).

Single source of truth for every expA logit-lens case used in the paper.
All downstream tables/figures (paper/appendix/make_numbers_ledger.py,
paper/appendix/verify_all.py, appendix ibp work) read the CSVs this
script writes — never the raw JSONs directly.

Run from the repo root:
    python paper/appendix/master_ledger.py

Outputs are written next to this script (paper/appendix/).

VERIFIED FIELD SEMANTICS (audited twice — do not rediscover):
  - expA logit-lens JSONs are dicts case_id -> case. In ALL files (error and
    correct alike): `written_sign` = the char the model actually wrote;
    `correct_sign` = the OPPOSITE foil in correct files (never use it for the
    written sign); `layer_diffs` = dict layer -> logit(wrong_sign_tok) -
    logit(correct_sign_tok), i.e. the lead of the written char.
  - final_lead = layer_diffs value at the max layer key. Trust filter:
    final_lead >= +2 logits (confirmed: written sign leads at final layer);
    cases failing this (weak lead <2 OR reversed sign leading) are FLAGGED,
    never deleted.
  - peak_layer = signed argmax of layer_diffs (recomputed here; compared to
    the stored `peak_layer` field, warning on mismatch — never forced).
  - rel_depth = peak_layer / (n_layers - 1)   [paper-wide depth convention]
    where n_layers = number of entries in the layer_diffs curve
    (keys 0..n_layers-1). late = rel_depth >= 0.75.
  - Mistral-Large-675B schema differs: written sign in `wrong_sign` (errors
    only), curve in `layers` {'L<k>': {'logit_diff': ...}} over a SAMPLED
    grid (22 of 61 layers; peaks are over the sampled grid),
    n_layers = `n_layers_total` (61). Behavioral only, 5x5 task.

SOURCE EXCEPTION (recorded in the registry): Mistral-Small discovery det
corrects come from this repo's canonical copy; an ICML_paper copy of that
one domain is a divergent probe-pick variant (77/78 cases differ in
probe_tok) and is NOT used.

All paths in REGISTRY are repo-relative (from repo root). Run from repo root.

Outputs (next to this script, paper/appendix/):
  ledger_cases.csv       one row per case
  ledger_aggregates.csv  per model x phase x domain (+ pooled rows)
  ledger_manifest.csv    canonical path + md5 per source file

Self-check anchors (det): raises at the end if any mismatch (outputs are
still written first so mismatches can be investigated — never forced).
"""
import csv
import hashlib
import json
import os
import statistics

# Repo root = two levels up from this file (paper/appendix/master_ledger.py)
REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def _repo(rel):
    """Resolve a repo-relative path to an absolute path."""
    return os.path.join(REPO_ROOT, rel)


FILTER_LOGITS = 2.0
LATE_FRAC = 0.75  # prereg s03_derive_targets.py LATE_WINDOW_FRAC

# ── Registry: (model, phase, domain) -> {path, notes} ───────────────────────
# domain encodes task x class: det_error / det_correct / ibp_error /
# ibp_correct. Table 1 and Fig 1 are det-only; ibp rows are carried for
# later appendix work.
# All paths are repo-relative strings; _repo() converts them at load time.

_DOM_DIR = {
    "det_error":   "DET_error",
    "det_correct": "DET_correct_deepsign",
    "ibp_error":   "IBP_error",
    "ibp_correct": "IBP_correct_deepsign",
}
_DOM_FILE = {
    "det_error":   "det_4x4_error_expA_logit_lens.json",
    "det_correct": "det_4x4_correct_deepsign_expA_logit_lens.json",
    "ibp_error":   "ibp_error_expA_logit_lens.json",
    "ibp_correct": "ibp_correct_deepsign_expA_logit_lens.json",
}

REGISTRY = {}

# Gemma-3-27B / Phi-4-14B / Mistral-Small-24B: discovery + heldout, all domains
for _short, _model in (("Gemma", "Gemma-3-27B"),
                       ("Phi", "Phi-4-14B"),
                       ("Mistral-Small-24B", "Mistral-Small-24B")):
    for _phase in ("discovery", "heldout"):
        for _dom, _dir in _DOM_DIR.items():
            _rel = (f"{_short}/{_phase}_{_dir}/s01_logit_lens/"
                    f"{_DOM_FILE[_dom]}")
            REGISTRY[(_model, _phase, _dom)] = {"path": _rel, "notes": ""}

# EXCEPTION — Mistral-Small discovery det corrects: canonical file is this
# repo's copy; an ICML_paper copy is a divergent probe-pick variant
# (77/78 cases differ in probe_tok) and must not be used.
REGISTRY[("Mistral-Small-24B", "discovery", "det_correct")] = {
    "path": ("Mistral-Small-24B/discovery_DET_correct_deepsign/"
             "s01_logit_lens/det_4x4_correct_deepsign_expA_logit_lens.json"),
    "notes": ("canonical release-repo copy; an ICML_paper copy at results/"
              "Mistral/det_4x4_correct_deepsign/v2_mean_ablation is a "
              "divergent probe-pick variant — do not use"),
}

# Llama-3.3-70B and Qwen-2.5-72B: own layout (repo paths)
_LQ = {
    ("Llama-3.3-70B", "discovery", "det_error"):
        "Llama/discovery_4x4_DET/s01_logit_lens/llama_error_logit_lens.json",
    ("Llama-3.3-70B", "discovery", "det_correct"):
        "Llama/discovery_4x4_DET/s01_logit_lens/llama_correct_logit_lens.json",
    ("Llama-3.3-70B", "heldout", "det_error"):
        "Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json",
    ("Llama-3.3-70B", "heldout", "det_correct"):
        "Llama/heldout_4x4_DET/s01_logit_lens/det_4x4_correct_expA_logit_lens.json",
    ("Qwen-2.5-72B", "discovery", "det_error"):
        "Qwen/discovery_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json",
    ("Qwen-2.5-72B", "discovery", "det_correct"):
        "Qwen/discovery_4x4_DET/s01_logit_lens/det_4x4_correct_expA_logit_lens.json",
    ("Qwen-2.5-72B", "heldout", "det_error"):
        "Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_error_expA_logit_lens.json",
    ("Qwen-2.5-72B", "heldout", "det_correct"):
        "Qwen/heldout_4x4_DET/s01_logit_lens/det_4x4_correct_expA_logit_lens.json",
}
for _m in ("Llama-3.3-70B", "Qwen-2.5-72B"):
    _short = _m.split("-")[0]
    for _phase, _pdir in (("discovery", "discovery_IBP"),
                          ("heldout", "heldout_IBP")):
        for _cls in ("error", "correct"):
            _LQ[(_m, _phase, f"ibp_{_cls}")] = (
                f"{_short}/{_pdir}/s01_logit_lens/"
                f"ibp_{_cls}_expA_logit_lens.json")
for _k, _p in _LQ.items():
    REGISTRY[_k] = {"path": _p, "notes": ""}

# Mistral-Large-675B: behavioral only, det_error, sampled grid
REGISTRY[("Mistral-Large-675B", "single", "det_error")] = {
    "path": "Mistral-Large-675B/determinant/expA_logit_lens.json",
    "notes": ("behavioral only, 5x5 determinant task, errors only; "
              "22-of-61 sampled layers — peaks are over the sampled grid; "
              "written sign stored in `wrong_sign`"),
}


# ── Loader (verified semantics baked in) ────────────────────────────────────
def load_cases(rel_path, warnings):
    """Yield per-case dicts with the paper-wide computed quantities."""
    path = _repo(rel_path)
    with open(path) as fh:
        data = json.load(fh)
    out = []
    for cid, c in data.items():
        if "layer_diffs" in c:                       # standard pipeline schema
            ld = {int(k): float(v) for k, v in c["layer_diffs"].items()}
            n_layers = max(ld) + 1
            final_lead = ld[max(ld)]
            peak = max(sorted(ld), key=lambda L: ld[L])   # signed argmax
            stored = c.get("peak_layer")
            if stored is not None and int(stored) != peak:
                warnings.append(f"peak mismatch {rel_path}:{cid} "
                                f"recomputed={peak} stored={stored}")
            ws = c["written_sign"].strip()
        else:                                        # Mistral-Large-675B schema
            ld = {int(k[1:]): float(v["logit_diff"])
                  for k, v in c["layers"].items()}
            n_layers = int(c["n_layers_total"])
            final_lead = ld[max(ld)]
            peak = max(sorted(ld), key=lambda L: ld[L])
            ws = c["wrong_sign"].strip()
        rel_depth = peak / (n_layers - 1)
        out.append({
            "case_id": cid,
            "written_sign": ws,
            "final_lead": final_lead,
            # confirmed: final_lead >= +2 (written sign leads at final layer)
            "passes_filter": final_lead >= FILTER_LOGITS,
            "peak_layer": peak,
            "n_layers": n_layers,
            "rel_depth": rel_depth,
            "late": rel_depth >= LATE_FRAC,
        })
    return out


def aggregate(cases):
    filt = [c for c in cases if c["passes_filter"]]
    med = (statistics.median(c["rel_depth"] for c in filt) if filt else None)
    return {
        "n": len(cases),
        "n_ge2": len(filt),
        "n_excluded": len(cases) - len(filt),  # excluded: weak OR reversed final lead
        "wrote_plus": sum(c["written_sign"] == "+" for c in cases),
        "wrote_minus": sum(c["written_sign"] == "-" for c in cases),
        "n_late_unfilt": sum(c["late"] for c in cases),
        "n_late_filt": sum(c["late"] for c in filt),
        "median_depth_filt": med,
    }


# ── Self-check anchors (det; audited numbers — investigate, never force) ────
ANCHORS_LATE_UNFILT = {  # det_error: (model, phase) -> (n_late_unfilt, n)
    ("Gemma-3-27B", "discovery"): (60, 92),
    ("Gemma-3-27B", "heldout"): (57, 126),
    ("Mistral-Small-24B", "discovery"): (49, 95),
    ("Mistral-Small-24B", "heldout"): (74, 142),
    ("Phi-4-14B", "discovery"): (53, 61),
    ("Phi-4-14B", "heldout"): (142, 150),
    ("Llama-3.3-70B", "discovery"): (13, 16),
    ("Llama-3.3-70B", "heldout"): (152, 192),
    ("Qwen-2.5-72B", "discovery"): (43, 59),
    ("Qwen-2.5-72B", "heldout"): (90, 147),
}
ANCHORS_LATE_FILT_POOLED_ERR = {  # det_error pooled: (n_late_filt, n_ge2)
    # updated for final_lead >= +2 filter (confirmed: written sign leads)
    "Gemma-3-27B": (83, 116),
    "Mistral-Small-24B": (97, 102),
    "Phi-4-14B": (192, 198),
}
ANCHOR_GEMMA_CORR_FILT_POOLED = (60, 169)  # det_correct pooled late filt
ANCHOR_PHI_HELD_WROTE_SPLIT = (36, 263)    # det err+corr heldout: wrote+, wrote-


def run_self_checks(agg):
    errs = []

    def chk(label, got, exp):
        status = "PASS" if got == exp else "FAIL"
        line = f"[{status}] {label}: got {got} expected {exp}"
        print(line)
        if got != exp:
            errs.append(line)

    for (m, p), (nl, n) in ANCHORS_LATE_UNFILT.items():
        a = agg[(m, p, "det_error")]
        chk(f"det_error late-unfilt {m} {p}",
            (a["n_late_unfilt"], a["n"]), (nl, n))
    for m, (nl, n2) in ANCHORS_LATE_FILT_POOLED_ERR.items():
        a = agg[(m, "pooled", "det_error")]
        chk(f"det_error late-filt pooled {m}",
            (a["n_late_filt"], a["n_ge2"]), (nl, n2))
    a = agg[("Gemma-3-27B", "pooled", "det_correct")]
    chk("det_correct late-filt pooled Gemma-3-27B",
        (a["n_late_filt"], a["n_ge2"]), ANCHOR_GEMMA_CORR_FILT_POOLED)
    e = agg[("Phi-4-14B", "heldout", "det_error")]
    c = agg[("Phi-4-14B", "heldout", "det_correct")]
    chk("Phi-4-14B held det wrote+/wrote- (err+corr)",
        (e["wrote_plus"] + c["wrote_plus"],
         e["wrote_minus"] + c["wrote_minus"]),
        ANCHOR_PHI_HELD_WROTE_SPLIT)
    return errs


def main():
    warnings = []
    all_cases = {}     # (model, phase, domain) -> list of case dicts
    manifest = []
    for (model, phase, domain), entry in REGISTRY.items():
        rel_path = entry["path"]
        cases = load_cases(rel_path, warnings)
        all_cases[(model, phase, domain)] = cases
        abs_path = _repo(rel_path)
        md5 = hashlib.md5(open(abs_path, "rb").read()).hexdigest()
        manifest.append([model, phase, domain, rel_path, md5, len(cases),
                         entry["notes"]])

    # ledger_cases.csv
    cases_path = os.path.join(OUT_DIR, "ledger_cases.csv")
    with open(cases_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "phase", "domain", "case_id", "written_sign",
                    "final_lead", "passes_filter", "peak_layer", "n_layers",
                    "rel_depth", "late"])
        for (model, phase, domain), cases in all_cases.items():
            for c in cases:
                w.writerow([model, phase, domain, c["case_id"],
                            c["written_sign"], f"{c['final_lead']:.4f}",
                            int(c["passes_filter"]), c["peak_layer"],
                            c["n_layers"], f"{c['rel_depth']:.6f}",
                            int(c["late"])])
    print(f"wrote {cases_path}")

    # aggregates (+ pooled)
    agg = {}
    for key, cases in all_cases.items():
        agg[key] = aggregate(cases)
    models_phases = {}
    for (model, phase, domain) in all_cases:
        models_phases.setdefault(model, set()).add(phase)
    for model, phases in models_phases.items():
        if {"discovery", "heldout"} <= phases:
            doms = {d for (m, p, d) in all_cases if m == model}
            for d in doms:
                pooled = (all_cases[(model, "discovery", d)] +
                          all_cases[(model, "heldout", d)])
                agg[(model, "pooled", d)] = aggregate(pooled)
                all_cases[(model, "pooled", d)] = pooled  # for checks only

    agg_path = os.path.join(OUT_DIR, "ledger_aggregates.csv")
    dom_order = {"det_error": 0, "det_correct": 1,
                 "ibp_error": 2, "ibp_correct": 3}
    ph_order = {"discovery": 0, "heldout": 1, "pooled": 2, "single": 3}
    model_order = {m: i for i, m in enumerate(
        ["Gemma-3-27B", "Mistral-Small-24B", "Phi-4-14B", "Llama-3.3-70B",
         "Qwen-2.5-72B", "Mistral-Large-675B"])}
    with open(agg_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "phase", "domain", "n", "n_ge2", "n_excluded",
                    "wrote_plus", "wrote_minus", "n_late_unfilt",
                    "n_late_filt", "median_depth_filt"])
        for (model, phase, domain) in sorted(
                agg, key=lambda k: (model_order.get(k[0], 99),
                                    dom_order[k[2]], ph_order[k[1]])):
            a = agg[(model, phase, domain)]
            med = "" if a["median_depth_filt"] is None else \
                f"{a['median_depth_filt']:.6f}"
            w.writerow([model, phase, domain, a["n"], a["n_ge2"],
                        a["n_excluded"], a["wrote_plus"], a["wrote_minus"],
                        a["n_late_unfilt"], a["n_late_filt"], med])
    print(f"wrote {agg_path}")

    # manifest
    man_path = os.path.join(OUT_DIR, "ledger_manifest.csv")
    with open(man_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "phase", "domain", "path", "md5", "n_cases",
                    "notes"])
        for row in manifest:
            w.writerow(row)
    print(f"wrote {man_path}")

    for wmsg in warnings:
        print(f"WARNING: {wmsg}")
    if not warnings:
        print("no stored-vs-recomputed peak_layer mismatches")

    errs = run_self_checks(agg)
    if errs:
        raise SystemExit("ANCHOR SELF-CHECK FAILED — investigate before "
                         "using the ledger:\n" + "\n".join(errs))
    print("all anchor self-checks passed")


if __name__ == "__main__":
    main()
