#!/usr/bin/env python3
"""Appendix G figures: five-model steering specificity, POOLED = discovery +
held-out (same task, same cohort type). The two tasks stay separate and are
STACKED: 4x4 determinant panel on top, integration by parts below.

Pooling definition. For each model, task, and cohort type, the pooled count
is the sum of the discovery-phase and held-out-phase counts for the identical
cohort, and the pooled mean is the case-weighted mean over the union of
cases. det and ibp are never mixed. Pooling across the phase split is sound
here: the sign direction and the habit layers were frozen on discovery data,
the held-out phase is the out-of-sample confirmation, and both phases run
the identical C2 protocol on the identical cohort definitions; pooling
simply gives the per-task estimates more cases.

Terminology and symbols follow the main working draft (v2): the *sign lead*
is the written sign's logit minus the alternative's; C2 (minus-removal
steering) subtracts the scaled sign direction at the frozen habit-layer
sites (Gemma L58+L60; Mistral L38+L39; Phi L37+L39; Llama L77+L79 det /
L77+L78 ibp; Qwen L75+L78, MLP outputs); alpha is the dose; CTRL_MAG is the
magnitude-matched random control.

Cohorts and conventions:
  - error files: written_sign is the sign the model wrote (the wrong one);
    minus-written errors have written_sign == "-", plus-written == "+".
  - correct files: the runs use the deepsign role-matched inputs, whose
    wrong_sign_deep column holds the sign actually present in the text at
    the matched site; the steering field written_sign equals it (verified
    per-case). correct-minus answers are written_sign == "-".
  - "flipped" on errors / "broken" on corrects: strict zero-crossing of the
    sign lead (baseline lead > 0 and post-edit lead < 0).

Coverage (verified against the experiment-ready funnels case-by-case):
  - The steering runs cover exactly the LATE-CIRCUIT cases (logit-lens peak
    layer > 5, the preregistered s08 filter). Every plus-written
    experiment-ready error is late-circuit, so plus-written coverage is
    complete in every cell; every case excluded by the filter is an
    early-peaking minus-written error (largest cell: Qwen det held-out,
    48 of 73 minus-written are early-peak, leaving 25).
  - Llama det discovery error steering was never run (skipped, not faked);
    Llama det error bars are held-out only.
  - Qwen ibp discovery has no correct-cohort run; Qwen ibp correct bars are
    held-out only. Qwen ibp has zero plus-written cases in both phases.

Outputs (no figure numbers or captions baked in; captions live in the doc):
  figG1_specificity.png    stacked specificity fingerprints (det top, ibp
                           bottom): per model at alpha=3, pooled fraction of
                           minus-written errors flipped, plus-written errors
                           flipped, correct-minus broken, correct-plus
                           broken, annotated k/n.
  figG2_dose_response.png  stacked dose-response (det top, ibp bottom):
                           pooled mean shift in the written sign's lead on
                           minus-written errors vs alpha, one line per
                           model, grey band = spread of CTRL_MAG means.

Every pooled count equals the sum of the matching per-phase rows in
paper/appendix/ledger_results.csv (stage == "s08_c2_steering"), and every
pooled mean equals the case-weighted average of the per-phase means; the
__main__ block prints the pooled numbers for that cross-check.

Usage: python3 fig_G_specificity.py [--repo REPO_ROOT] [--out OUT_DIR]
"""
import argparse, glob, json, os, statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ALPHAS = ["a1.0", "a2.0", "a3.0"]
MODELS = [  # (repo dir, display name per main-draft Table 1, color)
    ("Gemma",             "Gemma-3-27B",       "#4c78a8"),
    ("Qwen",              "Qwen-2.5-72B",      "#f58518"),
    ("Llama",             "Llama-3.3-70B",     "#54a24b"),
    ("Phi",               "Phi-4-14B",         "#b279a2"),
    ("Mistral-Small-24B", "Mistral-Small-24B", "#e45756"),
]
TASKS = [("det", "4×4 determinant"), ("ibp", "integration by parts")]
PATS = {"err": "*error*combined_ablation.json",
        "ctl": "*error*ctrl_mag.json",
        "cor": "*c2_on_correct.json"}


def find(repo, mdir, phase, task, kind):
    # task must be matched on the full path: Llama's det discovery correct
    # file has no "det" in its basename.
    fs = [f for f in glob.glob(os.path.join(repo, mdir, f"{phase}*",
                                            "s08_c2_steering", PATS[kind]))
          if (task == "det") == ("DET" in f.upper().replace("IBP", ""))
          and (task == "ibp") == ("IBP" in f.upper())]
    assert len(fs) <= 1, (mdir, phase, task, kind, fs)
    return json.load(open(fs[0]))["results"] if fs else None


def leaf(c, a):
    v = c["conditions"].get("C2", {})
    v = v.get(a) if isinstance(v, dict) else None
    return v if isinstance(v, dict) else None


def load(repo):
    """Pool discovery + held-out per (model, task); counts are sums,
    means are case-weighted."""
    out = {}
    for mdir, mname, _ in MODELS:
        for task, _t in TASKS:
            rec = {"n_minus": 0, "n_plus": 0, "phases_err": [],
                   "phases_cor": [], "cminus": [0, 0], "cplus": [0, 0]}
            for a in ALPHAS:
                rec[f"vals_{a}"] = []
                rec[f"fl_{a}"] = 0
                rec[f"plusfl_{a}"] = 0
                rec[f"ctrl_{a}"] = []
            for phase in ("discovery", "heldout"):
                err = find(repo, mdir, phase, task, "err")
                ctl = find(repo, mdir, phase, task, "ctl")
                cor = find(repo, mdir, phase, task, "cor")
                if err is not None:
                    rec["phases_err"].append(phase)
                    minus = [c for c in err.values()
                             if str(c.get("written_sign", "")).strip() == "-"]
                    plus = [c for c in err.values()
                            if str(c.get("written_sign", "")).strip() == "+"]
                    rec["n_minus"] += len(minus)
                    rec["n_plus"] += len(plus)
                    for a in ALPHAS:
                        for c in minus:
                            lf = leaf(c, a)
                            if lf is None:
                                continue
                            rec[f"vals_{a}"].append(lf["delta_ld"])
                            rec[f"fl_{a}"] += bool(lf.get("flipped"))
                        for c in plus:
                            lf = leaf(c, a)
                            if lf is not None:
                                rec[f"plusfl_{a}"] += bool(lf.get("flipped"))
                if ctl is not None:
                    for a in ALPHAS:
                        for c in ctl.values():
                            if str(c.get("written_sign", "")).strip() != "-":
                                continue
                            conds = c["conditions"]
                            # some models carry extra control variants (e.g.
                            # Qwen's CTRL_MAG_BORING); use CTRL_MAG exactly
                            cn = ("CTRL_MAG" if "CTRL_MAG" in conds else
                                  next((k for k in conds
                                        if k.startswith("CTRL")), None))
                            v = conds.get(cn, {})
                            v = v.get(a) if isinstance(v, dict) else None
                            if isinstance(v, dict):
                                rec[f"ctrl_{a}"].append(v["delta_ld"])
                if cor is not None:
                    rec["phases_cor"].append(phase)
                    for grp, sel in (("cminus", "-"), ("cplus", "+")):
                        cases = [c for c in cor.values()
                                 if str(c.get("written_sign", "")).strip() == sel]
                        br = sum(bool((leaf(c, "a3.0") or {}).get("broken"))
                                 for c in cases)
                        rec[grp][0] += br
                        rec[grp][1] += len(cases)
            for a in ALPHAS:
                rec[f"mean_{a}"] = (st.mean(rec[f"vals_{a}"])
                                    if rec[f"vals_{a}"] else None)
                rec[f"cmean_{a}"] = (st.mean(rec[f"ctrl_{a}"])
                                     if rec[f"ctrl_{a}"] else None)
            out[(mname, task)] = rec
    return out


def fig1(data, path):
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 8.2), sharex=True)
    width = 0.2
    groups = ["err", "plus", "cminus", "cplus"]
    labels = ["minus-written errors flipped", "plus-written errors flipped",
              "correct-minus broken", "correct-plus broken"]
    colors = ["#2166ac", "#92c5de", "#b2182b", "#bdbdbd"]
    for ax, (task, tname) in zip(axes, TASKS):
        for gi, (grp, lab, col) in enumerate(zip(groups, labels, colors)):
            xs, hs, notes = [], [], []
            for mi, (_d, mname, _c) in enumerate(MODELS):
                rec = data[(mname, task)]
                if grp == "err":
                    k, n = rec["fl_a3.0"], rec["n_minus"]
                elif grp == "plus":
                    k, n = rec["plusfl_a3.0"], rec["n_plus"]
                else:
                    k, n = rec[grp]
                xs.append(mi + (gi - 1.5) * width)
                hs.append(k / n if n else 0.0)
                notes.append(f"{k}/{n}" if n else "n=0")
            bars = ax.bar(xs, hs, width * 0.9, color=col,
                          label=lab if ax is axes[0] else None)
            for b, note in zip(bars, notes):
                ax.annotate(note, (b.get_x() + b.get_width() / 2,
                                   b.get_height()),
                            ha="center", va="bottom", fontsize=7.0,
                            xytext=(0, 1.5), textcoords="offset points")
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("fraction of cases\n(discovery + held-out)")
        ax.set_title(f"{tname} — pooled discovery + held-out, α = 3",
                     fontsize=11)
        ax.axhline(0, color="0.4", lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].set_xticks(range(len(MODELS)))
    axes[1].set_xticklabels([m[1] for m in MODELS], fontsize=9.5)
    axes[0].legend(loc="upper left", fontsize=8.6, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig2(data, path):
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 8.4))
    xs = [1, 2, 3]
    for ax, (task, tname) in zip(axes, TASKS):
        ctrl_all = []
        for _d, mname, col in MODELS:
            rec = data[(mname, task)]
            ys = [rec[f"mean_{a}"] for a in ALPHAS]
            ax.plot(xs, ys, "-o", color=col, ms=4.5,
                    label=f"{mname} (n={rec['n_minus']})")
            ctrl_all += [rec[f"cmean_{a}"] for a in ALPHAS
                         if rec[f"cmean_{a}"] is not None]
        lo, hi = min(ctrl_all), max(ctrl_all)
        pad = 0.15
        ax.axhspan(lo - pad, hi + pad, color="0.82", alpha=0.5, zorder=0,
                   label="random control (CTRL_MAG)")
        ax.axhline(0, color="0.4", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xlabel(r"steering strength $\alpha$")
        ax.set_title(f"{tname} — pooled discovery + held-out, "
                     "minus-written errors", fontsize=11)
        ax.set_ylabel("Mean shift in the written\nsign's lead (logits), C2")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=8.0, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    repo = os.path.normpath(args.repo)
    out = args.out or os.path.join(repo, "paper", "figures")
    os.makedirs(out, exist_ok=True)
    data = load(repo)
    # print pooled numbers for red-team cross-check against the ledger
    for task, _ in TASKS:
        print("=" * 10, task)
        for _d, mname, _c in MODELS:
            r = data[(mname, task)]
            print(f"{mname:18s} err_phases={r['phases_err']} "
                  f"minus {r['fl_a3.0']}/{r['n_minus']} "
                  f"(a1 {r['fl_a1.0']}, a2 {r['fl_a2.0']}) "
                  f"mean_a3={None if r['mean_a3.0'] is None else round(r['mean_a3.0'],3)} | "
                  f"plus {r['plusfl_a3.0']}/{r['n_plus']} | "
                  f"c- {r['cminus'][0]}/{r['cminus'][1]} "
                  f"c+ {r['cplus'][0]}/{r['cplus'][1]} "
                  f"cor_phases={r['phases_cor']} | "
                  f"ctrl means {[None if r[f'cmean_{a}'] is None else round(r[f'cmean_{a}'],3) for a in ALPHAS]}")
    fig1(data, os.path.join(out, "figG1_specificity.png"))
    fig2(data, os.path.join(out, "figG2_dose_response.png"))
    print("wrote", out)
