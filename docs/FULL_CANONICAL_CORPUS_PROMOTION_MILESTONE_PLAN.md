# Full Canonical Corpus Promotion Milestone Plan

Date: 2026-05-10
Status: Closed 2026-05-10
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` current-corpus promotion boundary

## Purpose

The repo now has a refreshed merged corpus that closes the Region 1 forest-plan support-document
capture and replay gap, but the active canonical catalog and promoted corpus language still point at
older source sets. This milestone exists to make the refreshed merged corpus the active full
canonical corpus without overstating downstream reviewer-ready status.

The implementation must replace the stale split between:

- active canonical catalog: `source-set-d3b9e2a728accda6`
- promoted downstream V1 source set: `source-set-ba8d0feae79501b8`
- refreshed merged replay surface: `source-set-8a4005c8a083af1a`
- promoted active full canonical catalog under current code:
  `source-set-34061d1e4bf6c460`

The repo should end this milestone with one truthful answer to "what is the full canonical corpus?"
and with gates that prevent future Codex sessions from silently mixing corpus promotion with
reviewer-ready East Crazies promotion.

## Closeout Notes

Closed on 2026-05-10 with the following repo-grounded outcome:

- `source_library/catalog/` was rebuilt from
  `corpus-update-2026-05-01-cg-support-batches` plus
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches`
- the active full canonical catalog source set is now `source-set-34061d1e4bf6c460`
- the promotion suite now records that active full-corpus identity separately from current
  reviewer-ready V1 identity `source-set-ba8d0feae79501b8`
- the archived merged replay surface `source-set-8a4005c8a083af1a` remains the freshest fully
  replayed extraction/retrieval/graph surface and still owns the blocked merged-corpus East Crazies
  replay
- the preserved Kootenai gap remains explicit in `source_delta_input` and
  `config/r1_forest_plan_official_source_gap_evidence.json`, not as a silently downloaded source row
- stale Sequence 4 wording was corrected so the plan now matches the implemented full-corpus
  semantics instead of telling `README.md` to call the archived merged replay surface the active
  full canonical corpus
- closeout implementation commit: `5aa32d9`
- verification replay after closeout alignment:
  - `tests/test_catalog.py tests/test_captured_library.py`: `19/19` passed
  - `tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py`: `41/41` passed
  - `tests/test_promotion_suite.py tests/test_final_qa_certification.py`: `30/30` passed
  - `tests/test_architecture_contract.py`: `5/5` passed
  - `ruff check src tests`, `python -m compileall src`, `forest-plan-source-delta-readiness`,
    `promotion-suite`, and `final-qa-certification --validate-only` all passed

## Current Evidence

- `docs/SESSION_HANDOFF.md` records the 2026-05-10 refresh as scoped source set
  `source-set-bfe49a94e22fd1e2` and merged source set `source-set-8a4005c8a083af1a`, with merged
  extraction `349/349`, retrieval eval `12/12`, source-set `phase-eval` `7/7`, and one preserved
  official-source gap.
- `docs/CURRENT_SYSTEM_STATE.md` still says the promoted downstream V1 source set is
  `source-set-ba8d0feae79501b8` and the active canonical catalog is
  `source-set-d3b9e2a728accda6`, while separately documenting the green merged refresh on
  `source-set-8a4005c8a083af1a`.
- `README.md` still describes the Region 1 support-document layer as a controlled source delta and
  still labels `source-set-ba8d0feae79501b8` as the promoted downstream V1 source set.
- `config/promotion_suite_v1.json` hard-codes `source_set_id=source-set-ba8d0feae79501b8` for the
  current East Crazies promotion lane.
- `src/usfs_r1_ea_sources/catalog.py` already supports repeated `--batch-run-id` values and a
  caller-selected `--catalog-dir`, which is enough to rebuild `source_library/catalog/` from the
  merged inputs rather than only archiving merged gates.
- `src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py` already proves the merged corpus is
  complete enough to promote as the full corpus and carries the official-source gap as explicit
  evidence instead of a silent omission.
- `tests/test_captured_library.py` is still anchored to the older 190-row canonical run and active
  `source_library/catalog/` contract, so active-catalog promotion will otherwise make the integrity
  suite lie or fail for the wrong reason.

## Goal

Promote the refreshed merged corpus built from the canonical workbook corpus plus completed
forest-plan support-document capture into the active full canonical corpus contract, with explicit
separation between:

- full canonical corpus truth
- reviewer-ready current-promotion truth
- blocked merged-corpus East Crazies replay truth

The repo should expose the promoted current-code active catalog source set as the full canonical
corpus only after the active catalog, integrity tests, promotion/report contracts, and durable docs
all agree on that state.

## Non-Goals

- Do not resolve the `7` East Crazies applicability adjudications in the merged replay.
- Do not resolve the failing East Crazies forest-plan component eval cases in the merged replay.
- Do not claim that `source-set-8a4005c8a083af1a` is already reviewer-ready for the East Crazies
  package review lane.
- Do not remove or hide the preserved official-source gap `R1PLAN-kootenai-nf-18`.
- Do not change the ignored-file policy for `source_library/`.
- Do not touch unrelated dirty files under `viewer/nepa-3d/` or root-level East Crazies draft
  artifacts.

## Scope

- active `source_library/catalog/` promotion from the archived merged gate
- corpus-integrity tests and gates that define the active full corpus
- promotion-manifest and report semantics that currently conflate full-corpus identity with
  reviewer-ready East Crazies promotion
- durable docs that identify the active canonical corpus
- session handoff closeout for the promotion milestone

## Out Of Scope

- new source capture beyond the 2026-05-10 refresh
- downloader behavior changes unrelated to catalog promotion
- broad review-engine logic changes outside the source-set identity and gate semantics required for
  truthful promotion
- package-facing artifact rewrites unless required to keep promotion docs truthful

## Owner Surfaces

- `src/usfs_r1_ea_sources/catalog.py`
- `src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py`
- `src/usfs_r1_ea_sources/promotion_suite.py`
- `src/usfs_r1_ea_sources/final_qa_certification.py` if current-promotion reporting needs an
  explicit split from full-corpus promotion
- `config/promotion_suite_v1.json`
- `tests/test_catalog.py`
- `tests/test_captured_library.py`
- `tests/test_forest_plan_source_delta_readiness.py`
- `tests/test_promotion_suite.py`
- `tests/test_final_qa_certification.py` if the manifest/report split changes final QA expectations
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/SESSION_HANDOFF.md`
- this plan file

## Placement Rules

- Keep catalog promotion logic in `catalog.py` and CLI wiring that already owns catalog-build
  behavior. Do not introduce a parallel ad hoc script that rewrites `source_library/catalog/`.
- Keep corpus-readiness truth in `forest_plan_source_delta_readiness.py` or a nearby gate module.
  Do not bury promotion conditions inside README-only prose.
- Keep promotion semantics in `promotion_suite.py` plus manifest/config surfaces. If the repo needs a
  distinction between full-corpus promotion and reviewer-ready current promotion, model it as
  explicit manifest/report fields or an adjacent manifest, not as undocumented operator knowledge.
- Keep integrity expectations in tests that read `source_library/catalog/` and the relevant run
  directories. Do not rely on manual inspection of ignored outputs as the only proof.
- Preserve workbook row identity, source-record IDs, source partitions, artifact hashes, citation
  labels, and official-source-gap evidence during promotion.

## Weak-Point Prevention Contract

### Weak Point 1: Active catalog promotion becomes a silent file swap

- Weak point forecast: a future Codex session could copy the archived merged gate into
  `source_library/catalog/` or rerun catalog-build with the wrong inputs, producing an active
  catalog that looks plausible but is not provably the refreshed merged corpus.
- Owner surface: `catalog.py`, catalog-build CLI wiring, `tests/test_catalog.py`,
  `tests/test_captured_library.py`.
- Prevention gate: `catalog-build` must rebuild the active catalog from the canonical batch run plus
  the refreshed source-delta batch run and must emit a manifest whose `source_set_id`,
  `download_batch_run_ids`, `source_count`, `artifact_count`, and source-partition counts match the
  merged gate truth.
- Fail threshold: the active manifest does not equal the promoted current-code full canonical source
  set, the active
  catalog validation fails, any expected batch run ID is missing, or the active catalog drops the
  explicit `candidate_blocked_source` row for `R1PLAN-kootenai-nf-18`.
- Controlled violation: a focused test fixture removes one batch run ID or downgrades the active
  manifest counts; the promotion gate must fail.
- Future-Codex misuse scenario: someone treats the archived merged gate as a static artifact and
  skips catalog rebuild verification. The milestone must force a rebuild-or-prove workflow.

### Weak Point 2: Full-corpus promotion is confused with reviewer-ready East Crazies promotion

- Weak point forecast: changing the active full corpus source set could make
  `promotion-suite --manifest config/promotion_suite_v1.json` report false failures or false
  readiness because it currently hard-codes the older East Crazies V1 source set.
- Owner surface: `promotion_suite.py`, `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite.py`, `tests/test_final_qa_certification.py`, promotion docs.
- Prevention gate: promotion reporting must explicitly distinguish full-corpus identity from
  reviewer-ready current-promotion identity, and the manifest-driven current-promotion lane must
  either remain intentionally pinned to the older review-ready source set or be updated only after
  the merged review replay becomes green.
- Fail threshold: any doc or report says the full canonical corpus is the archived replay source set
  while a current-promotion report silently still means
  `source-set-ba8d0feae79501b8` without explanation, or any manifest conflates those identities in
  a way that changes pass/fail meaning.
- Controlled violation: a fixture sets the full-corpus source set and reviewer-promotion source set
  to inconsistent values without explanatory metadata; the suite/report test must fail.
- Future-Codex misuse scenario: a later session updates only `source_set_id` in the manifest and
  assumes that means East Crazies current promotion is complete. The milestone must make that wrong
  pattern fail loudly.

### Weak Point 3: Official-source gap evidence disappears during promotion

- Weak point forecast: once the merged corpus becomes canonical, the one preserved official-source
  gap could be lost from active-catalog and docs language, making the corpus look complete in a way
  the evidence does not support.
- Owner surface: `forest_plan_source_delta_readiness.py`, active catalog tests, current-state docs.
- Prevention gate: the active-corpus promotion gate must require the official-source-gap evidence
  file and must assert that the promoted corpus keeps one explicit `candidate_blocked_source` row.
- Fail threshold: the promoted corpus reports zero blocker rows, the gap-evidence file is missing,
  or the active-corpus docs omit the preserved gap.
- Controlled violation: remove the gap evidence path from a fixture or mutate the blocker count to
  zero; readiness or promotion verification must fail.
- Future-Codex misuse scenario: a future session treats "full canonical corpus" as meaning "no
  unresolved official gaps". This milestone must preserve the repo's explicit-gap contract.

### Weak Point 4: Durable docs drift away from live active-corpus truth

- Weak point forecast: code and active catalog could be promoted while README, current-system-state,
  and handoff docs still describe the older canonical or promoted source sets.
- Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/SESSION_HANDOFF.md`.
- Prevention gate: closeout requires a docs freshness check that compares live manifest IDs/counts
  against the durable docs and fails on stale source-set language.
- Fail threshold: any closeout doc still says the active full canonical corpus is
  `source-set-d3b9e2a728accda6` or `source-set-ba8d0feae79501b8` after the active catalog is
  promoted.
- Controlled violation: keep one doc pinned to the old source-set string in a controlled test or
  grep-based closeout check; the milestone must fail until the drift is removed.
- Future-Codex misuse scenario: a future session answers user questions from stale prose instead of
  the live manifest. This milestone must keep the prose aligned to the manifest.

## Milestone Sequence

### Sequence 0 - Promotion Gate Baseline

Goal: create the failing-or-baseline gate that defines what "active full canonical corpus promotion"
means before changing any live catalog contract.

Implementation steps:

1. Add or extend a gate that reads:
   - the archived merged catalog gate under
     `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`
   - the active `source_library/catalog/`
   - `config/r1_forest_plan_document_register_draft.csv`
   - `config/r1_forest_plan_official_source_gap_evidence.json`
   - any manifest/config surface that defines current-promotion reporting
2. Make the gate compare active full-corpus identity, blocker-row preservation, and doc/report
   truth rather than only catalog file existence.
3. Add negative fixtures proving the gate fails on stale active manifest IDs, missing blocker rows,
   or report/config identity drift.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_catalog.py
PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py
git diff --check
```

### Sequence 1 - Active Catalog Promotion

Goal: make the refreshed merged corpus the active `source_library/catalog/` contract.

Implementation steps:

1. Promote the merged inputs to the active catalog through the owned catalog-build path rather than
   manual file copying.
2. Ensure the active manifest records the merged truth:
   - `source_set_id=source-set-34061d1e4bf6c460`
   - both batch run IDs required to form the merged corpus
   - `350` source rows
   - `319` artifacts
   - `349` `active_review_corpus` rows
   - `1` `candidate_blocked_source` row
   - `160` supplemental source-delta rows
3. Preserve the archived merged gate as the reference artifact even after the active catalog is
   updated.
4. Update integrity tests so `source_library/catalog/` is validated as the promoted merged corpus
   rather than as the older 190-row canonical-only catalog.

Required implementation artifacts:

- updated catalog promotion logic or CLI wiring if needed
- updated active catalog integrity tests
- local regenerated `source_library/catalog/` manifest, catalog, validation, sqlite, and graph files

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id corpus-update-2026-05-01-cg-support-batches \
  --batch-run-id r1-forest-plan-source-delta-capture-20260510-refresh-batches \
  --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_captured_library.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

### Sequence 2 - Derived Active-Corpus Alignment

Goal: prove the promoted active catalog can serve as the repo's default full-corpus input without
needing archived-gate-only routing for standard full-corpus commands.

Implementation steps:

1. Identify commands and tests that still assume the active catalog means the older 190-row corpus.
2. Update those default-active-catalog assumptions where needed so the active full corpus means the
   merged source set while preserving the archived-gate path for historical or scoped replays.
3. Regenerate or refresh the active full-corpus derived surfaces that are expected to follow the
   active catalog identity, at minimum where docs or gates claim active-corpus truth.
4. Keep reviewer-ready status separate from source-set freshness. A derived artifact may be current
   for the full corpus while the East Crazies merged review replay remains blocked.

Required implementation artifacts:

- any source-set-aware command or test updates required for default active-catalog behavior
- refreshed active-corpus derived reports that are referenced by docs or gates

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness \
  --output-dir source_library \
  --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-refresh-batches \
  --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

### Sequence 3 - Promotion And Final-QA Contract Split

Goal: make promotion reporting truthful after active full-corpus promotion.

Implementation steps:

1. Decide the explicit contract:
   - either `config/promotion_suite_v1.json` remains the current reviewer-promotion manifest pinned
     to `source-set-ba8d0feae79501b8`
   - or the repo introduces a separate full-corpus promotion/status manifest while leaving the
     current reviewer-promotion lane unchanged until merged review blockers are closed
2. Encode that contract in manifest fields, suite reporting, and any final-QA dependencies so the
   repo no longer uses one source-set field for two different truths.
3. Add tests for the negative case where a source-set swap is made without the accompanying contract
   explanation.
4. Update operator docs to say exactly when a corpus can be canonical without being current-promotion
   ready for East Crazies.

Required implementation artifacts:

- updated `config/promotion_suite_v1.json` or adjacent manifest/config artifact
- updated `promotion_suite.py` and final-QA expectations if contract fields change
- focused tests covering truthful split semantics

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_final_qa_certification.py
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
git diff --check
```

### Sequence 4 - Documentation And Handoff Closeout

Goal: make the durable repo narrative agree with the promoted active-corpus truth and the still
blocked merged-review truth.

Implementation steps:

1. Update `README.md` to state that the active full canonical corpus is the promoted current-code
   catalog source set and to distinguish that from both the archived merged replay surface and
   reviewer-ready East Crazies promotion.
2. Update `docs/CURRENT_SYSTEM_STATE.md` with the active-catalog source set, preserved official
   source gap, and current downstream blocker boundary.
3. Update `docs/POST_V1_PROMOTION_SUITE.md` if promotion semantics or manifest ownership changed.
4. Update `docs/SESSION_HANDOFF.md` with:
   - the milestone name
   - the promoted active source set
   - the exact verification commands
   - the commit hash
   - residual risks
   - next milestone routing

Required verification:

```bash
rg -n "source-set-ba8d0feae79501b8|source-set-d3b9e2a728accda6|source-set-8a4005c8a083af1a|source-set-34061d1e4bf6c460" README.md docs/CURRENT_SYSTEM_STATE.md docs/POST_V1_PROMOTION_SUITE.md docs/SESSION_HANDOFF.md
git diff --check
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_CORPUS_PROMOTION_MILESTONE_PLAN.md
```

## Verification Gates

The milestone is not complete until all required gates below pass on the promoted slice:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_captured_library.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_final_qa_certification.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness \
  --output-dir source_library \
  --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-refresh-batches \
  --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
git diff --check
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_CORPUS_PROMOTION_MILESTONE_PLAN.md
```

If final-QA contract fields change as part of Sequence 3, also run the relevant validate-only final
QA command that consumes the updated promotion-suite artifact before commit.

## Acceptance Criteria

- `source_library/catalog/source_set_manifest.json` reports
  `source_set_id=source-set-34061d1e4bf6c460`, the merged input batch IDs, `source_count=350`,
  `artifact_count=319`, `active_review_corpus=349`, and exactly `1` explicit
  `candidate_blocked_source`.
- `tests/test_captured_library.py` and related catalog tests pass against the promoted active
  catalog and no longer encode the stale 190-row-only active-catalog assumption.
- `forest-plan-source-delta-readiness` passes against the refresh batch run and still reports the
  preserved Kootenai official-source gap instead of hiding it.
- promotion reporting is explicit about the difference between full canonical corpus identity and
  reviewer-ready East Crazies promotion identity. A manifest or report that tries to use one source
  set value for both meanings must fail a test or gate.
- `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` all give the same
  active full-corpus answer, and none of them call `source-set-ba8d0feae79501b8` the active full
  canonical corpus after closeout.
- The milestone closeout includes the plan, code/tests/config changes, doc updates, and handoff in
  one atomic commit after the full gate set passes with `0` unresolved failures in the promoted
  slice.

## Documentation And Handoff Updates

Before closeout, update:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/POST_V1_PROMOTION_SUITE.md` if Sequence 3 changes manifest semantics
- `docs/SESSION_HANDOFF.md`
- this plan file with closeout notes if the implementation sequence changes materially during work

The handoff must record:

- promoted active source set ID
- active catalog counts
- whether `config/promotion_suite_v1.json` stayed pinned to the older reviewer-ready lane or gained
  explicit split semantics
- exact verification commands and pass/fail counts
- residual risks
- next milestone routing
- commit hash

## Commit Closeout

- Stage only the verified milestone slice.
- Leave unrelated dirty files and untracked drafts alone.
- Include implementation, focused tests, config changes, docs, and handoff updates in the same
  atomic commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Stop before commit if the active-catalog promotion cannot be verified cleanly or if the
  reviewer-promotion contract cannot be made truthful without broader scope than this milestone.

## Stop Conditions

- The refreshed merged catalog gate cannot be rebuilt or verified from official repo inputs.
- Promoting `source_library/catalog/` would require silent manual file copying with no owned rebuild
  or validation path.
- The full-corpus source-set identity and current-promotion source-set identity cannot be separated
  truthfully within the current promotion/final-QA contract.
- Verification requires mutating unrelated user work or staging ignored `source_library/` artifacts
  contrary to repo policy.
- The preserved official-source gap cannot remain explicit after promotion without a broader data
  model change.

## Residual Risks And Next Milestone Routing

Residual risks after this milestone:

- East Crazies merged-corpus replay on `source-set-8a4005c8a083af1a` still remains blocked by
  `7` applicability adjudications and failing forest-plan component eval cases.
- The preserved official-source gap `R1PLAN-kootenai-nf-18` remains an accepted corpus boundary, not
  a resolved capture.
- Reviewer-facing promotion artifacts may still remain intentionally pinned to
  `source-set-ba8d0feae79501b8` until the merged review replay becomes reviewer-ready.

Next milestone routing after this promotion milestone:

1. Applicability adjudication closure for
   `source_library/reviews/v1-cg-ecid-source-delta-review/applicability/`.
2. Forest-plan component gap closure for the merged-corpus East Crazies replay.
3. After those are green, update reviewer-facing promotion and final-QA lanes to the merged full
   canonical corpus if the package replay proves reviewer-ready.
