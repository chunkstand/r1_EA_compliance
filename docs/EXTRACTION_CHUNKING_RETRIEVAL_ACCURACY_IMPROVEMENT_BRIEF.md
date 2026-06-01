# Extraction Chunking And Retrieval Accuracy Improvement Brief

Date: 2026-06-01

Status: First bounded packet implemented locally. The read-only
`chunk-quality-audit` gate is now routed in `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md`; sidecar chunk
layers and retrieval scoring changes remain future packets.

## Implementation Status

- closed:
  `chunk-quality-audit` writes
  `source_library/derived/<source_set_id>/diagnostics/chunk_quality_audit.json`
  from the existing `chunks/chunks.jsonl` spine and reports parser, heading,
  table, structural-marker, boundary-split, offset, source-identity, and
  parent-context risk without mutating downstream artifacts.
- live smoke:
  the active source set produced `113,830` audited chunks across `719` sources,
  passed required provenance/offset/source-identity checks, and reported the
  expected `parent_context_missing` risk for every source because the sidecar
  `chunks_v2` layer is not yet present.
- still open:
  sidecar atomic/structural chunks, parent context windows, FTS/BM25 retrieval
  scoring, deterministic contextual index text, and expanded atomic/structure
  retrieval evals.

## Grounded Repo Snapshot

Read-only local evidence for `source-set-f70ea11e04ae3d53` shows:

- extraction is complete for `719/719` catalog sources with `0` extraction
  failures;
- retrieval is reviewer-ready with `113,830` chunks over `719` sources;
- current chunks average about `1,590` characters, with a `1,684` character
  median and `1,799` character maximum;
- parser chunk counts are dominated by `pypdf_text_fallback`
  (`94,736/113,830` chunks), followed by legal XML, Apple Vision OCR,
  workbook cells, HTML, DOC, DOCX, and ZIP metadata parsers;
- retrieval direct eval passes the current `12/12` shipped cases with hard
  negatives, multi-source cases, `recall_at_k=1.0`, `mrr=1.0`, and
  `ndcg_at_k=1.0`.

The implementation surface explains the main accuracy boundary:

- `extract_chunking.py` currently emits character-window chunks with structural
  hints only when parser blocks supply `heading`, `section`, or `page`.
- default extraction/review chunk settings are `1800` max characters and `200`
  overlap characters.
- `retrieval_runtime.py` creates SQLite rows and an FTS5 table, but
  `retrieval_query.py` currently loads candidate rows and applies deterministic
  Python lexical scoring instead of using SQLite FTS/BM25 as the first-stage
  retrieval scorer.
- current retrieval evals prove source/rank/provenance behavior, but do not yet
  prove atomic chunk recall, parent-window recall, table-row recall,
  section-boundary integrity, or parser/layout fidelity for the graph-KB.

## Expert Perspective

The current chunk size is not the first problem to solve. Around `1.6k`
characters is a defensible baseline for broad evidence lookup, and the current
source-set direct evals are green. The high-risk gap is that authority-bearing
NEPA, NFMA, CFR, forest-plan, FEIS, biological opinion, and table evidence is
often smaller or more structured than a fixed text window. A green source-level
retrieval eval can still hide the wrong table row, split legal condition, weak
heading context, or missing parent section.

The repo should treat chunking as a layered evidence contract rather than a
single replacement value:

1. Keep current chunks as `baseline_text_chunk_v1`.
2. Add `atomic_text_chunk_v2` for token-aware paragraph/list/section units with
   exact source offsets.
3. Add `structural_evidence_chunk_v1` for legal sections, forest-plan
   components, table rows, table cells, definitions, standards, guidelines,
   desired conditions, exceptions, and applicability clauses.
4. Add `parent_context_window_v1` for larger source windows used after precise
   retrieval.
5. Add deterministic `contextual_index_text_v1` that prepends source title,
   citation label, source record ID, document role, authority level, support
   document role, forest unit when known, heading path, page range, and parser
   route before FTS/vector indexing.

The strongest immediate improvement is audit-first, not a broad rechunk. The
repo already has a large f70 graph-KB spine; the next slice should measure where
that spine is structurally weak before changing all downstream artifacts.

## Recommended Improvement Sequence

### 1. Chunk-Quality Audit Gate

Add a read-only command such as `chunk-quality-audit` that writes tracked schema
docs and generated diagnostics under `source_library/derived/<source_set_id>/`.

Minimum per-source metrics:

- source record ID, citation label, document role, support document role,
  authority level, parser name, artifact hash;
- page count where known, extracted character count, chunk count,
  chars-per-page, chunks-per-page, low-density flags, scanned/OCR flags, and
  fallback-parser flags;
- boundary diagnostics for section headings, numbered lists, CFR sections,
  forest-plan component labels, table markers, definitions, and NEPA terms;
- chunk-offset integrity and overlap/boundary split counts.

This should produce failure buckets such as `low_density_pdf`,
`fallback_parser_table_risk`, `missing_page_map`, `heading_context_missing`,
`table_row_unstructured`, `numbered_requirement_split`, and
`parent_context_missing`.

### 2. Sidecar Chunk Layer V2

Add a sidecar chunk artifact instead of replacing `chunks.jsonl` immediately:

`source_library/derived/<source_set_id>/chunks_v2/atomic_chunks.jsonl`

Required fields:

- `chunk_layer`, `chunk_id`, `parent_chunk_id`, `parent_window_id`,
  `source_set_id`, `source_record_id`, `artifact_sha256`, `citation_label`;
- `char_start`, `char_end`, token estimate, page range, parser route,
  parser confidence/fallback flags where available;
- `section_path`, `heading_path`, `structure_type`, `component_type`,
  `table_id`, `row_index`, `cell_coordinates` where applicable;
- `content_sha256`, `contextual_index_sha256`, and exact source text.

The v2 layer should be generated from parser blocks first, then fall back to
safe text spans when structure is unavailable. It should never drop workbook row
identity or citation labels.

### 3. Structural Evidence Chunks

Implement parser-specific structure extractors where the repo already has
stronger sources:

- legal XML/XHTML: section/subsection-aware chunks for USC, CFR, CEQ, NFMA,
  ESA, NHPA, and agency directive sources;
- Docling JSON: headings, lists, tables, rows, cells, captions, page/bbox
  metadata;
- XLSX: worksheet/row/cell chunks with row and column provenance;
- forest-plan PDFs: detected standards, guidelines, desired conditions,
  objectives, management areas, geographic areas, exceptions, and applicability
  text.

This is the layer that should feed forest-plan components, rule claims, and
compliance rows. Plain text chunks remain useful for recall, but structural
chunks should carry the actual reviewer-facing evidence identity.

### 4. Retrieval Upgrade

Upgrade retrieval in steps:

- use SQLite FTS5/BM25 as a real first-stage lexical retriever instead of only
  as a persisted side table;
- index both raw text and `contextual_index_text_v1`;
- preserve deterministic metadata filters before scoring;
- merge lexical, metadata, and optional vector candidates with a deterministic
  fusion method such as reciprocal-rank fusion;
- return atomic spans plus linked parent context windows;
- add an optional provider-gated reranker experiment after deterministic
  lexical/contextual retrieval is measurable.

Do not make embeddings or a hosted reranker mandatory for reviewer readiness.
They should be evaluated as quality extensions behind runtime/provider
availability gates.

### 5. Retrieval Eval Expansion

Extend direct evals beyond current source-level retrieval:

- atomic chunk recall: the expected source is not enough; the expected legal
  unit or table row must be retrieved;
- parent-window recall: the retrieved atomic span must link to enough context
  to interpret exceptions, definitions, and applicability;
- structure recall: table rows, numbered legal requirements, definitions, and
  forest-plan components are first-class expected targets;
- wrong-forest and wrong-authority rejection;
- parser-risk stratification, especially `pypdf_text_fallback` versus Docling,
  OCR, legal XML, and XLSX sources;
- thresholded metrics for recall@k, MRR, nDCG, hard-negative pass rate,
  missing-required-unit rate, and citation correctness.

## Source Research Alignment

- Current research on chunk size does not support a universal best value. Small
  chunks can win concise fact lookup; larger chunks can win broad-context
  retrieval. This repo needs multiple evidence granularities, not one global
  chunk size.
- Contextual retrieval research supports adding chunk-specific context before
  lexical and vector indexing, then reranking a larger candidate pool. For this
  repo, the first version should use deterministic metadata context rather than
  model-generated context.
- Late chunking is relevant as an optional experiment because isolated chunks
  lose document context before embedding. It should not be the mandatory path
  until local evals prove a gain over deterministic contextual indexing.
- Legal chunking research warns that simple, recursive, and semantic chunking
  can all fail at individual legal relevance. This supports structural evidence
  chunks and legal-unit evals over a naive semantic splitter.
- Document parser capabilities matter as much as retrieval scoring. Docling can
  expose reading order, page/bbox, table, row, column, header, list, and OCR
  structure; the repo should exploit that where available and explicitly flag
  fallback-parser risks where not.

## Suggested First Bounded Packet

Open a new implementation packet for `chunk-quality-audit` before changing the
production chunk spine.

Goal:
build a read-only chunk/parser/layout risk report for the active source set.

Non-goals:
no full corpus regeneration, no network download, no graph rebuild, no
embedding provider dependency, no replacement of `chunks.jsonl`.

Owner surfaces:

- `src/usfs_r1_ea_sources/extract_chunking.py`
- a new small audit owner such as `src/usfs_r1_ea_sources/chunk_quality_audit.py`
- CLI registration
- `docs/OUTPUT_SCHEMAS.md`
- focused tests under `tests/`

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_chunk_quality_audit.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-quality-audit --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53
git diff --check
```

Stop conditions:

- the audit cannot distinguish source-level green state from chunk/structure
  weakness;
- adding the audit requires changing generated graph, claim, rule, or
  compliance artifacts;
- the active source set changes before closeout without rerunning the audit.

## Sources

- Anthropic, "Contextual Retrieval in AI Systems":
  https://www.anthropic.com/engineering/contextual-retrieval
- OpenAI API docs, File Search chunking settings:
  https://developers.openai.com/api/docs/assistants/tools/file-search
- Michael Gunther et al., "Late Chunking: Contextual Chunk Embeddings Using
  Long-Context Embedding Models": https://arxiv.org/abs/2409.04701
- Sinchana Ramakanth Bhat et al., "Rethinking Chunk Size For Long-Document
  Retrieval": https://arxiv.org/abs/2505.21700
- Andrea Filippo Ferraris et al., "Legal Chunking: Evaluating Methods for
  Effective Legal Text Retrieval": https://journals.sagepub.com/doi/10.3233/FAIA241255
- Docling project overview: https://www.docling.ai/
- "From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for
  Text-and-Table Documents": https://arxiv.org/abs/2604.01733
