# Full Canonical Direct-File Capture Queue Resolution Milestone Plan

Date: 2026-05-23
Status: Active packet (`Milestones 0-2 resolved locally through 85f087b; Milestone 3 blocker-family reduction resolved locally through 8b889a9; SCC structured-export Milestone 3 slice resolved locally through e78f491 and docs-aligned through 82e2195; Flathead reading-room blocker slice reduced locally through eb09556; WILD-ESA NCDE amendment blocker slice reduced locally through 3a8dd2d; Lolo Pinyon blocker slice reduced locally through 2d7d7c2; NPC planning-record blocker slice reduced locally; remaining export-backed Milestone 3 slice next`)
Owner context: follow-on from the resolved full-canonical source-truth and compliance-gold
rebaseline packets

## Latest Local Implementation

Milestones `0`, `1`, and `2` are now resolved locally through commit `85f087b`
(`Resolve direct-file queue Milestone 2`). Milestone `3` is now reduced
locally through commit `8b889a9`
(`Open project-specific queue blocker packet`) for the project-specific
blocker-family opening slice, the SCC structured-export slice is now
resolved locally through commit `e78f491`
(`Resolve direct-file queue Milestone 3 SCC exports`) and docs-aligned
through commit `82e2195`
(`Align direct-file queue SCC slice docs`), and the Flathead reading-room
blocker slice is now reduced locally through commit `eb09556`
(`Open Flathead reading-room blocker packet`). The mixed
`WILD-ESA-Q001` NCDE amendment export family is now also reduced locally as an
explicit blocker packet through commit `3a8dd2d`
(`Open WILD-ESA NCDE blocker packet`). The mixed `FINAL-Q-LOLO-001` Lolo
Pinyon family is now also reduced locally as an explicit blocker packet
through commit `2d7d7c2` (`Open Lolo Pinyon blocker packet`). The mixed
`FINAL-Q-NPC-001` Nez Perce-Clearwater planning-record family is now also
reduced locally as an explicit blocker packet.

- `config/source_register_queue_resolution_ledger_v1.json` now enumerates all
  `51` queue rows exactly once with `49` current/project-applicable rows, `2`
  historical/noncurrent rows (`FPS-380`, `SUP-007`), planned disposition
  counts of `37` `promote_direct_file`, `5`
  `promote_structured_export`, `7` `named_blocker`, and `2`
  `historical_scope_only`, plus resolution status counts of `36` `planned`,
  `7` `blocked`, and `8` `resolved`.
- The low-complexity direct-file family now promotes
  `FINAL-Q-HLC-001`, `FINAL-Q-HLC-002`, `FINAL-Q-HLC-003`, and `PROG-010`
  into `Document_Register_Master`.
- The first export-backed Milestone `3` slice now resolves the SCC rationale
  families `R1-SCC-Q-CGNF-RATIONALES`, `R1-SCC-Q-FLAT-RATIONALES`,
  `R1-SCC-Q-HLC-RATIONALES`, and `R1-SCC-Q-NPC-RATIONALES` into nine
  workbook successors:
  `R1-SCC-CGNF-005`, `R1-SCC-CGNF-006`, `R1-SCC-FLAT-005`,
  `R1-SCC-FLAT-006`, `R1-SCC-FLAT-007`, `R1-SCC-HLC-005`,
  `R1-SCC-HLC-006`, `R1-SCC-NPC-004`, and `R1-SCC-NPC-005`.
- Those promotions raise the live full-canonical catalog to
  `source-set-4fb59e9eb43045cb` with `source_count=647`,
  `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  and `status_counts={"downloaded_existing":635,"duplicate_content":12}`.
- Milestone `3` now opens the named blocker family for project-specific
  placeholders: `PROG-011`, `PROG-012`, and `PROG-013` route to
  `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`
  and now carry explicit `blocked` status instead of a free-text ledger hint.
- Milestone `3` now also opens the named blocker family for the Flathead
  reading-room placeholder: `FINAL-Q-FLAT-001` routes to
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md` and now
  carries explicit `blocked` status instead of remaining in the generic
  planned structured-export roster.
- Milestone `3` now also opens the named blocker family for the mixed NCDE
  amendment export placeholder: `WILD-ESA-Q001` routes to
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`
  because the live public export roster crosses overlapping Flathead plan/FEIS
  records, still-missing Flathead appendix-map surfaces, and distinct
  multi-forest NCDE amendment documents.
- Milestone `3` now also opens the named blocker family for the mixed Lolo
  Pinyon placeholder: `FINAL-Q-LOLO-001` routes to
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md` because the live root
  folder is a multi-folder planning library that overlaps existing Lolo plan
  and SCC rows while also carrying assessment, notice, geospatial, and topical
  support surfaces.
- Milestone `3` now also opens the named blocker family for the mixed
  Nez Perce-Clearwater planning-record placeholder: `FINAL-Q-NPC-001` routes
  to `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md`
  because the live Box share is a multi-page planning-record library that
  already overlaps governed NPC plan-family rows while also carrying
  high-volume FEIS-reference, objection-reference, consultation, amendment,
  infrastructure, and misc-support folders.
- `source-register-queue-audit` now provides the machine-checked gate for the
  queue packet and passes with zero missing, unexpected, duplicated, or
  drifted rows, `blocked_current_or_project_applicable_count=7`,
  `unresolved_current_or_project_applicable_count=34`, and the same governed
  historical roster.
- The strengthened extraction/runtime gate now supports governed `.xlsx`
  direct files and distinguishes verified payload-cache reuse from opaque
  text-only reuse. `extraction-accuracy-audit` now admits `594/594`
  active-current rows with `53` explicit archive/currentness rows,
  `authority-currentness` now reports
  `current_authority_source_record_count=594` and
  `authority_family_count=460`, and `retrieval-build` is
  `validation_passed=true` and `reviewer_ready=true`.
- The full-canonical downstream contract intentionally remains split at the
  end of this slice: `promotion-suite` is still pinned to
  `full_canonical_source_set_id=source-set-3f7d4578cafb0704` and now
  truthfully reports `full_canonical_corpus_ready=false` with
  `full_canonical_failure_category_counts={"stale_artifact":2}` until the
  successor source-truth packet reruns the downstream artifacts on
  `source-set-4fb59e9eb43045cb`.
- The next routed slice remains Milestone `3` for the export-backed family
  after the project-specific, Flathead, NCDE, Lolo, and NPC blocker-family
  openers.

## Purpose

Open an explicit owner for the `51` deferred `Direct_File_Capture_Queue` rows so the repo stops
carrying them as a known but ownerless boundary outside the active canonical load-bearing surface.

This packet exists to convert every queue row into one of four governed outcomes without weakening
the already-resolved active-current admission lane, whose current live successor
is `594/594` on `source-set-4fb59e9eb43045cb`:

1. promoted to `Document_Register_Master` with direct document evidence;
2. resolved through structured export and then promoted with file-level provenance;
3. retained only as historical/noncurrent lineage evidence; or
4. carried in a named blocker packet with explicit official-source evidence and stop conditions.

## Current Evidence

- `docs/CURRENT_ROUTING.md` now records the strengthened active source-truth
  lane on `source-set-4fb59e9eb43045cb`, with `594/594`
  `active_review_corpus` rows admitted, `53` explicit archive/currentness
  rows outside verified admission, while also recording that
  `promotion-suite` is still pinned to the older downstream contract on
  `source-set-3f7d4578cafb0704`.
- The same routing file also records that the workbook still carries `51`
  `Direct_File_Capture_Queue` rows by contract, but `8` of them now have
  governed `resolved` promotions, `5` now have explicit blocker ownership,
  and only `36` current/project-applicable rows remain in the generic
  unresolved planned roster.
- `config/source_register_sheet_contract_v1.json` defines `Document_Register_Master` as the only
  load-bearing sheet and `Direct_File_Capture_Queue` as a deferred queue with `emits_load_rows=false`.
- `config/source_register_row_states_v1.json` defines queue rows as
  `deferred_direct_file_queue_row` with `emits_corpus_ready_source=false`.
- `config/direct_file_readiness_contract_v1.json` freezes queue rows as
  `deferred_direct_file_capture` until direct file capture, structured export, or explicit exclusion
  resolves them.
- `src/usfs_r1_ea_sources/source_register_validation.py` already fail-closes the queue contract on
  row counts and `Database_Load` leakage.
- `config/source_register_proving_slice_v1.json` and
  `src/usfs_r1_ea_sources/source_register_proving.py` already exercise five representative queue
  rows in the Phase 1.5 proving slice, so queue resolution can start from an existing governed test
  boundary instead of a blind bulk edit.
- Live workbook census on 2026-05-23 now shows:
  - `51` queue rows total;
  - `49` rows that still classify as current or project-applicable;
  - `8` rows now resolved by governed promotion;
  - `7` rows now explicitly blocked by governed blocker packets:
    `FINAL-Q-FLAT-001` by
    `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`, and
    `WILD-ESA-Q001` by
    `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`, and
    `FINAL-Q-LOLO-001` by
    `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`, and
    `FINAL-Q-NPC-001` by
    `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md`, and
    `3` project-specific rows by
    `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`;
  - `34` current/project-applicable rows still unresolved in the generic
    planned roster;
  - `2` explicitly historical/noncurrent rows: `FPS-380` and `SUP-007`;
  - dominant queue reasons:
    - `21` `Folder/listing/manual-export placeholder`;
    - `10` `Forest plan support row needs direct document file URL`;
    - `4` `Manual/project-record placeholder`;
    - `4` `Placeholder row`;
    - `3` `Specific FEIS volume listed on official page but direct file URL unresolved.`
- `src/usfs_r1_ea_sources/authority_currentness_projection.py` already projects queue rows as
  candidate authority families with `Queue_Reason` plus `Resolution_Required`, which means the repo
  has a runtime surface that can expose queue drift instead of hiding it in workbook-only state.

## Goal

Retire the silent queue boundary by giving every queue row a machine-checkable governed disposition
while preserving current active-corpus truth:

- no current/applicable queue row remains ownerless;
- no queue row is promoted by treating a wrapper page, folder listing, or manual placeholder as a
  canonical direct document;
- the active `594/594` current-admission lane remains green throughout the packet or strengthens
  through governed promotions; and
- any remaining unresolved queue rows are explicit historical lineage or a named blocker packet, not
  an unowned side surface.

## Non-Goals

- Do not reopen the resolved active-current source-truth packet just to restate the current
  `594/594` successor baseline.
- Do not weaken `extraction-accuracy-audit`, `retrieval-build`, `authority-currentness`, or
  `promotion-suite` to make queue work look green.
- Do not admit wrapper pages, JS folders, reading-room placeholders, SCC listing pages, Box/Pinyon
  folders, or manual export stubs as if they were the actual row-level canonical documents.
- Do not broaden this packet into West Reservoir replay repair, base rule-pack reviewer readiness,
  or unrelated package-review work.
- Do not stage ignored `source_library/` outputs unless repository policy changes.

## Scope

- The workbook `Direct_File_Capture_Queue` rows and any promoted replacements in
  `Document_Register_Master`.
- Queue-resolution contracts, validators, reports, and focused tests.
- Targeted preflight/download/catalog/extraction/retrieval checks for rows promoted by this packet.
- Currentness/historical routing for the two noncurrent queue rows.
- Durable routing docs, workbook-audit docs, and the canonical session handoff.

## Out Of Scope

- Reworking already-admitted `Document_Register_Master` rows that are not promoted from the queue.
- Changing the `53` `currentness_supersession_archive` policy from the resolved source-truth packet.
- Replacing the workbook as the source of truth with an ad hoc local spreadsheet, notes file, or
  corpus-only workaround.

## Owner Surfaces

- Workbook:
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Contracts:
  `config/source_register_sheet_contract_v1.json`,
  `config/source_register_row_states_v1.json`,
  `config/direct_file_readiness_contract_v1.json`,
  `config/source_register_proving_slice_v1.json`
- Runtime and validation:
  `src/usfs_r1_ea_sources/source_register.py`,
  `src/usfs_r1_ea_sources/source_register_validation.py`,
  `src/usfs_r1_ea_sources/source_register_proving.py`,
  `src/usfs_r1_ea_sources/authority_currentness_projection.py`
- Tests:
  `tests/test_source_register_schema.py`,
  `tests/test_source_register_proving.py`,
  `tests/test_source_partitions.py`,
  `tests/test_authority_currentness.py`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_retrieval_validation.py`,
  `tests/test_promotion_suite_full_canonical.py`,
  `tests/test_cli.py`,
  `tests/test_architecture_contract.py`
- Docs and routing:
  `README.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`

## Placement Rules

- Keep the workbook as the canonical row-identity surface. Do not create a sidecar spreadsheet that
  becomes the de facto queue source of truth.
- Any new queue-resolution metadata must live in a tracked machine-readable contract under `config/`
  plus focused runtime/tests, not only in prose notes.
- If queue-resolution logic needs new code, prefer a narrow helper or validator module over adding
  more branching to a broad orchestration file.
- Promoted rows must preserve row identity and provenance. If a row moves from queue to master, the
  transition must remain auditable from workbook state plus tracked contract metadata.
- Capture direct URLs from workbook cells, direct exports, or explicit governed resolution artifacts.
  Do not scrape URLs out of free text or use regex heuristics as a promotion shortcut.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  queue rows get promoted by treating placeholders or wrapper pages as if they were direct documents
- Owner surface:
  the workbook, `config/direct_file_readiness_contract_v1.json`,
  `src/usfs_r1_ea_sources/source_register_validation.py`, and
  `tests/test_extraction_accuracy.py`
- Prevention gate:
  `source-register-validate`, focused queue-resolution tests, `extraction-accuracy-audit`, and
  `retrieval-build`
- Fail threshold:
  any row promoted from the queue still resolves to a placeholder URL class, non-file wrapper page,
  or queue-only `Database_Load` state
- Controlled violation:
  a fixture that changes a queue row to `Database_Load=Yes` or leaves a promoted row on a
  placeholder URL must fail the validation/test stack
- Future-Codex misuse scenario:
  a later session copies a queue row into the master sheet without capturing the actual file; the
  gate must fail before commit

### Weak Point 2

- Weak point forecast:
  the queue remains a permanent shadow corpus because rows have no governed disposition beyond
  "known but separate"
- Owner surface:
  the workbook, the queue-resolution contract introduced by this packet, `docs/CURRENT_ROUTING.md`,
  and `docs/SESSION_HANDOFF.md`
- Prevention gate:
  per-row queue disposition audit, `source-register-diff`, stale-reference audit in routing docs,
  and focused tests for missing/duplicate queue-resolution entries
- Fail threshold:
  any current/applicable queue row lacks an explicit governed disposition of promotion, historical
  scoping, exclusion, or named blocker
- Controlled violation:
  a fixture that omits one queue `Source_ID` or duplicates a queue `Source_ID` in the resolution
  contract must fail
- Future-Codex misuse scenario:
  a later session leaves the queue count unchanged while claiming the packet is done; the audit must
  show unchanged unresolved current rows and fail the milestone

### Weak Point 3

- Weak point forecast:
  queue promotions destabilize the already-green active-current source-truth and promotion lanes
- Owner surface:
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/retrieval_runtime.py`,
  `src/usfs_r1_ea_sources/authority_currentness_projection.py`,
  `config/promotion_suite_v1.json`, and the promoted workbook rows
- Prevention gate:
  `authority-currentness`, `extraction-accuracy-audit`, `retrieval-build`, and `promotion-suite`
- Fail threshold:
  the promoted workbook regresses below `594/594` admitted active-current rows, produces a new
  blocked active-current row, or introduces a new full-canonical promotion-suite failure
- Controlled violation:
  a focused fixture that promotes a queue row without valid direct-document evidence must fail
  downstream validation
- Future-Codex misuse scenario:
  a future session broadens admission by selector drift instead of fixing the row; the downstream
  gates must stay fail-closed

### Weak Point 4

- Weak point forecast:
  historical rows get silently promoted as current authority
- Owner surface:
  the workbook currentness fields, `src/usfs_r1_ea_sources/authority_currentness_projection.py`, and
  currentness-focused tests/docs
- Prevention gate:
  queue disposition audit, `authority-currentness`, and focused workbook tests around `FPS-380` and
  `SUP-007`
- Fail threshold:
  either historical row remains current/applicable without explicit lineage scoping, or is promoted
  into `Document_Register_Master` as a current authority row
- Controlled violation:
  a fixture that reclassifies `FPS-380` or `SUP-007` as current/load-ready must fail
- Future-Codex misuse scenario:
  a later session reduces queue count by moving historical rows into master rather than resolving
  current rows; the gate must reject that shortcut

## Milestone Sequence

### Milestone 0 - Freshness Lock And Queue Baseline

Outcome label: resolved

Goal: freeze the live queue baseline before any promotion work starts.

Implementation tasks:

- Re-run `source-register-validate` and `source-register-diff` against the current workbook.
- Create a tracked machine-readable queue-resolution ledger under `config/` that enumerates all `51`
  queue rows with:
  - `Source_ID`;
  - currentness class;
  - queue reason;
  - required resolution pattern;
  - planned disposition (`promote_direct_file`, `promote_structured_export`,
    `historical_scope_only`, `explicit_exclusion`, or `named_blocker`);
  - any target successor row or blocker packet reference.
- Record the live `49` current/project-applicable plus `2` historical split in the ledger and
  matching docs.
- Update any stale docs that still imply the queue is unresolved but ownerless.

Acceptance criteria:

- All `51` queue `Source_ID` values appear exactly once in the ledger.
- `FPS-380` and `SUP-007` are explicitly classified as historical/noncurrent in the ledger.
- No current/applicable queue row has a blank planned disposition.
- The docs route this packet as active follow-on work instead of saying no queue owner exists.

### Milestone 1 - Queue Disposition Audit Gate

Outcome label: resolved

Goal: add a machine-checked gate that proves queue rows are governed rather than tribal knowledge.

Implementation tasks:

- Add a narrow queue-disposition audit surface that reads the workbook plus the new ledger and
  reports:
  - total queue row count;
  - current/applicable unresolved count;
  - historical count;
  - per-disposition counts;
  - any missing, duplicated, or drifted queue rows.
- Wire the audit into focused tests and, if a new CLI command is added, the architecture and CLI
  contract tests.
- Keep the audit small and owned; do not bury it in unrelated reviewer or graph code.

Acceptance criteria:

- The audit fails when a queue row is missing from the ledger, duplicated in the ledger, or marked
  current/applicable without a governed disposition.
- The audit summary exposes the remaining unresolved current/applicable queue count as a durable
  machine-readable signal.
- The queue audit does not weaken or replace the existing `source-register-validate` gate; it adds
  stricter coverage.

### Milestone 2 - Low-Complexity Direct-File Promotions

Outcome label: reduced

Goal: remove the straightforward queue families first without waiting on export-heavy edge cases.

Implementation tasks:

- Resolve rows that already have a clear direct-file path, starting with the dominant low-complexity
  families:
  - forest-plan support rows needing direct document URLs;
  - specific FEIS volume rows with official direct files;
  - placeholder/manual rows where an official file or file list already exists without export-only
    tooling.
- For each promoted row:
  - capture or verify the direct file;
  - update the workbook row state and metadata;
  - preserve provenance fields;
  - run targeted preflight/download and rebuild the relevant catalog/extraction/retrieval surfaces.
- Update the ledger and docs after each promoted family lands.

Acceptance criteria:

- The current/applicable unresolved queue count drops materially below `49`.
- No promoted row still points at a placeholder, folder listing, or wrapper page as the canonical
  source URL.
- Promoted rows pass the existing direct-document admission checks rather than bypassing them.

### Milestone 3 - Export-Backed Families And Named Blockers

Outcome label: reduced

Goal: resolve the remaining export-heavy queue families or narrow them into explicit blocker packets.

Implementation tasks:

- Work the export-heavy families:
  - SCC rationale listings;
  - Box/Pinyon folders and planning records;
  - reading-room widget/static page rows;
  - JS-only folder/listing rows.
- For each row, do exactly one of:
  - promote via governed export to a file-level canonical row;
  - classify as historical/noncurrent lineage only; or
  - open a named blocker packet with official-source evidence, stop conditions, and routing.
- Do not leave any current/applicable row in a generic "queue only" state after this milestone
  claims closeout.

Acceptance criteria:

- Every remaining current/applicable queue row has either a promoted canonical row, an explicit
  exclusion/historical disposition, or a named blocker packet reference.
- The docs and ledger expose the exact remaining unresolved roster instead of a single opaque queue
  count.

### Milestone 4 - Queue Retirement And Downstream Revalidation

Outcome label: resolved

Goal: retire the queue as an ownerless current-work boundary.

Implementation tasks:

- Finish the historical routing for `FPS-380` and `SUP-007`.
- Re-run the full source-truth gate stack after the last promotion/exclusion batch:
  `authority-currentness`, `extraction-accuracy-audit`, `retrieval-build`, and `promotion-suite`.
- Update the routing docs so they no longer describe the queue as an unowned boundary.
- Close this packet only if zero current/applicable queue rows remain without a governed terminal
  disposition.

Acceptance criteria:

- No current/applicable queue row remains outside the canonical target without promotion, explicit
  exclusion, historical scoping, or a named blocker packet.
- The source-truth lane remains green on the active-current `594/594` baseline or an auditable
  stronger successor count after legitimate promotions.
- Routing docs no longer say that the queue is unresolved and ownerless.

## Required Implementation Artifacts

- Updated workbook rows in
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- A tracked queue-resolution contract/ledger under `config/`
- Any new queue audit/validator module plus focused tests
- Updated queue-related workbook audit and routing docs
- If queue rows are promoted, matching catalog/extraction/currentness/retrieval/promotion evidence
  under `source_library/` for local verification only

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`
- `docs/SESSION_HANDOFF.md`
- this milestone plan
- `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md` if queue status text or routing
  summary changes

## Required Verification Gates

Use the smallest gate set that proves the touched slice, then re-run the full source-truth stack
before any milestone that changes workbook row state closes.

Baseline and gate verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_schema.py tests/test_source_register_proving.py tests/test_cli.py -q
git diff --check
```

If a milestone adds queue-resolution runtime code or CLI registration:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_architecture_contract.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src tests
```

If a milestone promotes queue rows into the active corpus:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
```

For any family-specific promotion batch, add targeted `preflight`, `download`, and `catalog-build`
commands with explicit `--id` filters and archived run IDs before closing the milestone.

## Stop Conditions

- Stop if the only way to reduce the queue is to admit wrapper pages, folder listings, or manual
  placeholders as canonical direct documents.
- Stop if a current/applicable row needs private access, non-public evidence, or a policy decision
  that the repo does not already authorize.
- Stop if a proposed queue promotion regresses the active-current admission lane or the full
  canonical promotion-suite gate.
- Stop if row-identity preservation would be lost without a new governed workbook policy.
- Stop if the remaining work becomes a distinct export-only family with different tooling or policy
  needs; open a narrower blocker packet instead of hiding it inside this plan.

## Local Commit Closeout Policy

- Complete one milestone at a time.
- Make one atomic local commit per completed milestone.
- Stage only the workbook/config/code/tests/docs/handoff slice that belongs to that milestone.
- Do not stage ignored `source_library/` artifacts unless repository policy explicitly changes.
- A milestone is not complete until the required verification and doc/handoff updates are in the
  same local commit.

## Residual Risks And Next Routing

- The highest residual-risk families are the export-backed rows that may require Box/Pinyon/SCC or
  reading-room workflow decisions. If those cannot be resolved within this packet, route them into a
  named blocker packet rather than leaving them implicit in the queue.
- West Reservoir remains outside this packet as a separate intentional `typed_blocked` replay
  quarantine.
- Do not reopen the resolved full-canonical source-truth or compliance-gold packets as active work
  unless this queue packet actually changes their governed boundary or downstream counts.
