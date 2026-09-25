# O1 / O2 Offline Analysis — Phi-4 Minus Token Variant Stratification

**Date:** 2026-09-14  
**Status:** Complete — outputs ready for pod HARD PRE-CHECK

---

## 1. Variant counts

**Variant inference rule:** inspect `full_input[sign_char_offset - 1]`. Space before sign → token 482 (` -`). Non-space (parenthesis, digit, newline, `=`) → token 12 (`-`). Same logic for plus tokens.  
**Ambiguous cases:** 0 (rule was unambiguous for every case).

| Domain               | tok-12 | tok-482 | plus_12 | plus_482 |
|----------------------|--------|---------|---------|----------|
| det_error (n=61)     | 0      | 55      | 0       | 6        |
| ibp_error (n=40)     | 0      | 40      | 0       | 0        |
| det_correct_deepsign (n=50) | 13 | 26    | 2       | 9        |
| ibp_correct_deepsign (n=50) | 7  | 30    | 0       | 13       |

**Key finding:** Error domains are 100% tok-482 for their minus-sign cases. The tok-12 contamination is entirely in the deepsign correct domains (13/39 minus cases in det, 7/37 in ibp).

---

## 2. How much tok-12 dragged pooled numbers

### deepsign corrects — c2_on_correct condition, α=3 (minus-sign cases only)

| Domain | Stratum | n  | mean Δld (pooled) | mean Δld (stratum) |
|--------|---------|----|--------------------|---------------------|
| det    | POOLED  | 39 | −9.20              | —                   |
| det    | tok-482 | 26 | —                  | **−13.60**          |
| det    | tok-12  | 13 | —                  | −0.40               |
| ibp    | POOLED  | 37 | −18.71             | —                   |
| ibp    | tok-482 | 30 | —                  | **−22.76**          |
| ibp    | tok-12  | 7  | —                  | −1.35               |

**Corrected headline (tok-482 only):** det Δld = −13.6 (was −9.2 pooled); ibp Δld = −22.8 (was −18.7 pooled). The tok-12 stratum dragged the pooled det number down by ~32% and ibp by ~18%.

### expG′ at α=2, L39_mlp (all deepsign minus-sign cases)

| Domain | Stratum | n  | mean Δld |
|--------|---------|-----|---------|
| det    | tok-482 | 24  | −4.18   |
| det    | tok-12  | 11  | −0.35   |
| ibp    | tok-482 | 30  | −8.50   |
| ibp    | tok-12  | 7   | −0.87   |

This confirms the investigation.md claim (Δld ≈ −0.7 on tok-12 vs ≈ −8.5 on tok-482 for ibp L39).

### Error domains (det_error / ibp_error)

No tok-12 contamination. All C2/C4 α=3 numbers reported previously are already 100% tok-482 and do not change.

- det_error C2 α=3: n=51, mean Δld=−8.41, flips=1 (2.0%)
- det_error C4 α=3: n=51, mean Δld=−9.70, flips=2 (3.9%)
- ibp_error C2 α=3: n=40, mean Δld=−14.58, flips=1 (2.5%)
- ibp_error C4 α=3: n=40, mean Δld=−14.28, flips=0 (0%)

---

## 3. Plus token variant issue

Plus token cases: 30 total (det_error: 6, det_correct_deepsign: 11, ibp_correct_deepsign: 13).  
28/30 are space-prefixed (`plus_482`), 2/30 are bare-prefix (`plus_12`) — both in det_correct_deepsign:

- `NC_4x4_det_478`: char before `+` is `1` (in `^{1+2}`)
- `NC_4x4_det_382`: char before `+` is `\n` (line-start plus)

**Verdict:** Plus token has the same two-variant issue but is low-severity (2 cases). The plus token ids must be verified on the pod — they are not recorded in the existing results meta (only `space-prefixed, norm-weighted` is noted for d̂).

---

## 4. Ambiguous cases

None. Every sign offset produced a clear space vs non-space determination.

---

## 5. Summary

Correcting for the tok-12 mismatch in deepsign corrects yields:
- det c2_on_correct: tok-482 mean Δld **−13.6** (pooled was −9.2, a 48% undercount)
- ibp c2_on_correct: tok-482 mean Δld **−22.8** (pooled was −18.7, a 22% undercount)

The error-domain intervention numbers are unaffected (0% tok-12 contamination there). The primary finding — that large leads prevent flips despite large Δld — is unchanged, but the magnitude of the correct-domain specificity signal is meaningfully stronger after stratification.

Variant table and pod spec are ready. The pod HARD PRE-CHECK can proceed once plus token ids are confirmed on the pod.
