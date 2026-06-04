# System Evaluation Best-In-Class Research Brief

Date: 2026-06-04
Status: Research addendum
Owner context: supports `docs/FIRST_CLASS_SYSTEM_EVALUATION_IMPROVEMENT_MILESTONE_PLAN.md`.

This brief summarizes current evaluation practice for agent systems, RAG systems, graph systems,
and observability platforms, then maps the useful parts to the local USFS R1 EA reviewer-engine.
It does not supersede the milestone plan, current routing, current state, or the local
eval-trace/observability contracts.

## Executive Takeaways

Best-in-class evaluation systems are no longer just final-answer scorecards. The common production
loop is:

1. capture traces, spans, artifacts, scores, labels, and runtime metadata;
2. promote selected traces and failures into datasets or durable cases;
3. replay the same cases across versions of prompts, tools, retrieval, graph construction, and
   workflow code;
4. score both final outputs and intermediate trajectory steps;
5. calibrate automated scorers against human labels before they can block release; and
6. use scoped CI, phase, or promotion gates to prevent regressions.

The repo already has a strong local substrate for this pattern: deterministic direct evals,
phase-eval gates, a first-class eval-trace SQLite store, OpenInference-shaped export, trace-to-case
promotion, and a local observability/eval context graph. The next improvement should not be a
hosted evaluator migration. It should be a deeper local eval contract that makes every pipeline
boundary measurable and starts with applicability, as the milestone plan already says.

The best external pattern to copy from Braintrust, Phoenix, LangSmith, Langfuse, MLflow, and OpenAI
is not their UI. It is the flywheel: traces -> datasets/cases -> experiments -> online/offline
scores -> human calibration -> regression gates -> failure intake.

## Current External Patterns

### Braintrust-style flywheel

Braintrust's current eval docs organize evaluation around datasets, tasks, and scorers, with a
workflow that moves from playground iteration to immutable experiments, CI/CD regression checks,
production online scoring, and feeding production traces back into datasets. Braintrust's 2026
agent-evaluation article explicitly separates agent evaluation from single prompt-response evals:
agents need layered metrics for reasoning, tool selection, action execution, and final outcomes.

Repo implication: keep local deterministic scorers as the first gate, but add a Braintrust-like
closed loop for applicability failures. Any failed applicability trace should be promotable to a
tracked case with source-set, review, source-record, citation, artifact hash, trace hash, scorer,
owner, risk, assertion, review condition, and removal condition.

### Phoenix and OpenInference pattern

Phoenix is built on OpenTelemetry and OpenInference, accepts traces over OTLP, and scores traces or
spans with LLM-based evaluators, code checks, and human labels. OpenInference standardizes span
kinds such as `LLM`, `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `GUARDRAIL`, `EVALUATOR`, and
`PROMPT`.

Repo implication: preserve the current local source of record, but continue mapping exported spans
to OpenInference kinds. Applicability and graph evals should add `RETRIEVER`, `RERANKER`,
`EVALUATOR`, `TOOL`, and `AGENT`-equivalent span metadata where the local store can represent it
without exposing raw source text or prompts.

### LangSmith, Langfuse, and MLflow pattern

LangSmith emphasizes multiple evaluator types: human annotation queues, heuristic checks,
LLM-as-judge, pairwise comparison, and custom evaluators. It also recommends sampling production
traces into datasets when no labeled dataset exists. Langfuse similarly supports online evaluation
with LLM-as-judge, code evaluators, and human annotation, and it distinguishes trace-level from
observation-level evaluators. MLflow's GenAI dataset docs describe building evaluation datasets
from existing traces and adding expectations before replay.

Repo implication: add explicit "case source" and "label status" metadata to future eval rows. A
case should say whether it came from a tracked fixture, generated mutation, live trace failure,
human adjudication, or production-like replay. Observation-level scoring maps well to this repo's
individual pipeline artifacts: retrieval trace row, graph trace row, applicability decision row,
generated rule row, compliance finding row, matrix row, and phase-eval phase row.

### OpenAI trace grading and agent evals

OpenAI's current agent evaluation surface centers on traces, graders, datasets, and eval runs. Its
trace grading docs frame a trace as the end-to-end log of decisions, tool calls, and reasoning
steps; trace evals then score many examples to benchmark changes and find regressions. The Agents
SDK tracing docs also call out sensitive-data capture controls.

Repo implication: use trace grading as a concept, not as the source-of-record platform. The local
equivalent should grade applicability and review traces by structured criteria, then retain only
safe source refs, hashes, candidate IDs, decision IDs, score summaries, and redacted payload hashes
in the eval/observability graph.

### RAG and GraphRAG evaluation pattern

RAGAS exposes RAG metrics such as context precision, context recall, context entity recall, noise
sensitivity, response relevancy, and faithfulness, plus agent/tool metrics such as tool-call
accuracy and agent-goal accuracy. RAGChecker argues for fine-grained diagnostics across retrieval
and generation rather than a single aggregate score. Recent GraphRAG work stresses that GraphRAG
must be evaluated across graph construction, knowledge retrieval, and answer generation, and the
2026 version of "RAG vs. GraphRAG" emphasizes unified evaluation protocols, failure modes,
efficiency tradeoffs, and evaluation biases. Microsoft GraphRAG's query model also separates local
entity-focused search, global community-report search, DRIFT search, and basic search.

Repo implication: graph evaluations should be split into intrinsic graph quality and extrinsic
reviewer-task quality:

- intrinsic graph construction: node/edge typing, entity/relation extraction precision and recall,
  citation/provenance edge coverage, alias resolution, currentness metadata, component inventory
  binding, and graph health;
- graph retrieval: path recall, path precision, multi-hop support, neighborhood relevance,
  citation-bearing evidence support, no-evidence certificates, freshness warnings, and query-type
  coverage;
- downstream generation/review: generated rule-pack fidelity, compliance finding support,
  matrix row support, decision-support support, and reviewer-ready gate consistency.

### Agent benchmark pattern

AgentBench evaluates agents in interactive environments rather than only static prompts. GAIA tests
real-world assistant tasks that require reasoning, multimodal handling, browsing, and tool use.
tau-bench adds simulated user interaction, domain tools, policy guidelines, database-state scoring,
and `pass^k` reliability over repeated trials. AgentProcessBench, updated in June 2026, adds
human-labeled step-level annotations for realistic tool trajectories. AlphaEval, published in April
2026, argues for production-grounded benchmarks that evaluate complete agent products, not just
models, using mixed scoring paradigms such as LLM-as-judge, reference checks, formal verification,
rubrics, and UI tests.

Repo implication: applicability and review evals should measure both outcome and process. A review
can reach the right final status while using weak evidence, skipping a required source family,
opening the wrong Forest Plan branch, or generating rules from the wrong partition. Process
metrics should include selected-source correctness, trace path support, decision step validity,
tool/command sequence validity, no-evidence handling, retry/loop behavior, latency, and repeated
run reliability when stochastic steps are present.

## Best-In-Class Evaluation Stack For This Repo

The local target should be a seven-layer evaluation stack.

### 1. Identity and provenance layer

Every eval row, score, case, trace, graph node, and promoted failure must preserve:

- source-set ID;
- review ID when applicable;
- workbook/source-record ID when available;
- citation label or source artifact ref when available;
- artifact path and content hash;
- trace/span/run IDs;
- scorer contract ID, scorer version, thresholds, and config hash;
- case source and label status;
- local source-of-record and redaction policy.

This is already partly implemented by the first-class eval-trace contract. The next work is to
ensure applicability and all-step eval summaries emit enough fields for this substrate.

### 2. Structural validation layer

Structural validation should keep failing fast on schema, required fields, identity mismatch, stale
hashes, missing artifacts, malformed summaries, unsupported enum values, orphaned rows, and missing
links. These are not quality metrics; they are admission controls.

Implementation examples:

- add typed applicability eval summary schema fields;
- require source-set/review identity in applicability summaries;
- fail when a generated rule pack references decisions from another review;
- fail when a gate graph was built against a stale authority-universe or contract hash.

### 3. Direct-eval quality layer

Each pipeline step needs task-specific metrics. For applicability, the first critical lane should
track at least:

- authority-universe coverage: expected candidate families, selected forest component inventory
  coverage, source-record coverage, hard-negative exclusion rate;
- retrieval trace quality: recall@k, MRR/nDCG where ranked, context precision, missing-required
  source guard, no-evidence certificate quality;
- graph trace quality: path recall, path precision, graph-path provenance, multi-hop support,
  freshness warning detection;
- decision partition fidelity: applicable/not-applicable/unresolved/adjudication-needed confusion
  matrix, per-family floors, hard-negative false-positive rate;
- generated rule-pack fidelity: generated rule precision/recall against the applicable partition,
  missing expected rules, unexpected rules, source-claim link coverage;
- gate-graph consistency: parent/child open-closed-blocked consistency, Forest Plan subgate
  behavior, NFMA branch propagation, contradiction detection;
- failure intake: promoted-case replayability, lifecycle metadata completeness, owner and removal
  condition presence.

### 4. Trajectory and process layer

Borrow from trace grading, tau-bench, and AgentProcessBench: score the path, not only the result.
For this repo, "trajectory" is the sequence of local commands, generated artifacts, selected
sources, trace rows, graph paths, applicability decisions, rule-generation steps, compliance
findings, and phase-eval phases.

Useful metrics:

- required-step presence and order;
- invalid transition count;
- tool/command success and failure class;
- retry without new evidence count;
- no-evidence decision correctness;
- stale artifact avoidance;
- decision drift from prior accepted case;
- step-level label: correct, neutral/exploratory, or erroneous;
- first bad step and error propagation class.

### 5. Graph evaluation layer

Keep two graph families separate:

- source knowledge graphs: domain/source facts, authority relationships, citations, component
  inventories, source claims, rule claims, package facts;
- observability/eval context graphs: traces, spans, scores, cases, artifacts, command events,
  failures, labels, review state, and replay lineage.

Best-in-class graph evals should check:

- required node and edge kinds;
- edge resolution;
- source provenance on every source-backed node or edge;
- alias/citation collision controls;
- graph currentness metadata;
- path support for each generated decision or finding;
- graph query surface hard negatives;
- graph retrieval coverage by query type;
- failure recurrence neighborhoods in the context graph;
- trace-to-result-to-score-to-case paths.

### 6. Human label and scorer calibration layer

LLM judges should remain reserved until there are human-labeled examples and calibration results.
When introduced, each judge must record judge model, prompt hash, rubric hash, example set hash,
temperature, output schema, agreement with human labels, disagreement queue, and scorer drift
checks.

Near-term deterministic/human path:

- add adjudication labels for selected applicability failures;
- store labeler, label status, rationale summary, reviewed timestamp, and removal condition;
- compare any future model judge against those labels before using it in a gate;
- treat disagreement as a failure-intake source, not as an automatic pass.

### 7. Scoped gate and improvement layer

Use ratchets only when the scope is explicit and replayable. A good first applicability ratchet is
one governed review/source-set with full source-set/review identity and no wildcard scope.

Gate levels:

- local focused test gate;
- direct-eval summary gate;
- eval-trace inventory/store/export gate;
- context-graph eval gate;
- phase-eval scoped ratchet;
- promotion-suite ratchet only after the phase-eval ratchet is stable.

## Recommended Implementation For Milestone 0 And Milestone 1

Milestone 0 should update the coverage register without changing runtime behavior. Add or confirm
rows for every pipeline stage with these fields:

- stage/subsystem;
- structural owner;
- direct-eval owner or explicit gap status;
- eval unit;
- metrics;
- hard-negative coverage;
- human-label/adjudication status;
- trace/case promotion route;
- phase or promotion gate status;
- widening stop condition.

For applicability sub-rows, use the metric groups in this brief:

- authority universe;
- retrieval trace;
- graph trace;
- decision partition;
- generated rule pack;
- gate graph;
- Forest Plan subgate;
- failure intake;
- trajectory/process.

Milestone 1 should add or extend an applicability summary artifact that can be indexed by
eval-trace inventory and consumed by phase-eval. It should not require hosted scoring or model
judges. The summary should include:

- `schema_version`;
- `source_set_id`;
- `review_id`;
- `contract_id`;
- `contract_hash`;
- `scorer_version`;
- `source_artifact_refs`;
- `source_artifact_hashes`;
- `metric_groups`;
- `case_results`;
- `hard_negative_results`;
- `per_family_scores`;
- `trace_quality_scores`;
- `graph_path_scores`;
- `rule_pack_fidelity_scores`;
- `gate_graph_consistency_scores`;
- `failure_intake_candidates`;
- `passed`;
- `blocking_failures`.

## What Not To Do Yet

- Do not make Braintrust, Phoenix, LangSmith, Langfuse, MLflow, OpenAI, or any hosted platform the
  source of record for this repo's gates.
- Do not add LLM-as-judge scoring as a blocking gate until deterministic and human-label contracts
  are present.
- Do not collapse source knowledge graph facts into the observability/eval context graph.
- Do not use aggregate green counts as proof when per-family applicability, hard negatives, graph
  path support, or generated-rule fidelity can regress silently.
- Do not add global phase-eval ratchets or wildcard source-set/review scopes.

## Source Links

- Braintrust, "Evaluate systematically": https://www.braintrust.dev/docs/evaluate
- Braintrust, "AI agent evaluation: A practical framework for testing multi-step agents":
  https://www.braintrust.dev/articles/ai-agent-evaluation-framework
- Arize Phoenix docs: https://arize.com/docs/phoenix
- OpenInference semantic conventions: https://arize-ai.github.io/openinference/spec/semantic_conventions.html
- OpenTelemetry GenAI semantic conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- LangSmith evaluation page: https://www.langchain.com/langsmith/evaluation
- Langfuse evaluation concepts: https://langfuse.com/docs/evaluation/core-concepts
- MLflow GenAI evaluation datasets: https://mlflow.org/docs/latest/genai/datasets/
- MLflow judges and scorers: https://mlflow.github.io/mlflow-website/docs/latest/genai/eval-monitor/scorers/
- OpenAI agent evals: https://developers.openai.com/api/docs/guides/agent-evals
- OpenAI trace grading: https://developers.openai.com/api/docs/guides/trace-grading
- RAGAS available metrics: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/
- RAGChecker, NeurIPS 2024: https://papers.nips.cc/paper_files/paper/2024/hash/27245589131d17368cccdfa990cbf16e-Abstract-Datasets_and_Benchmarks_Track.html
- Microsoft GraphRAG docs: https://microsoft.github.io/graphrag/
- Microsoft BenchmarkQED: https://microsoft.github.io/benchmark-qed/
- RAG vs. GraphRAG systematic evaluation: https://arxiv.org/abs/2502.11371
- Knowledge-Graph Based RAG System Evaluation Framework: https://arxiv.org/abs/2510.02549
- GraphRAG-Bench repository: https://github.com/GraphRAG-Bench/GraphRAG-Benchmark
- AgentBench: https://arxiv.org/abs/2308.03688
- GAIA: https://arxiv.org/abs/2311.12983
- tau-bench: https://arxiv.org/abs/2406.12045
- AgentProcessBench: https://arxiv.org/abs/2603.14465
- AlphaEval: https://arxiv.org/abs/2604.12162
