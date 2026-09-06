#!/usr/bin/env python3
"""
qwen_embed_geometry.py
======================
Hypothesis test: Qwen2.5-72B-Instruct embedding geometry — is the layer-0 bias
toward the "−" sign token a property of the raw weight matrices alone?

For every vocab token t, compute:
  diff(t) = u_minus · f(e_t) − u_plus · f(e_t)
where:
  u_minus = lm_head row for token 481 ("Ġ-")
  u_plus  = lm_head row for token 488 ("Ġ+")
  e_t     = embed_tokens row for token t
  f = (a) identity, (b) RMSNorm with model.norm.weight gain

Steps:
  1. Download tokenizer.json → confirm token IDs
  2. Download model.safetensors.index.json → find shards for needed tensors
  3. Use HTTP Range requests against safetensors shards to pull only the
     required rows (2 lm_head rows, model.norm.weight, ≥20k embed_tokens rows)
  4. Compute stats and save results

Model: Qwen/Qwen2.5-72B-Instruct
  tie_word_embeddings: False
  hidden_size: 8192
  vocab_size: 152064
  num_hidden_layers: 80
  torch_dtype: bfloat16
"""

import json, struct, requests, numpy as np, os, sys

# ── Config ──────────────────────────────────────────────────────────────────
MODEL_ID     = "Qwen/Qwen2.5-72B-Instruct"
HF_BASE      = f"https://huggingface.co/{MODEL_ID}/resolve/main"
MINUS_TOK    = 481   # "Ġ-"  (space+minus, as used in logit-lens records)
PLUS_TOK     = 488   # "Ġ+"  (space+plus)
HIDDEN       = 8192
VOCAB        = 152064
DTYPE        = "bfloat16"
BYTES_PER_EL = 2     # bf16 / fp16
OUTPUT_JSON  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qwen_embed_geometry_results.json")

# Probe tokens from logit-lens records (written_sign="-", layer 0 diff ≈ +4.5)
PROBE_TOKS = [267, 256, 257, 258, 513, 1796, 261, 262, 1415, 264, 263,
              250, 251, 254, 255]
INTERPRET_TOKS = {
    "newline": None,    # determined from tokenizer
    "equals":  28,      # "="
    "rparen":  8,       # ")"
    "digit_0": 15, "digit_1": 16, "digit_2": 17, "digit_3": 18,
    "digit_4": 19, "digit_5": 20, "digit_6": 21, "digit_7": 22,
    "digit_8": 23, "digit_9": 24,
    "minus_bare": 12,   # "-"
    "plus_bare":  10,   # "+"
    "space_minus": 481, "space_plus": 488,
}

def get_json(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def bf16_to_float32(buf):
    """Convert raw bfloat16 bytes to float32 numpy array."""
    arr_u16 = np.frombuffer(buf, dtype=np.uint16)
    arr_u32 = arr_u16.astype(np.uint32) << 16
    return arr_u32.view(np.float32)

def range_get(url, start, end):
    """HTTP Range GET [start, end] inclusive (bytes)."""
    headers = {"Range": f"bytes={start}-{end}"}
    r = requests.get(url, headers=headers, timeout=120)
    assert r.status_code in (200, 206), f"Range GET failed: {r.status_code} {url}"
    return r.content

def fetch_safetensors_rows(shard_filename, tensor_name, row_indices, n_cols,
                            header_json, data_offset_base):
    """
    Fetch specific rows from a safetensors shard via HTTP Range.
    header_json: the parsed safetensors header dict (from the shard)
    data_offset_base: byte offset where the actual data starts (after header length + header json)
    """
    url = f"{HF_BASE}/{shard_filename}"
    meta = header_json[tensor_name]
    dtype_str = meta["dtype"]   # "BF16" or "F16"
    offsets = meta["data_offsets"]  # [start, end] within data section
    shape = meta["shape"]
    assert shape[-1] == n_cols, f"Col mismatch: {shape[-1]} vs {n_cols}"
    bpe = 2  # bf16 or fp16

    rows = []
    for ridx in sorted(set(row_indices)):
        row_start = data_offset_base + offsets[0] + ridx * n_cols * bpe
        row_end   = row_start + n_cols * bpe - 1
        raw = range_get(url, row_start, row_end)
        vec = bf16_to_float32(raw)
        rows.append((ridx, vec))
    return rows

def fetch_safetensors_header(shard_filename):
    """Fetch the safetensors header from a shard."""
    url = f"{HF_BASE}/{shard_filename}"
    # First 8 bytes = header length (little-endian uint64)
    raw8 = range_get(url, 0, 7)
    hlen = struct.unpack("<Q", raw8)[0]
    # Header JSON
    raw_hdr = range_get(url, 8, 8 + hlen - 1)
    header = json.loads(raw_hdr.decode("utf-8"))
    data_offset = 8 + hlen  # byte where tensor data starts
    return header, data_offset

def rmsnorm(x, gain):
    """RMSNorm: x / rms(x) * gain"""
    rms = np.sqrt(np.mean(x * x) + 1e-6)
    return x / rms * gain

def run():
    results = {}

    # ── Step 1: Confirm token IDs ────────────────────────────────────────────
    print("Step 1: Downloading tokenizer.json ...")
    tok_data = get_json(f"{HF_BASE}/tokenizer.json")
    vocab = tok_data["model"]["vocab"]
    id_to_tok = {v: k for k, v in vocab.items()}
    assert id_to_tok[MINUS_TOK] == "Ġ-", f"Unexpected: {id_to_tok[MINUS_TOK]}"
    assert id_to_tok[PLUS_TOK]  == "Ġ+", f"Unexpected: {id_to_tok[PLUS_TOK]}"
    print(f"  Confirmed: token {MINUS_TOK}='{id_to_tok[MINUS_TOK]}', {PLUS_TOK}='{id_to_tok[PLUS_TOK]}'")

    results["model_id"] = MODEL_ID
    results["minus_tok_id"] = MINUS_TOK
    results["plus_tok_id"]  = PLUS_TOK
    results["minus_tok_str"] = id_to_tok[MINUS_TOK]
    results["plus_tok_str"]  = id_to_tok[PLUS_TOK]
    results["tie_word_embeddings"] = False
    results["dtype"] = DTYPE
    results["hidden_size"] = HIDDEN
    results["vocab_size"] = VOCAB

    # ── Step 2: Safetensors index ────────────────────────────────────────────
    print("Step 2: Downloading safetensors index ...")
    idx = get_json(f"{HF_BASE}/model.safetensors.index.json")
    wmap = idx["weight_map"]
    shard_embed = wmap["model.embed_tokens.weight"]  # model-00001-of-00037.safetensors
    shard_lm    = wmap["lm_head.weight"]             # model-00037-of-00037.safetensors
    shard_norm  = wmap["model.norm.weight"]          # model-00037-of-00037.safetensors
    assert shard_lm == shard_norm, "lm_head and norm in different shards — update script"
    print(f"  embed_tokens: {shard_embed}, lm_head+norm: {shard_lm}")

    # ── Step 3: Fetch lm_head rows + norm ───────────────────────────────────
    print("Step 3: Fetching lm_head header from shard 37 ...")
    hdr37, data_off37 = fetch_safetensors_header(shard_lm)

    print("  Fetching lm_head rows for minus/plus tokens ...")
    lm_rows = fetch_safetensors_rows(
        shard_lm, "lm_head.weight",
        [MINUS_TOK, PLUS_TOK], HIDDEN, hdr37, data_off37
    )
    lm_dict = {ridx: vec for ridx, vec in lm_rows}
    u_minus = lm_dict[MINUS_TOK]
    u_plus  = lm_dict[PLUS_TOK]

    print("  Fetching model.norm.weight ...")
    norm_meta = hdr37["model.norm.weight"]
    norm_start = data_off37 + norm_meta["data_offsets"][0]
    norm_end   = data_off37 + norm_meta["data_offsets"][1] - 1
    raw_norm = range_get(f"{HF_BASE}/{shard_norm}", norm_start, norm_end)
    gain = bf16_to_float32(raw_norm)  # shape (HIDDEN,)
    assert len(gain) == HIDDEN

    # ── Step 4: Fetch embed_tokens rows ─────────────────────────────────────
    print("Step 4: Fetching embed_tokens header from shard 01 ...")
    hdr01, data_off01 = fetch_safetensors_header(shard_embed)

    # Sample at least 20,000 rows (or all vocab rows if the shard can provide them)
    # We'll fetch all vocab indices but stream in batches to keep memory low
    SAMPLE_SIZE = min(VOCAB, 25000)
    rng = np.random.default_rng(42)
    # Always include probe toks and interpretable toks
    required = list(set(PROBE_TOKS + list(INTERPRET_TOKS.values())))
    required = [t for t in required if t is not None and t < VOCAB]
    random_sample = rng.choice(VOCAB, size=SAMPLE_SIZE - len(required), replace=False).tolist()
    all_indices = sorted(set(required + random_sample))
    print(f"  Fetching {len(all_indices)} embed rows ...")

    embed_rows = fetch_safetensors_rows(
        shard_embed, "model.embed_tokens.weight",
        all_indices, HIDDEN, hdr01, data_off01
    )
    embed_dict = {ridx: vec for ridx, vec in embed_rows}
    print(f"  Got {len(embed_dict)} embed rows")

    # ── Step 5: Compute diffs ────────────────────────────────────────────────
    print("Step 5: Computing diffs ...")
    diff_dir = u_minus - u_plus  # direction vector (const across tokens)

    diffs_raw  = []
    diffs_norm = []
    for tidx, e in embed_dict.items():
        d_raw  = float(np.dot(diff_dir, e))
        e_norm = rmsnorm(e, gain)
        d_norm = float(np.dot(diff_dir, e_norm))
        diffs_raw.append(d_raw)
        diffs_norm.append(d_norm)

    diffs_raw  = np.array(diffs_raw)
    diffs_norm = np.array(diffs_norm)

    pct_pos_raw  = float(np.mean(diffs_raw  > 0)) * 100
    pct_pos_norm = float(np.mean(diffs_norm > 0)) * 100
    mean_raw,   med_raw  = float(np.mean(diffs_raw)),  float(np.median(diffs_raw))
    mean_norm,  med_norm = float(np.mean(diffs_norm)), float(np.median(diffs_norm))

    # Per-probe-token diffs
    probe_results = {}
    for tid in PROBE_TOKS:
        if tid in embed_dict:
            e = embed_dict[tid]
            probe_results[str(tid)] = {
                "token_str": id_to_tok.get(tid, "?"),
                "diff_raw":  float(np.dot(diff_dir, e)),
                "diff_norm": float(np.dot(diff_dir, rmsnorm(e, gain))),
            }

    # Interpretable token diffs
    interp_results = {}
    for name, tid in INTERPRET_TOKS.items():
        if tid is not None and tid in embed_dict:
            e = embed_dict[tid]
            interp_results[name] = {
                "token_id": tid,
                "token_str": id_to_tok.get(tid, "?"),
                "diff_raw":  float(np.dot(diff_dir, e)),
                "diff_norm": float(np.dot(diff_dir, rmsnorm(e, gain))),
            }

    results.update({
        "vocab_coverage": len(embed_dict),
        "vocab_coverage_pct": round(len(embed_dict) / VOCAB * 100, 2),
        "pct_leaning_minus_raw":  round(pct_pos_raw, 2),
        "pct_leaning_minus_norm": round(pct_pos_norm, 2),
        "mean_diff_raw":    round(mean_raw, 4),
        "median_diff_raw":  round(med_raw,  4),
        "mean_diff_norm":   round(mean_norm, 4),
        "median_diff_norm": round(med_norm,  4),
        "probe_tok_diffs":  probe_results,
        "interpretable_tok_diffs": interp_results,
        "observed_layer0_logit_diff": 4.5,
        "note": "diff = dot(u_minus - u_plus, f(e_t)); positive = lean toward '-'",
    })

    # Verdict
    verdict = (
        "SUPPORTED: embedding geometry alone predicts the − bias for >X% of vocab tokens"
        if pct_pos_norm > 90 else
        "NOT SUPPORTED: the − bias is not a simple property of embedding geometry"
    )
    results["verdict"] = verdict

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {OUTPUT_JSON}")
    print(f"  % leaning − (raw):  {pct_pos_raw:.1f}%")
    print(f"  % leaning − (norm): {pct_pos_norm:.1f}%")
    print(f"  Mean/median diff (norm): {mean_norm:.4f} / {med_norm:.4f}")

if __name__ == "__main__":
    run()
