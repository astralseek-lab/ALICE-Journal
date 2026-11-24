# Intake QA Review Record: ALICE-2026 BCT Batch (0001–0014)

> Translation note (2026-11-24): translated from the Chinese original under
> the Director's public-repo English-only order (Change Order S1-01-049).
> Content is unchanged except that path references follow the English publish
> layout (`docs/intake-qa/`), and the approval line — pending at the time of
> the original review — is completed with its actual outcome.

| Item | Value |
| --- | --- |
| Document ID | Intake-QA-2026-11-24-01 |
| Review date | 2026-11-24 |
| Reviewer | journal-editor (main line) |
| Approver | Director — **approved 2026-11-24**; published in commit `7f1216f` |
| Status | All 10 machine checks passed; one disclosure (§3) |
| Repository | This repo (ALICE-Journal, public projection) |

## 1. Scope and process

Intake object: fourteen new task-package directories `ALICE-2026-0001/` …
`ALICE-2026-0014/` in the staging tree, plus the accompanying
`publish_manifest.json` update. Unit files total **518 / 27,352,265 bytes**;
unit-projection tree_hash =
`085a104ded9215dbe000729cbb57d0d311f70e6e18a042d65c23e4474a2e3440`.

This document itself enters the manifest through the projector's whitelist
channel (publish_face v0.3.0+; English publish path since v0.3.2) and is
guarded by CI like every other file. **The whole-tree file count and
tree_hash are authoritative only as recorded in `publish_manifest.json`**
(this document's own content affects the tree hash, so no self-inclusive
hash is quoted here).

Intake process (this document is produced by it):

1. the reviewer runs the machine checklist in §2 against the staging tree
   and records concrete evidence per item;
2. every finding is disclosed in §3 as-is, never smoothed over;
3. when all machine checks pass and every disclosure has a ruling basis,
   the batch goes to the Director for approval;
4. only after the Director's approval may the repo be committed and pushed.

## 2. Machine checklist (10 items, all passed)

| # | Check | Method | Result | Evidence |
| --- | --- | --- | --- | --- |
| A1 | Projection integrity | projector `--check` full recomputation on the staging tree | PASS | files=518; per-file sha256 + size recomputed identical; tree_hash recomputed identical |
| A2 | Files outside the manifest | CI-guard-equivalent simulation: walk the whole tree; any file not in the manifest and not a repo-level meta file fails | PASS | extra files = 0 |
| A3 | Forbidden-item scan | lexical path scan of the whole tree: `.pdf` / `fulltext__*.xml` / `esm1.docx` / `_check` / `__pycache__` / `_tmp` / `.pyc` | PASS | zero hits (Director's ruling ② of 2026-11-24: publisher originals are not published; `_check` never goes public by internal red line) |
| A4 | Guard-word rescan | independent rerun of guard rules over all text files (FATAL: absolute paths / loopback addresses / internal appellations; WARN: internal role words / suspected keys) | PASS | FATAL=0, WARN=0 |
| A5 | Per-file hash recomputation | recompute sha256 and byte size for every listed file | PASS | 518/518 identical |
| A6 | Source spot-check (10%) | seed 20261124, 51 files sampled; published bytes vs controlled-tree source bytes | PASS | 51/51 byte-identical; normalized files this round = 0 (no difference between published and source bytes) |
| A7 | Per-unit mandatory files | all 14 units checked for `SHA256SUMS.txt` and `paper_text.txt` | PASS | 14/14 present; `profile.json` tolerated for legacy trees (present in 5 units, absent in 9, per the v24 retirement note) |
| A8 | Unit SUMS forward verification | parse each unit's `SHA256SUMS.txt`; recompute every listed row against the staging tree | 8 units fully pass; 6 units have 9 rows pointing to unpublished files | details in §3 D-1 — disclosure, not a blocker |
| A9 | Unit SUMS reverse verification | every published file (except SUMS itself) must be covered by its unit SUMS | PASS | 14/14 units, zero omissions |
| A10 | Per-file size cap | projector enforces ≤ 5 MB per file | PASS | all 518 files within the cap |

Also verified: all 14 units' per-unit gates were re-run green immediately
before this intake (units 0002/0003 had their gate-red repairs recorded in
Change Order S1-01-046; both went fully green under `gate --all` before
joining this batch).

## 3. Disclosures

### D-1 Nine unit-SUMS rows point to files excluded from publication (non-blocking)

Each unit's `SHA256SUMS.txt` is the close-time hash ledger of the unit's
**complete** file set, which is larger than the published subset. Nine rows
point to files that do not enter the public repo by the Director's rulings
or by internal red line; a reader checking the public tree row by row will
find these 9 rows unverifiable because their files are absent:

| Unit | Row points to | Basis for exclusion |
| --- | --- | --- |
| ALICE-2026-0001 | `fulltext__PMC10427801.xml` | publisher full-text XML, Director's ruling ② 2026-11-24 |
| ALICE-2026-0005 | `pkg-A/_check/report.json` | `_check` never goes public (internal red line) |
| ALICE-2026-0011 | `fulltext__PMC7786424.xml` | publisher full-text XML, ruling ② |
| ALICE-2026-0012 | `fulltext__PMC11170071.xml`, `paper.pdf` | publisher originals, ruling ② |
| ALICE-2026-0013 | `fulltext__PMC12596556.xml`, `paper.pdf` | publisher originals, ruling ② |
| ALICE-2026-0014 | `esm1.docx`, `fulltext.pdf` | publisher originals, ruling ② |

Disposition: unit SUMS are projected as closed (the projection never
rewrites unit files; bytes are faithful). The authoritative whole-tree
integrity evidence for the public repo is `publish_manifest.json`
(CI recomputes every file); unit SUMS are supplementary per-unit evidence.
**Reverse verification passed 14/14 (A9)** — every file in this repo is
checkable against its unit SUMS.

### D-2 This document's own hash

This document is listed in `publish_manifest.json`; its sha256 is whatever
the manifest records. No self-hash is embedded here.

## 4. Conclusion and approval

All 10 machine checks passed; the single finding (D-1) is the necessary
consequence of the Director's rulings and the internal red line, with a
precise basis and a bounded scope (9 rows, 6 units), disclosed as-is.
Review conclusion: **pass — submitted for approval.**

- journal-editor (main line): machine review executed, evidence per §2, 2026-11-24.
- Director: **approved 2026-11-24**; committed and pushed by journal-editor
  (public commit `7f1216f`); CI recomputes the whole tree on every push.

## 5. How to re-verify (publicly reproducible)

1. **Whole tree**: CI recomputes every listed file's sha256 / byte size and
   the tree_hash on each push, and rejects any file outside the manifest;
2. **Single file**: hash any downloaded file with sha256 and compare,
   character by character, with its `sha256` entry in
   `publish_manifest.json`;
3. **Per unit**: use the unit's `SHA256SUMS.txt` to verify the unit's files
   in this repo (except the 9 rows listed in D-1, whose targets are not
   published).
