# Extraction Chunking And Retrieval Accuracy Improvement Brief

Date: 2026-06-01

Status: Retrieval worktree implementation merged to `main`. The read-only
`chunk-quality-audit` gate, generated sidecar `chunk-layer-build` command,
sidecar-aware `chunk-sidecar-retrieval-eval` command, fail-closed
`chunk-sidecar-consumer-eval` preview gate, opt-in graph/claim promotion
command, sidecar rule-link preview/eval path, compliance-review adoption,
phase-eval adoption, and reviewer-package lineage validation are now routed in
`docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
`docs/SESSION_HANDOFF.md`. Production source-library sidecar promotion remains
opt-in and gated; knowledge-graph sidecar adoption remains future work.

## Implementation Status

- closed:
  `chunk-quality-audit` writes
  `source_library/derived/<source_set_id>/diagnostics/chunk_quality_audit.json`
  from the existing `chunks/chunks.jsonl` spine and reports parser, heading,
  table, structural-marker, boundary-split, offset, source-identity, and
  parent-context risk without mutating downstream artifacts.
- closed:
  `chunk-layer-build` writes `chunks_v2/atomic_chunks.jsonl`,
  `chunks_v2/structural_chunks.jsonl`,
  `chunks_v2/parent_context_windows.jsonl`, and `chunks_v2/summary.json`
  without replacing the baseline chunk spine. The live f70 smoke produced
  `296,442` atomic chunks, `116,004` structural chunks, and `19,117` parent
  windows from `113,830` baseline chunks, with full atomic parent-window
  coverage.
- closed:
  `chunk-sidecar-retrieval-eval` builds an opt-in sidecar retrieval SQLite
  index over `chunks_v2/atomic_chunks.jsonl`, runs eval cases that require
  exact atomic chunk IDs, structure types, citation labels, and parent-window
  links, and compares sidecar metrics against the baseline retrieval index.
  The live f70 smoke indexed `296,442` atomic chunks across `719` sources and
  passed `4/4` tracked eval cases with sidecar `pass_rate=1.0`,
  `atomic_chunk_recall_at_k=1.0`, `structure_hit_rate=1.0`, and
  `parent_window_coverage_rate=1.0`; the baseline comparison completed and
  exposed the intended gap with baseline `pass_rate=0.25` and zero
  atomic/structure/parent-window coverage.
- closed:
  `chunk-sidecar-consumer-eval` builds sidecar evidence-graph and claim
  previews from atomic chunks and sidecar retrieval, writes only noncanonical
  outputs, and compares graph/claim metrics against baseline summaries. The
  full f70 smoke validated sidecar chunks, retrieval, graph, and claims; graph
  metrics were not worse than baseline. The gate failed closed on claim
  promotion because sidecar claims produced `142,748` claims versus baseline
  `143,255`, and sidecar `claim_entity_coverage_rate=0.479054` versus baseline
  `0.494231`.
- closed:
  `chunk-sidecar-consumer-promote` adds the explicit opt-in canonical
  graph/claim adoption step. Dry-run is default; canonical mutation requires
  `--apply`, and replacing existing canonical graph/claim directories requires
  `--replace-canonical`. Promotion requires a passed, non-partial sidecar
  consumer eval plus reviewer-ready sidecar retrieval, graph, and claim
  summaries, and it writes failed promotion results instead of inferring paths
  when required sidecar artifacts are missing or invalid.
- closed:
  sidecar downstream adoption now extends through rule-link preview/eval,
  compliance review, phase-eval, and reviewer package lineage validation.
  `rule-claim-link --links-dir` writes isolated
  `rule_claim_links_sidecar/<rule_pack_id>/<version>/` artifacts, compliance
  review can consume validated sidecar rule links, review-scoped phase eval can
  follow those noncanonical links, and `review-packet-index` fails closed when
  sidecar compliance review, phase-eval, direct-eval, or selected sidecar paths
  are missing or inconsistent.
- live smoke:
  the active source set produced `113,830` audited chunks across `719` sources,
  passed required provenance/offset/source-identity checks, and reported the
  expected `parent_context_missing` risk for every source when the default
  `chunks_v2` sidecar summary was absent.
- still open:
  before any production canonical apply, rerun the merged sidecar consumer eval
  on the target source set and require a passed non-partial result; add broader
  sidecar eval coverage across parser-risk strata; open a separate
  knowledge-graph sidecar adoption packet with direct eval thresholds over the
  adopted sidecar-backed layers; and consider optional FTS/BM25 or reranker
  experiments only after deterministic sidecar gains remain measurable.

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
- `retrieval_runtime.py` creates SQLite rows and an FTS5 table. It now also
  supports opt-in noncanonical sidecar index directories and persists
  `chunk_layer`, `parent_chunk_id`, `parent_window_id`, `structure_type`,
  `component_type`, and deterministic contextual index text/hash fields.
- retrieval evals now prove source/rank/provenance behavior and can prove
  atomic chunk recall, structure recall, citation correctness, and
  parent-window coverage. Broader parser/layout fidelity coverage remains a
  follow-on eval expansion.

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

- closed first sidecar step: index `chunks_v2/atomic_chunks.jsonl` into a
  noncanonical retrieval sidecar and compare exact atomic/structure/parent
  eval metrics against baseline retrieval;
- closed first consumer-preview step: build noncanonical graph and claim
  previews from sidecar retrieval, compare them against baseline summaries, and
  fail closed on tracked graph/claim regressions;
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

- closed first eval step: `chunk-sidecar-retrieval-eval` adds exact
  `expected_chunk_ids`, `expected_structure_types`, `expected_citation_labels`,
  `require_parent_window`, and thresholded metrics for atomic chunk recall,
  structure hit rate, parent-window coverage, and citation correctness;
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

## Suggested Next Bounded Packet

Status: closed by `chunk-quality-audit`; the follow-on sidecar layer is closed
by `chunk-layer-build`; the first sidecar retrieval/eval packet is closed by
`chunk-sidecar-retrieval-eval`; and the first sidecar graph/claim consumer
preview gate is closed by `chunk-sidecar-consumer-eval`.

Open a new implementation packet before changing any downstream consumer to use
`chunks_v2` or `retrieval_sidecar` canonically.

Goal:
explain and resolve the f70 sidecar claim-count/entity-coverage regression, or
explicitly scope a graph-only promotion gate while leaving claim, review, and
compliance consumers on the baseline chunk spine.

Non-goals:
no full corpus regeneration, no network download, no graph rebuild, no
embedding provider dependency, no unguarded replacement of `chunks.jsonl`.

Owner surfaces:

- `src/usfs_r1_ea_sources/sidecar_retrieval_eval.py`
- `src/usfs_r1_ea_sources/sidecar_consumer_eval.py`
- `src/usfs_r1_ea_sources/retrieval_eval_runtime.py`
- `src/usfs_r1_ea_sources/claim_extraction.py`
- `src/usfs_r1_ea_sources/evidence_graph.py`
- the selected downstream consumer if promotion is chosen
- CLI registration
- `docs/OUTPUT_SCHEMAS.md`
- focused tests under `tests/`

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_sidecar_retrieval_eval.py tests/test_retrieval_eval.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-sidecar-retrieval-eval --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --chunks-v2-dir /tmp/usfs-r1-chunks-v2-next-slice --sidecar-index-dir /tmp/usfs-r1-retrieval-sidecar-next-slice --results-dir /tmp/usfs-r1-retrieval-sidecar-eval-next-slice --top-k 10
git diff --check
```

Stop conditions:

- the promotion candidate cannot distinguish source-level green state from
  exact chunk/structure/parent-window weakness;
- downstream promotion would replace baseline retrieval without a side-by-side
  comparison artifact;
- the active source set changes before closeout without rerunning the sidecar
  eval comparison.

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
