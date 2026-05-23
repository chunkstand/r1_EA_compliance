# NCDE Grizzly Bear Amendment Export Blocker Milestone Plan

Date: 2026-05-23
Status: Active blocker packet (`Milestone 0 resolved locally; Milestone 1 next when the mixed Flathead and multi-forest NCDE amendment roster is reconciled document-by-document into governed canonical successors or explicit exclusions`)
Owner context: the `WILD-ESA-Q001` queue family spans overlapping Flathead plan/FEIS documents, still-missing Flathead map appendices, and distinct multi-forest NCDE grizzly-bear amendment documents, so it is not an honest one-shot structured-export promotion

## Purpose

Own the NCDE amendment export placeholder instead of leaving it in the generic
planned structured-export queue:

- `WILD-ESA-Q001` FNF Plan Revision and NCDE Grizzly Bear Conservation
  Strategy Forest Plan Amendments - direct document export

This row cannot be marked `resolved` honestly from current repo state because
the live public Pinyon/Box folder mixes:

- Flathead documents that already partially overlap existing canonical rows;
- Flathead documents that are still missing from the canonical workbook; and
- distinct multi-forest NCDE amendment documents for the Flathead, Lolo,
  Helena-Lewis and Clark, and Kootenai National Forests.

## Latest Local Implementation

Milestone `0` is now resolved locally in the current slice.

- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `WILD-ESA-Q001` to this exact packet path and marks it
  `resolution_status="blocked"`.
- `source-register-queue-audit` now fail-closes this mixed export family the
  same way it fail-closes the Flathead and project-specific blocker families:
  the row must point at an existing tracked packet under `docs/`.
- Routed docs and handoff surfaces now make the NCDE amendment export boundary
  explicit instead of leaving it inside the generic planned structured-export
  roster.

## Current Evidence

- The queue row itself is still a mixed export placeholder:
  `WILD-ESA-Q001` uses the Flathead archive project page URL
  `https://www.fs.usda.gov/r01/flathead/projects/archive/46286`,
  carries `Queue_Reason="Non-load source placeholder"`, and explicitly
  requires export plus direct-row promotion before it can leave the queue.
- The official Forest Service archive page points to the public Pinyon/Box
  folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158194435235`,
  currently titled
  `FNF Plan Revision & NCDE GBCS Amendment to the Lolo, Helena, Lewis & Clark,and Kootenai NFs (46286)`.
- That live public folder currently exposes the exact nine-file roster below:
  - `Forest Plan / Final Forest Plan / 2018 Land Management Plan for the Flathead National Forest.pdf`
  - `Decision / ROD NCDE Grizzly Bear Forest Plan Amendments.pdf`
  - `Decision / Flathead FEIS Land Mgt Plan Final ROD.pdf`
  - `Analysis / FEIS / Volume 4 FEIS Flathead 2018 Land Mgt Plan without Appendix1Maps.pdf`
  - `Analysis / FEIS / Volume 4 FEIS Flathead 2018 Land Mgt Plan Appendix 1 Part 2 Figures 1-40 to 1-81.pdf`
  - `Analysis / FEIS / Volume 4 FEIS Flathead 2018 Land Mgt Plan Appendix 1 Part 1 Figures 1-1 to 1-39.pdf`
  - `Analysis / FEIS / Volume 3 FEIS NCDE Grizzly Bear Amendments.pdf`
  - `Analysis / FEIS / Volume 2 FEIS Flathead 2018 LandMgtPlan.pdf`
  - `Analysis / FEIS / Volume 1 FEIS Flathead 2018 LandMgtPlan.pdf`
- The current canonical workbook already holds overlapping Flathead successors
  from the same family, including `FINAL-FLAT-001`, `FINAL-FLAT-002`,
  `FINAL-FLAT-003`, `FINAL-FLAT-004`, `FINAL-FLAT-005`, `FINAL-FLAT-006`,
  `FINAL-FLAT-007`, and `FPS-180` through `FPS-186`.
- Direct workbook inspection shows that the canonical master does not yet
  contain rows titled:
  `ROD NCDE Grizzly Bear Forest Plan Amendments`,
  `Volume 3 FEIS NCDE Grizzly Bear Amendments`,
  `Appendix 1 Part 1`, or `Appendix 1 Part 2`.
- Because one public export family crosses both the active
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md` boundary and
  distinct multi-forest NCDE amendment documents, a blind batch promotion
  would either guess equivalence for already-captured Flathead records or
  introduce duplicate canonical rows.

## Goal

Keep `WILD-ESA-Q001` as an explicit blocked family until every document in the
public export roster is governed as one of:

- an already-covered canonical row with explicit equivalence;
- a newly promoted canonical successor row with direct file provenance; or
- an explicit exclusion with durable evidence and rationale.

## Non-Goals

- Do not mark `WILD-ESA-Q001` `resolved` just because the export folder
  contains some documents that resemble current Flathead canonical rows.
- Do not bulk-promote every Box file as a new canonical source row to reduce
  the queue count.
- Do not treat the Forest Service project page or the Pinyon/Box folder page
  itself as a substitute for the actual direct documents.
- Do not duplicate Flathead plan, ROD, or FEIS rows without governed
  document-level equivalence review.

## Scope

- `WILD-ESA-Q001` blocker routing.
- The queue-resolution ledger reference for that row.
- Routed docs and handoff text that describe the blocker family.
- Overlap notes with the Flathead reading-room blocker packet.
- Future acceptance rules for leaving blocked state.

## Out Of Scope

- Reworking already-admitted canonical rows that are not needed to explain this
  blocker.
- Solving the remaining Lolo, NPC, or ECID/Pinyon export families in this
  packet.
- Rerunning the full catalog, extraction, retrieval, or promotion pipeline for
  this blocker-opening slice.

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `config/source_register_queue_resolution_ledger_v1.json`
- `config/r1_forest_plan_document_register_draft.csv`
- `src/usfs_r1_ea_sources/source_register_queue_resolution.py`
- `tests/test_source_register_queue_resolution.py`
- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`

## Placement Rules

- The blocker owner stays in a tracked doc under `docs/`; do not leave
  `WILD-ESA-Q001` as a generic planned export row.
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
  a future session bulk-promotes the mixed export folder and silently creates
  duplicate Flathead canonical rows
- Owner surface:
  queue-resolution ledger, canonical workbook rows, and this blocker packet
- Prevention gate:
  `source-register-queue-audit`, direct workbook inspection, and this blocker
  packet
- Fail threshold:
  `WILD-ESA-Q001` leaves blocked state without explicit document-level
  equivalence or successor rows for the overlapping Flathead documents
- Controlled violation:
  add a second canonical row for a document already represented by an existing
  Flathead canonical row; the slice must stop and explain the duplicate rather
  than silently absorb it

### Weak Point 2

- Weak point forecast:
  the NCDE-specific amendment documents and Flathead appendix-map surfaces stay
  hidden inside one mixed placeholder and never get routed to real owners
- Owner surface:
  public Box roster, workbook row set, and the Flathead plus NCDE blocker
  packets
- Prevention gate:
  document-level roster review before any exit from blocked state
- Fail threshold:
  `WILD-ESA-Q001` remains the only place where the mixed roster is described
  and no future slice records which files are covered, promoted, or excluded
- Controlled violation:
  close the queue row without a document-by-document disposition table; the
  blocker packet should make that absence obvious

## Milestone Sequence

### Milestone 0 - Blocker Packet Opening

Outcome label: resolved

Goal: replace the generic planned export state with an explicit NCDE amendment
blocker.

Implementation tasks:

- create this blocker packet
- update the queue-resolution ledger to reference this packet path
- move `WILD-ESA-Q001` from the generic planned structured-export roster to
  explicit `blocked` status

Acceptance criteria:

- `WILD-ESA-Q001` points to this exact packet path
- the queue audit reports the NCDE amendment row as a blocked
  current/applicable item rather than a generic unresolved planned item
- routed docs describe the remaining generic export roster without
  `WILD-ESA-Q001`

### Milestone 1 - Document-Level Reconciliation

Outcome label: reduced

Goal: reconcile the mixed NCDE amendment export roster into governed row-level
truth.

Implementation tasks:

- classify each public export file as existing canonical coverage, new
  canonical successor, or explicit exclusion
- promote distinct NCDE amendment documents and any missing Flathead documents
  only when row identity can be governed cleanly
- coordinate with the Flathead blocker packet so overlapping map and FEIS
  surfaces are not owned twice

Acceptance criteria:

- the blocker packet records the exact public export roster and its
  document-level dispositions
- any future exit from blocked state preserves row identity and avoids
  duplicate canonical source rows

## Required Implementation Artifacts

- this blocker packet doc
- updated queue-resolution ledger entry for `WILD-ESA-Q001`
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

- Stop if the mixed export roster cannot be reconciled without guessing
  equivalence between existing Flathead rows and the public Box files.
- Stop if the only apparent fix is to duplicate existing Flathead canonical
  rows under new IDs.
- Stop if the NCDE amendment documents need a broader workbook family or
  multi-forest ownership decision before they can be added cleanly.

## Local Commit Closeout Policy

- Commit this blocker-opening slice atomically with the queue ledger, focused
  tests, routed docs, and this blocker packet.
- Do not stage ignored `source_library/` artifacts for this blocker-opening
  slice.
- Treat any future direct-row promotions or equivalence decisions for the mixed
  roster as a separate milestone slice.

## Residual Risks And Next Routing

- `WILD-ESA-Q001` remains blocked until the mixed Flathead and multi-forest
  NCDE amendment export roster is governed document by document.
- The active direct-file queue packet remains the live next route; after this
  blocker-opening slice, continue Milestone `3` on the remaining export-backed
  families `FINAL-Q-LOLO-001`, `FINAL-Q-NPC-001`, and `LEX-Q-001`.
