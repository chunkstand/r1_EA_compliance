# Flathead Reading-Room File Set Blocker Milestone Plan

Date: 2026-05-23
Status: Active blocker packet (`Milestone 0 resolved locally through eb09556; Milestone 1 next when the remaining Flathead reading-room documents are promoted or explicitly excluded with direct evidence`)
Owner context: the `FINAL-Q-FLAT-001` queue family partially overlaps already-promoted Flathead canonical rows, but the remaining public reading-room documents are not yet represented as governed row-level canonical sources

## Purpose

Own the Flathead public reading-room queue placeholder instead of leaving it as
an opaque export-heavy queue row:

- `FINAL-Q-FLAT-001` Flathead 2018 Forest Plan Revision and 1986 Forest Plan
  public reading-room file set

This row cannot be marked `resolved` honestly from current repo state because
the workbook already contains some direct Flathead successors, but the
reading-room family is only partially materialized as canonical rows and the
remaining members are not yet represented as governed row-level sources.

## Latest Local Implementation

Milestone `0` is now resolved locally through commit `eb09556`
(`Open Flathead reading-room blocker packet`).

- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `FINAL-Q-FLAT-001` to this exact packet path and marks it
  `resolution_status="blocked"`.
- `source-register-queue-audit` now fail-closes this blocker the same way it
  fail-closes the project-specific blocker family: the row must point at an
  existing tracked packet under `docs/`.
- Routed docs and handoff surfaces now make the Flathead reading-room boundary
  explicit instead of keeping it inside the generic planned export queue.

## Current Evidence

- The queue row itself is still a file-set placeholder:
  `FINAL-Q-FLAT-001` uses the Flathead planning page URL
  `https://www.fs.usda.gov/r01/flathead/planning/forest-plan`,
  carries `Queue_Reason="Reading-room widget/static page does not expose every direct file row in this environment."`,
  and explicitly requires export plus direct-row promotion before it can leave
  the queue.
- The current canonical workbook already holds a partial Flathead successor
  family sourced from the same reading-room/support context, including
  `FINAL-FLAT-001`, `FINAL-FLAT-002`, `FINAL-FLAT-003`,
  `FINAL-FLAT-006`, `FINAL-FLAT-007`, and `FPS-180` through `FPS-186`.
- The preserved legacy Flathead source-delta register still records additional
  public reading-room documents that do not yet exist as canonical master rows,
  including the Flathead BA/BO family, monitoring/BMER records,
  administrative change, ROD cover letter, and response-to-comments volume.
  The forest-plan-amendments and appendix-map surfaces now also overlap the
  separately routed
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`
  packet because the live `WILD-ESA-Q001` export family carries the same
  mixed Flathead plus NCDE amendment roster.
- Because the current canonical family mixes NFSL mirror links, Federal
  Register notice coverage, and preserved Box-hosted direct links from the
  legacy source-delta register, the remaining work is no longer a simple
  “export the folder and promote everything” batch. It is a governed
  reconciliation boundary.

## Goal

Keep `FINAL-Q-FLAT-001` as an explicit blocked family until the remaining
public reading-room documents are either:

- promoted into `Document_Register_Master` as row-level direct sources; or
- explicitly scoped out with direct evidence and durable rationale.

## Non-Goals

- Do not mark `FINAL-Q-FLAT-001` `resolved` just because some Flathead support
  documents already exist in the canonical workbook.
- Do not duplicate already-promoted Flathead canonical rows under new source
  IDs only to reduce the queue count.
- Do not guess equivalence between legacy Box-hosted file links and current
  NFSL or FS-media mirrors without governed row-level evidence.
- Do not treat the Flathead planning page or reading-room landing page itself
  as a substitute for the missing direct documents.

## Scope

- `FINAL-Q-FLAT-001` blocker routing.
- The queue-resolution ledger reference for that row.
- Routed docs and handoff text that describe the blocker family.
- Future acceptance rules for leaving blocked state.

## Out Of Scope

- Reworking already-admitted Flathead canonical rows that are not needed to
  explain this blocker.
- Solving the remaining Lolo, NPC, ECID Pinyon, or NCDE amendment export
  families in this packet.
- Reopening the historical forest-plan identity-reconciliation packet beyond
  the direct evidence needed to explain this blocker.

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `config/source_register_queue_resolution_ledger_v1.json`
- `config/r1_forest_plan_document_register_draft.csv`
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
  `FINAL-Q-FLAT-001` as a generic planned queue row.
- Any future promotion must point at the actual direct document URL used for
  the canonical row, not merely back to the reading-room landing page.
- If a remaining legacy Flathead document is already materially covered by an
  existing canonical row, record that governed equivalence explicitly before
  closing the blocker.
- If a remaining document cannot be promoted without guessing identity or
  introducing duplicate canonical rows, stop and route the narrower decision
  explicitly.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  a future session marks the Flathead reading-room family resolved because some
  direct rows already exist, while silently leaving the remaining reading-room
  documents uncaptured
- Owner surface:
  queue-resolution ledger, Flathead workbook rows, and routed docs
- Prevention gate:
  `source-register-queue-audit`, direct workbook inspection, and this blocker
  packet
- Fail threshold:
  `FINAL-Q-FLAT-001` leaves blocked state without either explicit successor
  rows for the remaining documents or documented exclusion rationale
- Controlled violation:
  switch `FINAL-Q-FLAT-001` back to generic planned or resolved state without a
  packet or successor rows; the queue audit and doc stack should make the drift
  obvious

### Weak Point 2

- Weak point forecast:
  a future session duplicates already-captured Flathead documents under new
  source IDs instead of reconciling what already exists
- Owner surface:
  workbook row set, legacy Flathead source-delta evidence, and current
  canonical Flathead direct rows
- Prevention gate:
  direct row-by-row review of Flathead successor candidates before promotion,
  plus normal workbook uniqueness and downstream catalog validation
- Fail threshold:
  a new Flathead canonical row is added for a document already represented by
  an existing current canonical row without durable justification
- Controlled violation:
  add a second canonical row for the same Flathead direct document; the slice
  must stop and explain the duplicate rather than silently absorb it

## Milestone Sequence

### Milestone 0 - Blocker Packet Opening

Outcome label: resolved

Goal: replace the generic planned queue state with an explicit Flathead
reading-room blocker.

Implementation tasks:

- create this blocker packet
- update the queue-resolution ledger to reference this packet path
- move `FINAL-Q-FLAT-001` from the generic planned export roster to explicit
  `blocked` status

Acceptance criteria:

- `FINAL-Q-FLAT-001` points to this exact packet path
- the queue audit reports the Flathead reading-room row as a blocked
  current/applicable item rather than a generic unresolved planned item
- routed docs describe the Flathead blocker family explicitly

### Milestone 1 - Governed Successor Capture Or Exclusion

Outcome label: reduced

Goal: reconcile the remaining public Flathead reading-room documents into
canonical row-level truth.

Implementation tasks:

- enumerate the remaining reading-room documents not already represented by
  current canonical rows
- either promote those direct documents into `Document_Register_Master` or
  write explicit document-level exclusion rationale
- update the ledger to leave blocked state only when the remaining roster is
  fully governed

Acceptance criteria:

- the blocker packet lists the remaining Flathead reading-room gap explicitly
- any future exit from blocked state preserves row identity and avoids duplicate
  canonical source rows

## Required Implementation Artifacts

- this blocker packet doc
- updated queue-resolution ledger entry for `FINAL-Q-FLAT-001`
- routed docs and focused tests needed to enforce the blocker state

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`

## Required Verification Gates

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/source_register_queue_resolution.py tests/test_source_register_queue_resolution.py
git diff --check
```

## Stop Conditions

- Stop if the remaining Flathead reading-room documents cannot be matched to
  governed direct canonical rows without guessing equivalence.
- Stop if the only apparent “fix” is to duplicate existing Flathead canonical
  rows under new IDs.
- Stop if future promotion would need a broader workbook naming or family
  policy decision before the remaining documents can be added cleanly.

## Local Commit Closeout Policy

- Commit this blocker-opening slice atomically with the queue ledger, focused
  tests, routed docs, and this blocker packet.
- Do not stage ignored `source_library/` artifacts for this blocker-opening
  slice.
- Treat any future direct-row promotions for the remaining Flathead documents
  as a separate milestone slice.

## Residual Risks And Next Routing

- `FINAL-Q-FLAT-001` remains blocked until the remaining Flathead public
  reading-room documents are governed as row-level canonical sources or
  explicitly excluded.
- The active direct-file queue packet remains the live next route; after this
  blocker-opening slice, continue Milestone `3` on the remaining export-backed
  family `LEX-Q-001`, while the overlapping amendment/map surfaces are now
  explicitly owned by
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md` and the
  mixed Lolo planning-library surfaces are now explicitly owned by
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`, and the NPC
  planning-record surfaces are now explicitly owned by
  `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md`.
