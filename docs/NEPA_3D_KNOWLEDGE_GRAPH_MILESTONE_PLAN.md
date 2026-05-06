# NEPA 3D Knowledge Graph Milestone Plan

Date: 2026-05-06

This plan defines the work required to show a full 3D knowledge graph of the USDA and Forest
Service legal, regulatory, policy, forest-plan, and review-risk authority universe that can apply
to Environmental Assessments in USDA Forest Service Region 1.

The 3D graph is a visualization and exploration layer over audited repo artifacts. It must not
become a second legal source of truth. The source of truth remains the workbook, catalog, current
authority inventory, source-set manifests, extraction/retrieval artifacts, evidence graph,
source-claim graph, rule-claim links, applicability artifacts, generated rule packs, and validation
outputs.

## Goal

Build a reviewer-facing 3D knowledge graph that can show:

- every known USDA, Forest Service, Region 1, and project-triggered authority family considered for
  Region 1 EA review;
- every current source record, source artifact, rule template, authority-family template, and
  Forest Plan component candidate represented in the active authority universe;
- which authorities are active, candidate, superseded, out of scope, applicable, not applicable,
  unresolved, or adjudicated;
- how source records, legal authorities, agency policies, forest-plan components, source claims,
  package facts, graph paths, applicability decisions, generated rules, and compliance findings
  connect;
- which source-currentness, supersession, missing-source, adjudication, and real-package expansion
  blockers prevent a broader Region 1 readiness claim.

## Non-Goals

- Do not provide legal advice or turn the graph into a substitute for a qualified NEPA/USFS
  reviewer.
- Do not infer laws, policies, or regulations from model prose, raw filenames, or unverified web
  snippets.
- Do not treat the 3D layout as evidence. It is only a projection of validated graph data.
- Do not mark every authority as applicable. The graph must preserve not-applicable authorities and
  the evidence or coverage certificates that support those determinations.
- Do not bury new domain logic in visualization code. Authority relationships, triggers, source
  evidence requirements, dependencies, exceptions, and supersession links must remain data-backed.
- Do not mix rescinded, revoked, superseded, or reserved source material into the active review
  corpus. Non-current material may be retained only as separate currentness/supersession evidence.
- Do not stage ignored `source_library/` artifacts unless repository policy changes explicitly.

## Current Baseline

The current repo already has the core graph ingredients:

- workbook/catalog coverage for `190` source rows;
- authority-family inventory with `35` families: `33` active, `1` candidate, and `1` superseded;
- `44/44` base rule-pack rules crosswalked to authority families;
- `19` authority-family rule templates for expanded conditional authority coverage;
- reviewer-ready evidence graph and source-claim graph artifacts for
  `source-set-ba8d0feae79501b8`;
- a current expanded authority-universe contract build with `392` candidates:
  `44` base rule-template candidates, `19` authority-family rule-template candidates, and `329`
  Custer Gallatin Forest Plan component candidates;
- promoted V1 applicability artifacts for `v1-cg-ecid-compliance-review` with `373` candidates,
  `33` applicable authorities, `340` not-applicable authorities, no unresolved decisions, and a
  validated generated rule pack;
- post-V1 expansion artifacts for `region1-expansion-ecid-preliminary-ea` with `43` applicable
  authorities, `346` non-applicable authorities, and `3` decisions requiring adjudication.

The largest gap is not whether the repo has graph data. It does. The gap is that the existing graph
layers are fragmented: catalog graph seeds, evidence graph, claim graph, applicability graph traces,
generated rule packs, finding graphs, and authority-family sidecars are separate artifacts. A full
3D NEPA graph needs a normalized export contract and viewer that can join those layers without
weakening the existing gates.

## Full Authority Boundary

"Full" means the bounded USDA/Forest Service Region 1 EA authority universe, not every
environmental law in the United States. The graph must cover at least these authority groups:

- NEPA statute, Fiscal Responsibility Act NEPA amendments, and current CEQ status, guidance, and
  agency-procedure implications;
- USDA NEPA procedures under `7 CFR part 1b`, including EA, FONSI, EIS, categorical exclusion,
  applicant/third-party document, lead/cooperating agency, timing, and emergency-action provisions;
- Forest Service national NEPA directives and guidance, including FSM 1950 and FSH 1909.15, with
  FSH handbook chapters represented as separate source records when they are used by EA review;
- current reserved/superseded status for `36 CFR part 220`, with replacement links to current USDA
  and Forest Service NEPA procedures;
- NFMA and land management planning authorities, including `36 CFR part 219`, project consistency,
  forest-plan components, and Region 1 forest-plan overlays;
- administrative review, objection/appeal, final agency action, and APA-related authority families;
- ESA, NHPA, CWA, CAA, MBTA, BGEPA, floodplain, wetlands, tribal consultation, sacred-site,
  cultural-resource, roadless, wilderness, wild-and-scenic-river, national-trail, invasive-species,
  hazardous-materials, land-exchange, roads/access, special-use, minerals/energy, vegetation,
  wildfire, and state/local permit authority families already represented in the inventory;
- USDA civil-rights, nondiscrimination, Title VI, limited-English-proficiency, and environmental
  justice/civil-rights sources if promoted from candidate status through a scoped workbook/source
  delta;
- Region 1 field directives and unit-specific forest-plan source records when they affect EA
  applicability, source-currentness, package triggers, or forest-plan component review;
- NEPA litigation and review-risk doctrine, including hard look, reasonable alternatives,
  cumulative effects, segmentation, stale science, tiering, mitigation enforceability,
  site-specific analysis, public-comment response, forest-plan consistency, and independent ESA/NHPA
  compliance, to the extent current source records and rule templates support them.

Initial official source anchors that must be reverified at implementation time include the eCFR
current `7 CFR part 1b`, eCFR current `36 CFR part 219`, eCFR current reserved `36 CFR part 220`,
the Forest Service Directives System, Forest Service NEPA Procedures and Guidance, chapter-level
FSH 1909.15 records, FSM 1950, USDA civil-rights directives and regulations, and CEQ NEPA
rulemaking/guidance pages.

Initial anchor URLs:

- `https://www.ecfr.gov/current/title-7/subtitle-A/part-1b`
- `https://www.ecfr.gov/current/title-36/chapter-II/part-219`
- `https://www.ecfr.gov/current/title-36/chapter-II/part-220`
- `https://www.fs.usda.gov/im/directives/`
- `https://www.fs.usda.gov/cgi-bin/Directives/get_dirs/fsh?1909.15=`
- `https://www.fs.usda.gov/about-agency/regulations-policies/manual/1950-environmental-policy-and-procedures`
- `https://www.fs.usda.gov/es/node/758804628`
- `https://www.usda.gov/about-usda/general-information/staff-offices/office-assistant-secretary-civil-rights/policy/directives-and-regulations`
- `https://ceq.doe.gov/laws-regulations/regulations.html`

## Target Invariant

The graph export must be replayable from durable artifacts:

```text
workbook/catalog/source set
  -> source partition check (active corpus versus currentness/supersession archive)
  -> authority inventory/currentness
  -> evidence graph/source claims/rule-claim links
  -> authority universe snapshot
  -> package fact graph
  -> applicability retrieval and graph traces
  -> applicability decisions and validation
  -> generated rule pack
  -> compliance findings and finding graph
  -> normalized 3D knowledge graph export
  -> static or local 3D viewer
```

The viewer cannot promote readiness. Readiness remains controlled by the existing validation,
phase-eval, applicability eval, gold eval, and promotion-suite gates.

## Graph Model

Minimum node types:

- `AuthorityFamily`
- `AuthorityRequirementGroup`
- `Law`
- `Regulation`
- `Policy`
- `ExecutiveOrder`
- `CaseLaw`
- `StateRequirement`
- `ForestPlan`
- `ForestPlanComponent`
- `SourceRecord`
- `SourcePartition`
- `RawArtifact`
- `ExtractedDocument`
- `DocumentSection`
- `DocumentChunk`
- `EvidenceSpan`
- `SourceClaim`
- `Entity`
- `RulePack`
- `RuleTemplate`
- `AuthorityFamilyRuleTemplate`
- `CandidateAuthority`
- `PackageFact`
- `GraphTracePath`
- `RetrievalTrace`
- `SearchCoverageCertificate`
- `ApplicabilityDecision`
- `GeneratedRule`
- `ComplianceFinding`
- `Review`
- `Validation`
- `AdjudicationRecord`
- `ReadinessBlocker`

Minimum edge types:

- `SUPPORTED_BY_SOURCE`
- `BELONGS_TO_SOURCE_PARTITION`
- `CAPTURED_AS_ARTIFACT`
- `EXTRACTED_TO`
- `HAS_CHUNK`
- `HAS_EVIDENCE_SPAN`
- `MENTIONS_ENTITY`
- `EMITS_SOURCE_CLAIM`
- `CLAIM_SUPPORTS_RULE`
- `RULE_DERIVES_FROM_AUTHORITY`
- `CANDIDATE_FOR_FAMILY`
- `REQUIRES_PACKAGE_FACT`
- `TRIGGERED_BY_PACKAGE_FACT`
- `NEGATED_BY_PACKAGE_FACT`
- `USES_RETRIEVAL_TRACE`
- `USES_GRAPH_PATH`
- `HAS_SEARCH_COVERAGE`
- `DECIDED_APPLICABLE`
- `DECIDED_NOT_APPLICABLE`
- `NEEDS_ADJUDICATION`
- `GENERATES_RULE`
- `SUPPORTS_FINDING`
- `SUPERSEDED_BY`
- `REPLACES_RESERVED_AUTHORITY`
- `DEPENDS_ON`
- `HAS_EXCEPTION`
- `HAS_CURRENTNESS_STATUS`
- `BLOCKED_BY`

Every graph node and edge must carry source-set, review, artifact path, artifact hash, source
record, citation label, and generated-at provenance when those fields are available.

## Visual Lenses

The 3D viewer must support these lenses before it is treated as useful:

- Authority universe: all families, rules, templates, source records, candidate status, and
  supersession/currentness status.
- USDA/Forest Service NEPA: NEPA statute, USDA 7 CFR part 1b, Forest Service directives, CEQ
  status/guidance, reserved 36 CFR part 220, and the authority relationships among them.
- Region 1 forest-plan: forest units, profiles, active plans, components, standards, geographic
  areas, management areas, overlays, and source readiness.
- Package applicability: candidate authorities for a selected review colored by applicable,
  not applicable, needs adjudication, unresolved, or adjudicated.
- Evidence path: source record -> artifact -> chunk -> evidence span -> source claim ->
  rule/template -> applicability decision -> generated rule -> compliance finding.
- Readiness blockers: missing source, stale artifact, superseded source, retrieval miss,
  graph trace gap, search coverage gap, adjudication needed, package fixture missing, or forest
  profile not ready.
- Difference view: base V1 universe versus expanded `392`-candidate universe, and promoted V1
  review versus real-package expansion review.

## Milestone 1: Graph Export Contract

Goal:
Define the normalized graph export schema before implementation.

Required outputs:

- `docs/OUTPUT_SCHEMAS.md` section for `nepa_3d_knowledge_graph.json`
- schema examples for node, edge, summary, lens metadata, currentness metadata, and validation
- architecture-contract ownership entry for any new module or CLI command
- test fixtures for the smallest graph slice

Acceptance criteria:

- The schema names every node and edge type used by the 3D graph.
- Required provenance fields are explicit.
- The schema distinguishes graph display status from review readiness.
- The schema supports source-set-level exports and review-specific exports.
- Superseded, reserved, candidate, out-of-scope, active, applicable, not-applicable, unresolved,
  adjudicated, and readiness-blocked states are represented directly.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

## Milestone 2: Authority Source-Currentness And Gap Closure

Goal:
Reconcile the authority graph boundary with current USDA/Forest Service Region 1 EA authority
sources before claiming "full" coverage.

Required outputs:

- source-currentness checklist for official USDA, Forest Service, CEQ, eCFR, Federal Register,
  Region 1, and forest-plan sources;
- scoped workbook/source delta plan for any missing current sources;
- scoped source-partition plan for separating active review-corpus source records from
  rescinded, revoked, superseded, reserved, and currentness-only source records;
- explicit decision for the `environmental_justice_civil_rights` candidate family: promote through
  official Title VI/USDA nondiscrimination sources, keep candidate-blocked, or mark out of scope
  with reviewer-visible rationale;
- explicit graph rules for reserved/superseded `36 CFR part 220` nodes;
- update to `config/authority_universe_families_nepa_ea_v1.json`,
  `config/authority_source_addition_decisions_nepa_ea_v1.json`, and docs only when source evidence
  supports the change.

Acceptance criteria:

- No active authority family depends on revoked, reserved, superseded, excluded, failed, or
  challenge-page source material.
- Rescinded, revoked, superseded, and reserved source material is not part of the active
  review-corpus partition and is available only through separate currentness/supersession records.
- Candidate families remain visible as graph blockers rather than hidden runtime gaps.
- Source additions preserve workbook row identity and pass downloader/catalog/currentness gates.
- Currentness output records source title, citation, URL, effective date when available, capture
  date, supersession status, source record ID, and authority-family ID.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness \
  --output-dir source_library \
  --source-set-id <source-set-id>
git diff --check
```

If workbook/source rows are added, also run the downloader/catalog acceptance gates named in
`DOWNLOADER_RULES.md`.

## Milestone 2A: Source Partitioning And Handbook Chapter Records

Goal:
Make source-record boundaries explicit before graph export work begins, so the graph can show
currentness and supersession without letting non-current material enter the active review corpus.

Implementation status:
Completed on 2026-05-06. `config/source_partition_contract_nepa_3d_v1.json`,
`source_partitions.py`, catalog `source_partition` fields, and expanded `authority-currentness`
validation now implement the pre-graph source boundary. The validator also fails closed when the
contract drops required partitions, lets non-active partitions derive active review rules, omits the
reserved `36 CFR part 220` boundary, or loses the scoped workbook/source-delta plan. The current
source set validates with `189` active review-corpus records and `1` candidate/blocked source. FSH
1909.15 chapter records remain a scoped workbook/source delta before graph export can claim
handbook completeness.

Required outputs:

- source-partition contract that distinguishes at least the active review corpus, the
  currentness/supersession archive, and candidate or blocked-source records that are visible to the
  graph but not eligible for active review rules;
- workbook/source delta plan for moving any existing rescinded, revoked, superseded, or reserved
  material out of the active review corpus while preserving source record IDs, citation labels,
  provenance, capture metadata, and replacement/supersession links;
- separate Forest Service handbook source records for the FSH 1909.15 chapters used by EA review,
  including contents/zero-code records and chapter records such as environmental analysis, EIS,
  EA, and related-document chapters when current official chapter pages are available;
- graph rules that allow archived non-current records to support only `SUPERSEDED_BY`,
  `REPLACES_RESERVED_AUTHORITY`, `HAS_CURRENTNESS_STATUS`, and blocker/currentness relationships,
  not active rule derivation;
- catalog/export validation fixtures for one active USDA NEPA regulation, one reserved/superseded
  Forest Service NEPA regulation, and at least two separate FSH 1909.15 chapter records.

Acceptance criteria:

- Every source record has an explicit `source_partition` or equivalent graph-export field.
- Validation fails if any rescinded, revoked, superseded, or reserved source record is included in
  the active review-corpus partition.
- Validation fails if `36 CFR part 220` or any other reserved/superseded record is treated as an
  active controlling authority rather than a currentness/supersession node.
- Validation fails if FSH 1909.15 is represented only as a single collapsed handbook source when
  chapter-level official records are available and used by EA review.
- The graph can still display non-current records and their replacement relationships, but they are
  visually and semantically separate from current active source records.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness \
  --output-dir source_library \
  --source-set-id <source-set-id>
git diff --check
```

## Milestone 3: Source-Set Knowledge Graph Export Builder

Goal:
Build a read-only export command that joins catalog graph seeds, authority inventory,
currentness, evidence graph, source claims, rule packs, rule-claim links, Forest Plan component
inventory, and authority-family templates into one source-set-level graph.

Candidate command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8
```

Required outputs:

- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph.json`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_nodes.jsonl`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_edges.jsonl`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_summary.json`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_validation.json`

Acceptance criteria:

- The builder reads catalog/reviewer surfaces, not raw artifact filenames.
- The export includes all `35` authority families and all current base-rule and
  authority-family-template candidates.
- The export includes candidate and superseded families even when they are not current active
  review authorities.
- Every edge resolves to existing nodes.
- Source-record, artifact, citation, hash, source-set, and currentness provenance is preserved.
- The export can be regenerated deterministically from existing artifacts.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Milestone 4: Review-Specific Applicability Overlay

Goal:
Add a review overlay that connects the source-set graph to a selected EA package and shows exactly
which authorities were applicable, not applicable, adjudicated, or blocked.

Candidate command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review
```

Required outputs:

- review-specific graph export under
  `source_library/reviews/<review_id>/knowledge_graph/`
- graph links to `authority_universe_snapshot.json`, `package_fact_graph.json`,
  `applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`,
  `applicability_decisions.jsonl`, `search_coverage_certificates.json`,
  `generated_rule_pack.json`, `compliance_matrix.json`, and finding graph artifacts
- status summaries for candidate, applicable, non-applicable, needs-adjudication, unresolved,
  generated-rule, finding, and blocker counts

Acceptance criteria:

- Every candidate authority in `authority_universe_snapshot.json` has a graph node.
- Every decision in `applicability_decisions.jsonl` maps to exactly one candidate authority node.
- Non-applicable decisions stay visible with search coverage or adjudication support.
- Generated rules are linked only from validated applicable decisions.
- Compliance findings link to generated rules and evidence, not directly to arbitrary source text.
- The V1 review export validates cleanly before any broader readiness claim.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
git diff --check
```

## Milestone 5: Region 1 Forest-Plan And Field-Directive Expansion

Goal:
Move from the current Custer Gallatin-heavy proving graph toward a Region 1 graph that can show
forest-plan and field-directive authorities across Region 1 units.

Required outputs:

- source-readiness matrix for Region 1 forests/grasslands and overlays;
- profile-specific source requirements for each added forest profile;
- component inventory build and validation for each added profile before graph promotion;
- graph nodes for forest unit, plan, plan component, management area, geographic area, overlay,
  standard, guideline, desired condition, objective, suitability, and supporting document sources;
- eval fixtures for positive and hard-negative applicability cases across at least one additional
  Region 1 profile.

Acceptance criteria:

- The graph does not claim Region 1 forest-plan completeness from Custer Gallatin artifacts alone.
- Each added profile has source-record readiness, component inventory validation, and
  applicability eval coverage.
- Forest Plan profile expansion remains data-driven and profile-driven; no forest-specific hidden
  code branches are added.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --source-set-id <source-set-id>
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

## Milestone 6: 3D Viewer

Goal:
Create a local 3D viewer that renders the normalized graph export with useful reviewer lenses.

Implementation options:

- a static viewer checked into the repo and pointed at graph export JSON;
- a local dev viewer under a clearly separated `viewer/` or equivalent directory;
- a generated static HTML report under `source_library/visualizations/` for local review.

The final implementation should choose one option and document it. The viewer should use a proven
3D force-graph or Three.js-based library rather than hand-rolling graph physics.

Required controls:

- source set selector;
- review selector;
- lens selector;
- search by authority family, citation, source record, rule ID, component ID, or package fact;
- filters for status, authority category, document role, source currentness, readiness blocker,
  evidence type, forest unit, and review phase;
- click-through detail panel with provenance, artifact hashes, source paths, citations, and
  validation status;
- layout controls for depth, neighbor expansion, pinned nodes, hidden high-degree nodes, and
  exported screenshot/report metadata.

Acceptance criteria:

- The initial view is not a marketing page; it opens directly into the graph experience.
- The graph can render the source-set export and the V1 review overlay without blank canvas or
  unreadable node overlap.
- The viewer defaults to manageable lenses rather than rendering every high-degree evidence edge at
  once.
- Color, labels, and legends distinguish authority category, currentness, applicability status, and
  readiness blockers.
- The UI never implies that a graph edge is a legal conclusion unless the underlying validated
  artifact says so.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
git diff --check
```

If the viewer uses a web runtime, also verify desktop and mobile screenshots plus canvas nonblank
state through the local browser workflow before closeout.

## Milestone 7: Graph Validation And Promotion Gates

Goal:
Make graph completeness and viewer-readiness testable.

Required outputs:

- graph validation command or validation phase in `nepa-knowledge-graph-export`;
- optional `phase-eval` graph phase when review-specific exports are present;
- promotion-suite manifest entries for required graph exports if the graph becomes part of a demo
  readiness claim;
- failure categories for graph-specific blockers.

Required failure categories:

- `graph_missing_authority_family`
- `graph_missing_candidate_authority`
- `graph_missing_source_record`
- `graph_missing_source_partition`
- `graph_missing_currentness_status`
- `graph_missing_applicability_decision`
- `graph_dangling_edge`
- `graph_stale_artifact`
- `graph_noncurrent_document_in_main_corpus`
- `graph_superseded_as_current`
- `graph_handbook_chapter_collapsed`
- `graph_viewer_export_invalid`
- `graph_region1_profile_gap`

Acceptance criteria:

- Validation fails when authority families, candidates, decisions, source records, or currentness
  statuses are missing.
- Validation fails when a superseded/reserved authority is rendered as current active authority.
- Validation fails when a rescinded, revoked, superseded, or reserved source record appears in the
  active review-corpus partition.
- Validation fails when FSH 1909.15 chapter records are collapsed into one source record despite
  chapter-level official records being available and used by EA review.
- Validation reports graph counts by node type, edge type, authority category, source status,
  applicability status, and readiness blocker.
- Promotion can distinguish current V1 graph readiness from broader Region 1 graph readiness.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
git diff --check
```

## Milestone 8: Operating Runbook And Demo Closeout

Goal:
Document the operator path and produce a defensible demo graph for the current V1 review while
making broader Region 1 gaps visible.

Required outputs:

- README entry for graph export and viewer commands;
- `docs/CURRENT_SYSTEM_STATE.md` update once implemented behavior exists;
- `docs/SESSION_HANDOFF.md` update with latest graph readiness and next target;
- runbook section for source-set graph export, review overlay export, viewer launch, validation,
  and screenshot verification;
- demo notes explaining the difference between:
  - current V1 graph readiness;
  - expanded `392`-candidate authority universe graph;
  - Region 1 forest-plan expansion readiness;
  - civil-rights/environmental-justice source gap status;
  - real-package expansion blockers.

Acceptance criteria:

- A reviewer can open the graph and answer: what authorities were considered, what sources support
  them, why each authority is applicable or not applicable, which authorities are blocked, and which
  artifacts prove the graph is current.
- The docs do not claim all Region 1 forest-plan profiles are complete until their source readiness
  and eval artifacts exist.
- The docs do not claim environmental-justice/civil-rights authority coverage is active unless the
  scoped source delta has been implemented and validated.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

## Completion Definition

This milestone plan is complete when:

- the graph export contract exists and is documented;
- a source-set-level graph export validates against current source-set artifacts;
- a review-specific graph overlay validates for `v1-cg-ecid-compliance-review`;
- the 3D viewer renders the graph locally with useful authority, applicability, evidence, and
  blocker lenses;
- current/superseded/candidate/source-gap states are visible rather than hidden;
- broader Region 1 profile and civil-rights/EJ gaps are represented as explicit graph blockers
  until resolved;
- verification gates can fail closed on stale, incomplete, misleading, or non-replayable graph
  exports.

## Commit Policy

Implement this plan as atomic sequence commits. Each sequence should include only the code, tests,
docs, and eval fixtures needed for that sequence. Do not stage unrelated local reports or ignored
generated source-library artifacts.

## Stop Conditions

- A source-currentness question cannot be resolved from official sources.
- A graph export requires scanning raw artifact filenames instead of catalog/review surfaces.
- A graph node or edge cannot carry enough provenance to be replayed.
- A viewer layout suggests legal conclusions that are not present in validated artifacts.
- A Region 1 completeness claim would rely on Custer Gallatin-only forest-plan artifacts.
- New source additions would require broad downloader/corpus reruns outside a scoped source delta.
