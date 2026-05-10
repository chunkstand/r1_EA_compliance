# Region 1 Forest-Plan Source-Delta Readiness Milestone Plan

Date: 2026-05-10

## Outcome

This milestone completes Region 1 forest-plan support-document readiness by turning the promoted
register and captured source-delta rows into an auditable corpus layer that can support forest-plan
review beyond the Custer Gallatin proving package.

The milestone is complete only when the system can prove, from register, batch, catalog, extraction,
retrieval, and readiness artifacts, that:

- every required Region 1 forest-plan support document is either in the corpus, already confirmed in
  the canonical workbook/catalog contract, or carried as an explicit official-source gap;
- all find/download work is documented through official-source evidence, not ad hoc local files;
- the `159` captured source-delta rows have extracted text, parser diagnostics, chunks, and retrieval
  inputs or explicit parser/blocker records;
- the canonical 190-row corpus and the Region 1 support-document source delta can be incorporated
  into one reviewable corpus view without losing source-row identity or weakening catalog validation;
- forest-plan resolver/readiness outputs can consume the support-document corpus through catalog
  surfaces instead of raw artifact paths.

## Current Baseline

Already completed:

- Register: `config/r1_forest_plan_document_register_draft.csv`
  - `189` rows
  - `28` catalog-confirmed rows
  - `159` corpus-ready source-delta rows
  - `2` documented official-source gaps
- Source-delta capture:
  - parent run: `r1-forest-plan-source-delta-capture-20260510-batches`
  - `33/33` child batches passed
  - `159` planned rows
  - `158` unique artifacts
  - repair queue empty except header
- Scoped source-delta catalog gate:
  - archived path:
    `source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/catalog_gate/`
  - source set: `source-set-411b3736b3691eed`
  - `159` `forest_plan_support` rows
  - `158` artifacts
  - `159` `active_review_corpus` rows
  - catalog validation passed
- Active canonical catalog restored:
  - parent run: `corpus-update-2026-05-01-cg-support-batches`
  - latest regenerated catalog source set: `source-set-d3b9e2a728accda6`
  - promoted downstream V1 derived source set remains `source-set-ba8d0feae79501b8`
- Official-source gap evidence:
  - tracked config: `config/r1_forest_plan_official_source_gap_evidence.json`
  - evidence date: `2026-05-10`
  - schema: `r1-forest-plan-official-source-gap-evidence-v0`
  - gap records: `R1PLAN-kootenai-nf-18`,
    `R1PLAN-nez-perce-clearwater-nfs-18`

Known official-source gaps:

- `R1PLAN-kootenai-nf-18`: Kootenai plan-level Biological Assessment. The 2026-05-10 official
  source check confirmed that current official planning pages expose Biological Opinion chapters
  1-4, but no current official plan-level BA PDF was found.
- `R1PLAN-nez-perce-clearwater-nfs-18`: Nez Perce-Clearwater project record / revision support
  package. The 2026-05-10 official source check confirmed that the current official 2025 LMP page
  links a Box plan revision project record URL, but live access returned `404`.

Readiness gate implementation status:

- Implemented command:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-batches --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json`
- Generated report family:
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/source_delta_readiness/r1_forest_plan_source_delta_readiness_report.json`
  and `.md`
- Live result: passed with `0` failed checks, `159` captured source-delta rows, scoped source set
  `source-set-411b3736b3691eed`, active canonical source set `source-set-d3b9e2a728accda6`, and
  extraction/retrieval readiness recorded as `not_started`. The report schema is now
  `r1-forest-plan-source-delta-readiness-v1` and includes a fail-closed check that the tracked gap
  evidence matches the current register gap IDs.
- Remaining blockers: downstream extraction/retrieval readiness for the scoped support-document
  source set, plus the two preserved official-source gaps unless future official URLs are found and
  targeted preflight passes.

Merged catalog implementation status:

- `catalog-build` accepts repeated `--batch-run-id` values and `--catalog-dir`.
- Live archived merged gate:
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/`
- Merged source set: `source-set-7e2652d23e764068`
- Inputs: canonical batch run `corpus-update-2026-05-01-cg-support-batches`, source-delta batch run
  `r1-forest-plan-source-delta-capture-20260510-batches`, and
  `config/r1_forest_plan_document_register_draft.csv`.
- Live result: `349` source rows, `318` artifacts, `331` unique URLs, `348`
  `active_review_corpus` rows, `1` `candidate_blocked_source` row, `159` supplemental source-delta
  rows, `0` `not_in_run` rows, and catalog validation passed with `0` failed checks.
- Active canonical catalog remains `source-set-d3b9e2a728accda6` under `source_library/catalog/`.

## Weak-Point Prevention Contract

- Weak point forecast: stale or missing source-delta gate artifacts could let later sequences build
  on an unverified support-document baseline.
- Owner surface: `forest_plan_source_delta_readiness.py`, the source-delta batch run directory, the
  archived scoped catalog gate, and the active canonical catalog.
- Prevention gate: `forest-plan-source-delta-readiness` fails when required batch, ledger,
  repair-queue, scoped catalog, canonical catalog, or official-source gap evidence files are absent
  or invalid.
- Fail threshold: any missing required artifact, non-passing scoped catalog validation, non-passing
  canonical catalog validation, source-delta/source-register mismatch, or canonical source count not
  equal to `190` fails the milestone. Missing, stale, duplicate, or replacement-accepting gap
  evidence also fails the gate.
- Controlled violation: focused tests remove the scoped catalog gate, remove one source-delta ID
  from the gate fixture, and omit official-source gap evidence; all negative cases must fail before
  the command can be accepted.
- Future-Codex misuse scenario: a later session might scan raw artifacts, collapse
  catalog-confirmed rows into the source-delta set, or silently omit gap rows. This contract
  prevents that by requiring the gate to read register, batch, catalog, extraction, retrieval, and
  profile-placeholder surfaces and to list the two gap IDs as explicit blockers.

## Non-Goals

- Do not broaden this milestone into a full Region 1 EA package review.
- Do not change the legal or reviewer-ready claim for the promoted East Crazies V1 package.
- Do not stage ignored `source_library/` outputs unless repository policy changes.
- Do not treat the two official-source gap rows as downloaded or corpus-ready without replacement
  official links or an accepted gap policy.
- Do not scan raw artifact filenames for readiness decisions. Use catalog, manifest, extraction,
  retrieval, and readiness surfaces.
- Do not collapse canonical workbook rows and support-document register rows when they share URLs or
  artifacts.

## Readiness Definition

Use these readiness states throughout the milestone:

- `register_ready`: every required support-document row has a valid register disposition and stable
  source record ID.
- `official_source_resolved`: a row has an official HTTP(S) URL that can be planned and preflighted.
- `official_source_gap`: official sources were searched and a current official URL is still absent
  or blocked; the row is excluded from download planning and listed with evidence.
- `capture_ready`: the planned row is covered by a passing download manifest row or an accepted
  non-artifact duplicate/content status.
- `catalog_ready`: catalog validation passes for the scoped or merged corpus view.
- `extraction_ready`: each artifact has extracted text/chunks or an explicit parser/blocker record.
- `retrieval_ready`: each extracted/chunked source is present in retrieval inputs and retrieval
  validation artifacts.
- `forest_plan_review_ready`: resolver/readiness artifacts can prove required plan/supporting
  evidence for a forest profile from catalog/retrieval surfaces.

## Milestone Sequences

### Sequence 0 - Readiness Baseline And Stop Conditions

Goal: freeze the current source-delta baseline and create the working evidence map for this
milestone.

Implementation tasks:

- Add a generated or tracked readiness report that reads the register, batch summary, scoped catalog
  gate, canonical catalog, and gap rows.
- Record counts for register rows, source-delta captured rows, official-source gaps, catalog
  validation, extraction coverage, parser blockers, retrieval coverage, and forest-profile
  readiness.
- Fail closed when any required artifact is missing, stale, or inconsistent.
- Keep the two gap rows visible as blockers, not as silent omissions.

Acceptance signals:

- Readiness report lists `159` captured support-document rows and the two gap IDs.
- Report distinguishes the scoped source-delta catalog from the active canonical 190-row catalog.
- Focused tests cover missing/stale source-delta catalog gate artifacts.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-batches
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_captured_library.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The scoped source-delta catalog gate cannot be found or no longer validates.
- The active canonical catalog no longer validates against `tests/test_captured_library.py`.

### Sequence 1 - Official-Source Gap Resolution

Goal: close, or explicitly preserve, the two remaining official-source gaps before claiming full
Region 1 support-document coverage.

Implementation tasks:

- Research only official sources for:
  - `R1PLAN-kootenai-nf-18`
  - `R1PLAN-nez-perce-clearwater-nfs-18`
- For each candidate URL, record:
  - source record ID;
  - official page or file URL;
  - access result;
  - content type;
  - reason accepted or rejected;
  - search date;
  - operator notes.
- If an official source is found, update the register row from
  `official_source_gap_documented` to `source_delta_required` only after a targeted preflight
  passes.
- If no official source is found, retain `official_source_gap_documented` and update the gap
  evidence notes with checked official locations.

Acceptance signals:

- Each gap row has either a passing official-source preflight or a current gap evidence record.
- No non-official mirror, search result, or local copy is treated as a replacement source.
- Register validation still reports no duplicate IDs and no unsupported statuses.

Implementation status:

- Complete for the current official-source pass. No replacement URL was accepted.
- `config/r1_forest_plan_official_source_gap_evidence.json` records the checked official pages and
  rejected candidates for both remaining gap rows.
- `config/r1_forest_plan_document_register_draft.csv` preserves both rows as
  `official_source_gap_documented` and points to the tracked evidence file in the notes.
- The readiness gate now fails if these evidence records are missing, stale relative to the register
  gap IDs, or mark a replacement source accepted without the register moving through targeted
  preflight and status promotion.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_r1_forest_plan_document_register.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness \
  --output-dir source_library \
  --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv \
  --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-batches \
  --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv \
  --source-delta-only \
  --id <resolved-gap-source-id>
git diff --check
```

The targeted preflight command applies only if a gap row is promoted to `source_delta_required`;
the 2026-05-10 pass found no accepted replacement URL, so no gap-source preflight was run.

Stop conditions:

- A replacement URL is not clearly official.
- A candidate returns a challenge, not-found body, empty body, unsupported content type, or blocked
  response.

### Sequence 2 - Targeted Gap Capture And Register Re-Capture

Goal: capture any newly resolved gap rows without rerunning unrelated source rows.

Implementation tasks:

- If Sequence 1 resolves one or both gaps, run targeted `dry-run`, `preflight`, and `batch-download`
  with `--source-delta-only` and selected IDs.
- Validate child manifests and repair queue.
- Archive a new scoped catalog gate for the incremental capture, or rerun the scoped source-delta
  catalog gate if the source-delta row universe changes from `159`.
- Preserve the previous capture run as historical evidence.

Acceptance signals:

- New gap rows, if resolved, have passing manifests and artifacts.
- Updated source-delta row count is reflected in the readiness report.
- Repair queue is empty or contains explicit non-ready rows.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix r1-forest-plan-source-delta-gap-capture-<date> \
  --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv \
  --source-delta-only \
  --batch-size 5
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id <gap-or-full-source-delta-parent-run-id> \
  --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv \
  --source-delta-only
```

Stop conditions:

- Any batch stops with `failed` or `needs_repair`.
- Catalog validation reports unknown source IDs, duplicate source IDs, missing child manifests, or
  ledger/manifest row mismatch.

### Sequence 3 - Merged Corpus Catalog Contract

Goal: create a single corpus catalog view that incorporates the canonical workbook corpus and the
Region 1 forest-plan support-document source delta without rerunning unnecessary downloads.

Implementation tasks:

- Implement one explicit merge strategy:
  - preferred: allow `catalog-build` to consume multiple batch parent runs and merge manifest records
    by source record ID; or
  - alternative: generate a composite parent batch ledger that references the canonical
    `corpus-update-2026-05-01-cg-support-batches` child manifests plus the source-delta child
    manifests.
- Run merged catalog build with the register supplied but without `--source-delta-only`.
- Preserve one catalog record per canonical workbook row and one catalog record per emitted
  source-delta row.
- Make `source_delta_input`, supplemental counts, and source filters visible in
  `source_set_manifest.json`.
- Keep catalog validation strict for unknown rows and duplicate rows.

Acceptance signals:

- Merged catalog source count equals canonical workbook rows plus emitted source-delta rows.
  With the current baseline this is `190 + 159 = 349` source rows.
- Catalog validation passes.
- SQLite tables, graph seed JSONL, citation labels, and source partitions include both canonical and
  support-document rows.
- Existing `tests/test_captured_library.py` continues to validate the canonical view, or a new
  explicit test validates the merged view without replacing the canonical gate accidentally.

Implementation status:

- Complete for the current baseline.
- Merge strategy: `catalog-build` consumes multiple parent batch runs directly through repeated
  `--batch-run-id`; no composite batch ledger is required.
- Archive strategy: `--catalog-dir` writes merged catalog artifacts outside `source_library/catalog/`
  so the canonical gate remains intact.
- Controlled violation: unit coverage creates duplicate source IDs across parent batch runs and
  separately creates an incomplete merged run with `not_in_run` rows; both cases verify the merged
  catalog validation fails before closeout.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_captured_library.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Merged catalog can only be produced by silently overwriting the canonical catalog without an
  archived gate.
- Unknown-source validation must be weakened to make the merge pass.

### Sequence 4 - Extraction And Parser Readiness

Goal: extract support-document text and chunks from the captured artifacts, using reuse where safe
and parser blockers where necessary.

Implementation tasks:

- Run a read-only reuse inventory scoped to the support-document corpus.
- Classify each row as already current, reusable, needs extraction, excluded/gap, or parser blocker.
- Run `extract-build --reuse-existing` only for rows whose artifact hashes match reusable extracted
  payloads.
- Parse remaining PDFs, XML, HTML, ZIP, and Box/Federal Register artifacts through the existing
  extractor paths.
- Emit diagnostics for unsupported ZIP contents or parser failures rather than hiding them.

Acceptance signals:

- Extraction diagnostics cover every captured source-delta source record.
- Every successful artifact has extracted text and chunks.
- Parser failures are explicit blocker records tied to source IDs and artifact hashes.
- No full canonical extraction rebuild is required unless merged-corpus identity changes demand it.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library \
  --reuse-existing
PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py tests/test_reuse_inventory.py
```

Stop conditions:

- Artifact hash mismatches appear in reuse inventory.
- Extraction produces chunks for fewer rows than the readiness report expects without explicit
  blocker records.

### Sequence 5 - Retrieval Readiness And Evaluation

Goal: make the support-document text discoverable through retrieval surfaces with coverage checks
that can support forest-plan review.

Implementation tasks:

- Build retrieval inputs for the support-document source set or merged source set.
- Add retrieval coverage checks for support-document roles such as land management plan, ROD, FEIS,
  Biological Assessment, Biological Opinion, amendments, appendices, monitoring direction, species
  overlays, and grassland overlays where applicable.
- Add a small retrieval evaluation suite for source-delta questions that should retrieve exact
  support-document evidence by forest and document role.
- Keep validation separate from evaluation: validation gates readiness; evaluation measures retrieval
  quality.

Acceptance signals:

- Retrieval validation passes for the support-document corpus.
- Evaluation cases cover at least one query per forest/profile family with captured support
  documents, plus negative cases for the two official-source gaps.
- Retrieval outputs cite source IDs and artifact/chunk IDs.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py
git diff --check
```

Stop conditions:

- Retrieval cannot distinguish a missing official-source gap from a retrieved support document.
- Evaluation requires model-generated assertions without source citations.

### Sequence 6 - Forest-Profile Readiness Integration

Goal: wire the support-document corpus into forest-plan profile readiness so Region 1 expansion
blockers become document-specific instead of generic profile blockers.

Implementation tasks:

- Extend profile/source readiness outputs to consume the merged/support-document corpus through
  catalog and retrieval surfaces.
- For each Region 1 forest/grassland profile, emit required document-role coverage:
  - plan;
  - ROD/decision;
  - EIS/FEIS or equivalent plan-revision environmental analysis;
  - Biological Assessment when applicable;
  - Biological Opinion when applicable;
  - amendments/appendices/overlays where the register lists them.
- Preserve the difference between:
  - `catalog_confirmed`;
  - captured source-delta support document;
  - unresolved official-source gap;
  - extracted but not retrieval-ready;
  - retrieval-ready.
- Keep `forest_profile_not_ready` blockers concrete by source ID and document role.

Acceptance signals:

- Readiness output lists every Region 1 forest/profile with document-role counts and blocker IDs.
- Custer Gallatin remains ready under the existing proving package assumptions.
- Broader Region 1 profiles are no longer blocked by vague missing-support-document language; each
  blocker points to a source ID, document role, parser gap, retrieval gap, or official-source gap.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py
```

Stop conditions:

- A profile becomes ready without all required support-document roles present and retrieval-ready.
- Gap rows are treated as corpus-ready evidence.

### Sequence 7 - Corpus Incorporation And Downstream Replay

Goal: incorporate the support-document rows into the corpus in a form downstream review, graph, and
promotion gates can consume without stale source-set confusion.

Implementation tasks:

- Promote the merged/support-document corpus source-set ID as the active Region 1 support-document
  corpus.
- Rebuild extraction, retrieval, evidence graph, source-claim, and rule-claim artifacts only for the
  intended source-set boundary.
- Update graph/readiness summaries to include support-document corpus coverage and residual gap
  counts.
- Rerun promotion or phase gates only where the readiness claim crosses downstream surfaces.
- Keep canonical V1 East Crazies artifacts separate unless the user explicitly asks to replay that
  review against the new merged corpus.

Acceptance signals:

- Current-state docs distinguish:
  - canonical 190-row V1 catalog;
  - scoped source-delta catalog gate;
  - merged Region 1 support-document corpus;
  - any downstream derived source-set IDs.
- `phase-eval`/promotion gates that cite source-set IDs are fresh for the selected claim.
- Residual risks include the two official-source gap rows unless they have been resolved.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_evidence_graph.py tests/test_source_partitions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_v1_ea_eval.py
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- A downstream artifact references an old source set while claiming support-document corpus
  readiness.
- The corpus is called Region 1 complete while the two official-source gap rows remain unresolved.

## Milestone Closeout

Close the milestone only after:

- register and gap evidence are current;
- source-delta capture and any gap captures are validated;
- scoped and merged catalog gates pass;
- extraction and retrieval readiness artifacts cover every captured support-document row or explicit
  blocker;
- forest-profile readiness emits source-ID-level blockers;
- docs and session handoff name the active source-set IDs and the remaining gap rows;
- focused tests, architecture contract, ruff, compileall, `git diff --check`, and the full test suite
  pass.

Atomic closeout commit should include:

- implementation changes;
- focused tests and fixtures;
- this milestone plan updates if the sequence changed during execution;
- current-state docs;
- output schema docs when artifact shapes change;
- session handoff.

## Next Immediate Slice

Sequence 3 is closed for the current baseline: the merged catalog contract is implemented,
generated, and validated while the canonical catalog remains intact. The next immediate slice is
Sequence 4: run support-document extraction/parser readiness from merged source set
`source-set-7e2652d23e764068` and scoped support-document source set
`source-set-411b3736b3691eed`, using reuse inventory before any extraction rebuild and preserving
the two official-source gaps as explicit blockers.
