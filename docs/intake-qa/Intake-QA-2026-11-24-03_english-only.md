# Intake QA Review Record: Public-Repo English-Only Migration

| Item | Value |
| --- | --- |
| Document ID | Intake-QA-2026-11-24-03 |
| Review date | 2026-11-24 |
| Reviewer | journal-editor (main line) |
| Approver | Director (**pending**) |
| Status | All 6 machine checks passed; no new disclosures; awaiting approval before push |
| Repository | This repo (ALICE-Journal, public projection) |
| Related | Intake-QA-2026-11-24-01 / -02; Change Order S1-01-049 |

## 1. Scope

The Director's order of 2026-11-24: **the public repo goes all-English.**
Scope, as ruled by the Director on scan evidence (1,751 CJK characters in
repo-level documents; 283 frozen unit files with ≈53,000 CJK characters):

- **In scope**: repo-level documents — the two intake-QA records are
  translated into English; publish paths migrate from the former Chinese
  prefix to `docs/intake-qa/*.md`); `README.md` is already
  English. From the next unit onward, all public-facing unit materials are
  English at birth.
- **Out of scope (grandfathered)**: the 14 published units' frozen files —
  they are close-time evidence under their own `SHA256SUMS.txt`; editing
  them for language alone would touch frozen evidence, so they remain
  as published. Translation at projection time (diverging published bytes
  from source bytes) was ruled out permanently: it would break byte
  fidelity and hash verifiability.

This intake therefore adds/moves **repo-level files only**:

1. `docs/intake-qa/Intake-QA-2026-11-24-01_BCT-batch.md` (translated;
   approval outcome completed — approved 2026-11-24, published `7f1216f`);
2. `docs/intake-qa/Intake-QA-2026-11-24-02_public-README.md` (translated;
   approved 2026-11-24, published `7b70015`);
3. this document.

## 2. Machine checklist (6 items, all passed)

| # | Check | Method | Result | Evidence |
| --- | --- | --- | --- | --- |
| C1 | English-only repo level | CJK scan of `README.md` and `docs/**` | PASS | zero CJK characters |
| C2 | ASCII paths | every path in `publish_manifest.json` must be pure ASCII | PASS | all 521 paths ASCII; old Chinese paths pruned by the build |
| C3 | Zero unit-file drift | 518 unit entries vs the previous published commit (`7b70015`) | PASS | path / bytes / sha256 all equal, zero added or changed |
| C4 | Projection integrity | projector `--check` full recomputation | PASS | per-file sha256 + size identical; tree_hash recomputed identical |
| C5 | Guard rescan | FATAL / WARN rescan of the three English repo-level documents | PASS | FATAL=0, WARN=0 |
| C6 | Link validity | in-repo links in `README.md` and `docs/**` resolve | PASS | 14 unit links match the manifest units set; no dead links |

## 3. Disclosures

None new. Disclosure D-1 of Intake-QA-2026-11-24-01 continues to apply and
is restated in its English translation.

One factual note for readers: the 14 published units' task packages contain
Chinese in human-readable materials (package READMEs, code comments, claim
annotations — ≈53,000 characters in 283 files). These files are close-time
evidence and remain as produced (see §1). New units are English at birth
from the next unit onward.

## 4. Conclusion and approval

All 6 machine checks passed; no new disclosures. Review conclusion:
**pass — submitted for approval.**

- journal-editor (main line): machine review executed, evidence per §2, 2026-11-24.
- Director: **(pending)** — on approval, journal-editor commits and pushes;
  CI recomputes the whole tree on push.

## 5. How to re-verify

Same as Intake-QA-2026-11-24-01 §5. The English-only property can be
spot-checked by browsing `docs/` and by the ASCII-only file paths in
`publish_manifest.json`.
