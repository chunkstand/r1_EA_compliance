# Current System State

This project is a local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA
Forest Service Region 1 source material.

The workbook `usfs_region1_ea_document_checklist_current_2026.xlsx` remains the source-of-truth
input for the knowledge base. The generated `source_library/` is the audited local capture and
derived reviewer corpus used by extraction, retrieval, evidence graph, source-claim extraction,
rule-claim binding, and deterministic EA package review commands.

## Current Capture

The current full-library capture is:

- Parent batch run: `full-library-batches`
- Canonical workbook rows: `147`
- Batch count: `28`
- Passed batches: `28`
- Failed batches: `0`
- Repair-needed batches: `0`
- Repair queue: empty except the CSV header
- Unique effective URLs: `144`
- Reviewer catalog source rows: `147`
- Reviewer catalog unique artifacts: `131`
- Reviewer catalog source-artifact links: `147`

The current catalog validation passes. The captured-library integrity test suite also passes against these generated outputs.

## Verified State Snapshot

Last verified locally on 2026-04-30.

- Active source set: `source-set-e364ea220cffd938`
- Base phase eval: passed, `6/6` phases reviewer-ready
- Compliance phase eval: passed, `7/7` phases reviewer-ready for
  `smoke-compliance-review-v0-hardened`
- Catalog: `147` source rows, `131` unique raw artifacts
- Extraction: `147/147` selected sources extracted, validation passed
- Retrieval: `13,619` chunks indexed, validation passed, reviewer-ready
- Evidence graph: `36,578` nodes, `106,182` edges, validation passed, reviewer-ready
- Retrieval-to-graph binding mismatches: `0`
- Source claim graph: `35,348` claims, `8,479` entities, `90,153` nodes, `231,214`
  edges, validation passed, reviewer-ready
- Claim eval seed: passed, `2/2` cases
- Rule-claim binding: `25` links across `5/5` seed compliance rules, `0` explicit no-claim
  gaps, validation passed, reviewer-ready
- Rule-claim eval seed: passed, `5/5` cases
- EA review smoke: `review_validation.json` passed for `smoke-ea-review-v0-hardened`
- Compliance review smoke: `compliance_validation.json` passed for
  `smoke-compliance-review-v0-hardened`
- Unit suite: `105` tests passed

The verification set was:

```bash
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall -q src
uv run --extra dev ruff check src tests
git diff --check
uv lock --check
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library
printf '%s\n' \
  'Purpose and Need' \
  '' \
  'The proposed action improves trail access and includes alternatives, affected environment, environmental effects, consultation, mitigation, and a finding of no significant impact.' \
  > /tmp/ea-package-v0-smoke.txt
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /tmp/ea-package-v0-smoke.txt \
  --output-dir source_library \
  --review-id smoke-ea-review-v0-hardened
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /tmp/ea-package-v0-smoke.txt \
  --output-dir source_library \
  --review-id smoke-compliance-review-v0-hardened
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id smoke-compliance-review-v0-hardened
```

## Storage Model

The system stores source material in layers.

### Raw Artifacts

Path:

```text
source_library/artifacts/raw/
```

Raw artifacts are downloaded bytes saved before extraction or transformation. They are grouped by host and named with stable source/title slug information plus a SHA256 prefix. The downloader does not overwrite validated artifacts during normal resume behavior.

Artifact metadata is recorded in manifests and catalog records:

- `artifact_path`
- `artifact_sha256`
- `artifact_byte_size`
- `content_type`
- `fetch_timestamp`
- `final_url`

### Row Manifests

Path:

```text
source_library/manifests/download_<run_id>.jsonl
```

Each manifest is JSONL with one row per workbook source in that run. A row records workbook provenance, original URL, effective URL after overrides, normalized URL, final URL, artifact metadata, status, duplicate links, validation result, and failure evidence when applicable.

For full-batch operation, the parent batch ledger points to many child download manifests.

### Batch Evidence

Path:

```text
source_library/runs/full-library-batches/
```

The parent batch run contains:

- `batch_plan.json`
- `batch_ledger.json`
- `summary.json`
- `operator_report.md`
- `repair_queue.csv`

Each child batch also has its own run directory under `source_library/runs/<child-run-id>/` with its own summary, report, events, failures, and acceptance gate.

### Reviewer Catalog

Path:

```text
source_library/catalog/
```

The catalog contains:

- `source_catalog.jsonl`: one reviewer-facing source record per workbook row
- `source_set_manifest.json`: versioned source-set metadata and counts
- `catalog_validation.json`: reviewer-catalog acceptance gate
- `review_sources.sqlite`: queryable index for the EA review engine
- `source_graph_nodes.jsonl`: portable graph seed nodes
- `source_graph_edges.jsonl`: portable graph seed edges

The reviewer catalog links every workbook row to an artifact, including duplicate-content rows.

## Extraction, Retrieval, Review, And Graph Status

The raw source library does not store semantic chunks. A derived extraction layer is implemented
through `extract-build`; it reads the reviewer catalog, rehashes artifacts, and writes rebuildable
extracted text, chunk JSONL, and extraction diagnostics under
`source_library/derived/<source_set_id>/`.

The first retrieval layer is also implemented through `retrieval-build`. It indexes extracted
chunks into a local SQLite evidence index and supports deterministic text queries filtered by
document role, authority level, source record, review topic, citation label, and host.

The document evidence graph layer is implemented through `evidence-graph-build`. It turns extracted
chunks and retrieval metadata into graph artifacts for source documents, raw artifacts, extracted
text, sections, chunks, evidence spans, parsers, and review topics. It is a graph substrate for
auditable review; source-text legal claims are handled by the separate claim graph layer.

Source Claim Graph V0 is implemented through `claim-extract`. It extracts deterministic legal-style
claims from exact chunk text spans, links entities and authorities, validates offsets and retrieval
bindings, and writes claim graph artifacts under
`source_library/derived/<source_set_id>/claims/`.

EA Package Review V0 is implemented through `ea-review`. It extracts a local EA package, runs the
seed checklist, retrieves source-library evidence for each item, and writes package evidence,
source-library evidence, finding status, limitations, and validation artifacts.

Compliance Rule Pack + Finding Graph V0 is implemented through `compliance-review`. It evaluates a
versioned rule pack from `config/compliance_rule_pack_nepa_ea_v0.json`, reuses the `ea-review`
package/retrieval gates, requires validated rule-to-source-claim bindings, and writes compliance
validation, a compliance review report, and a finding graph for rules, findings, source claims,
source evidence, package evidence, and package gaps.

Current state:

- Raw source documents are captured and cataloged.
- Source metadata is normalized into JSONL and SQLite.
- Derived extraction builds text and chunks from the catalog.
- The extraction accuracy audit verifies text hashes, raw artifact hashes, chunk offset fidelity,
  gap-free chunk coverage, eCFR section/subpart scoping, markup cleanup, and PDF token coverage.
- Retrieval builds and queries a provenance-bearing local evidence index.
- The document evidence graph builds source, artifact, extracted-text, section, chunk, evidence-span,
  parser, and review-topic nodes with health metrics.
- The source claim graph builds claim, entity, authority, and claim-evidence-span nodes with exact
  chunk and source-text offsets.
- The rule-claim binding layer links compliance rules to validated source claims and records explicit
  no-claim gaps when no validated source claim matches a rule.
- Phase eval reports catalog, extraction, retrieval, evidence-graph, claim-extraction, and
  rule-claim-binding readiness separately.
- EA review runs deterministic checklist execution against a local package and emits JSON/Markdown
  reports plus `review_validation.json`.
- Compliance review runs a versioned rule pack and emits `compliance_validation.json`,
  `compliance_review.json`, `finding_graph_nodes.jsonl`, and `finding_graph_edges.jsonl`.
- A seed retrieval eval file exists at `config/retrieval_eval_seed.json`.
- A seed claim extraction eval file exists at `config/claim_eval_seed.json`.
- A seed rule-claim binding eval file exists at `config/rule_claim_link_eval_seed.json`.
- A seed EA review checklist exists at `config/ea_review_checklist_seed.json`.
- A seed NEPA EA compliance rule pack exists at `config/compliance_rule_pack_nepa_ea_v0.json`.
- Catalog graph seed files exist for source-level relationships.
- No embeddings exist yet.
- No model-generated compliance narrative is trusted without deterministic package and source
  evidence.
- Page/section offsets are available only where the selected parser can infer them; all chunks carry
  extracted-text character offsets.

The catalog graph seed is a source metadata graph. It includes relationships such as:

- source to artifact
- source to authority
- source to review topic
- source to applicability

The document evidence graph is the implemented content graph. It includes document sections, chunks,
evidence spans, parser provenance, and review-topic edges. It does not include table structure
recovery, embeddings, or vector chunks.

The source claim graph is the implemented claim/entity graph. It includes extracted source-text
claims, entities, authority nodes, claim evidence spans, and edges back to chunk/source provenance.
It is deterministic pattern extraction with strict validation, not a model-generated interpretation
of compliance meaning.

The rule-claim binding layer is the implemented bridge from compliance rules to source claims. It
uses rule-pack queries and source filters to rank validated source claims, writes exact provenance
for each link, and treats missing rule support as explicit no-claim gaps rather than silent evidence.

The finding graph is the implemented compliance-review graph. It includes rule packs, compliance
rules, findings, source-claim references, evidence-span references, and package-gap nodes. It does
not replace human reviewer adjudication.

## Accuracy Guarantees

The current downloader and catalog guarantee capture integrity, not legal interpretation.

Validated guarantees:

- Every canonical workbook source row has one final captured status.
- The full-library batch covers all `147` workbook rows.
- The repair queue is empty after URL repairs.
- Every successful row links to an artifact.
- Every artifact path exists.
- Artifact byte sizes match manifest metadata.
- Artifact SHA256 values recompute from saved bytes.
- Duplicate-content rows link to canonical artifacts.
- URL overrides preserve the workbook `original_url` and record the `effective_url`.
- Override metadata includes `override_url` and `override_reason`.
- The reviewer catalog matches batch manifests.
- SQLite source-artifact links match the JSONL catalog.
- Extraction outputs match raw artifact hashes and manifest text hashes.
- Chunk text matches extracted-text offset slices.
- Retrieval chunks validate against source-set IDs, content hashes, offsets, required provenance, and
  catalog linkage.
- Evidence graph chunks validate against the retrieval index before graph artifacts are marked
  reviewer-ready.
- EA review `pass` findings require both package evidence and source-library evidence.
- EA review `gap` findings require source-library evidence and explicitly mean package evidence was
  not found.
- EA review validation rejects unsupported compliance claims.
- Compliance review validates the rule pack, requires every rule to be evaluated, requires source
  citations for claim-bearing findings, and validates finding graph node/edge integrity.
- Rule-pack validation rejects unsafe rule-pack or rule IDs, unsupported source-filter keys, and
  empty source-filter values.
- Phase eval rejects stale compliance review artifacts when the review source set does not match the
  evaluated source set.

Boundaries:

- A successful download means the source bytes were captured and validated.
- It does not prove that the source is legally current beyond the workbook metadata and retrieval evidence.
- It proves the current generated extraction artifacts pass deterministic accuracy gates for
  source scoping, chunk fidelity, markup cleanup, and independent PDF token comparison.
- It proves the current retrieval and evidence graph artifacts passed deterministic provenance and
  binding gates.
- It proves the current EA review V0 cannot mark a finding as `pass` without both package and
  source-library evidence.
- It proves the current compliance review V0 cannot produce claim-bearing findings without
  source-library citations.
- It does not prove semantic legal interpretation of the extracted text.
- It does not prove that future web versions will remain unchanged.

## Reviewer Engine Read Path

The EA review engine should not scan `artifacts/raw/` directly as its source of truth. It should
read through the catalog, extraction outputs, and retrieval index in order.

Recommended read path:

1. Read `source_library/catalog/source_set_manifest.json`.
2. Confirm the intended `source_set_id`, `download_batch_run_id`, source counts, artifact counts, and validation status.
3. Query `source_library/catalog/review_sources.sqlite` or read `source_library/catalog/source_catalog.jsonl`.
4. Select source rows by `document_role`, `authority_level`, `review_topics`, `applies_to`, `host`, or `expected_parser`.
5. For each source row, open `artifact_path`.
6. Recompute SHA256 and byte size before parsing.
7. Parse by `expected_parser` and `content_type`.
8. Emit downstream chunks with immutable provenance fields.
9. Build `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`.
10. Retrieve evidence spans through `retrieval-query` or the retrieval module before generating any
    compliance answer.
11. For package review, run `ea-review` so each checklist item records both package evidence and
    source-library evidence, or marks the item as a gap/uncertain without unsupported claims.

Every downstream text chunk should carry:

- `source_set_id`
- `source_record_id`
- `artifact_sha256`
- `artifact_path`
- `citation_label`
- `original_url`
- `effective_url`
- `final_url`
- parser name and parser version
- extraction timestamp
- page, section, heading, byte, or character offsets when available

The review engine should cite `citation_label` and offset metadata, not raw filenames.

## EA Package Review V0

The current package-review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/review_report.json` and
`review_report.md`, `review_validation.json`, plus package extraction artifacts under
`source_library/reviews/<review_id>/package/`.
Findings use the statuses `pass`, `gap`, `uncertain`, and `not_applicable`.

A `gap` means the source library returned supporting review authority but matching package evidence
was not found. An `uncertain` finding does not make a compliance claim.
The command fails fast if the source-library retrieval index is not reviewer-ready, and rerunning a
fixed review ID replaces prior package artifacts before writing the new report.

`review_validation.json` is the gate-facing artifact. It checks source retrieval readiness, package
extraction, package chunk creation, valid finding statuses, dual evidence for `pass` findings, source
evidence for `gap` findings, and absence of unsupported compliance claims.

## Compliance Rule Pack And Finding Graph V0

The rule-pack milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

The command writes these artifacts beside the base EA review artifacts:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

The rule pack is data, not hidden code. Each rule includes identity, title, question, requirement,
severity, package query and terms, source query, source filters, and an evidence expectation.

The finding graph contains:

- `ComplianceRulePack`
- `ComplianceReview`
- `ComplianceRule`
- `ComplianceFinding`
- `SourceLibraryEvidence`
- `PackageEvidence`
- `PackageEvidenceGap`

`compliance_validation.json` checks rule-pack validity, base EA review validation, all-rules
coverage, valid finding statuses, dual evidence for `pass`, source evidence for `gap`, source
citations for claim-bearing findings, unsupported-claim absence, finding graph evidence-edge
coverage, and finding graph integrity.

Rule-pack IDs, rule IDs, and fixed review IDs are constrained to letters, numbers, dots,
underscores, and hyphens so review outputs cannot escape the intended review directory. Rule
`source_filters` must use supported retrieval filter keys; typoed keys fail validation instead of
silently widening retrieval.

## Derived Extraction Layer

The extraction layer builds a derived text/chunk index without modifying raw artifacts.
PDF extraction uses Docling first; born-digital PDFs that exceed the Docling timeout can fall back
to `pypdf_text_fallback`, with parser name/version preserved in manifests and chunks and fallback
metadata preserved in the extraction manifest.

Derived layout:

```text
source_library/
  derived/
    <source_set_id>/
      extracted_text/
      docling_json/
      chunks/
        chunks.jsonl
      diagnostics/
        extraction_manifest.jsonl
        extraction_validation.json
        extraction_accuracy_audit.json
        summary.json
```

Derived outputs:

- extracted text per artifact
- Docling JSON when Docling is used by the parser
- HTML/XML section extraction
- chunk JSONL with stable chunk IDs
- chunk-level SHA256 or content hash
- parser diagnostics
- extraction validation report
- chunk-to-source and chunk-to-artifact links

Derived data should always be rebuildable from raw artifacts and the reviewer catalog.

## Evidence Retrieval Layer

Retrieval layout:

```text
source_library/
  derived/
    <source_set_id>/
      retrieval/
        evidence_index.sqlite
        retrieval_manifest.json
        retrieval_validation.json
        summary.json
        retrieval_eval_results.json
```

The retrieval layer is intentionally lexical and auditable for v1. It stores the source chunk text
and the provenance required for a reviewer to verify the citation back to raw artifacts and extracted
text offsets.

Retrieval validation checks:

- extraction validation passed unless explicitly overridden
- extraction scope is complete unless `--allow-partial-extraction` is passed for diagnostics
- chunks JSONL exists and contains chunks
- catalog SQLite exists
- chunk source-set IDs match the target source set
- chunk IDs are unique
- indexed source IDs match extracted source IDs in `extraction_manifest.jsonl`
- chunk hashes match the stored text
- chunk offsets are valid
- linked artifact and extracted-text paths still exist
- required citation, artifact, URL, parser, and offset fields are present

`retrieval-build` records `reviewer_ready`. This is true only when the index validates and the
extraction summary shows complete catalog coverage. A filtered one-document slice can still be
indexed with `--allow-partial-extraction`, but it remains a diagnostic index, not a reviewer-ready
corpus.

## Document Evidence Graph Layer

Evidence graph layout:

```text
source_library/
  derived/
    <source_set_id>/
      evidence_graph/
        document_graph_nodes.jsonl
        document_graph_edges.jsonl
        evidence_graph.sqlite
        evidence_graph_validation.json
        summary.json
        phase_eval_results.json
```

The evidence graph contains these node types:

- `SourceSet`
- `SourceDocument`
- `RawArtifact`
- `ExtractedText`
- `DocumentSection`
- `DocumentChunk`
- `EvidenceSpan`
- `Parser`
- `ReviewTopic`

Every `EvidenceSpan` traces to a chunk, source document, raw artifact, parser version, content
hash, citation label, URL provenance, and extracted-text offsets. The graph build also reopens the
retrieval SQLite index and requires chunk IDs, source-set IDs, provenance fields, offsets, content
hashes, text, and review topics to match before graph artifacts are persisted. The graph records
health metrics: connected components, isolated nodes, dangling edges, evidence coverage, topic
coverage, source-artifact coverage, retrieval binding mismatches, and chunk hash mismatches.

`phase-eval` keeps readiness checks phase-aligned:

- catalog capture
- extraction
- retrieval
- evidence graph
- claim extraction
- rule-claim binding
- optional compliance review when `--review-id` or `--review-dir` is passed

When a compliance review phase is included, `phase-eval` requires the review report to exist,
validation to pass, the review ID to match when supplied, and the review source set to match the
evaluated source set.

Next downstream layers are broader rule-pack coverage, reviewer adjudication workflow, embeddings
or reranking for recall improvement, and model-assisted synthesis that is constrained by evidence
and validation gates.

## Verification Commands

Run all tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Run captured-library integrity tests only:

```bash
PYTHONPATH=src python -m unittest tests.test_captured_library
```

Rebuild the full reviewer catalog from the current full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --batch-run-id full-library-batches
```

Build derived extraction outputs from the current reviewer catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

Build the evidence retrieval index:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library
```

Run a retrieval query:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-query \
  --output-dir source_library \
  --review-topic alternatives \
  "alternatives environmental effects"
```

Run the seed retrieval eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --eval-file config/retrieval_eval_seed.json
```

Build the evidence graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build \
  --output-dir source_library
```

Build source claims and run the seed claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
```

Run phase-aligned readiness evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library
```
