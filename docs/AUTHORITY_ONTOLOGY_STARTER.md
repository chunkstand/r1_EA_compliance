# Authority Ontology Starter

Date: 2026-05-15
Status: Phase 0 starter baseline

## Purpose

This artifact turns the ontology research and the canonical-register refoundation
plan into repo-specific starter contracts. It is the semantic baseline for the
future canonical workbook, not a claim that the runtime already enforces the
full ontology.

The starter exists to prevent a common Phase 0 failure mode: treating workbook
rows, downloaded files, legal authorities, sections, scopes, and review
findings as the same thing. In this repo they are not the same thing, and the
ontology must keep them separate.

## Starter Assumptions

- `Document_Register_Master` will become the only canonical load table.
- A workbook row is provenance and capture governance, not the authority object
  an agent reasons over.
- Legal currentness, supersession, and scope must remain explicit data, not
  inferred only from document titles or URLs.
- The graph must stay reviewer-visible and agent-legible: every important
  semantic relationship needs typed provenance and later eval coverage.
- This starter is JSON-contract-first so it can be versioned in the repo now.
  A later Protégé or OWL export may be derived from the same contracts.

## Competency Questions

1. Which authority document, expression, or section controls a review finding?
2. What lower-level regulation, directive, handbook, or forest plan implements
   or interprets a higher-level authority?
3. Which authority version was current on the review date?
4. Which forest plan component operationalizes a higher-level authority for a
   specific forest unit?
5. Which supporting forest-plan document provides evidence for a component or
   amendment?
6. Which source record, artifact, and evidence span prove a semantic
   relationship?
7. Which aliases normalize to the same authority identity, and which aliases
   must stay unresolved until more context exists?
8. Within what jurisdiction, forest unit, project scope, or resource topic does
   a given authority apply?
9. Which sources remain historical or currentness-only and must not be treated
   as controlling review authority?
10. What authority path and justification path support a generated rule,
    compliance finding, or draft section?

## Core Modeling Rule

The repo needs a five-layer chain:

`authority_family -> authority_document/version -> authority_fragment or forest_plan_component -> source_record/artifact/evidence_span -> review reasoning object`

If the system collapses these layers, the agent loses the ability to explain
why a document matters, what authority it belongs to, whether it is current,
and which evidence actually supports a finding.

## Class Model

- `authority_family`: normalized legal or policy family already tracked in
  `config/authority_universe_families_nepa_ea_v1.json`
- `authority_document`: the legal or policy resource the agent reasons about
- `authority_expression`: a dated or versioned expression of an authority
  document
- `authority_fragment`: a cited fragment, appendix, chapter, or appendix-like
  component of an authority expression
- `authority_section`: a structured section-level fragment
- `forest_plan`: a forest-plan authority document
- `forest_plan_component`: a standard, guideline, desired condition, suitability
  statement, or mapped component anchored in a forest plan
- `jurisdiction_scope`: the scope boundary within which an authority applies
- `issuer`: the body that issued an authority document or expression
- `forest_unit`: a specific Region 1 forest or grassland
- `source_record`: a canonical workbook or catalog source row
- `source_artifact`: a captured file or page with hash-backed provenance
- `evidence_span`: a deterministic chunk/span used for retrieval and review
- `review`: a package-specific review overlay
- `applicability_decision`: a package-specific applicability outcome
- `generated_rule`: a rule derived from applicable authorities
- `compliance_finding`: a citation-bearing review finding
- `authority_path`: a reviewer-visible path from governing authority to lower
  authority or component
- `justification_path`: a reviewer-visible path from authority to evidence to
  review output

## Key Separation Rules

- `source_record` is never the same class as `authority_document`.
- `source_artifact` is never the same class as `authority_expression`.
- `evidence_span` is never the same class as `authority_fragment`.
- Review reasoning objects are not authority objects.
- `forest_plan_component` is a semantic object anchored in a forest plan, not a
  raw source row.

## Key Object Properties

- `belongsToFamily`
- `issuedBy`
- `hasExpression`
- `isExpressionOf`
- `hasFragment`
- `isFragmentOf`
- `hasComponent`
- `appliesWithinScope`
- `governsForestUnit`
- `capturedBySourceRecord`
- `hasArtifact`
- `hasSourceRecord`
- `hasEvidenceSpan`
- `hasSourceArtifact`
- `hasReview`
- `hasAuthorityPath`
- `hasJustificationPath`
- `supportsFinding`

The ontology starter keeps legal relationships such as `IMPLEMENTS`,
`INTERPRETS`, `SUPERSEDES`, `REQUIRES_CONSISTENCY_WITH`, and
`SUPPORTS_FOREST_PLAN_COMPONENT` in the separate relationship-type contract so
that relationship vocabularies can evolve independently from the class
hierarchy.

## Starter Manchester Axioms

```text
AuthorityExpression SubClassOf isExpressionOf exactly 1 AuthorityDocument
AuthoritySection SubClassOf AuthorityFragment
ForestPlan SubClassOf AuthorityDocument
ForestPlanComponent SubClassOf AuthorityFragment
SourceArtifact SubClassOf hasSourceRecord exactly 1 SourceRecord
EvidenceSpan SubClassOf hasSourceArtifact exactly 1 SourceArtifact
ApplicabilityDecision SubClassOf hasReview exactly 1 Review
GeneratedRule SubClassOf hasReview exactly 1 Review
ComplianceFinding SubClassOf hasReview exactly 1 Review
AuthorityDocument DisjointWith SourceRecord
AuthorityExpression DisjointWith SourceArtifact
AuthorityFragment DisjointWith EvidenceSpan
Review DisjointWith AuthorityDocument
```

## Repo Projection

### Existing Repo Surfaces

- `config/authority_universe_families_nepa_ea_v1.json` already owns
  `authority_family`.
- `config/source_partition_contract_nepa_3d_v1.json` already owns major
  currentness and partition boundaries.
- `config/nepa_3d_graph_contract_v1.json` already owns many provenance-layer
  node types such as `source_record`, `artifact`, `evidence_span`, `review`,
  `applicability_decision`, `generated_rule`, `compliance_finding`,
  `forest_plan`, and `forest_plan_component`.

### New Starter Contracts

- `config/authority_document_ontology_v1.json`: class and property baseline
- `config/authority_relationship_types_v1.json`: allowed legal/policy edge
  vocabulary
- `config/authority_relationship_register_v1.json`: schema for curated
  relationship rows plus starter examples
- `config/citation_alias_register_v1.json`: alias and ambiguity baseline
- `config/jurisdiction_scope_register_v1.json`: jurisdiction and scope baseline
- `config/authority_ontology_eval_v1.json`: ontology integrity starter gates
- `config/authority_relationship_eval_v1.json`: relationship integrity starter
  gates

### Future Canonical Workbook Projection

- every load-ready row creates exactly one `source_record`
- curated identity fields later create `authority_document_id` and
  `authority_expression_id`
- section-aware or component-aware rows later create `authority_fragment_id` or
  `forest_plan_component_id`
- scope-bearing rows later bind to `jurisdiction_scope_id`
- every semantic relationship later cites one or more `source_record_id`
  values as provenance

## Explicit Non-Goals

- This starter does not claim the full ontology is already enforced in runtime
  code.
- This starter does not load live workbook relationships into the graph yet.
- This starter does not replace currentness, graph, or retrieval evals.
- This starter does not attempt a full legal-rule language. Normative rules stay
  downstream in rule packs and review artifacts.
- This starter does not silently activate example relationship rows. Curated
  production rows belong in `rows`, while starter examples stay isolated under
  `starter_rows`.

## Next Implementation Use

Use this starter as the baseline for:

1. `source_register_schema_v1.json` field design
2. canonical `authority_document_id` and `authority_expression_id` strategy
3. `authority-ontology-validate` and `authority-relationship-eval`
4. the Phase `1.5` mixed proving slice
5. graph export upgrades that add authority, currentness, scope, and
   justification-path semantics
