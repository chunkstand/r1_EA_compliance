# USFS Region 1 EA Sources

Local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA Forest Service Region 1
source material.

The workbook is the source-of-truth input for the knowledge base. The system captures the full
canonical workbook source set into a local, auditable source library, then builds derived extraction,
retrieval, evidence graph, source-claim graph, rule-claim binding, and deterministic EA package
review artifacts on top of that corpus.

Current workbook source contract:

- Workbook: `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx`
- `Ingest_Checklist` ingest rows: `162`
- `Scope=Baseline` rows that must be evaluated in every EA compliance review: `26`
- `Scope=Conditional` rows loaded for trigger-based review: `136`
- `R1_Forest_Plans` unit/overlay rows: `28`

Current generated source-library capture:

- Run ID: `corpus-update-2026-05-01-cg-support-batches`
- Workbook rows covered: `190`
- Batch result: `52/52` batches passed
- Repair queue: empty except header
- Unique workbook/effective URLs: `172`
- Unique raw artifacts in reviewer catalog: `160`
- Source-to-artifact links: `189`
- Status counts: `downloaded=8`, `downloaded_existing=170`, `duplicate_content=2`,
  `duplicate_url=9`, `skipped_excluded=1`

The current catalog source set is `source-set-ba8d0feae79501b8`. The latest corpus update added the
Custer Gallatin FEIS Volume 1, FEIS Volume 2, Biological Assessment, and Biological Opinion as
forest-plan supporting records beside the 2022 Custer Gallatin Land Management Plan and ROD. The
Custer Gallatin forest-plan resolver now requires the planning page, LMP, ROD, FEIS Volumes 1 and 2,
Biological Assessment, and Biological Opinion to be present in the retrieval index before it reviews
a Custer Gallatin EA. A Custer Gallatin-only extraction/retrieval slice for those seven records is
built under the current source set for forest-plan review. Full all-source extraction, evidence
graph, source-claim, rule-claim, and compliance promotion artifacts still need to be rebuilt for this
source set; older reviewer-ready downstream artifacts under `source-set-e364ea220cffd938` remain
useful only as prior 147-row evidence.

See `docs/CURRENT_SYSTEM_STATE.md` for the current architecture, storage model, and reviewer-engine
read path. See `docs/BITTER_LESSON_ALIGNMENT.md` for the design guardrails that keep the reviewer
engine biased toward scalable search, learning, evidence, and eval loops instead of hidden
domain-specific heuristics.

## Current Inputs

- `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx`
- `DOWNLOADER_RULES.md`
- `config/downloader.toml`
- `config/url_overrides.toml`
- `config/retrieval_eval_seed.json`
- `config/claim_eval_seed.json`
- `config/rule_claim_link_eval_seed.json`
- `config/compliance_review_eval_seed.json`
- `config/compliance_gold_eval_v0.json`
- `config/compliance_rule_pack_coverage_nepa_ea_v0.json`
- `config/ea_review_checklist_seed.json`
- `config/compliance_rule_pack_nepa_ea_v0.json`

## Stored Data

Generated outputs are written under `source_library/` and ignored by git:

- Raw downloaded artifacts: `source_library/artifacts/raw/`
- Row manifests: `source_library/manifests/download_<run_id>.jsonl`
- Batch ledgers and reports: `source_library/runs/<run_id>/`
- Reviewer catalog: `source_library/catalog/source_catalog.jsonl`
- Reviewer SQLite index: `source_library/catalog/review_sources.sqlite`
- Source-set manifest: `source_library/catalog/source_set_manifest.json`
- Graph seed files:
  - `source_library/catalog/source_graph_nodes.jsonl`
  - `source_library/catalog/source_graph_edges.jsonl`
- Derived extraction outputs: `source_library/derived/<source_set_id>/`
- Retrieval index and eval outputs:
  - `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
  - `source_library/derived/<source_set_id>/retrieval/retrieval_manifest.json`
  - `source_library/derived/<source_set_id>/retrieval/retrieval_validation.json`
  - `source_library/derived/<source_set_id>/retrieval/retrieval_eval_results.json`
- Document evidence graph outputs:
  - `source_library/derived/<source_set_id>/evidence_graph/document_graph_nodes.jsonl`
  - `source_library/derived/<source_set_id>/evidence_graph/document_graph_edges.jsonl`
  - `source_library/derived/<source_set_id>/evidence_graph/evidence_graph.sqlite`
  - `source_library/derived/<source_set_id>/evidence_graph/evidence_graph_validation.json`
  - `source_library/derived/<source_set_id>/evidence_graph/phase_eval_results.json`
- Source claim graph outputs:
  - `source_library/derived/<source_set_id>/claims/claims.jsonl`
  - `source_library/derived/<source_set_id>/claims/entities.jsonl`
  - `source_library/derived/<source_set_id>/claims/claim_graph_nodes.jsonl`
  - `source_library/derived/<source_set_id>/claims/claim_graph_edges.jsonl`
  - `source_library/derived/<source_set_id>/claims/claim_graph.sqlite`
  - `source_library/derived/<source_set_id>/claims/claim_validation.json`
- Rule-claim binding outputs:
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_links.jsonl`
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_link_gaps.jsonl`
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_links.sqlite`
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_link_validation.json`
- EA package review outputs:
  - `source_library/reviews/<review_id>/package/package_manifest.jsonl`
  - `source_library/reviews/<review_id>/package/package_chunks.jsonl`
  - `source_library/reviews/<review_id>/review_validation.json`
  - `source_library/reviews/<review_id>/review_report.json`
  - `source_library/reviews/<review_id>/review_report.md`
  - `source_library/reviews/<review_id>/compliance_validation.json`
  - `source_library/reviews/<review_id>/compliance_review.json`
  - `source_library/reviews/<review_id>/compliance_matrix.json`
  - `source_library/reviews/<review_id>/compliance_matrix.md`
  - `source_library/reviews/<review_id>/compliance_matrix.pdf`
  - `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
  - `source_library/reviews/<review_id>/finding_graph_edges.jsonl`
- Compliance review eval outputs:
  - `source_library/reviews/compliance_review_eval/compliance_review_eval_results.json`
  - `source_library/reviews/compliance_review_eval/packages/<case_id>.txt`
  - `source_library/reviews/compliance_review_eval/reviews/<case_id>/`
- Compliance gold eval outputs:
  - `source_library/reviews/compliance_gold_eval/compliance_gold_eval_results.json`
  - `source_library/reviews/compliance_gold_eval/adjudicated_cases.compliance_review_eval.json`
  - `source_library/reviews/compliance_gold_eval/compliance_review_eval/`

The raw artifacts are not semantic chunks. They are source bytes plus provenance. The
`extract-build` command builds a derived text/chunk layer from the catalog. The
`retrieval-build` command turns those chunks into a queryable local evidence index. The
`evidence-graph-build` command promotes document, chunk, evidence-span, topic, parser, and artifact
links into a local graph artifact. The `claim-extract` command extracts deterministic source-text
claims and entities with exact offsets and graph bindings. The `rule-claim-link` command binds
versioned compliance rules to validated source claims before compliance findings rely on those
authorities. The `ea-review` command runs deterministic package checklist reviews against
reviewer-ready retrieval evidence. The `forest-plan-resolve` command extracts Custer Gallatin
forest-plan review context from an EA package, including project location signals, geographic areas,
management areas, overlays, and source-library plan evidence. It also routes triggered package cues
to the Custer Gallatin ROD, FEIS Volumes 1 and 2, Biological Assessment, and Biological Opinion so
forest-plan reviews can apply the supporting plan record set, not only the primary LMP. Supporting
routes are trigger-gated and report `trigger_evidence` so reviewers can see why a supporting record
was applied. The `compliance-review` command
identifies applicable
statutory, regulatory, policy, state, executive-order, and forest-plan authorities from a versioned
rule pack, evaluates the EA against each applicable authority, and emits a compliance matrix plus
finding graph with source-claim support. The
`compliance-gold-eval` command runs the 10-case adjudication promotion gate. The active compliance
rule pack is `0.4.0`: it declares the 26 workbook `Scope=Baseline` source records explicitly and
contains 44 total authority rules. Embeddings and expanded human adjudication over real EA packages
remain downstream work.

## Reviewer Engine Entry Points

The EA review engine should start from one of these catalog surfaces rather than scanning filenames:

- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`

Forest-plan improvement work uses sequence discipline: each implemented forest-plan sequence must
update repo docs, pass focused verification, and be committed before the next sequence begins.

For each selected source row, the engine should:

1. Read the source metadata from SQLite or `source_catalog.jsonl`.
2. Open `artifact_path`.
3. Recompute SHA256 and byte size before parsing.
4. Choose a parser using `expected_parser` and `content_type`.
5. Attach `source_record_id`, `artifact_sha256`, `citation_label`, URL provenance, and page/section offsets to every extracted chunk.

The catalog graph JSONL files are source metadata graph seeds. They link sources to artifacts,
authorities, review topics, applicability, and related reviewer concepts. The derived evidence graph
adds document, chunk, evidence-span, parser, and topic nodes. The source claim graph adds extracted
claim, entity, authority, and claim-evidence-span nodes. The rule-claim binding layer links
compliance rules to validated claim nodes without generating legal conclusions. No graph layer stores
embeddings or trusted model-generated compliance conclusions.

## Common Commands

Dry-run workbook parsing without network access:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library
```

Preflight URL reachability without saving artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --limit 10
```

Preflight records HTTP status, final URL, redirect chain, content type, content length, challenge-page detection, and failure status for each workbook row while fetching each unique URL only once.

Download a small controlled slice:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --limit 5
```

The downloader saves immutable raw artifacts under `source_library/artifacts/raw/`, computes SHA256 hashes, reuses existing artifacts on resume, and writes a row-level manifest for every workbook source row.

Build an operator report for any run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources report \
  --output-dir source_library \
  --run-id pilot-core-sources
```

The report writes `source_library/runs/<run_id>/operator_report.md` and lists status counts, host counts, adapter usage, and rows that need manual URL repair.

Before scaling a pilot into a full download, run the acceptance gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id pilot-core-sources-adapted
```

The gate writes `source_library/runs/<run_id>/acceptance_gate.json` and exits nonzero if artifact hashes, byte sizes, duplicate links, status counts, exclusion safety, or repair-queue coverage fail.

Run staged host pilots before the full download:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources pilot-hosts \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix staged-pilot \
  --host www.ecfr.gov \
  --host uscode.house.gov
```

Each host pilot runs `download`, `report`, and `validate-run`. The command writes a parent summary under `source_library/runs/<run-id-prefix>-host-pilots/` and exits nonzero if any selected host has failed rows or a failed acceptance gate.

Plan controlled download batches before scaling beyond pilots:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix first-batch \
  --batch-size 5 \
  --limit-per-host 1 \
  --plan-only
```

Remove `--plan-only` to execute the planned batches. Each batch runs `download`, `report`, and `validate-run`, writes a parent `batch_plan.json`, `batch_ledger.json`, and `repair_queue.csv`, then stops on the first failed or repair-needed batch unless `--continue-on-failure` is passed.
Use `--resume` to skip already passed batches under the same run prefix.

Run or refresh the full captured library:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix full-library \
  --batch-size 10 \
  --continue-on-failure
```

Build the reviewer-engine catalog from the full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id corpus-update-2026-05-01-cg-support-batches
```

The catalog command writes `source_library/catalog/source_catalog.jsonl`, `source_set_manifest.json`, `catalog_validation.json`, `review_sources.sqlite`, and graph seed node/edge JSONL.
Pass `--run-id <download-run-id>` after downloads to link artifact hashes, paths, content types, and retrieval timestamps into the same reviewer-facing catalog.
Pass `--batch-run-id <run-id-prefix>-batches` after controlled batch downloads to link artifacts from every passed child batch through the parent batch ledger.

Build the verified extraction/chunk layer from the reviewer catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

The extraction command reads `review_sources.sqlite`, recomputes every artifact SHA256 before
parsing, routes by `expected_parser` and `content_type`, and writes:

- `source_library/derived/<source_set_id>/extracted_text/`
- `source_library/derived/<source_set_id>/docling_json/`
- `source_library/derived/<source_set_id>/chunks/chunks.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_manifest.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_validation.json`
- `source_library/derived/<source_set_id>/diagnostics/extraction_accuracy_audit.json`
- `source_library/derived/<source_set_id>/diagnostics/summary.json`

For delta extraction, repeat `--id` for each selected `source_record_id`. The command records the
complete selected ID list in `diagnostics/summary.json`; retrieval remains non-reviewer-ready for a
filtered extraction unless rebuilt with explicit partial-extraction allowance.

When a prior extraction already produced matching text for unchanged artifacts, pass
`--reuse-existing` to rebuild the manifest and chunks without reparsing those artifacts. This is
intended for critical targeted recovery or source-slice refreshes, not for promotion evidence that
requires a clean full-source-set extraction.

Before a reuse-first rebuild, inventory current and prior extracted text without running extraction
or review commands:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory \
  --output-dir source_library
```

The command writes `source_library/derived/<source_set_id>/reuse_inventory/` with one row per
current catalog source classified as `already_current_cg_slice`, `reuse_extraction`,
`needs_extract`, or `excluded`. Reuse candidates require matching `source_record_id`, artifact
SHA256, parser/content type metadata, existing extracted text, and matching text SHA256.

For eCFR XML records whose workbook URL points at a section or subpart, extraction scopes the text
to that XML element and records the applied source scope in parser metadata. Run the accuracy audit
after extraction to verify text hashes, raw artifact hashes, chunk offsets, no chunk coverage gaps,
scoped XML text, markup/entity cleanup, and PDF token coverage against independent `pypdf` text:

```bash
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library
```

PDF extraction uses Docling first. The default PDF path disables OCR for born-digital sources and
runs Docling in a child process with a hard per-document timeout; when a born-digital PDF exceeds
that timeout, extraction falls back to `pypdf_text_fallback` and records that parser in the
manifest with fallback audit metadata. Pass `--docling-ocr` only for scanned PDFs and adjust
`--docling-timeout-seconds` with operator intent. Use Python 3.12 for that lane:

```bash
uv venv --python python3.12 .venv-docling
. .venv-docling/bin/activate
uv pip install -e ".[extraction]"
```

Build the local evidence retrieval index from the extracted chunks:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library
```

By default, `retrieval-build` requires a full extraction scope: no extraction filters, selected
source count equal to catalog source count, and one indexed chunk source for every extracted source.
For a one-source diagnostic slice, pass `--allow-partial-extraction`; the command will build the
index but mark `reviewer_ready` as `false`.

Query the evidence index with text and reviewer filters:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-query \
  --output-dir source_library \
  --document-role regulation \
  --authority-level federal_regulation \
  "alternatives environmental effects"
```

Each result includes the `source_record_id`, `artifact_sha256`, `citation_label`, parser name and
version, extracted-text offsets, URLs, and a short evidence span.

Run a first-pass EA package review against the source-library evidence index:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

`ea-review` extracts supported local package files (`.pdf`, `.html`, `.xml`, `.docx`, `.txt`, and
`.md`), runs the seeded checklist in `config/ea_review_checklist_seed.json`, retrieves supporting
knowledge-base evidence for each item, and writes:

- `source_library/reviews/<review_id>/package/package_manifest.jsonl`
- `source_library/reviews/<review_id>/package/package_chunks.jsonl`
- `source_library/reviews/<review_id>/review_validation.json`
- `source_library/reviews/<review_id>/review_report.json`
- `source_library/reviews/<review_id>/review_report.md`

Findings are deterministic `pass`, `gap`, `uncertain`, or `not_applicable` records. A `gap` means
the source library supports the review requirement but no matching EA package evidence span was
found. An `uncertain` item does not make a compliance claim.
Package evidence search requires at least one configured package term to match; single-word package
terms match whole tokens, while phrase terms match contiguous text.
The command requires the source-library retrieval summary and validation to be reviewer-ready before
running, and fixed review IDs replace prior package artifacts so stale package chunks cannot survive
reruns. Pass `--reuse-package-cache` only when a review directory already has
`package/package_manifest.jsonl` and `package/package_chunks.jsonl` that you intend to reuse; this
reruns checklist/rule evaluation against cached package chunks without re-extracting PDFs.

Resolve Custer Gallatin forest-plan context from a local EA package:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

`forest-plan-resolve` is the first Custer Gallatin-only forest-plan review sequence. It extracts or
reuses the package cache, resolves whether the EA is for the Custer Gallatin National Forest, then
extracts ranger district, project-location, geographic-area, management-area, and overlay signals.
For resolved Custer Gallatin packages, it records the expected Custer Gallatin plan source records
and retrieves supporting source-library plan evidence from the primary Land Management Plan. It also
routes triggered ROD, FEIS, designated-area/allocation, ESA Biological Assessment, and Biological
Opinion cues to the required Custer Gallatin supporting records. Broad section labels such as
`purpose and need` do not activate FEIS routing by themselves, and acronym triggers such as `ROD`,
`FEIS`, `BA`, `BO`, and `ESA` require uppercase matches. The command then writes:

- `source_library/reviews/<review_id>/forest_plan_context.json`
- `source_library/reviews/<review_id>/forest_plan_context_validation.json`
- `source_library/reviews/<review_id>/forest_plan_context_summary.json`
- `source_library/reviews/<review_id>/package/package_manifest.jsonl`
- `source_library/reviews/<review_id>/package/package_chunks.jsonl`

Custer Gallatin packages with no resolved geographic area, management area, or overlay are not
reviewer-ready and set `needs_reviewer_resolution`. Ambiguous `Gallatin`-only packages are not
guessed. Non-Custer packages are marked `not_custer_gallatin` and treated as out of scope.

Run a versioned compliance rule pack and emit the compliance matrix and finding graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

To refresh rules against an already extracted package, keep the same review ID and add
`--reuse-package-cache`:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --review-id <existing-review-id> \
  --reuse-package-cache
```

`compliance-review` reuses the package extraction and source retrieval gates from `ea-review`, then
writes:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/compliance_matrix.json`
- `source_library/reviews/<review_id>/compliance_matrix.md`
- `source_library/reviews/<review_id>/compliance_matrix.pdf`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

The command follows an authority-first workflow: baseline authorities always apply, conditional
authorities are marked applicable only when configured EA package terms are found, and not-applicable
authorities are carried through the matrix without source or EA compliance citations. The rule pack
declares `baseline_source_record_ids`; for the active workbook this list is the 26
`Ingest_Checklist` rows where `Scope=Baseline`, not the first rows in workbook order. Rule-pack
validation fails when a declared baseline source record has no rule or when its rule is not
`applicability_mode=baseline`. Every
applicable `pass` finding requires package evidence and source-library evidence. Every applicable
`gap` finding requires source-library evidence and records that matching package evidence was not
found. Claim-bearing findings also require validated rule-to-source-claim links. The finding graph
connects the review, rule pack, rules, findings, evidence spans, source claims, and package gaps.
Rule-pack IDs, rule IDs, and fixed review IDs must use only letters, numbers, dots, underscores, and
hyphens. Unknown or empty `source_filters` fail rule-pack validation so typoed filters cannot
silently broaden source retrieval.
The compliance matrix is the reviewer-facing table: each row carries authority category, authority
source record, authority document role, applicability mode, applicability status and basis, rule
status, package citation, source-library citation, source-claim IDs, limitations, and whether
citation requirements were met. Every compliance review also renders `compliance_matrix.pdf` from
the same matrix data.

Run the final compliance review eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

`compliance-review-eval` writes deterministic package fixtures from the eval file, runs the real
`compliance-review` command for each case, and scores the generated findings. It asserts expected
statuses for every rule in the rule pack, claim types, package evidence, source-library evidence,
source-claim links, expected source record IDs, expected source document roles, finding status
counts, unsupported finding IDs, citation coverage, failure taxonomy, and finding-graph coverage.
Bad eval filters, unknown rule IDs, partial rule expectations, and mismatched status counts fail
fast so typoed or incomplete fixtures cannot silently broaden scoring.

Run the adjudicated gold eval promotion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
```

`compliance-gold-eval` reads a structured adjudication file, requires positive, mixed, and negative
case profiles, verifies every case covers the active rule pack, then runs those cases through the
real `compliance-review-eval` path. The current gold file contains 10 realistic adjudicated package
profiles with expected status counts, applicable source rows, and source document classes. It emits
`promotion_ready` only when adjudication checks and the underlying compliance-review eval both pass.
Gold case IDs must be unique and safe for generated paths, and package fixture paths must stay under
the gold file directory.

Run the seed retrieval eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --eval-file config/retrieval_eval_seed.json
```

The eval checks whether expected compliance-review evidence can be retrieved with citation-bearing
provenance. It reports hit rate, expected-term coverage, citation coverage, unsupported-answer rate,
and zero-result rate.

Build the document evidence graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build \
  --output-dir source_library
```

The graph builder creates source-document, raw-artifact, extracted-text, document-section,
document-chunk, evidence-span, parser, and review-topic nodes with provenance edges. It requires a
reviewer-ready retrieval index by default and compares each chunk back to the retrieval SQLite index
so stale or edited chunk files cannot produce reviewer-ready graph artifacts. Use
`--allow-partial-retrieval` only for diagnostic slices; the graph can validate structurally, but
`reviewer_ready` remains `false`.

Build deterministic source claims and entity graph artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract \
  --output-dir source_library
```

`claim-extract` reads extracted chunks, catalog topics, and the reviewer-ready retrieval index. It
emits exact source-text claim spans, entities, authority links, graph JSONL, SQLite, validation, and
summary artifacts. Claims are deterministic `obligation`, `prohibition`, `condition`,
`authorization`, `definition`, `exemption`, or `guidance` records and are reviewer-ready only when
their offsets, hashes, chunk IDs, citations, and retrieval-index bindings validate.

Run the seed claim eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
```

`claim-eval` revalidates the current claim artifacts before scoring cases. It refuses missing,
tampered, or non-reviewer-ready claim outputs, and eval case filters fail fast on unknown or empty
keys so typoed filters cannot silently broaden the eval.

Build deterministic rule-to-source-claim links:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

`rule-claim-link` reads reviewer-ready claim artifacts and a versioned compliance rule pack. It
writes rule-to-claim links, explicit no-claim gaps, SQLite, validation, and summary artifacts. Links
carry rule ID, claim ID, claim type, score, matched terms, citation label, chunk ID, artifact hash,
and exact source offsets. Rule-claim outputs are versioned by rule-pack ID and version. After the
active rule pack moved to `0.4.0` and 44 rules, old `0.3.0`/20-rule link, coverage, compliance-eval,
and gold-eval artifacts should be treated as stale for promotion until regenerated and adjudicated
against the `0.4.0` rule set.

Run the seed rule-claim eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
```

`rule-claim-eval` revalidates current link artifacts before scoring cases and refuses stale,
tampered, or non-reviewer-ready bindings.

Run rule-pack coverage:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

`compliance-coverage` validates that every rule has a coverage-matrix row, current source-claim
links, source-claim term support, and compliance-review eval coverage. It reports uncovered rules,
rules without eval cases, rules without source-claim links, source-record mismatches, and
source-claim terms that do not match current rule-claim bindings.

Run phase-aligned readiness evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library
```

This reports catalog, extraction, retrieval, evidence-graph, claim-extraction, and rule-claim
binding readiness separately so validation failures are not hidden inside a single aggregate score.
When `compliance_coverage_results.json` exists beside the rule-claim outputs, it also reports a
`compliance_coverage` phase for matrix, source-claim, source-claim-term, and eval-case coverage.
When `source_library/reviews/compliance_gold_eval/compliance_gold_eval_results.json` exists, it also
reports a `compliance_gold_eval` promotion phase with explicit failed checks for stale source-set,
rule-pack, failed-gold, or not-promotion-ready artifacts. Pass `--review-id <review-id>` after a
compliance review to include `compliance_review` as an additional phase gate. The compliance phase
requires the review source set to match the evaluated source set and requires the review's
`compliance_matrix.json` to exist with the expected schema version, review ID, source set, rule pack,
row count, and status counts. It also requires `compliance_matrix.pdf` to exist and have a valid PDF
header.

Repair stale or blocked workbook URLs through `config/url_overrides.toml`:

```toml
[[overrides]]
source_record_id = "R1EA-000"
override_url = "https://example.gov/current-official-source"
reason = "Replaces stale workbook URL after manual source verification."
```

Manifests preserve the workbook cell as `original_url` and use `effective_url` for fetching, deduplication, host pilots, and artifact paths.
Overrides must be unique by `source_record_id`, use absolute HTTP(S) URLs with hosts, and avoid workbook scope-exclusion URLs.
Run summaries include `override_count` and `filtered_override_count`, and `validate-run` fails if override provenance or counts drift from the manifest.

## Development

Use the bundled Python runtime or any Python 3.11+ environment with `openpyxl` installed.

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

The captured-library integrity tests validate the current generated `source_library` when present. They check full-batch coverage, manifest-to-ledger consistency, artifact SHA256 and byte sizes, override provenance, catalog linkage, and SQLite/catalog agreement.
