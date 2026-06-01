# Context Graphs For Agent Traces Research Brief

Date: 2026-05-31

Status: Research addendum. The first local implementation slice is now tracked
in `docs/FIRST_CLASS_OBSERVABILITY_EVAL_CONTEXT_GRAPH.md`; this brief remains
background research and does not supersede `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, or `docs/SESSION_HANDOFF.md`.

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

## 2026 Neo4j And Adjacent Signals

As of 2026-05-31, Neo4j is using "context graph" as a broad production-AI
infrastructure term. The clearest Neo4j signal is the NODES AI 2026 Graph Memory
& Agents track:

- "Exploring Context Graphs: From Data to Decisions" frames context graphs as
  the missing layer between data and decisions: systems capture the why behind
  actions, learn from experience, and evolve with interactions.
- "Tracing Agent Decisions with Graph Evals and Neo4j" narrows that idea toward
  this repo's target. It describes graph evals where every agent step, action,
  state, tool call, reasoning hop, and failure point is stored as a graph so
  teams can query reasoning paths, loops, blind spots, and policy failures.
- "Agent Interaction Graphs" is even closer to the eval/debugging shape:
  executions become an interaction graph in Neo4j, evals are attached, and graph
  queries identify critical issues, recurring failure points, and bottlenecks.
- "The AI Agent Memory Landscape" positions memory as the difference between
  stateless demos and production agents, with cognitive memory types and
  implementation patterns across LangGraph, CrewAI, and Pydantic AI.

Neo4j's product surface is also moving in this direction. The Google Cloud agent
release describes a persistent knowledge layer with MCP, GraphRAG agents, an
agent memory API, reasoning memory including agent traces and tool calls, and
decision traces/context graphs. The Neo4j Agent Memory Service goes further: it
offers short-term conversations, long-term entity memory, reasoning traces, and
observations in a graph-native layer backed by Neo4j Aura and vector search. The
MCP reference exposes memory search over messages, entities, preferences, and
traces, with an extended profile that includes reasoning traces, graph export,
and Cypher queries.

The practical interpretation for this repo: Neo4j's current language validates
the graph shape, but it is broader than the slice we should implement. Neo4j is
using context graphs for agent memory and GraphRAG as well as trace/eval
analysis. This repo should keep those concerns separate:

- source evidence graphs remain about domain evidence and reviewer findings;
- context graphs remain about execution evidence, evals, traces, logs, state,
  human review, and failure lineage;
- any Neo4j export should be optional and derived, not the local source of
  record.

Adjacent current signals reinforce that boundary:

- LangChain announced SmithDB as a purpose-built data layer for agent
  observability. Its stated query workloads are trace-tree loads, filtering,
  full-text search, JSON filtering, tree-aware queries, thread reconstruction,
  and aggregations over cost, latency, token usage, and evaluator scores. That
  is a strong signal that trace/eval storage has become its own infrastructure
  problem, not just application logging.
- OpenTelemetry GenAI semantic conventions now explicitly cover GenAI events,
  metrics, model spans, and agent spans, with a stability opt-in path because
  the conventions remain under development. A May 2026 OpenTelemetry post shows
  local GenAI telemetry over LLM calls, tool invocations, tokens, structured
  logs, and privacy-sensitive content capture.
- AgentTelemetry argues that OpenTelemetry GenAI is necessary but incomplete
  for agent observability: planning, reasoning, safety monitoring,
  inter-agent delegation, and memory management need explicit span-level
  representation. Its benchmark frames this as a fault-detection problem, not
  only a trace-format problem.
- Zep/Graphiti are strong references for temporal agent memory and context
  graphs. They model episodes, entities, entity edges, valid-time/provenance,
  and temporal retrieval. This is relevant to state checkpoints and memory
  lineage, but it should not pull this repo's trace/eval context graph into a
  general-purpose user-memory product.

## Expert And Project Map

These are the people and groups most worth tracking for this specific field.
This is not an endorsement list; it is a map of current public work.

Neo4j and graph-memory practitioners:

- Emil Eifrem, Neo4j co-founder and CEO; public Neo4j context-graph speaker.
- Philip Rathle, Neo4j CTO; context-graph and graph-platform speaker.
- William Lyon, Neo4j Senior Product Manager; AI innovation, agent memory, MCP,
  and GraphRAG with Neo4j.
- Vincent Koc, NODES AI speaker on agent interaction graphs and graph-based
  multi-agent evaluation.
- Ashok Vishwakarma, NODES AI speaker on graph evals for tracing agent
  decisions in Neo4j.
- Lasse Andresen, IndyKite founder; context/control layer for governed agents.
- Animesh Koratana, PlayerZero founder; AI production engineering and incident
  reasoning context.

Trace-to-graph and causal-debugging research:

- Zekun Wu, Seonglae Cho, Cristian Enrique Munoz Villalobos, Theo King, Umar
  Mohammed, Emre Kazim, Maria Perez-Ortiz, Sahan Bulathwela, and Adriano
  Koshiyama, the AgentGraph team.
- Zhaohui Geoffrey Wang, author of AgentTrace causal graph tracing for root
  cause analysis in deployed multi-agent systems.
- Adam AlSayyad, Kelvin Yuxiang Huang, and Richik Pal, authors of the
  AgentTrace structured logging framework across operational, cognitive, and
  contextual surfaces.
- The anonymous AgentTelemetry authors, for a current fault-taxonomy benchmark
  around agent-specific span kinds. Names are not public in the reviewed copy,
  so treat the paper as a signal, not a contact map.

Observability, eval, and trace-storage infrastructure:

- James Newton-King at Microsoft/OpenTelemetry, author of the May 2026 GenAI
  observability post and a visible contributor to GenAI telemetry education.
- Ankush Gola and the LangChain/LangSmith team, for SmithDB and
  agent-observability storage/query workloads.
- The Arize Phoenix/OpenInference maintainers, for OpenTelemetry-compatible
  AI span semantics, Phoenix tracing/evaluation workflows, and OpenInference
  conventions.
- Braintrust's observability/evals team, for the production loop that connects
  traces, online scoring, datasets, eval cases, and release enforcement.

Temporal agent-memory graph work:

- Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, and Daniel
  Chalef, authors of the Zep temporal knowledge graph architecture paper.
- Chang Yang, Chuang Zhou, Yilin Xiao, Su Dong, Luyao Zhuang, Yujing Zhang, Zhu
  Wang, Zijin Hong, Zheng Yuan, Zhishang Xiang, Shengyuan Chen, Huachi Zhou,
  Qinggang Zhang, Ninghao Liu, Jinsong Su, Xinrun Wang, Yi Chang, and Xiao
  Huang, authors of the 2026 graph-based agent-memory survey.

## Current Design Implications

The current field is separating into four overlapping layers:

1. Instrumentation standards: OpenTelemetry GenAI, OpenInference, and proposed
   agent-specific span taxonomies.
2. Trace/eval stores: SmithDB, Braintrust, Phoenix, LangSmith, Langfuse, and
   other platforms optimized for large nested traces plus scores.
3. Graph analysis layers: Neo4j interaction graphs, AgentGraph, AgentTrace
   causal graphs, and graph evals that add typed non-tree edges over the trace
   tree.
4. Agent memory/context products: Neo4j Agent Memory, Zep/Graphiti, and MCP
   memory servers that persist conversations, episodes, entities, observations,
   tool calls, and reasoning traces.

For this repo, the next approved implementation should sit in layer 3 while
remaining export-compatible with layers 1 and 2. Layer 4 should be treated as a
future memory product boundary, not a reason to put conversational memory,
domain knowledge, and source facts into the eval/trace graph.

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
- Neo4j NODES AI context graphs:
  <https://neo4j.com/nodes-ai/agenda/keynote-tbd/>
- Neo4j NODES AI graph evals:
  <https://neo4j.com/nodes-ai/agenda/tracing-agent-decisions-with-graph-evals-and-neo4j/>
- Neo4j NODES AI agent interaction graphs:
  <https://neo4j.com/nodes-ai/agenda/agent-interaction-graphs-evaluating-multi-agent-systems-with-graph-based-reasoning/>
- Neo4j NODES AI agent memory landscape:
  <https://neo4j.com/nodes-ai/agenda/the-ai-agent-memory-landscape/>
- Neo4j Google Cloud agent knowledge layer:
  <https://neo4j.com/blog/news/knowledge-layer-agentic-systems-google-cloud/>
- Neo4j Agent Memory Service:
  <https://memory.neo4jlabs.com/>
- Neo4j Agent Memory MCP tools:
  <https://neo4j.com/labs/agent-memory/reference/mcp-tools/>
- LangChain SmithDB:
  <https://www.langchain.com/blog/introducing-smithdb>
- OpenTelemetry GenAI semantic conventions:
  <https://opentelemetry.io/docs/specs/semconv/gen-ai/>
- OpenTelemetry GenAI observability post:
  <https://opentelemetry.io/blog/2026/genai-observability/>
- AgentTelemetry benchmark:
  <https://openreview.net/pdf?id=owdmAYFk6k>
- Zep Context Graph and Graphiti docs:
  <https://help.getzep.com/overview> and
  <https://help.getzep.com/v2/understanding-the-graph>
- Zep temporal knowledge graph architecture:
  <https://arxiv.org/abs/2501.13956>
- Graph-based agent memory survey:
  <https://arxiv.org/abs/2602.05665>
