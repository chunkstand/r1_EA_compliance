# Applicability-First Review Milestone Plan

Date: 2026-05-04

This plan defines the post-V1 architecture change needed to make legal-authority applicability a
first-class, pre-review stage. The critical system function is not merely to evaluate a static rule
pack. The system must first determine which laws, regulations, policies, Forest Plan requirements,
and supporting authorities apply to the EA package, produce auditable artifacts for both applicable
and non-applicable authorities, validate those determinations, generate the review rule pack from
the validated applicability result, and only then run the compliance review.

The prior plan established the first artifact contract and implemented the
`applicability-authority-universe` snapshot slice. This revision updates the target architecture to
use an explicit authority universe, package fact graph, per-authority hybrid retrieval,
bounded graph expansion, deterministic decision ledger, search coverage certificates,
adjudication, and provenance-backed generated rule packs.

## Current Implementation Boundary

Implemented today:

- `applicability-authority-universe` writes `authority_universe_snapshot.json` with the complete
  candidate authority universe used by later applicability determination.
- Milestone 1 schema and gate semantics are defined in `docs/OUTPUT_SCHEMAS.md` for the package
  fact graph, retrieval trace, graph trace, search coverage certificates, provenance, validated
  applicable/non-applicable authority artifacts, and generated rule-pack identity.
- Milestone 2 authority-universe hardening is implemented: rule-template and Forest Plan component
  candidates carry required package fact types, positive/negative trigger groups, source evidence
  requirements, source/package filters, retrieval contracts, graph-expansion contracts,
  dependency/exception/supersession fields, and search coverage requirements.
- Milestone 3 package context is implemented: `applicability-context-build` reads the existing EA
  package cache and writes `package_fact_graph.json`, `package_applicability_context.json`, and
  `package_fact_graph_validation.json` before any applicability decisions are attempted.
- Milestone 4 retrieval and graph tracing is implemented: `applicability-retrieve` writes
  `applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`, and
  `applicability_retrieval_graph_diagnostics.json` without deciding applicability. Graph traces
  explicitly carry authority-category, source-claim/rule-claim-link, supporting-source, package
  fact, and Forest Plan component provenance when those artifacts are available.
- Milestone 5 deterministic decisions are implemented: `applicability-determine` consumes the
  authority universe, package fact graph/context, retrieval trace, and graph trace, then writes
  `applicability_decisions.jsonl`, applicable/non-applicable authority artifacts, search coverage
  certificates, provenance, and a reviewer report without producing compliance findings.
- Milestone 6 validation and adjudication is implemented: `applicability-validate` writes
  `applicability_validation.json` and fails closed on missing, duplicated, stale, unsupported, or
  unresolved decisions; `applicability-adjudication-template`,
  `applicability-adjudication-eval`, and `applicability-adjudication-apply` provide a replayable
  machine-readable adjudication path for resolving open decisions.
- Milestone 7 generated rule pack is implemented: `applicability-generate-rule-pack` writes and
  validates a generated compliance rule pack from validated applicable authorities only.
- Milestone 8 compliance-review gate is implemented and gap-closed: reviewer-ready
  `compliance-review` requires a generated rule pack plus passing applicability/generated-pack
  validation, non-applicable authority, coverage, provenance, source-set, package-manifest, and
  package-chunk hash gates. Base rule packs can run only as non-reviewer-ready diagnostics and are
  excluded from promotion readiness.

Not implemented yet:

- applicability decision-quality evals and gold evals that independently promote applicability
  correctness before compliance quality is scored.

## Target Invariant

No compliance review should run directly from the standing authority corpus or from a hand-selected
rule pack. The review sequence must be:

```text
EA package + source library + authority universe
  -> package fact graph
  -> per-authority hybrid retrieval
  -> graph expansion and dependency tracing
  -> deterministic applicability decision ledger
  -> applicable_authorities artifact
  -> non_applicable_authorities artifact
  -> search coverage certificates
  -> applicability validation and adjudication gate
  -> generated review rule pack
  -> compliance review
```

The compliance review stage must consume the generated review rule pack and the validated
applicability run identity. It must not decide whether laws, regulations, policies, or Forest Plan
components apply.

## Research Basis

The recommended architecture treats applicability as legal issue spotting over a complete authority
universe, not as an open-ended model answer.

- Legal retrieval benchmarks emphasize exact retrieval, expert adjudication, and supporting
  passages: [LegalBench-RAG](https://arxiv.org/abs/2408.10343) and
  [Legal RAG Bench](https://arxiv.org/abs/2603.01710).
- GraphRAG supports corpus-wide sensemaking, entity relationships, and multi-hop expansion, but
  should be used for evidence discovery rather than final legal decisions:
  [Microsoft GraphRAG](https://arxiv.org/abs/2404.16130) and
  [DRIFT Search](https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/).
- Hybrid retrieval should combine exact keyword/citation search, semantic search when available,
  metadata filters, and fused ranking. Reciprocal Rank Fusion is the default merger:
  [Azure AI Search RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking).
- Auditability should follow provenance-first patterns: W3C PROV-style entities, activities,
  agents, derivations, and hashes; and NIST AI RMF-style traceability, evaluation, and human
  oversight controls:
  [W3C PROV](https://www.w3.org/blog/2013/prov-a-framework-for-provenance-interchange/) and
  [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework).
- The legal workflow itself supports early applicability determination: USDA NEPA regulations
  describe determining what actions are subject to NEPA and the applicable level of review, and
  Forest Service planning rules require projects to be consistent with applicable plan components:
  [7 CFR 1b.1](https://www.law.cornell.edu/cfr/text/7/1b.1) and
  [36 CFR 219.15](https://www.law.cornell.edu/cfr/text/36/219.15).

## Recommended Architecture

1. Authority universe:
   Start with a complete candidate set of statutes, regulations, policies, executive orders,
   Forest Plan components, supporting source records, and rule templates. This is a bounded legal
   universe with versioned source identity, not a dynamic web search.
2. Package fact graph:
   Convert the EA package into typed facts: action type, lead agency, decision posture, NEPA level,
   project location, forest unit, geography, management areas, overlays, resource topics,
   consultations, permits, cooperating agencies, public involvement, alternatives, and no-action
   context. Each fact must carry package span IDs and hashes.
3. Per-authority hybrid retrieval:
   For every candidate authority, run an evidence search plan using exact citations/terms, semantic
   retrieval when embeddings are available, metadata filters, source-role filters, package-section
   filters, and rule-declared trigger groups. Persist all queries, result ranks, fused scores, and
   rejected candidates.
4. Graph expansion:
   Expand from retrieved nodes through authority hierarchy, source-record relationships,
   rule-claim links, Forest Plan profile links, component inventory relationships, geographic
   overlays, exceptions, dependencies, and related permits or consultations. Persist the graph paths
   that were inspected.
5. Deterministic decision ledger:
   Evaluate typed predicates over package facts, retrieved evidence, graph paths, and authority
   trigger contracts. The output is one decision row per candidate authority:
   `applicable`, `not_applicable`, `unresolved`, or `needs_adjudication`.
6. Coverage and negative-proof gate:
   A not-applicable decision is defensible only when it has affirmative negative evidence,
   explicit trigger-miss evidence, a replayable search coverage certificate, or adjudication.
   Absence alone is not enough unless the system proves where it searched and why that search was
   sufficient for the authority predicate.
7. Generated rule pack:
   Generate the downstream rule pack only from validated applicable decisions. Non-applicable
   authorities remain in the non-applicable artifact and report, not in the compliance matrix.
8. Compliance review:
   Review compliance only for generated applicable rules. Compliance findings may cite the
   applicability run, but they must not revise applicability.

## Defensibility Standard

An applicability run is defensible when an independent reviewer can replay the run from durable
artifacts and answer these questions:

- What authority universe was considered?
- What package facts were extracted, from which spans, and with what hashes?
- What exact keyword, vector, metadata-filtered, and graph-neighbor searches were run for each
  authority?
- What evidence, negative evidence, and graph paths supported each decision?
- Which authorities were unresolved, adjudicated, or excluded, and by what reviewer record?
- Why is the generated rule pack a complete and current derivative of the validated applicable
  authorities?

The system must fail closed when those questions cannot be answered.

## System Changes Required

The milestone sequence must update these surfaces to support the architecture:

- Schemas and docs:
  - extend `docs/OUTPUT_SCHEMAS.md` for package fact graph, retrieval trace, graph expansion trace,
    search coverage certificates, and provenance fields;
  - update `README.md` once each artifact family becomes implemented behavior;
  - keep `docs/CURRENT_SYSTEM_STATE.md` honest about implemented versus planned state.
- Applicability module:
  - expand `src/usfs_r1_ea_sources/applicability.py` from authority-universe snapshotting into
    staged context building, retrieval, graph tracing, decision-ledger writing, validation,
    adjudication, and generated-rule-pack production.
- CLI:
  - add staged commands for context build, retrieval/graph trace, deterministic decision,
    validation, adjudication, and generated-rule-pack generation;
  - keep `applicability-authority-universe` as the bounded universe builder.
- Retrieval:
  - add or extend local retrieval surfaces so applicability can run exact BM25/keyword search,
    optional dense retrieval, source-role filters, package-section filters, authority-category
    filters, and RRF-style fusion;
  - persist per-authority query plans and result ledgers.
- Graph:
  - add authority, package-fact, source-claim, Forest Plan component, geography, overlay,
    exception, dependency, and generated-rule-pack edges needed for bounded GraphRAG-style
    traversal;
  - persist inspected graph paths so graph retrieval is auditable.
- Predicate engine:
  - move applicability tests out of `compliance-review` into data-backed predicates over package
    facts, evidence traces, graph paths, and adjudication state.
- Validation and eval:
  - add validation checks for universe partition, stale hashes, evidence sufficiency, negative
    proof, graph path traceability, search coverage, adjudication replay, and generated-rule-pack
    consistency;
  - add applicability evals and gold evals that score applicability precision/recall separately
    from compliance correctness.
- Compliance review:
  - refactor `compliance-review` so reviewer-ready execution accepts only a validated generated
    rule pack and validated applicability run.

## Artifact Contract

All artifacts should live under:

```text
source_library/reviews/<review_id>/applicability/
```

Required artifacts:

- `authority_universe_snapshot.json`
  - candidate authority set considered for the package;
  - source set ID, catalog hash, authority source records, rule-template IDs, Forest Plan profile
    IDs, component inventory IDs, currentness metadata, predicate contracts, retrieval contracts,
    graph expansion contracts, dependencies, exceptions, and search coverage requirements.
- `package_fact_graph.json`
  - typed package facts and relationships used for applicability;
  - package span IDs, section IDs, fact confidence class, fact extraction method, and package hash
    lineage.
- `package_applicability_context.json`
  - package manifest hash, package section map, project type, federal action signals, forest unit,
    geography, management areas, overlays, consultations, permits, public involvement, decision
    posture, and supporting document signals.
- `applicability_retrieval_trace.jsonl`
  - one or more rows per candidate authority recording exact keyword/citation queries, vector
    queries when available, metadata filters, package-section filters, ranked results, fused rank,
    rejected results, and timestamps.
- `applicability_graph_trace.jsonl`
  - graph paths inspected for each candidate authority, including source-record, authority,
    rule-claim, Forest Plan component, geography, overlay, exception, dependency, and package-fact
    edges.
- `applicability_decisions.jsonl`
  - one row per candidate authority;
  - decision status: `applicable`, `not_applicable`, `unresolved`, or `needs_adjudication`;
  - decision basis, predicate result, evidence spans, negative evidence spans, missing evidence,
    source-record IDs, package chunk IDs, graph path IDs, retrieval trace IDs, confidence class,
    and adjudication state.
- `applicable_authorities.json`
  - only authorities selected for review;
  - evidence-backed applicability basis and generated-rule metadata.
- `non_applicable_authorities.json`
  - only authorities excluded from review;
  - cited non-applicability basis, negative trigger evidence, absent-trigger rationale, search
    coverage certificate ID, or adjudicator decision.
- `search_coverage_certificates.json`
  - one certificate per not-applicable or unresolved decision class proving which source indexes,
    package indexes, metadata filters, graph neighborhoods, and query variants were searched.
- `applicability_validation.json`
  - machine gate proving complete candidate coverage, artifact consistency, source freshness,
    evidence requirements, negative-proof requirements, graph traceability, no unresolved
    decisions, and generated-rule-pack readiness.
- `applicability_provenance.json`
  - W3C PROV-style run lineage linking package/source entities, retrieval and graph activities,
    deterministic predicate activities, adjudication agents, artifact hashes, and generated outputs.
- `applicability_report.md`
  - reviewer-facing summary of applicable, non-applicable, unresolved, and adjudicated decisions.
- `generated_rule_pack.json`
  - the only rule pack accepted by downstream reviewer-ready compliance review.
- `generated_rule_pack_validation.json`
  - derived identity, hash, source-set, package, applicable-authority, validation, and staleness
    consistency.

Optional but expected once adjudication and model-assisted evidence proposal are introduced:

- `applicability_adjudication_template.json`
- `applicability_adjudication_worklist.md`
- `applicability_adjudication_eval.json`
- `applicability_adjudication_apply.json`
- `llm_evidence_proposals.jsonl`
  - diagnostic-only model proposals for evidence or query expansion; never authoritative
    applicability decisions.

## Milestone 1: Schema And Contract Revision

Goal:
Update the artifact schemas and gate semantics for the full architecture before runtime changes.

Non-goals:

- Do not change `compliance-review` behavior yet.
- Do not regenerate source-library artifacts.
- Do not broaden the authority corpus in this milestone.

Relevant files or surfaces:

- `docs/OUTPUT_SCHEMAS.md`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`
- `config/compliance_rule_pack_nepa_ea_v0.json`

Implementation direction:

- Add schemas for `package_fact_graph.json`, `applicability_retrieval_trace.jsonl`,
  `applicability_graph_trace.jsonl`, `search_coverage_certificates.json`, and
  `applicability_provenance.json`.
- Define package fact node/edge types:
  - action, agency, decision posture, NEPA level, geography, management area, overlay,
    consultation, permit, public involvement, alternative, resource topic, package section, and
    evidence span.
- Define retrieval trace fields:
  - query text, query type, authority ID, source filter, package-section filter, result rank,
    fused score, selected/rejected status, and hash of the searched index.
- Define graph trace fields:
  - start node, end node, relationship type, traversal depth, path rationale, selected/rejected
    status, and hash of the graph artifact.
- Define search coverage certificate requirements for each not-applicable decision class.
- Define generated rule-pack identity fields:
  - `base_rule_pack_id`
  - `base_rule_pack_version`
  - `generated_rule_pack_id`
  - `applicability_run_id`
  - `applicability_validation_sha256`
  - `authority_universe_sha256`
  - `package_fact_graph_sha256`
  - `retrieval_trace_sha256`
  - `graph_trace_sha256`
  - `search_coverage_certificates_sha256`
  - `package_manifest_sha256`
  - `source_set_id`
  - `review_id`
- Define hard validation failures:
  - candidate authority missing from the decision ledger;
  - authority present in both applicable and non-applicable artifacts;
  - unresolved or needs-adjudication authority still present at generated-pack time;
  - non-applicable authority has no basis, coverage certificate, or adjudication;
  - applicable authority has no package/source basis unless an explicitly validated mandatory
    basis applies;
  - retrieval evidence lacks query/result trace;
  - graph-supported decision lacks graph path trace;
  - generated rule pack does not match applicable-authorities artifact; and
  - generated rule pack is stale relative to package, source set, authority universe, retrieval
    trace, graph trace, or validation artifact.

Required eval signal:

- The schema docs make clear that applicability happens before compliance review.
- The non-applicable artifact is separate from the review matrix.
- Graph and model-assisted retrieval are evidence-discovery inputs only; deterministic predicates
  and adjudication produce the final decision ledger.

Required tests:

```bash
git diff --check
```

Commit policy:
Commit the schema/docs contract as an atomic planning slice.

Stop conditions:

- The schema still allows `compliance-review` to be the first place where applicability is decided.
- The non-applicable artifact is optional or merged only into the compliance matrix.
- Not-applicable decisions can pass without search coverage or adjudication.

## Milestone 2: Authority Universe Snapshot Hardening

Current status:
Implemented. `applicability-authority-universe` now writes the complete candidate universe needed by
the recommended architecture. It still writes only `authority_universe_snapshot.json`; it does not
build the package fact graph or decide package applicability.

Goal:
Build the complete candidate authority universe used by applicability determination.

Non-goals:

- Do not decide package applicability in this milestone.
- Do not run compliance review.
- Do not fetch new sources unless a missing source blocks the authority universe contract.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/applicability.py`
- `src/usfs_r1_ea_sources/cli.py`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/forest_plan_profiles.json`
- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/derived/<source_set_id>/claims/claims.jsonl`
- `source_library/derived/<source_set_id>/rule_claim_links/`
- focused applicability tests

Implementation direction:

- Enrich every candidate with:
  - required package fact types;
  - positive trigger groups;
  - negative trigger groups;
  - required source evidence;
  - source-role filters;
  - package-section filters;
  - graph-neighbor expansion rules;
  - dependencies, exceptions, and supersession relationships; and
  - search coverage requirements for not-applicable decisions.
- Include all candidate authorities, not only baseline or likely-triggered authorities.
- Represent Forest Plan components as authority candidates with geography, management area, overlay,
  component-type, plan-source, and package-fact predicates.
- Validate that every candidate has source-record identity, document role, authority category,
  source evidence availability, and a deterministic applicability predicate contract.

Required eval signal:

- The current authority rules are represented in the snapshot.
- Custer Gallatin Forest Plan candidates are represented through profile/component inventory
  references rather than hardcoded runtime branches.
- Conditional authorities remain in the candidate universe even when expected not to apply.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the authority-universe hardening, focused tests, and schema docs together.

Stop conditions:

- Candidate authorities are inferred by scanning raw filenames.
- The universe omits conditional authorities because they are not expected to apply.
- A candidate lacks source-record provenance, predicate metadata, or search coverage requirements.

## Milestone 3: Package Fact Graph

Current status:
Implemented. `applicability-context-build` now reads
`source_library/reviews/<review_id>/package/package_manifest.jsonl` and
`source_library/reviews/<review_id>/package/package_chunks.jsonl`, then writes the package fact
graph, package applicability context, and package fact graph validation summary under
`source_library/reviews/<review_id>/applicability/`. It does not decide authority applicability,
write retrieval or graph traces, emit applicability decisions, generate rule packs, or run
compliance review. The gap-closure pass added explicit project-location facts, weak-signal
uncertainty records, missing-common-fact uncertainty records, and contradiction tests that prove
negative-context facts create `contradicts_fact` edges instead of silent resolution.

Goal:
Build a package fact graph before applicability decisions are attempted.

Non-goals:

- Do not decide authority applicability.
- Do not evaluate compliance status.
- Do not emit generated rule packs.

Relevant files or surfaces:

- package extraction/cache helpers
- section-detection helpers
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `src/usfs_r1_ea_sources/forest_plan_components.py`
- new package fact graph code under `src/usfs_r1_ea_sources/`
- focused package fact graph fixtures/tests

Implementation direction:

- Add a staged command such as `applicability-context-build`.
- Reuse the existing package cache and section detection, but emit applicability-specific context
  under `source_library/reviews/<review_id>/applicability/`.
- Write:
  - `package_fact_graph.json`
  - `package_applicability_context.json`
  - package fact graph validation summary
- Extract typed facts for:
  - project/action type;
  - lead agency and cooperating agencies;
  - decision posture and NEPA level;
  - forest unit, project location, geographic areas, management areas, and overlays;
  - land exchange, road, recreation, minerals, wildlife, water, heritage, botany, fire, scenery,
    grazing, and other resource-topic signals;
  - ESA, NHPA, MBTA, Clean Water Act, wetlands/floodplains, roadless, wilderness, tribal, and
    permit/consultation cues;
  - purpose and need, alternatives, no action, cumulative effects, mitigation, public involvement,
    and finding/decision document signals.
- Attach every fact to package span IDs, section IDs, parser provenance, and hashes.
- Treat contradictory, weak, or missing facts as graph uncertainty, not as applicability decisions.

Required eval signal:

- The East Crazy package can produce typed project/action, forest-plan scope, geography/overlay,
  resource-topic, and consultation/permit facts before compliance review.
- Fact extraction preserves exact package citations and section bindings.
- Negative or out-of-scope location statements do not become positive geography facts.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the package fact graph command, validation, focused tests, and schema/docs updates together.

Stop conditions:

- Package facts are hidden inside `compliance-review`.
- Facts lack package span IDs or hashes.
- Contradictory facts are silently resolved without trace or adjudication path.

## Milestone 4: Hybrid Retrieval And Graph Expansion Traces

Current status:
Implemented. `applicability-retrieve` now consumes the authority universe, package fact graph, and
local retrieval index, then writes replayable per-candidate retrieval rows, RRF fused result rows,
bounded graph path rows, and diagnostics under
`source_library/reviews/<review_id>/applicability/`. Gap closure added explicit graph paths and
evidence references for authority-category hierarchy, source-claim/rule-claim-link bindings,
supporting source records, package facts, and Forest Plan components. The command does not decide
final applicability, emit coverage certificates, generate rule packs, or run compliance review.

Goal:
Run replayable per-authority evidence discovery using hybrid search and bounded graph traversal.

Non-goals:

- Do not decide final applicability.
- Do not use graph summaries as legal conclusions.
- Do not require external hosted search services for local reviewer-ready operation.

Relevant files or surfaces:

- local retrieval index builder/query helpers
- `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
- evidence graph artifacts
- source claim graph artifacts
- rule-claim link artifacts
- package fact graph artifacts
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/forest_plan_profiles.json`

Implementation direction:

- Add a staged command such as `applicability-retrieve`.
- For each candidate authority, execute a query plan with:
  - exact citation/authority-term search;
  - keyword/BM25-style search over source and package chunks;
  - optional dense retrieval when local embeddings are present;
  - source-record, document-role, authority-category, and currentness filters;
  - package-section filters;
  - Forest Plan profile/component filters; and
  - RRF-style fused ranking across independent result lists.
- Persist all evidence discovery in `applicability_retrieval_trace.jsonl`.
- Add bounded graph expansion from retrieved nodes through:
  - authority hierarchy;
  - source-record relationships;
  - rule-claim links;
  - Forest Plan profile/component relationships;
  - geography, management area, and overlay links;
  - exception, dependency, supersession, and supporting-record links; and
  - package fact graph nodes.
- Persist graph paths in `applicability_graph_trace.jsonl`.
- Emit diagnostics for retrieval misses, low-confidence retrieval, graph dead ends, and excessive
  graph fan-out.

Required eval signal:

- CE/FANEC, ESA/NHPA/MBTA, wetlands/floodplains, roadless, and Forest Plan authorities each have
  per-authority retrieval traces whether they apply or not.
- Graph expansion is bounded by authority-declared contracts and cannot wander across unrelated
  authorities.
- Every selected evidence span in a future decision can be traced back to a query or graph path.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit retrieval/graph trace implementation, focused tests, and schema/docs updates together.

Stop conditions:

- Retrieval traces cannot reproduce which searches produced a decision.
- Graph expansion can create unbounded or untyped authority relationships.
- Search results are selected without source-record, package-section, or graph-path provenance.

## Milestone 5: Deterministic Applicability Decision Ledger

Current status:
Implemented. `applicability-determine` now consumes `authority_universe_snapshot.json`,
`package_fact_graph.json`, `package_applicability_context.json`,
`applicability_retrieval_trace.jsonl`, and `applicability_graph_trace.jsonl`, then writes
`applicability_decisions.jsonl`, `applicable_authorities.json`,
`non_applicable_authorities.json`, `search_coverage_certificates.json`,
`applicability_provenance.json`, and `applicability_report.md`. The predicate engine records
mandatory baseline, positive package trigger, absent-trigger, negative-evidence, Forest Plan
component, source-required, and unresolved-conflict bases. Weak package evidence becomes
`needs_adjudication`; not-applicable decisions cite search coverage certificates. Gap closure added
raw package-chunk trigger checks for explicit negative evidence, source-index hash requirements for
sufficient coverage, retained source-library evidence spans on non-applicable decisions, and
package manifest/chunk provenance entities. The command does not emit compliance findings, generate
a rule pack, or validate adjudication readiness.

Goal:
Add the pre-review decision command that writes all first-class applicability artifacts without
producing compliance findings.

Non-goals:

- Do not evaluate compliance status.
- Do not emit `pass`, `gap`, or `uncertain` compliance findings.
- Do not let model prose decide legal applicability.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/applicability.py`
- `src/usfs_r1_ea_sources/cli.py`
- package fact graph artifacts
- retrieval and graph trace artifacts
- authority universe snapshot
- focused applicability tests

Implementation direction:

- Add or complete `applicability-determine`.
- Consume:
  - `authority_universe_snapshot.json`
  - `package_fact_graph.json`
  - `package_applicability_context.json`
  - `applicability_retrieval_trace.jsonl`
  - `applicability_graph_trace.jsonl`
- Evaluate deterministic predicates for each candidate authority.
- Emit:
  - `applicability_decisions.jsonl`
  - `applicable_authorities.json`
  - `non_applicable_authorities.json`
  - `search_coverage_certificates.json`
  - `applicability_provenance.json`
  - `applicability_report.md`
- Record separate bases for:
  - mandatory baseline applicability;
  - positive package triggers;
  - explicit negative package evidence;
  - absent trigger evidence backed by coverage certificate;
  - forest-plan profile resolution;
  - Forest Plan component applicability;
  - authority dependency or exception;
  - source currentness;
  - human adjudication; and
  - unresolved evidence conflict.
- Treat weak or contradictory evidence as `needs_adjudication`, not as a reviewable decision.
- If LLM-assisted evidence proposals are introduced, persist them only as
  `llm_evidence_proposals.jsonl`; the predicate engine must still make the decision.

Required eval signal:

- The East Crazy package produces applicable and non-applicable artifacts before review.
- Current CE/FANEC non-applicable decisions are recorded in `non_applicable_authorities.json`, not
  only as matrix rows.
- The currently pending conditional rows become explicit `needs_adjudication` or adjudicated
  decisions and block generated-rule-pack readiness until resolved.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the decision command, focused tests, and docs only after it produces first-class
applicability artifacts.

Stop conditions:

- Applicability output depends on compliance findings.
- Non-applicable authorities lack evidence, search coverage, or explicit no-trigger rationale.
- Pending conditional applicability is accepted as review-ready.

## Milestone 6: Validation, Coverage, And Adjudication Gate

Current status:
Implemented and gap-closed. `applicability-validate` validates required artifacts, candidate
decision coverage, applicable/non-applicable partitioning, unresolved/needs-adjudication status,
evidence sufficiency, search coverage, retrieval/graph traceability, source/package freshness,
Forest Plan component scope, package fact-graph validation status, contradiction/adjudication
handling, human-adjudication replayability, partition/coverage freshness, and provenance hash
alignment. `applicability-adjudication-template`, `applicability-adjudication-eval`, and
`applicability-adjudication-apply` provide a replayable adjudication route; apply rewrites decision
and partition artifacts with `human_adjudication` bases and updates provenance. This milestone still
does not generate a rule pack or gate `compliance-review`.

Goal:
Make applicability validation a hard gate that must pass before a generated rule pack can be used.

Non-goals:

- Do not rely on manual inspection without a machine-readable adjudication record.
- Do not downgrade unresolved authorities to not-applicable for convenience.
- Do not let `compliance-review` override the applicability gate.

Relevant files or surfaces:

- applicability artifacts from Milestones 2 through 5
- `phase-eval`
- `compliance-review-eval`
- new applicability eval fixtures under `config/`
- focused tests for validation failure modes

Implementation direction:

- Add `applicability-validate`.
- Add `applicability-adjudication-template`, `applicability-adjudication-apply`, and
  `applicability-adjudication-eval` for unresolved decisions.
- Validation must prove:
  - every authority in the universe has exactly one decision row;
  - applicable and non-applicable artifacts partition the candidate universe after adjudication;
  - no unresolved authority remains at generated-pack time;
  - every applicable decision has source and package evidence or an explicitly validated mandatory
    basis;
  - every non-applicable decision has negative evidence, trigger-miss evidence plus coverage
    certificate, or adjudication;
  - every decision that used retrieval has retrieval trace IDs;
  - every decision that used graph expansion has graph path IDs;
  - Forest Plan profile/component applicability has required source and package context;
  - artifact hashes match current package/source-set inputs; and
  - provenance lineage covers every required artifact with non-stale entity hashes.
- Add failure taxonomy:
  - `missing_candidate_decision`
  - `duplicate_decision`
  - `applicable_evidence_gap`
  - `non_applicable_basis_gap`
  - `search_coverage_gap`
  - `retrieval_trace_gap`
  - `graph_trace_gap`
  - `contradictory_package_evidence`
  - `forest_plan_scope_unresolved`
  - `source_set_stale`
  - `package_cache_stale`
  - `adjudication_missing`
  - `provenance_gap`

Required eval signal:

- A package with pending conditional rows fails validation until adjudicated.
- A non-applicable decision without evidence, coverage, or adjudication fails validation.
- A stale applicability artifact fails validation.
- A graph-supported decision without graph path trace fails validation.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit validation, adjudication tooling, tests, and schema updates together.

Stop conditions:

- Validation passes with unresolved applicability decisions.
- Validation passes when a candidate authority is absent from both first-class artifacts.
- Adjudication cannot be replayed deterministically.
- Not-applicable decisions can pass from simple absence without coverage proof.

## Milestone 7: Generated Rule Pack

Current status:
Implemented and gap-closed. `applicability-generate-rule-pack` reads a passing and current
`applicability_validation.json`, the validated `applicable_authorities.json`,
`non_applicable_authorities.json`, the authority universe snapshot, the decision ledger, and the base
rule pack, then writes `generated_rule_pack.json` and `generated_rule_pack_validation.json`.
Generated packs include only validated applicable authorities, carry decision/evidence/trace/source
metadata, explicit base/generated rule IDs, per-rule artifact hashes, and synthesize Forest Plan
component rules when applicable. Validation fails if the pack lacks a recorded generated-pack hash,
is manually edited, or is stale relative to current applicability artifacts. This milestone still
does not gate `compliance-review`; that boundary is Milestone 8.

Goal:
Generate the review rule pack from the validated applicable-authorities artifact.

Non-goals:

- Do not hand-edit generated rule packs.
- Do not include non-applicable authorities in the generated review rule pack.
- Do not preserve baseline rules by default unless their applicability decision has passed the
  applicability gate.

Relevant files or surfaces:

- `config/compliance_rule_pack_nepa_ea_v0.json`
- applicability artifacts
- `validate_rule_pack`
- rule-claim binding validation
- compliance coverage validation

Implementation direction:

- Add `applicability-generate-rule-pack`.
- The generated rule pack should contain only validated applicable authorities.
- Each generated rule must carry:
  - base rule ID;
  - generated rule ID if transformed;
  - applicability decision ID;
  - applicability evidence references;
  - retrieval trace IDs;
  - graph path IDs;
  - source-record IDs;
  - document roles;
  - source-claim link requirements;
  - package-section expectations;
  - Forest Plan component references when relevant; and
  - source, package, authority-universe, validation, and provenance hashes.
- Emit `generated_rule_pack.json` under the applicability directory.
- Emit `generated_rule_pack_validation.json`.
- Preserve a hash of the exact applicable-authorities artifact used to generate it.
- Fail if source-claim links are missing for claim-bearing generated rules.

Required eval signal:

- Generated rule-pack rule count equals validated applicable-authority count.
- Non-applicable authorities are absent from generated rules and present only in
  `non_applicable_authorities.json`.
- Rule-pack validation fails if the generated pack is edited by hand or stale relative to
  applicability artifacts.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack source_library/reviews/<review_id>/applicability/generated_rule_pack.json \
  --eval-file config/rule_claim_link_eval_seed.generated.json
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit generated-rule-pack implementation and tests after validation proves derived identity and
staleness checks.

Stop conditions:

- Generated pack can drift from applicability artifacts without detection.
- Non-applicable authorities can appear in generated rules.
- Review can run against the base rule pack instead of the generated pack.

## Milestone 8: Gate Compliance Review Behind Generated Rule Pack

Current status:
Implemented and gap-closed. Reviewer-ready `compliance-review` now requires a generated
applicability rule pack and the adjacent applicability validation, generated-pack validation,
non-applicable authority, search-coverage, provenance, source-set, package-manifest, and
package-chunk hash gates. Generated-pack validation must explicitly set
`generated_rule_pack_ready=true`; missing readiness no longer defaults to passing. The base rule
pack remains available only through the explicit diagnostic flag, and there is no internal
reviewer-ready bypass for base-pack API or eval callers. Diagnostic base-pack outputs are not
reviewer-ready and are excluded from compliance-gold promotion readiness. Generated-rule-pack
review evaluates the generated applicable rules only and records the applicability gate plus
non-applicable authority artifact links in the compliance matrix.

Goal:
Refactor `compliance-review` so reviewer-ready review can only occur after applicability
validation and generated-rule-pack creation.

Non-goals:

- Do not remove the base authority rule pack. It remains the candidate authority template.
- Do not lose the ability to produce a combined reviewer-facing report.
- Do not use the review matrix as the source of truth for non-applicability.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/cli.py`
- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `tests/test_compliance_review.py`

Implementation direction:

- Replace direct reviewer-ready use of `--rule-pack config/...` with a generated-pack path plus
  applicability-run reference.
- For transition, allow an explicit diagnostic flag such as `--allow-base-rule-pack-review`, but
  mark outputs non-reviewer-ready and exclude them from promotion gates.
- Make `compliance-review` validate:
  - generated rule pack exists;
  - applicability validation passed;
  - generated pack hash matches applicability validation;
  - package manifest hash matches;
  - package chunks hash matches;
  - source set matches;
  - non-applicable artifact exists and validates;
  - search coverage certificates exist for non-applicable decisions; and
  - generated rule pack provenance matches the applicability run.
- Change compliance matrix semantics:
  - compliance findings evaluate generated applicable rules only;
  - matrix summary links to `non_applicable_authorities.json`;
  - combined Markdown/PDF report may include a separate non-applicable section, but it must cite the
    applicability artifact as source of truth.

Required eval signal:

- `compliance-review` refuses to run against the base pack in reviewer-ready mode.
- `compliance-review` refuses to run when non-applicable artifacts or coverage certificates are
  missing.
- The existing V1 package can complete the new sequence only after applicability artifacts,
  validation, and generated pack exist.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the review gate refactor only after the full local sequence passes.

Stop conditions:

- `compliance-review` still decides applicability.
- A review can be promoted without validated non-applicable artifacts.
- The matrix can be mistaken as the source artifact for non-applicability.

## Milestone 9: Applicability Evaluation And Promotion Gates

Goal:
Add eval coverage that proves applicability decisions are correct before compliance quality is
scored.

Non-goals:

- Do not treat generated review success as proof of applicability correctness.
- Do not rely only on synthetic all-authorities fixtures.
- Do not broaden Region 1 readiness without real-package adjudication.

Relevant files or surfaces:

- new `config/applicability_eval_seed.json`
- new `config/applicability_gold_eval_v0.json`
- `phase-eval`
- `v1-ea-eval`
- `compliance-review-eval`
- `compliance-gold-eval`

Implementation direction:

- Add `applicability-eval` for deterministic seed packages.
- Add `applicability-gold-eval` for adjudicated real or realistic packages.
- Each eval case must cover:
  - full candidate authority universe;
  - expected package facts;
  - expected retrieval evidence and hard-negative misses;
  - expected graph paths and graph non-paths;
  - expected applicable authorities;
  - expected non-applicable authorities;
  - expected unresolved/adjudication cases when allowed by the fixture;
  - source-record and document-role alignment;
  - package-section alignment;
  - negative evidence and no-trigger rationale;
  - search coverage certificate presence; and
  - generated rule-pack identity and counts.
- Update `phase-eval` to include:
  - `authority_universe`
  - `package_fact_graph`
  - `applicability_retrieval_trace`
  - `applicability_graph_trace`
  - `applicability_determination`
  - `applicability_validation`
  - `generated_rule_pack`
  - then existing compliance phases

Required eval signal:

- Applicability eval fails on false positives, false negatives, missing non-applicable rows, stale
  artifacts, missing coverage certificates, graph trace gaps, and generated-rule-pack mismatch.
- Compliance eval no longer needs to score non-applicable rows as compliance findings.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/applicability_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit eval fixtures, commands, phase gates, docs, and focused tests together.

Stop conditions:

- Applicability eval can pass without checking the non-applicable artifact.
- Phase eval can report reviewer-ready when applicability validation is missing or stale.
- Generated rule-pack coverage is not tied back to applicable-authority decisions.

## Milestone 10: Real-Package Expansion And Operating Runbook

Goal:
Prove the applicability-first architecture on a broader set of real EA packages and document the
operator workflow.

Non-goals:

- Do not claim full Region 1 production readiness from one package.
- Do not add more forest profiles without profile-specific source readiness and eval coverage.
- Do not use model prose as an adjudication substitute.

Relevant files or surfaces:

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- real package intake directories under `source_library/reviews/_intake/`
- applicability and compliance eval artifacts

Implementation direction:

- Select a small real-package set covering:
  - Custer Gallatin;
  - at least one additional Region 1 forest profile once implemented;
  - ESA/NHPA/MBTA/Roadless/wetlands negative and positive cases;
  - missing or ambiguous package evidence;
  - Forest Plan component positives and hard negatives; and
  - authorities with exceptions, dependencies, or supersession relationships.
- Run the full sequence for each package.
- Adjudicate applicability before reviewing compliance.
- Record false positives, false negatives, retrieval misses, graph expansion misses, source gaps,
  ambiguous evidence, and coverage certificate failures.
- Update docs with exact command sequence and current readiness boundary.

Required eval signal:

- At least one package passes the full applicability-first plus compliance-review sequence.
- At least one adjudicated package intentionally fails readiness because applicability remains
  unresolved.
- Metrics report applicability precision/recall, non-applicable correctness, generated rule-pack
  consistency, and downstream compliance review quality separately.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit code/docs/eval fixtures as one milestone slice. Do not stage ignored generated
`source_library/` artifacts unless repository policy changes.

Stop conditions:

- Real-package coverage exposes unadjudicated applicability uncertainty that the system cannot
  represent.
- Operator docs imply generated compliance findings are legal conclusions.
- Forest Plan profile expansion lacks source readiness or validation artifacts.

## Target CLI Sequence

The final operator path should look like this:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id <source-set-id> \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --package-path /path/to/ea-package \
  --output-dir source_library \
  --source-set-id <source-set-id> \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /path/to/ea-package \
  --output-dir source_library \
  --rule-pack source_library/reviews/<review_id>/applicability/generated_rule_pack.json \
  --source-set-id <source-set-id> \
  --review-id <review-id> \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id <review-id>
```

Later implementation may add an orchestration command such as `applicability-run`, but the staged
commands above remain useful because each stage produces reviewable artifacts and can fail closed.

## Completion Definition

This architecture is complete when:

- every candidate authority is represented in the authority universe;
- every candidate authority has predicate, retrieval, graph expansion, dependency/exception, and
  search coverage contracts;
- package facts are represented as a typed, cited, hash-backed graph;
- every applicability decision can be traced to retrieval queries, graph paths, package facts,
  source evidence, coverage certificates, or adjudication;
- every candidate authority has exactly one validated applicability decision;
- applicable authorities and non-applicable authorities are separate durable artifacts;
- unresolved applicability blocks review;
- not-applicable decisions fail without negative evidence, coverage proof, or adjudication;
- generated review rule packs are derived only from validated applicable authorities;
- compliance review refuses reviewer-ready execution without a valid applicability run;
- phase eval includes package fact graph, retrieval trace, graph trace, applicability, coverage,
  and generated-rule-pack gates before compliance gates; and
- real-package evals score applicability quality separately from compliance-review quality.
