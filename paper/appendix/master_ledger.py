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
REPO_ROOT = os.environ.get("LEDGER_REPO_ROOT") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT_DIR = os.environ.get("LEDGER_OUT_DIR") or os.path.dirname(os.path.abspath(__file__))


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


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — ALL-STAGES LEDGER (added after the held-out data commit made the
# repo self-contained). Same philosophy as Part 1: explicit classification
# tables (no fuzzy path guessing), every number recomputed from raw JSON,
# md5 per source file, hard self-checks, and a completeness guarantee:
# EVERY git-tracked file in the repository (all extensions, not just .json)
# appears in ledger_manifest_full.csv — result JSONs with extracted metrics,
# everything else with an explicit category. The manifest path list is
# asserted EQUAL to `git ls-files` output; any tracked file missing from the
# manifest (or vice versa) is a hard failure. Untracked disk files are
# reported informationally.
#
# Outputs (in addition to Part 1's three CSVs):
#   ledger_results.csv        one row per (source file, metric)
#   ledger_manifest_full.csv  one row per git-tracked file in the repo
#
# Audited anchors: five DLA cells independently recomputed from raw JSONs
# during the 2026-09 ledger audit (tolerance checks, pooled across phases).
# ═══════════════════════════════════════════════════════════════════════════

# Named layers per model for detailed DLA reporting (from the paper).
NAMED_LAYERS = {
    "Gemma-3-27B":        [58, 60],
    "Qwen-2.5-72B":       [75],
    "Llama-3.3-70B":      [77, 78, 79],
    "Phi-4-14B":          [37, 39],
    "Mistral-Small-24B":  [37, 38, 39],
    "Mistral-Large-675B": [],
}

# ── Strict classification tables (exact names only; unknown → recorded) ─────
MODEL_DIRS = {
    "Gemma": "Gemma-3-27B", "Phi": "Phi-4-14B",
    "Mistral-Small-24B": "Mistral-Small-24B", "Llama": "Llama-3.3-70B",
    "Qwen": "Qwen-2.5-72B", "Mistral-Large-675B": "Mistral-Large-675B",
}
# second path component -> (phase, task, class or None=from filename)
COHORT_DIRS = {}
for _ph in ("discovery", "heldout"):
    for _tk, _tdir in (("det", "DET"), ("ibp", "IBP")):
        COHORT_DIRS[f"{_ph}_{_tdir}_error"] = (_ph, _tk, "error")
        COHORT_DIRS[f"{_ph}_{_tdir}_correct_deepsign"] = (_ph, _tk, "correct")
    COHORT_DIRS[f"{_ph}_4x4_DET"] = (_ph, "det", None)
    COHORT_DIRS[f"{_ph}_IBP"] = (_ph, "ibp", None)
COHORT_DIRS["arith_control"] = ("control", "arith", None)
COHORT_DIRS["base_origin"] = ("exploratory", "det", None)
COHORT_DIRS["determinant"] = ("single", "det", "error")   # Mistral-Large-675B

NON_RESULT_CATEGORIES = (
    # (path predicate name, category) — manifest-only, no metrics expected
    ("raw_data",        "raw_data"),
    ("preregistration", "preregistration"),
    ("predeclarations", "preregistration"),
    ("pipeline_release", "pipeline_config"),
    ("paper/",          "paper_asset"),
)


def _class_from_filename(fname):
    f = fname.lower()
    if "_error" in f or f.startswith("llama_error") or f.startswith("ibp_error"):
        return "error"
    if "_correct" in f or f.startswith("llama_correct"):
        return "correct"
    return "n/a"


def classify(rel_path):
    """(category, model, phase, task, cls, stage) from exact tables."""
    parts = rel_path.split("/")
    for pred, cat in NON_RESULT_CATEGORIES:
        if rel_path.startswith(pred) or f"/{pred}" in rel_path:
            return (cat, "n/a", "n/a", "n/a", "n/a", "n/a")
    if parts[0] not in MODEL_DIRS:
        return ("UNCLASSIFIED", "n/a", "n/a", "n/a", "n/a", "n/a")
    model = MODEL_DIRS[parts[0]]
    if len(parts) < 2 or parts[1] not in COHORT_DIRS:
        if "targets" in parts[-1]:      # model-root frozen targets file
            return ("config_targets", model, "n/a", "n/a", "n/a", "root")
        return ("UNCLASSIFIED", model, "n/a", "n/a", "n/a", "n/a")
    phase, task, cls = COHORT_DIRS[parts[1]]
    if cls is None:
        cls = _class_from_filename(parts[-1])
    stage = next((p for p in parts if p.startswith("s0")), "root")
    fname = parts[-1]
    if stage == "root":
        if "targets" in fname:
            return ("config_targets", model, phase, task, cls, stage)
        if "sites" in fname or "groups" in fname:
            return ("config_sites", model, phase, task, cls, stage)
    return ("results", model, phase, task, cls, stage)


# Root-level repository metadata files (exact names).
REPO_META_FILES = {
    "README.md", "LICENSE", "requirements.txt", "CHECKSUMS.sha256",
    ".gitignore",
}


def classify_nonjson(rel_path):
    """Category for every git-tracked non-.json file (exact rules only)."""
    parts = rel_path.split("/")
    fname = parts[-1]
    if rel_path.startswith("paper/appendix/ledger_") and \
            rel_path.endswith(".csv"):
        return ("ledger_output", "n/a", "n/a", "n/a", "n/a", "n/a")
    if rel_path.startswith("paper/") and rel_path.endswith(".py"):
        return ("analysis_script", "n/a", "n/a", "n/a", "n/a", "n/a")
    for pred, cat in NON_RESULT_CATEGORIES:
        if rel_path.startswith(pred) or f"/{pred}" in rel_path:
            return (cat, "n/a", "n/a", "n/a", "n/a", "n/a")
    if "/" not in rel_path and fname in REPO_META_FILES:
        return ("repo_meta", "n/a", "n/a", "n/a", "n/a", "n/a")
    if parts[0] in MODEL_DIRS:
        model = MODEL_DIRS[parts[0]]
        phase, task, cls = COHORT_DIRS.get(
            parts[1], ("n/a", "n/a", None)) if len(parts) > 1 else (
            "n/a", "n/a", None)
        return ("input_data", model, phase, task, cls or "n/a", "root")
    return ("UNCLASSIFIED", "n/a", "n/a", "n/a", "n/a", "n/a")


def git_tracked_files():
    """`git ls-files` from REPO_ROOT, or None if git/.git unavailable."""
    if not os.path.isdir(os.path.join(REPO_ROOT, ".git")):
        return None
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", REPO_ROOT, "ls-files"],
            capture_output=True, text=True, check=True)
        return sorted(l for l in out.stdout.splitlines() if l.strip())
    except Exception:
        return None


# ── Metric helpers ──────────────────────────────────────────────────────────
def _r6(x):
    return round(float(x), 6)


def _mean_metric(name, vals, note=""):
    return (name, _r6(statistics.mean(vals)), len(vals), note) if vals else None


FLAG_KEYS = ("flipped", "broken", "fixed", "top1_now_correct", "edit_correct")


# ── Extractors (schema-fingerprint dispatched; see detect_kind) ─────────────
def x_lens_standard(data, model):
    """expA logit lens, standard schema — V2-compatible metric names."""
    cases = []
    for cid, c in data.items():
        ld = {int(k): float(v) for k, v in c["layer_diffs"].items()}
        n_layers = max(ld) + 1
        final_lead = ld[max(ld)]
        peak = max(sorted(ld), key=lambda L: ld[L])
        cases.append({
            "ws": c["written_sign"].strip(), "final_lead": final_lead,
            "conf": final_lead >= FILTER_LOGITS,
            "rel_depth": peak / (n_layers - 1),
        })
    return _lens_metrics(cases)


def x_lens_675(data, model):
    cases = []
    for cid, c in data.items():
        ld = {int(k[1:]): float(v["logit_diff"]) for k, v in c["layers"].items()}
        n_layers = int(c["n_layers_total"])
        final_lead = ld[max(ld)]
        peak = max(sorted(ld), key=lambda L: ld[L])
        cases.append({
            "ws": c.get("wrong_sign", "?").strip(), "final_lead": final_lead,
            "conf": final_lead >= FILTER_LOGITS,
            "rel_depth": peak / (n_layers - 1),
        })
    return _lens_metrics(cases)


def _lens_metrics(cases):
    m = []
    n = len(cases)
    if n == 0:
        return m
    conf = [c for c in cases if c["conf"]]
    late = [c for c in cases if c["rel_depth"] >= LATE_FRAC]
    m.append(("n_cases_all", n, n, ""))
    m.append(("n_wrote_plus_all", sum(c["ws"] == "+" for c in cases), n, ""))
    m.append(("n_wrote_minus_all", sum(c["ws"] == "-" for c in cases), n, ""))
    m.append(("n_confirmed_all", len(conf), n, ""))
    m.append(("n_late_all", len(late), n, ""))
    m.append(("frac_late_all", _r6(len(late) / n), n, ""))
    m.append(("median_peak_depth_all",
              _r6(statistics.median(c["rel_depth"] for c in cases)), n, ""))
    if conf:
        m.append(("n_late_confirmed", sum(c["rel_depth"] >= LATE_FRAC for c in conf),
                  len(conf), ""))
        m.append(("frac_late_confirmed",
                  _r6(sum(c["rel_depth"] >= LATE_FRAC for c in conf) / len(conf)),
                  len(conf), ""))
        m.append(("median_peak_depth_confirmed",
                  _r6(statistics.median(c["rel_depth"] for c in conf)),
                  len(conf), ""))
    for tag, sel in (("wrote_plus", "+"), ("wrote_minus", "-")):
        vs = [c["final_lead"] for c in cases if c["ws"] == sel]
        mm = _mean_metric(f"mean_final_lead_{tag}_all", vs)
        if mm:
            m.append(mm)
    return m


def x_dla_standard(data, model):
    """expB / matched DLA — per named layer, split by written sign,
    _all and _confirmed (true_logit_diff >= 2). V2-compatible names."""
    m = []
    named = NAMED_LAYERS.get(model, [])
    per_layer_mlp, per_layer_attn = {}, {}
    triples = []          # (ws, conf, mlp_dict, attn_dict, emb)
    for cid, c in data.items():
        ws = c.get("written_sign", "?")
        ws = ws.strip() if isinstance(ws, str) else "?"
        tld = c.get("true_logit_diff")
        conf = tld is not None and float(tld) >= FILTER_LOGITS
        mlp = {int(k): float(v) for k, v in c.get("mlp_dla", {}).items()}
        attn = {int(k): float(v) for k, v in c.get("attn_dla", {}).items()}
        triples.append((ws, conf, mlp, attn, c.get("embedding_dla")))
        for L, v in mlp.items():
            per_layer_mlp.setdefault(L, []).append(v)
        for L, v in attn.items():
            per_layer_attn.setdefault(L, []).append(v)
    n = len(triples)
    m.append(("n_cases_all", n, n, ""))
    m.append(("n_confirmed_all", sum(t[1] for t in triples), n, ""))
    embs = [(float(e), ws) for ws, cf, mp, at, e in triples if e is not None]
    mm = _mean_metric("mean_embedding_dla_all", [v for v, w in embs])
    if mm:
        m.append(mm)
    for tag, sel in (("wrote_plus", "+"), ("wrote_minus", "-")):
        mm = _mean_metric(f"mean_embedding_dla_{tag}_all",
                          [v for v, w in embs if w == sel])
        if mm:
            m.append(mm)
    for L in named:
        for comp, idx in (("mlp", 2), ("attn", 3)):
            sub = [(t[idx].get(L), t[0], t[1]) for t in triples
                   if t[idx].get(L) is not None]
            if not sub:
                m.append((f"mean_{comp}_dla_L{L}_all", None, 0, "NO_DATA"))
                continue
            for name, vals in (
                (f"mean_{comp}_dla_L{L}_all", [v for v, w, cf in sub]),
                (f"mean_{comp}_dla_L{L}_wrote_plus_all",
                 [v for v, w, cf in sub if w == "+"]),
                (f"mean_{comp}_dla_L{L}_wrote_minus_all",
                 [v for v, w, cf in sub if w == "-"]),
                (f"mean_{comp}_dla_L{L}_confirmed",
                 [v for v, w, cf in sub if cf]),
                (f"mean_{comp}_dla_L{L}_wrote_plus_confirmed",
                 [v for v, w, cf in sub if cf and w == "+"]),
                (f"mean_{comp}_dla_L{L}_wrote_minus_confirmed",
                 [v for v, w, cf in sub if cf and w == "-"]),
            ):
                mm = _mean_metric(name, vals)
                if mm:
                    m.append(mm)
        tot = [(t[2][L] + t[3][L], t[0]) for t in triples
               if L in t[2] and L in t[3]]
        for name, vals in (
            (f"mean_total_dla_L{L}_all", [v for v, w in tot]),
            (f"mean_total_dla_L{L}_wrote_plus_all",
             [v for v, w in tot if w == "+"]),
            (f"mean_total_dla_L{L}_wrote_minus_all",
             [v for v, w in tot if w == "-"]),
        ):
            mm = _mean_metric(name, vals)
            if mm:
                m.append(mm)
    for L in sorted(per_layer_mlp):
        if L not in named:
            m.append((f"mean_mlp_dla_L{L}_all", _r6(statistics.mean(
                per_layer_mlp[L])), len(per_layer_mlp[L]), "non_named"))
    for L in sorted(per_layer_attn):
        if L not in named:
            m.append((f"mean_attn_dla_L{L}_all", _r6(statistics.mean(
                per_layer_attn[L])), len(per_layer_attn[L]), "non_named"))
    return m


def x_dla_675(data, model):
    """Mistral-Large-675B expB: per-case mlp/attn dicts, no sign fields."""
    per_mlp, per_attn = {}, {}
    n = 0
    for cid, c in data.items():
        n += 1
        for key, store in (("mlp", per_mlp), ("attn", per_attn)):
            v = c.get(key)
            if isinstance(v, dict):
                for L, val in v.items():
                    try:
                        store.setdefault(int(str(L).lstrip("L")), []).append(
                            float(val))
                    except (ValueError, TypeError):
                        pass
    m = [("n_cases_all", n, n, "no sign fields in this schema")]
    for comp, store in (("mlp", per_mlp), ("attn", per_attn)):
        for L in sorted(store):
            m.append((f"mean_{comp}_dla_L{L}_all",
                      _r6(statistics.mean(store[L])), len(store[L]), ""))
    return m


def x_projections_case(data, model):
    """s04 per-case projections (proj_d_L* / norm_h_L* fields)."""
    fields = {}
    n = 0
    signs = {}
    for cid, c in data.items():
        n += 1
        ws = c.get("written_sign", "?")
        for k, v in c.items():
            if (k.startswith("proj_d_L") or k.startswith("norm_h_L")) and \
                    isinstance(v, (int, float)):
                fields.setdefault(k, []).append((float(v), ws))
    m = [("n_cases_all", n, n, "")]
    for k in sorted(fields):
        vs = fields[k]
        m.append((f"mean_{k}_all", _r6(statistics.mean(v for v, w in vs)),
                  len(vs), ""))
        for tag, sel in (("wrote_plus", "+"), ("wrote_minus", "-")):
            sub = [v for v, w in vs if w == sel]
            mm = _mean_metric(f"mean_{k}_{tag}_all", sub)
            if mm:
                m.append(mm)
    return m


def x_projections_meta(data, model):
    m = []
    data = data.get("meta", data)   # some files wrap the descriptor in `meta`
    if "n_entries" in data:
        m.append(("n_entries", int(data["n_entries"]), int(data["n_entries"]),
                  "aggregate descriptor file"))
    if "capture_layers" in data:
        m.append(("capture_layers", None, len(data["capture_layers"]),
                  "layers: " + ",".join(map(str, data["capture_layers"]))))
    return m


def x_s05_ablations(data, model):
    """expD-style: per-case `ablations` dict keyed by site name."""
    deltas = {}
    n = 0
    for cid, c in data.items():
        n += 1
        for k, a in c.get("ablations", {}).items():
            if isinstance(a, dict) and "delta_ld" in a:
                deltas.setdefault(k, []).append(float(a["delta_ld"]))
    m = [("n_cases_all", n, n, "")]
    for k in sorted(deltas):
        m.append((f"mean_delta_ld[{k}]", _r6(statistics.mean(deltas[k])),
                  len(deltas[k]), ""))
    return m


def x_s05_joint(data, model):
    """expE-style: per-case target_delta with permutation null."""
    tds, beats = [], 0
    n = 0
    for cid, c in data.items():
        n += 1
        if c.get("target_delta") is not None:
            tds.append(float(c["target_delta"]))
        if c.get("beats_null_p5"):
            beats += 1
    m = [("n_cases_all", n, n, "")]
    mm = _mean_metric("mean_target_delta", tds)
    if mm:
        m.append(mm)
    m.append(("n_beats_null_p5", beats, n, ""))
    return m


def x_flat_delta(data, model):
    """Per-case flat `*_delta_ld` fields (habit_ablation, L78_ablation...)."""
    fields = {}
    n = 0
    for cid, c in data.items():
        n += 1
        for k, v in c.items():
            if k.endswith("_delta_ld") and isinstance(v, (int, float)):
                fields.setdefault(k, []).append(float(v))
    m = [("n_cases_all", n, n, "")]
    for k in sorted(fields):
        m.append((f"mean_{k}", _r6(statistics.mean(fields[k])),
                  len(fields[k]), ""))
    return m


def x_retest_counts(data, model):
    n = 0
    counts = {}
    for cid, c in data.items():
        n += 1
        for k in ("fixed_any", "strict_flip_any", "loose_flip_any"):
            if k in c:
                counts[k] = counts.get(k, 0) + int(bool(c[k]))
    m = [("n_cases_all", n, n, "")]
    for k in sorted(counts):
        m.append((f"n_{k}", counts[k], n, ""))
    return m


def x_percase_simple(data, model):
    """Per-case direct delta_ld (+ optional flip flag)."""
    deltas, flips = [], 0
    n = 0
    for cid, c in data.items():
        n += 1
        if c.get("delta_ld") is not None:
            deltas.append(float(c["delta_ld"]))
        if c.get("flipped"):
            flips += 1
    m = [("n_cases_all", n, n, "")]
    mm = _mean_metric("mean_delta_ld", deltas)
    if mm:
        m.append(mm)
    m.append(("n_flipped", flips, n, ""))
    return m


def x_s05b_sites(data, model):
    per_site = {}
    n = 0
    for cid, c in data.items():
        n += 1
        for s, sd in c.get("sites", {}).items():
            if isinstance(sd, dict) and "delta_ld" in sd:
                per_site.setdefault(s, []).append(float(sd["delta_ld"]))
    m = [("n_cases_all", n, n, "")]
    for s in sorted(per_site):
        m.append((f"mean_delta_ld[{s}]", _r6(statistics.mean(per_site[s])),
                  len(per_site[s]), ""))
    return m


def x_s05c_groups(data, model):
    per_g, flips, corr = {}, {}, {}
    n = 0
    for cid, c in data.items():
        n += 1
        for g, gd in c.get("groups", {}).items():
            if isinstance(gd, dict) and "delta_ld" in gd:
                per_g.setdefault(g, []).append(float(gd["delta_ld"]))
                flips[g] = flips.get(g, 0) + int(bool(gd.get("flipped")))
                corr[g] = corr.get(g, 0) + int(bool(gd.get("top1_now_correct")))
    m = [("n_cases_all", n, n, "")]
    for g in sorted(per_g):
        m.append((f"mean_delta_ld[{g}]", _r6(statistics.mean(per_g[g])),
                  len(per_g[g]), ""))
        m.append((f"n_flipped[{g}]", flips[g], len(per_g[g]), ""))
        m.append((f"n_top1_now_correct[{g}]", corr[g], len(per_g[g]), ""))
    return m


def x_s06_edits(data, model):
    per, flags = {}, {}
    rc = []
    n = 0
    for cid, c in data.items():
        n += 1
        if c.get("random_ctrl_delta_ld") is not None:
            rc.append(float(c["random_ctrl_delta_ld"]))
        for ek, ed in c.get("edits", {}).items():
            if not isinstance(ed, dict):
                continue
            if "delta_ld" in ed:                       # un-nested edit
                per.setdefault((ek,), []).append(float(ed["delta_ld"]))
                _count_flags(flags, (ek,), ed)
            else:                                      # alpha-nested
                for ak, leaf in ed.items():
                    if isinstance(leaf, dict) and "delta_ld" in leaf:
                        per.setdefault((ek, ak), []).append(
                            float(leaf["delta_ld"]))
                        _count_flags(flags, (ek, ak), leaf)
    m = [("n_cases_all", n, n, "")]
    mm = _mean_metric("mean_random_ctrl_delta_ld", rc)
    if mm:
        m.append(mm)
        m.append(("n_flipped[random_ctrl]", sum(1 for d in rc if d < 0),
                  len(rc), "delta<0 count, informational"))
    _emit_keyed(m, per, flags)
    return m


def _count_flags(flags, key, leaf):
    for fk in FLAG_KEYS:
        if fk in leaf:
            flags.setdefault((key, fk), 0)
            flags[(key, fk)] += int(bool(leaf[fk]))


def _emit_keyed(m, per, flags):
    for key in sorted(per):
        label = "|".join(key)
        m.append((f"mean_delta_ld[{label}]",
                  _r6(statistics.mean(per[key])), len(per[key]), ""))
        for fk in FLAG_KEYS:
            if (key, fk) in flags:
                m.append((f"n_{fk}[{label}]", flags[(key, fk)],
                          len(per[key]), ""))


def x_s07_patches(data, model):
    per, flags = {}, {}
    n = 0
    for cid, c in data.items():
        n += 1
        for pk, pd in c.get("patches", {}).items():
            if isinstance(pd, dict) and "delta_ld" in pd:
                per.setdefault((pk,), []).append(float(pd["delta_ld"]))
                _count_flags(flags, (pk,), pd)
    m = [("n_cases_all", n, n, "")]
    _emit_keyed(m, per, flags)
    return m


def x_meta_results(data, model):
    """s07 signmatched / s08 / s09: {meta, results}; results[case] holds a
    condition tree (conditions|boosts|patches) whose leaves carry delta_ld."""
    m = []
    meta = data.get("meta", {})
    if isinstance(meta, dict):
        if meta.get("n_questions") is not None:
            m.append(("n_questions_meta", int(meta["n_questions"]),
                      int(meta["n_questions"]), ""))
        if meta.get("d_dot_r") is not None:
            m.append(("d_dot_r", _r6(meta["d_dot_r"]), 0, ""))
        if meta.get("failure_observed") is not None:
            m.append(("failure_observed", int(bool(meta["failure_observed"])),
                      0, ""))
    results = data.get("results", {})
    per, flags = {}, {}
    base = []
    n = 0
    for cid, c in results.items():
        if not isinstance(c, dict):
            continue
        n += 1
        if c.get("baseline_ld") is not None:
            base.append(float(c["baseline_ld"]))
        for tree_key in ("conditions", "boosts", "patches"):
            for ck, cv in c.get(tree_key, {}).items():
                if not isinstance(cv, dict):
                    continue
                if "delta_ld" in cv:                   # leaf directly
                    per.setdefault((ck,), []).append(float(cv["delta_ld"]))
                    _count_flags(flags, (ck,), cv)
                else:                                  # alpha/gamma level
                    for sk, leaf in cv.items():
                        if isinstance(leaf, dict) and "delta_ld" in leaf:
                            per.setdefault((ck, sk), []).append(
                                float(leaf["delta_ld"]))
                            _count_flags(flags, (ck, sk), leaf)
    m.append(("n_cases_all", n, n, ""))
    mm = _mean_metric("mean_baseline_ld", base)
    if mm:
        m.append(mm)
    _emit_keyed(m, per, flags)
    return m


def x_scalar_report(data, model):
    m = []
    for k, v in data.items():
        if isinstance(v, (int, float)):
            m.append((k, v, 0, "report scalar"))
    return m


def x_generic(data, model):
    n = len(data) if isinstance(data, (dict, list)) else 0
    keys = ""
    if isinstance(data, dict) and data:
        v0 = next(iter(data.values()))
        if isinstance(v0, dict):
            keys = ",".join(sorted(v0.keys())[:8])
    return [("n_cases_all", n, n,
             f"enumerated only, no extractor (v0 keys: {keys})")]


# ── Fingerprint dispatch (exact key presence, not fuzzy matching) ───────────
GENERIC_EXPECTED = ("staircase_topk", "adaptive_alpha", "base_origin",
                    "generate_flipped")


def detect_kind(data, rel_path):
    if not isinstance(data, dict) or not data:
        return "generic"
    if "meta" in data and "results" in data:
        return "meta_results"
    _meta = data.get("meta", data)
    if isinstance(_meta, dict) and "capture_layers" in _meta \
            and "n_entries" in _meta:
        return "projections_meta"
    v0 = next(iter(data.values()))
    if not isinstance(v0, dict):
        if all(isinstance(v, (int, float)) for v in data.values()):
            return "scalar_report"
        return "generic"
    k = set(v0.keys())
    if "layer_diffs" in k:
        return "lens_standard"
    if "layers" in k and "n_layers_total" in k:
        return "lens_675"
    if "mlp_dla" in k and "attn_dla" in k:
        return "dla_standard"
    if "mlp" in k and "attn" in k and "heads" in k:
        return "dla_675"
    if "ablations" in k:
        return "s05_ablations"
    if "target_delta" in k:
        return "s05_joint"
    if "sites" in k and "baseline_ld" in k:
        return "s05b_sites"
    if "groups" in k and "baseline_ld" in k:
        return "s05c_groups"
    if "edits" in k:
        return "s06_edits"
    if "patches" in k and "baseline_ld" in k:
        return "s07_patches"
    if any(key.startswith("proj_d_L") for key in k):
        return "projections_case"
    if "fixed_any" in k:
        return "retest_counts"
    if "delta_ld" in k and "baseline_ld" in k:
        return "percase_simple"
    if any(key.endswith("_delta_ld") for key in k):
        return "flat_delta"
    return "generic"


EXTRACTORS = {
    "lens_standard": x_lens_standard, "lens_675": x_lens_675,
    "dla_standard": x_dla_standard, "dla_675": x_dla_675,
    "projections_case": x_projections_case,
    "projections_meta": x_projections_meta,
    "s05_ablations": x_s05_ablations, "s05_joint": x_s05_joint,
    "s05b_sites": x_s05b_sites, "s05c_groups": x_s05c_groups,
    "s06_edits": x_s06_edits, "s07_patches": x_s07_patches,
    "meta_results": x_meta_results, "scalar_report": x_scalar_report,
    "retest_counts": x_retest_counts, "percase_simple": x_percase_simple,
    "flat_delta": x_flat_delta, "generic": x_generic,
}

# ── Audited anchors (2026-09 ledger audit; recomputed from raw JSONs) ───────
# Pooled across phases, weighted by n — tolerance checks as in the audit.
AUDITED_DLA_ANCHORS = [
    # (label, model, task, class, metric, expected, expected_n, tol)
    ("Gemma L58 pooled mlp wrote+ det error", "Gemma-3-27B", "det", "error",
     "mean_mlp_dla_L58_wrote_plus_all", -0.98, 131, 0.15),
    ("Qwen L75 pooled mlp wrote+ det error", "Qwen-2.5-72B", "det", "error",
     "mean_mlp_dla_L75_wrote_plus_all", -0.72, 104, 0.15),
    ("Phi L39 pooled mlp wrote+ det error", "Phi-4-14B", "det", "error",
     "mean_mlp_dla_L39_wrote_plus_all", 1.56, 30, 0.15),
    ("Llama L79 pooled mlp wrote+ IBP error", "Llama-3.3-70B", "ibp", "error",
     "mean_mlp_dla_L79_wrote_plus_all", 5.66, 13, 0.5),
    ("Mistral L38 pooled mlp wrote+ IBP error", "Mistral-Small-24B", "ibp",
     "error", "mean_mlp_dla_L38_wrote_plus_all", 0.006, 11, 0.15),
]


def run_stage2_anchors(result_rows):
    lookup = {}
    for r in result_rows:
        key = (r["model"], r["task"], r["class"], r["metric"])
        # audited anchors were computed on expB DLA only (matched_dla files
        # repeat the same cases and would double-count)
        if r["value"] is not None and r["phase"] in ("discovery", "heldout") \
                and "matched" not in r["experiment"]:
            lookup.setdefault(key, []).append((float(r["value"]), int(r["n"])))
    errs = []
    for label, model, task, cls, metric, exp, exp_n, tol in \
            AUDITED_DLA_ANCHORS:
        vals = lookup.get((model, task, cls, metric), [])
        tot_n = sum(n for v, n in vals)
        if not vals or tot_n == 0:
            errs.append(f"[FAIL] {label}: metric missing")
            print(errs[-1])
            continue
        pooled = sum(v * n for v, n in vals) / tot_n
        ok = abs(pooled - exp) <= tol and abs(tot_n - exp_n) <= max(
            2, exp_n * 0.1)
        line = (f"[{'PASS' if ok else 'FAIL'}] {label}: got {pooled:.4f} "
                f"(n={tot_n}) expected ~{exp} (n~{exp_n}, tol {tol})")
        print(line)
        if not ok:
            errs.append(line)
    return errs


# ── Stage-2 main ────────────────────────────────────────────────────────────
def stage2_main():
    print("\n── PART 2: all-stages ledger ──")
    disk_files = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for f in sorted(filenames):
            if f == ".DS_Store":
                continue
            disk_files.append(os.path.relpath(
                os.path.join(dirpath, f), REPO_ROOT).replace(os.sep, "/"))
    disk_files.sort()

    tracked = git_tracked_files()
    if tracked is not None:
        missing_on_disk = sorted(set(tracked) - set(disk_files))
        if missing_on_disk:
            raise SystemExit(
                "git-tracked files MISSING on disk:\n"
                + "\n".join(missing_on_disk))
        untracked = sorted(set(disk_files) - set(tracked))
        file_list = tracked
        print(f"{len(tracked)} git-tracked files (source of truth: "
              f"`git ls-files`); {len(untracked)} untracked disk files "
              f"(informational, not in manifest)")
        for u in untracked:
            print(f"  [untracked] {u}")
    else:
        file_list = disk_files
        print(f"WARNING: no .git / git unavailable — falling back to disk "
              f"walk ({len(file_list)} files); git completeness check "
              f"SKIPPED")

    manifest, results = [], []
    generic_files, unclassified = [], []
    for rel in file_list:
        is_json = rel.endswith(".json")
        cat, model, phase, task, cls, stage = (
            classify(rel) if is_json else classify_nonjson(rel))
        p = _repo(rel)
        n_cases, n_metrics, note, kind = "", 0, "", ""
        if cat == "ledger_output":
            md5, size = "", ""
            note = ("output of this script (self-referential; "
                    "md5/size not fixed here)")
        elif rel == "CHECKSUMS.sha256":
            md5, size = "", ""
            note = "release checksum file; updated after ledger generation"
        else:
            md5 = hashlib.md5(open(p, "rb").read()).hexdigest()
            size = os.path.getsize(p)
        if cat == "UNCLASSIFIED":
            unclassified.append(rel)
            note = "UNCLASSIFIED — investigate"
        elif cat == "results":
            try:
                data = json.load(open(p))
            except Exception as e:
                raise SystemExit(f"PARSE ERROR {rel}: {e}")
            kind = detect_kind(data, rel)
            if kind == "generic" and not any(
                    t in rel for t in GENERIC_EXPECTED) and \
                    not rel.endswith("dry_run_report.json"):
                note = "UNEXPECTED generic fallback"
                generic_files.append(rel)
            n_cases = len(data) if isinstance(data, (dict, list)) else ""
            metrics = EXTRACTORS[kind](data, model)
            n_metrics = len(metrics)
            exp = os.path.splitext(os.path.basename(rel))[0]
            for name, value, n, mnote in metrics:
                results.append({
                    "model": model, "phase": phase, "task": task,
                    "class": cls, "stage": stage, "experiment": exp,
                    "metric": name, "value": value, "n": n,
                    "source_path": rel, "source_md5": md5, "notes": mnote,
                })
        manifest.append([rel, md5, size, cat, kind, model, phase, task, cls,
                         stage, n_cases, n_metrics, note])

    res_path = os.path.join(OUT_DIR, "ledger_results.csv")
    with open(res_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "model", "phase", "task", "class", "stage", "experiment",
            "metric", "value", "n", "source_path", "source_md5", "notes"])
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"wrote {res_path} ({len(results)} metric rows)")

    man_path = os.path.join(OUT_DIR, "ledger_manifest_full.csv")
    with open(man_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "md5", "size", "category", "schema_kind", "model",
                    "phase", "task", "class", "stage", "n_cases", "n_metrics",
                    "note"])
        for row in manifest:
            w.writerow(row)
    print(f"wrote {man_path} ({len(manifest)} files, "
          f"{sum(1 for r in manifest if r[3] == 'results')} result files)")
    cat_counts = {}
    for r in manifest:
        cat_counts[r[3]] = cat_counts.get(r[3], 0) + 1
    for c in sorted(cat_counts):
        print(f"  {c}: {cat_counts[c]}")

    errs = []
    if tracked is not None:
        man_paths = [r[0] for r in manifest]
        if man_paths != tracked:
            d1 = sorted(set(tracked) - set(man_paths))
            d2 = sorted(set(man_paths) - set(tracked))
            errs.append(f"MANIFEST != git ls-files — tracked-not-in-manifest:"
                        f" {d1[:5]}; manifest-not-tracked: {d2[:5]}")
        else:
            print(f"COMPLETENESS: manifest == git ls-files "
                  f"({len(tracked)} files, exact match)")
    if unclassified:
        errs.append(f"{len(unclassified)} UNCLASSIFIED files: "
                    + "; ".join(unclassified[:10]))
    if generic_files:
        errs.append(f"{len(generic_files)} unexpected generic fallbacks: "
                    + "; ".join(generic_files[:10]))
    errs += run_stage2_anchors(results)
    if errs:
        raise SystemExit("PART 2 SELF-CHECK FAILED — investigate:\n"
                         + "\n".join(errs))
    print("PART 2: completeness + audited DLA anchors all passed")
    return results


if __name__ == "__main__":
    main()          # Part 1: expA logit-lens case ledger + anchors
    stage2_main()   # Part 2: all-stages ledger + completeness + DLA anchors
