# First-Class Generated Observability Eval Context Graph

Date: 2026-06-01

Status: Milestone 0 contract, first generated graph builder and graph-eval
commands, Milestone 1 trace-event materialization, Milestone 2 explicit
event-log capture, Milestone 3 canonical CLI command-event capture, and
Milestone 4 f70 source-set phase-eval ratchet are implemented locally.

Owner surfaces:

- Contract config: `config/context_graph_contract_v1.json`
- Build/eval helper: `src/usfs_r1_ea_sources/eval_context_graph.py`
- Contract helper: `src/usfs_r1_ea_sources/eval_context_graph_contract.py`
- Event extraction helper: `src/usfs_r1_ea_sources/eval_context_graph_events.py`
- Validation helper: `src/usfs_r1_ea_sources/eval_context_graph_validation.py`
- Command event capture helper: `src/usfs_r1_ea_sources/observability_events.py`
- Phase-eval ratchet helper:
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_context_graph.py`
- Phase-eval graph producer dispatch:
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_graph_producers.py`
- Phase-eval contract: `config/phase_eval_direct_eval_v1.json`
- CLI commands: `eval-context-graph-build`, `eval-context-graph-eval`
- Contract and behavior tests: `tests/test_eval_context_graph.py`
- Command capture tests: `tests/test_observability_events.py`
- CLI parser tests: `tests/test_eval_context_graph_cli.py`
- Phase-eval ratchet tests: `tests/test_phase_eval_context_graph.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`, `tests/test_phase_eval.py`

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
- `event_source` for explicitly supplied local event/log artifacts
- `span_event` for rows from event-like trace artifacts
- `log_event` for rows from explicitly supplied local log/event artifacts
- `trace`
- `failure_class` when a stored failure reason exists

The first edge set includes:

- `CONTAINS`
- `DERIVED_FROM`
- `EMITTED` from spans or explicit event sources to materialized event rows
- `EVALUATED_BY`
- `FAILED_BECAUSE` when a stored failure reason exists
- `PRODUCED_ARTIFACT`
- `SCORED_AS`
- `TARGETS`
- `USED_ARTIFACT`

`span_event`, `log_event`, and `event_source` are conditional node kinds. Span
events materialize when the store points at event-like JSON/JSONL artifacts
such as trace or log files. Explicit log events materialize when
`eval-context-graph-build` receives one or more `--event-log-path` inputs.
The top-level CLI appends redacted command lifecycle events to
`source_library/evaluations/observability_events/command_events.jsonl` by
default. `eval-context-graph-build` includes that canonical command-event log
when it exists, unless `--no-observability-event-log` is passed.
`USFS_R1_OBSERVABILITY_EVENT_LOG` can point command capture and graph builds at
another local JSONL path, and `USFS_R1_OBSERVABILITY_EVENTS_DISABLED` disables
command capture.
Current event extraction records event ID, event name, timestamp, payload hash,
payload keys, source-set/review IDs, trace IDs, candidate IDs, query type,
selected status, and compact counts for diagnostics/results. It does not copy
raw source text or prompt/body payloads into graph properties.

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
- event nodes have incoming `EMITTED` edges from spans or explicit event
  sources;
- event-like source artifact rows are materialized without parse errors;
- canonical command-event nodes keep command, phase, invocation ID, payload
  hash, and incoming `EMITTED` edges;
- source knowledge-graph node kinds are absent;
- the graph remains local source-of-record and not approved for external export.

This is the first step toward adaptive learning: failures and regressions can
be promoted from graph paths instead of only from flat result files.

## Phase-Eval Ratchet

`config/phase_eval_direct_eval_v1.json` now requires
`source_library/evaluations/eval_context_graph/eval_context_graph_eval_summary.json`
as the `observability_eval_context_graph` source-set phase for
`source-set-f70ea11e04ae3d53`.

The ratchet fails closed when the graph eval summary is missing, schema-invalid,
identity-mismatched, failed, missing the expected source-set ID, missing event
nodes, missing clean validation checks, or built against a stale context-graph
contract hash. Passing status contributes one critical direct-eval phase to
`evaluation_coverage`; it does not make the optional first-class eval-trace
gate blocking for unrelated review IDs.

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

Standalone local event logs can be attached with repeated `--event-log-path`
arguments:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources eval-context-graph-build \
  --sqlite-path source_library/evaluations/eval_trace/system_eval_trace.sqlite \
  --graph-json-path source_library/evaluations/eval_context_graph/eval_context_graph.json \
  --summary-path source_library/evaluations/eval_context_graph/eval_context_graph_build_summary.json \
  --event-log-path source_library/evaluations/operator_events/operator_events.jsonl
```

Each explicit path is represented by an `event_source` node. Rows from JSONL
or JSON `events` arrays become `log_event` or `span_event` nodes and must be
connected by `EMITTED` edges to pass graph eval.

The canonical command-event log is included automatically when present. Disable
that automatic inclusion for isolated tests with `--no-observability-event-log`.

After building and evaluating the graph, replay the f70 source-set ratchet with:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --source-set-id source-set-f70ea11e04ae3d53
```

The current local replay passes `23/23` phases with
`observability_eval_context_graph="direct_eval_present"`,
`critical_phase_count=10`, `direct_eval_ready_phase_count=10`, and
`missing_direct_eval_phase_count=0`.

## Stop Conditions

Stop and open a new packet if the next slice requires:

- adding raw prompt, source document body, or sensitive content fields to
  exportable graph properties;
- making Neo4j, a hosted observability platform, or an external telemetry sink
  the source of record;
- adding LLM-inferred causal/root-cause edges without deterministic scorer or
  human-label provenance;
- mixing source knowledge-graph facts into observability/eval graph nodes;
- adding promotion gates or additional ratcheted source-set/review scopes
  without a new explicit scope.
