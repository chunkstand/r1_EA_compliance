# Extraction Chunking Retrieval Accuracy Implementation Milestone Plan

Date: 2026-06-01

Status: Resolved locally on branch `codex/extraction-chunking-retrieval-accuracy`.
Plan class: implementation
High-risk implementation: yes

Owner context: isolated worktree
`/Users/chunkstand/projects/usfs-r1-EA-sources-extraction-chunking-retrieval-accuracy`.
This plan implements the research and improvement briefs without changing the
active source-set route or replacing the production chunk spine.

## Intent Lock

Advance extraction/chunking/retrieval accuracy for the f70 graph-KB by adding
measurable sidecar artifacts and retrieval/eval hooks. Do not reopen source
capture, forest-specific example promotion, context-graph work, hosted query
service work, or full graph rebuilds in this packet.

## Purpose

Turn the research brief into executable repo behavior. The current f70 chunk
spine is source-set green, but it does not expose chunk/layout risk, sidecar
atomic/structural evidence chunks, contextual index text, or eval fields for
atomic/parent/structural retrieval quality.

## Current Evidence

- `docs/EXTRACTION_CHUNKING_RETRIEVAL_ACCURACY_RESEARCH_BRIEF.md` concludes
  chunk size alone is not the accuracy lever.
- `docs/EXTRACTION_CHUNKING_RETRIEVAL_ACCURACY_IMPROVEMENT_BRIEF.md`
  recommends an audit-first sidecar path.
- Current implementation uses `1800` character chunks with `200` character
  overlap in `extract_chunking.py`.
- `retrieval_runtime.py` writes FTS5 but `retrieval_query.py` primarily scores
  Python-loaded rows rather than treating FTS/BM25 as first-stage retrieval.
- Current retrieval eval coverage is source/rank/provenance oriented, not
  atomic chunk, structural evidence, or parent-window oriented.

## Goal

Complete the first high-accuracy implementation packet:

- add a read-only `chunk-quality-audit` command;
- add a `chunk-layer-build` sidecar command that writes atomic chunks,
  structural evidence chunks, parent context windows, and deterministic
  contextual index text;
- update retrieval indexing/querying so contextual index text is indexed and
  FTS5/BM25 acts as first-stage candidate generation where available;
- extend retrieval eval output to score expected chunk IDs, structural types,
  parent-window presence, and citation correctness when cases declare those
  expectations;
- update schema/routing docs and handoff/current-state docs without declaring a
  full f70 graph rebuild.

## Non-Goals

- No downloader, workbook, catalog, or network refresh.
- No replacement of `source_library/derived/<source_set_id>/chunks/chunks.jsonl`.
- No mandatory embedding provider, hosted reranker, or hosted query API.
- No rebuild of evidence graph, claims, rule links, compliance review, or NEPA
  knowledge graph as part of this packet.
- No changes to context-graph work in the main checkout.

## Intent Hierarchy

- Invariant: preserve the current source-set route, baseline chunk spine, and
  reviewer-ready graph state while adding measurable sidecar accuracy surfaces.
- Optimization target: improve retrieval accuracy observability and candidate
  quality through deterministic chunk diagnostics, sidecar structure, and
  contextual lexical search before adding model-hosted reranking.
- Acceptable tradeoffs: sidecar outputs may be opt-in until eval coverage
  proves promotion readiness; live f70 smoke may use temporary output paths to
  avoid mutating ignored production evidence.
- Explicit non-negotiables: do not weaken tests, eval thresholds, fixture
  expectations, architecture gates, or extraction/retrieval validation to make
  this packet pass.

## Owner Surfaces

- `src/usfs_r1_ea_sources/chunk_quality_audit.py`
- `src/usfs_r1_ea_sources/chunk_layers.py`
- `src/usfs_r1_ea_sources/retrieval_runtime.py`
- `src/usfs_r1_ea_sources/retrieval_query.py`
- `src/usfs_r1_ea_sources/retrieval_eval_runtime.py`
- `src/usfs_r1_ea_sources/cli_derived.py`
- `src/usfs_r1_ea_sources/cli_derived_registration.py`
- `docs/architecture_contract.toml`
- `docs/OUTPUT_SCHEMAS.md`
- focused tests under `tests/`

## Placement Rules

- Sidecar chunk artifacts belong to the extraction layer and must keep workbook
  row identity, artifact hash, citation label, parser route, source offsets,
  and source text.
- Retrieval may consume sidecar atomic chunks but must continue to accept the
  current baseline `chunks.jsonl`.
- Contextual index text must be deterministic metadata, not model-generated
  prose.
- Retrieval eval expansion must be optional per case so existing source-level
  eval contracts remain compatible.

## Weak-Point Prevention

| Weak point | Owner | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Audit reports source-set green while hiding layout/chunk risk | `chunk_quality_audit.py` | per-source risk buckets and aggregate counts | no fallback/parser/boundary/structure risk buckets are emitted for risky fixtures |
| Sidecar chunks lose citation identity | `chunk_layers.py` | tests assert source record, artifact hash, citation label, offsets, parent window, and hashes | any sidecar record lacks required provenance |
| Retrieval still ignores FTS/BM25 | `retrieval_query.py` | tests assert query summaries report FTS candidate generation | non-empty text queries over FTS indexes use only row-scan mode |
| Contextual indexing pollutes evidence spans | `retrieval_runtime.py`, `retrieval_query.py` | contextual text indexed separately; evidence spans still come from source text | returned evidence span contains contextual prefix text |
| Eval expansion breaks legacy cases | `retrieval_eval_runtime.py` | existing retrieval tests plus new structural cases | default retrieval eval cannot run without structural expectations |

## Milestone Sequence

### Milestone 1 - Audit And Sidecar Chunk Layers

Outcome label: resolved

Implement `chunk-quality-audit` and `chunk-layer-build`, add schema docs,
architecture ownership, CLI registration, and focused tests.

Acceptance:

- `chunk-quality-audit` writes
  `source_library/derived/<source_set_id>/diagnostics/chunk_quality_audit.json`
  with per-source metrics, aggregate risk counts, checks, and `passed=true`
  for valid input.
- `chunk-layer-build` writes
  `chunks_v2/atomic_chunks.jsonl`,
  `chunks_v2/structural_chunks.jsonl`,
  `chunks_v2/parent_context_windows.jsonl`, and `chunks_v2/summary.json`.
- Atomic records carry `chunk_layer`, `parent_chunk_id`, `parent_window_id`,
  source IDs, offsets, citation label, parser route, token estimate,
  contextual index text, and content hashes.
- Structural records are emitted for numbered/legal/table/forest-plan markers
  in fixtures.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_chunk_quality_audit.py tests/test_chunk_layers.py tests/test_cli.py tests/test_architecture_contract.py
git diff --check
```

### Milestone 2 - Contextual FTS/BM25 Retrieval And Eval Hooks

Outcome label: resolved

Extend retrieval index/query/eval behavior while preserving compatibility.

Acceptance:

- retrieval index rows include deterministic `contextual_index_text`.
- FTS indexes raw text plus contextual text and query summaries identify
  `retrieval_mode="fts_first_stage"` when FTS candidate generation is used.
- query results include sidecar metadata when indexed chunks carry it, while
  evidence spans remain source-text spans.
- eval results score optional `expected_chunk_ids`,
  `expected_structure_types`, `require_parent_window`, and citation
  expectations.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_retrieval_eval.py tests/test_retrieval_validation.py tests/test_architecture_contract.py
git diff --check
```

### Milestone 3 - Live Smoke And Closeout

Outcome label: resolved

Run the new commands against available local source-library evidence without
staging ignored generated outputs, update durable docs/handoff, and commit the
verified slice.

Acceptance:

- if f70 ignored corpus is available, run:

```bash
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources chunk-quality-audit --output-dir <source_library_owner> --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources chunk-layer-build --output-dir <source_library_owner> --source-set-id source-set-f70ea11e04ae3d53
```

- if the isolated worktree lacks f70 ignored corpus, record that limitation and
  rely on focused fixture coverage plus `git diff --check`.
- docs updated: `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, and this plan.
- one atomic local commit contains the verified implementation slice.

## Stop Conditions

- Any change requires replacing the baseline `chunks.jsonl` or rebuilding graph
  artifacts to preserve current green state.
- Retrieval compatibility with existing `retrieval-build`, `retrieval-query`,
  or `retrieval-eval` breaks.
- Architecture-contract ownership cannot be expressed without a broad layer
  rewrite.
- Live source-library smoke would overwrite production retrieval artifacts
  rather than writing sidecar/audit outputs.

## Closeout Outcome Record

- Outcome: resolved locally. The implementation adds the audit command,
  sidecar chunk-layer command, contextual FTS/BM25 retrieval fields, optional
  atomic/structural retrieval eval expectations, schema docs, state docs, and
  handoff updates.
- Verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_chunk_layers.py tests/test_chunk_quality_audit.py tests/test_retrieval.py tests/test_retrieval_eval.py tests/test_retrieval_validation.py tests/test_cli.py tests/test_architecture_contract.py -q`
  passed `60` tests; `PYTHONPATH=src uv run --extra dev ruff check src tests`
  passed; plan lint passed in strict mode; `git diff --check` passed.
- Live smoke: using the ignored f70 corpus in the main checkout as read-only
  input, `chunk-quality-audit` passed over `113830` chunks and `719` sources
  with output in `/tmp`; `chunk-layer-build` wrote temporary `/tmp` sidecars
  with `296442` atomic chunks, `116004` structural chunks, `19117` parent
  windows, and `validation_passed=true`.
- Docs and handoff: updated `README.md`, `docs/OUTPUT_SCHEMAS.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and this plan.
- Commit policy: stage only the verified implementation slice and record one
  atomic local commit; push remains out of scope.
