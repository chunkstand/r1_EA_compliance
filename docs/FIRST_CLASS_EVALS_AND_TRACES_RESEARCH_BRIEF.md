# First-Class Evals And Traces Research Brief

Date: 2026-05-28

Status: Research addendum. This is not an active route change and does not
supersede `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, or
`docs/SESSION_HANDOFF.md`.

## Purpose

This brief validates the 2026-05-28 first-class evals and traces proposal
against current external evaluation practice and adapts it to this repository.
The target is the local Region 1 EA reviewer-engine, not a hosted observability
platform and not the separate `docling-system` application.

The conclusion is direct: the proposed direction is right, but this repo should
begin with a read-only inventory and contract milestone over existing
artifact-backed evals and traces. Schema migrations or hosted telemetry export
should come later, after the inventory proves that current eval artifacts,
retrieval traces, replay contexts, review outputs, and promotion gates have
stable cross-links.

## External Research Check

Current eval practice converges on a durable loop:

1. Capture traces for real workflow executions.
2. Inspect traces and label failures.
3. Promote representative traces into versioned datasets.
4. Run offline evals on candidate workflow, prompt, profile, model, or tool
   changes.
5. Score live traces online or asynchronously.
6. Feed failures, labels, and drift back into the dataset.

Braintrust describes this as an Instrument, Observe, Annotate, Evaluate, Deploy
cycle, with offline experiments, CI/CD evals, online scoring, and production
trace feedback forming one loop. It also emphasizes that agent workflows need
both whole-task and per-step evaluation.

OpenAI's current eval surfaces support the same split: trace grading is useful
while debugging agent behavior, then datasets and eval runs become the repeatable
comparison surface once the team knows what "good" means. OpenAI evals are built
around test data and testing criteria/graders.

Anthropic's January 2026 agent-evals guidance adds two important constraints:
record the full transcript/trace for each trial, and evaluate stochastic agents
with repeated trials. Use pass@k when one successful attempt is sufficient; use
pass^k when reliability across every attempt matters.

OpenTelemetry GenAI semantic conventions and OpenInference make the export shape
clear. OpenTelemetry provides GenAI span attributes for operations such as
retrieval and retrieved documents. OpenInference adds AI-specific span kinds
including `LLM`, `AGENT`, `CHAIN`, `TOOL`, `RETRIEVER`, `RERANKER`,
`EMBEDDING`, `GUARDRAIL`, and `EVALUATOR`. This repo should store canonical
local rows first, but use names that can export to OTLP/OpenInference without
semantic loss.

RAG eval guidance is consistent across Ragas and TruLens: split retrieval
quality from generation quality. Track context precision/recall or relevance,
groundedness/faithfulness, answer relevance, and answer correctness separately
instead of hiding them behind one end-to-end score.

DeepEval's agent tracing guidance reinforces the same component split: attach
task-completion and step-efficiency metrics at the agent/root level, and
tool-correctness and argument-correctness metrics at the LLM/tool span level.
That pattern maps well to future agent-task or semantic-generation lanes in
this repo.

Practitioner guidance from Hamel Husain is especially relevant operationally:
start with scoped deterministic assertions, make traces easy to inspect and
label, calibrate model judges against humans, and track judge precision/recall
instead of trusting raw agreement.

## Repo Fit

This repo already has many eval pieces, but they are not yet first-class as a
single system:

- deterministic eval commands and manifests such as `phase-eval`, `v1-ea-eval`,
  `retrieval-eval`, `compliance-review-eval`, `forest-plan-component-eval`,
  `forest-plan-profile-eval`, `real-package-review-coverage-eval`,
  `gold-coverage-eval`, and `project-sow-eval`;
- replay contexts in `config/replay_contexts/`;
- catalog and retrieval SQLite surfaces such as `review_sources.sqlite` and
  `evidence_index.sqlite`;
- applicability retrieval and graph traces under
  `source_library/reviews/<review_id>/applicability/`;
- review-scoped artifacts with hashes, source-set IDs, rule-pack links,
  citations, and validation sidecars;
- `docs/EVALUATION_COVERAGE_REGISTER.md`, which separates structural validation
  from direct-eval coverage.

The missing layer is not another domain-specific eval command. It is an
inventory and linking substrate that can answer:

- which evals exist for this source set or review;
- which traces, replay contexts, catalog surfaces, source rows, artifacts,
  claims, findings, and reports they used;
- which scorer/threshold contract version produced each pass or failure;
- which gates would block profile, graph, memory, report, or example-package
  promotion;
- whether the result is exportable to a portable trace/eval shape.

## Repo-Specific Adjustments

Do not copy command names or table ownership from `docling-system`. For this
repository, the first public command should be an eval-family CLI such as
`eval-trace-inventory`, not `docling-system-eval-trace-inventory`.

Do not start by wiring Braintrust, LangSmith, Phoenix, or another hosted tool.
Those are useful inspection and export targets, but they should not be the
system of record.

Do not start with migrations. This repo currently stores much of its durable
state as generated JSON/JSONL plus local SQLite artifact databases under
`source_library/`. First prove linkability with a read-only inventory report.
Only then add a DB-backed generic eval/trace store.

Do not weaken deterministic gates in favor of LLM judges. Model judges should be
reserved for cases that cannot be scored through schema, hash, citation,
retrieval, source-record, rule, graph, or artifact checks.

## Candidate Contract

The eventual generic model should be compatible with the proposed objects:

- `system_eval_runs`
- `system_eval_cases`
- `system_eval_case_results`
- `system_eval_scores`
- `trace_runs`
- `trace_spans`

For this repo, those objects should link to these local entities before they add
new semantics:

- workbook row and source record ID;
- source-set ID and catalog directory;
- run ID and artifact hash;
- review ID and replay context;
- extraction, retrieval, evidence-graph, claim, rule-claim, applicability,
  compliance, decision-support, final-QA, packet-index, and phase-eval
  artifacts;
- config manifest path and hash;
- eval command, scorer/threshold version, and result artifact;
- trace file path and row IDs for applicability retrieval/graph traces;
- promotion or report gate that consumed the eval.

Span kinds should use local names that map cleanly to OpenTelemetry and
OpenInference:

| Local span kind | Export mapping |
| --- | --- |
| `workflow` | OpenInference `CHAIN` or `AGENT`, depending on control flow |
| `retrieve` | OTel `gen_ai.operation.name=retrieval`; OpenInference `RETRIEVER` |
| `rerank` | OpenInference `RERANKER` |
| `embed` | OTel embeddings operation; OpenInference `EMBEDDING` |
| `tool` | OTel tool execution; OpenInference `TOOL` |
| `llm` | OpenInference `LLM` |
| `evaluation` or `score` | OpenInference `EVALUATOR` |
| `guardrail` | OpenInference `GUARDRAIL` |
| `artifact` | local span with artifact hash/path attributes |

## Recommended First Slice

Create a contract and read-only inventory milestone:

1. Add `docs/first_class_eval_trace_contract.md`.
2. Add `eval-trace-inventory` as a read-only CLI command.
3. The command should report existing coverage for:
   - direct eval manifests and result artifacts;
   - phase eval source-set and review-scoped outputs;
   - replay contexts and catalog/retrieval SQLite surfaces;
   - applicability retrieval and graph trace files;
   - V1, component, gold, real-package, promotion, decision-support,
     packet-index, and final-QA gate artifacts;
   - missing cross-links required before generic eval/trace rows can be
     created.
4. Add unit tests for the inventory JSON schema and negative cases.
5. Update `docs/EVALUATION_COVERAGE_REGISTER.md` only after the inventory
   command exists and can report real surfaces.

Stop if the inventory shows that current eval artifacts cannot be linked without
broad artifact-schema changes. That should become a separate migration plan.

## Stop Conditions

- The work would require rerunning large downloader, extraction, review, or
  network workflows.
- The inventory would need to mutate `source_library/`.
- Existing deterministic eval gates would be weakened or replaced by an
  uncalibrated model judge.
- A generic table would require changing multiple domain artifact schemas before
  the inventory proves linkability.
- Active West Reservoir packet closeout would be mixed into this research or
  contract slice.

## Source Notes

- Braintrust workflow: <https://www.braintrust.dev/docs/workflow>
- Braintrust systematic evaluation: <https://www.braintrust.dev/docs/evaluate>
- Braintrust evaluating agents: <https://www.braintrust.dev/docs/best-practices/agents>
- OpenTelemetry GenAI spans:
  <https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/>
- OpenInference specification: <https://arize-ai.github.io/openinference/spec/>
- Phoenix overview: <https://arize.com/docs/phoenix>
- LangSmith evaluation: <https://docs.langchain.com/langsmith/evaluation>
- OpenAI evals: <https://platform.openai.com/docs/guides/evals>
- OpenAI agent evals:
  <https://platform.openai.com/docs/guides/agent-evals>
- OpenAI trace grading:
  <https://platform.openai.com/docs/guides/trace-grading>
- Anthropic agent evals:
  <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>
- Ragas metrics:
  <https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/>
- TruLens RAG triad:
  <https://www.trulens.org/getting_started/core_concepts/rag_triad/>
- DeepEval agent tracing:
  <https://deepeval.com/guides/guides-tracing-ai-agents>
- Hamel Husain, Your AI Product Needs Evals:
  <https://hamel.dev/blog/posts/evals/>
