# Full Canonical Downstream Freshness Refresh Milestone Plan

Date: 2026-05-19
Status: Reduced 2026-05-19
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` active full-canonical downstream refresh boundary

## Purpose

The canonical source-register import packet made the 635-row workbook import the active local
catalog, but the full-canonical downstream artifact family, coverage manifests, and promotion
contracts still point at historical source set `source-set-5e65d845ce77e1a0`. This milestone exists
to make the active imported catalog the truthful full-canonical downstream boundary without
silently relabeling historical review fixtures or weakening the gates that currently catch stale
artifacts.

## Closeout Notes

Reduced on 2026-05-19 with the following repo-grounded outcome:

- Active full-canonical manifest contracts and focused tests are now rebound to
  `source-set-cac9c7d02b280825` rather than historical `source-set-5e65d845ce77e1a0`.
- `authority-currentness --source-set-id source-set-cac9c7d02b280825` now passes and records
  `authority_family_count=454`,
  `catalog_source_partition_counts={"active_review_corpus": 583, "currentness_supersession_archive": 52}`,
  `source_currentness_record_count=635`, and `validation_passed=true`.
- The first full-source-set extraction replay is now historical blocker evidence only. The live
  extraction summary on `source-set-cac9c7d02b280825` has since moved to
  `extracted=633`, `parser_error=2`, `chunk_count=97248`, and `validation_passed=false` through a
  targeted external-Docling OCR merge replay plus three in-environment no-timeout Docling retries
  on `WILD-ESA-038`, `WILD-ESA-054`, and `FPS-241`.
- The residual extraction blocker set is now exact:
  `FPS-005` (`docling_conversion_failed`; invalid PDF structure),
  `FPS-125` (`pdf_text_fallback_empty`).
- A fresh upstream redownload of `FPS-005` reproduces the same invalid xref/pages corruption, so
  that blocker is not a bad local artifact. `pdftotext` still returns zero characters on
  `FPS-125`, while `pdftoppm` can render it. A no-timeout in-environment OCR retry on `FPS-125`
  remained compute-bound for roughly `40` minutes and was interrupted without a merged success
  result. That narrows the remaining lane to upstream PDF replacement/repair plus one OCR-heavy
  raster recovery straggler rather than broader manifest or downloader drift.
- The extractor now ships two explicit scanned-PDF rescue paths for the remaining OCR-heavy
  straggler lane: `pdf_raster_ocr` (`pdftoppm` + `RapidOCR(torch)`) and a chunked Docling OCR
  fallback. Focused regression coverage now passes `25/25` in `tests/test_extract.py`, but the
  active source-set blocker state above remains unchanged because the first long targeted live
  `FPS-125` replay under the new rescue path was interrupted before it produced a merged success
  record.
- Fresh `promotion-suite --manifest config/promotion_suite_v1.json` now fails for the right reason:
  the old full-canonical stale-manifest split is gone, and the remaining full-canonical failure
  surface is narrowed to `4/8` required results passing with
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2, "stale_artifact": 2}`.
  The only remaining failed full-canonical results are the missing
  `derived/source-set-cac9c7d02b280825/knowledge_graph/*` artifacts plus the still-historical
  `forest_plan_profile` and `forest_plan_component_retrieval` eval result identities.
- This packet is therefore reduced, not resolved. The remaining issue is a concrete extraction and
  parser-recovery lane for the `2` failed source records, after which the source-set graph and the
  two still-historical full-canonical eval artifacts can be replayed on
  `source-set-cac9c7d02b280825`.

## Reduced Closeout Evidence

- `source_library/catalog/source_set_manifest.json` now records active local catalog
  `source-set-cac9c7d02b280825` with `source_count=635`, `artifact_count=623`,
  `source_partition_counts={"active_review_corpus": 583, "currentness_supersession_archive": 52}`,
  and governing download run `phase2-canonical-download-full-post-head429-fallback-20260519`.
- Active full-canonical manifest contracts in
  `config/promotion_suite_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`, and
  `config/phase_eval_direct_eval_v1.json` are now rebound to
  `source-set-cac9c7d02b280825`.
- `source_library/derived/source-set-cac9c7d02b280825/authority_currentness/authority_currentness_report.json`
  now passes with `authority_family_count=454`,
  `catalog_source_partition_counts={"active_review_corpus": 583, "currentness_supersession_archive": 52}`,
  `source_currentness_record_count=635`, and `validation_passed=true`.
- `source_library/derived/source-set-cac9c7d02b280825/diagnostics/summary.json` now records the
  live reduced blocker state with `extracted_count=633`,
  `failed_count=2`,
  `chunk_count=97248`,
  `validation_passed=false`, and
  `failure_counts={"docling_conversion_failed": 1, "pdf_text_fallback_empty": 1}`.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  now reports `current_promotion_ready=true`, `promotion_ready=true`, `expansion_ready=true`,
  `full_canonical_corpus_ready=false`, `passed_required_full_canonical_result_count=4`,
  `required_full_canonical_result_count=8`, and
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2, "stale_artifact": 2}`
  with active full-canonical source set `source-set-cac9c7d02b280825`.
- The preserved review-slot manifests for West Reservoir and older source-delta lanes remain
  historical fixtures. They were intentionally not mass-relabeled during this packet.

## Goal

Refresh the bounded full-canonical downstream source-set artifact family onto active catalog
`source-set-cac9c7d02b280825`, update the live gate manifests and contract tests to that new
truth, and leave the repo with one accurate answer to "what is the active full-canonical
downstream corpus?".

## Non-Goals

- Do not weaken or remove the stale-artifact gates just to turn `promotion-suite` green.
- Do not relabel historical review fixtures such as West Reservoir, the East Crazies current
  reviewer-ready lane, or source-delta replay outputs unless the bounded replay actually rebuilds
  those artifacts on the new source set.
- Do not rerun bulk downloads, catalog import, or workbook mutation work already closed by the
  canonical import-completion packet.
- Do not claim that every preserved historical review packet has been replayed on the new source
  set if the refreshed contract only proves source-set downstream freshness.

## Scope

- source-set derived replay for the active imported catalog:
  extraction, authority-currentness, retrieval, evidence graph, claim extraction, rule-claim link,
  forest-plan component inventory, and source-set NEPA 3D graph export
- full-canonical coverage/eval contracts tied to the active source set:
  profile eval, component retrieval eval, promotion-suite full-canonical checks, and
  phase-eval direct-eval requirements
- focused contract tests for the live manifests above
- durable docs and handoff updates that describe the refreshed full-canonical downstream state

## Out Of Scope

- changing reviewer-facing current-promotion source set `source-set-ba8d0feae79501b8`
- changing West Reservoir or other historical review-slot source-set expectations unless a bounded
  review replay is required and completed in this same milestone
- broader architecture refactors unrelated to the source-set identity and gate ownership split

## Owner Surfaces

- `config/promotion_suite_v1.json`
- `config/region1_forest_plan_profile_eval_coverage_v1.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/r1_forest_plan_component_inventory_build_manifest.json`
- `config/forest_plan_component_retrieval_eval_v1.json`
- `config/phase_eval_direct_eval_v1.json`
- `src/usfs_r1_ea_sources/promotion_suite.py`
- `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`
- `tests/test_promotion_suite.py`
- `tests/test_phase_eval_direct_eval_contracts.py`
- `tests/test_forest_plan_profile_eval_contracts.py`
- `tests/test_forest_plan_inventory_build_manifest.py`
- `tests/test_phase_eval.py`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan file

## Placement Rules

- Keep active full-canonical identity changes in the manifest/config surfaces that already own those
  gates. Do not add an ad hoc alias layer that rewrites source-set IDs at runtime.
- Keep historical review fixtures pinned unless the replay regenerates them. If the active
  full-canonical refresh needs preserved historical fixtures, describe that dependency explicitly in
  the manifest instead of silently mutating historical artifacts.
- Keep new source-set replay outputs under
  `source_library/derived/source-set-cac9c7d02b280825/` and evaluation outputs under the existing
  `source_library/evaluations/` locations.
- Preserve the explicit split between current reviewer-ready promotion truth and active
  full-canonical downstream truth in promotion reporting.

## Weak-Point Prevention Contract

### Weak Point 1: The repo silently relabels stale artifacts as fresh

- Weak point forecast: a future session could update only `full_canonical_source_set_id` and doc
  prose while leaving the downstream artifact files on the historical source set.
- Owner surface: `config/promotion_suite_v1.json`, source-set derived outputs, and
  `tests/test_promotion_suite.py`.
- Prevention gate: `promotion-suite --manifest config/promotion_suite_v1.json` must stay fail-closed
  on stale source-set identity until the bounded replay writes new-source-set artifacts and the
  required full-canonical checks pass.
- Fail threshold: any required full-canonical result still reports the historical source set or a
  missing new-source-set artifact path.
- Controlled violation: the committed promotion-suite tests must still include a stale-artifact
  mismatch case proving the suite fails when manifest and artifact IDs diverge.
- Future-Codex misuse scenario: changing only config text and docs to match the new source set. The
  suite must still fail loudly if artifact ownership was not replayed.

### Weak Point 2: Historical review fixtures get mass-relabeled without proof

- Weak point forecast: a broad search-and-replace could mutate West Reservoir, source-delta replay,
  or adjudication fixtures to the new source set even though those review artifacts were not
  replayed.
- Owner surface: historical review configs under `config/forest_plan_component_*`,
  `config/applicability_adjudications/`, `config/replay_contexts/`, and review outputs under
  `source_library/reviews/`.
- Prevention gate: only active full-canonical source-set contracts may change unless a review-bound
  replay command is run and the refreshed review artifacts pass.
- Fail threshold: historical review fixtures are edited without a matching replay command and
  verification artifact in the same milestone.
- Controlled violation: preserve mixed-source coverage expectations in the aggregate coverage
  manifest so tests fail if the slot/source identities drift unexpectedly.
- Future-Codex misuse scenario: replacing every historical source-set ID in `config/`. The plan
  forbids that unless the fixture is truly part of the active source-set replay boundary.

### Weak Point 3: Docs drift back into split-state language

- Weak point forecast: code and artifacts may refresh while README, current-state, or handoff docs
  keep describing the old "import is fresh but downstream is stale" state.
- Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and this
  plan.
- Prevention gate: closeout requires all three durable docs plus this plan to name the same active
  full-canonical source set and report whether `promotion-suite` is green or still routed-red.
- Fail threshold: any top-of-file closeout section still treats `source-set-5e65d845ce77e1a0` as
  the live active full-canonical downstream source set after this milestone.
- Controlled violation: targeted `rg` checks over the active doc set before commit.
- Future-Codex misuse scenario: updating only one doc after a replay. The milestone closes only when
  the durable doc set is aligned.

### Weak Point 4: The milestone turns green by weakening gates

- Weak point forecast: the refresh may be tempted to drop full-canonical checks, lower thresholds,
  or bypass required evals instead of rebuilding the needed artifacts.
- Owner surface: promotion-suite manifest, profile/component eval manifests, and focused tests.
- Prevention gate: replay the existing required commands and keep current thresholds unless the
- replacement check is stronger and documented.
- Fail threshold: removing a required check, reducing a threshold, or deleting a stale-artifact
  assertion without replacement proof.
- Controlled violation: focused contract tests for promotion-suite and phase-eval direct-eval must
  still pass the negative stale-identity cases.
- Future-Codex misuse scenario: converting this packet into a docs-only green report. The committed
  test slice must prove the gates remain fail-closed.

## Milestone Sequence

1. Rebind the active full-canonical manifest contracts to `source-set-cac9c7d02b280825` while
   preserving historical review-slot ownership.
   Outcome label: resolved.
2. Replay the bounded active source-set derived lane on `source-set-cac9c7d02b280825` until
   extraction, currentness, retrieval, graph, and component inventory artifacts exist under the new
   derived directory.
   Outcome label: reduced.
3. Replay the full-canonical source-set coverage/eval chain and rerun `promotion-suite` until the
   active full-canonical contract no longer depends on historical source-set artifact ownership.
   Outcome label: reduced.
4. Rebaseline durable docs and handoff to the refreshed active full-canonical downstream truth and
   close this packet with one atomic commit or a reduced blocker handoff if extraction fails.
   Outcome label: resolved.

## Required Implementation Artifacts

- refreshed `source_library/derived/source-set-cac9c7d02b280825/` artifact family
- refreshed `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json`
- refreshed `source_library/evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_results.json`
- refreshed `source_library/evaluations/forest_plan_component_eval_coverage/forest_plan_component_eval_coverage_results.json`
- refreshed `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan file

## Required Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profile_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py -q`
- `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library`
- `PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-cac9c7d02b280825 --contract-path config/verified_extraction_admission_contract.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- `PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-cac9c7d02b280825 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-cac9c7d02b280825`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `git diff --check`

## Acceptance Criteria

- The active full-canonical contract surfaces named above all point at
  `source-set-cac9c7d02b280825`, and focused tests for those committed manifests pass.
- `source_library/derived/source-set-cac9c7d02b280825/` exists with passing extraction,
  currentness, retrieval, graph, and component-inventory artifacts.
- `promotion-suite --manifest config/promotion_suite_v1.json` no longer fails because the active
  full-canonical manifest is pinned to `source-set-5e65d845ce77e1a0`.
- If the packet reduces instead of resolves, the remaining blocker set must be named explicitly by
  source record ID and parser failure class, and the active docs must route the next extraction
  recovery milestone rather than pretending the downstream refresh is merely pending.
- The repo still distinguishes current reviewer-ready promotion
  `source-set-ba8d0feae79501b8` from the refreshed active full-canonical downstream source set.
- Historical review fixtures remain unchanged unless they were replayed and verified in this same
  milestone.

## Stop Conditions

- Stop if the bounded source-set replay requires bulk download or workbook mutation work already
  closed by the import-completion packet.
- Stop if active full-canonical freshness cannot be restored without mutating historical review
  fixtures that are not part of the bounded replay surface; in that case, reroute the remaining
  issue into a narrower historical-review rebinding packet.
- Stop if the refresh can only be made green by weakening stale-artifact, coverage, or direct-eval
  gates.

## Local Commit Closeout Policy

Close this milestone only after the bounded replay commands, focused tests, durable docs, and this
plan file are all updated together in one atomic local commit. Stage only the verified refresh
slice. A verified but uncommitted refresh is ready-to-close, not complete-after-commit.

## Residual Risks And Next Milestone Routing

- If preserved historical review slots still need source-set rebinding after the active source-set
  refresh is green, route that as a separate review-bound packet rather than mixing it into this
  milestone.
- If the new full-canonical replay exposes real extraction/parser failures on the 635-row corpus,
  record them as runtime blockers and stop at a reduced closeout instead of silently reusing
  historical outputs.
