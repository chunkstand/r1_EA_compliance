# Context Graphs For Agent Traces Research Brief

Date: 2026-05-31

Status: Research addendum. This is not an active route change and does not
supersede `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, or
`docs/SESSION_HANDOFF.md`.

## Purpose

This brief covers context graphs for agent logs, evals, traces, and execution
history. It does not cover knowledge graphs for source documents or regulatory
authority facts.

The useful distinction is:

- a source knowledge graph models external domain facts;
- a trace tree models one execution path as nested spans;
- a context graph models the evidence around execution itself: traces, logs,
  eval cases, scores, datasets, state checkpoints, artifacts, human review, and
  causal or replay relationships across runs.

For this repository, a context graph should be a derived observability and eval
layer over the existing first-class eval/trace store, not a replacement for
source-set catalogs, evidence graphs, or reviewer-facing knowledge graph work.

## Research Takeaways

OpenTelemetry is still the right base layer. It treats a trace as the path of a
request through a system, with spans as units of work. Spans already include
parent span IDs, timestamps, attributes, events, status, and optional span links.
Span events are structured log annotations at a point in time, and span links
exist specifically to associate spans across traces when there is causal but
non-parent-child execution, such as asynchronous work.

OpenTelemetry logs also carry first-class trace context fields. The stable log
data model includes `TraceId`, `SpanId`, severity, body, resource,
instrumentation scope, attributes, and event name. That makes log records
joinable into the same execution graph instead of leaving them as unstructured
side text.

Agent systems need AI-specific trace semantics on top of that base. OpenInference
defines a span-kind taxonomy over OpenTelemetry for `LLM`, `AGENT`, `CHAIN`,
`TOOL`, `RETRIEVER`, `RERANKER`, `EMBEDDING`, `GUARDRAIL`, `EVALUATOR`, and
`PROMPT`. Its framing is close to the context-graph need: traces need enough
identity and context to explain or reproduce an agent run, while preserving
field-level privacy controls before export.

Current agent observability products are converging on the same loop:

1. Capture trace/span/log data for a run.
2. Attach scores, labels, or evaluator results to traces or spans.
3. Promote important production traces into datasets or eval cases.
4. Compare experiments across model, prompt, tool, retrieval, and workflow
   versions.
5. Use failing traces to drive new test cases, scorer changes, and remediation.

Examples:

- OpenAI Agents SDK traces agent runs, LLM generations, tool calls, handoffs,
  guardrails, and custom events by default; OpenAI trace grading uses graded
  traces for systematic agent evaluation.
- Phoenix combines tracing, evaluation, prompt work, datasets, experiments,
  human annotations, and OpenTelemetry/OpenInference ingestion.
- Braintrust treats a trace as one end-to-end execution in logs or experiments
  and includes span types for eval, task, llm, function, tool, and score.
- LangSmith experiments capture outputs, evaluator scores, and execution traces
  per dataset example.
- Langfuse models traces as requests and nested observations such as
  generations, tool calls, and RAG retrieval steps.
- LangGraph makes the execution graph explicit through state, nodes, and edges,
  and its checkpointer persists state snapshots at execution steps. That is not
  the same as a post-hoc context graph, but it shows why state snapshots and
  graph transitions should be preserved as first-class nodes.

The research trend is moving from trace inspection to graph analysis. AgentGraph
converts execution logs into trace-linked graph nodes for agents, tasks, tools,
data inputs/outputs, and humans, with typed edges for consumption, delegation,
sequencing, tool use, produced outputs, delivery, and human intervention.
AgentTrace's causal-graph paper reconstructs causal graphs from execution logs,
walks backward from failures, and ranks likely root causes without needing an
LLM at debugging time. Another AgentTrace paper argues for structured logs
across operational, cognitive, and contextual surfaces, exported through
JSONL/OpenTelemetry-style sinks.

The important lesson is that the graph is not "more tracing UI." It is a
queryable model that adds non-tree edges the span hierarchy cannot express:
dataset lineage, eval lineage, human approval, artifact version, state snapshot,
replay/fork, async causal links, failure class, and cross-run comparison.

## Candidate Context Graph Shape

Minimal nodes:

- `session` or `thread`
- `run`
- `trace`
- `span`
- `span_event`
- `log_event`
- `state_checkpoint`
- `artifact`
- `config_version`
- `prompt_version`
- `model_invocation`
- `tool_invocation`
- `eval_case`
- `eval_run`
- `score`
- `dataset_example`
- `human_label`
- `failure_class`

Minimal edges:

- `contains`: session to run, run to trace, trace to span, span to child span
- `follows`: ordered step-to-step sequence when it differs from parentage
- `links_to`: OpenTelemetry-style causal span links across traces
- `emitted`: span to span event or log event
- `used`: span or run to prompt, model, tool, config, source-set, or artifact
- `produced`: span or run to artifact, output, score, or report
- `evaluated_by`: run, trace, span, or artifact to eval case/run
- `scored_as`: eval result to score and threshold contract
- `derived_from`: dataset example or promoted eval case to source trace/span
- `reviewed_by`: trace/run/artifact to human label or approval decision
- `checkpoint_before` and `checkpoint_after`: span or graph node to state
  snapshot
- `replayed_from` or `forked_from`: rerun to prior run or checkpoint
- `failed_because`: failing run/span/eval to failure class or root-cause node

In a local store, these can be materialized as a property graph table pair:

- `context_graph_nodes(id, kind, stable_ref, properties_json, source_hash)`
- `context_graph_edges(id, kind, from_node_id, to_node_id, properties_json)`

The graph should be rebuilt from canonical trace/eval/log artifacts, not edited
manually. Each node and edge needs enough provenance to point back to the source
trace span, eval result, log line, artifact hash, or handoff record that created
it.

## Fit For This Repository

The current first-class eval/trace store is already the right substrate:

- `system_eval_runs`
- `system_eval_cases`
- `system_eval_case_results`
- `system_eval_scores`
- `trace_runs`
- `trace_spans`

The next context-graph slice, if approved later, should derive from those rows
plus existing local artifacts. It should not mutate source-library evidence or
make a hosted telemetry platform the source of record.

Recommended interpretation:

- Keep `system_eval_*` and `trace_*` as canonical normalized tables.
- Add a derived graph export or generated local SQLite graph view only after the
  existing eval-trace store remains green for the selected ratcheted scopes.
- Preserve local identifiers, source-set IDs, review IDs, artifact paths,
  artifact hashes, scorer contract IDs, redaction status, and ratchet scope.
- Use OpenInference/OpenTelemetry names for export compatibility, but keep local
  provenance fields as required, fail-closed data.
- Treat model-judge scores as graph annotations, not gate-satisfying truth,
  until calibrated scorer contracts exist.

Do not confuse this with the repo's source evidence graph. The source evidence
graph answers "what source information supports this EA review finding?" A
context graph answers "what happened during this agent/reviewer-system run, what
state and artifacts did it use, how was it scored, and where did failures or
human decisions come from?"

## Queries A Context Graph Should Answer

- Which traces produced failing eval scores for a given review ID or source-set
  ID?
- Which failure classes recur across runs even when final phase-eval is green?
- Which artifact hash, prompt/config version, or scorer contract changed between
  two runs?
- Which tool/retrieval spans fed the evaluated output?
- Which production trace was promoted into a tracked eval case, and what human
  label justified it?
- Which span or state checkpoint should be replayed to reproduce a failure?
- Which apparent success used a fallback path, stale retrieval trace, or
  unapproved model-judge annotation?
- Which human approval or rejection decision is linked to the run and the exact
  output artifact it reviewed?

## Guardrails

- Keep the graph local-first and rebuildable.
- Separate trace observation from gate truth: a trace can describe a run without
  proving that the run was reviewer-ready.
- Keep source knowledge-graph nodes out of this graph except by stable artifact
  reference.
- Do not store raw sensitive prompts or document bodies in exportable graph
  fields unless the redaction policy explicitly allows it.
- Prefer deterministic edge construction from known IDs and hashes over
  LLM-inferred causal relationships.
- Let causal/root-cause annotations be additional graph edges with scorer or
  detector provenance, not unqualified facts.

## Possible Future Slice

If this becomes implementation work, the narrow first slice should be docs and
schema only:

1. Add a context-graph contract that names node kinds, edge kinds, required
   provenance, and redaction policy.
2. Add a read-only builder that derives graph nodes/edges from an existing
   `system_eval_trace.sqlite` file and writes a generated local JSON export.
3. Add focused tests for span-parent edges, eval-to-score edges, artifact-hash
   provenance, and no source-knowledge-graph pollution.
4. Do not add hosted exports, model-judge root-cause scoring, or gate ratchets
   in the first slice.

## Source Notes

- OpenTelemetry traces:
  <https://opentelemetry.io/docs/concepts/signals/traces/>
- OpenTelemetry log data model:
  <https://opentelemetry.io/docs/specs/otel/logs/data-model/>
- OpenInference specification:
  <https://arize-ai.github.io/openinference/spec/>
- OpenAI Agents SDK tracing:
  <https://openai.github.io/openai-agents-python/tracing/>
- OpenAI trace grading:
  <https://platform.openai.com/docs/guides/trace-grading>
- Phoenix overview:
  <https://arize.com/docs/phoenix>
- Braintrust trace anatomy:
  <https://www.braintrust.dev/docs/observe/examine-traces>
- LangSmith evaluation concepts:
  <https://docs.langchain.com/langsmith/evaluation-concepts>
- Langfuse data model:
  <https://langfuse.com/docs/observability/data-model>
- LangGraph graph API and persistence:
  <https://docs.langchain.com/oss/python/langgraph/graph-api> and
  <https://docs.langchain.com/oss/python/langgraph/persistence>
- AgentGraph, AAAI 2026:
  <https://ojs.aaai.org/index.php/AAAI/article/view/42393>
- AgentTrace causal graph tracing:
  <https://arxiv.org/abs/2603.14688>
- AgentTrace structured logging:
  <https://arxiv.org/abs/2602.10133>
