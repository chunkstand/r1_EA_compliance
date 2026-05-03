# Forest Plan Component Evaluation And NFMA Compliance Milestone Plan

Date: 2026-05-01

## Outcome

This plan turns the current forest-plan context resolver into a mandatory NFMA Forest Plan compliance
review path for EA packages. For any package resolved to the selected forest-plan profile, the system
must identify the governing plan, verify current source-library evidence, determine every applicable
plan component, apply every applicable standard to the EA package, and emit citation-bearing
compliance findings, coverage artifacts, and reviewer-resolution items.

The review is not complete unless all applicable Forest Plan standards have been considered and
evaluated against EA package evidence. Missing inventory coverage, stale source-set IDs, missing plan
evidence, missing package evidence, ambiguous applicability, or unresolved contradictions must block
reviewer-ready status and become explicit reviewer work.

The output is an evidence-backed NFMA compliance review aid. It must not pretend to be final legal
advice, but it must be strong enough to show the basis for a project/activity consistency review and
to prove that the system did not skip applicable standards.

## NFMA Compliance Basis

Primary authority:

- 36 CFR 219.15, "Project and activity consistency with the plan":
  https://www.ecfr.gov/current/title-36/chapter-II/part-219/subpart-A/section-219.15

As of the current eCFR text checked on 2026-05-01, `36 CFR 219.15` requires projects and activities
authorized after plan approval to be consistent with the plan, requires inconsistency to be resolved
by modification, rejection/termination, or plan amendment, and requires the approval document to
describe consistency with applicable plan components. The system must encode this as a review
contract:

- Goals, desired conditions, and objectives: evaluate whether the project contributes to or does not
  foreclose maintenance or attainment over the long term.
- Standards: verify that the project or activity complies with every applicable standard.
- Guidelines: verify compliance with the guideline or evidence that the project is designed to be as
  effective in achieving the guideline purpose.
- Suitability: verify that the activity occurs where the plan identifies the area as suitable for
  that activity, or where the plan is silent about suitability for that activity.

System implication:

- Forest-plan review is mandatory for selected-profile packages.
- Standards are mandatory compliance checks, not optional evidence hints.
- Every component in the active inventory must receive an applicability determination.
- Every applicable standard must receive a compliance determination.
- Reviewer-ready status is false until component inventory coverage, applicability coverage, standard
  coverage, evidence grounding, provenance, and reviewer-resolution coverage all pass.

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
- Forest-plan component evaluation V0 is implemented as a default `forest-plan-resolve` stage for
  packages resolved to the selected forest-plan profile.
- `forest-plan-components-build` generates the active-source-set Custer Gallatin LMP component
  inventory from extracted chunks.
- The current generated inventory for `source-set-ba8d0feae79501b8` has `329` components, `58`
  standards, and passing build coverage with no missing or duplicate component/standard IDs.
- `config/forest_plan_component_inventory_seed.json` remains a narrow fallback/test fixture for the
  Crazy Mountains Backcountry Area proving case.
- Component findings now have a stable JSON/Markdown output contract and a machine-readable
  reviewer-resolution queue.
- Component validation fails closed on source-set drift and requires supported/partial findings to
  carry both package evidence and current plan-source evidence.
- NFMA standard coverage V0 writes selected-inventory coverage and applicable-standard coverage
  artifacts, adds structured compliance status to findings, and fails reviewer-ready when an
  applicable standard lacks plan-source evidence, EA package evidence, or a resolved compliance
  status.

Remaining gaps:

- No complete real-package V1 proving review has been run and adjudicated through the updated
  `compliance-review` path.
- No standalone component retrieval precision/recall eval artifact exists yet.
- Component-level graph artifacts are not yet emitted as a separate component graph; the compliance
  finding graph currently links the review to forest-plan review/component-evaluation artifacts.
- The compliance-status model remains V0 standard support/gap classification and should be expanded
  only after real-package failures show the next needed categories.
- The current generated inventory covers the active Custer Gallatin LMP source record; future plan
  amendments or other forest plans still require their own generated inventories and coverage.

## Definition Of Complete NFMA Forest Plan Review

A forest-plan review is complete only when the generated artifacts prove all of the following:

- The EA package is resolved to a governing forest-plan profile, or it is explicitly marked out of
  scope with evidence.
- All profile-required plan and supporting source records are present in the current retrieval index.
- The active source-set component inventory is complete for the governing plan scope used by the
  package, including standards, guidelines, suitability direction, goals, desired conditions,
  objectives, monitoring direction when relevant, plan amendments, geographic areas, management
  areas, overlays, and activity-specific direction.
- Every component in the active inventory has an applicability determination:
  `applicable`, `not_applicable`, `candidate`, or `needs_reviewer_resolution`.
- Every applicable standard has a compliance determination and package-evidence basis. A standard
  cannot be silently omitted, collapsed into a topic, or treated as satisfied by a broad Forest Plan
  consistency statement.
- Guidelines, suitability, goals, desired conditions, and objectives are evaluated using the
  criteria in `36 CFR 219.15(d)`, not by generic keyword overlap.
- The review emits an all-components coverage artifact and an all-applicable-standards coverage
  artifact. Both must pass before the review is reviewer-ready.
- The compliance matrix includes each applicable standard and its status, evidence, source component,
  package evidence, rationale, provenance, and reviewer-resolution item when unresolved.
- Any missing inventory, missing retrieval evidence, stale source-set ID, weak package evidence,
  ambiguous applicability, or potential inconsistency blocks reviewer-ready status.

## Non-Goals

- Do not hardcode East Crazies-specific runtime branches.
- Do not replace the responsible official's decision or counsel review with a model-generated legal
  conclusion.
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
      component_inventory_coverage.json
      applicable_standard_coverage.json
  reviews/<review_id>/
    forest_plan_context.json
    forest_plan_context_validation.json
    forest_plan_component_findings.json
    forest_plan_component_findings.md
    forest_plan_reviewer_resolution_queue.json
    forest_plan_component_inventory_coverage.json
    forest_plan_applicable_standard_coverage.json
    compliance_matrix.json
    compliance_matrix.md
    compliance_matrix.pdf
```

## Milestone 1: Data Model, Provenance, And Output Contract

Goal:
Define the component, finding, queue, and provenance contracts before building extraction logic.

Deliverables:

- `ForestPlanComponent` schema: **implemented for V0 seed inventories**
  - `component_id`
  - `forest_unit_id`
  - `plan_version`
  - `source_set_id`
  - `source_record_id`
  - `component_type`
  - `nfma_consistency_category`
  - `mandatory_for_nfma_review`
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
  - `applicability_rule`
  - `source_chunk_ids`
  - `artifact_sha256`
  - `content_sha256`
  - `provenance`
- `ForestPlanComponentFinding` schema: **implemented for V0 component findings**
  - `finding_id`
  - `component_id`
  - `applicability_status`
  - `finding_status`
  - `compliance_status`
  - `applicability_basis`
  - `plan_source_evidence`
  - `package_evidence`
  - `rationale`
  - `reviewer_resolution_items`
  - `provenance`
- `ForestPlanNFMAComplianceMatrix` schema:
  - one row per applicable standard
  - one row per non-standard applicable component when it affects the consistency determination
  - component ID, component type, NFMA consistency category, applicability status, compliance status,
    plan citation, package citation, rationale, provenance, and reviewer-resolution link
- Coverage schemas:
  - all component inventory records considered
  - all applicable components evaluated
  - all applicable standards evaluated
  - no skipped, duplicate, stale, or collapsed standard records
- `forest_plan_reviewer_resolution_queue.json` schema. **Implemented.**
- Docs in `docs/OUTPUT_SCHEMAS.md` and current-state notes. **Implemented.**

Research alignment:

- W3C PROV-style entity/activity/agent fields are part of the schema.
- Finding status is machine-readable; prose never becomes the only status surface.
- Compliance status is separate from evidence support. For example, a finding can have evidence but
  still be `potential_noncompliance` or `insufficient_evidence`.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- A finding can omit source-record IDs, source chunks, or provenance.
- A standard can be represented only as a broad topic instead of a first-class component row.
- Compliance status is inferred from Markdown report text instead of structured data.
- Readiness requires parsing Markdown prose.

## Milestone 2: Structured Component Inventory

Goal:
Create a versioned Custer Gallatin component inventory that is complete enough to support NFMA
project consistency review for the active plan scope. The East Crazies proving slice may be the first
run target, but the inventory cannot be limited only to components that the EA happens to mention.

Deliverables:

- Rebuildable component artifact under
  `source_library/derived/<source_set_id>/forest_plan_components/`.
- `components.jsonl` and `components.sqlite` with one record per reviewable plan component.
- One first-class component record for every standard. Standards must not be merged into broad
  resource-topic records.
- Component records for guidelines, suitability, goals, desired conditions, objectives, monitoring
  direction when relevant to project consistency, and plan amendments.
- Explicit component hierarchy and scope fields for:
  - Bridger/Bangtail/Crazy Mountains Geographic Area
  - Crazy Mountains Backcountry Area
  - designated areas and allocations
  - overlays and special designations
  - resource topics and activity tags
- `component_inventory_coverage.json` proving:
  - expected plan sections parsed
  - expected component counts by type
  - no duplicate component IDs
  - no collapsed standards
  - all source chunks and citations resolve to current artifacts
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
- The inventory cannot prove that all standards in the active plan scope were captured.

## Milestone 3: Precise Component Retrieval

Goal:
Retrieve exact component-level snippets and prove retrieval quality before using them in findings.

Deliverables:

- Component-aware retrieval queries and filters over `components.sqlite` and the existing evidence
  index.
- Retrieval output that returns minimal relevant snippets with source-record IDs, source chunk IDs,
  offsets, citation labels, and component IDs.
- `component_retrieval_eval.json` with precision/recall-oriented checks for fixture queries.
- Recall checks proving every applicable standard can retrieve its exact plan-source text before the
  evaluator uses it in a compliance finding.
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
- A missing plan-source snippet can still produce a reviewer-ready standard finding.

## Milestone 4: Applicability Graph And Selection

Goal:
Select applicable components using resolved package context plus component metadata and graph links.
Selection must be exhaustive: every component in the active inventory receives an applicability
status, and every potentially applicable standard remains in the review until resolved.

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
- Activity extraction for the EA package, including land exchange actions, road or access changes,
  motorized/mechanized uses, construction or disturbance, vegetation/wildlife/watershed effects,
  design features, alternatives, mitigations, and proposed decision commitments.
- `applicable_standard_coverage.json` with:
  - all standards in scope
  - applicability status and basis for each standard
  - package evidence that triggered applicability
  - `candidate` or `needs_reviewer_resolution` entries for uncertain matches
- Negative tests proving the evaluator does not mark all Custer Gallatin components applicable just
  because the package is on the forest.
- Positive tests proving an applicable standard cannot be omitted when the package contains matching
  geography, management area, overlay, activity, or resource-topic evidence.

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
- A `candidate` or unresolved standard is allowed to disappear from the compliance matrix.

## Milestone 5: Evidence-Backed NFMA Compliance Findings

Goal:
Compare EA package evidence against each applicable component and emit findings. Standards are
mandatory compliance checks: the evaluator must decide whether the EA package evidence shows
compliance, potential noncompliance, insufficient evidence, or unresolved applicability.

Deliverables:

- Finding statuses:
  - `supported`
  - `partial`
  - `gap`
  - `not_applicable`
  - `needs_reviewer_resolution`
- Compliance statuses:
  - `complies`
  - `potential_noncompliance`
  - `insufficient_evidence`
  - `not_applicable`
  - `needs_reviewer_resolution`
  - `guideline_equivalent_design`
  - `suitability_silent`
- Evidence matching that links package chunks to component requirements.
- Validation that `supported` and `partial` require both package evidence and forest-plan source
  evidence.
- Validation that a component remains a `gap` when plan evidence exists but package evidence is
  missing.
- Validation that every applicable standard has one compliance-status row and cannot be marked
  reviewer-ready without package evidence and plan-source evidence.
- Standard-specific rationale that explains how the package complies or why evidence is missing or
  contradictory. General statements like "the project is consistent with the Forest Plan" are
  supporting context only; they do not satisfy a standard by themselves.
- Guideline, suitability, goal, desired-condition, and objective logic aligned with
  `36 CFR 219.15(d)`:
  - guidelines require compliance or equivalent design-effectiveness evidence
  - suitability requires suitable-area or plan-silent evidence
  - goals, desired conditions, and objectives require contribution or non-foreclosure evidence
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
- A standard can be marked `complies` from a broad plan-consistency assertion alone.
- A potential inconsistency is hidden as `partial` without a reviewer-resolution item.
- The evaluator presents legal sufficiency conclusions instead of evidence-backed reviewer signals.

## Milestone 6: Evaluation Gates

Goal:
Add eval gates that measure the forest-plan evaluator before the real demo run. The critical metric
is recall for applicable standards: a review fails if the evaluator misses a standard that should
have been applied.

Deliverables:

- Fixture-level eval cases for:
  - relevant component retrieval
  - irrelevant component rejection
  - applicability classification
  - grounded component findings
  - all-applicable-standard recall
  - standard compliance status classification
  - guideline equivalent-design handling
  - suitability suitable/silent handling
  - goals, desired conditions, and objectives non-foreclosure handling
  - reviewer-resolution queue generation
- Metrics grouped by:
  - retrieval relevance
  - applicable-standard recall
  - component applicability precision
  - groundedness
  - compliance-status accuracy
  - report/finding relevance
  - provenance completeness
- Fail-closed behavior when source-set IDs, component IDs, source chunks, or citations drift.
- Failure taxonomy for missed standards, false applicability, stale inventory, missing package
  evidence, missing plan evidence, contradictory evidence, and unsupported compliance assertions.

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
- Applicable-standard recall is not measured independently.
- A missed applicable standard can still produce reviewer-ready output.

## Milestone 7: Component Outputs And Human Review Report

Goal:
Make component evaluation outputs usable as a mandatory NFMA Forest Plan compliance review package.

Deliverables:

- Write these artifacts under `source_library/reviews/<review_id>/`:
  - `forest_plan_component_findings.json`
  - `forest_plan_component_findings.md`
  - `forest_plan_reviewer_resolution_queue.json`
  - `forest_plan_component_inventory_coverage.json`
  - `forest_plan_applicable_standard_coverage.json`
  - forest-plan rows linked from the review-level `compliance_matrix.json`, `compliance_matrix.md`,
    and `compliance_matrix.pdf`
- Add summary fields to `forest_plan_context_summary.json`:
  - component count
  - applicable count
  - applicable standard count
  - standard compliance status counts
  - all-applicable-standards-applied boolean
  - supported count
  - partial count
  - gap count
  - reviewer-resolution count
  - provenance-complete count
- Human-readable report sections for:
  - applicable plan components
  - all applicable standards and compliance status
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
- The PDF matrix is omitted when the review claims NFMA compliance-readiness.
- The report obscures unresolved or unsupported components.

## Milestone 8: Real East Crazies Package Run

Goal:
Run the improved evaluator against the actual local East Crazies package and determine whether the
NFMA Forest Plan compliance review is complete. The run cannot be called reviewer-ready unless all
applicable standards are applied, all coverage gates pass, and unresolved items are explicit.

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
- Verified all-components and all-applicable-standards coverage artifacts.
- Verified NFMA compliance matrix JSON, Markdown, and PDF outputs.
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
- Any applicable standard is missing from the compliance matrix.
- Any applicable standard lacks plan-source evidence, package evidence, compliance status, or
  reviewer-resolution item.
- Generated findings depend on stale source-set IDs.
- The package cannot be reproduced from documented commands and committed config/code.

## Milestone 9: V1 Demo Integration

Goal:
Make NFMA Forest Plan compliance review a mandatory gate in the V1 demo document review and the
broader compliance-review path.

Deliverables:

- V1 demo review report section summarizing forest-plan component findings.
- `compliance-review` consumes forest-plan component findings and fails closed when the forest-plan
  component gate is absent, stale, incomplete, or not reviewer-ready.
- Clear distinction between forest-plan component evaluation, EA checklist review, and the mandatory
  NFMA component gate.
- Handoff that states the forest-plan compliance status, incomplete standards if any, and whether the
  V1 demo may proceed into broader `compliance-review`.

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
- The broader compliance-review path can pass while forest-plan compliance outputs are absent,
  stale, or incomplete for a selected-profile package.

## Milestone Discipline

- Keep one milestone per commit.
- Stage only the verified milestone slice.
- Prefer narrow fixtures and current source-set reuse over broad corpus rebuilds.
- Keep NFMA Forest Plan compliance review mandatory for selected-profile packages; command flags may
  override inventory paths for testing, but must not disable the review path.
- Treat the all-applicable-standards coverage gate as a release blocker, not a warning.
- Treat every unsupported, ambiguous, or missing plan-component result as reviewer work, not as a
  hidden pass.
- Treat every missed, stale, or unresolved applicable standard as incomplete NFMA review.
- Update `docs/SESSION_HANDOFF.md` after substantial implementation work.
