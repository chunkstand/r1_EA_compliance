# Lolo Pinyon File Set Blocker Milestone Plan

Date: 2026-05-23
Status: Active blocker packet (`Milestone 0 resolved locally through 2d7d7c2; Milestone 1 next when the mixed Lolo plan-revision library is reconciled document-by-document into governed canonical successors or explicit exclusions`)
Owner context: the `FINAL-Q-LOLO-001` queue family points at a large mixed Pinyon planning library that overlaps existing canonical Lolo plan and SCC rows while also containing broader assessment, notice, geospatial, and topical support folders

## Purpose

Own the Lolo Pinyon file-set placeholder instead of leaving it in the generic
planned structured-export queue:

- `FINAL-Q-LOLO-001` Lolo Forest Plan Revision Pinyon Public file set

This row cannot be marked `resolved` honestly from current repo state because
the live public Pinyon folder is not a single plan-file export. It is a mixed
planning library that includes already-governed canonical Lolo documents, draft
or process-stage materials, geospatial content, legal notices, and topical
support folders that are not yet classified document by document.

## Latest Local Implementation

Milestone `0` is now resolved locally through commit `2d7d7c2`
(`Open Lolo Pinyon blocker packet`).

- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `FINAL-Q-LOLO-001` to this exact packet path and marks it
  `resolution_status="blocked"`.
- `source-register-queue-audit` now fail-closes this mixed folder family the
  same way it fail-closes the Flathead, NCDE, and project-specific blocker
  families: the row must point at an existing tracked packet under `docs/`.
- Routed docs and handoff surfaces now make the Lolo Pinyon boundary explicit
  instead of leaving it inside the generic planned structured-export roster.

## Current Evidence

- The queue row itself is still a mixed folder placeholder:
  `FINAL-Q-LOLO-001` uses the public Pinyon folder URL
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/174926438550`,
  carries
  `Queue_Reason="Box/Pinyon folder cannot be represented as row-level document sources without export."`,
  and explicitly requires export plus direct-row promotion before it can leave
  the queue.
- The live public folder is currently titled
  `Lolo National Forest Land Management Plan Revision (62960)` and exposes
  `14` top-level folders:
  `Public Engagement`, `Recreation`, `Geospatial Library`,
  `1986 Forest Plan and 2006 Draft`, `RattlesnakeNRA`,
  `2024 ProposedAction and Need to Change`, `Legal Notices`,
  `Vegetation Management`, `Wilderness`, `Wild and Scenic Rivers`,
  `Connectivity`, `Land Allocations`, `2023 Species of Conservation Concern`,
  and `2023 Assessment`.
- The `1986 Forest Plan and 2006 Draft` folder already narrows into
  `1986ForestPlan` and `2006_DraftPlan`, which overlaps existing canonical
  Lolo plan-family rows including `FPS-298`, `FPS-299`, `FPS-300`,
  `FPS-418`, and `FPS-419`.
- The `2023 Species of Conservation Concern` folder currently exposes eight
  files, including the final October 2023 SCC PDFs already represented by
  `FOR-028` and `R1-SCC-LOLO-001` through `R1-SCC-LOLO-004`, plus additional
  June 2023 draft PSCC materials that are not yet classified as current
  canonical rows.
- The `2023 Assessment` folder is itself a mixed subtree containing
  `Revised Assessment_Sept2023`, `Draft Assessment_June2023`, and
  `Assessment Supporting Information`, which is not an atomic direct-file
  promotion surface.
- The `Legal Notices` folder currently exposes four planning notices,
  including Federal Register and local notice PDFs, which are not yet governed
  as explicit canonical successors or exclusions.
- Because the root folder mixes already-captured plan and SCC records with
  broader assessment, legal-notice, geospatial, and topical support folders,
  a blind bulk promotion would either duplicate existing canonical rows or
  force row-level judgments that are not yet explicit in the workbook.

## Goal

Keep `FINAL-Q-LOLO-001` as an explicit blocked family until the live Pinyon
library is governed document by document as one of:

- an already-covered canonical row with explicit equivalence;
- a newly promoted canonical successor row with direct file provenance; or
- an explicit exclusion with durable evidence and rationale.

## Non-Goals

- Do not mark `FINAL-Q-LOLO-001` `resolved` just because the Pinyon folder
  contains some documents already represented by current canonical Lolo rows.
- Do not bulk-promote every Pinyon file or subfolder as a new canonical source
  row to reduce the queue count.
- Do not treat the Pinyon folder page itself as a substitute for the actual
  direct documents or data layers.
- Do not duplicate existing Lolo plan, SCC, monitoring, or administrative
  change rows without governed document-level equivalence review.

## Scope

- `FINAL-Q-LOLO-001` blocker routing.
- The queue-resolution ledger reference for that row.
- Routed docs and handoff text that describe the blocker family.
- Future acceptance rules for leaving blocked state.

## Out Of Scope

- Reworking already-admitted canonical rows that are not needed to explain this
  blocker.
- Solving the remaining NPC or LEX export families in this packet.
- Rerunning the full catalog, extraction, retrieval, or promotion pipeline for
  this blocker-opening slice.

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `config/source_register_queue_resolution_ledger_v1.json`
- `config/r1_forest_plan_identity_reconciliation_v1.json`
- `src/usfs_r1_ea_sources/source_register_queue_resolution.py`
- `tests/test_source_register_queue_resolution.py`
- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`

## Placement Rules

- The blocker owner stays in a tracked doc under `docs/`; do not leave
  `FINAL-Q-LOLO-001` as a generic planned export row.
- Any future promotion must point at the exact direct file URL and preserve the
  workbook successor row identity; do not close the blocker with a folder-level
  citation.
- If a public export file is already materially covered by an existing
  canonical row, record that governed equivalence explicitly before closing the
  blocker.
- If a remaining document cannot be promoted without guessing identity or
  introducing duplicate canonical rows, stop and route the narrower decision
  explicitly.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  a future session bulk-promotes the mixed Pinyon folder and silently creates
  duplicate Lolo canonical rows
- Owner surface:
  queue-resolution ledger, canonical workbook rows, and this blocker packet
- Prevention gate:
  `source-register-queue-audit`, direct workbook inspection, and this blocker
  packet
- Fail threshold:
  `FINAL-Q-LOLO-001` leaves blocked state without explicit document-level
  equivalence or successor rows for the overlapping Lolo plan and SCC records
- Controlled violation:
  add a second canonical row for a document already represented by an existing
  Lolo canonical row; the slice must stop and explain the duplicate rather
  than silently absorb it

### Weak Point 2

- Weak point forecast:
  assessment, legal-notice, geospatial, and topic-support materials stay
  hidden inside one mixed folder and never get governed explicitly
- Owner surface:
  public Pinyon roster, workbook row set, and this blocker packet
- Prevention gate:
  document-level roster review before any exit from blocked state
- Fail threshold:
  `FINAL-Q-LOLO-001` remains the only place where the mixed folder scope is
  described and no future slice records which files are covered, promoted, or
  excluded
- Controlled violation:
  close the queue row without a document-by-document disposition table; the
  blocker packet should make that absence obvious

## Milestone Sequence

### Milestone 0 - Blocker Packet Opening

Outcome label: resolved

Goal: replace the generic planned export state with an explicit Lolo Pinyon
blocker.

Implementation tasks:

- create this blocker packet
- update the queue-resolution ledger to reference this packet path
- move `FINAL-Q-LOLO-001` from the generic planned structured-export roster to
  explicit `blocked` status

Acceptance criteria:

- `FINAL-Q-LOLO-001` points to this exact packet path
- the queue audit reports the Lolo Pinyon row as a blocked current/applicable
  item rather than a generic unresolved planned item
- routed docs describe the remaining generic export roster without
  `FINAL-Q-LOLO-001`

### Milestone 1 - Document-Level Reconciliation

Outcome label: reduced

Goal: reconcile the mixed Lolo plan-revision library into governed row-level
truth.

Implementation tasks:

- classify each relevant Pinyon file or subfolder surface as existing
  canonical coverage, new canonical successor, or explicit exclusion
- promote distinct direct documents only when row identity can be governed
  cleanly
- keep geospatial, draft, and process-stage materials explicit rather than
  silently treating the folder as already closed

Acceptance criteria:

- the blocker packet records the exact planning-library surfaces and their
  document-level dispositions
- any future exit from blocked state preserves row identity and avoids
  duplicate canonical source rows

## Required Implementation Artifacts

- this blocker packet doc
- updated queue-resolution ledger entry for `FINAL-Q-LOLO-001`
- routed docs and focused tests needed to enforce the blocker state

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`
- `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`

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

- Stop if the mixed Pinyon library cannot be reconciled without guessing
  equivalence between existing Lolo rows and the public folder contents.
- Stop if the only apparent fix is to duplicate existing Lolo canonical rows
  under new IDs.
- Stop if the assessment, geospatial, or legal-notice materials need a broader
  workbook family or source-boundary decision before they can be added cleanly.

## Local Commit Closeout Policy

- Commit this blocker-opening slice atomically with the queue ledger, focused
  tests, routed docs, and this blocker packet.
- Do not stage ignored `source_library/` artifacts for this blocker-opening
  slice.
- Treat any future direct-row promotions or equivalence decisions for the mixed
  library as a separate milestone slice.

## Residual Risks And Next Routing

- `FINAL-Q-LOLO-001` remains blocked until the mixed Lolo plan-revision
  library is governed document by document.
- The active direct-file queue packet remains the live next route; after this
  blocker-opening slice, continue Milestone `3` on the remaining export-backed
  family `LEX-Q-001`, while the NPC planning-record surfaces are now
  explicitly owned by
  `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md`.
