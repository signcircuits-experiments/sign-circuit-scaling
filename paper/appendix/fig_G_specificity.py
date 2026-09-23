#!/usr/bin/env python3
"""Appendix G figures: five-model steering specificity (held-out, C2, POOLED).

Terminology and symbols follow the main working draft (v2): the *sign lead*
is the written sign's logit minus the alternative's; the *sign direction*
was extracted on discovery data and frozen; the C2 condition (minus-removal
steering) adds a scaled negative of the sign direction at the habit layers;
alpha controls dose; CTRL_MAG is the magnitude-matched random control.

Both figures POOL the two held-out tasks (4x4 determinant + integration by
parts); pooled counts are sums over the two tasks and pooled means are
case-weighted. Per-task percentages appear in main-draft Figure 6; the
pooled view here has larger n and tighter statistics.

Generates two images with NO figure numbers or captions baked in (captions
live in the paper so numbering can change):

  figG1_specificity.png    the specificity fingerprint: per model, at
                           alpha=3, pooled fraction of minus-written errors
                           flipped, of plus-written errors flipped, of
                           correct-minus answers broken, of correct-plus
                           answers broken; CTRL_MAG flips/breaks are zero
                           everywhere except one Llama det control flip
                           (one flip in 5,529 CTRL_MAG evaluations overall).
  figG2_dose_response.png  pooled mean shift in the written sign's lead on
                           minus-written errors vs alpha, one line per
                           model, grey band = spread of the CTRL_MAG means.

Data: {Model}/heldout_*/s08_c2_steering/*.json. Sign conventions:
  - error files: written_sign is the sign the model wrote (the wrong one);
    minus-written errors are written_sign == "-", plus-written == "+".
  - correct files: the field named written_sign comes from row["wrong_sign"]
    but, because correct-cohort rows reuse the error-row schema (where that
    column holds the sign actually present in the text), it equals the sign
    the model wrote = the TRUE sign. See exp_c2_on_correct.py line 98, which
    asserts the input text carries this sign. So correct-minus answers are
    written_sign == "-".
  - "flipped" on errors / "broken" on corrects: strict zero-crossing of the
    sign lead (baseline lead > 0 and post-edit lead < 0).

Every pooled count equals the sum of the corresponding per-task rows in
paper/appendix/ledger_results.csv (n_flipped_minus[C2|a*], n_flipped[C2|a*]
minus n_flipped_minus[C2|a*] for plus-written, n_broken[C2|a*],
n_wrote_minus_all), and every pooled mean equals the case-weighted average
of the per-task mean_delta_ld_minus[C2|a*] rows.

Usage: python3 fig_G_specificity.py [--repo REPO_ROOT] [--out OUT_DIR]
"""
import argparse, glob, json, os, statistics

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
TASKS = ["det", "ibp"]


def _leaf(cond, a):
    v = cond.get(a) if isinstance(cond, dict) else None
    return v if isinstance(v, dict) else None


def _one(repo, mdir, task, pattern):
    fs = [f for f in glob.glob(os.path.join(repo, mdir, "heldout*",
                                            "s08_c2_steering", pattern))
          if (task == "det") == ("det" in os.path.basename(f))]
    assert len(fs) == 1, (mdir, task, pattern, fs)
    return json.load(open(fs[0]))["results"]


def load(repo):
    """Pool det+ibp per model: counts are sums, means are case-weighted."""
    out = {}
    for mdir, mname, _ in MODELS:
        rec = {"n_minus": 0, "n_plus": 0}
        for a in ALPHAS:
            rec[f"err_vals_{a}"] = []
            rec[f"err_fl_{a}"] = 0
            rec[f"plus_fl_{a}"] = 0
            rec[f"ctrl_vals_{a}"] = []
        rec["cminus"] = [0, 0]
        rec["cplus"] = [0, 0]
        for task in TASKS:
            err = _one(repo, mdir, task, f"{task}*error*combined_ablation.json")
            ctl = _one(repo, mdir, task, f"{task}*error*ctrl_mag.json")
            cor = _one(repo, mdir, task, f"{task}*correct*c2_on_correct.json")
            minus = [c for c in err.values()
                     if str(c.get("written_sign", "")).strip() == "-"]
            plus = [c for c in err.values()
                    if str(c.get("written_sign", "")).strip() == "+"]
            rec["n_minus"] += len(minus)
            rec["n_plus"] += len(plus)
            for a in ALPHAS:
                for c in minus:
                    lf = _leaf(c["conditions"].get("C2", {}), a)
                    if lf is None:
                        continue
                    rec[f"err_vals_{a}"].append(lf["delta_ld"])
                    rec[f"err_fl_{a}"] += bool(lf.get("flipped"))
                for c in plus:
                    lf = _leaf(c["conditions"].get("C2", {}), a)
                    if lf is not None:
                        rec[f"plus_fl_{a}"] += bool(lf.get("flipped"))
                for c in ctl.values():
                    if str(c.get("written_sign", "")).strip() != "-":
                        continue
                    conds = c["conditions"]
                    # some models carry extra control variants (e.g. Qwen's
                    # CTRL_MAG_BORING / CTRL_MAG_L75); use CTRL_MAG exactly
                    cn = ("CTRL_MAG" if "CTRL_MAG" in conds else
                          next((k for k in conds if k.startswith("CTRL")),
                               None))
                    lf = _leaf(conds.get(cn, {}), a)
                    if lf is not None:
                        rec[f"ctrl_vals_{a}"].append(lf["delta_ld"])
            for grp, sel in (("cminus", "-"), ("cplus", "+")):
                cases = [c for c in cor.values()
                         if str(c.get("written_sign", "")).strip() == sel]
                br = sum(bool((_leaf(c["conditions"].get("C2", {}), "a3.0")
                               or {}).get("broken")) for c in cases)
                rec[grp][0] += br
                rec[grp][1] += len(cases)
        for a in ALPHAS:
            rec[f"err_{a}"] = (statistics.mean(rec[f"err_vals_{a}"]),
                               rec[f"err_fl_{a}"],
                               len(rec[f"err_vals_{a}"]))
            rec[f"ctrl_{a}"] = statistics.mean(rec[f"ctrl_vals_{a}"])
        out[mname] = rec
    return out


def fig1(data, path):
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    width = 0.2
    groups = ["err", "plus", "cminus", "cplus"]
    labels = ["minus-written errors flipped", "plus-written errors flipped",
              "correct-minus broken", "correct-plus broken"]
    colors = ["#2166ac", "#92c5de", "#b2182b", "#bdbdbd"]
    for gi, (grp, lab, col) in enumerate(zip(groups, labels, colors)):
        xs, hs, notes = [], [], []
        for mi, (_d, mname, _c) in enumerate(MODELS):
            rec = data[mname]
            if grp == "err":
                _m, fl, n = rec["err_a3.0"]
                k, n_ = fl, n
            elif grp == "plus":
                k, n_ = rec["plus_fl_a3.0"], rec["n_plus"]
            else:
                k, n_ = rec[grp]
            xs.append(mi + (gi - 1.5) * width)
            hs.append(k / n_ if n_ else 0.0)
            notes.append(f"{k}/{n_}" if n_ else "n=0")
        bars = ax.bar(xs, hs, width * 0.9, color=col, label=lab)
        for b, note in zip(bars, notes):
            ax.annotate(note, (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=7.0,
                        xytext=(0, 1.5), textcoords="offset points")
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("fraction of held-out cases (pooled)")
    ax.set_title("Pooled held-out specificity (det + ibp), α = 3",
                 fontsize=11)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xticks(range(len(MODELS)))
    ax.set_xticklabels([m[1] for m in MODELS], fontsize=9.5)
    ax.legend(loc="upper left", fontsize=8.6, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig2(data, path):
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    xs = [1, 2, 3]
    ctrl_all = []
    for _d, mname, col in MODELS:
        rec = data[mname]
        ys = [rec[f"err_{a}"][0] for a in ALPHAS]
        ax.plot(xs, ys, "-o", color=col, ms=4.5,
                label=f"{mname} (n={rec['n_minus']})")
        ctrl_all += [rec[f"ctrl_{a}"] for a in ALPHAS]
    lo, hi = min(ctrl_all), max(ctrl_all)
    pad = 0.15
    ax.axhspan(lo - pad, hi + pad, color="0.82", alpha=0.5, zorder=0,
               label="random control (CTRL_MAG)")
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xticks(xs)
    ax.set_xlabel(r"steering strength $\alpha$")
    ax.set_title("Pooled dose–response (det + ibp), minus-written errors",
                 fontsize=11)
    ax.set_ylabel("Mean shift in the written sign's\nlead (logits), C2")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8.2, frameon=False, loc="lower left")
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
    fig1(data, os.path.join(out, "figG1_specificity.png"))
    fig2(data, os.path.join(out, "figG2_dose_response.png"))
    # print pooled numbers for red-team cross-check against the ledger
    for _d, mname, _c in MODELS:
        r = data[mname]
        print(mname, "minus", [(a, round(r[f"err_{a}"][0], 3),
                                r[f"err_{a}"][1], r[f"err_{a}"][2])
                               for a in ALPHAS],
              "plus_fl_a3", r["plus_fl_a3.0"], "/", r["n_plus"],
              "cminus", r["cminus"], "cplus", r["cplus"],
              "ctrl", [round(r[f"ctrl_{a}"], 3) for a in ALPHAS])
    print("wrote", out)
