# Intake QA Review Record: Public-Face README Addition

> Translation note (2026-11-24): translated from the Chinese original under
> the Director's public-repo English-only order (Change Order S1-01-049).
> Content is unchanged except that path references follow the English
> publish layout (`docs/intake-qa/`), and the approval line — pending at the
> time of the original review — is completed with its actual outcome.

| Item | Value |
| --- | --- |
| Document ID | Intake-QA-2026-11-24-02 |
| Review date | 2026-11-24 |
| Reviewer | journal-editor (main line) |
| Approver | Director — **approved 2026-11-24**; published in commit `7b70015` |
| Status | All 8 machine checks passed; no new disclosures |
| Repository | This repo (ALICE-Journal, public projection) |
| Related | Intake-QA-2026-11-24-01 (batch 0001–0014); Change Orders S1-01-047 / 048 / 049 |

## 1. Scope

An **extra-file addition** (journal-editor hard constraint 7 covers this
case), adding 2 files:

1. `README.md` (repo root): the public-face directory tree — grouped by
   research area, with clickable links straight into each
   `ALICE-2026-xxxx` folder. The authoritative source lives in the
   controlled tree under its own (Chinese) path — retained unrenamed by the
   append-only record-keeping rule — and is projected to the repo root via
   publish_face v0.3.1 path mapping (Change Order S1-01-048). Restructured and fully English by the
   Director's own hand (2026-11-24), then polished and translated by
   journal-editor — structure and editorial choices are the Director's.
2. This document (`docs/intake-qa/Intake-QA-2026-11-24-02_public-README.md`
   in the publish layout).

The 518 unit files are **untouched** (check B6). Whole-tree file count and
tree_hash are authoritative only as recorded in `publish_manifest.json`.

## 2. Machine checklist (8 items, all passed)

| # | Check | Method | Result | Evidence |
| --- | --- | --- | --- | --- |
| B1 | Projection integrity | projector `--check` full recomputation | PASS | per-file sha256 + size identical; tree_hash recomputed identical |
| B2 | Files outside the manifest | CI-guard-equivalent simulation | PASS | extra files = 0 |
| B3 | Forbidden-item scan | lexical path scan of the whole tree (same criteria as check A3 of record 01) | PASS | zero hits |
| B4 | Guard-word rescan | full-text FATAL / WARN rescan of the README and this document | PASS | FATAL=0, WARN=0 |
| B5 | Per-file hash recomputation | every listed file recomputed | PASS | 521/521 identical |
| B6 | Zero unit-file drift | new manifest's 518 unit entries vs the previous published commit (`7f1216f`/`7b70015`) | PASS | path / bytes / sha256 all equal, zero added or changed |
| B7 | README link validity | parse all README links; in-repo relative targets must exist (external links excluded) | PASS | all 14 unit-directory links hit and match the manifest units set exactly |
| B8 | Annotation-to-artifact | every filename mentioned in the README (`*.owl` / `*.csv` / `*.xlsx` in backticks) must exist in that unit's directory | PASS | all hit, no fabricated annotations |

## 3. Disclosures

None new. The nine unit-SUMS rows pointing to unpublished files (record 01,
§3 D-1) continue to apply, and the README discloses the same to readers.

## 4. Conclusion and approval

All 8 machine checks passed; no new disclosures.
Review conclusion: **pass — submitted for approval.**

- journal-editor (main line): machine review executed, evidence per §2, 2026-11-24.
- Director: **approved 2026-11-24**; committed and pushed by journal-editor
  (public commit `7b70015`).

## 5. How to re-verify

Same as Intake-QA-2026-11-24-01 §5: CI whole-tree recomputation, per-file
sha256 comparison, per-unit `SHA256SUMS.txt` checks. README link validity
can be exercised by clicking through on the repo page.

## 6. Revision note (2026-11-24, pre-approval)

The README draft was restructured by the Director: lean structure (one-line
intro / per-package contents / how to use / directory tree), a new
"How to use" section (copy a folder link and send it to ALICE at
https://astralseek.bio/), and full English. Polishing and translation were
executed by journal-editor; structure and editorial choices remain the
Director's. The B-series checks were re-run on the revised version and all
B1–B8 still passed (B7 criterion clarified: external links are excluded
from in-repo verification). This document's B7 evidence row was updated
accordingly; all other conclusions are unchanged.
