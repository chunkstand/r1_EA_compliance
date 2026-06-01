# First-Class Generated Observability Eval Context Graph

Date: 2026-06-01

Status: Milestone 0 contract, first generated graph builder and graph-eval
commands, and Milestone 1 trace-event materialization are implemented locally.

Owner surfaces:

- Contract config: `config/context_graph_contract_v1.json`
- Build/eval helper: `src/usfs_r1_ea_sources/eval_context_graph.py`
- Contract helper: `src/usfs_r1_ea_sources/eval_context_graph_contract.py`
- Event extraction helper: `src/usfs_r1_ea_sources/eval_context_graph_events.py`
- Validation helper: `src/usfs_r1_ea_sources/eval_context_graph_validation.py`
- CLI commands: `eval-context-graph-build`, `eval-context-graph-eval`
- Contract and behavior tests: `tests/test_eval_context_graph.py`
- CLI parser tests: `tests/test_cli_eval.py`

## Purpose

This graph is the generated local observability and eval graph for agent-system
execution evidence. It models logs, traces, events, eval runs, cases, scores,
artifacts, targets, and failure relationships as graph nodes and edges so later
evals can reason over paths rather than isolated result files.

The first implementation slice derives from the existing first-class
eval-trace SQLite store. It does not replace the source-set catalog, evidence
graph, source claims, or reviewer-facing NEPA knowledge graph. Source evidence
appears only as stable artifact, source-set, review, source-record, citation,
or hash references.

## Implemented Slice

`eval-context-graph-build` reads a generated
`system-eval-trace.sqlite` store and writes a deterministic graph JSON artifact.
It requires the six eval-trace store tables:

- `system_eval_runs`
- `system_eval_cases`
- `system_eval_case_results`
- `system_eval_scores`
- `trace_runs`
- `trace_spans`

The builder materializes these node kinds:

- `artifact`
- `eval_case`
- `eval_result`
- `eval_run`
- `review`
- `score`
- `source_set`
- `span`
- `span_event` for rows from event-like trace artifacts
- `trace`
- `failure_class` when a stored failure reason exists

The first edge set includes:

- `CONTAINS`
- `DERIVED_FROM`
- `EMITTED` from spans to materialized event rows
- `EVALUATED_BY`
- `FAILED_BECAUSE` when a stored failure reason exists
- `PRODUCED_ARTIFACT`
- `SCORED_AS`
- `TARGETS`
- `USED_ARTIFACT`

`span_event` and `log_event` are conditional node kinds. They materialize only
when the store points at event-like JSON/JSONL artifacts such as trace or log
files. Current trace-event extraction records event ID, event name, timestamp,
payload hash, payload keys, source-set/review IDs, trace IDs, candidate IDs,
query type, selected status, and compact counts for diagnostics/results. It
does not copy raw source text or prompt/body payloads into graph properties.

Reserved future node kinds include `state_checkpoint`, `tool_invocation`,
`model_invocation`, `prompt_version`, `dataset_example`, and `human_label`.
They are contract-visible now but not materialized until upstream capture
tables or artifacts exist.

## Graph Evals

`eval-context-graph-eval` reads the generated graph JSON and evaluates graph
invariants directly. The first graph eval checks:

- required node kinds are present;
- required edge kinds are present;
- all edges resolve to existing nodes;
- every eval result has a trace-to-result edge and a result-to-score edge;
- artifact nodes retain artifact refs or hash provenance;
- event nodes have incoming `EMITTED` edges from spans;
- event-like source artifact rows are materialized without parse errors;
- source knowledge-graph node kinds are absent;
- the graph remains local source-of-record and not approved for external export.

This is the first step toward adaptive learning: failures and regressions can
be promoted from graph paths instead of only from flat result files.

## Commands

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources eval-context-graph-build \
  --sqlite-path source_library/evaluations/eval_trace/system_eval_trace.sqlite \
  --graph-json-path source_library/evaluations/eval_context_graph/eval_context_graph.json \
  --summary-path source_library/evaluations/eval_context_graph/eval_context_graph_build_summary.json

PYTHONPATH=src python -m usfs_r1_ea_sources eval-context-graph-eval \
  --graph-json-path source_library/evaluations/eval_context_graph/eval_context_graph.json \
  --summary-path source_library/evaluations/eval_context_graph/eval_context_graph_eval_summary.json
```

Both commands are generated-artifact-only. They do not mutate source-library
catalog, extraction, retrieval, review, compliance, or promotion artifacts.

## Stop Conditions

Stop and open a new packet if the next slice requires:

- adding raw prompt, source document body, or sensitive content fields to
  exportable graph properties;
- making Neo4j, a hosted observability platform, or an external telemetry sink
  the source of record;
- adding LLM-inferred causal/root-cause edges without deterministic scorer or
  human-label provenance;
- mixing source knowledge-graph facts into observability/eval graph nodes;
- ratcheting phase or promotion gates on context graph evals before an explicit
  scope is approved.
