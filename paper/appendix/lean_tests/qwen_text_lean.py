#!/usr/bin/env python3
"""
qwen_text_lean.py
=================
Follow-up to qwen_embed_geometry.py.

That test showed the vocab at large is 50/50 on the "-" vs "+" direction
(49.6% lean -), so the layer-0 lean is NOT a blanket weight property.
But the 15 probe-position tokens leaned - in 12/15 cases.

This test asks the sharper question: does the text Qwen ACTUALLY READS in our
determinant problems lean "-"?

Method:
  1. Tokenize all 288 held-out question texts (147 error + 141 correct) with
     the real Qwen tokenizer, each cut at sign_char_offset (the context the
     model has read when the layer-0 lean is measured).
  2. Count token frequencies; fetch embedding rows for the unique tokens only
     (HTTP Range requests, same as qwen_embed_geometry.py).
  3. diff(t) = dot(u_minus - u_plus, f(e_t)),  f = identity and RMSNorm.
     positive = leans "-".
  4. Report OCCURRENCE-WEIGHTED stats: % of actual text-token mass leaning -,
     weighted mean lean, top contributors.

Interpretation:
  - If the weighted lean is clearly positive -> token composition of math text
    explains (at least part of) the layer-0 lean.
  - If ~50/50 like the vocab -> the lean must come from position/copying/lens
    artifact instead; token identity is ruled out too.

Run on Mac:
  python3 -m pip install --quiet numpy requests tokenizers
  python3 qwen_text_lean.py
"""

import json, struct, csv, os, sys
from collections import Counter

import numpy as np
import requests

# ── Config ──────────────────────────────────────────────────────────────────
MODEL_ID     = "Qwen/Qwen2.5-72B-Instruct"
HF_BASE      = f"https://huggingface.co/{MODEL_ID}/resolve/main"
MINUS_TOK    = 481   # "Ġ-"
PLUS_TOK     = 488   # "Ġ+"
HIDDEN       = 8192
VOCAB        = 152064
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON  = os.path.join(SCRIPT_DIR, "qwen_text_lean_results.json")
TOKENIZER_JSON = os.path.join(SCRIPT_DIR, "qwen_tokenizer.json")

CSV_DIR = "../../../Qwen/raw_data_4x4_DET/heldout"
CSV_FILES = [
    "qwen_det_4x4_error_heldout_n147_experiment_ready.csv",
    "qwen_det_4x4_correct_heldout_n141_experiment_ready.csv",
]

# ── HTTP helpers (same as qwen_embed_geometry.py) ───────────────────────────
def get_json(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def get_file(url, path):
    if os.path.exists(path):
        return
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)

def bf16_to_float32(buf):
    arr_u16 = np.frombuffer(buf, dtype=np.uint16)
    arr_u32 = arr_u16.astype(np.uint32) << 16
    return arr_u32.view(np.float32)

def range_get(url, start, end):
    headers = {"Range": f"bytes={start}-{end}"}
    r = requests.get(url, headers=headers, timeout=120)
    assert r.status_code in (200, 206), f"Range GET failed: {r.status_code} {url}"
    return r.content

def fetch_safetensors_header(shard_filename):
    url = f"{HF_BASE}/{shard_filename}"
    raw8 = range_get(url, 0, 7)
    hlen = struct.unpack("<Q", raw8)[0]
    raw_hdr = range_get(url, 8, 8 + hlen - 1)
    header = json.loads(raw_hdr.decode("utf-8"))
    return header, 8 + hlen

def fetch_rows(shard_filename, tensor_name, row_indices, header_json, data_offset_base):
    url = f"{HF_BASE}/{shard_filename}"
    meta = header_json[tensor_name]
    offsets = meta["data_offsets"]
    assert meta["shape"][-1] == HIDDEN
    bpe = 2
    out = {}
    idxs = sorted(set(row_indices))
    for i, ridx in enumerate(idxs):
        row_start = data_offset_base + offsets[0] + ridx * HIDDEN * bpe
        raw = range_get(url, row_start, row_start + HIDDEN * bpe - 1)
        out[ridx] = bf16_to_float32(raw)
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(idxs)} rows ...")
    return out

def rmsnorm(x, gain):
    rms = np.sqrt(np.mean(x * x) + 1e-6)
    return x / rms * gain

# ── Main ────────────────────────────────────────────────────────────────────
def run():
    results = {"model_id": MODEL_ID, "minus_tok_id": MINUS_TOK, "plus_tok_id": PLUS_TOK}

    # Step 1: tokenizer
    print("Step 1: Loading Qwen tokenizer ...")
    get_file(f"{HF_BASE}/tokenizer.json", TOKENIZER_JSON)
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(TOKENIZER_JSON)
    id_to_tok = {i: tok.id_to_token(i) for i in range(tok.get_vocab_size())}
    assert id_to_tok[MINUS_TOK] == "Ġ-" and id_to_tok[PLUS_TOK] == "Ġ+"
    print("  Confirmed sign token IDs 481/488")

    # Step 2: tokenize question texts up to sign_char_offset
    print("Step 2: Tokenizing question texts ...")
    freq = Counter()
    n_texts = 0
    for fname in CSV_FILES:
        path = os.path.join(CSV_DIR, fname)
        for row in csv.DictReader(open(path)):
            txt = row["full_input"]
            off = row.get("sign_char_offset", "")
            try:
                off = int(off)
                if 0 < off <= len(txt):
                    txt = txt[:off]
            except (ValueError, TypeError):
                pass  # no offset (e.g. correct rows) -> use full text
            enc = tok.encode(txt, add_special_tokens=False)
            freq.update(enc.ids)
            n_texts += 1
    total_occ = sum(freq.values())
    uniq = sorted(freq)
    print(f"  {n_texts} texts, {total_occ} token occurrences, {len(uniq)} unique tokens")
    results["n_texts"] = n_texts
    results["total_token_occurrences"] = total_occ
    results["n_unique_tokens"] = len(uniq)

    # Step 3: fetch weights
    print("Step 3: Fetching weights ...")
    idx = get_json(f"{HF_BASE}/model.safetensors.index.json")
    wmap = idx["weight_map"]
    shard_embed = wmap["model.embed_tokens.weight"]
    shard_lm    = wmap["lm_head.weight"]

    hdr_lm, off_lm = fetch_safetensors_header(shard_lm)
    lm = fetch_rows(shard_lm, "lm_head.weight", [MINUS_TOK, PLUS_TOK], hdr_lm, off_lm)
    diff_dir = lm[MINUS_TOK] - lm[PLUS_TOK]

    norm_meta = hdr_lm["model.norm.weight"]
    raw_norm = range_get(f"{HF_BASE}/{wmap['model.norm.weight']}",
                         off_lm + norm_meta["data_offsets"][0],
                         off_lm + norm_meta["data_offsets"][1] - 1)
    gain = bf16_to_float32(raw_norm)

    hdr_e, off_e = fetch_safetensors_header(shard_embed)
    print(f"  Fetching {len(uniq)} embed rows ...")
    embed = fetch_rows(shard_embed, "model.embed_tokens.weight", uniq, hdr_e, off_e)

    # Step 4: occurrence-weighted lean
    print("Step 4: Computing occurrence-weighted lean ...")
    per_tok = {}
    for tid in uniq:
        e = embed[tid]
        per_tok[tid] = {
            "token_str": id_to_tok.get(tid, "?"),
            "count": freq[tid],
            "diff_raw": float(np.dot(diff_dir, e)),
            "diff_norm": float(np.dot(diff_dir, rmsnorm(e, gain))),
        }

    occ_pos = sum(v["count"] for v in per_tok.values() if v["diff_norm"] > 0)
    occ_pos_raw = sum(v["count"] for v in per_tok.values() if v["diff_raw"] > 0)
    w_mean_norm = sum(v["count"] * v["diff_norm"] for v in per_tok.values()) / total_occ
    w_mean_raw  = sum(v["count"] * v["diff_raw"]  for v in per_tok.values()) / total_occ
    uniq_pos = sum(1 for v in per_tok.values() if v["diff_norm"] > 0)

    contrib = sorted(per_tok.items(), key=lambda kv: -abs(kv[1]["count"] * kv[1]["diff_norm"]))
    top = [{"token_id": tid, **v,
            "contribution": round(v["count"] * v["diff_norm"] / total_occ, 4)}
           for tid, v in contrib[:25]]

    results.update({
        "pct_occurrences_leaning_minus_norm": round(100 * occ_pos / total_occ, 2),
        "pct_occurrences_leaning_minus_raw":  round(100 * occ_pos_raw / total_occ, 2),
        "pct_unique_tokens_leaning_minus_norm": round(100 * uniq_pos / len(uniq), 2),
        "weighted_mean_diff_norm": round(w_mean_norm, 4),
        "weighted_mean_diff_raw":  round(w_mean_raw, 6),
        "top_contributors": top,
        "vocab_baseline": {"pct_leaning_minus_norm": 49.3,
                           "source": "qwen_embed_geometry_results.json"},
        "observed_layer0_logit_diff": 4.5,
        "note": "diff = dot(u_minus - u_plus, f(e_t)); positive = lean toward '-'. "
                "Weighted by how often each token occurs in the question text "
                "(cut at sign_char_offset where available).",
    })

    pct = results["pct_occurrences_leaning_minus_norm"]
    if pct >= 65 and w_mean_norm > 0:
        verdict = ("SUPPORTED: the token mass of our question text leans '-' "
                   f"({pct}% of occurrences, weighted mean {w_mean_norm:+.2f}) "
                   "vs a 49.3% vocab baseline - token composition contributes "
                   "to the layer-0 lean")
    elif pct <= 55:
        verdict = ("NOT SUPPORTED: question-text token mass is near the vocab "
                   f"baseline ({pct}% vs 49.3%) - token identity does not "
                   "explain the layer-0 lean")
    else:
        verdict = f"WEAK/AMBIGUOUS: {pct}% of occurrences lean '-' (baseline 49.3%)"
    results["verdict"] = verdict

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {OUTPUT_JSON}")
    print(f"  texts: {n_texts}, occurrences: {total_occ}, unique: {len(uniq)}")
    print(f"  % occurrences leaning - (norm): {pct:.1f}%  (vocab baseline 49.3%)")
    print(f"  % occurrences leaning - (raw):  {results['pct_occurrences_leaning_minus_raw']:.1f}%")
    print(f"  weighted mean diff (norm): {w_mean_norm:+.4f}")
    print(f"  verdict: {verdict}")

if __name__ == "__main__":
    run()
