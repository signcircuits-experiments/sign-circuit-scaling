#!/usr/bin/env python3
"""Appendix G figures: five-model steering specificity (held-out, C2 condition).

Terminology and symbols follow the main draft (sec2/sec4/sec5) and
fig3_steering.py: the *sign lead* is the written wrong sign's logit minus the
correct sign's logit; the *sign direction* was extracted on discovery data and
frozen; the C2 condition adds a scaled negative of the sign direction at the
habit layers; alpha controls dose; CTRL_MAG is the magnitude-matched random
control.

Generates two images with NO figure numbers or captions baked in (captions
live in the paper so numbering can change):

  figG1_specificity.png    the specificity fingerprint: per model, at alpha=3,
                           fraction of wrong '-' errors flipped, of correct '-'
                           answers broken, of correct '+' answers broken;
                           CTRL_MAG flips/breaks are zero everywhere except
                           one Llama det control flip (one flip in 5,529
                           CTRL_MAG evaluations overall).
  figG2_dose_response.png  mean shift in the wrong sign's lead on wrong '-'
                           errors vs alpha, one line per model, grey band =
                           spread of the CTRL_MAG means.

Data: {Model}/heldout_*/s08_c2_steering/*.json. Sign conventions:
  - error files: written_sign is the sign the model wrote (the wrong one);
    wrong '-' errors are written_sign == "-".
  - correct files: the field named written_sign comes from row["wrong_sign"]
    but, because correct-cohort rows reuse the error-row schema (where that
    column holds the sign actually present in the text), it equals the sign
    the model wrote = the TRUE sign. See exp_c2_on_correct.py line 98, which
    asserts the input text carries this sign. So correct '-' answers are
    written_sign == "-".
  - "flipped" on errors / "broken" on corrects: strict zero-crossing of the
    sign lead (baseline lead > 0 and post-edit lead < 0).

Every count and mean plotted here equals the corresponding row in
paper/appendix/ledger_results.csv (n_flipped_minus[C2|a*], n_broken[C2|a*],
mean_delta_ld_minus[C2|a*], n_wrote_minus_all).

Usage: python3 fig_G_specificity.py [--repo REPO_ROOT] [--out OUT_DIR]
"""
import argparse, glob, json, os, statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ALPHAS = ["a1.0", "a2.0", "a3.0"]
MODELS = [  # (repo dir, display name per main-draft Table 1, color)
    ("Gemma",             "Gemma-3-27B",       "#4c78a8"),
    ("Qwen",              "Qwen2.5-72B",       "#f58518"),
    ("Llama",             "Llama-3.3-70B",     "#54a24b"),
    ("Phi",               "Phi-4",             "#b279a2"),
    ("Mistral-Small-24B", "Mistral-Small-24B", "#e45756"),
]
TASKS = [("det", "4×4 determinant"), ("ibp", "integration by parts")]


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
    out = {}
    for mdir, mname, _ in MODELS:
        for task, _t in TASKS:
            err = _one(repo, mdir, task, f"{task}*error*combined_ablation.json")
            ctl = _one(repo, mdir, task, f"{task}*error*ctrl_mag.json")
            cor = _one(repo, mdir, task, f"{task}*correct*c2_on_correct.json")
            minus = [c for c in err.values()
                     if str(c.get("written_sign", "")).strip() == "-"]
            rec = {"n_minus": len(minus)}
            for a in ALPHAS:
                vals, fl = [], 0
                for c in minus:
                    lf = _leaf(c["conditions"].get("C2", {}), a)
                    if lf is None:
                        continue
                    vals.append(lf["delta_ld"])
                    fl += bool(lf.get("flipped"))
                rec[f"err_{a}"] = (statistics.mean(vals), fl, len(vals))
                cvals = []
                for c in ctl.values():
                    if str(c.get("written_sign", "")).strip() != "-":
                        continue
                    conds = c["conditions"]
                    # some models carry extra control variants (e.g. Qwen's
                    # CTRL_MAG_BORING / CTRL_MAG_L75); use CTRL_MAG exactly
                    cn = ("CTRL_MAG" if "CTRL_MAG" in conds else
                          next((k for k in conds if k.startswith("CTRL")), None))
                    lf = _leaf(conds.get(cn, {}), a)
                    if lf is not None:
                        cvals.append(lf["delta_ld"])
                rec[f"ctrl_{a}"] = statistics.mean(cvals)
            for grp, sel in (("cminus", "-"), ("cplus", "+")):
                cases = [c for c in cor.values()
                         if str(c.get("written_sign", "")).strip() == sel]
                br = sum(bool((_leaf(c["conditions"].get("C2", {}), "a3.0")
                               or {}).get("broken")) for c in cases)
                rec[grp] = (br, len(cases))
            out[(mname, task)] = rec
    return out


def fig1(data, path):
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 6.4), sharex=True)
    width, groups = 0.26, ["err", "cminus", "cplus"]
    labels = ["wrong '$-$' errors flipped", "correct '$-$' broken",
              "correct '$+$' broken"]
    colors = ["#2166ac", "#b2182b", "#bdbdbd"]
    for ax, (task, tname) in zip(axes, TASKS):
        for gi, (grp, lab, col) in enumerate(zip(groups, labels, colors)):
            xs, hs, notes = [], [], []
            for mi, (_d, mname, _c) in enumerate(MODELS):
                rec = data[(mname, task)]
                if grp == "err":
                    _m, fl, n = rec["err_a3.0"]
                    k, n_ = fl, n
                else:
                    k, n_ = rec[grp]
                x = mi + (gi - 1) * width
                xs.append(x)
                hs.append(k / n_ if n_ else 0.0)
                notes.append(f"{k}/{n_}" if n_ else "n=0")
            bars = ax.bar(xs, hs, width * 0.92, color=col,
                          label=lab if ax is axes[0] else None)
            for b, note in zip(bars, notes):
                ax.annotate(note, (b.get_x() + b.get_width() / 2,
                                   b.get_height()),
                            ha="center", va="bottom", fontsize=7.2,
                            rotation=0, xytext=(0, 1.5),
                            textcoords="offset points")
        ax.set_ylim(0, 1.12)
        ax.set_ylabel("fraction of held-out cases")
        ax.set_title(f"{tname} — held-out, α = 3", fontsize=11)
        ax.axhline(0, color="0.4", lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].set_xticks(range(len(MODELS)))
    axes[1].set_xticklabels([m[1] for m in MODELS], fontsize=9.5)
    axes[0].legend(loc="upper left", fontsize=9, frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig2(data, path):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.1))
    xs = [1, 2, 3]
    for ax, (task, tname) in zip(axes, TASKS):
        ctrl_all = []
        for _d, mname, col in MODELS:
            rec = data[(mname, task)]
            ys = [rec[f"err_{a}"][0] for a in ALPHAS]
            n = rec["n_minus"]
            ax.plot(xs, ys, "-o", color=col, ms=4.5,
                    label=f"{mname} (n={n})")
            ctrl_all += [rec[f"ctrl_{a}"] for a in ALPHAS]
        lo, hi = min(ctrl_all), max(ctrl_all)
        pad = 0.15
        ax.axhspan(lo - pad, hi + pad, color="0.82", alpha=0.5, zorder=0,
                   label="random control (CTRL_MAG)" if ax is axes[0] else None)
        ax.axhline(0, color="0.4", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xlabel(r"steering strength $\alpha$")
        ax.set_title(tname, fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=7.6, frameon=False, loc="lower left")
    axes[0].set_ylabel("Mean shift in the wrong\nsign's lead (logits)\n"
                       "(wrong '$-$' errors, C2)")
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
    print("wrote", out)
