# USFS Region 1 EA Sources

Local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA Forest Service Region 1
source material.

The workbook is the source-of-truth input for the knowledge base. The system captures the full
canonical workbook source set into a local, auditable source library, then builds derived extraction,
retrieval, evidence graph, source-claim graph, rule-claim binding, and deterministic EA package
review artifacts on top of that corpus.

Current full-library capture:

- Run ID: `full-library-batches`
- Workbook rows covered: `147`
- Batch result: `28/28` batches passed
- Repair queue: empty except header
- Unique workbook/effective URLs: `144`
- Unique raw artifacts in reviewer catalog: `131`
- Source-to-artifact links: `147`

See `docs/CURRENT_SYSTEM_STATE.md` for the current architecture, storage model, and reviewer-engine
read path. See `docs/BITTER_LESSON_ALIGNMENT.md` for the design guardrails that keep the reviewer
engine biased toward scalable search, learning, evidence, and eval loops instead of hidden
domain-specific heuristics.

## Current Inputs

- `usfs_region1_ea_document_checklist_current_2026.xlsx`
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
  - `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
  - `source_library/reviews/<review_id>/finding_graph_edges.jsonl`
- Compliance review eval outputs:
  - `source_library/reviews/compliance_review_eval/compliance_review_eval_results.json`
  - `source_library/reviews/compliance_review_eval/packages/<case_id>.txt`
  - `source_library/reviews/compliance_review_eval/reviews/<case_id>/`

The raw artifacts are not semantic chunks. They are source bytes plus provenance. The
`extract-build` command builds a derived text/chunk layer from the catalog. The
`retrieval-build` command turns those chunks into a queryable local evidence index. The
`evidence-graph-build` command promotes document, chunk, evidence-span, topic, parser, and artifact
links into a local graph artifact. The `claim-extract` command extracts deterministic source-text
claims and entities with exact offsets and graph bindings. The `rule-claim-link` command binds
versioned compliance rules to validated source claims before compliance findings rely on those
authorities. The `ea-review` command runs deterministic package checklist reviews against
reviewer-ready retrieval evidence. The `compliance-review` command evaluates a versioned rule pack
and emits a finding graph with source-claim support. Embeddings and a full adjudication workflow
remain downstream work.

## Reviewer Engine Entry Points

The EA review engine should start from one of these catalog surfaces rather than scanning filenames:

- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`

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
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library
```

Preflight URL reachability without saving artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --limit 10
```

Preflight records HTTP status, final URL, redirect chain, content type, content length, challenge-page detection, and failure status for each workbook row while fetching each unique URL only once.

Download a small controlled slice:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources download \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
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
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix staged-pilot \
  --host www.ecfr.gov \
  --host uscode.house.gov
```

Each host pilot runs `download`, `report`, and `validate-run`. The command writes a parent summary under `source_library/runs/<run-id-prefix>-host-pilots/` and exits nonzero if any selected host has failed rows or a failed acceptance gate.

Plan controlled download batches before scaling beyond pilots:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
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
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix full-library \
  --batch-size 10 \
  --continue-on-failure
```

Build the reviewer-engine catalog from the full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --batch-run-id full-library-batches
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
The command requires the source-library retrieval summary and validation to be reviewer-ready before
running, and fixed review IDs replace prior package artifacts so stale package chunks cannot survive
reruns.

Run a versioned compliance rule pack and emit the finding graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

`compliance-review` reuses the package extraction and source retrieval gates from `ea-review`, then
writes:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

Every `pass` finding requires package evidence and source-library evidence. Every `gap` finding
requires source-library evidence and records that matching package evidence was not found.
Claim-bearing findings also require validated rule-to-source-claim links. The finding graph connects
the review, rule pack, rules, findings, evidence spans, source claims, and package gaps. Rule-pack
IDs, rule IDs, and fixed review IDs must use only letters, numbers, dots, underscores, and hyphens.
Unknown or empty `source_filters` fail rule-pack validation so typoed filters cannot silently broaden
source retrieval.

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
source-claim links, finding status counts, unsupported finding IDs, citation coverage, and
finding-graph coverage. Bad eval filters, unknown rule IDs, partial rule expectations, and mismatched
status counts fail fast so typoed or incomplete fixtures cannot silently broaden scoring.

Run the adjudicated gold eval promotion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
```

`compliance-gold-eval` reads a structured adjudication file, requires positive, mixed, and negative
case profiles, verifies every case covers the active rule pack, then runs those cases through the
real `compliance-review-eval` path. It emits `promotion_ready` only when adjudication checks and the
underlying compliance-review eval both pass.

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
and exact source offsets. The current full corpus links all `7/7` seed rules with `35` validated
links and no explicit gaps.

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
reports a `compliance_gold_eval` promotion phase. Pass `--review-id <review-id>` after a compliance
review to include `compliance_review` as an additional phase gate. The compliance phase requires the
review source set to match the evaluated source set.

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
