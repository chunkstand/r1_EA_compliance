# Project-Specific Public-Private Source Boundary Blocker Milestone Plan

Date: 2026-05-23
Status: Active blocker packet (`Milestone 0 resolved locally through 8b889a9; Milestone 1 next when a concrete project-specific source becomes load-bearing`)
Owner context: project-specific consultation/agreement source rows that cannot be promoted truthfully until a concrete public project file or governed nonpublic citation path exists

## Purpose

Own the three queue placeholders that represent project-specific consultation
or agreement artifacts whose public availability is conditional on the actual
project record:

- `PROG-011` project-specific NHPA programmatic agreement inventory placeholder
- `PROG-012` project-specific ESA programmatic BO inventory placeholder
- `PROG-013` project-specific water-quality agreement inventory placeholder

These rows cannot be promoted as canonical sources from the current workbook
state because they intentionally describe a class of possible project-file
documents rather than a verified public file URL.

## Latest Local Implementation

Milestone `0` is now resolved locally through commit `8b889a9`
(`Open project-specific queue blocker packet`).

- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `PROG-011`, `PROG-012`, and `PROG-013` to this exact packet path and marks
  them `resolution_status="blocked"`.
- `source-register-queue-audit` now fail-closes named blockers unless they
  reference an existing tracked packet under `docs/`, and it reports
  `blocked_current_or_project_applicable_count=3` with the blocker roster
  `["PROG-011", "PROG-012", "PROG-013"]`.
- Routed docs and handoff surfaces now pin this blocker-family opener as the
  current Milestone `3` reduced slice while leaving the export-backed
  families as the next routed work.

## Current Evidence

- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `PROG-011`, `PROG-012`, and `PROG-013` as
  `planned_disposition="named_blocker"` with `resolution_status="blocked"`.
- The workbook queue rows use `manual:` placeholder URLs and explicit notes
  that the direct source row must be added only when the governing project file
  is known and cited.
- `PROG-008` (`National Core BMP Technical Guide`) and `PROG-010`
  (`National Interagency Prescribed Fire Guide`) already prove the canonical
  workbook can hold public, direct programmatic sources when they exist.
- The queue-row notes now make the blocker explicit:
  - `PROG-011`: not all forest/state/tribal PAs or MOAs are public or
    linkable; add the exact row if used.
  - `PROG-012`: specialist report extraction must add the actual BO or
    concurrence source row when cited.
  - `PROG-013`: hydrology extraction must add the actual permit/agreement row
    when cited.
- Promoting these placeholders now would violate the canonical-source rule that
  every master row must carry the actual governing document URL rather than a
  generic class label or manual reminder.

## Goal

Keep these three rows as governed blocked placeholders until a real
project-specific source becomes load-bearing, while making the blocker durable,
discoverable, and machine-checkable.

## Non-Goals

- Do not promote `manual:` placeholder rows into `Document_Register_Master`.
- Do not invent surrogate public sources just to eliminate the queue rows.
- Do not treat a generic program webpage as equivalent to the actual
  project-specific BO, PA/MOA, permit, SWPPP, or agreement used by a review.
- Do not bypass the workbook by keeping the real source only in a review folder
  or one-off notes file.

## Scope

- `PROG-011`, `PROG-012`, and `PROG-013` blocker routing.
- The queue-resolution ledger reference for those rows.
- Routed docs and handoff text that describe the blocker family.
- Future criteria for when these rows may leave blocked state.

## Out Of Scope

- Capturing any specific project-file document in this packet.
- Reworking the broader export-backed queue families.
- Changing already-admitted public programmatic rows outside these three queue
  placeholders.

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

- The blocker owner stays in a tracked doc under `docs/`; do not leave the
  blocker reference as free text in the ledger only.
- If one of these rows becomes load-bearing, the real source must land as a
  direct row in `Document_Register_Master` with the exact file URL, date, and
  provenance-bearing notes.
- If the actual project source is nonpublic, the packet must stop and route the
  decision explicitly instead of pretending a public URL exists.
- Specialist extraction or review-time evidence may trigger promotion only when
  the actual cited document is identified.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  a future session promotes a generic `manual:` placeholder into the master
  sheet just to reduce queue counts
- Owner surface:
  workbook queue rows, queue-resolution ledger, and queue audit
- Prevention gate:
  `source-register-queue-audit`, `source-register-validate`, and focused
  queue-resolution tests
- Fail threshold:
  any blocker row loses its packet reference, stops being clearly blocked, or
  appears in `Document_Register_Master` without an actual file URL
- Controlled violation:
  mutate a blocker reference to a nonexistent packet path and require the audit
  to fail
- Future-Codex misuse scenario:
  replacing a manual placeholder with a generic landing page or keeping the row
  `planned` forever without a blocker owner

### Weak Point 2

- Weak point forecast:
  a later review cites a project-specific BO, PA/MOA, or permit, but the repo
  forgets to convert the placeholder into the actual source row
- Owner surface:
  project review inputs, workbook promotion workflow, and this blocker packet
- Prevention gate:
  project-specific review or extraction work that cites one of these source
  classes must either add the real row or explicitly document why the source is
  unavailable/nonpublic
- Fail threshold:
  a review depends on one of these source classes while the queue row remains a
  placeholder with no traced actual source row
- Controlled violation:
  future project-specific packets must include a negative check that cited
  consultation/agreement artifacts are not left as placeholder-only references
- Future-Codex misuse scenario:
  assuming the placeholder itself is enough because the review mentions a BO or
  agreement generically

## Milestone Sequence

### Milestone 0 - Blocker Packet Opening

Outcome label: resolved

Goal: replace the free-text blocker hint with a real doc-backed packet.

Implementation tasks:

- create this blocker packet
- update the queue-resolution ledger to reference this packet path
- move `PROG-011`, `PROG-012`, and `PROG-013` from generic `planned` queue
  work to explicit `blocked` status

Acceptance criteria:

- the three queue rows point to this exact packet path
- the queue audit reports the rows as blocked current/applicable items rather
  than generic unresolved planned rows
- routed docs can name the blocker family explicitly

### Milestone 1 - Load-Bearing Project Trigger

Outcome label: reduced

Goal: define the exact condition that would let one of these rows leave blocked
state later.

Implementation tasks:

- require a concrete project-specific cited document
- require a public direct file URL before promotion to the master sheet
- stop and route separately if the only governing source is nonpublic

Acceptance criteria:

- the packet makes promotion rules explicit enough that a later session can
  decide between promote, remain blocked, or route nonpublic evidence without
  chat history

## Required Implementation Artifacts

- this blocker packet doc
- updated queue-resolution ledger entries for `PROG-011`, `PROG-012`, and
  `PROG-013`
- queue audit/runtime/test updates needed to enforce doc-backed blocker
  references

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

- Stop if the only available evidence is a generic landing page or manual note.
- Stop if a later slice would need a nonpublic document and no repo policy yet
  authorizes that capture path.
- Stop if a future session tries to collapse these rows into a generic
  “programmatic source” surrogate instead of the actual cited document.

## Local Commit Closeout Policy

- Commit this blocker-opening slice atomically with the queue ledger, queue
  audit, tests, and routed docs.
- Do not stage `source_library/` artifacts for this packet-opening slice.
- Treat any later actual promotion as a separate milestone commit.

## Residual Risks And Next Routing

- These rows remain blocked until a concrete project-specific public document is
  cited and available.
- The active direct-file queue packet remains the live next route; after this
  blocker-opening slice, continue Milestone `3` on the remaining export-backed
  portal families.
