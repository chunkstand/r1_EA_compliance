# USFS Region 1 EA Sources

Local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA Forest Service Region 1
source material.

The workbook is the source-of-truth input for the knowledge base. The system captures the full
canonical workbook source set into a local, auditable source library, then builds derived extraction,
retrieval, evidence graph, source-claim graph, rule-claim binding, and deterministic EA package
review artifacts on top of that corpus.

Current workbook source contract:

- Workbook: `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx`
- `Ingest_Checklist` ingest rows: `162`
- `Scope=Baseline` rows that must be evaluated in every EA compliance review: `26`
- `Scope=Conditional` rows loaded for trigger-based review: `136`
- `R1_Forest_Plans` unit/overlay rows: `28`

Current generated source-library capture:

- Run ID: `corpus-update-2026-05-01-cg-support-batches`
- Workbook rows covered: `190`
- Batch result: `52/52` batches passed
- Repair queue: empty except header
- Unique workbook/effective URLs: `172`
- Unique raw artifacts in reviewer catalog: `160`
- Source-to-artifact links: `189`
- Status counts: `downloaded=8`, `downloaded_existing=170`, `duplicate_content=2`,
  `duplicate_url=9`, `skipped_excluded=1`

The current catalog source set is `source-set-ba8d0feae79501b8`. The latest corpus update added the
Custer Gallatin FEIS Volume 1, FEIS Volume 2, Biological Assessment, and Biological Opinion as
forest-plan supporting records beside the 2022 Custer Gallatin Land Management Plan and ROD. The
Custer Gallatin forest-plan resolver now requires the planning page, LMP, ROD, FEIS Volumes 1 and 2,
Biological Assessment, and Biological Opinion to be present in the retrieval index before it reviews
a Custer Gallatin EA. Full all-source extraction, retrieval, evidence graph, source-claim,
rule-claim, compliance coverage, compliance-review eval, compliance-gold eval, and phase-eval
artifacts have been promoted for this source set. The source-set Custer Gallatin Land Management
Plan component inventory has also been generated from current chunks with `329` components, `58`
standards, passing build coverage, and `2` inventory-quality warnings for suppressed
component-like labels with nonnumeric number tokens. Older reviewer-ready downstream artifacts under
`source-set-e364ea220cffd938` remain useful only as prior 147-row evidence.

The East Crazy Inspiration Divide V1 EA gate is promoted for review ID
`v1-cg-ecid-compliance-review`: the regenerated compliance review is reviewer-ready, evaluates all
`26` baseline source records through the generated applicability rule pack, validates a
`373`-candidate authority universe with `33` applicable and `340` non-applicable authorities,
emits `33` generated compliance findings, applies `12/12` Custer Gallatin standards, passes
review-bound `phase-eval` `17/17` with the post-V1 applicability and decision-support gates
included, passes
`v1-ea-eval` with broader EA and forest-plan lanes true, and keeps `14` conditional adjudication
rows as explicit accepted V1 reviewer risk.

Authority-universe completion Milestones 1 through 4 are now represented by
`config/authority_universe_families_nepa_ea_v1.json`,
`config/authority_source_addition_decisions_nepa_ea_v1.json`,
`config/source_partition_contract_nepa_3d_v1.json`,
`config/authority_family_rule_templates_nepa_ea_v1.json`,
`config/authority_family_rule_template_coverage_nepa_ea_v1.json`,
`config/applicability_eval_seed.json`, `config/applicability_gold_eval_v0.json`, the expanded
applicability fixture under `config/fixtures/applicability/`, and the `authority-currentness`
command. The inventory has `35` authority families, `18` required authority
requirement groups, `33` active families, all `44/44` current rule-pack rules crosswalked, and all
`190/190` workbook source records mapped to an authority family. The currentness gate validates
`source-set-ba8d0feae79501b8` with `207` family/source currentness records, `33` source-currentness
confirmed families, `1` documented candidate non-addition, `1` superseded replacement-source
confirmation, `21` Milestone 2 families closed or documented, and `0` failed families. The NEPA 3D
Milestone 2A source-partition contract is now implemented: the catalog/currentness surfaces
distinguish active review-corpus, currentness/supersession archive, and candidate/blocked-source
records; the live catalog partitions are `189` active review-corpus records and `1` candidate or
blocked source; the contract itself now validates required partitions, graph-rule limits, reserved
`36 CFR part 220` boundaries, and scoped workbook/source deltas; and reserved/superseded authority
fixtures plus FSH 1909.15 chapter-collapse fixtures fail closed before graph export work can rely on
them. NEPA 3D Milestone 1 now defines the source-set/review graph export contract in
`config/nepa_3d_graph_contract_v1.json` with fixture-backed validation for node and edge types,
display status, review readiness, required provenance, edge endpoint compatibility, lens metadata,
and readiness blockers. NEPA 3D Milestone 3 now adds the read-only
`nepa-knowledge-graph-export` source-set builder. The live export for
`source-set-ba8d0feae79501b8` passes `61` validation checks with `1,410` nodes, `2,564` edges, all
`35` authority families, all `190` catalog source records, all `44` base rules, all `19`
authority-family templates, `191` rule-claim links, and `329` forest-plan components. NEPA 3D
Milestone 4 now adds the review-specific overlay for `v1-cg-ecid-compliance-review`: the export
under `source_library/reviews/<review_id>/knowledge_graph/` passes `75` validation checks with
`1,916` nodes, `3,442` edges, `373` candidate authorities/decisions, `33` generated rules and
compliance findings, `340` non-applicable authorities with search coverage, and explicit validation
that review artifact, search-coverage, retrieval-trace, and graph-trace references resolve. NEPA 3D
Milestone 5 now adds the Region 1 forest-plan readiness matrix and first added profile contract:
the source-set graph tracks `10` Region 1 forest/grassland profiles, keeps `1` Custer Gallatin
profile graph-ready, blocks `9` broader Region 1 profiles from completeness claims, adds the
Beaverhead-Deerlodge profile with catalog-confirmed planning page/LMP sources plus positive and
hard-negative applicability fixture contracts, renders `3` field-directive requirements and `5`
overlay requirement groups as graph-visible nodes with source links, and leaves component inventory
validation as a reviewer-visible blocker before graph promotion. NEPA 3D Milestone 6 now adds the
checked-in local viewer under `viewer/nepa-3d/`; it opens directly into the graph experience, reads
the normalized source-set and review overlay JSON exports, defaults to the
`v1-cg-ecid-compliance-review` demo review with scene buttons above Lens, and keeps
validation/readiness status tied to the exported artifacts rather than viewer layout while tests
lock the `node_id` and edge-endpoint mapping needed by the 3D runtime. The viewer
dropdown gap passes separate authority category from authority family, split node/edge type from
evidence/basis semantics, read forest-unit values from exported forest codes, ground lens and filter
options with graph-export counts, treat filter selections as context seeds instead of strict
edge-endpoint requirements, add a Clear filters action, and live sweep source-set/review dropdown
selections so populated options no longer blank the graph. A demo-mode pass now adds one-click
scene buttons for source library, authority graph, applicability, evidence path, forest plan,
readiness, and full graph views; the evidence-path scene derives a clickable source-to-finding
spotlight from the graph itself, and a right-side Capability shown panel keeps demo claims grounded
in rendered graph counts. The graph surface now adds human-readable scene labels plus graph-native
node labels: zoomed-out views show scene anchors, mid-zoom adds focus labels, and close zoom adds a
larger set of node labels without changing the validated graph data. Advanced search and category
filters remain available under a visually subordinate Advanced filters disclosure. A generated
4-page service capabilities brief now lives at `docs/capabilities/nepa_3d_capabilities_brief.pdf`
with graph figures that frame USFS Region 1 as the current implementation evidence for reviewing
NEPA document packages, authority graph updates with the most current applicable regulations and
procedures,
reverse compliance, source-to-finding traceability,
Forest Plan and full profile consistency review, responsible-official decision support, and
readiness blockers from the validated V1 graph export. The earlier
authority-universe Milestone 3 adds
`19` data-backed authority-family rule templates with positive/negative trigger contracts,
source evidence requirements, retrieval/graph contracts, and coverage rows. Milestone 4 adds
independent applicability eval and gold-adjudication coverage for those expanded families: seed evals
now score positive and negative coverage for all `19` high-priority authority-family templates, a
realistic Region 1 land-exchange fixture exercises land exchange, water/wetlands, cultural/tribal,
wildlife/species, designated-area, and forest-plan consistency triggers, and gold evals include
unresolved and replay-adjudicated authority-family decisions. The next authority-universe work is
now complete: reviewer-facing compliance outputs carry authority-family provenance,
non-applicable authority appendices, reviewer-resolution status, and deterministic litigation-risk
categories tied to evidence artifacts.

See `docs/CURRENT_SYSTEM_STATE.md` for the current architecture, storage model, and reviewer-engine
read path. See `docs/ARCHITECTURE.md` and `docs/architecture_contract.toml` for the architecture
map, layer ownership, generated-artifact ownership, command groups, and automated architecture gate.
See `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md` for the canonical V1 system plan: a Custer
Gallatin National Forest EA compliance review as the proving ground. See
`docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` for the post-V1 plan that makes authority
applicability, non-applicability, validation, and generated rule packs first-class pre-review
artifacts. See `docs/AUTHORITY_UNIVERSE_COMPLETION_MILESTONE_PLAN.md` for the current completion
milestone that expands the bounded authority-family inventory beyond the V1 proving path. See
`docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md` for the planned graph-export and 3D visualization
sequence covering USDA/Forest Service Region 1 EA authority families, applicability, evidence, and
readiness blockers. See
`docs/EA_CONSISTENCY_DECISION_SUPPORT_MILESTONE_PLAN.md` for the East Crazies decision-support
report sequence; Sequence 5 has closed the milestone by making the generated East Crazies
JSON/Markdown/PDF decision-support report family both gate-checked and supervisor-readable while
keeping the ignored outputs under the review `decision_support/` directory. See
`docs/OUTPUT_SCHEMAS.md` for the upstream `project-sow-package` contract that converts a structured
proposed-action intake into resource SOW requirements and, for the East Crazies calibration fixture,
compares proposed-action resource areas to the actual specialist/supporting reports produced. See
`docs/POST_V1_PROMOTION_SUITE.md` for the manifest-driven promotion-suite runbook. See
`docs/BITTER_LESSON_ALIGNMENT.md` for the design guardrails that keep the reviewer engine biased
toward scalable search, learning, evidence, and eval loops instead of hidden domain-specific
heuristics.

## Current Inputs

- `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx`
- `DOWNLOADER_RULES.md`
- `config/downloader.toml`
- `config/url_overrides.toml`
- `config/retrieval_eval_seed.json`
- `config/claim_eval_seed.json`
- `config/rule_claim_link_eval_seed.json`
- `config/applicability_eval_seed.json`
- `config/applicability_gold_eval_v0.json`
- `config/fixtures/applicability/region1-land-exchange-expanded-authority.txt`
- `config/compliance_review_eval_seed.json`
- `config/compliance_gold_eval_v0.json`
- `config/compliance_rule_pack_coverage_nepa_ea_v0.json`
- `config/authority_family_rule_templates_nepa_ea_v1.json`
- `config/authority_family_rule_template_coverage_nepa_ea_v1.json`
- `config/authority_universe_families_nepa_ea_v1.json`
- `config/authority_source_addition_decisions_nepa_ea_v1.json`
- `config/source_partition_contract_nepa_3d_v1.json`
- `config/nepa_3d_graph_contract_v1.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/ea_consistency_decision_support_v1.json`
- `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
- `config/project_sow_resource_scopes_v1.json`
- `config/fixtures/project_sow/east_crazies_land_exchange_intake.json`
- `config/ea_review_checklist_seed.json`
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/forest_plan_profiles.json`
- `config/forest_plan_component_inventory_seed.json`
- `config/forest_plan_component_eval_seed.json`
- `config/v1_ecid_real_ea_eval.json`
- `config/promotion_suite_v1.json`

## Stored Data

Generated outputs are written under `source_library/` and ignored by git:

- Raw downloaded artifacts: `source_library/artifacts/raw/`
- Row manifests: `source_library/manifests/download_<run_id>.jsonl`
- Batch ledgers and reports: `source_library/runs/<run_id>/`
- Reviewer catalog: `source_library/catalog/source_catalog.jsonl`
- Reviewer SQLite index: `source_library/catalog/review_sources.sqlite`
- Source-set manifest: `source_library/catalog/source_set_manifest.json`
- Graph seed files:
  - `source_library/catalog/source_graph_nodes.jsonl`
  - `source_library/catalog/source_graph_edges.jsonl`
- Derived extraction outputs: `source_library/derived/<source_set_id>/`
- Authority currentness outputs:
  - `source_library/derived/<source_set_id>/authority_currentness/authority_currentness_report.json`
- Retrieval index and eval outputs:
  - `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
  - `source_library/derived/<source_set_id>/retrieval/retrieval_manifest.json`
  - `source_library/derived/<source_set_id>/retrieval/retrieval_validation.json`
  - `source_library/derived/<source_set_id>/retrieval/retrieval_eval_results.json`
- Document evidence graph outputs:
  - `source_library/derived/<source_set_id>/evidence_graph/document_graph_nodes.jsonl`
  - `source_library/derived/<source_set_id>/evidence_graph/document_graph_edges.jsonl`
  - `source_library/derived/<source_set_id>/evidence_graph/evidence_graph.sqlite`
  - `source_library/derived/<source_set_id>/evidence_graph/evidence_graph_validation.json`
  - `source_library/derived/<source_set_id>/evidence_graph/phase_eval_results.json`
- NEPA 3D knowledge graph outputs:
  - `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph.json`
  - `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_nodes.jsonl`
  - `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_edges.jsonl`
  - `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_summary.json`
  - `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_validation.json`
  - `source_library/reviews/<review_id>/knowledge_graph/nepa_3d_graph.json`
- NEPA 3D static viewer:
  - `viewer/nepa-3d/index.html`
  - `viewer/nepa-3d/manifest.json`
  - `viewer/nepa-3d/app.js`
  - `viewer/nepa-3d/styles.css`
- NEPA 3D service capabilities brief:
  - `docs/capabilities/nepa_3d_capabilities_brief.pdf`
  - `docs/capabilities/nepa_3d_capabilities_brief.html`
  - `docs/capabilities/assets/graph_applicability_service_view.png`
  - `docs/capabilities/assets/graph_evidence_trace_service_view.png`
  - `docs/capabilities/assets/graph_readiness_service_view.png`
  - `tools/build_nepa_3d_capabilities_brief.mjs`
- Source claim graph outputs:
  - `source_library/derived/<source_set_id>/claims/claims.jsonl`
  - `source_library/derived/<source_set_id>/claims/entities.jsonl`
  - `source_library/derived/<source_set_id>/claims/claim_graph_nodes.jsonl`
  - `source_library/derived/<source_set_id>/claims/claim_graph_edges.jsonl`
  - `source_library/derived/<source_set_id>/claims/claim_graph.sqlite`
  - `source_library/derived/<source_set_id>/claims/claim_validation.json`
- Rule-claim binding outputs:
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_links.jsonl`
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_link_gaps.jsonl`
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_links.sqlite`
  - `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/rule_claim_link_validation.json`
- Forest-plan component inventory outputs:
  - `source_library/derived/<source_set_id>/forest_plan_components/component_inventory.json`
  - `source_library/derived/<source_set_id>/forest_plan_components/component_inventory_build_coverage.json`
  - `source_library/derived/<source_set_id>/forest_plan_components/components.jsonl`
  - `source_library/derived/<source_set_id>/forest_plan_components/summary.json`
- Project SOW requirements package outputs:
  - `source_library/projects/<project_id>/requirements_package/project_sow_package.json`
  - `source_library/projects/<project_id>/requirements_package/project_sow_package.md`
  - `source_library/projects/<project_id>/requirements_package/project_sow_package_manifest.json`
- EA package review outputs:
  - `source_library/reviews/<review_id>/package/package_manifest.jsonl`
  - `source_library/reviews/<review_id>/package/package_chunks.jsonl`
  - `source_library/reviews/<review_id>/review_validation.json`
  - `source_library/reviews/<review_id>/review_report.json`
  - `source_library/reviews/<review_id>/review_report.md`
  - `source_library/reviews/<review_id>/compliance_validation.json`
  - `source_library/reviews/<review_id>/compliance_review.json`
  - `source_library/reviews/<review_id>/compliance_matrix.json`
  - `source_library/reviews/<review_id>/compliance_matrix.md`
  - `source_library/reviews/<review_id>/compliance_matrix.pdf`
  - `source_library/reviews/<review_id>/authority_family_provenance.json`
  - `source_library/reviews/<review_id>/non_applicable_authority_appendix.json`
  - `source_library/reviews/<review_id>/non_applicable_authority_appendix.md`
  - `source_library/reviews/<review_id>/authority_reviewer_resolution_report.json`
  - `source_library/reviews/<review_id>/litigation_risk_summary.json`
  - `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
  - `source_library/reviews/<review_id>/finding_graph_edges.jsonl`
  - `source_library/reviews/<review_id>/forest_plan_context.json`
  - `source_library/reviews/<review_id>/forest_plan_context_validation.json`
  - `source_library/reviews/<review_id>/forest_plan_context_summary.json`
  - `source_library/reviews/<review_id>/forest_plan_component_findings.json`
  - `source_library/reviews/<review_id>/forest_plan_component_findings.md`
  - `source_library/reviews/<review_id>/forest_plan_reviewer_resolution_queue.json`
  - `source_library/reviews/<review_id>/forest_plan_component_inventory_coverage.json`
  - `source_library/reviews/<review_id>/forest_plan_applicable_standard_coverage.json`
  - `source_library/reviews/<review_id>/forest_plan_component_eval_results.json`
  - `source_library/reviews/<review_id>/v1_ea_eval_results.json`
- Applicability-first review outputs, defined as the post-V1 pre-review contract:
  - `source_library/reviews/<review_id>/applicability/authority_universe_snapshot.json`
  - `source_library/reviews/<review_id>/applicability/package_fact_graph.json`
  - `source_library/reviews/<review_id>/applicability/package_applicability_context.json`
  - `source_library/reviews/<review_id>/applicability/package_fact_graph_validation.json`
  - `source_library/reviews/<review_id>/applicability/applicability_retrieval_trace.jsonl`
  - `source_library/reviews/<review_id>/applicability/applicability_graph_trace.jsonl`
  - `source_library/reviews/<review_id>/applicability/applicability_retrieval_graph_diagnostics.json`
  - `source_library/reviews/<review_id>/applicability/applicability_decisions.jsonl`
  - `source_library/reviews/<review_id>/applicability/applicable_authorities.json`
  - `source_library/reviews/<review_id>/applicability/non_applicable_authorities.json`
  - `source_library/reviews/<review_id>/applicability/search_coverage_certificates.json`
  - `source_library/reviews/<review_id>/applicability/applicability_validation.json`
  - `source_library/reviews/<review_id>/applicability/applicability_provenance.json`
  - `source_library/reviews/<review_id>/applicability/applicability_report.md`
  - `source_library/reviews/<review_id>/applicability/generated_rule_pack.json`
  - `source_library/reviews/<review_id>/applicability/generated_rule_pack_validation.json`
- Compliance review eval outputs:
  - `source_library/reviews/compliance_review_eval/compliance_review_eval_results.json`
  - `source_library/reviews/compliance_review_eval/packages/<case_id>.txt`
  - `source_library/reviews/compliance_review_eval/reviews/<case_id>/`
- Compliance gold eval outputs:
  - `source_library/reviews/compliance_gold_eval/compliance_gold_eval_results.json`
  - `source_library/reviews/compliance_gold_eval/adjudicated_cases.compliance_review_eval.json`
  - `source_library/reviews/compliance_gold_eval/compliance_review_eval/`
- Promotion suite outputs:
  - `source_library/reviews/promotion_suite/<suite_id>/promotion_suite_results.json`
  - `source_library/reviews/promotion_suite/<suite_id>/promotion_suite_report.md`

The raw artifacts are not semantic chunks. They are source bytes plus provenance. The
`authority-currentness` command validates the authority-family inventory against the catalog source
set before candidate or template-backed authority families are promoted. The `extract-build` command
builds a derived text/chunk layer from the catalog. The
`retrieval-build` command turns those chunks into a queryable local evidence index. The
`evidence-graph-build` command promotes document, chunk, evidence-span, topic, parser, and artifact
links into a local graph artifact. The `claim-extract` command extracts deterministic source-text
claims and entities with exact offsets and graph bindings. The `rule-claim-link` command binds
versioned compliance rules to validated source claims before compliance findings rely on those
authorities. The `ea-review` command runs deterministic package checklist reviews against
reviewer-ready retrieval evidence. The `forest-plan-resolve` command extracts forest-plan review
context from an EA package using the selected profile in `config/forest_plan_profiles.json`; the
first profile is Custer Gallatin. It resolves project location signals, geographic areas,
management areas, overlays, and source-library plan evidence, then routes triggered package cues to
profile-declared supporting records such as the Custer Gallatin ROD, FEIS Volumes 1 and 2,
Biological Assessment, and Biological Opinion. Supporting routes are trigger-gated and report
`trigger_evidence` so reviewers can see why a supporting record was applied. The `compliance-review`
command invokes the forest-plan resolver against the same package cache, requires reviewer-ready
forest-plan component evaluation for Custer Gallatin packages, and identifies applicable
statutory, regulatory, policy, state, executive-order, and forest-plan authorities from a versioned
rule pack, evaluates the EA against each applicable authority, and emits a compliance matrix plus
finding graph with source-claim support. The `v1-ea-eval` command scores the current East Crazy
Inspiration Divide real EA review against the V1 contract, including the explicit pending
conditional-adjudication policy. The `compliance-gold-eval` command runs the 10-case adjudication
promotion gate. The `promotion-suite` command checks manifest-declared readiness evidence for the
current V1 review and post-V1 expansion slots. The active compliance rule pack is `0.4.0`: it
declares the 26 workbook `Scope=Baseline` source records explicitly and contains 44 total authority
rules.

The post-V1 applicability-first contract moves authority applicability into a pre-review artifact
family under `source_library/reviews/<review_id>/applicability/`: candidate authorities are
snapshotted, package facts are graphed, per-authority retrieval and graph expansion traces are
persisted, applicable and non-applicable authorities are separate artifacts, not-applicable decisions
carry search coverage or adjudication, validation blocks unresolved or stale decisions, and the
downstream review rule pack is generated from the validated applicable-authorities artifact. The
implemented staged path now includes `applicability-authority-universe`,
`applicability-context-build`, `applicability-retrieve`, `applicability-determine`,
`applicability-validate`, replayable applicability adjudication template/apply/eval commands,
`applicability-generate-rule-pack`, generated-pack validation, and reviewer-ready
`compliance-review` gating on the generated rule pack. The promoted V1 review now uses the
generated applicability rule pack; the base rule pack remains the candidate-authority template and
can only be used for explicit non-reviewer-ready diagnostics. The ECID preliminary-EA expansion pass
has replayed the three pending applicability adjudications and now validates with `46` applicable
authorities, `346` non-applicable authorities, no unresolved or `needs_adjudication` decisions, and
`generated_rule_pack_ready=true`. The ECID generated rule pack now validates with `46` rules, the
generated rule-claim binding has `211` links and `0` gaps, and the Forest Plan component
adjudication eval resolves the current `158`-row queue as true EA package-evidence omissions with
`0` system misses. ECID compliance review and review-scoped phase eval are reviewer-ready; broader
strict expansion is now blocked by the South Plateau six-item applicability adjudication worklist.

## Reviewer Engine Entry Points

The EA review engine should start from one of these catalog surfaces rather than scanning filenames:

- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`

Forest-plan improvement work uses sequence discipline: each implemented forest-plan sequence must
update repo docs, pass focused verification, and be committed before the next sequence begins.

For each selected source row, the engine should:

1. Read the source metadata from SQLite or `source_catalog.jsonl`.
2. Open `artifact_path`.
3. Recompute SHA256 and byte size before parsing.
4. Choose a parser using `expected_parser` and `content_type`.
5. Attach `source_record_id`, `artifact_sha256`, `citation_label`, URL provenance, and page/section offsets to every extracted chunk.

The catalog graph JSONL files are source metadata graph seeds. They link sources to artifacts,
authorities, review topics, applicability, and related reviewer concepts. The derived evidence graph
adds document, chunk, evidence-span, parser, and topic nodes. The source claim graph adds extracted
claim, entity, authority, and claim-evidence-span nodes. The rule-claim binding layer links
compliance rules to validated claim nodes without generating legal conclusions. No graph layer stores
embeddings or trusted model-generated compliance conclusions.

Forest-plan component evaluation is a default part of `forest-plan-resolve` for packages resolved to
the selected forest-plan profile. The resolver uses a source-set component inventory when present and
falls back to `config/forest_plan_component_inventory_seed.json`; `--forest-plan-component-inventory-path`
only overrides the inventory path. The evaluator writes component findings and a reviewer-resolution
queue; supported/partial findings require both package evidence and plan-source evidence from the
component inventory's source chunk binding, while source-set drift and missing package evidence
become reviewer work. The first NFMA coverage gate also writes selected-inventory coverage and
applicable-standard coverage artifacts, and reviewer-ready status fails when an applicable standard
lacks plan-source evidence, package evidence, or a resolved compliance status. The current source-set
inventory for the 2022 Custer Gallatin LMP is generated from extracted chunks and has passing build
coverage; the seed inventory is now only a fallback/test fixture.

The applicable-standard gate also reads explicit EA package plan-consistency table rows keyed by
component code, including extraction variants such as `FW-STD-FAC -01` and
`FW-STD-ROSSPNM- 01`. A `Yes` row supplies package evidence and the reviewed EA section when
present; a `No` row marks the standard not applicable with citation-bearing package evidence.
Malformed table rows with an empty component-code cell can still bind when the row's component text
matches the LMP component text. Standards excluded by resolved project context still retain an LMP
component binding and plan-source citation so the coverage table is auditable instead of silently
dropping source context. Affirmative Plan Consistency Table rows are now marked as explicit
component-row section bindings, and supported findings fail validation when package evidence has a
missing or mismatched section binding outside those explicit table determinations.

Component package retrieval is section-aware. Queries are built from the component code, component
text, resource topics, activity tags, geography/management context, and mandatory/prohibitive terms;
candidate package evidence is then bound to a package section family such as hydrology, wildlife,
botany, scenery, sustainability, recreation/access, land exchange, minerals, or general EA.
Non-standard components use stricter section binding: outside explicit Plan Consistency Table rows,
desired conditions, goals, guidelines, objectives, and suitability components require a matching EA
package section family and substantive component terms before package evidence can support the
finding. Negative plan-consistency determinations and absence statements such as `not part of the
project area`, `no ... in the parcels`, or `outside of <area/overlay>` suppress false-applicable
context unless the package also contains affirmative location evidence. Restrictive recreation/access
standards can also bind to proposed trail or route evidence that explicitly supports
nonmotorized/no-motorized use, so standards written as prohibitions do not require the EA to repeat
the plan's exact phrasing.

`forest-plan-component-eval` scores the current forest-plan review against adjudicated
component-level cases in `config/forest_plan_component_eval_seed.json`. The eval measures component
applicability precision/recall, applicable-standard recall, false-applicable component rate,
package-section match rate, plan-source citation correctness, package-evidence citation
correctness, resolved compliance-status rate, and reviewer-resolution closure rate. This is the
feedback loop for improving forest-plan accuracy across runs; it fails closed when package evidence,
plan citations, section bindings, applicability, compliance status, reviewer-resolution state, or
the identity of any consumed review artifact drifts from the adjudicated contract. The current seed
also carries coverage requirements so it fails if the cases no longer cover every applicable
standard, representative non-standard component types, hard negatives, and section-bound package
evidence. Citation correctness is exact: extra or missing plan/package citations both fail the case.

## Common Commands

Dry-run workbook parsing without network access:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library
```

Preflight URL reachability without saving artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --limit 10
```

Preflight records HTTP status, final URL, redirect chain, content type, content length, challenge-page detection, and failure status for each workbook row while fetching each unique URL only once.

Download a small controlled slice:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --limit 5
```

The downloader saves immutable raw artifacts under `source_library/artifacts/raw/`, computes SHA256 hashes, reuses existing artifacts on resume, and writes a row-level manifest for every workbook source row.

Build an operator report for any run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources report \
  --output-dir source_library \
  --run-id pilot-core-sources
```

The report writes `source_library/runs/<run_id>/operator_report.md` and lists status counts, host counts, adapter usage, and rows that need manual URL repair.

Before scaling a pilot into a full download, run the acceptance gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id pilot-core-sources-adapted
```

The gate writes `source_library/runs/<run_id>/acceptance_gate.json` and exits nonzero if artifact hashes, byte sizes, duplicate links, status counts, exclusion safety, or repair-queue coverage fail.

Run staged host pilots before the full download:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources pilot-hosts \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix staged-pilot \
  --host www.ecfr.gov \
  --host uscode.house.gov
```

Each host pilot runs `download`, `report`, and `validate-run`. The command writes a parent summary under `source_library/runs/<run-id-prefix>-host-pilots/` and exits nonzero if any selected host has failed rows or a failed acceptance gate.

Plan controlled download batches before scaling beyond pilots:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix first-batch \
  --batch-size 5 \
  --limit-per-host 1 \
  --plan-only
```

Remove `--plan-only` to execute the planned batches. Each batch runs `download`, `report`, and `validate-run`, writes a parent `batch_plan.json`, `batch_ledger.json`, and `repair_queue.csv`, then stops on the first failed or repair-needed batch unless `--continue-on-failure` is passed.
Use `--resume` to skip already passed batches under the same run prefix.

Run or refresh the full captured library:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix full-library \
  --batch-size 10 \
  --continue-on-failure
```

Build the reviewer-engine catalog from the full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id corpus-update-2026-05-01-cg-support-batches
```

The catalog command writes `source_library/catalog/source_catalog.jsonl`, `source_set_manifest.json`, `catalog_validation.json`, `review_sources.sqlite`, and graph seed node/edge JSONL.
Pass `--run-id <download-run-id>` after downloads to link artifact hashes, paths, content types, and retrieval timestamps into the same reviewer-facing catalog.
Pass `--batch-run-id <run-id-prefix>-batches` after controlled batch downloads to link artifacts from every passed child batch through the parent batch ledger.

Build the verified extraction/chunk layer from the reviewer catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

The extraction command reads `review_sources.sqlite`, recomputes every artifact SHA256 before
parsing, routes by `expected_parser` and `content_type`, and writes:

- `source_library/derived/<source_set_id>/extracted_text/`
- `source_library/derived/<source_set_id>/docling_json/`
- `source_library/derived/<source_set_id>/chunks/chunks.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_manifest.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_validation.json`
- `source_library/derived/<source_set_id>/diagnostics/extraction_accuracy_audit.json`
- `source_library/derived/<source_set_id>/diagnostics/summary.json`

For delta extraction, repeat `--id` for each selected `source_record_id`. The command records the
complete selected ID list in `diagnostics/summary.json`; retrieval remains non-reviewer-ready for a
filtered extraction unless rebuilt with explicit partial-extraction allowance.

Before a reuse-first rebuild, inventory current and prior extracted text without running extraction
or review commands:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory \
  --output-dir source_library
```

The command writes `source_library/derived/<source_set_id>/reuse_inventory/` with one row per
current catalog source classified as `already_current_cg_slice`, `reuse_extraction`,
`needs_extract`, or `excluded`. Reuse candidates require matching `source_record_id`, artifact
SHA256, parser/content type metadata, existing extracted text, and matching text SHA256.

When unchanged artifacts already have matching extracted text, pass `--reuse-existing` to reuse the
current source-set text/cache and pass `--reuse-inventory-path` to copy validated prior source-set
candidate text into the current extraction. This rewrites the manifest and chunks for the current
source set while reparsing only rows that the inventory classified as `needs_extract`:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library \
  --reuse-existing \
  --reuse-inventory-path source_library/derived/<source_set_id>/reuse_inventory/reuse_inventory_records.jsonl
```

For eCFR XML records whose workbook URL points at a section or subpart, extraction scopes the text
to that XML element and records the applied source scope in parser metadata. Run the accuracy audit
after extraction to verify text hashes, raw artifact hashes, chunk offsets, no chunk coverage gaps,
scoped XML text, markup/entity cleanup, and PDF token coverage against independent `pypdf` text:

```bash
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library
```

PDF extraction uses Docling first. The default PDF path disables OCR for born-digital sources and
runs Docling in a child process with a hard per-document timeout; when a born-digital PDF exceeds
that timeout, extraction falls back to `pypdf_text_fallback` and records that parser in the
manifest with fallback audit metadata. Pass `--docling-ocr` only for scanned PDFs and adjust
`--docling-timeout-seconds` with operator intent. Use Python 3.12 for that lane:

```bash
uv venv --python python3.12 .venv-docling
. .venv-docling/bin/activate
uv pip install -e ".[extraction]"
```

Build the local evidence retrieval index from the extracted chunks:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library
```

By default, `retrieval-build` requires a full extraction scope: no extraction filters, selected
source count equal to catalog source count, all required non-excluded sources extracted, and one
indexed chunk source for every extracted source. Scope-excluded rows remain terminal manifest rows
but do not require chunks. For a one-source diagnostic slice, pass `--allow-partial-extraction`; the
command will build the index but mark `reviewer_ready` as `false`.

Query the evidence index with text and reviewer filters:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-query \
  --output-dir source_library \
  --document-role regulation \
  --authority-level federal_regulation \
  "alternatives environmental effects"
```

Each result includes the `source_record_id`, `artifact_sha256`, `citation_label`, parser name and
version, extracted-text offsets, URLs, and a short evidence span.

Run a first-pass EA package review against the source-library evidence index:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

`ea-review` extracts supported local package files (`.pdf`, `.html`, `.xml`, `.docx`, `.txt`, and
`.md`), runs the seeded checklist in `config/ea_review_checklist_seed.json`, retrieves supporting
knowledge-base evidence for each item, and writes:

- `source_library/reviews/<review_id>/package/package_manifest.jsonl`
- `source_library/reviews/<review_id>/package/package_chunks.jsonl`
- `source_library/reviews/<review_id>/review_validation.json`
- `source_library/reviews/<review_id>/review_report.json`
- `source_library/reviews/<review_id>/review_report.md`

Findings are deterministic `pass`, `gap`, `uncertain`, or `not_applicable` records. A `gap` means
the source library supports the review requirement but no matching EA package evidence span was
found. An `uncertain` item does not make a compliance claim.
Package evidence search requires at least one configured package term to match; single-word package
terms match whole tokens, while phrase terms match contiguous text.
The command requires the source-library retrieval summary and validation to be reviewer-ready before
running, and fixed review IDs replace prior package artifacts so stale package chunks cannot survive
reruns. Pass `--reuse-package-cache` only when a review directory already has
`package/package_manifest.jsonl` and `package/package_chunks.jsonl` that you intend to reuse; this
reruns checklist/rule evaluation against cached package chunks without re-extracting PDFs.

Resolve Custer Gallatin forest-plan context from a local EA package:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

`forest-plan-resolve` is the first profile-driven forest-plan review sequence, with Custer Gallatin
as the first configured profile. It extracts or reuses the package cache, resolves whether the EA
matches the selected profile, then extracts ranger district, project-location, geographic-area,
management-area, and overlay signals from profile data. For resolved Custer Gallatin packages, it
records the expected profile source records and retrieves supporting source-library plan evidence
from the primary Land Management Plan. It also routes triggered ROD, FEIS,
designated-area/allocation, ESA Biological Assessment, and Biological Opinion cues to the required
Custer Gallatin supporting records declared by the profile. Broad section labels such as
`purpose and need` do not activate FEIS routing by themselves. Generic project decision labels such
as `selected alternative`, `decision basis`, or `plan approval` do not activate the Custer Gallatin
ROD route unless the package explicitly says `Record of Decision` or `ROD`; `plan consistency`
labels do not activate FEIS routing unless an explicit FEIS/tiering/incorporation cue is present.
Acronym triggers such as `ROD`, `FEIS`, `BA`, `BO`, and `ESA` require uppercase matches. The command
then writes:

- `source_library/reviews/<review_id>/forest_plan_context.json`
- `source_library/reviews/<review_id>/forest_plan_context_validation.json`
- `source_library/reviews/<review_id>/forest_plan_context_summary.json`
- `source_library/reviews/<review_id>/package/package_manifest.jsonl`
- `source_library/reviews/<review_id>/package/package_chunks.jsonl`

Custer Gallatin packages with no resolved geographic area, management area, or overlay are not
reviewer-ready and set `needs_reviewer_resolution`. Ambiguous `Gallatin`-only packages are not
guessed. Other configured forest profiles remain blocking evidence when they are mentioned as
operative project scope, but incidental background, reference, bibliography, or coordination
mentions do not force an otherwise Custer Gallatin package to `ambiguous`. Negative package-location
text such as `not part of the project area` is filtered before geographic and management area
resolution. Non-Custer packages are marked `not_custer_gallatin` and treated as out of scope.

Export and evaluate a forest-plan component adjudication file for an existing review:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --adjudication-file source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_adjudication.json
```

The template command reads `forest_plan_component_findings.json` and
`forest_plan_reviewer_resolution_queue.json`, then writes a reviewer-fillable JSON adjudication file
and a Markdown worklist with one item per open queue item. Each item carries compact component and
evidence trace references from the current finding, including source-record IDs, citations, hashes,
chunk/page fields, and available offsets/spans. The eval command fails until each item has explicit
adjudication metadata, preserves required trace refs, and has a resolved disposition such as
`true_ea_omission`, `retrieval_miss`,
`package_section_chunking_miss`, `component_inventory_overreach`, `applicability_false_positive`, or
`evidence_linking_miss`. This keeps model or code guesses out of the legal conclusion while turning
reviewer decisions into measurable improvement data.

Run a versioned compliance rule pack and emit the compliance matrix and finding graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack source_library/reviews/<review-id>/applicability/generated_rule_pack.json \
  --review-id <review-id> \
  --source-set-id <source-set-id>
```

To refresh rules against an already extracted package, keep the same review ID and add
`--reuse-package-cache`:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack source_library/reviews/<review-id>/applicability/generated_rule_pack.json \
  --review-id <existing-review-id> \
  --source-set-id <source-set-id> \
  --reuse-package-cache
```

Reviewer-ready `compliance-review` requires the generated applicability rule pack, a passing
`applicability_validation.json`, matching `generated_rule_pack_validation.json`, matching package and
source-set hashes, valid `non_applicable_authorities.json`, search coverage for non-applicable
decisions, and matching applicability provenance. The base rule pack under `config/` remains the
candidate-authority template; pass `--allow-base-rule-pack-review` only for a non-reviewer-ready
diagnostic run.

`compliance-review` reuses the package extraction and source retrieval gates from `ea-review`, then
writes:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/compliance_matrix.json`
- `source_library/reviews/<review_id>/compliance_matrix.md`
- `source_library/reviews/<review_id>/compliance_matrix.pdf`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

For Custer Gallatin packages, the same review directory also includes the forest-plan context and
component-evaluation artifacts. `compliance_validation.json` includes the
`forest_plan_component_gate_reviewer_ready` check, the compliance matrix summary links to
`forest_plan_review`, the matrix renders Forest Plan component compliance in a separate
`forest_plan_compliance` table, and the finding graph includes `ForestPlanReview` and
`ForestPlanComponentEvaluation` nodes.

The command follows an applicability-first workflow: compliance findings evaluate generated
applicable rules only, while non-applicable authorities remain in
`non_applicable_authorities.json`. The compliance matrix links to that artifact as the source of
truth rather than recreating non-applicability decisions. The generated rule pack declares
`baseline_source_record_ids`; for the active workbook this list is the 26
`Ingest_Checklist` rows where `Scope=Baseline`, not the first rows in workbook order. Rule-pack
validation fails when a declared baseline source record has no rule or when its rule is not
`applicability_mode=baseline`. Every
applicable `pass` finding requires package evidence and source-library evidence. Every applicable
`gap` finding requires source-library evidence and records that matching package evidence was not
found. Claim-bearing findings also require validated rule-to-source-claim links. The finding graph
connects the review, rule pack, rules, findings, evidence spans, source claims, and package gaps.
Rule-pack IDs, rule IDs, and fixed review IDs must use only letters, numbers, dots, underscores, and
hyphens. Unknown or empty `source_filters` fail rule-pack validation so typoed filters cannot
silently broaden source retrieval.
The compliance matrix is the reviewer-facing table set: the `NEPA / Authority Compliance` table
records authority category, authority source record, authority document role, applicability mode,
applicability status and basis, rule status, package citation, source-library citation, source-claim
IDs, limitations, and whether citation requirements were met. When a Forest Plan lane is present,
the matrix also includes a separate `Forest Plan Compliance` table derived from component findings
and applicable-standard coverage, so Forest Plan compliance is clearly separated from
NEPA/generated-rule compliance. Every compliance review also renders `compliance_matrix.pdf` from
the same matrix data.

Run the final compliance review eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

`compliance-review-eval` writes deterministic package fixtures from the eval file, runs the real
`compliance-review` command for each case, and scores the generated findings. It asserts expected
statuses for every rule in the rule pack, claim types, package evidence, source-library evidence,
source-claim links, expected source record IDs, expected source document roles, finding status
counts, unsupported finding IDs, citation coverage, failure taxonomy, and finding-graph coverage.
Bad eval filters, unknown rule IDs, partial rule expectations, and mismatched status counts fail
fast so typoed or incomplete fixtures cannot silently broaden scoring. When this eval is run against
the base rule pack during the applicability-first transition, those case outputs are diagnostic:
they can score finding quality, but they are not reviewer-ready promotion artifacts.

Run the adjudicated gold eval promotion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
```

`compliance-gold-eval` reads a structured adjudication file, requires positive, mixed, and negative
case profiles, verifies every case covers the active rule pack, then runs those cases through the
real `compliance-review-eval` path. The current gold file contains 10 realistic adjudicated package
profiles with expected status counts, applicable source rows, and source document classes. It emits
`promotion_ready` only when the rule pack is a reviewer-ready generated applicability rule pack and
adjudication checks plus the underlying compliance-review eval both pass.
Gold case IDs must be unique and safe for generated paths, and package fixture paths must stay under
the gold file directory.

Run the V1 real-EA review eval after the East Crazy Inspiration Divide compliance review exists:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
```

`v1-ea-eval` does not rerun extraction or review. It reads an existing review directory and scores
whether the real EA review applied the correct source documents to the correct EA sections. The
default V1 contract tracks required EA section detection, baseline authority/source alignment,
all 26 baseline source records, rule-to-section matches, rule-to-source-record matches,
rule-to-document-role matches, conditional applicability expectations, applicable conditional
source/section alignment, missing conditional expectations, conditional false positives/negatives,
Custer Gallatin required plan records, forest-plan geographic/management area resolution, component
coverage, applicable-standard application, citation requirements, reviewer-resolution queue size,
and failure-category counts.

The result summary separates the overall readiness gate from two diagnostic lanes:
`broader_ea` for package sections, baseline authorities, rule bindings, conditional sources, and
review artifacts outside the forest-plan set; and `forest_plan` for Custer Gallatin source records,
scope, component coverage, applicable standards, reviewer readiness, and component adjudication.
This allows the real V1 eval to fail overall on non-forest-plan gaps while still reporting
`forest_plan_passed=true` when the forest-plan review lane is complete.

Run the manifest-driven promotion suite:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

`promotion-suite` reads existing promotion artifacts and writes an aggregate JSON/Markdown report
under `source_library/reviews/promotion_suite/<suite_id>/`. It separates
`current_promotion_ready`, `expansion_ready`, and `promotion_ready` so agents can distinguish the
promoted East Crazy V1 evidence from post-V1 real-package expansion work. Use
`--strict-expansion` when additional real-package slots should block the command exit status.
When recording both normal and strict expansion results, send the strict run to a separate
`--results-dir` or rerun the normal suite last so the default suite output remains the current
promotion signal.
The manifest also requires the applicability seed and gold eval artifacts that prove Milestone 4
authority-family positive/negative, unresolved, and adjudication coverage.
Default runs keep current-promotion failures in `failure_category_counts` and expansion-only gaps in
`expansion_failure_category_counts`.
Failure categories include `missing_source`, `extraction_miss`, `retrieval_miss`,
`applicability_miss`, `unsupported_package_evidence`, `stale_artifact`, `adjudication_needed`,
`forest_plan_reviewer_not_ready`, and `package_fixture_missing`.
Selected not-ready expansion slots must carry review/package/source-set metadata, expected gate
artifacts, next action, and a typed non-`package_fixture_missing` failure category; ready slots fail
validation if they retain a failure category.

As of the latest post-V1 real-package expansion pass, the ECID preliminary-EA expansion slot is
ready locally. `applicability-adjudication-eval`, `applicability-adjudication-apply`,
`applicability-validate`, generated rule-pack validation, compliance review, Forest Plan component
adjudication eval, and review-scoped phase eval all pass for
`region1-expansion-ecid-preliminary-ea`. The Forest Plan component adjudication eval matches the
current `158`-row queue, resolves all rows as true EA package-evidence omissions, and records `0`
system misses; those rows remain visible as gaps rather than being converted into support or legal
conclusions. The third real package is South Plateau Area Landscape Treatment Project under review
ID `region1-expansion-south-plateau-landscape-treatment`. Sequence 4 imported `26` official PDFs,
extracted `26/26` files into `3,671` package chunks, and ran the applicability-first path through
validation. The slot remains not ready with `adjudication_needed`: applicability determination found
`55` applicable authorities, `331` non-applicable authorities, and `6` authority-family
positive/negative trigger conflicts requiring replayable adjudication before generated rule-pack,
compliance-review, or phase-eval promotion.

Run the seed retrieval eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --eval-file config/retrieval_eval_seed.json
```

The eval checks whether expected compliance-review evidence can be retrieved with citation-bearing
provenance. It reports hit rate, expected-term coverage, citation coverage, unsupported-answer rate,
and zero-result rate.

Build the document evidence graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build \
  --output-dir source_library
```

The graph builder creates source-document, raw-artifact, extracted-text, document-section,
document-chunk, evidence-span, parser, and review-topic nodes with provenance edges. It requires a
reviewer-ready retrieval index by default and compares each chunk back to the retrieval SQLite index
so stale or edited chunk files cannot produce reviewer-ready graph artifacts. Use
`--allow-partial-retrieval` only for diagnostic slices; the graph can validate structurally, but
`reviewer_ready` remains `false`.

Build deterministic source claims and entity graph artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract \
  --output-dir source_library
```

`claim-extract` reads extracted chunks, catalog topics, and the reviewer-ready retrieval index. It
emits exact source-text claim spans, entities, authority links, graph JSONL, SQLite, validation, and
summary artifacts. Claims are deterministic `obligation`, `prohibition`, `condition`,
`authorization`, `definition`, `exemption`, or `guidance` records and are reviewer-ready only when
their offsets, hashes, chunk IDs, citations, and retrieval-index bindings validate.

Run the seed claim eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
```

`claim-eval` revalidates the current claim artifacts before scoring cases. It refuses missing,
tampered, or non-reviewer-ready claim outputs, and eval case filters fail fast on unknown or empty
keys so typoed filters cannot silently broaden the eval.

Build deterministic rule-to-source-claim links:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

`rule-claim-link` reads reviewer-ready claim artifacts and a versioned compliance rule pack. It
writes rule-to-claim links, explicit no-claim gaps, SQLite, validation, and summary artifacts. Links
carry rule ID, claim ID, claim type, score, matched terms, citation label, chunk ID, artifact hash,
and exact source offsets. Rule-claim outputs are versioned by rule-pack ID and version. Old
`0.3.0`/20-rule link, coverage, compliance-eval, and gold-eval artifacts should be treated as stale
for base-pack diagnostics. Current base rule-claim and coverage evidence must come from the
regenerated `0.4.0`/44-rule artifacts for `source-set-ba8d0feae79501b8`; reviewer-ready V1
compliance evidence must come from the generated applicability rule pack for the review.

Run the seed rule-claim eval gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
```

`rule-claim-eval` revalidates current link artifacts before scoring cases and refuses stale,
tampered, or non-reviewer-ready bindings.

Build the applicability-first authority universe snapshot:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id <review-id> \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

`applicability-authority-universe` reads the source catalog, source-set manifest, base rule pack,
Milestone 3 authority-family template config, forest-plan profiles, source-set component inventory,
source-claim artifacts, and rule-claim links. It writes
`source_library/reviews/<review_id>/applicability/authority_universe_snapshot.json` with one
rule-template candidate per base rule, one authority-family rule-template candidate per Milestone 3
template, and one forest-plan component candidate per component inventory record. Each candidate
carries required package fact types, positive and negative trigger groups, source evidence
requirements, source-role filters, package-section filters, retrieval contracts, graph-expansion
contracts, dependency/exception/supersession fields, and search coverage requirements for later
non-applicability proof. This command does not write package fact graphs, retrieval traces, graph
traces, search coverage certificates, applicability decisions, applicable/non-applicable authority
artifacts, generated rule packs, or compliance findings.

The default authority-family template config is
`config/authority_family_rule_templates_nepa_ea_v1.json`. Use
`--authority-family-templates-path <path>` to test a replacement template set, or
`--no-authority-family-templates` only for narrow legacy/unit runs that intentionally exclude the
expanded Milestone 3 authority universe.

Build the package fact graph and package applicability context from an existing EA package cache:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id> \
  --package-path /path/to/ea-package
```

`applicability-context-build` reads
`source_library/reviews/<review_id>/package/package_manifest.jsonl` and
`source_library/reviews/<review_id>/package/package_chunks.jsonl`, which are produced by
`ea-review`. It writes `package_fact_graph.json`, `package_applicability_context.json`, and
`package_fact_graph_validation.json` under the review applicability directory. Facts are bound to
package chunk IDs, section IDs, parser provenance, artifact hashes, content hashes, and evidence
span IDs. Negative or out-of-scope location statements are recorded as negative-context facts rather
than positive geography facts. Weakly worded facts and missing common fact types are recorded as
graph uncertainty for later applicability stages instead of being resolved inside the package
context command. This command does not write applicability decisions, retrieval traces, graph
traces, generated rule packs, or compliance findings.

Build per-authority retrieval and bounded graph traces:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id>
```

`applicability-retrieve` reads the authority universe snapshot, package fact graph, local retrieval
index, and available graph/link artifacts. It writes `applicability_retrieval_trace.jsonl`,
`applicability_graph_trace.jsonl`, and `applicability_retrieval_graph_diagnostics.json`. Retrieval
rows include exact/keyword, metadata/source-role, package-section, graph-seed, and fused RRF result
sets with selected and rejected results. Graph rows are bounded by each candidate's declared graph
contract and preserve authority-category, source-claim/rule-claim-link, supporting-source, package
fact, and Forest Plan component provenance when those artifacts are available. This command records
evidence discovery only; it does not write applicability decisions, search coverage certificates,
generated rule packs, or compliance findings.

Write deterministic applicability decisions before review:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id>
```

`applicability-determine` reads the authority universe, package fact graph/context, retrieval trace,
and graph trace. It writes `applicability_decisions.jsonl`, `applicable_authorities.json`,
`non_applicable_authorities.json`, `search_coverage_certificates.json`,
`applicability_provenance.json`, and `applicability_report.md`. The command records deterministic
applicability bases, preserves inspected source-library evidence spans, requires source-index hashes
for sufficient coverage, and runs trigger arbitration so strong, rule-contract-sufficient trigger
evidence can carry an `applicable` decision while weak auxiliary evidence stays visible. All-weak
trigger evidence and unresolved positive/negative trigger conflicts remain `needs_adjudication`. It
does not write a generated rule pack, compliance matrix, or compliance findings.

Validate the applicability run before generated rule-pack creation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id>
```

`applicability-validate` reads all applicability artifacts through the decision ledger and writes
`applicability_validation.json`. It fails closed when candidate decisions are missing or duplicated,
applicable/non-applicable artifacts do not partition the authority universe, unresolved or
`needs_adjudication` rows remain, retrieval or graph traceability is missing, non-applicable
decisions lack coverage or adjudication, artifact hashes are stale, or provenance does not cover
the required artifacts.

Create, evaluate, and apply applicability adjudication records:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-template \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id> \
  --adjudication-file source_library/reviews/<review-id>/applicability/applicability_adjudication_template.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id> \
  --adjudication-file source_library/reviews/<review-id>/applicability/applicability_adjudication_template.json
```

The template command writes `applicability_adjudication_template.json` and
`applicability_adjudication_worklist.md` for unresolved decisions. The eval command proves the
completed adjudication is current, complete, and replayable. The apply command rewrites the decision
ledger and applicable/non-applicable authority artifacts with `human_adjudication` bases, writes
`applicability_adjudication_apply.json`, and updates provenance. These commands still do not create
a generated rule pack or compliance findings.

Generate the applicability-derived rule pack:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id <review-id> \
  --source-set-id <source-set-id> \
  --validate-only
```

`applicability-generate-rule-pack` requires a passing, current `applicability_validation.json`. It
writes `generated_rule_pack.json` and `generated_rule_pack_validation.json` from validated
applicable authorities only; non-applicable authorities remain in `non_applicable_authorities.json`.
Generated rules carry explicit base/generated rule IDs, applicability decision IDs, retrieval and
graph trace IDs, source-record/document-role metadata, source-claim link requirements,
package-section expectations, Forest Plan component metadata when relevant, and per-rule
freshness/provenance hashes. `--validate-only` rechecks an existing generated pack, requires the
previously recorded generated-pack hash, and fails if the pack was edited by hand or is stale
relative to applicability artifacts.

Run applicability decision-quality evals:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/applicability_eval_seed.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/applicability_gold_eval_v0.json
```

`applicability-eval` runs deterministic seed packages through authority-universe creation,
package-fact graph construction, applicability retrieval/graph traces, deterministic decisions,
validation, and generated-rule-pack creation. It fails on false positive/negative applicability
statuses, partition mismatches, missing non-applicable coverage certificates, retrieval or graph
trace gaps, package-fact mismatches, and generated-rule-pack coverage drift. The default eval seed
includes all `19` Milestone 3 authority-family rule templates, positive/negative coverage counts,
unresolved weak-signal handling, arbitration status/effect expectations, and real-package coverage
tags. The current seed has `9` cases and explicitly covers strong-positive plus weak auxiliary
evidence, weak-only evidence, positive/negative conflicts, no-action/background-only evidence, and
rule-template-specific trigger sufficiency. `applicability-gold-eval` wraps adjudicated positive,
mixed, negative, unresolved, and replay-adjudicated package profiles; it now carries
arbitration-field expectations and emits `promotion_ready=true` only when the adjudication checks
and applicability eval both pass.

Run rule-pack coverage:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

`compliance-coverage` validates that every rule has a coverage-matrix row, current source-claim
links, source-claim term support, and compliance-review eval coverage. It reports uncovered rules,
rules without eval cases, rules without source-claim links, source-record mismatches, and
source-claim terms that do not match current rule-claim bindings.

Run forest-plan component eval against an existing review:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/forest_plan_component_eval_seed.json
```

`forest-plan-component-eval` reads the review's component findings, applicable-standard coverage,
and reviewer-resolution queue, then writes `forest_plan_component_eval_results.json` beside the
review artifacts. Use this after `forest-plan-resolve` or `compliance-review` when changing
component applicability, source binding, package evidence extraction, or reviewer-resolution logic.

Run phase-aligned readiness evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library
```

This reports catalog, extraction, retrieval, evidence-graph, claim-extraction, and rule-claim
binding readiness separately so validation failures are not hidden inside a single aggregate score.
When `compliance_coverage_results.json` exists beside the rule-claim outputs, it also reports a
`compliance_coverage` phase for matrix, source-claim, source-claim-term, and eval-case coverage.
When `source_library/reviews/compliance_gold_eval/compliance_gold_eval_results.json` exists, it also
reports a `compliance_gold_eval` promotion phase with explicit failed checks for stale source-set,
rule-pack, failed-gold, or not-promotion-ready artifacts. If a review uses a generated rule pack,
phase eval can accept a passing gold eval against the generated pack's declared base rule pack and
reports `rule_pack_match_mode=generated_base`. Pass `--review-id <review-id>` or
`--review-dir <path>` to include the applicability phase gates for `authority_universe`,
`package_fact_graph`, `applicability_retrieval_trace`, `applicability_graph_trace`,
`applicability_determination`, `applicability_validation`, and `generated_rule_pack`, followed by
the `compliance_review` gate. If the review directory contains
`forest_plan_component_eval_results.json`, phase eval also reports a `forest_plan_component_eval`
phase with component-level metrics and failure categories. If the review directory contains
`forest_plan_component_adjudication_eval.json`, or a completed
`forest_plan_component_adjudication.json` that still needs an eval, phase eval also reports a
`forest_plan_component_adjudication` phase with completion rate, expectation match rate,
disposition counts, and failure categories. The applicability phases require current validation,
hash-aligned traces, complete applicable/non-applicable partitions, coverage certificates for
non-applicable authorities, and generated-rule-pack rules that exactly match applicable
authorities. The compliance phase requires the review source set to match the evaluated source set
and requires the review's `compliance_matrix.json` to exist with the expected schema version,
review ID, source set, rule pack, row count, and status counts. It also requires
`compliance_matrix.pdf` to exist and have a valid PDF header.

Repair stale or blocked workbook URLs through `config/url_overrides.toml`:

```toml
[[overrides]]
source_record_id = "R1EA-000"
override_url = "https://example.gov/current-official-source"
reason = "Replaces stale workbook URL after manual source verification."
```

Manifests preserve the workbook cell as `original_url` and use `effective_url` for fetching, deduplication, host pilots, and artifact paths.
Overrides must be unique by `source_record_id`, use absolute HTTP(S) URLs with hosts, and avoid workbook scope-exclusion URLs.
Run summaries include `override_count` and `filtered_override_count`, and `validate-run` fails if override provenance or counts drift from the manifest.

## Development

Use the bundled Python runtime or any Python 3.11+ environment with `openpyxl` installed.

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

The captured-library integrity tests validate the current generated `source_library` when present. They check full-batch coverage, manifest-to-ledger consistency, artifact SHA256 and byte sizes, override provenance, catalog linkage, and SQLite/catalog agreement.
