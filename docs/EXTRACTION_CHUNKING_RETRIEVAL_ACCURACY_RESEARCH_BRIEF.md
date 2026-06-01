# Extraction Chunking And Retrieval Accuracy Research Brief

Date: 2026-05-31

Status: Research addendum for implementation planning. This brief does not
change the active route and does not supersede `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, or `docs/SESSION_HANDOFF.md`.

## Purpose

This brief answers whether the current approximately `1.6k` character chunks
are likely to be accurate enough for a Region 1 NEPA extracted graph knowledge
base, and what the next high-accuracy chunking target should be.

The short answer: the current chunk size is plausible as a baseline retrieval
unit, but chunk size alone is not the accuracy lever. The accuracy risks are
parser fidelity, table/layout loss, missing structural boundaries, context loss
inside isolated chunk embeddings, weak hybrid retrieval/reranking, and sparse
eval coverage for NEPA and forest-plan evidence questions.

## Current Local Snapshot

Read-only local artifact snapshot on 2026-05-31 for
`source-set-f70ea11e04ae3d53`:

- current pointer reported `719` sources and `707` artifacts;
- retrieval reported `113,830` chunks over all `719` source rows;
- chunk text averaged about `1,590` characters per chunk;
- extracted text totaled about `158.4M` source characters, while chunk text
  totaled about `181.0M` characters after overlap;
- PDF artifacts accounted for `475` files, about `49,496` pages, `96,779`
  chunks, about `2,718` extracted characters per page, and about `1.96` chunks
  per page;
- extraction parser mix was dominated by `pypdf_text_fallback` for PDFs, with
  smaller Docling and Apple Vision/OCR subsets.

Treat these numbers as a local snapshot, not as durable current truth. Future
implementation should recompute them from manifest and chunk artifacts.

## Research Takeaways

There is no universal high-accuracy chunk size. A 2025 long-document retrieval
study found that small chunks around `64-128` tokens can be strongest for
concise fact lookup, while larger `512-1024` token chunks can work better for
questions requiring broader context. The repo's current average chunk, roughly
`350-450` tokens depending on text, sits between those regimes and is
reasonable for a baseline evidence index, but it is not enough by itself for
high-confidence legal and forest-plan reasoning.

OpenAI File Search currently defaults to `800` token chunks with `400` token
overlap, up to `20` chunks added to context for GPT-4-class and o-series runs.
That default is larger than the repo's current chunks and has much heavier
overlap. The comparison suggests the repo's chunks are not unusually large; if
anything, the more important gap is the lack of token-aware overlap,
contextualization, and reranking guarantees around those chunks.

Legal and regulatory chunking remains hard. A 2024 legal chunking study found
that simple splitting, recursive splitting, and semantic chunking did not
consistently produce high semantic relevance at the individual-chunk level for
legal questions. NEPA, NFMA, forest-plan, ESA, and CFR evidence has the same
failure modes: definitions, exceptions, table rows, standards, and applicability
conditions often depend on surrounding headings and clauses.

Contextual Retrieval is a strong current pattern. Anthropic's approach prepends
short chunk-specific context before embedding and BM25 indexing, then combines
contextual embeddings, contextual BM25, and reranking. Anthropic reports that a
reranked contextual embedding plus contextual BM25 setup reduced top-20
retrieval failure rate from `5.7%` to `1.9%` in its tests. The relevant lesson
for this repo is not to copy the exact hosted workflow, but to make chunk
identity and surrounding source context part of retrieval.

Late chunking is another current pattern. Instead of splitting first and
embedding isolated chunks, late chunking embeds a larger document context with a
long-context embedding model, then pools chunk embeddings afterward. This
directly addresses the problem that isolated chunks lose anaphora, definitions,
topic continuity, and section-level meaning.

Structure-aware and semantic chunking are useful, but not sufficient alone.
Recent semantic chunking work argues that fixed-size chunking can split meaning
and that document structure such as sections, titles, tables, and paragraphs can
improve retrieval quality. For this repo, the practical implementation should
combine structure-aware chunking with deterministic provenance, not replace
provenance with opaque semantic clusters.

## Implications For This Repo

The current `1.6k` character chunk size is not the main blocker. At roughly two
chunks per PDF page, it is plausible for first-pass retrieval. The bigger risks
are:

- `pypdf_text_fallback` can lose layout, table structure, reading order, headers,
  footers, and scanned-page content;
- table-heavy forest-plan, FEIS, biological opinion, and regulatory documents
  need row/cell-aware evidence, not only plain text spans;
- heading and section paths must travel with chunks so "standard," "guideline,"
  "desired condition," "exception," and "applicability" clauses are not
  detached from their authority context;
- fixed-size chunks can split numbered requirements, definitions, and citations;
- overlap in characters is weaker than token-aware or structure-aware overlap;
- retrieval evals need to measure whether the right chunk, parent section,
  table row, and source document are recovered for known NEPA/forest-plan
  questions.

## Recommended Implementation Target

Keep the current chunks as `baseline_text_chunk_v1`, then add a high-accuracy
chunk layer instead of replacing the existing artifact immediately.

Recommended chunk layers:

1. `atomic_text_chunk`
   Token-aware paragraph/list/section chunks, constrained by a target such as
   `300-600` tokens and carrying exact source offsets, page range, section path,
   heading, source record ID, parser, artifact hash, and citation label.

2. `structural_evidence_chunk`
   First-class chunks for numbered standards, guidelines, desired conditions,
   definitions, CFR subsections, forest-plan components, table rows, and table
   cells. These should be emitted from parser/layout output where available and
   fail closed to text spans when structure is not recoverable.

3. `parent_context_window`
   Larger parent sections or page windows, approximately `800-1500` tokens, used
   for answer grounding after atomic retrieval. This keeps precise matching
   separate from enough context to reason correctly.

4. `contextual_chunk_text`
   A deterministic context prefix for indexing, initially generated from source
   metadata rather than an LLM:
   source title, citation label, document role, authority level, forest unit
   where known, section path, page range, component type, and support-document
   role. Optional model-generated context can be evaluated later, with hashes and
   provenance.

5. `late_chunk_embedding_experiment`
   Optional experimental index over long-context embedding models. It should be
   gated behind reproducible evals and provider/runtime availability, not made
   the only retrieval path.

Recommended retrieval stack:

- keep BM25/FTS over raw and contextual chunk text;
- add vector retrieval over contextual chunks when an embedding provider is
  available;
- add reranking over the merged top candidates;
- return parent context windows for final evidence review;
- preserve exact citation-bearing atomic spans for graph edges, claims, rules,
  and compliance rows.

## Required Eval Gates

Before calling high-accuracy chunks implemented, add gates that answer these
questions from artifacts, not prose:

- Extraction density:
  every PDF has page count, chars per page, parser name, OCR/table flags, and a
  documented exemption bucket for maps, images, or intentionally short notices.
- Parser fidelity:
  sampled pypdf, Docling, OCR, HTML, XML, DOCX, DOC, and XLSX sources compare
  extracted text to source bytes or parser-native blocks.
- Structure preservation:
  table rows, numbered list items, forest-plan component labels, CFR sections,
  and definitions are present as retrievable structural chunks where the source
  contains them.
- Boundary integrity:
  chunks do not split critical legal units without parent links; every atomic
  chunk has parent section/page context.
- Retrieval quality:
  gold NEPA/forest-plan questions evaluate source recall, atomic chunk recall,
  parent-window recall, hard-negative rejection, wrong-forest rejection, and
  citation correctness.
- Graph compatibility:
  evidence graph, source claims, rule-claim binding, compliance review, and
  knowledge graph exports read the new chunk layer without losing source record
  identity or citation labels.

## Suggested First Slice

The best bounded implementation slice is an audit-first chunk-quality report:

- compute per-source `page_count`, `text_char_count`, `chars_per_page`,
  `chunk_count`, `chunks_per_page`, parser name, document role, and source
  partition;
- identify low-density PDFs, table-heavy PDFs, scanned/OCR sources, and sources
  dominated by fallback parsers;
- compare current chunk boundaries against section headings, numbered lists,
  table markers, forest-plan component markers, CFR section markers, and NEPA
  terms;
- output a tracked summary schema and focused tests, while writing generated
  corpus diagnostics under `source_library/`;
- use the audit to select the next parser/chunking work by measured failure
  bucket instead of intuition.

That slice avoids premature rewrites while giving the repo a measurable answer
to whether `113,830` chunks are complete enough for a graph knowledge base.

## Sources

- Anthropic, "Contextual Retrieval in AI Systems":
  https://www.anthropic.com/engineering/contextual-retrieval
- OpenAI API docs, File Search chunking configuration:
  https://developers.openai.com/api/docs/assistants/tools/file-search
- Michael Gunther, Isabelle Mohr, Daniel James Williams, Bo Wang, Han Xiao,
  "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding
  Models": https://arxiv.org/abs/2409.04701
- Sinchana Ramakanth Bhat, Max Rudat, Jannis Spiekermann, Nicolas
  Flores-Herr, "Rethinking Chunk Size For Long-Document Retrieval":
  https://arxiv.org/abs/2505.21700
- Andrea Filippo Ferraris, Davide Audrito, Giovanni Siragusa, Alessandro
  Piovano, "Legal Chunking: Evaluating Methods for Effective Legal Text
  Retrieval": https://journals.sagepub.com/doi/10.3233/FAIA241255
- Max-Min semantic chunking of documents for RAG application:
  https://link.springer.com/article/10.1007/s10791-025-09638-7
