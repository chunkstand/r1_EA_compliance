# Full Canonical Final Blocker Resolution Milestone Plan

Date: 2026-05-19
Status: Active 2026-05-19; Milestone 0 resolved 2026-05-19
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` active full-canonical final-blocker boundary

## Purpose

The canonical source-register import and downstream-freshness reduction packets have already made
`source-set-cac9c7d02b280825` the active local full-canonical source set and have narrowed the
remaining red surface to two source rows plus four blocked downstream artifacts. This milestone
exists to finish that last bounded lane so the repo can truthfully claim a green full canonical
corpus on the active source set instead of a merely current-promotion-ready corpus.

## Current Evidence

- `source_library/derived/source-set-cac9c7d02b280825/diagnostics/summary.json` currently records
  `extracted_count=633`,
  `failed_count=2`,
  `chunk_count=97248`,
  `validation_passed=false`, and
  `failure_counts={"docling_conversion_failed": 1, "pdf_text_fallback_empty": 1}`.
- The exact residual extraction blockers are
  `FPS-005` (`docling_conversion_failed`) and
  `FPS-125` (`pdf_text_fallback_empty`).
- `FPS-125` has already exercised the current reduced raster path in
  `src/usfs_r1_ea_sources/extract.py`: `100` DPI rasterization, classifier-disabled
  `RapidOCR(torch)`, bounded `4`-worker page pool, and fail-closed page-error behavior. Focused
  extractor coverage is already green at `30/30`, but the latest targeted merged replay still
  remained compute-bound after rendering all `346` raster pages and did not write a merged
  extracted record.
- `FPS-005` is not currently a local parser-tuning problem. Fresh upstream redownloads reproduce
  the same invalid xref/pages corruption, and local `pypdf` salvage still fails even with
  `strict=False` because the file cannot reconstruct a root catalog.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  currently reports
  `current_promotion_ready=true`,
  `promotion_ready=true`,
  `expansion_ready=true`,
  `full_canonical_corpus_ready=false`,
  `passed_required_full_canonical_result_count=4`,
  `required_full_canonical_result_count=8`, and
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2, "stale_artifact": 2}`.
- The exact remaining failed required full-canonical slots are:
  `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/nepa_3d_graph_validation.json`,
  `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/nepa_3d_graph_summary.json`,
  `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json`, and
  `source_library/evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_results.json`.
- Milestone 0 rebaseline was closed on `2026-05-19` with no baseline drift. The live
  `extraction_manifest.jsonl`, `source_catalog.jsonl`, workbook rows `FPS-005` and `FPS-125`, and
  `promotion_suite_results.json` all still match the blocker and failed-slot truth above on active
  source set `source-set-cac9c7d02b280825`.
- `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` already agree that
  the remaining work is this exact two-row blocker lane plus the four downstream reruns above.

## Goal

Reach a truthful green full-canonical closeout for active source set `source-set-cac9c7d02b280825`
by:

- clearing `FPS-125` and `FPS-005` from the active extraction blocker set through governed
  recovery or contract action,
- rerunning the exact four blocked downstream artifact families on the active source set, and
- closing the repo with `full_canonical_corpus_ready=true` and `8/8` required full-canonical
  results passing.

## Non-Goals

- Do not weaken or bypass the stale-artifact and missing-artifact gates just to make
  `promotion-suite` green.
- Do not mass-relabeled preserved historical review fixtures, West Reservoir artifacts, or the
  reviewer-ready East Crazies lane to the active full-canonical source set without replay proof.
- Do not mutate `source_library/` by hand outside the existing catalog/extraction/eval command
  paths.
- Do not silently substitute a different Beaverhead artifact for `FPS-005` unless the workbook row,
  title, URL, and provenance are updated to match the actual governing source.
- Do not route canonical source-register URL repair through `config/url_overrides.toml`; under
  `source_register_v1`, repaired active URLs must live in the workbook contract itself.

## Scope

- targeted blocker resolution for `FPS-125` and `FPS-005`
- any narrow extractor/runtime changes strictly required to finish `FPS-125`
- any governed workbook/source-contract change strictly required to resolve `FPS-005`
- targeted preflight/download/catalog/extraction refresh only for changed blocker rows
- reruns of
  `nepa-knowledge-graph-export`,
  `forest-plan-profile-eval`,
  `forest-plan-component-retrieval-eval`, and
  `promotion-suite`
  on `source-set-cac9c7d02b280825`
- durable docs and handoff updates that describe the full-canonical green closeout

## Out Of Scope

- broad full-workbook recapture or full-source-set redownload
- unrelated forest-profile expansion, review-slot replay, or East Crazies reviewer-ready work
- downloader, catalog, or architecture cleanup not required by the two residual blockers
- historical source-set identity cleanup outside the exact active full-canonical contracts

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `src/usfs_r1_ea_sources/extract.py`
- `tests/test_extract.py`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`
- `source_library/derived/source-set-cac9c7d02b280825/diagnostics/summary.json`
- `source_library/derived/source-set-cac9c7d02b280825/diagnostics/extraction_manifest.jsonl`
- `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/`
- `source_library/evaluations/forest_plan_profile/`
- `source_library/evaluations/forest_plan_component_retrieval/`
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/`
- `config/promotion_suite_v1.json`
- `config/region1_forest_plan_profile_eval_coverage_v1.json`
- `config/forest_plan_component_retrieval_eval_v1.json`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan file

## Placement Rules

- Keep active source-contract repairs in the workbook. Do not add a parallel repair registry for
  `FPS-005`.
- Keep extractor/runtime behavior inside `src/usfs_r1_ea_sources/extract.py` plus focused tests.
  Do not create an ad hoc one-off OCR script as the only durable recovery path.
- If `FPS-125` must use an external/manual OCR lane, route it through existing extraction outputs
  and manifest metadata so the recovered text remains provenance-bearing and replayable.
- Keep all targeted reruns scoped to the changed blocker rows and the four named downstream artifact
  families unless a failed gate proves wider replay is required.
- This repo does not maintain `docs/agentic_architecture_index.md`; active routing for this lane
  must therefore stay aligned across `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, and this plan file.

## Weak-Point Prevention Contract

### Weak Point 1: `FPS-125` becomes a fake recovery by silently dropping pages

- Weak point forecast: a future session could accept an OCR result that omits failed pages or
  side-steps provenance by pasting manual text into the derived tree.
- Owner surface: `extract.py`, `tests/test_extract.py`, active extraction manifest, and
  `summary.json`.
- Prevention gate: the blocker closes only when `FPS-125` is `status="extracted"` in the active
  extraction manifest, has a non-null `text_path`, and records parser metadata proving the actual
  recovery path used.
- Fail threshold: `FPS-125` still appears as `parser_error`, has null output paths, or succeeds
  only through a handwritten text artifact with no parser metadata or no page-count provenance.
- Controlled violation: extractor tests must keep a negative case where OCR setup/runtime failure
  returns control to the remaining fallback lane instead of being treated as blank text.
- Future-Codex misuse scenario: treating a partial OCR dump as “good enough” because the file is
  hard to parse. This milestone must force either a real extracted record or a visible failure.

### Weak Point 2: `FPS-005` is “resolved” by silently changing the source contract

- Weak point forecast: a future session could swap in a different Beaverhead PDF, full-plan file,
  or generic planning page URL without updating the workbook row to describe the actual governing
  source.
- Owner surface: workbook row `FPS-005`, source-register validation, targeted download run,
  catalog/build outputs, and blocker docs.
- Prevention gate: any `FPS-005` fix must be traceable through the workbook contract and must pass
  `source-register-validate`, targeted preflight/download validation, and targeted catalog/extract
  refresh on the updated row.
- Fail threshold: the workbook row still points at `/media/228272` after claiming a fix, the row
  title/url no longer matches the captured artifact, or the row is changed only in runtime/config
  surfaces.
- Controlled violation: preserve a negative-path test or scripted check proving that a workbook URL
  mismatch or invalid direct PDF still fails extraction.
- Future-Codex misuse scenario: reusing `FOR-002` or another adjacent artifact for convenience
  without row-level contract repair. The milestone must make that substitution explicit or fail it.

### Weak Point 3: downstream reruns stay stale while promotion prose turns green

- Weak point forecast: the repo could clear the two extraction blockers but forget to rerun one or
  more of the exact blocked downstream artifacts, leaving promotion red for the same stale/missing
  reasons.
- Owner surface: `knowledge_graph/`, `forest_plan_profile` results,
  `forest_plan_component_retrieval` results, `promotion_suite` results, and the three manifest
  configs that govern those checks.
- Prevention gate: the milestone closes only when all four previously failed required full-canonical
  slots exist and point at `source-set-cac9c7d02b280825`, and `promotion-suite` reports
  `full_canonical_corpus_ready=true`.
- Fail threshold: any of the four failed slots remain missing or stale, or promotion remains
  `4/8`, `5/8`, `6/8`, or `7/8`.
- Controlled violation: keep the existing stale-artifact and missing-artifact checks green by proof,
  not by reducing coverage.
- Future-Codex misuse scenario: rerunning only `promotion-suite` and calling the lane complete. The
  milestone must require the upstream artifact families first.

### Weak Point 4: the lane reopens because routing docs disagree

- Weak point forecast: implementation could finish but README, current-state, handoff, and plan
  files could still point at the reduced freshness packet or stale blocker counts.
- Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and this
  plan file.
- Prevention gate: closeout requires the durable doc set to report the same active source set, same
  final full-canonical readiness state, same blocker disposition, and the same closeout commit hash
  for the finishing sequence.
- Fail threshold: any doc still says the active remaining work is the two-blocker lane after the
  full-canonical reruns are green, or any closeout doc omits the terminal promotion result.
- Controlled violation: targeted `rg` checks over the durable doc set before the final commit.
- Future-Codex misuse scenario: updating only the handoff after the rerun. The milestone is not
  complete until the full routing set is aligned.

## Milestone Sequence

### Milestone 0: Freshness Rebaseline And Baseline Lock

Outcome label: resolved

- Reconfirm the live blocker truth from:
  `summary.json`,
  `extraction_manifest.jsonl`,
  `promotion_suite_results.json`,
  workbook rows `FPS-005` and `FPS-125`, and the corresponding catalog rows.
- Reconfirm the exact four failed required full-canonical slots and the active source-set ID before
  any runtime or workbook edits.
- If the live blocker set differs from the evidence above, update this plan’s baseline section plus
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` before implementation
  proceeds.
- Closed `2026-05-19`: no drift was found. `FPS-005` remains `status="parser_error"` with
  `docling_conversion_failed` on active workbook/catalog row
  `https://www.fs.usda.gov/media/228272`, `FPS-125` remains `status="parser_error"` with
  `pdf_text_fallback_empty` on active workbook/catalog row
  `https://www.fs.usda.gov/media/51402`, and the exact required full-canonical failures remain the
  two missing NEPA 3D graph artifacts plus the two stale forest-plan eval artifacts. The next
  active implementation slice is Milestone 1 on `FPS-125`.

### Milestone 1: Resolve `FPS-125` Through Governed OCR Completion

Outcome label: resolved

- First rerun the current reduced raster path on `FPS-125` only:
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extract-build --output-dir source_library --id FPS-125 --docling-ocr --docling-timeout-seconds 1 --merge-selected-into-existing`
- If that path still produces no merged extracted record after a bounded, observable compute run
  with all `346` raster pages rendered and the `4`-worker pool active, finish the same milestone by
  adding a narrow governed external/manual OCR lane that still writes a real extracted record with
  parser provenance under the existing extraction surfaces.
- Do not accept a partial or ad hoc OCR artifact. The milestone closes only when `FPS-125` leaves
  the blocker set in the active extraction manifest and summary.

### Milestone 2: Resolve `FPS-005` Through Workbook-Contract Action

Outcome label: resolved

- Recheck the official Beaverhead planning/source evidence and determine the governed contract
  action for row `FPS-005`.
- Allowed terminal outcomes for this milestone are:
  1. update `FPS-005` in the workbook to a valid exact official replacement/repair source and prove
     it through targeted preflight/download/catalog/extraction refresh, or
  2. make an explicit workbook-contract reclassification/removal decision that takes the row out of
     the active load-bearing set and revalidates the workbook, catalog, and source-set truth
     accordingly.
- Forbidden outcomes are:
  silent runtime remapping,
  config-only URL repair,
  or silently substituting a different document while the workbook row still describes the old one.

### Milestone 3: Replay The Four Blocked Full-Canonical Artifacts

Outcome label: resolved

- After both blocker rows are cleared, rerun:
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- Rerun:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json`
- Rerun:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json`
- Rerun:
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- Close the milestone only when the two missing graph artifacts exist, the two stale eval results
  point at the active source set, and promotion reports `full_canonical_corpus_ready=true`.

### Milestone 4: Durable Closeout And Routing Reset

Outcome label: resolved

- Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and this plan file
  so they describe the terminal full-canonical green state rather than the reduced blocker lane.
- Record the exact closeout commit hash and verification commands in `docs/SESSION_HANDOFF.md`.
- If any runtime surface, parser metadata, or output-schema contract changed while resolving
  `FPS-125` or `FPS-005`, update the matching operator docs and schema docs in the same closeout
  slice.

## Required Implementation Artifacts

- any narrow extractor/runtime changes required to finish `FPS-125`
- focused extractor tests for any new OCR/runtime path
- updated workbook row and fingerprint data for `FPS-005`, if that row stays load-bearing
- targeted run artifacts for any changed blocker row:
  preflight summary,
  download summary,
  `validate-run` result,
  refreshed catalog manifest,
  refreshed extraction manifest and summary
- refreshed graph-validation and graph-summary artifacts under the active source-set knowledge-graph
  directory
- refreshed profile-eval and component-retrieval eval result files
- refreshed promotion-suite result/report files

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan file
- `docs/OUTPUT_SCHEMAS.md` if any parser metadata, extracted-record fields, or eval output schema
  changes while resolving `FPS-125`

## Required Verification Gates

- Workbook/source-contract work:
  `PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Targeted row capture work for `FPS-005`:
  `PYTHONPATH=src python -m usfs_r1_ea_sources preflight --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --id FPS-005 --run-id <run-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --id FPS-005 --run-id <run-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id <run-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --run-id <run-id>`
- Extractor/runtime work:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py -q`
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/extract.py tests/test_extract.py`
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extract-build --output-dir source_library --id FPS-125 --docling-ocr --docling-timeout-seconds 1 --merge-selected-into-existing`
- Active source-set freshness after any contract-changing row fix:
  `PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- Downstream closeout gates:
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json`
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json`
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- Docs and plan closeout:
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
  `git diff --check`

## Acceptance Criteria

- `FPS-125` no longer appears as `parser_error` in the active extraction manifest and has a durable
  extracted record under the active source set.
- `FPS-005` no longer blocks the active source set, either because it extracts successfully from a
  governed workbook repair or because the workbook contract has been explicitly changed and
  revalidated.
- `summary.json` for `source-set-cac9c7d02b280825` no longer reports `failed_count=2`.
- `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/nepa_3d_graph_validation.json`
  exists and validates the active source set.
- `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/nepa_3d_graph_summary.json`
  exists and reports the active source set.
- `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json` points at
  `source-set-cac9c7d02b280825`.
- `source_library/evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_results.json`
  points at `source-set-cac9c7d02b280825`.
- `promotion-suite` reports `full_canonical_corpus_ready=true` and
  `passed_required_full_canonical_result_count=8`.
- The durable doc set no longer routes future work through the two-blocker reduced lane.

## Stop Conditions

- No exact official replacement, repair, or explicit contract disposition can be proven for
  `FPS-005` from the official source evidence.
- `FPS-125` still cannot produce a provenance-bearing extracted record without using an OCR path
  that cannot be documented, replayed, or validated in the repo.
- The targeted blocker fixes unexpectedly require broad historical review-fixture rewrites or
  reviewer-ready East Crazies contract changes.
- Any required gate above can be satisfied only by weakening tests, narrowing assertions, or
  bypassing stale-artifact checks.

## Local Commit Closeout Policy

- Implement and close this plan milestone by milestone, not as one broad catch-all commit.
- `complete-after-commit` rule: no milestone in this plan may be marked complete, `resolved`, or
  `reduced` until verification passes, durable docs/handoff updates land, and the local atomic
  commit exists. A verified but uncommitted slice is only ready-to-close.
- Stage only the verified slice for each milestone.
- Leave unrelated tracked or ignored work alone, including unrelated `source_library/` evidence.
- Include implementation, tests, updated docs, and handoff updates that describe the finished
  milestone in the same commit.
- Record the actual closeout commit hash in `docs/SESSION_HANDOFF.md`.
- Treat each milestone as incomplete until its verification passes and its local atomic commit
  exists.

## Residual Risks And Next Milestone Routing

- The only acceptable residual risk after this plan is ordinary reviewer-ready versus
  full-canonical distinction. If `full_canonical_corpus_ready` is still false after the targeted
  blocker rows and four reruns, this plan remains open.
- If `FPS-125` ultimately requires a human-run OCR tool outside the repo runtime, route that as a
  narrow provenance-preserving follow-on and do not claim this plan `resolved` until the resulting
  extracted record lands in the active source set.
- If `FPS-005` lacks a governable official replacement, stop and route a dedicated workbook-contract
  policy decision rather than faking a green full-canonical corpus.
