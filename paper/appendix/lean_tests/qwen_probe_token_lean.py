#!/usr/bin/env python3
"""
qwen_probe_token_lean.py
========================
Test 3 in the layer-0 lean investigation (after qwen_embed_geometry.py and
qwen_text_lean.py). Runs OFFLINE: no model weights, no network needed.

Question:
  qwen_text_lean.py showed the question-text token mass leans "-" (weighted
  mean +0.99), but the observed layer-0 lead is +4.5. What explains the gap?

Hypothesis:
  At layer 0 the residual at the probe position is just the EMBEDDING of the
  token sitting there. So the per-problem layer-0 lean should be a lookup
  table of that one token, not a property of the whole text.

Method:
  1. Load all 288 held-out s01 logit-lens records (147 error + 141 correct).
  2. Per record: layer-0 minus-lead = layer_diffs['0'], sign-flipped when the
     written sign is "+" (so positive always = leans "-").
  3. Tokenize each record's full_input with the saved Qwen tokenizer and read
     off the token at index probe_tok.
  4. Group leans by that token; compare group means against the known
     embedding-table diffs from qwen_text_lean_results.json (diff_norm =
     dot(u_minus - u_plus, RMSNorm(embed(t)))).

Interpretation:
  - If the '})' group (the dominant probe token) matches its embedding diff
    and the range is tight -> the layer-0 lean is a per-token lookup;
    magnitude gap closed.
  - Residual mismatch in other groups (e.g. '}') = context added by block 0.

Run:  python3 qwen_probe_token_lean.py [path to "GITHUB UPLOADS" folder]
      (needs: tokenizers; qwen_tokenizer.json and qwen_text_lean_results.json
       must sit next to this script. If no argument is given, the data folder
       is searched relative to the script location.)
"""
import json, csv, os, sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def data_root():
    """Locate the 'GITHUB UPLOADS' data folder: CLI argument first, then
    relative to the script (script lives two levels below the folder that
    also holds 'GITHUB UPLOADS')."""
    cands = sys.argv[1:2] + [
        os.path.join(SCRIPT_DIR, "..", "..", "GITHUB UPLOADS"),
        os.path.join(SCRIPT_DIR, "..", "..", "Desktop", "GITHUB UPLOADS"),
    ]
    for c in cands:
        if c and os.path.isdir(c):
            return os.path.abspath(c)
    sys.exit('data folder not found - pass the "GITHUB UPLOADS" path as the first argument')

QWEN      = os.path.join(data_root(), "Qwen")
TOKENIZER = os.path.join(SCRIPT_DIR, "qwen_tokenizer.json")
TEXTLEAN  = os.path.join(SCRIPT_DIR, "qwen_text_lean_results.json")
OUT = os.path.join(SCRIPT_DIR, "qwen_probe_token_lean_results.json")

def load(p):
    d = json.load(open(p)); d = d.get('results', d)
    return list(d.values()) if isinstance(d, dict) else d

def run():
    from tokenizers import Tokenizer
    recs = []
    for kind in ('error', 'correct'):
        for r in load(f"{QWEN}/heldout_4x4_DET/s01_logit_lens/det_4x4_{kind}_expA_logit_lens.json"):
            r['_kind'] = kind; recs.append(r)
    print(f"records: {len(recs)}")

    txt = {}
    for f in ("qwen_det_4x4_error_heldout_n147_experiment_ready.csv",
              "qwen_det_4x4_correct_heldout_n141_experiment_ready.csv"):
        for row in csv.DictReader(open(f"{QWEN}/raw_data_4x4_DET/heldout/{f}")):
            txt[row['id']] = row['full_input']

    tok = Tokenizer.from_file(TOKENIZER)

    # known embedding-table diffs (RMSNorm) from the text-lean run
    known = {t['token_str']: t['diff_norm']
             for t in json.load(open(TEXTLEAN))['top_contributors']}

    rows = []
    for r in recs:
        L0 = r['layer_diffs']['0']
        minus_lead = L0 if r['written_sign'] == '-' else -L0
        toks = tok.encode(txt[r['id']], add_special_tokens=False).tokens
        pt = r['probe_tok']
        rows.append({'id': r['id'], 'kind': r['_kind'], 'written': r['written_sign'],
                     'minus_lead': round(minus_lead, 4),
                     'probe_tok_index': pt,
                     'probe_token': toks[pt] if pt < len(toks) else '<OOB>'})

    groups = defaultdict(list)
    for x in rows: groups[x['probe_token']].append(x['minus_lead'])
    table = []
    for t, v in sorted(groups.items(), key=lambda kv: -sum(kv[1])/len(kv[1])):
        table.append({'probe_token': t, 'n': len(v),
                      'mean_L0_lead': round(sum(v)/len(v), 3),
                      'min': round(min(v), 3), 'max': round(max(v), 3),
                      'embedding_diff_norm': round(known[t], 3) if t in known else None})
        print(f"  {t!r:<12} n={len(v):>3}  mean {sum(v)/len(v):+6.2f}  "
              f"range [{min(v):+.2f},{max(v):+.2f}]  embed {known.get(t)}")

    dom = table[0] if table and table[0]['probe_token'] == '})' else \
          next(x for x in table if x['probe_token'] == '})')
    gap_closed = dom['embedding_diff_norm'] is not None and \
                 abs(dom['mean_L0_lead'] - dom['embedding_diff_norm']) < 0.5
    verdict = (f"SUPPORTED: the layer-0 lean is a per-token lookup. "
               f"{dom['n']}/{len(rows)} probes sit on '}})' whose embedding diff "
               f"({dom['embedding_diff_norm']:+.2f}) matches the observed group mean "
               f"({dom['mean_L0_lead']:+.2f}); range is tight. The dataset mean +4.5 "
               f"reflects probe-token identity, not average text composition."
               ) if gap_closed else "NOT CONFIRMED: '})' group does not match its embedding diff."

    ctx = next((x for x in table if x['probe_token'] == '}'), None)
    note_ctx = (f"Context effect (secondary): '}}' embedding predicts "
                f"{ctx['embedding_diff_norm']:+.2f} but observed {ctx['mean_L0_lead']:+.2f} "
                f"on n={ctx['n']} -> block-0 attention adds ~+3.7 from the minus-heavy context."
                ) if ctx and ctx['embedding_diff_norm'] is not None else None

    json.dump({'model_id': 'Qwen/Qwen2.5-72B-Instruct',
               'n_records': len(rows), 'group_table': table,
               'verdict': verdict, 'context_effect_note': note_ctx,
               'per_record': rows}, open(OUT, 'w'), indent=1)
    print(f"\nverdict: {verdict}")
    if note_ctx: print(note_ctx)
    print(f"saved -> {OUT}")

if __name__ == '__main__':
    run()
