# Nez Perce-Clearwater Planning Record Blocker Milestone Plan

Date: 2026-05-23
Status: Active blocker packet (`Milestone 0 resolved locally through 2625aa2; Milestone 1 next when the mixed NPC planning-record library is reconciled document-by-document into governed canonical successors or explicit exclusions`)
Owner context: the `FINAL-Q-NPC-001` queue family points at a large Box planning-record library that overlaps existing canonical NPC plan and SCC rows while also containing extensive FEIS-reference, objection-reference, consultation, amendment, infrastructure, and misc-support folders

## Purpose

Own the Nez Perce-Clearwater planning-record placeholder instead of leaving it
in the generic planned structured-export queue:

- `FINAL-Q-NPC-001` Nez Perce-Clearwater 2025 LMP Planning Record Box file set

This row cannot be marked `resolved` honestly from current repo state because
the live Box planning record is not a single export bundle. It is a multi-page
planning library that already overlaps many governed NPC canonical rows while
also carrying thousands of reference and support materials that are not yet
classified document by document.

## Latest Local Implementation

Milestone `0` is now resolved locally through commit `2625aa2`
(`Open NPC planning-record blocker packet`).

- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `FINAL-Q-NPC-001` to this exact packet path and marks it
  `resolution_status="blocked"`.
- `source-register-queue-audit` now fail-closes this mixed planning-record
  family the same way it fail-closes the Flathead, NCDE, Lolo, and
  project-specific blocker families: the row must point at an existing tracked
  packet under `docs/`.
- Routed docs and handoff surfaces now make the NPC planning-record boundary
  explicit instead of leaving it inside the generic planned structured-export
  roster.

## Current Evidence

- The queue row itself is still a mixed planning-record placeholder:
  `FINAL-Q-NPC-001` uses the public Box share URL
  `https://usfs-public.app.box.com/s/a6tlve91fe1ma9u4hgfggd12oj8xmnwv`,
  carries
  `Queue_Reason="Box planning record cannot be represented as row-level document sources without export."`,
  and explicitly requires export plus direct-row promotion before it can leave
  the queue.
- The live public share is currently titled
  `Nez Perce-Clearwater NFs Forest Plan Revision (44089)` and the current HTML
  payload reports `pageCount=5` with `pageNumber=1`, which already shows at
  least `20` top-level folders.
- The visible top-level folders on the current page already mix core plan
  documents with large support and reference families, including
  `001_LandManagementPlan` (`19` files), `004_FEISreferences` (`1445` files),
  `004b_FEISreferences` (`340` files), `040_ESAconsultation` (`36` files),
  `044_Direction` (`15` files), `066_Infrastructure` (`9` files),
  `075_GBCAsupplementComments` (`426` files), `083_Amendment` (`3` files),
  `090_ObjLtrRefFOC` (`3212` files), and `009_MiscNotes` (`9` files).
- The current canonical workbook already holds overlapping NPC plan-family rows
  from this same planning lane, including `FOR-031`, `FOR-032`, `FOR-033`,
  `FPS-347` through `FPS-373`, and `R1-SCC-NPC-001` through
  `R1-SCC-NPC-005`.
- The queue still separately carries `FPS-376` (`Objections process
  documentation`), whose notes also point back to the NPC 2025 LMP page and
  its plan, FEIS, objection, and planning-record surfaces.
- Because the root planning-record share mixes already-captured canonical NPC
  documents with thousands of objection-reference, FEIS-reference, and support
  files, a blind bulk promotion would either duplicate existing canonical rows
  or bury unresolved support surfaces inside one folder-level placeholder.

## Goal

Keep `FINAL-Q-NPC-001` as an explicit blocked family until the live NPC
planning-record library is governed document by document as one of:

- an already-covered canonical row with explicit equivalence;
- a newly promoted canonical successor row with direct file provenance; or
- an explicit exclusion with durable evidence and rationale.

## Non-Goals

- Do not mark `FINAL-Q-NPC-001` `resolved` just because the Box planning record
  contains some files already represented by current canonical NPC rows.
- Do not bulk-promote every Box file or subfolder as a new canonical source row
  to reduce the queue count.
- Do not treat the Box planning-record page itself as a substitute for the
  actual direct documents.
- Do not duplicate existing NPC plan, FEIS, appendix, consultation, SCC, or
  notice rows without governed document-level equivalence review.

## Scope

- `FINAL-Q-NPC-001` blocker routing.
- The queue-resolution ledger reference for that row.
- Routed docs and handoff text that describe the blocker family.
- Future acceptance rules for leaving blocked state.

## Out Of Scope

- Reworking already-admitted canonical rows that are not needed to explain this
  blocker.
- Solving the remaining ECID/Pinyon export family in this packet.
- Rerunning the full catalog, extraction, retrieval, or promotion pipeline for
  this blocker-opening slice.

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `config/source_register_queue_resolution_ledger_v1.json`
- `src/usfs_r1_ea_sources/source_register_queue_resolution.py`
- `tests/test_source_register_queue_resolution.py`
- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`

## Placement Rules

- The blocker owner stays in a tracked doc under `docs/`; do not leave
  `FINAL-Q-NPC-001` as a generic planned structured-export row.
- Any future promotion must point at the exact direct file URL and preserve the
  workbook successor row identity; do not close the blocker with a folder-level
  citation.
- If a public planning-record file is already materially covered by an existing
  canonical row, record that governed equivalence explicitly before closing the
  blocker.
- If a remaining document cannot be promoted without guessing identity or
  introducing duplicate canonical rows, stop and route the narrower decision
  explicitly.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  a future session bulk-promotes the mixed Box planning record and silently
  creates duplicate NPC canonical rows
- Owner surface:
  queue-resolution ledger, canonical workbook rows, and this blocker packet
- Prevention gate:
  `source-register-queue-audit`, direct workbook inspection, and this blocker
  packet
- Fail threshold:
  `FINAL-Q-NPC-001` leaves blocked state without explicit document-level
  equivalence or successor rows for the overlapping NPC plan-family records
- Controlled violation:
  add a second canonical row for a document already represented by an existing
  NPC canonical row; the slice must stop and explain the duplicate rather than
  silently absorb it

### Weak Point 2

- Weak point forecast:
  the FEIS-reference, objection-reference, consultation, amendment, and misc
  support materials stay hidden inside one mixed planning-record share and
  never get governed explicitly
- Owner surface:
  public Box roster, workbook row set, and this blocker packet
- Prevention gate:
  document-level roster review before any exit from blocked state
- Fail threshold:
  `FINAL-Q-NPC-001` remains the only place where the mixed planning-record
  scope is described and no future slice records which files are covered,
  promoted, or excluded
- Controlled violation:
  close the queue row without a document-by-document disposition table; the
  blocker packet should make that absence obvious

## Milestone Sequence

### Milestone 0 - Blocker Packet Opening

Outcome label: resolved

Goal: replace the generic planned structured-export state with an explicit NPC
planning-record blocker.

Implementation tasks:

- create this blocker packet
- update the queue-resolution ledger to reference this packet path
- move `FINAL-Q-NPC-001` from the generic planned structured-export roster to
  explicit `blocked` status

Acceptance criteria:

- `FINAL-Q-NPC-001` points to this exact packet path
- the queue audit reports the NPC planning-record row as a blocked
  current/applicable item rather than a generic unresolved planned item
- routed docs describe the remaining generic export roster without
  `FINAL-Q-NPC-001`

### Milestone 1 - Document-Level Reconciliation

Outcome label: reduced

Goal: reconcile the mixed NPC planning-record library into governed row-level
truth.

Implementation tasks:

- classify each relevant planning-record file or folder surface as existing
  canonical coverage, new canonical successor, or explicit exclusion
- promote distinct direct documents only when row identity can be governed
  cleanly
- keep high-volume reference and support materials explicit rather than
  silently treating the planning-record share as already closed

Acceptance criteria:

- the blocker packet records the exact planning-record surfaces and their
  document-level dispositions
- any future exit from blocked state preserves row identity and avoids
  duplicate canonical source rows

## Required Implementation Artifacts

- this blocker packet doc
- updated queue-resolution ledger entry for `FINAL-Q-NPC-001`
- routed docs and focused tests needed to enforce the blocker state

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`
- `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`

## Required Verification Gates

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q
PYTHONPATH=src .venv/bin/python -m ruff check tests/test_source_register_queue_resolution.py
git diff --check
```

## Stop Conditions

- Stop if the mixed Box planning record cannot be reconciled without guessing
  equivalence between existing NPC rows and the public share contents.
- Stop if the only apparent fix is to duplicate existing NPC canonical rows
  under new IDs.
- Stop if the high-volume reference or support materials need a broader
  workbook family or source-boundary decision before they can be added cleanly.

## Local Commit Closeout Policy

- Commit this blocker-opening slice atomically with the queue ledger, focused
  tests, routed docs, and this blocker packet.
- Do not stage ignored `source_library/` artifacts for this blocker-opening
  slice.
- Treat any future direct-row promotions or equivalence decisions for the mixed
  planning-record library as a separate milestone slice.

## Residual Risks And Next Routing

- `FINAL-Q-NPC-001` remains blocked until the mixed NPC planning-record
  library is governed document by document.
- The active direct-file queue packet remains the live next route; after this
  blocker-opening slice, continue Milestone `3` on the remaining export-backed
  family `LEX-Q-001`.
