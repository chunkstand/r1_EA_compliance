# Canonical Source Register Import Completion Milestone Plan

Date: 2026-05-18
Status: Active 2026-05-18 (Milestone 0 resolved at `6a949ae`; Milestone 1 federal-blocker slice live)
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` post-refoundation canonical
source-register import boundary

Milestone 0 closeout summary on 2026-05-18:

- The docs-only Milestone 0 slice chose the rebaseline path, not a local
  `source_library/catalog/` restore. The current checkout already carries a
  reproducible proving-slice active catalog and a separate reproducible planned
  Phase 2 gate, while restoring the older documented full-canonical catalog in
  a docs milestone would require mutating ignored local evidence before the
  import packet has closed its active truth boundary.
- The active local catalog baseline is now pinned as proving source set
  `source-set-9dcf819bc4cca486` with `source_count=26`,
  `artifact_count=26`, `unique_url_count=26`,
  `source_partition_counts={"active_review_corpus": 25,
  "currentness_supersession_archive": 1}`,
  `status_counts={"downloaded_existing": 26}`, and governing download run
  `source-register-proving-download-20260518T105620Z-08363bef`.
- The full-register Phase 2 gate baseline is now pinned as planned-only source
  set `source-set-ae989382c52344db` with `source_count=635`,
  `artifact_count=0`, `unique_url_count=635`,
  `source_partition_counts={"candidate_blocked_source": 635}`,
  `status_counts={"planned": 635}`, and `download_run_id=null`.
- The current master-sheet import blocker baseline is now exact:
  `phase2-canonical-dry-run-20260518` planned all `635` canonical URLs, while
  `phase2-canonical-preflight-20260518` checked `25` URLs and recorded
  `7` `preflight_ok` plus `18` `ssl_error`, dominated by `ecos.fws.gov`
  (`18`) and `www.fws.gov` (`5`).
- The current local promotion truth is now pinned exactly: non-strict
  `promotion-suite` still reports `current_promotion_ready=true` and
  `promotion_ready=true`, but the same local artifact also reports
  `full_canonical_corpus_ready=false`, `expansion_ready=false`, and
  `full_canonical_source_set_id=source-set-5e65d845ce77e1a0`.
- `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md`
  now treat the older `source-set-5e65d845ce77e1a0` full-canonical and
  all-green expansion claims as historical for this checkout until a later
  milestone explicitly restores or reruns those lanes.
- With the live baseline now locked, the next executable slice in this packet
  is Milestone 1: canonical preflight and fetch-failure closure.

Milestone 1 federal-blocker slice on 2026-05-18 after implementation
commit `cf2d5f6` (`Resolve unsupported-format canonical blocker slice`), the
earlier workbook repair slices, replay
`phase2-canonical-preflight-full-repaired-20260518`, the scoped
unsupported-format direct-document validation set, and the scoped federal
repair replay:

- The first Milestone 1 code/config slice is now live: `ecos.fws.gov` uses
  host-level verified `curl` transport through `config/downloader.toml`,
  `preflight.py`, and `download.py` because that host currently presents an
  incomplete TLS chain to the Python/OpenSSL path in this environment.
- The transport stays fail-closed: certificate verification remains enabled,
  no broad TLS bypass was added, and focused coverage landed in
  `tests/test_preflight.py` and `tests/test_download.py`.
- The completed host replay
  `phase2-canonical-preflight-ecos-replay-20260518` passed `27/27`
  `preflight_ok` with `failed_count=0` across the full `ecos.fws.gov`
  canonical-master host set.
- The governed workbook repair lane is now live on the canonical master sheet.
  `Document_Register_Master` now carries `55` governed URL repairs total:
  `45` earlier directive/USDA repairs,
  `3` stale-URL repairs for `PROG-008`, `STP-015`, and `STP-011`,
  `1` direct-artifact repair for `WILD-ESA-094`, and
  `6` federal/challenge repairs for `FED-042`, `FED-041`, `FED-039`,
  `FED-043`, `FED-029`, and `FPS-344`.
- `config/parser_admission_contract_v1.json` now also treats
  `www.archives.gov` and `www.govinfo.gov` as official structured authority
  hosts so those repaired federal rows stay on the structured-web path rather
  than falling through to generic fallback routing.
- `source-register-validate` now passes with `issue_count=0` on workbook SHA
  `b1628b6a6db11d73ef20dcde027531fbc7654db236c3b38fb07f21ff30249fff`.
- Scoped repair replay
  `phase2-canonical-preflight-directives-repair-validated-20260518`
  now passes `45/45` `preflight_ok` with `failed_count=0` across the repaired
  directive-family rows.
- Dedicated post-repair host replay
  `phase2-canonical-preflight-usda-post-directives-repair-validated-20260518`
  now proves the `www.usda.gov` blocker family is reduced from `15` rows to
  `6`: only `USDA-008`, `USDA-009`, `USDA-010`, `USDA-011`, `USDA-012`, and
  `USDA-013` remain on that host, and all `6` finalized as `timeout`.
- The fresh full-master replay
  `phase2-canonical-preflight-full-repaired-20260518`
  is now complete against the repaired workbook. It checked all `635`
  canonical URLs and finished with `607` `preflight_ok` plus `28` failed rows:
  `8` `not_found`, `8` `timeout`, `8` `unsupported_content_type`,
  `3` `rate_limited`, and `1` `challenge_page`.
- The scoped blocker replay
  `phase2-canonical-preflight-blocker-repair-slice-20260518`
  now passes `8/8` `preflight_ok` with `failed_count=0` across the `3`
  repaired stale-URL rows (`PROG-008`, `STP-015`, `STP-011`) plus the `5`
  previously failing `www.fs.usda.gov/media...` rows (`FOR-005`, `FPS-296`,
  `FPS-425`, `FPS-095`, `FPS-079`). Those `5` media rows are no longer active
  blocker rows for routing, but final confirmation still requires a fresh
  full-master replay after the remaining blocker families close.
- A broader replay under
  `source_library/runs/phase2-canonical-preflight-full-complete-20260518/`
  was intentionally stopped after `105` finalized rows once a second blocker
  class surfaced on `www.fs.usda.gov`. The partial event log records timeout
  rows for `USFS-024`, `USFS-034`, `USFS-008`, `USFS-016`, and `USFS-033`
  from the pre-repair workbook state. Those wrapper rows are now covered by
  the `45`-row Directives CGI repair slice above.
- Despite its `full-complete` run ID, that broader replay remains partial
  blocker evidence only. It must not be cited as a completed Milestone 1
  validation artifact or as a fresh full-master preflight closeout.
- The structural unsupported-format boundary slice is now live in code and
  workbook contract. `config/downloader.toml` now admits
  `application/msword` and `image/jpeg`,
  `config/parser_admission_contract_v1.json` now classifies `.doc` and
  image suffixes as `direct_document`,
  `download.py` plus `catalog.py` preserve those direct-artifact parser
  routes, and `extract.py` now uses macOS `textutil` for legacy `.doc`
  artifacts plus Docling for image artifacts.
- Scoped replay
  `phase2-canonical-preflight-unsupported-format-replay-20260518`
  now passes `8/8` `preflight_ok` with `failed_count=0` across
  `R1-021`, `R1-020`, `R1-019`, `R1-023`, `R1-022`, `R1-015`, `R1-009`, and
  `WILD-ESA-094`.
- Scoped download replay
  `phase2-canonical-download-unsupported-format-replay-20260518`
  now finishes with `downloaded_count=8`, `failed_count=0`, and
  `status_counts={"downloaded": 8}`.
- Scoped federal replay
  `phase2-canonical-preflight-federal-blocker-repair-validated-20260518`
  now passes `6/6` `preflight_ok` with `failed_count=0` across the repaired
  federal/challenge rows:
  `FED-042`, `FED-041`, `FED-039`, `FED-043`, `FED-029`, and `FPS-344`.
- Archived scoped catalog gate
  `source_library/runs/phase2-canonical-catalog-unsupported-format-replay-20260518/catalog_gate/`
  is now live as source set `source-set-a0402de124943920` with
  `source_count=8`,
  `artifact_count=8`, and
  `expected_parser_counts={"doc": 7, "image": 1}`.
- Scoped extraction on `source-set-a0402de124943920` now passes with
  `selected_source_count=8`,
  `extracted_count=8`,
  `parser_counts={"docling": 1, "macos_textutil_doc": 7}`, and
  extraction-accuracy admits all `8` direct-document rows with
  `knowledge_base_blocked_source_record_ids=[]`.
- Upstream direct eval remains green after the new admission path:
  `source_library/evaluations/upstream/upstream_evaluation_results.json`
  now reports `passed=true`, `case_count=38`, and `failed_case_ids=[]`.
- The historical full replay still records the `28` failed rows above, but the
  active unresolved blocker surface is now reduced to the `6`
  residual `www.usda.gov` timeout rows before the next full-master rerun:
  `USDA-012`, `USDA-013`, `USDA-009`, `USDA-010`, `USDA-008`, and `USDA-011`.
- Milestone 1 is still not resolved. The next truthful slice is the governed
  USDA transport/final-blocker closure packet for those `6` rows, then
  another fresh full-master canonical preflight replay. Do not start full
  `download`, `batch-download`, or `catalog-build` for the entire master sheet
  until those remaining blocker families close or are explicitly accepted.

## Dependency And Live Refresh Rule

This is a fresh standalone follow-on packet after the resolved
`docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md` packet. It does
not reopen the refoundation phases. It exists to finish the remaining import
work that the resolved refoundation packet intentionally left outside its
implementation boundary.

- Milestone 0 is now resolved through local commit `6a949ae`
  (`Resolve Milestone 0 canonical import rebaseline`). Start implementation
  from Milestone 1 unless the live baseline drifts first.
- If `source_library/catalog/`, the active promotion-suite artifacts, or the
  final workbook SHA drift before Milestone 1 starts, rerun the
  Milestone 0-style rebaseline and rewrite later milestone counts, source-set
  IDs, and run IDs before code or workbook changes begin.
- If a later session proves that the documented full-canonical catalog can be
  restored reproducibly from existing run evidence without hidden manual steps,
  pause Milestone 1, refresh this packet to that restored baseline, and record
  the change explicitly instead of silently reverting the docs-only rebaseline.
- If later milestones prove that direct-document queue promotion or downstream
  derived-lane replay is larger than this packet can close truthfully, this
  packet must stop after import truth is established and route the remaining
  work into a fresh follow-on milestone rather than silently broadening scope.

## Purpose

The refoundation plan is resolved as a contract and code packet, but the local
repo still does not expose one truthful answer to "what has actually been
imported from the canonical source register right now?" The remaining work is no
longer foundation-loader design. It is execution truth:

- settle the mismatch between durable routing docs and the local ignored
  `source_library`;
- remove ambiguous Phase 2 fetch failures from the active import path;
- run the actual full-register capture/catalog path for
  `Document_Register_Master`;
- keep `Direct_File_Capture_Queue` out of the active corpus unless rows are
  promoted through an explicit direct-file path; and
- close with durable docs and handoff language that matches the live imported
  catalog and its real residual blockers.

The repo should end this packet with one truthful active canonical import
baseline backed by real run artifacts, not a proving slice, not a planned-only
catalog gate, and not stale docs.

## Current Evidence

- `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md` is resolved
  and says the refoundation packet is complete, the canonical register is the
  sole active ledger, and the proving gate is in place.
- `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md`
  now pin the active local import baseline to proving source set
  `source-set-9dcf819bc4cca486` and treat the older
  `source-set-5e65d845ce77e1a0` full-canonical lane as historical preserved
  baseline evidence for this checkout. The remaining truth gap is no longer a
  doc-versus-manifest disagreement; it is that the active local import baseline
  is still a proving slice rather than a real full-register import.
- The local Phase 2 canonical catalog gate under
  `source_library/runs/canonical-source-register-phase2-catalog-gate-20260518/catalog_gate/`
  proves loader and row-shape readiness for all `635` master rows, but it is
  still planned-only:
  `artifact_count=0`, `download_run_id=null`, `status_counts={"planned": 635}`,
  and `source_partition_counts={"candidate_blocked_source": 635}`.
- The full-register dry run under
  `source_library/runs/phase2-canonical-dry-run-20260518/summary.json` proves
  the master load-sheet scope is `635` canonical rows and `635` unique URLs.
- The sampled canonical preflight under
  `source_library/runs/phase2-canonical-preflight-20260518/summary.json` only
  checked `25` URLs and recorded `7` `preflight_ok` plus `18` `ssl_error`,
  dominated by `ecos.fws.gov` and `www.fws.gov`.
- The final workbook contract remains:
  `Document_Register_Master=635`,
  `Direct_File_Capture_Queue=51`,
  `Removed_Not_Applicable_Final=2`.
  The queue is still dominated by folder/listing/manual-export placeholders and
  unresolved forest-plan support URLs, so import closeout must preserve explicit
  queue discipline.
- The local non-strict promotion-suite artifact at
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  currently reports `current_promotion_ready=true` but also
  `full_canonical_corpus_ready=false` and `expansion_ready=false`. That local
  artifact remains an explicit downstream-truth boundary that later milestones
  must either rerun or keep marked historical rather than ignoring.

## Goal

Import the canonical source register truthfully enough that the local repo can
answer all of the following from live artifacts without contradiction:

- what the active canonical workbook is;
- what the active imported source set is;
- how many `Document_Register_Master` rows were actually captured, blocked, or
  deferred;
- which rows are still outside the corpus because they belong in
  `Direct_File_Capture_Queue` or remain explicit blockers; and
- whether downstream full-canonical and promotion lanes were refreshed, still
  stale, or intentionally left for a follow-on packet.

Completion means the active catalog is backed by a real full-register
download/batch-download plus `catalog-build` path for the master sheet, the
docs/handoff match that live state, and no durable file still answers from the
proving slice or planned-only Phase 2 gate as if it were the imported corpus.

## Non-Goals

- Do not reopen the resolved refoundation plan as a new Phase 9.
- Do not claim reviewer-ready direct-document downstream truth for the entire
  canonical corpus unless the required derived-lane replays are actually rerun
  in this packet.
- Do not treat `Direct_File_Capture_Queue`, listing pages, project pages,
  wrapper pages, manual-export placeholders, or unresolved support URLs as
  corpus-ready source documents.
- Do not weaken TLS verification globally, add broad allowlists, or suppress
  `ssl_error` handling just to make preflight or download green.
- Do not use the legacy forest-plan source-delta register as an active import
  bypass for `source_register_v1`.
- Do not overwrite or silently replace local ignored `source_library` evidence
  unless the replacement path is reproducible and documented in the same
  milestone closeout.

## Scope

- live-state rebaseline between durable docs and local ignored artifacts
- canonical preflight and host-failure closure for `Document_Register_Master`
- full-register `download` or `batch-download`, `validate-run`, and
  `catalog-build` on the canonical master sheet
- queue-boundary preservation and direct-file promotion discipline
- active catalog validation and truthful docs/handoff closeout

## Out Of Scope

- full downstream retrieval, evidence-graph, claim, rule-binding, and review
  readiness across the newly imported canonical corpus unless those replays are
  explicitly proven necessary to keep import docs truthful
- broad workbook restructuring beyond the row-level URL or queue-state fixes
  required for this import packet
- unrelated forest-profile, review-package, or viewer work

## Owner Surfaces

- workbook and loader contract owners:
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `src/usfs_r1_ea_sources/workbook.py`,
  `src/usfs_r1_ea_sources/source_register.py`,
  `config/source_register_sheet_contract_v1.json`,
  `config/source_register_row_states_v1.json`,
  `config/direct_file_readiness_contract_v1.json`
- capture and preflight owners:
  `src/usfs_r1_ea_sources/cli_capture.py`,
  `src/usfs_r1_ea_sources/preflight.py`,
  `src/usfs_r1_ea_sources/download.py`,
  `src/usfs_r1_ea_sources/batches.py`,
  `src/usfs_r1_ea_sources/validate_run.py`,
  `config/downloader.toml`
- catalog and partition owners:
  `src/usfs_r1_ea_sources/catalog.py`,
  `src/usfs_r1_ea_sources/catalog_surface.py`,
  `src/usfs_r1_ea_sources/source_partitions.py`
- focused tests:
  `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_preflight.py`,
  `tests/test_download.py`,
  `tests/test_batches.py`,
  `tests/test_validate_run.py`,
  `tests/test_catalog.py`,
  `tests/test_captured_library.py`,
  `tests/test_upstream_evaluation.py`,
  `tests/test_cli.py`,
  `tests/test_architecture_contract.py`
- durable routing owners:
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan file

## Placement Rules

- Keep import behavior in the existing capture/preflight/download/catalog
  modules. Do not create a sidecar script that mutates `source_library/catalog/`
  outside the governed CLI path.
- Keep queue and row-state truth in the workbook contract plus the existing
  canonical row-state and direct-file-readiness config surfaces. Do not create a
  second hidden register for queue promotion.
- Keep host-specific failure handling in `config/downloader.toml`,
  `preflight.py`, and `download.py` with focused tests. Do not implement
  host-specific behavior as undocumented one-off terminal commands.
- Keep active catalog identity in `source_set_manifest.json`,
  `catalog_validation.json`, and the exact run IDs that produced them. Do not
  rely on README or handoff prose as the only evidence of import truth.
- Preserve workbook row identity, source-record IDs, original/effective URLs,
  artifact hashes, source partitions, and explicit blocker evidence during the
  import.
- Leave `source_library/` ignored. Closeout must cite local run IDs and artifact
  paths in docs/handoff rather than trying to stage generated outputs.

## Weak-Point Prevention Contract

### Weak Point 1: Docs and local import artifacts keep disagreeing

- Weak point forecast: a future session could keep answering from
  `README.md` or `docs/CURRENT_SYSTEM_STATE.md` while the active local catalog
  still points at a different source set.
- Owner surface:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `source_library/catalog/source_set_manifest.json`.
- Prevention gate: Milestone 0 must compare live manifest IDs/counts against the
  durable docs and record one active import baseline before any import changes.
- Fail threshold: any closeout doc still names `source-set-5e65d845ce77e1a0`
  as active while `source_library/catalog/` names another source set, or a
  restore path is used without matching run evidence.
- Controlled violation: keep one durable doc pinned to the old active catalog ID
  after Milestone 0 or swap `source_library/catalog/` without updating the
  closeout note; the milestone must fail.
- Future-Codex misuse scenario: a later session trusts stale prose instead of
  the live manifest. This packet must make that wrong pattern fail loudly.

### Weak Point 2: The import is faked by a planned-only catalog gate

- Weak point forecast: the repo could keep the `635`-row planned Phase 2 gate
  and talk about "imported canonical corpus" without a real download or batch
  run.
- Owner surface:
  `cli_capture.py`, `download.py`, `batches.py`, `validate_run.py`,
  `catalog.py`, `tests/test_catalog.py`, `tests/test_captured_library.py`.
- Prevention gate: closeout must prove an active catalog built from real
  `download_run_id` or `download_batch_run_ids`, plus a nonzero
  `artifact_count` and truthful source-partition counts.
- Fail threshold: the active catalog still has `download_run_id=null` and
  `artifact_count=0`, or the active manifest cannot be tied to the exact run IDs
  that produced it.
- Controlled violation: mutate a fixture or the active manifest so it reports
  only `planned` statuses or drops run IDs; catalog validation or focused tests
  must fail.
- Future-Codex misuse scenario: someone reuses the planned Phase 2 gate as if it
  were the imported corpus. This packet must force a run-backed import truth.

### Weak Point 3: SSL and host failures are papered over by weaker network rules

- Weak point forecast: ambiguous `ssl_error` rows could be "fixed" by broad TLS
  weakening, blanket user-agent changes, or skipping hard hosts.
- Owner surface:
  `config/downloader.toml`, `preflight.py`, `download.py`,
  `tests/test_preflight.py`, `tests/test_download.py`,
  `tests/test_upstream_evaluation.py`.
- Prevention gate: host-specific fixes must preserve TLS verification defaults,
  emit explicit failure evidence, and keep challenge/not-found/wrapper-page
  detection fail-closed.
- Fail threshold: global TLS verification is weakened, a host-specific bypass is
  undocumented, or an `ssl_error` becomes `preflight_ok` without validated
  content evidence.
- Controlled violation: a focused fixture converts a broken TLS or wrapper-page
  response into a nominal pass; the targeted preflight or upstream-eval gate
  must fail.
- Future-Codex misuse scenario: a later session "solves" stubborn hosts by
  relaxing validation. This packet must preserve the downloader rules boundary.

### Weak Point 4: Queue rows leak into the imported corpus

- Weak point forecast: during full-register import, queue rows or unresolved
  placeholders could silently enter `active_review_corpus` or lose explicit
  blocker classification.
- Owner surface:
  the workbook,
  `source_register.py`,
  `source_partitions.py`,
  `catalog.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_source_register_loader.py`,
  `tests/test_catalog.py`.
- Prevention gate: the import path must continue to load only
  `Document_Register_Master`, and any queue promotion must first land as an
  explicit workbook-side direct official file row before it can enter the active
  corpus.
- Fail threshold: `Direct_File_Capture_Queue` rows appear in the active catalog
  without workbook promotion, or unresolved placeholders lose explicit blocker
  state.
- Controlled violation: mutate a loader or catalog fixture so queue rows enter
  the active catalog directly; the schema/loader/catalog tests must fail.
- Future-Codex misuse scenario: a later session treats the queue as an optional
  second load sheet. This packet must keep the one-load-sheet contract intact.

### Weak Point 5: Docs overclaim downstream readiness after import

- Weak point forecast: once the full-register catalog is imported, the repo
  could continue to claim old full-canonical or promotion results that were
  produced against another source set or not rerun at all.
- Owner surface:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `source_library/reviews/promotion_suite/.../promotion_suite_results.json`,
  `phase-eval` source-set artifacts when rerun.
- Prevention gate: docs closeout must distinguish imported-catalog truth from
  downstream replay truth. Any unchanged downstream lane must be called
  historical, stale, or not rerun rather than silently reused as current truth.
- Fail threshold: docs present downstream `full_canonical_corpus_ready`,
  `expansion_ready`, or source-set readiness claims as current without matching
  rerun artifacts.
- Controlled violation: leave one doc asserting old promotion-suite truth after
  import while not rerunning the suite; the docs freshness gate must fail.
- Future-Codex misuse scenario: a future session assumes import completion
  implies full downstream replay. This packet must keep those boundaries
  explicit.

## Milestone Sequence

### Milestone 0 - Live Rebaseline And Active Import Baseline Lock

Outcome label: resolved

Closed on 2026-05-18 by local commit `6a949ae`
(`Resolve Milestone 0 canonical import rebaseline`).

Purpose: settle the durable-doc versus local-artifact mismatch and record the
exact active baseline this import packet will replace or continue from.

Implementation tasks:

1. Compare the live local artifacts and durable routing docs for:
   - `source_library/catalog/source_set_manifest.json`
   - `source_library/runs/canonical-source-register-phase2-catalog-gate-20260518/catalog_gate/source_set_manifest.json`
   - `source_library/runs/phase2-canonical-dry-run-20260518/summary.json`
   - `source_library/runs/phase2-canonical-preflight-20260518/summary.json`
   - `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
   - `README.md`
   - `docs/CURRENT_SYSTEM_STATE.md`
   - `docs/SESSION_HANDOFF.md`
2. Choose and document one truth-preserving starting state:
   - rebaseline docs to the actual local proving-slice and Phase 2 gate state;
     or
   - restore the documented full-canonical catalog only if the restore path is
     reproducible from named run evidence and does not silently overwrite unique
     local evidence.
3. Record the exact workbook SHA, active source-set ID, Phase 2 gate source-set
   ID, current promotion-suite truth, and the import path that Milestone 1 will
   follow.
4. Add or refresh a docs-freshness check so future closeout cannot mix the old
   documented full-canonical source set with a different active local catalog.

Required implementation artifacts:

- this plan file with Milestone 0 baseline values refreshed if the live state
  drifts before implementation starts
- a new top handoff note routing to this plan
- durable doc updates that truthfully name the selected active import baseline

Verification:

```bash
python - <<'PY'
import json, pathlib
for path in [
    "source_library/catalog/source_set_manifest.json",
    "source_library/runs/canonical-source-register-phase2-catalog-gate-20260518/catalog_gate/source_set_manifest.json",
    "source_library/runs/phase2-canonical-dry-run-20260518/summary.json",
    "source_library/runs/phase2-canonical-preflight-20260518/summary.json",
    "source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json",
]:
    print(path)
    print(json.dumps(json.loads(pathlib.Path(path).read_text()), indent=2)[:2000])
PY

rg -n "source-set-|full_canonical_corpus_ready|expansion_ready|Local active import baseline|Historical broader capture baseline|Historical documented full-corpus promotion baseline" \
  README.md docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md

python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/CANONICAL_SOURCE_REGISTER_IMPORT_COMPLETION_MILESTONE_PLAN.md

git diff --check
```

Acceptance signals:

- The repo has one explicit active import baseline recorded in durable docs and
  handoff.
- No durable routing doc still silently treats the proving slice and the older
  full-canonical source set as the same live state.
- If a restore path is chosen, it is backed by named run evidence in the same
  closeout note.

Milestone 0 stop conditions:

- The active local catalog cannot be tied to a reproducible source-set or run
  family.
- A restore path would overwrite unique local evidence without a reversible,
  documented procedure.

### Milestone 1 - Canonical Preflight And Fetch-Failure Closure

Outcome label: resolved

Purpose: remove ambiguous canonical-master fetch blockers from the import path
without weakening downloader safety or queue discipline.

Implementation tasks:

1. Expand canonical preflight beyond the current `25`-URL sample to a governed
   full-master or host-complete coverage run against
   `Document_Register_Master`.
2. Triage the observed `ssl_error` failures, starting with `ecos.fws.gov` and
   `www.fws.gov`, and determine whether each class requires:
   - a legitimate host-specific runtime/config change;
   - a workbook URL correction to a better official source;
   - queue deferral because only a wrapper/manual-export path exists; or
   - explicit blocker retention in the master import path.
3. Implement only truth-preserving fixes:
   - no global TLS weakening;
   - no silent override of canonical workbook URLs outside governed surfaces;
   - no conversion of wrapper/listing pages into `preflight_ok`.
4. Add or tighten focused negative coverage for SSL handling, wrapper-page
   misclassification, queue leakage, and preserved blocker status.
5. Produce a refreshed preflight summary that covers the full intended import
   scope and names the exact remaining blocked rows, if any.

Required implementation artifacts:

- refreshed canonical preflight run summaries and manifests under
  `source_library/runs/`
- any required focused config/code/test updates for host handling
- docs or handoff note naming the exact remaining master-row blocker classes

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_preflight.py \
  tests/test_download.py \
  tests/test_validate_run.py \
  tests/test_upstream_evaluation.py \
  tests/test_cli.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src uv run --extra dev ruff check \
  src/usfs_r1_ea_sources/preflight.py \
  src/usfs_r1_ea_sources/download.py \
  src/usfs_r1_ea_sources/cli_capture.py \
  tests/test_preflight.py \
  tests/test_download.py \
  tests/test_validate_run.py \
  tests/test_upstream_evaluation.py \
  tests/test_cli.py

git diff --check
```

Acceptance signals:

- The canonical preflight covers the full intended import scope, not only a
  small sample.
- Remaining non-`preflight_ok` master rows are explicit and truthfully routed as
  blockers or queue-boundary cases rather than ambiguous network failures.
- No fix weakens TLS or the downloader/content validation rules.

Milestone 1 stop conditions:

- The only way to make the affected hosts green is a global TLS bypass or an
  undocumented host exception.
- A material subset of master rows actually belongs in queue or workbook repair
  work larger than this milestone can close safely.

### Milestone 2 - Full Master Capture And Catalog Import

Outcome label: resolved

Purpose: run the real canonical-master capture/catalog path and replace the
planned-only Phase 2 gate with an artifact-backed active catalog.

Implementation tasks:

1. Run the actual import on `Document_Register_Master` through governed
   `download` or `batch-download` after Milestone 1 closes.
2. Run `validate-run` and `catalog-build` against the exact run ID or batch run
   IDs produced by the import.
3. Promote the resulting artifact-backed catalog into `source_library/catalog/`
   and ensure the manifest records:
   - the real `download_run_id` or `download_batch_run_ids`;
   - nonzero artifact counts where rows were actually captured;
   - truthful source partitions for active, blocked, duplicate, and
     supersession-only rows; and
   - no queue-sheet leakage into the active corpus.
4. Preserve `Direct_File_Capture_Queue` as non-load truth. A queue row may only
   enter the imported corpus if the workbook is updated with a direct official
   source row in `Document_Register_Master` and the relevant schema/loader
   checks still pass.
5. If active import still retains explicit blocked master rows, keep them as
   visible blocker evidence rather than forcing them green by policy change.

Required implementation artifacts:

- full-register canonical download or batch-download run(s)
- matching `validate-run` output
- refreshed active `source_library/catalog/` manifest, validation, graph-node,
  and graph-edge surfaces
- focused tests and config/code changes required to keep the import truthful

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library

PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library

PYTHONPATH=src python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id <canonical-run-id>

PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --batch-run-id <canonical-batch-run-id>

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_source_register_loader.py \
  tests/test_source_register_schema.py \
  tests/test_batches.py \
  tests/test_download.py \
  tests/test_validate_run.py \
  tests/test_catalog.py \
  tests/test_captured_library.py \
  tests/test_cli.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src uv run --extra dev ruff check \
  src/usfs_r1_ea_sources/workbook.py \
  src/usfs_r1_ea_sources/source_register.py \
  src/usfs_r1_ea_sources/cli_capture.py \
  src/usfs_r1_ea_sources/download.py \
  src/usfs_r1_ea_sources/batches.py \
  src/usfs_r1_ea_sources/validate_run.py \
  src/usfs_r1_ea_sources/catalog.py \
  src/usfs_r1_ea_sources/source_partitions.py \
  tests/test_source_register_loader.py \
  tests/test_source_register_schema.py \
  tests/test_batches.py \
  tests/test_download.py \
  tests/test_validate_run.py \
  tests/test_catalog.py \
  tests/test_captured_library.py \
  tests/test_cli.py

git diff --check
```

Acceptance signals:

- `source_library/catalog/source_set_manifest.json` is backed by a real
  full-register import rather than the planned-only Phase 2 gate.
- The active catalog names exact run IDs and reports real artifact counts.
- Queue rows remain out of the active corpus unless the workbook explicitly
  promotes them first.
- Any residual blocked master rows remain explicit in source partitions and docs.

Milestone 2 stop conditions:

- The only way to finish import is manual artifact copying that is not
  represented by workbook rows, direct-file governance, or explicit blocker
  evidence.
- The active catalog cannot be rebuilt reproducibly from exact run IDs.

### Milestone 3 - Post-Import Truth Refresh And Durable Closeout

Outcome label: resolved

Purpose: make durable docs and truth-report artifacts match the imported
catalog without overstating downstream replay readiness.

Implementation tasks:

1. Rerun or explicitly re-read the truth-report artifacts that the durable docs
   use after import:
   - active `source_library/catalog/` manifest and validation;
   - current promotion-suite artifact if it is still cited as current truth;
   - any source-set `phase-eval` or adjacent report that the closeout will call
     "current".
2. Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
   `docs/SESSION_HANDOFF.md` so they name:
   - the active imported source-set ID;
   - the exact import run IDs;
   - the real partition counts for active, blocked, and supersession-only rows;
   - whether promotion-suite or downstream full-canonical replay was rerun in
     this packet; and
   - any residual blockers or follow-on lane that remains open.
3. If downstream full-canonical replay is not rerun here, mark the older
   downstream claims as historical or stale rather than current truth.
4. Close out this plan and route any residual direct-document queue or
   downstream replay work into one fresh follow-on packet.

Required implementation artifacts:

- refreshed durable docs and handoff
- any rerun truth-report outputs used by those docs
- closeout note in this plan recording the exact imported catalog identity and
  residual next route

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

rg -n "source-set-|full_canonical_corpus_ready|expansion_ready|Local active import baseline|Historical broader capture baseline|Historical documented full-corpus promotion baseline" \
  README.md docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md

python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/CANONICAL_SOURCE_REGISTER_IMPORT_COMPLETION_MILESTONE_PLAN.md

git diff --check
```

Acceptance signals:

- The durable docs and handoff agree with the live imported catalog.
- Any unchanged downstream artifact family is explicitly marked historical,
  stale, or not rerun rather than silently reused as current truth.
- This plan and the handoff identify one exact next packet if import completion
  still leaves downstream replay or queue-promotion work open.

Milestone 3 stop conditions:

- The closeout would require claiming downstream replay freshness that was not
  actually rerun.
- The imported catalog truth and the available docs cannot be reconciled without
  a broader artifact-restoration project.

## Required Implementation Artifacts

- fresh Milestone 0 rebaseline note in `docs/SESSION_HANDOFF.md`
- any import-owner code/config/test changes required by Milestones 1 and 2
- full canonical preflight, import, validation, and catalog local run artifacts
  under `source_library/runs/` and `source_library/catalog/`
- durable docs updated to the imported catalog truth:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- this plan file updated with closeout notes and exact run/source-set IDs as
  milestones land

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan file

If import closeout changes the truth relationship between the resolved
refoundation plan and this new packet, add one narrow routing note to
`docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md` rather than
rewriting its closed milestone history.

## Required Verification Gates

- Docs-only Milestone 0 closeout:
  - milestone-plan lint
  - `git diff --check`
  - explicit manifest/doc comparison
- Source/config/test Milestones 1 and 2 closeout:
  - focused pytest suites for touched modules
  - `ruff check` on touched files
  - live preflight/download/catalog commands for the milestone scope
  - `tests/test_architecture_contract.py` whenever CLI or owner boundaries move
- Docs-and-truth Milestone 3 closeout:
  - rerun or explicitly inspect every artifact named as current truth in docs
  - milestone-plan lint
  - `git diff --check`

## Acceptance Criteria

- The final workbook remains the sole active human-authored source ledger for
  import, and `Document_Register_Master` remains the only active load sheet.
- The active local catalog is no longer a proving slice or planned-only gate.
- The active catalog can be tied to exact import run IDs and real artifact
  counts.
- `Direct_File_Capture_Queue` remains explicit and non-load unless rows are
  promoted through a direct official file path in the workbook.
- Any remaining blocked master rows remain explicit as blockers, not hidden by
  relaxed validation.
- Durable docs and handoff match the live imported catalog and do not overclaim
  downstream freshness.

## Stop Conditions

- Import truth cannot be established without global TLS weakening, a second
  hidden register, or untracked manual artifact copying.
- The local `source_library` state is too inconsistent to rebaseline or restore
  without a broader evidence-recovery packet.
- Full downstream replay becomes necessary to answer import truthfully and is
  materially larger than the selected import boundary.

## Local Commit Closeout Policy

- Complete-after-commit rule: no milestone may be marked complete, `resolved`,
  or `reduced`. A milestone is not complete until its required verification
  passes and its local atomic commit lands.
- Follow the repo's milestone-by-milestone atomic commit rule.
- Milestone 0 may land as a docs-only commit if it changes only routing docs and
  this plan file.
- Milestones 1 and 2 must commit the exact verified code/config/test/doc slice
  needed for the import milestone and must not stage unrelated ignored
  `source_library` outputs.
- Generated local run artifacts remain ignored evidence; commit the code, tests,
  configs, docs, and handoff updates that prove how those runs were produced and
  what they mean.

## Residual Risks And Next Milestone Routing

- If the full-register catalog imports cleanly but downstream full-canonical
  derived lanes still point at older source sets, route that work into a fresh
  follow-on packet for full-canonical replay and promotion truth rather than
  folding it into this import packet late.
- If queue-heavy direct-document rows still require substantial workbook
  promotion or manual official-source discovery after Milestone 2, route that
  work into a dedicated direct-file queue resolution packet rather than
  broadening Milestone 2 indefinitely.
- If Milestone 0 proves the documented full-canonical catalog can be restored
  cleanly before any new import work, update this plan's later milestones to
  start from that restored baseline and keep the rebaseline note as historical
  evidence.
