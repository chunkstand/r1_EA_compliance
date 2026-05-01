# Forest Plan Component Evaluation Milestone Plan

Date: 2026-05-01

## Outcome

This plan turns the current forest-plan context resolver into a component-level evaluator for the V1
East Crazies demo review. The evaluator must identify the applicable Custer Gallatin Land Management
Plan components, compare the EA package against those components, and emit citation-bearing findings
and reviewer-resolution items.

The output is a reviewer aid, not a legal sufficiency determination.

## Research-Grounded Design

The implementation should follow these design constraints from current RAG, legal-document, and
provenance research:

- **Structured authority layer before generation.** LegalDocML/Akoma Ntoso shows the value of
  machine-readable legal/normative document structure: hierarchy, metadata, references, and stable
  portions. We should borrow that model lightly rather than inventing a full legal XML stack.
- **Precise retrieval over broad chunks.** LegalBench-RAG emphasizes minimal, highly relevant text
  segments instead of whole documents or large generic chunks. Component findings should cite exact
  snippets with offsets and source IDs.
- **Retrieval quality sets the ceiling.** Recent legal RAG benchmarks show many apparent
  hallucinations start as retrieval failures. The forest-plan evaluator should invest in component
  inventory, retrieval validation, and evidence coverage before adding more generation.
- **Modular RAG, not one opaque prompt.** Current RAG surveys frame strong systems as modular:
  indexing, retrieval, augmentation, generation/reporting, and evaluation are distinct stages with
  separate metrics.
- **Graph relationships for multi-hop context.** GraphRAG/DRIFT-style systems are useful for
  connecting local evidence to broader context. Here, graph links should connect forest units,
  plan components, management areas, overlays, EA evidence, supporting records, and findings.
- **First-class provenance.** W3C PROV maps directly to this system: source artifacts and component
  records are entities, extraction/index/evaluation runs are activities, and code/config versions are
  agents. Every finding must preserve this chain.
- **Evaluation checks retrieval and groundedness separately.** Use RAG-triad-style gates:
  context relevance, groundedness, and answer/report relevance. Do not accept a good-looking report
  unless evidence retrieval and citation support pass independently.
- **Risk management and auditability.** NIST GenAI guidance reinforces traceability, measurement,
  risk controls, and transparency for consequential AI-assisted workflows.

Key sources:

- Akoma Ntoso / LegalDocML: https://docs.oasis-open.org/legaldocml/akn-core/v1.0/akn-core-v1.0-part1-vocabulary.html
- LegalBench-RAG: https://huggingface.co/papers/2408.10343
- Legal RAG survey: https://doi.org/10.1109/access.2025.3550145
- Legal RAG Bench: https://huggingface.co/papers/2603.01710
- Microsoft GraphRAG DRIFT: https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/
- W3C PROV primer: https://www.w3.org/TR/prov-primer/
- RAG triad: https://www.trulens.org/getting_started/core_concepts/rag_triad/
- NIST GenAI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

## Current Baseline

Already implemented:

- `forest-plan-resolve` selects the Custer Gallatin profile through profile data.
- The resolver checks all seven required Custer Gallatin plan/supporting source records.
- The East Crazies fixture resolves Custer Gallatin scope, Bridger/Bangtail/Crazy Mountains
  Geographic Area, and Crazy Mountains Backcountry Area.
- FEIS, Biological Assessment, and Biological Opinion support routes require explicit package
  evidence and source-library evidence.
- Generic project decision labels and generic `plan consistency` labels no longer trigger Custer
  Gallatin ROD or FEIS routes by themselves.

Missing:

- No structured forest-plan component inventory exists yet.
- No precise component-snippet retrieval layer exists.
- No graph links connect components to context, package evidence, and findings.
- No finding layer compares EA package evidence to each applicable plan component.
- No stable output schema or eval gate exists for forest-plan component findings.

## Non-Goals

- Do not hardcode East Crazies-specific runtime branches.
- Do not claim legal sufficiency or final plan consistency.
- Do not require a full 190-row downstream corpus rebuild unless source evidence requires it.
- Do not use raw artifact filenames to decide applicability.
- Do not rely on an LLM or prose report as the source of truth for findings.

## Target Storage Shape

```text
source_library/
  artifacts/raw/
  catalog/source_catalog.jsonl
  catalog/review_sources.sqlite
  derived/<source_set_id>/
    chunks/chunks.jsonl
    retrieval/evidence_index.sqlite
    forest_plan_components/
      components.jsonl
      components.sqlite
      component_graph_nodes.jsonl
      component_graph_edges.jsonl
      component_validation.json
      component_retrieval_eval.json
  reviews/<review_id>/
    forest_plan_context.json
    forest_plan_context_validation.json
    forest_plan_component_findings.json
    forest_plan_component_findings.md
    forest_plan_reviewer_resolution_queue.json
```

## Milestone 1: Data Model, Provenance, And Output Contract

Goal:
Define the component, finding, queue, and provenance contracts before building extraction logic.

Deliverables:

- `ForestPlanComponent` schema:
  - `component_id`
  - `forest_unit_id`
  - `plan_version`
  - `source_set_id`
  - `source_record_id`
  - `component_type`
  - `section_id`
  - `section_heading`
  - `page`
  - `citation_label`
  - `component_text`
  - `geographic_area_ids`
  - `management_area_ids`
  - `overlay_ids`
  - `resource_topics`
  - `activity_tags`
  - `source_chunk_ids`
  - `artifact_sha256`
  - `content_sha256`
  - `provenance`
- `ForestPlanComponentFinding` schema:
  - `finding_id`
  - `component_id`
  - `applicability_status`
  - `finding_status`
  - `applicability_basis`
  - `plan_source_evidence`
  - `package_evidence`
  - `rationale`
  - `reviewer_resolution_items`
  - `provenance`
- `forest_plan_reviewer_resolution_queue.json` schema.
- Docs in `docs/OUTPUT_SCHEMAS.md` and current-state notes.

Research alignment:

- W3C PROV-style entity/activity/agent fields are part of the schema.
- Finding status is machine-readable; prose never becomes the only status surface.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- A finding can omit source-record IDs, source chunks, or provenance.
- Readiness requires parsing Markdown prose.

## Milestone 2: Structured Component Inventory

Goal:
Create a versioned Custer Gallatin component inventory for the East Crazies-relevant plan sections.

Deliverables:

- Rebuildable component artifact under
  `source_library/derived/<source_set_id>/forest_plan_components/`.
- `components.jsonl` and `components.sqlite` with one record per reviewable plan component.
- Initial scope focused on components relevant to:
  - Bridger/Bangtail/Crazy Mountains Geographic Area
  - Crazy Mountains Backcountry Area
  - designated areas and allocations
  - resources surfaced by the East Crazies package
- Validation that each component points to current source chunks and source-record IDs.
- Fixture inventory for tests, plus real-inventory validation when local derived artifacts exist.

Research alignment:

- Akoma Ntoso informs the hierarchy and citation model, but the repo stores a pragmatic JSONL/SQLite
  inventory rather than a full XML legal-document implementation.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
git diff --check
```

Stop conditions:

- Component records collapse multiple standards/guidelines/objectives into one broad topic.
- Component records cannot be traced to exact source text.
- The inventory stores conclusions about East Crazies rather than plan authority components.

## Milestone 3: Precise Component Retrieval

Goal:
Retrieve exact component-level snippets and prove retrieval quality before using them in findings.

Deliverables:

- Component-aware retrieval queries and filters over `components.sqlite` and the existing evidence
  index.
- Retrieval output that returns minimal relevant snippets with source-record IDs, source chunk IDs,
  offsets, citation labels, and component IDs.
- `component_retrieval_eval.json` with precision/recall-oriented checks for fixture queries.
- Negative retrieval cases proving broad terms such as `Forest Plan` and `plan consistency` do not
  retrieve unrelated plan components as applicable evidence.

Research alignment:

- LegalBench-RAG-style exact snippet retrieval is the acceptance target.
- Retrieval validation is separate from final report validation.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_retrieval.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Retrieval only returns document-level or large chunk-level evidence.
- Component retrieval is not measurable independently from finding generation.

## Milestone 4: Applicability Graph And Selection

Goal:
Select applicable components using resolved package context plus component metadata and graph links.

Deliverables:

- Component graph nodes and edges for:
  - forest unit
  - plan component
  - geographic area
  - management area
  - overlay
  - source record
  - package evidence
  - finding
- Applicability statuses:
  - `applicable`
  - `candidate`
  - `not_applicable`
  - `needs_reviewer_resolution`
- Selection logic using:
  - Custer Gallatin scope
  - Bridger/Bangtail/Crazy Mountains Geographic Area
  - Crazy Mountains Backcountry Area
  - overlays and designated areas
  - resource and activity evidence from the EA package
- Negative tests proving the evaluator does not mark all Custer Gallatin components applicable just
  because the package is on the forest.

Research alignment:

- GraphRAG/DRIFT informs the use of graph context for multi-hop relationships, but deterministic
  component metadata and evidence gates remain authoritative.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Applicability is inferred from broad package language alone.
- Graph links become decorative and are not used by validation or findings.

## Milestone 5: Evidence-Backed Component Findings

Goal:
Compare EA package evidence against each applicable component and emit findings.

Deliverables:

- Finding statuses:
  - `supported`
  - `partial`
  - `gap`
  - `not_applicable`
  - `needs_reviewer_resolution`
- Evidence matching that links package chunks to component requirements.
- Validation that `supported` and `partial` require both package evidence and forest-plan source
  evidence.
- Validation that a component remains a `gap` when plan evidence exists but package evidence is
  missing.
- Reviewer-resolution items for missing, weak, ambiguous, or contradictory package evidence.

Research alignment:

- RAG-triad groundedness is enforced at finding level: each finding must be grounded in retrieved
  context and package evidence.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- A finding can be `supported` without dual evidence.
- The evaluator presents legal sufficiency conclusions instead of evidence-backed reviewer signals.

## Milestone 6: Evaluation Gates

Goal:
Add eval gates that measure the forest-plan evaluator before the real demo run.

Deliverables:

- Fixture-level eval cases for:
  - relevant component retrieval
  - irrelevant component rejection
  - applicability classification
  - grounded component findings
  - reviewer-resolution queue generation
- Metrics grouped by:
  - retrieval relevance
  - groundedness
  - report/finding relevance
  - provenance completeness
- Fail-closed behavior when source-set IDs, component IDs, source chunks, or citations drift.

Research alignment:

- RAG surveys and RAG-triad practice separate retrieval quality from generated/report quality.
- NIST-style risk controls are represented as explicit validation gates and residual-risk outputs.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- The eval only checks file existence or happy-path output shape.
- Retrieval failures are hidden inside final report failures.

## Milestone 7: Component Outputs And Human Review Report

Goal:
Make component evaluation outputs usable in the V1 demo review.

Deliverables:

- Write these artifacts under `source_library/reviews/<review_id>/`:
  - `forest_plan_component_findings.json`
  - `forest_plan_component_findings.md`
  - `forest_plan_reviewer_resolution_queue.json`
- Add summary fields to `forest_plan_context_summary.json`:
  - component count
  - applicable count
  - supported count
  - partial count
  - gap count
  - reviewer-resolution count
  - provenance-complete count
- Human-readable report sections for:
  - applicable plan components
  - EA-supported points
  - gaps needing reviewer work
  - not-applicable components
  - residual risk

Research alignment:

- Report text is generated from structured findings, not the other way around.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Markdown is more complete than JSON.
- The report obscures unresolved or unsupported components.

## Milestone 8: Real East Crazies Package Run

Goal:
Run the improved evaluator against the actual local East Crazies package and decide whether the
forest-plan component evaluation is strong enough for the V1 demo review.

Target package:

```text
source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)
```

Required run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-demo-ecid-forest-plan
```

Deliverables:

- Verified forest-plan context outputs.
- Verified component findings outputs.
- Verified reviewer-resolution queue.
- Current-state doc update with review ID, source set, profile ID, pass/fail status, and residual
  risk.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Add `phase-eval` only if the V1 demo claims broader phase-level or compliance-promotion readiness.

Stop conditions:

- The real package produces many unresolved components that make the demo misleading.
- Generated findings depend on stale source-set IDs.
- The package cannot be reproduced from documented commands and committed config/code.

## Milestone 9: V1 Demo Integration

Goal:
Use forest-plan component evaluation as one input to the V1 demo document review.

Deliverables:

- V1 demo review report section summarizing forest-plan component findings.
- Clear distinction between forest-plan component evaluation, EA checklist review, and any
  compliance-review matrix.
- Handoff that states whether the V1 demo should stop at `forest-plan-resolve` plus `ea-review`, or
  continue into `compliance-review`.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Run generated-artifact checks only for the selected demo path.

Stop conditions:

- The demo report blurs evidence-backed findings with final legal conclusions.
- The forest-plan evaluation is not traceable to source-record IDs, package evidence, plan component
  evidence, and provenance.

## Milestone Discipline

- Keep one milestone per commit.
- Stage only the verified milestone slice.
- Prefer narrow fixtures and current source-set reuse over broad corpus rebuilds.
- Treat every unsupported, ambiguous, or missing plan-component result as reviewer work, not as a
  hidden pass.
- Update `docs/SESSION_HANDOFF.md` after substantial implementation work.
