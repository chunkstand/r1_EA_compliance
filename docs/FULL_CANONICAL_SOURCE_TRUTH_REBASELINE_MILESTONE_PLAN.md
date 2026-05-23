# Full Canonical Source Truth Rebaseline Milestone Plan

Date: 2026-05-23

Status: Resolved locally; Milestone 0 resolved on 2026-05-22 through the
routed-doc packet open, Milestone 1 is resolved locally, and Milestone 2 is
resolved locally: the checked-in verified-admission contract has been
rebaselined from the hidden `343`-row shadow-filtered subset to all `581`
active-current canonical rows via
`canonical-source-register-active-current-admission`, the live `FSH 2509.18`
transmittal now lands as a direct PDF, governed currentness lineage retains
`USFS-026` as `currentness_supersession_archive` evidence with replacement
`USFS-023`, and the refreshed `extraction-accuracy-audit`,
`authority-currentness`, and `retrieval-build` replays now agree on `581`
admitted out of `581` required active-current rows with `validation_passed=true`,
`reviewer_ready=true`, and `families_requiring_milestone_2_source_currentness=0`.
Milestone 3 now resolves the archive boundary explicitly: the checked-in
verified-admission contract declares the `53`
`currentness_supersession_archive` rows as governed full-canonical lineage
outside the active verified-admission roster, the refreshed
`extraction-accuracy-audit` now records `53`
`explicitly_non_admitted_source_record_ids`, `authority-currentness` records
`47` `currentness_archive_only` rows plus `6`
`replacement_source_confirmed` rows, `retrieval-build` records
`verified_extraction_explicitly_non_admitted_source_count=53`, and the
refreshed `promotion-suite` again reports
`full_canonical_corpus_ready=true` with `10/10` required full-canonical
results passing. The downstream compliance-gold rebaseline is now also
resolved locally, and the refreshed default `promotion-suite` now reports
`current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
`expansion_ready=true`, and `promotion_ready=true`. The downstream claim
refresh now records `claim_count=124458` and `source_record_count=539`, and
that closeout landed in commit `8e0e02b`
(`Resolve full canonical compliance gold rebaseline`).
`FPS-344` stays admitted as a structured Federal Register XML source, `9`
handbook wrapper rows admit through live National Directives contents PDFs,
and `12` manual wrapper rows admit through live USDA guidance or current
Forest Service static-file PDF targets. The Milestone 3 closeout commit is
`93a23b0` (`Resolve source-truth archive boundary rebaseline`).
The latest recorded Milestone 2
reduced local commit is `53d59da` (`Reduce source-truth Milestone 2 manual
redirect blockers`); the earlier Milestone 2 reduced manual-wrapper slice
remains `96450be` (`Reduce source-truth Milestone 2 manual wrapper
blockers`); the earlier Milestone 2 reduced handbook slice remains `4650837`
(`Reduce source-truth Milestone 2 handbook wrapper blockers`), and the
earlier Milestone 2 reduced slice remains `806cdf1` (`Reduce source-truth
Milestone 2 blockers`). Milestone 1 closeout commit: `46bff61` (`Resolve
source-truth rebaseline Milestone 1`).

Successor note: the queue Milestone `2` follow-on now promotes four direct-file
queue rows into live full-canonical source set `source-set-3f7d4578cafb0704`,
raising the active catalog to `638` extracted rows and `585` admitted
active-current rows while keeping the same `53` explicit archive/currentness
rows. The queue Milestone `2` closeout commit is `85f087b`
(`Resolve direct-file queue Milestone 2`). Older `634/581` references below
remain the historical closeout baseline for commit `93a23b0` unless a later
bullet explicitly updates them.

Owner context: on 2026-05-22 the governing intent was clarified: the newest imported source set
must fully replace the older source set as the canonical source of truth for this repository's
Region 1 NEPA review and document-generation system. Every applicable law, regulation, policy,
directive, forest-plan authority, and necessary support source must either land in the canonical
verified set or be explicitly classified as historical, removed-not-applicable, or still blocked by
named direct-file capture work. This packet closes the remaining archive-boundary contract gap for
the active canonical corpus.

## Purpose

Rebaseline the repo's definition of "full canonical" so the newest source set, its verified
admission boundary, and its downstream reviewer gates measure the intended full Region 1 NEPA source
truth instead of the older `343`-row active-review subset.

## Current Evidence

- `source_library/derived/source-set-f775524ab233ff27/diagnostics/summary.json` currently records
  `selected_source_count=634`, `required_extraction_source_count=634`, `extracted_count=634`,
  `failed_count=0`, and `validation_passed=true`.
- `source_library/derived/source-set-f775524ab233ff27/diagnostics/extraction_validation.json`
  currently records `all_required_rows_extracted=true`, `failed_source_record_ids=[]`, and
  `status_counts={"extracted": 634}`.
- The checked-in `config/verified_extraction_admission_contract.json` now defines
  `canonical-source-register-active-current-admission`, which selects every
  `source_register_v1` row already classified into
  `source_partitions=["active_review_corpus"]` with
  `artifact_is_proving_placeholder=false`, and it now also declares
  `source_partitions=["currentness_supersession_archive"]` as explicit governed
  non-admitted lineage rows; the old `docling_instructions_not_contains`
  shadow filter is removed.
- The latest
  `source_library/derived/source-set-f775524ab233ff27/retrieval/summary.json`
  now records `verified_extraction_admitted_source_count=581`,
  `verified_extraction_required_source_count=581`,
  `verified_extraction_explicitly_non_admitted_source_count=53`, and
  `verified_extraction_contract_ids=["canonical-source-register-active-current-admission"]`.
- The latest
  `source_library/derived/source-set-f775524ab233ff27/diagnostics/extraction_accuracy_audit.json`
  now records `audited_record_count=581`,
  `knowledge_base_admitted_source_record_ids=581`,
  `knowledge_base_blocked_source_record_ids=0`,
  `explicitly_non_admitted_source_record_ids=53`, and no failed gates.
- The latest
  `source_library/derived/source-set-f775524ab233ff27/retrieval/retrieval_validation.json`
  now derives the same truthful zero-blocker roster under the rebaselined
  contract.
- The latest
  `source_library/derived/source-set-f775524ab233ff27/authority_currentness/authority_currentness_report.json`
  now records `families_requiring_milestone_2_source_currentness=0`,
  `catalog_source_partition_counts={"active_review_corpus":581,"currentness_supersession_archive":53}`,
  `source_currentness_counts={"confirmed_from_catalog":581,"currentness_archive_only":47,"replacement_source_confirmed":6}`,
  `current_authority_source_record_count=581`, and `validation_passed=true`.
- The latest `promotion-suite` result at
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  now records `full_canonical_corpus_ready=true`,
  `passed_required_full_canonical_result_count=9`,
  `required_full_canonical_result_count=9`, and
  `full_canonical_failure_category_counts={}`. After the downstream
  compliance-gold closeout, the same default result now also records
  `current_promotion_ready=true`, `expansion_ready=true`, and
  `promotion_ready=true`.
- `FPS-344` now remains admissible as a structured Federal Register XML source
  because the generic listing-page direct-file instruction no longer upgrades
  authoritative structured-web rows into the direct-document bucket without a
  stronger row signal.
- `9` handbook wrappers now admit through the live National Directives
  contents-page path:
  `USFS-008`, `USFS-013`, `USFS-014`, `USFS-017`, `USFS-025`, `USFS-028`,
  `USFS-032`, `USFS-035`, and `USFS-037`.
- `12` manual wrappers now admit through live USDA guidance or current Forest
  Service static-file PDF targets:
  `USFS-007`, `USFS-015`, `USFS-016`, `USFS-019`, `USFS-022`, `USFS-023`,
  `USFS-029`, `USFS-033`, `USFS-034`, `USFS-039`, `USFS-018`, and `USFS-024`.
- `USFS-026` (`FSH 2509.18`) is no longer an active-current blocker; the
  servicewide transmittal removes the handbook from the directive system and
  incorporates the direction into `FSM 2550`, so the row is now retained only
  as governed currentness lineage evidence with replacement `USFS-023`.
- `README.md`, `AGENTS.md`, and the current workbook contract now define
  `Document_Register_Master=638` as the active load-bearing table while
  `Direct_File_Capture_Queue=51` remains a deferred non-load surface.
- Workbook queue census on 2026-05-23 still shows all `51`
  `Direct_File_Capture_Queue` rows preserved for audit lineage; `49` classify
  as current or project-applicable, `4` are now governed `resolved`
  promotions, `45` current/project-applicable rows remain unresolved, and `2`
  are explicitly historical/noncurrent (`FPS-380` and `SUP-007`).
- `config/direct_file_readiness_contract_v1.json` still records queue status `phase0_freeze` and
  defines queue rows as non-load until direct-file promotion or explicit exclusion.
- `config/source_register_queue_resolution_ledger_v1.json` and
  `source-register-queue-audit` now lock the queue roster to a governed
  Milestone `2` state with `resolution_status_counts={"planned":47,"resolved":4}`,
  `unresolved_current_or_project_applicable_count=45`, and the same `2`
  governed historical rows.
- `tests/test_extraction_accuracy.py` already proves the fail-closed negative case:
  wrapper pages are not admissible when a row requires a direct document artifact.
- The downstream packet
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md` remains
  live and is now aligned to the explicit active-current-plus-archive canonical
  boundary above.

## Goal

Encode and prove the intended full-canonical Region 1 NEPA source truth in the repo so that:

1. the newest source set fully replaces the older source set as the active canonical corpus;
2. the verified-admission contract targets every applicable canonical row, not only the current
   `343`-row subset;
3. any row outside verified admission is explicit governed lineage
   (`Removed_Not_Applicable_Final`, historical/archive-only, or named blocked direct-file work),
   not a silent permanent exclusion surface; and
4. downstream retrieval, claim, graph, review, compliance, and promotion lanes can truthfully say
   whether the full canonical Region 1 source set is admitted.

## Non-Goals

- Do not claim downstream `compliance-gold-eval` is fixed by only changing verified-admission
  scope.
- Do not silently admit wrapper pages, listing pages, folder pages, or manual-export placeholders as
  if they were direct documents.
- Do not mutate `source_library/` artifacts or rerun large network capture by default unless the
  executing milestone explicitly requires it.
- Do not weaken existing wrapper/direct-document negative tests, direct-extraction requirements, or
  admission audits just to make the count grow.
- Do not silently broaden the canonical target to historical or non-applicable rows without an
  explicit workbook/currentness decision.

## Scope

- Canonical-source intent lock for the newest imported source set.
- Verified-admission contract semantics and contract-ID routing.
- Workbook-side status of `Document_Register_Master`, `Direct_File_Capture_Queue`,
  `Removed_Not_Applicable_Final`, and `currentness_supersession_archive` rows.
- Direct-file promotion or explicit exclusion path for applicable queue and wrapper-bound rows.
- Downstream reruns required to prove the rebaselined target count and blocked-row roster.

## Out Of Scope

- Fixing every downstream gold/compliance finding in this packet.
- Broad architecture refactors unrelated to source-register, admission, currentness, or queue
  boundaries.
- Reopening preserved legacy workbook comparison surfaces except where they are needed to prove the
  canonical replacement boundary.

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `config/verified_extraction_admission_contract.json`
- `config/direct_file_readiness_contract_v1.json`
- `config/source_register_sheet_contract_v1.json`
- `config/source_register_schema_v1.json`
- `config/source_register_row_states_v1.json`
- `config/source_register_currentness_lineage_v1.json`
- `src/usfs_r1_ea_sources/source_register.py`
- `src/usfs_r1_ea_sources/source_register_validation.py`
- `src/usfs_r1_ea_sources/extraction_admission.py`
- `src/usfs_r1_ea_sources/extraction_accuracy.py`
- `src/usfs_r1_ea_sources/retrieval.py`
- `src/usfs_r1_ea_sources/retrieval_validation.py`
- `src/usfs_r1_ea_sources/authority_currentness.py`
- `tests/test_source_register_schema.py`
- `tests/test_source_register_loader.py`
- `tests/test_source_partitions.py`
- `tests/test_catalog.py`
- `tests/test_extract.py`
- `tests/test_extraction_accuracy.py`
- `tests/test_retrieval_validation.py`
- `tests/test_authority_currentness.py`
- `tests/test_upstream_evaluation.py`
- `tests/test_architecture_contract.py`
- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`

## Placement Rules

- Keep canonical scope and row-state truth in the workbook plus governed config contracts; do not
  introduce hidden runtime allowlists or one-off Python-side inclusion hacks.
- Keep direct-document admissibility enforcement in extraction/retrieval audit surfaces; do not
  bypass wrapper-page failures in downstream review or compliance code.
- If instruction-based exclusions remain temporarily, they must be paired with explicit governed
  row-state or blocker artifacts. Do not leave wording-only shadow exclusions as the long-term
  canonical contract.
- Any queue promotion must preserve workbook row identity, provenance, hashes, and currentness
  lineage rather than replacing rows ad hoc in runtime code.
- Do not stage `source_library/` outputs unless the repository policy changes or the user explicitly
  requests it; treat those artifacts as local verification evidence.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  a widened verified-admission selector simply unions every extracted row and silently admits
  wrapper/manual-placeholder artifacts as if they were direct documents
- owner surface:
  `config/verified_extraction_admission_contract.json`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_upstream_evaluation.py`
- prevention gate:
  `extraction-accuracy-audit`, `upstream-eval`, and focused wrapper-negative tests
- fail threshold:
  any `direct_document_artifact_required` row is admitted through a wrapper/listing/manual-export
  artifact, or the wrapper-negative tests are loosened or removed
- controlled violation:
  keep the existing wrapper-page negative fixture failing closed when a direct document is required
- future-Codex misuse scenario:
  a future session deletes the current `docling_instructions_not_contains` filters without promoting
  the real direct files; the audit must still block admission

### Weak Point 2

- Weak point forecast:
  `Direct_File_Capture_Queue` remains a permanent shadow corpus outside the claimed canonical source
  truth
- owner surface:
  the workbook, `config/direct_file_readiness_contract_v1.json`,
  `src/usfs_r1_ea_sources/source_register.py`, and `docs/CURRENT_SYSTEM_STATE.md`
- prevention gate:
  workbook queue census, `source-register-validate`, `source-register-diff`, and explicit routed
  promotion/exclusion accounting
- fail threshold:
  any current/applicable queue row remains outside the canonical target without a governed
  promotion, explicit exclusion, or named blocker packet
- controlled violation:
  fail the milestone if a queue row is still only `No - direct file capture queue only` after the
  packet claims full-canonical readiness
- future-Codex misuse scenario:
  a future session keeps the queue as "known but separate" while still claiming the full Region 1
  corpus is canonical

### Weak Point 3

- Weak point forecast:
  historical/archive rows are mixed into current reviewer truth without explicit lineage or
  historical scoping
- owner surface:
  `config/source_register_currentness_lineage_v1.json`,
  `src/usfs_r1_ea_sources/authority_currentness.py`,
  `tests/test_authority_currentness.py`,
  and `docs/CURRENT_SYSTEM_STATE.md`
- prevention gate:
  `authority-currentness`, `tests/test_source_partitions.py`, and updated currentness/source-partition
  docs
- fail threshold:
  archive/historical rows are admitted or excluded without explicit currentness reasoning and
  durable documentation
- controlled violation:
  fail the milestone if `currentness_supersession_archive` rows are silently folded into the same
  current-review target without a lineage decision
- future-Codex misuse scenario:
  a future session uses one flat "all rows" selector and loses the current-vs-historical boundary

### Weak Point 4

- Weak point forecast:
  docs, runtime, and generated summaries disagree about what the full-canonical target count
  actually is
- owner surface:
  `README.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, `config/verified_extraction_admission_contract.json`,
  and the live retrieval/extraction summaries
- prevention gate:
  targeted route/contract greps, fresh extraction/retrieval summary checks, and `git diff --check`
- fail threshold:
  routed docs still claim the active target is `343` after the rebaseline contract changes, or the
  docs claim a larger target count that the live summaries do not prove
- controlled violation:
  fail the milestone if the contract ID or required count changes but routing/current-state docs do
  not
- future-Codex misuse scenario:
  a future session fixes runtime counts but forgets to reroute the operator docs

### Weak Point 5

- Weak point forecast:
  downstream gold/compliance work continues against the stale `343`-row admission boundary and
  hides the real source-truth mismatch
- owner surface:
  `docs/CURRENT_ROUTING.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`,
  and the live retrieval summary
- prevention gate:
  routing docs must keep this packet as the root active lane until the verified-admission target is
  rebaselined and replayed
- fail threshold:
  the repo routes back to the downstream gold packet before the canonical target and blocker roster
  are explicit
- controlled violation:
  fail the milestone if the routed packet changes without a completed admission replay and updated
  docs
- future-Codex misuse scenario:
  a future session treats the gold packet as primary because it is visible, even though the source
  target is still underspecified

## Milestone Sequence

### Milestone 0 - Freshness Lock And Target Census

Outcome label: `resolved`

1. Re-read the live workbook contract, verified-admission contract, extraction manifest, extraction
   audit summary, retrieval summary, and queue census against the active local catalog.
2. Record the exact target mismatch in durable docs:
   imported/extracted load-bearing count,
   currently admitted count,
   queue count,
   active exclusion families,
   and whether the final full-canonical target is still `634` or must grow after queue promotion.
3. Reroute the repo's short current route away from the downstream gold packet and onto this packet.

### Milestone 1 - Admission Contract Rebaseline

Outcome label: `resolved`

Current worktree checkpoint on 2026-05-23:

- The checked-in live contract is now
  `canonical-source-register-active-current-admission`.
- Focused regression coverage is green:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_extraction_accuracy.py -q`.
- The refreshed `extraction-accuracy-audit` now records `582` audited
  active-current rows, `559` admitted rows, and `23` blocked rows under the
  new contract.
- The refreshed retrieval replay on `source-set-f775524ab233ff27` now records
  the same `582` required active-current rows, `559` admitted rows, and `23`
  blocked rows.
- The Milestone 1 closeout commit is
  `46bff61` (`Resolve source-truth rebaseline Milestone 1`).

1. Replace the current `canonical-source-register-active-review-admission` live target with a new
   full-canonical admission contract that reflects the intended Region 1 source truth.
2. Remove or narrow wording-only shadow exclusions so every still-excluded family is represented by
   explicit row-state, workbook, or blocker truth.
3. Re-run `extraction-accuracy-audit` and `retrieval-build` to produce the first truthful
   full-canonical required-count and blocked-row roster under the new contract.
4. Record the new contract ID, required-count delta, and blocker families in durable docs.

### Milestone 2 - Applicable Current-Row Promotion Or Exclusion

Outcome label: `resolved locally`

Current worktree checkpoint on 2026-05-23:

- The latest recorded reduced-slice closeout commit before this local
  resolution is `53d59da`
  (`Reduce source-truth Milestone 2 manual redirect blockers`).
- The earlier local reduced-slice closeout commit is
  `96450be` (`Reduce source-truth Milestone 2 manual wrapper blockers`).
- The earlier Milestone 2 reduced handbook slice remains
  `4650837` (`Reduce source-truth Milestone 2 handbook wrapper blockers`).
- The earlier Milestone 2 reduced slice remains
  `806cdf1` (`Reduce source-truth Milestone 2 blockers`).
- `FPS-344` is now back in the admitted set as a structured Federal Register
  XML source after the direct-document requirement stopped overfiring on its
  generic listing-page instruction clause.
- A follow-on handbook-wrapper slice now adapts legacy `fsh` wrapper URLs
  through the current National Directives contents pages and admits
  `USFS-008`, `USFS-013`, `USFS-014`, `USFS-017`, `USFS-025`, `USFS-028`,
  `USFS-032`, `USFS-035`, and `USFS-037` as direct-document rows.
- A follow-on manual-wrapper slice now adapts live-verified `fsm` codes to
  direct USDA guidance PDFs and admits `USFS-007`, `USFS-015`, `USFS-016`,
  `USFS-019`, `USFS-022`, `USFS-023`, `USFS-029`, `USFS-033`, `USFS-034`, and
  `USFS-039` as direct-document rows.
- The current worktree now further admits `USFS-018` (`FSM 2410`) and
  `USFS-024` (`FSM 2580`) through live current official Forest Service
  static-file PDFs exposed by the current directive surfaces.
- The current worktree now captures the live `FSH 2509.18` transmittal PDF,
  projects governed lineage metadata for `USFS-026`, and retains the row only
  as `currentness_supersession_archive` evidence with replacement `USFS-023`
  because the transmittal removes the handbook from the directive system and
  incorporates the direction into `FSM 2550`.
- The refreshed `extraction-accuracy-audit` and `retrieval-build` replays now
  agree on `581` required active-current rows, `581` admitted rows, `0`
  blocked rows, `validation_passed=true`, and `reviewer_ready=true`.
- The refreshed `authority-currentness` report now records
  `families_requiring_milestone_2_source_currentness=0`, so this milestone no
  longer carries an open active-current owner family.

1. Resolve the currently excluded active-review families
   (`0` remaining directives-wrapper blockers) by
   promoting direct files, converting queue placeholders into real canonical rows, or moving rows
   into explicit historical/not-applicable lineage where the evidence proves they do not belong in
   the canonical target.
2. For any queue-backed source family, make the workbook and config surfaces carry the truth instead
   of leaving it as an implicit deferred queue.
3. Keep direct-document negative gates intact while the blocker roster shrinks.

### Milestone 3 - Archive And Historical Boundary Closure

Outcome label: `resolved`

1. The `53` `currentness_supersession_archive` rows now land as a mixed
   full-canonical boundary: they remain searchable lineage/currentness evidence
   inside the active canonical source set, but they are explicitly outside the
   verified-admission roster.
2. `config/verified_extraction_admission_contract.json` now carries explicit
   `non_admitted_record_selectors` for the archive partition, and the focused
   extraction/promotion regressions prove the boundary instead of relying on
   selector omission.
3. The refreshed currentness and partition gates remain green with
   `581` active-current authority rows, `53` archive rows,
   `47` archive-only lineage rows, and `6` replacement-source lineage rows.

### Milestone 4 - Full Verified-Admission Replay

Outcome label: `resolved`

1. Refresh the active source set as needed after workbook/config changes.
2. Re-run `catalog-build`, `extract-build`, `extraction-accuracy-audit`, `authority-currentness`,
   and `retrieval-build` on the active canonical source set.
3. Prove that the verified-admission required count now equals the intended full-canonical target
   count and that every remaining non-admitted row is an explicit governed exclusion or named
   blocker.

### Milestone 5 - Downstream Route Rebase And Closeout

Outcome label: `resolved`

1. Update `README.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
   `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`, this plan, and
   `docs/SESSION_HANDOFF.md`.
2. Record the closeout source-set ID, target count, admitted count, blocker count, and the exact
   downstream packet that owns any remaining gold/compliance work.
3. Commit the verified slice atomically and route the repo back to the downstream packet only after
   this packet's full-canonical target is proven.

## Required Implementation Artifacts

- Updated workbook row states and/or promotions in
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Updated `config/verified_extraction_admission_contract.json` with the live full-canonical
  admission contract
- Updated `config/direct_file_readiness_contract_v1.json` and any related row-state/currentness
  contracts needed to remove shadow exclusions
- Fresh local
  `source_library/derived/<source_set_id>/diagnostics/extraction_accuracy_audit.json`
  proving the rebaselined audited set
- Fresh local `source_library/derived/<source_set_id>/retrieval/summary.json`
  proving the rebaselined required/admitted counts
- If the source set changes, fresh local
  `source_library/catalog/source_set_manifest.json`,
  `source_library/catalog/source_catalog.jsonl`,
  and `source_library/catalog/review_sources.sqlite`

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`
- this plan file
- `docs/SESSION_HANDOFF.md`

## Required Verification Gates

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx

PYTHONPATH=src python -m usfs_r1_ea_sources source-register-diff \
  --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --legacy-register config/r1_forest_plan_document_register_draft.csv \
  --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx

PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval \
  --manifest config/upstream_evaluation_v1.json \
  --results-dir source_library/evaluations/upstream

PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --batch-run-id <batch-run-id>

PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library

PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library

PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness \
  --output-dir source_library \
  --source-set-id <active-source-set-id>

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library \
  --source-set-id <active-source-set-id>

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_cli.py \
  tests/test_cli_derived.py \
  tests/test_source_register_schema.py \
  tests/test_source_register_loader.py \
  tests/test_source_partitions.py \
  tests/test_catalog.py \
  tests/test_extract.py \
  tests/test_extraction_accuracy.py \
  tests/test_retrieval_validation.py \
  tests/test_authority_currentness.py \
  tests/test_upstream_evaluation.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Acceptance Criteria

- The repo's routed packet is this plan until the full-canonical target is proven.
- The live canonical target count is explicit and durable:
  imported load-bearing count,
  queue count,
  historical/not-applicable exclusions,
  and final verified-admission target count are all documented and agree with runtime artifacts.
- `retrieval/summary.json` no longer reports the old `343`-row active-review contract as the live
  full-canonical target.
- `extraction-accuracy-audit` and `retrieval-build` agree on the full-canonical required/admitted
  roster after the contract rebaseline.
- No applicable current row remains outside the canonical target solely because of an implicit
  wording filter or a permanent deferred-queue convention.
- Wrapper/manual-placeholder negatives still fail closed whenever a direct document artifact is
  required.
- Any row still outside verified admission is explicit governed lineage or a named blocker with an
  owner packet.

## Stop Conditions

- Stop if the only way to raise admission counts is to treat wrapper pages or manual placeholders as
  admissible direct documents.
- Stop if current/applicable queue rows cannot be promoted, excluded, or historically scoped without
  a separate policy decision; open a narrower decision packet instead of inventing scope in code.
- Stop if the packet requires large fresh network capture or corpus rebuild work that the user has
  not approved for the current slice.
- Stop if a proposed contract change would make docs/runtime disagree about the full-canonical
  target count.
- Stop if downstream gold/compliance debugging resumes before the full-canonical admission boundary
  is rebaselined and replayed.

## Local Commit Closeout Policy

- Close each milestone with one local atomic commit after the milestone's verification passes.
- Stage only the verified milestone slice.
- Leave unrelated dirty or untracked files alone.
- Include implementation, tests, docs, and handoff updates for that milestone in the same commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat a verified but uncommitted milestone as ready-to-close, not complete.
- Do not stage `source_library/` unless the repository policy changes or the user explicitly
  requests it.

## Residual Risks And Next Milestone Routing

- The active source-truth packet is now closed locally. The remaining `51`
  queue rows stay explicit non-load workbook contract work rather than hidden
  full-canonical admission debt.
- The downstream packet
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md` is now the
  next active lane after this packet's explicit archive-boundary closeout.
- If the rebaseline proves some queue or archive rows are truly outside the final canonical source
  truth, that decision must be explicit in the workbook/currentness contracts and durable docs
  rather than preserved as an implicit operational convention.
