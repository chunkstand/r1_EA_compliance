# Current System State

This project is a local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA
Forest Service Region 1 source material.

The workbook `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx` remains the source-of-truth
input for the knowledge base. The generated `source_library/` is the audited local capture and
derived reviewer corpus used by extraction, retrieval, evidence graph, source-claim extraction,
rule-claim binding, and deterministic EA package review commands.

## Current Workbook Contract

The uploaded workbook now defines the active source contract:

- `Ingest_Checklist` ingest rows: `162`
- `Scope=Baseline` rows: `26`
- `Scope=Conditional` rows: `136`
- `R1_Forest_Plans` unit/overlay rows: `28`
- Total rows in the default ingest-driving sheets: `190`

The Region 1 forest-plan support-document register is promoted as a controlled supplemental
source-delta input at `config/r1_forest_plan_document_register_draft.csv`. The register has `189`
reviewed rows: `28` rows already confirmed in the workbook/catalog contract, `159`
`source_delta_required` rows that can be emitted as supplemental `WorkbookSource` records, and `2`
documented official-source gaps that are counted but not planned for corpus download. The promoted
CLI path is:

```text
--r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-only
```

The promotion validation is documented in
`docs/R1_FOREST_PLAN_DOCUMENT_REGISTER_PROMOTION_REPORT.md`. The register options are accepted by
`dry-run`, `preflight`, `download`, `batch-download`, and `catalog-build`. The live source-delta
capture run `r1-forest-plan-source-delta-capture-20260510-batches` passed `33/33` batches for all
`159` emitted rows, with an empty repair queue and `158` unique artifacts. The scoped source-delta
catalog gate is archived under
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/catalog_gate/` as
`source-set-411b3736b3691eed` with `159` forest-plan support rows, `158` artifacts, `159`
`active_review_corpus` rows, and `catalog_validation.json` passing.

The source-delta readiness gate is implemented by `forest-plan-source-delta-readiness`. The live
gate over `r1-forest-plan-source-delta-capture-20260510-batches` passes with `0` failed checks,
distinguishes the scoped source-delta source set `source-set-411b3736b3691eed` from the active
canonical catalog source set `source-set-d3b9e2a728accda6`, keeps
`R1PLAN-kootenai-nf-18` and `R1PLAN-nez-perce-clearwater-nfs-18` as explicit official-source gaps,
validates `config/r1_forest_plan_official_source_gap_evidence.json` against those gap IDs, and now
also evaluates the Sequence 4 merged-catalog extraction state. The generated JSON/Markdown report
uses schema `r1-forest-plan-source-delta-readiness-v3` and is under the source-delta run's ignored
`source_delta_readiness/` directory. The committed earlier artifact still reflects the pre-fallback
run, but the live merged replay is now refreshed on archived merged catalog
`source-set-7e2652d23e764068` with the active canonical catalog still untouched. Current live
Sequence 4 through Sequence 6 readiness results:

- merged reuse inventory: `reuse_extraction=189`, `needs_extract=159`, `excluded=1`
- merged extraction summary: `341` extracted rows, `7` explicit `parser_error` rows, `1`
  scope-excluded row, `75,708` chunks
- support-document extraction readiness: `159` expected source-delta rows covered, `152` extracted
  rows, `7` explicit parser blockers, status `ready_with_blockers`
- current blocker classes: `pdf_text_fallback_empty=5`, `pdf_text_fallback_failed=2`
- retrieval validation: passed on `source-set-7e2652d23e764068` with
  `--catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate`
  plus `--allow-failed-extraction --allow-partial-extraction`
- source-delta retrieval eval: `12/12` passed from
  `config/r1_forest_plan_source_delta_retrieval_eval.json`
- retrieval readiness: `ready_with_blockers`, with `152/152` extracted support-document rows
  indexed and the same `7` upstream parser blockers kept explicit
- Sequence 5 alignment closeout: merged-corpus chunks now carry register-backed
  `support_document_role` values for matching `R1PLAN-*` rows, including catalog-confirmed rows
  such as `R1PLAN-custer-gallatin-nf-06`, so the current retrieval eval pass is based on actual
  role-aware filters rather than source-ID-targeted shortcuts
- forest-profile readiness: `ready_with_blockers`, with configured profile readiness separated from
  register-only tracking coverage
- configured-profile status: `1` ready profile (`custer-gallatin-nf`) and `1` blocked profile
  (`beaverhead-deerlodge-nf`)
- retrieval-ready tracking-only rows: `flathead-nf`, `helena-lewis-and-clark-nf`, and
  `region-1-northern-region`; these remain tracked rows, not configured profiles
- current blocked forest-profile source IDs:
  `R1PLAN-beaverhead-deerlodge-nf-08`, `R1PLAN-bitterroot-nf-07`,
  `R1PLAN-dakota-prairie-grasslands-25`, `R1PLAN-idaho-panhandle-nfs-09`,
  `R1PLAN-idaho-panhandle-nfs-10`, `R1PLAN-kootenai-nf-08`, `R1PLAN-kootenai-nf-18`,
  `R1PLAN-lolo-nf-12`, and `R1PLAN-nez-perce-clearwater-nfs-18`

Sequence 4 runtime alignment update after that artifact:

- `extract-build` now treats `docling_unavailable` the same way it already treated
  `docling_timeout`: it falls back to `pypdf_text_fallback` when born-digital PDF text is
  extractable.
- external Docling execution is now opt-in through `USFS_R1_DOCLING_PYTHON` instead of being
  assumed from a repo-local `.venv-docling`.
- targeted live smoke over merged-catalog PDFs `R1PLAN-beaverhead-deerlodge-nf-02`, `-03`, and
  `-04` succeeded with `parser_name=pypdf_text_fallback`,
  `fallback_error_class=docling_unavailable`, and large extracted text payloads.
- the remaining blocker set is now narrow and explicit:
  `R1PLAN-beaverhead-deerlodge-nf-08`, `R1PLAN-bitterroot-nf-07`,
  `R1PLAN-dakota-prairie-grasslands-25`, `R1PLAN-idaho-panhandle-nfs-09`,
  `R1PLAN-idaho-panhandle-nfs-10`, `R1PLAN-kootenai-nf-08`, and `R1PLAN-lolo-nf-12`.
- Sequence 7 corpus incorporation and downstream replay is now implemented for merged support-document
  source set `source-set-7e2652d23e764068`.
- live downstream replay against the merged corpus is fresh through the source-set graph layer:
  `claim-extract --allow-partial-retrieval` now validates with `101,824` claims and
  `reviewer_ready=false`; `evidence-graph-build --allow-partial-retrieval` validates with
  `178,912` nodes and `559,467` edges while keeping inherited extraction blockers explicit;
  `rule-claim-link --allow-partial-claims` validates with `211` links, `0` gaps, and
  `reviewer_ready=false`; `nepa-knowledge-graph-export` validates with `1,837` nodes and `2,842`
  edges; and source-set `phase-eval` now passes `6/7` phases while remaining `reviewer_ready=false`
  only because extraction and inherited downstream reviewer-ready gates remain blocked.
- the stale-source-set gaps are closed for source-set replay: archived-catalog routing is explicit
  for evidence graph and phase eval, source-set-only phase replay ignores an unrelated root
  `compliance_gold_eval`, and the NEPA 3D graph contract now recognizes `extraction_blocked` and
  `official_source_gap`.
- the next work is not another source-set alignment pass. It is parser recovery for the seven
  blocked source IDs, resolution of the two official-source gaps, or an explicit review replay
  request against the merged corpus.

Latest refresh on 2026-05-10 supersedes that partial Sequence 7 state:

- `R1PLAN-nez-perce-clearwater-nfs-18` is now promoted from official-source gap to live
  `project_record`, so the Region 1 register now carries `160` source-delta rows and `1`
  preserved official-source gap (`R1PLAN-kootenai-nf-18`).
- refreshed source-delta capture is archived under
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/`, with scoped
  source set `source-set-bfe49a94e22fd1e2` and merged source set `source-set-8a4005c8a083af1a`.
- external Docling OCR replay clears all seven former PDF parser blockers. The merged extraction
  replay now validates with `349/349` required rows extracted, `0` failed rows, and `75,745`
  chunks.
- merged source-set replay is fully green: retrieval eval passes `12/12`, evidence graph validates
  with `153,198` nodes and `533,949` edges, claim extraction validates with `101,856` claims,
  rule-claim binding validates with `211` links and `0` gaps, NEPA 3D source-set export validates
  with `1,831` nodes and `2,835` edges, and source-set `phase-eval` passes `7/7` with
  `reviewer_ready=true`.
- `forest-plan-source-delta-readiness` now reports `160` source-delta rows, `0` extraction
  blockers, retrieval `ready`, and one official-source gap. Source readiness is broad enough to
  mark `beaverhead-deerlodge-nf` source-ready, but NEPA 3D graph promotion remains limited to
  `custer-gallatin-nf` until Beaverhead has a validated component inventory.
- merged-corpus review replay is now explicit under
  `source_library/reviews/v1-cg-ecid-source-delta-review/`. The review-scoped replay against
  `source-set-8a4005c8a083af1a` is blocked by `7` applicability adjudications and failing
  forest-plan component evaluation (`9` failing seed cases, `6` resolver gaps); review `phase-eval`
  is `12/17` with `reviewer_ready=false`.
- `applicability-authority-universe` now accepts `--catalog-path` and `--source-set-manifest-path`
  so noncanonical merged-corpus review replays can use archived merged catalog gates without
  replacing `source_library/catalog/`.

The Sequence 3 merged catalog contract is implemented without replacing the active canonical
catalog. `catalog-build` now accepts repeated `--batch-run-id` values and an explicit
`--catalog-dir` archive target. The live merged gate is archived at
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/` as
`source-set-7e2652d23e764068`. It combines canonical batch run
`corpus-update-2026-05-01-cg-support-batches` with source-delta batch run
`r1-forest-plan-source-delta-capture-20260510-batches`, keeps the active
`source_library/catalog/` view at canonical source set `source-set-d3b9e2a728accda6`, and validates
`349` source rows, `318` artifacts, `331` unique URLs, `348` `active_review_corpus` rows, `1`
`candidate_blocked_source` row, `159` supplemental source-delta rows, `0` `not_in_run` rows, and
`0` failed catalog checks.

The 26 `Scope=Baseline` rows are the baseline source records every EA compliance review must
evaluate. They are identified by the workbook `Scope` column, not by row position.

Baseline source record IDs:

```text
R1EA-001, R1EA-002, R1EA-003, R1EA-004, R1EA-008, R1EA-009, R1EA-010,
R1EA-013, R1EA-014, R1EA-015, R1EA-017, R1EA-018, R1EA-019, R1EA-020,
R1EA-021, R1EA-022, R1EA-023, R1EA-024, R1EA-025, R1EA-028, R1EA-029,
R1EA-031, R1EA-033, R1EA-034, R1EA-035, R1EA-067
```

The canonical generated downloader/catalog corpus covers the full 190-row workbook contract:

- Parent batch run: `corpus-update-2026-05-01-cg-support-batches`
- Canonical workbook rows: `190`
- Batch count: `52`
- Passed batches: `52`
- Failed batches: `0`
- Repair-needed batches: `0`
- Repair queue: empty except the CSV header
- Unique effective URLs: `172`
- Promoted downstream V1 source set: `source-set-ba8d0feae79501b8`
- Latest regenerated canonical catalog source set: `source-set-d3b9e2a728accda6`
- Reviewer catalog source rows: `190`
- Reviewer catalog unique artifacts: `160`
- Reviewer catalog source-artifact links: `189`
- Source statuses: `downloaded=8`, `downloaded_existing=170`, `duplicate_content=2`,
  `duplicate_url=9`, `skipped_excluded=1`

`R1EA-160` is present in the workbook/catalog as a `project_reference`, but has no artifact because
its URL remains in `Scope_Exclusions`. The canonical catalog validation passes, and the
captured-library integrity test suite passes against these generated outputs. The scoped
source-delta catalog gate is preserved under the source-delta parent run directory rather than left
as the active `source_library/catalog/` view.

## Authority Universe Family Inventory

Milestone 1 of the authority-universe completion plan is represented by
`config/authority_universe_families_nepa_ea_v1.json`. This file is the machine-readable crosswalk
between the required Region 1 EA authority families, the active workbook/catalog source records, the
current `nepa-ea-v0` rule pack, applicability predicate surfaces, package fact types, coverage
requirements, and eval cases.

Current inventory summary:

- Authority families: `35`
- Required authority requirement groups covered: `18`
- Family statuses: `active=33`, `candidate=1`, `superseded=1`
- Workbook source records crosswalked: `190/190`
- Current rule-pack rules crosswalked: `48/48`
- Authority-family rule templates: `19`
- Orphan rule IDs: none
- Orphan workbook source record IDs: none
- Families still requiring Milestone 2 source-currentness confirmation: `0`
- Families confirmed or documented by the Milestone 2 source-currentness gate: `21`
- Families requiring Milestone 3 rule-template work after currentness: `0`
- Families confirmed by Milestone 4 applicability eval expansion: `19`
- Families requiring Milestone 4 applicability eval expansion: `0`
- Milestone 5 compliance/report integration: implemented for generated compliance reviews through
  authority-family provenance, non-applicable authority appendix, reviewer-resolution report, and
  deterministic litigation-risk summary artifacts.

The only current `candidate` family is environmental justice and civil-rights authority coverage;
Milestone 2 documents a non-addition for revoked environmental-justice executive-order text and
keeps the family visible as a source-record gap for a later scoped workbook/source delta.
Reserved or superseded Forest Service NEPA regulations, including former 36 CFR part 220 references,
are represented as a `superseded` family and point reviewers back to current USDA NEPA procedure
sources under 7 CFR part 1b plus the Forest Service NEPA policy/currentness sources.

## Authority Family Rule Templates

Milestone 3 is implemented by `config/authority_family_rule_templates_nepa_ea_v1.json` and
`config/authority_family_rule_template_coverage_nepa_ea_v1.json`. The template config promotes the
`19` source-currentness-confirmed former `source_only` families into active, data-backed
authority-family rule templates without modifying the base `nepa-ea-v0` rule pack. Each template
records the authority-family ID, rule-template ID, primary and supporting source records, package
fact types, positive and negative package triggers, source filters, evidence expectations,
dependency/exception/supersession fields, and coverage follow-up metadata.

With the current 48-rule base pack, the full real-source authority universe comprises `48` base
rule-template candidates, `19` authority-family rule-template candidates, and `329` forest-plan
component candidates. The `19` template candidates are conditional and are included by default when
`applicability-authority-universe` runs from the repo with:

```text
config/authority_family_rule_templates_nepa_ea_v1.json
```

Use `--authority-family-templates-path` to point at a replacement template set, or
`--no-authority-family-templates` only for narrow legacy/unit runs that intentionally exclude the
expanded authority-family templates.

The templates map Clean Water Act, floodplain, tribal consultation, wilderness/designated-area, and
land-exchange package-fact cues to active authority families. Milestone 4 now supplies independent
positive/negative package fixtures and adjudication-quality scoring for these expanded families.

## Authority Currentness Gate

Milestone 2 of the authority-universe completion plan is implemented by
`config/authority_source_addition_decisions_nepa_ea_v1.json` and the `authority-currentness`
command. The decision config documents the current non-addition for the
`environmental_justice_civil_rights` candidate family: the system should not satisfy current
environmental-justice/civil-rights coverage with revoked executive-order text, and a later scoped
workbook delta should add official Title VI and USDA nondiscrimination sources if this family is
promoted.

The latest local report was generated for `source-set-ba8d0feae79501b8` at:

```text
source_library/derived/source-set-ba8d0feae79501b8/authority_currentness/authority_currentness_report.json
```

Report summary:

- Schema: `authority-currentness-report-v0`
- Authority families checked: `35`
- Family status counts: `active=33`, `candidate=1`, `superseded=1`
- Family/source currentness records: `207`
- Current authority family/source mappings confirmed from catalog: `203`
- Excluded source mappings that do not count as current authority: `1`
- Superseded replacement-source mappings confirmed without counting as current authority: `3`
- Family currentness: `source_currentness_confirmed=33`,
  `documented_source_non_addition=1`, `superseded_replacement_sources_confirmed=1`
- Milestone 2 source-currentness families closed or documented: `21`
- Failed families: `0`
- Validation: passed

This is a source-currentness and supersession gate. It proves that active families have
catalog-confirmed current source coverage, that reserved or superseded authority cannot silently
satisfy current authority requirements, and that the one candidate family has an explicit
non-addition decision. Milestone 3 supplies the semantic rule-template promotion layer, and
Milestone 4 supplies independent applicability eval/adjudication coverage for that expanded
authority universe.

## Source Partition Contract For NEPA 3D

NEPA 3D Milestone 2A is implemented by `config/source_partition_contract_nepa_3d_v1.json`,
`src/usfs_r1_ea_sources/source_partitions.py`, new `catalog-build` `source_partition` fields, and
expanded `authority-currentness` validation. The source-partition contract is the pre-graph
boundary that keeps displayable currentness/supersession evidence separate from sources eligible to
derive active review rules. The current generated catalog was not regenerated for this docs/code
milestone, so the live partition proof is the `authority-currentness` report over the current
catalog surfaces.

Current partition values:

- `active_review_corpus`: current source records eligible for extraction, claims, applicability,
  generated rules, and compliance findings.
- `currentness_supersession_archive`: rescinded, revoked, superseded, reserved, or
  currentness-only records that may support only supersession/currentness graph relationships.
- `candidate_blocked_source`: candidate, blocked, excluded, failed, or unresolved source records
  visible as graph blockers but not active review authority.

The live `authority-currentness` run for `source-set-ba8d0feae79501b8` now records:

- catalog source partitions: `active_review_corpus=189`, `candidate_blocked_source=1`;
- authority-family source roles: `active_authority_source=203`,
  `candidate_blocked_or_currentness_only_source=1`, and
  `supersession_or_replacement_source=3`;
- passing fail-closed checks that the source-partition contract defines the required partitions,
  active/non-active eligibility boundaries, non-active graph relationship limits, reserved
  `36 CFR part 220` archive handling, scoped workbook/source deltas, and catalog behavior where
  non-current sources are not in the active review corpus, superseded family sources use only
  currentness/supersession graph relationships, and collapsed FSH 1909.15 handbook records cannot
  satisfy chapter-level source boundaries.

The current source set does not yet add FSH 1909.15 chapter records. The contract keeps that as a
scoped workbook/source delta before any NEPA 3D graph export claims handbook completeness.

## NEPA 3D Graph Export Contract

NEPA 3D Milestone 1 is implemented by `config/nepa_3d_graph_contract_v1.json`,
`src/usfs_r1_ea_sources/nepa_3d_graph_contract.py`, `docs/OUTPUT_SCHEMAS.md`, and the smallest
source-set/review graph fixtures under `tests/fixtures/nepa_3d_graph/`. This is a contract slice
only: it defines the graph schema before the Milestone 3 source-set exporter or later 3D viewer is
built.

The contract validates:

- source-set and review export scopes, with `review_id` required for review-specific graphs;
- required node types for source sets, reviews, authority families, source records, artifacts,
  chunks, evidence spans, source claims, rule templates, applicability decisions, generated rules,
  compliance findings, forest-plan entities, readiness blockers, and graph lenses;
- required edge types for evidence paths, source/currentness relationships, package
  applicability, forest-plan overlays, compliance findings, and readiness blockers;
- required per-node provenance fields for each node type, including source-record, artifact,
  chunk, evidence-span, source-claim, rule-template, forest-plan, readiness-blocker, and graph-lens
  provenance;
- edge endpoint compatibility against the contract-declared source and target node types;
- display states for active, superseded, reserved, candidate, out-of-scope, applicable,
  not-applicable, unresolved, adjudicated, and readiness-blocked records;
- review-readiness states and blocker types so graph display status cannot be confused with
  reviewer readiness.
- lens metadata fields, required lenses, and referenced node, edge, and display-status values.

## NEPA 3D Source-Set Knowledge Graph Export

NEPA 3D Milestone 3 is implemented by `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`, the
`nepa-knowledge-graph-export` CLI command, `tests/test_nepa_knowledge_graph_export.py`, and the
generated source-set graph outputs under
`source_library/derived/<source_set_id>/knowledge_graph/`. The builder is read-only over audited
catalog and derived surfaces; it does not scan raw artifact filenames.

The live export command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8
```

The live export for `source-set-ba8d0feae79501b8` now records:

- `validation_passed=true`, `62` validation checks, `0` failed checks, and
  `failure_category_counts={}`;
- `1,470` nodes and `2,648` edges;
- source-set content: `35` authority families, `190` catalog source records, `160` artifact nodes,
  `48` base rules, `19` authority-family templates, `211` source-claim nodes, and `329`
  forest-plan component nodes;
- source input joins: `740` catalog graph seed nodes, `759` catalog graph seed edges, `211`
  rule-claim links, current authority-currentness validation, evidence graph node/edge inputs, and
  forest-plan component inventory;
- Region 1 profile readiness: `10` tracked forest/grassland profiles, `1` graph-ready profile, `9`
  blocked broader Region 1 profiles, `1` Milestone 5 added profile with positive and hard-negative
  applicability fixture contracts, `3` graph-visible field-directive requirements, and `5`
  graph-visible overlay requirement groups;
- readiness blockers remain visible as graph nodes and edges, including the scoped
  `fsh_chapter_delta_required`, `forest_profile_not_ready`, and `missing_source` blockers.

## NEPA 3D Review-Specific Applicability Overlay

NEPA 3D Milestone 4 is implemented by the same
`nepa-knowledge-graph-export` CLI command with `--review-id`. The review overlay writes
`nepa_3d_graph.json`, nodes, edges, summary, and validation files under
`source_library/reviews/<review_id>/knowledge_graph/`. It reads the existing applicability-first and
compliance artifacts for the selected review; it does not rerun applicability or compliance review.

The live review overlay command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review
```

The live overlay for `v1-cg-ecid-compliance-review` now records:

- `validation_passed=true`, `76` validation checks, `0` failed checks, and
  `failure_category_counts={}`;
- `1,996` nodes and `3,550` edges;
- review content: `377` candidate authority nodes/decisions, `37` applicable decisions, `340`
  non-applicable decisions, `37` generated rules, `37` compliance findings, and `340` search
  coverage certificates;
- review graph checks that every candidate maps to exactly one decision, every non-applicable
  decision has search coverage or adjudication support, search-coverage certificate IDs resolve to
  covering certificate records, referenced retrieval and graph trace IDs resolve, generated rules
  derive only from applicable decisions, and compliance findings link to generated rules plus
  evidence spans.

## NEPA 3D Region 1 Forest-Plan Readiness Expansion

NEPA 3D Milestone 5 is implemented by
`config/region1_forest_plan_readiness_nepa_3d_v1.json`, the Beaverhead-Deerlodge profile addition
in `config/forest_plan_profiles.json`, and expanded `nepa-knowledge-graph-export` validation. This
is a graph-readiness slice, not a broad source-capture rerun: it makes the broader Region 1
forest-plan universe visible while blocking any claim that Custer Gallatin artifacts prove Region 1
forest-plan completeness.

The readiness matrix now records:

- `10` tracked Region 1 forest/grassland profiles;
- `1` graph-ready profile: Custer Gallatin with validated `329`-component inventory and `58`
  standards;
- `1` Milestone 5 added active profile contract: Beaverhead-Deerlodge, with catalog-confirmed
  planning page and 2009 Forest Plan rows, positive and hard-negative applicability fixture
  contracts, and `component_inventory_build_required` before graph promotion;
- `9` blocked broader Region 1 profiles, visible through `forest_profile_not_ready` and
  `missing_source` graph blockers;
- `3` field-directive requirements and `5` overlay requirement groups, now rendered as
  graph-visible requirement nodes with source-record links where the readiness matrix has
  catalog-confirmed sources.

The graph export now validates that configured profiles and known Region 1 units are covered by the
readiness matrix, added profiles have source requirements and eval fixture contracts, promoted
profiles have catalog-confirmed sources and component inventory coverage, field-directive and
overlay requirements have graph nodes and source links, and `region1_completeness_claim=false`
while any tracked profile remains blocked.

## NEPA 3D Local Viewer

NEPA 3D Milestone 6 is implemented as a checked-in static viewer under `viewer/nepa-3d/`. The
chosen option is a repo-local browser surface over the normalized graph exports, not a generated
`source_library/` artifact and not a second knowledge base. The viewer uses Three.js plus
`3d-force-graph` from pinned CDN URLs, reads `viewer/nepa-3d/manifest.json` as a fallback manifest,
resolves the live dataset from `source_library/catalog/source_set_manifest.json` when possible, and
can load either the source-set graph or a matching review overlay graph. If the active catalog
source set has no graph export yet, the viewer falls back to the newest graph-capable source set
under `source_library/derived/`. It also accepts a local graph JSON file through the browser file
picker for ad hoc inspection.

Current viewer resolution state:

- active catalog source set:
  `source-set-d3b9e2a728accda6`
- newest graph-capable source set on disk:
  `source-set-8a4005c8a083af1a`
- current checked-in fallback manifest default:
  `source_library/derived/source-set-8a4005c8a083af1a/knowledge_graph/nepa_3d_graph.json`
- matching review overlays currently available for the resolved source set:
  none
- older review overlay still available for manual selection from the fallback manifest:
  `source_library/reviews/v1-cg-ecid-compliance-review/knowledge_graph/nepa_3d_graph.json`

Launch locally from the repo root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/viewer/nepa-3d/
```

The first viewport opens directly into the graph experience. It now defaults to the
`v1-cg-ecid-compliance-review` review overlay and its Applicability demo scene. Demo buttons above
the Lens dropdown switch among source library, authority graph, applicability, evidence path,
forest plan, readiness, and full graph scenes; Reset demo returns to the starting review and scene.
The evidence-path scene derives a source-record -> artifact -> chunk -> evidence-span ->
source-claim -> rule -> decision -> generated-rule -> compliance-finding spotlight from graph
edges, then exposes each step as a clickable item in the right-side Capability shown panel. Advanced
search and category controls remain available under Advanced filters. The graph surface now includes
scene labels for each demo scene and graph-native node labels rendered as Three.js sprites. Label
visibility is camera-distance aware: zoomed-out views show scene anchors, mid-zoom adds focus
labels, and close zoom adds additional node labels while preserving the same graph export and
readiness boundary. Controls cover source set, review, lens, search, status/readiness, authority
category, authority family, document role, currentness/partition, readiness blocker, node/edge type,
evidence/basis, forest unit, review phase, neighbor depth, high-degree hiding, selected-node
pinning, fit/reset, Clear filters, PNG export, and viewer-state JSON export. Lens and filter
dropdowns use graph-export counts and grounding metadata,
separate authority category from authority family, keep node/edge type distinct from evidence and
basis fields, read forest-unit values from exported forest codes, and treat selections as context
seeds so matching nodes remain visible even when the selected lens has no matching edges. The
detail panel shows node/edge provenance, citation labels, artifact hashes, source paths, currentness
metadata, and validation status. Static tests now lock the runtime URLs, relative graph-export
manifest paths, category/filter boundaries, and the `node_id`/edge endpoint mapping used by
`3d-force-graph`. The viewer status line explicitly records that layout does not change readiness.

## NEPA 3D Graph Validation And Promotion Gates

NEPA 3D Milestone 7 has its first promotion-gate slice implemented for the current source-set and
V1 review overlay graphs. Each graph validation check now carries a graph-specific
`failure_category`, and validation plus summary artifacts record `failure_category_counts`.
The summary now reports the Milestone 7 count dimensions explicitly: node type, edge type,
authority category, source status, source partition, source currentness status, applicability
status, and readiness blocker.
`phase-eval` adds `nepa_3d_source_set_graph` and `nepa_3d_review_graph` phases when those artifacts
exist. After review-packet row-completeness integration, the latest V1 review-bound phase eval
passes `21/21` phases with `reviewer_ready=true`, including both graph phases, the
`review_packet_index` phase, the final QA certification report, the post-V1 applicability family,
generated rule pack, decision-support report, compliance review, forest-plan component eval, and
gold eval.

## Review Packet Row Completeness

The East Crazies review packet now has a first-class row ledger and signer-facing index under
`source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/`. The generated family
includes `review_packet_row_inventory.json`, `review_packet_row_inventory.md`,
`compliance_matrix_render_manifest.json`, `review_packet_index.json`, `review_packet_index.md`,
`review_packet_index.pdf`, and `review_packet_index_validation.json`. The validation sidecar passes
with `37` applicable authority rows, `340` non-applicable authority boundary rows, `79` Forest Plan
component rows, `12` applicable Forest Plan standards, `4` dedicated land-exchange rows, `116`
rendered matrix rows, and no failed checks across `30` validation checks. It also keeps root-level
`East_Crazies_*` drafts out of the canonical packet boundary.

Decision support now live-validates that packet row sets match the compliance matrix and render
manifest without hashing downstream packet artifacts into the decision-support manifest. Final QA
does hash and gate the packet artifacts, exposes a `review_packet_index_qa` section, and validates
the refreshed packet at `196/196` checks. The current promotion suite requires the packet index
family plus final QA and passes current promotion with `31/31` required current results; South
Plateau remains expansion-blocked only by typed `forest_plan_reviewer_not_ready` gaps.

`config/promotion_suite_v1.json` now requires the source-set graph validation/summary artifacts and
the V1 review graph validation/summary artifacts before current promotion passes. The current live
graph gates pass with `62/62` source-set graph checks, `76/76` review graph checks,
`failure_category_counts={}`, `1,470` source-set graph nodes, `2,648` source-set graph edges,
`1,996` review graph nodes, and `3,550` review graph edges. Broader Region 1 profile readiness
blockers remain visible in the graph summaries and do not claim handbook or Region 1 forest-plan
completeness.

A NEPA 3D service capabilities brief is generated at
`docs/capabilities/nepa_3d_capabilities_brief.pdf` with matching HTML at
`docs/capabilities/nepa_3d_capabilities_brief.html`. The generator
`tools/build_nepa_3d_capabilities_brief.mjs` reads the current catalog manifest, source-set graph
summary and validation, phase-eval results, and promotion-suite status. It writes high-resolution
system graphics for the Region 1 knowledge-system architecture, evidence traceability, and the
Region 1 graph surface.
The brief presents reusable client-facing system capabilities and boundaries without named project
examples: the system structures fragmented Region 1 source, authority, evidence, and forest-plan
data for defensible, efficient land exchange execution. NEPA review is the V1 function, and the same
graph foundation can expand to additional workflows. Its three pages cover the core message,
supporting traceability architecture, and the R1 knowledge graph showcase with separate NEPA, USDA
regulation, source-evidence, and forest-plan layers.

## EA Consistency Decision-Support Generator

The East Crazies decision-support lane is complete through Sequence 5. Sequence 0 preflight recorded
the current artifact/count/hash baseline and closed with `go`; Sequence 1 added the tracked report
contract; Sequence 2 added the deterministic generator and public CLI command; Sequence 3 generated
the first local report family for the promoted East Crazies review; Sequence 4 made that family a
checked validation, phase-eval, and promotion-suite gate; Sequence 5 polished the Markdown/PDF
renderings for responsible official review without changing the canonical JSON schema. The tracked surfaces
are:

- `config/ea_consistency_decision_support_v1.json`
- `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
- `tests/fixtures/decision_support/minimal_decision_support_report.json`
- `tests/test_ea_consistency_decision_support.py`
- `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`
- `src/usfs_r1_ea_sources/cli_decision_support.py`
- `docs/OUTPUT_SCHEMAS.md`

The command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
```

The existing generated report can be validated without rewriting it with:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only
```

The generator reads existing audited review artifacts and tracked config/fixture contracts, compares
the Sequence 1 hash/count baseline, fails closed on stale, missing, non-reviewer-ready, or
hash-mismatched inputs, and writes:

- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.json`
- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.md`
- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.pdf`
- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support_manifest.json`

The generated report keeps applicability status, compliance status, implementation-confirmation
status, and residual risk/legal-conclusion flags separate. The 2026-05-06 East Crazies run wrote the
ignored local report family under
`source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`:

- `ea_consistency_decision_support.json`
- `ea_consistency_decision_support.md`
- `ea_consistency_decision_support.pdf`
- `ea_consistency_decision_support_manifest.json`

The latest Sequence 5 closeout regenerated and then validated that ignored local report family.
Validation returned `passed=true` and `reviewer_ready=true`, rechecked all current input hashes and
required report sections, kept all `37` applicable authority findings with package/source evidence,
kept the `340` non-applicable authority boundary with search coverage, represented all `329` Forest
Plan component rows, covered all `12/12` applicable standards with package and plan evidence, kept
`9` implementation-confirmation rows with evidence and `3` residual-risk notes with `0`
legal-conclusion risk flags, and confirmed the PDF starts with `%PDF-`. The Markdown/PDF now
front-load a use note, bottom-line reviewer-ready status, authority categories, Forest Plan basis,
applicable standards, non-applicable boundary, implementation confirmations, residual risks,
validation status, and concise table summaries before long evidence sections. The same closeout
replayed `phase-eval --review-id v1-cg-ecid-compliance-review`, which includes
`decision_support_report`; the current graph-gate pass now has V1 review-bound phase eval passing
`21/21` phases with `review_packet_index` and `reviewer_ready=true`. `promotion-suite` also reports the decision-support
JSON, manifest, PDF, and NEPA 3D graph validation/summary artifacts as required current-promotion
artifacts.
The post-sequence gap-close pass also makes validation fail closed when otherwise-current Markdown
or PDF outputs omit the supervisor-review front matter, review snapshot, table summaries, key
counts, required sections, or source-pointer content; those failures use
`false_negative_synthesis_omission` with explicit rendering source selectors. Generated
`source_library/` outputs remain ignored and are not staged. The EA consistency decision-support
milestone has no remaining planned sequence; future work should be a new milestone or a targeted
copy-review pass.

## East Crazies Final QA And Certification Replay Plan

`docs/EAST_CRAZIES_FINAL_QA_CERTIFICATION_MILESTONE_PLAN.md` is the completed focused plan for
turning the promoted East Crazy review into a replayable final QA packet. Sequence 0 baseline
replay, Sequence 1 contract/fixture work, Sequence 2 deterministic generator/CLI work, Sequence 3
gate integration, and Sequence 4 final packet QA/closeout are complete. The milestone is bounded to
review ID
`v1-cg-ecid-compliance-review` and source set `source-set-ba8d0feae79501b8`; it does not broaden
the claim to other Region 1 packages, does not resolve the South Plateau strict-expansion blocker,
and does not treat root-level `East_Crazies_*` draft exports as canonical artifacts.

Sequence 0 verified the promoted final-QA baseline from generated artifacts: `37` applicable
authorities, `340` non-applicable authorities, `0` unresolved authorities, `377` candidate
authorities, `37` generated compliance findings, `162` generated-pack rule-claim links,
`0` rule-claim gaps,
`43` package files, `1,265` package chunks, `329` Forest Plan component rows, `58` Forest Plan
standards, `12/12` Custer Gallatin applicable standards, passing decision-support validation, and
review-bound baseline `phase-eval` at `19/19` before final QA gate integration. Sequence 3 added
the final QA validation sidecar, review-scoped `phase-eval` passed `20/20` with
`final_qa_certification_report`, and non-strict `promotion-suite` passed `26/26` required
current-promotion results. The later row-completeness closeout adds the `review_packet_index` phase,
and the current replay passes `21/21` phase results and `31/31` current-promotion results. South
Plateau strict-expansion blockers remain separate as
`expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.
Generated final QA outputs live under
`source_library/reviews/v1-cg-ecid-compliance-review/final_qa/` and stay ignored unless repository
policy changes.

The replay sequences are:

- Sequence 0: baseline replay and drift check over existing generated artifacts; complete on
  2026-05-07.
- Sequence 1: final QA contract and fixtures; complete on 2026-05-07.
- Sequence 2: deterministic generator and CLI with `--validate-only`; complete on 2026-05-07.
- Sequence 3: `phase-eval` and promotion-suite integration; complete on 2026-05-07.
- Sequence 4: rendered packet QA, docs/handoff closeout, and atomic commit; complete on
  2026-05-07.

Sequence 4 closed the remaining packet QA issues. `v1-ea-eval` now preserves `generated_at` when
the semantic payload is unchanged, so reruns no longer churn the final QA input hash. After the
row-completeness closeout, the final QA report renders both baseline counts that exclude final-QA
self-reference (`20/20` phase eval and `27/27` current-promotion results) and live integrated
counts (`21/21` phase eval and `31/31` current-promotion results). The final closeout stack is
ordered so mutating V1 eval output runs before the final QA refresh; the final validate-only replay
then still passes after `phase-eval` and non-strict `promotion-suite` add only the permitted final-QA
outer-gate drift.

The 2026-05-08 gap-close replay accepted the land-exchange row-contract hardening. The
decision-support expected summary and final-QA expected summary now carry
`required_applicable_authority_rows` for all four first-class land-exchange rows, and validation
fails closed with `missing_applicable_authority_row` if any required row is absent or loses its
expected source record, authority family, applicability mode/status, or pass status.
`final-qa-certification` refreshed the ignored packet and passed `196/196`;
`final-qa-certification --validate-only` also passed `196/196` without rewriting outputs after the
outer gate replay. The CLI result includes the review packet index, render-manifest, outer
self-reference, freshness, and required-row checks around that sidecar. The rendered Markdown
exposes the required caveats, source pointers, accepted V1 risk ledger, residual blockers,
baseline/live gate counts, and root-level draft exclusion, and the generated PDF starts with
`%PDF-1.4`.

Sequence 1 added `config/east_crazies_final_qa_certification_v1.json`,
`config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json`,
`tests/fixtures/final_qa/minimal_final_qa_certification_report.json`,
`tests/test_final_qa_certification.py`, and the schema docs. The contract pins semantic counts,
source selectors, current artifact hashes, selected Markdown/PDF rendering requirements, optional
human reviewer signoff fields, accepted V1 risk visibility, and fail-closed categories without
pinning full rendered body text. The Sequence 1 gap-close pass now requires every scalar
expected-summary count to appear in `required_count_fields`, keeps config and expected-summary
sections/output files/failure categories aligned by test, and records `validation_expectations`
that map missing gates, stale hashes/artifacts, count drift, missing selectors, missing
non-applicable boundary evidence, unresolved reviewer items, invalid PDF output, manual draft
dependency, hidden accepted V1 risk, legal-conclusion leaks, and human-certification overclaims to
fail-closed categories.

Sequence 2 added the `final-qa-certification` CLI command and the
`src/usfs_r1_ea_sources/final_qa_certification.py` artifact reader. Sequence 3 added
`east_crazies_final_qa_certification_validation.json` as the validation result consumed by
outer readiness gates. A live generation pass for `v1-cg-ecid-compliance-review` wrote the ignored
JSON, Markdown, PDF, manifest, and validation outputs under
`source_library/reviews/v1-cg-ecid-compliance-review/final_qa/`; a follow-up `--validate-only`
replay passed `168/168` checks without rewriting outputs. The command validates required gate
selectors, pinned input hashes, source/source-set identity, semantic counts, configured source
selectors, required applicable authority rows, PDF headers, accepted V1 risk visibility,
legal-conclusion safeguards, and the non-canonical root-level draft boundary. The validator tolerates
the self-referential outer
phase-eval/promotion-suite hash drift only when the extra passing gates are exactly the final QA
outer gates. The Sequence 3 gap-close pass records JSON/Markdown/PDF/manifest output hashes in the
validation sidecar and makes `promotion-suite` compare those hashes against the local files before
current promotion can pass. The Sequence 2 gap-close pass carries all `37`
compliance-matrix authority findings in `finding_qa.findings`, with per-row compliance-matrix
selectors, package/source evidence pointers, and trace IDs.

Certification in this plan means deterministic machine replay plus optional human reviewer signoff
fields. It does not mean final legal sufficiency, responsible-official approval, or counsel
certification.

## Project SOW Requirements Package

Project SOW package generation and operationalization through Sequence 7 are implemented as an
upstream planning lane for proposed-action intake before a complete EA review package exists. The
core package command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
```

The command reads a structured `project-sow-intake-v0` JSON file, the tracked resource-scope config
at `config/project_sow_resource_scopes_v1.json`, and
`config/authority_universe_families_nepa_ea_v1.json`. It writes a local requirements package under
`source_library/projects/<project_id>/requirements_package/`:

- `project_sow_package.json`
- `project_sow_package.md`
- `project_sow_package.pdf`
- `project_sow_package_manifest.json`

The package scopes resource-specialist work needed to prepare a defensible EA package. It selects
resource scopes from explicit intake fields, project type, trigger terms, resource indicator keys,
and proposed-action resource-area IDs, then records scope of work tasks, data needs, deliverables,
defensibility checks, selected authority families, an authority-to-resource matrix, and a
resource-analysis coverage matrix, and a compact reviewer summary with package boundaries and a
review checklist. The reviewer summary separates unresolved resource areas from calibration gaps
where scope of work content is required but no observed East Crazies report was supplied for that area. It also
emits a package-local intake evidence graph connecting project, proposed action, action elements,
evidence refs, triggered resource areas, selected resource scopes, required deliverables, and observed
specialist/supporting reports. JSON is canonical; Markdown and PDF are renderings from the same
package JSON. The first checked-in intake fixture is the East Crazies
land-exchange proposed action and currently selects ten resource scopes: NEPA project management,
lands/realty land exchange, Forest Plan consistency, wildlife/species/botany, cultural/tribal
resources, hydrology/wetlands/water quality, roads/access/recreation/designated areas,
vegetation/soils/air-quality/climate/carbon, minerals/energy/hazardous materials, and public
involvement/coordination.

The East Crazies fixture now also compares proposed-action-derived resource areas to the actual
specialist/supporting reports observed in the completed package: mineral potential, aquatics,
at-risk plants/botany, carbon, cultural resources, recreation special areas, recreation special
uses, roads/trails/access, tribal relations, wetlands, wildlife, water rights, and the
plan-consistency table. Validation requires every observed report resource area to have selected
resource scope coverage and to be traceable to a proposed-action resource area in the intake.

Operationalization Sequence 5 adds the reviewer adjudication loop:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-template \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-eval \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --adjudication <completed-project-sow-adjudication.json>
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-apply \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --adjudication <completed-project-sow-adjudication.json> \
  --output-intake <adjudicated-intake.json>
```

The template/worklist covers unresolved resource areas, missing evidence refs, unknown resource-area
IDs, calibration gaps, and optional deliverable decisions. Eval fails closed on stale input hashes,
missing, duplicated, unexpected, pending, invalid, or queue-identity-tampered rows, and incomplete
top-level or per-item reviewer metadata. Apply reruns eval and writes an adjudicated intake copy
with `project_sow_adjudication` replay metadata, including top-level reviewer metadata. Generated
packages from that intake surface adjudication status and decision counts in the reviewer snapshot
and command summaries. It does not mutate the original intake and does not edit generated package
outputs by hand.

Operationalization Sequence 6 adds the downstream EA package assembly handoff:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-ea-package-handoff \
  --package source_library/projects/<project_id>/requirements_package/project_sow_package.json
```

The command reads a passing canonical `project_sow_package.json` plus
`config/project_sow_ea_handoff_rules_v1.json` and writes
`project_sow_ea_package_handoff.json` plus `project_sow_ea_package_handoff.md`. East Crazies
currently emits `27` expected future-artifact slots: `10` source-collection, `10`
specialist-report-production, `1` public-involvement, `3` consultation, `1` Forest Plan
consistency, and `2` decision-record-support slots. Future artifacts are checklist expectations
only; the command does not require them to exist.

The Sequence 6 gap-close pass adds an explicit downstream consumption contract and tightens
handoff-rules validation. Future commands may consume package identity, input hashes, assembly
categories, assembly slots, and downstream boundaries, but must not infer artifact existence,
artifact sufficiency, authority applicability, generated rule-pack readiness, compliance findings,
legal advice, legal sufficiency conclusions, or final agency decisions from the handoff alone.

Operationalization Sequence 7 adds the local-only operational readiness gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \
  --output-dir source_library/project_sow_operational_gate
```

The gate runs no-write intake validation for the minimal template and the three proving intakes,
the three-case `project-sow-eval`, package/rendering smoke checks for generated proving packages,
an East Crazies EA handoff smoke, and tracked JSON/docs checks before writing
`project_sow_operational_gate_summary.json` and `project_sow_operational_readiness_report.md`.
The command is intentionally not broad CI yet; the Sequence 7 closeout records it as local-only
until CI adoption is scoped as a separate milestone.
The Sequence 7 gap-close pass adds a machine-readable `closeout_contract`, expands tracked
docs/schema checks across the durable closeout set, fails closed on missing closeout-doc references,
and records output hashes for the gate report, proving eval summary, and EA handoff smoke artifacts.
The milestone closeout alignment pass adds
`docs/PROJECT_SOW_OPERATIONALIZATION_ACCEPTANCE_MATRIX.md`, which maps Sequences 1 through 7 to
their acceptance criteria and verification evidence; the operational gate now checks that matrix as
part of the durable-doc closeout set.

A scope of work service capabilities brief is generated at
`docs/capabilities/project_sow_capabilities_brief.pdf` with matching HTML at
`docs/capabilities/project_sow_capabilities_brief.html`. The generator
`tools/build_project_sow_capabilities_brief.mjs` mirrors the NEPA 3D capabilities-brief style and
uses the tracked system design artifacts rather than a single project example. The brief explains the service lane
for producing scopes of work: structured proposed-action intake, traceable resource selection,
contract-ready work package rendering, reviewer adjudication, operational-readiness gate, and
downstream EA package assembly handoff. It is two pages and intentionally general, with page-one
purpose and system facts sections plus a consolidated system-capability graphic replacing
project-example metric tiles.

An earlier requirements-package Sequence 5 CLI smoke run for the East Crazies intake selected `10`
resource scopes, found `23` proposed-action resource areas, emitted a `115`-node and `134`-edge intake
evidence graph, wrote a PDF with a valid `%PDF-` header, and reported `0` validation failures. Each
proposed-action-derived resource area has the canonical planning path:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

The requirements-package sequence plan for this lane is
`docs/PROJECT_SOW_REQUIREMENTS_PACKAGE_MILESTONE_PLAN.md`. The successor operationalization plan is
`docs/PROJECT_SOW_OPERATIONALIZATION_MILESTONE_PLAN.md`; Sequence 7 closes the operational gate and
release-closeout boundary for this branch.

This is a planning artifact only. It does not create applicability decisions, generated rule packs,
compliance findings, legal advice, legal sufficiency determinations, or final agency decisions.
Validation fails closed on missing required intake fields, unsupported intake schema, empty or
duplicated resource-scope config, unknown authority-family IDs, proposed-action resource areas that
cannot resolve to selected resource scope coverage, observed specialist-report resource areas that are
not derived from the proposed action or lack selected resource scope coverage, no selected resource
scopes, selected scopes without scope of work content, duplicate intake-derived graph IDs including
observed-report and required-deliverable collisions before graph assembly deduplicates nodes and
edges, dangling graph edges, missing action-element evidence refs, evidence-bearing action elements
with no triggered resource area, incomplete canonical resource-area graph paths, observed
specialist report areas without a proposed-action support path, land-exchange intakes with no
federal land action, or Markdown/PDF renderings missing required reviewer-facing sections.
Project-SOW adjudication eval additionally fails closed on stale hashes, missing queue rows,
unexpected or duplicate rows, changed queue identity fields, invalid item types, invalid decisions,
pending decisions, or incomplete reviewer metadata.
Project-SOW EA handoff validation additionally fails closed on invalid package schema, failed
package validation, missing selected scopes, unsupported handoff rules schema, incomplete handoff
categories, missing required handoff categories, unresolved or incomplete category rules,
incomplete downstream boundaries, missing explicit downstream boundary IDs, empty slots, or slots
without expected future artifact content.

## Verified State Snapshot

Latest corpus-update verification was run locally on 2026-05-01 after adding the missed Custer
Gallatin FEIS and ESA-supporting plan documents.

- Active catalog source set: `source-set-d3b9e2a728accda6`
- Download/catalog batch: `corpus-update-2026-05-01-cg-support-batches`, `52/52` batches passed
- Catalog: `190` source rows, `160` unique raw artifacts, `189` source-artifact links
- Custer Gallatin supporting PDF records added: `R1PLAN-custer-gallatin-nf-04` through
  `R1PLAN-custer-gallatin-nf-07`
- Reuse inventory for the current source set is implemented and has been run locally. It classified
  `7` sources as already current in the Custer Gallatin slice, `181` sources as reusable from prior
  extraction outputs, `1` source as needing extraction, and `1` source as excluded.
- Reuse-first extraction assembly has been run for the full source set. It produced `190` terminal
  extraction manifest rows: `189` extracted rows, `1` scope-excluded row, `18,822` chunks,
  `188` reused rows, and `0` failed rows. `R1PLAN-dakota-prairie-grasslands-02` was parsed as the
  one fresh HTML extraction.
- Retrieval has been rebuilt from the assembled extraction layer with `18,822` chunks and
  `reviewer_ready: true`.
- Extraction accuracy audit passed for the current source set: `190` records checked, `189`
  extracted records, `18,822` chunks, no text-hash, raw-hash, offset, gap-coverage, markup, eCFR
  scope, or PDF token cross-check failures.
- Evidence graph has been rebuilt and is reviewer-ready with `38,601` nodes, `134,501` edges, and
  `0` retrieval-binding mismatches.
- Source-claim extraction has been rebuilt and is reviewer-ready with `43,353` claims, `9,818`
  entities, and `1.0` claim evidence/topic/authority coverage rates.
- Rule-claim binding for rule pack `nepa-ea-v0` version `0.4.0` has been rebuilt with `211` links
  across `48/48` rules, `0` gaps, and no rules without source-claim links.
- Compliance coverage has been refreshed for the `48`-rule matrix and `3` seed eval cases.
- Compliance review eval passed `3/3` seed cases. The Custer-scoped all-authorities fixture now
  expects `reviewer_ready: false` when the full forest-plan component gate is unmet.
- Compliance gold eval passed `10/10` adjudicated cases in the pre-applicability V1 artifact set.
  Under the current Milestone 8 gate, base-rule-pack gold eval reruns are diagnostic and are not
  `promotion_ready`; promotion readiness now requires a reviewer-ready generated applicability rule
  pack. Custer-scoped gold fixtures likewise preserve rule-level expected statuses while expecting
  the overall forest-plan component gate to fail readiness unless component evidence coverage is
  complete.
- Phase eval passed `19/19` phases with `reviewer_ready: true` for
  `source-set-ba8d0feae79501b8` and `v1-cg-ecid-compliance-review`, including the post-V1
  applicability artifact family, generated rule-pack gate, decision-support-report gate, and
  NEPA 3D source-set/review graph gates.
- The current Custer Gallatin LMP component inventory was generated from the active source-set
  chunks: `329` components, `58` standards, `536` selected plan chunks, `0` missing component IDs,
  `0` duplicate component or standard IDs, and `2` non-blocking inventory-quality issues.
  Component-like labels with nonnumeric number tokens, such as cross-reference/table headings, are
  suppressed from generated component IDs and surfaced in build coverage.
- Current generated-pack V1 EA gate artifacts were verified locally on 2026-05-08 for
  `v1-cg-ecid-compliance-review`. The regenerated compliance review is reviewer-ready with `37`
  generated compliance findings, `37` pass findings, all `26` baseline source records evaluated
  through the generated applicability rule pack, `162` generated-pack rule-claim links, and `0`
  rule-claim gaps.
- Forest-plan component eval passed `35/35` adjudicated cases for the promoted review. The current
  component findings have `329` components, `79` supported components, `250` not applicable
  components, `0` gaps, `12/12` applicable standards applied, and `0` reviewer-resolution items.
- The final pre-applicability V1 gate commands passed: `phase-eval` `10/10`, `v1-ea-eval` with
  `broader_ea_passed=true` and `forest_plan_passed=true`, `compliance-review-eval` `3/3`, and
  `compliance-gold-eval` `10/10`. Direct base-pack review/gold reruns are diagnostic; the current
  generated-pack review-bound phase eval can use the passing base-pack gold suite through
  `rule_pack_match_mode=generated_base`.
- The post-V1 applicability run for `v1-cg-ecid-compliance-review` validates cleanly with `377`
  candidate authorities, `37` applicable authorities, `340` not-applicable authorities, no
  unresolved/adjudication decisions, and `generated_rule_pack_ready=true`; the generated rule pack
  contains `37` rules and validates against the applicability artifacts.
- Authority-universe Milestone 5 is implemented in the compliance review layer. Generated review
  findings now carry candidate authority IDs, applicability decision IDs, authority-family IDs,
  generated applicability provenance, and coverage/adjudication references. The promoted review
  writes `authority_family_provenance.json`, `non_applicable_authority_appendix.json/.md`,
  `authority_reviewer_resolution_report.json`, and `litigation_risk_summary.json`; promotion
  checks require those artifacts before current promotion can pass.
- The post-V1 promotion suite is implemented at `config/promotion_suite_v1.json`. Sequences 1, 2,
  2A, and 2B have closed the ECID `adjudication_needed`, `missing_source`, and
  `forest_plan_reviewer_not_ready` expansion blockers. Sequence 3 selected the South Plateau Area
  Landscape Treatment Project as the third real package under review ID
  `region1-expansion-south-plateau-landscape-treatment`. Sequence 4 imported `26` official South
  Plateau PDFs from the project Box folder, built the package cache with `.venv-docling`, extracted
  `26/26` files into `3,671` chunks, and ran the applicability-first path through validation.
  Sequence 5 completed the six positive/negative-trigger adjudications as replayable
  `human_applicable` decisions, evaluated and applied them, and reran validation. Sequence 6 then
  generated and validated the South Plateau rule pack, ran compliance review, matrix/PDF output,
  review-scoped phase eval, and added South Plateau required expansion artifact checks to the
  promotion suite. South Plateau applicability validation passes: `61` authorities are applicable,
  `331` are non-applicable, `0` are unresolved or `needs_adjudication`, and
  `generated_rule_pack_ready=true`. Generated rule-pack validation passes with `61` rules and hash
  `39663183f91ad309fcfad60a17d0d88b371e184df8f06664cadd612b5c7aebec`. The authority-review layer
  still emits `61` findings, `41` pass, `19` uncertain, `1` gap, `280` rule-claim links, and `0`
  rule-claim gaps. The South Plateau forest-plan context pass now resolves the package to
  `scope_status="custer_gallatin"` with context `validation_passed=true`, `2` geographic areas,
  `9` management areas, `4` overlays, `5` supporting-plan routes, and `0` unresolved mentions.
  The remaining blocker is narrower: forest-plan component evaluation has `329` components,
  `152` applicable components, `24` applicable standards, `21` applied standards, and `31`
  `missing_package_evidence` items in the component adjudication worklist. The South Plateau
  expansion slot remains `ready=false` with `failure_category="forest_plan_reviewer_not_ready"`,
  and the manifest now records the component findings, reviewer queue, adjudication template, and
  pending adjudication eval as expected gate artifacts. Strict
  promotion suite was written to
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion/`
  and now fails as expected with `current_promotion_ready=true`, `promotion_ready=false`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`,
  `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`. Non-strict promotion suite
  was rerun last and keeps current promotion green with `current_promotion_ready=true`,
  `promotion_ready=true`, `failure_category_counts={}`, and the same expansion-only blocker counts.
  Promotion-suite manifest validation now fails selected not-ready slots that omit
  review/package/source-set metadata, expected gate artifacts, next action, or a typed
  non-`package_fixture_missing` failure category. Ready slots must retain that
  review/package/source-set contract, omit failure categories, and list expected gate artifacts
  covering the matching review case's `required_for_expansion` artifact IDs; declared forest-plan
  profile slots must also prove reviewer-ready profile context before strict expansion can pass.
- The first Milestone 10 expansion pass has a local review ID:
  `region1-expansion-ecid-preliminary-ea`. The package cache extracted `7` PDFs into `160` chunks.
  Evidence-arbitration Milestone 4 replay covered `392` candidate authorities, with `43`
  applicable, `346` non-applicable, and `3` `needs_adjudication` authorities. The Sequence 1
  adjudication replay resolved cultural-resource/SHPO, minerals/energy, and species-supporting
  sources/overlays to `human_applicable`; `applicability-validate` now passes with `46` applicable
  authorities, `346` non-applicable authorities, `0` unresolved, `0` `needs_adjudication`,
  `generated_rule_pack_ready=true`, and `reviewer_ready=true`.
- The Sequence 2 ECID artifact pass generated and validated
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/generated_rule_pack.json`
  with `46` rules, ran compliance review with that generated rule pack, wrote the compliance
  matrix JSON/Markdown/PDF, wrote
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/phase_eval_results.json`, and
  generated `forest_plan_component_adjudication_template.json/.md`. The generated-pack gate passes,
  and Sequence 2A reports `rule_claim_gap_count=0` and `rule_claim_link_count=211`. Sequence 2B
  completed the `158`-item Forest Plan component adjudication replay, ran
  `forest-plan-component-adjudication-eval`, reran ECID compliance review with
  `--reuse-package-cache`, and reran review-scoped phase eval. The adjudication eval resolved all
  `158` rows as true EA package-evidence omissions with `0` system misses; compliance review now
  reports `reviewer_ready=true` and validation passes without treating those omissions as component
  support. The Sequence 2B closeout pass also tightened the adjudication template/eval contract so
  resolved items carry compact component/source trace references and fail if source-record,
  citation, hash, chunk/page, or available offset/span fields are dropped.
- The ECID roads/access/special-use adjudication item exposed the pre-Milestone-3
  evidence-arbitration gap: weak auxiliary trigger evidence could block an authority family even
  when strong independent roads/access/right-of-way evidence was present. The repair sequence is
  documented in `docs/EVIDENCE_ARBITRATION_MILESTONE_PLAN.md`.
- Evidence-arbitration Milestones 1 and 2 are implemented as behavior-preserving diagnostics.
  Applicability decision rows include `arbitration_summary` records, `applicability_report.md`
  renders arbitration diagnostics for `needs_adjudication` rows, and package/decision evidence now
  carries structured `evidence_strength` details while preserving existing `confidence_class`
  values. The Milestone 1/2 gap-close pass tightened weak-signal reason strings, expanded
  no-action/no-change background classification, preserved matched negative phrases when available,
  and added package graph assertions for fact/context/uncertainty `evidence_strength` fields. This
  diagnostic foundation is now used by Milestone 3.
- Evidence-arbitration Milestone 3 is implemented as the behavior-changing trigger-arbitration
  predicate. Strong, rule-contract-sufficient positive trigger groups can now carry an
  `applicable` decision while weak auxiliary trigger evidence stays visible in arbitration notes,
  reviewer notes, report diagnostics, and decision evidence. All-weak positives still require
  adjudication, and strong positive evidence plus explicit negative/out-of-scope evidence still
  requires adjudication by default.
- Evidence-arbitration Milestone 4 is implemented as the real-package replay/gate-alignment slice.
  ECID roads/access/special-use, Clean Water Act/WOTUS, and EO 11988 floodplain authority-family
  templates now resolve to `applicable` from strong independent trigger evidence. The later
  post-V1 expansion Sequence 1 replay resolved the remaining ECID cultural-resource/SHPO,
  minerals/energy, and species-supporting sources/overlays conflicts through replayable
  adjudication. Forest Plan component non-applicable decisions carry explicit scope-miss evidence,
  and ECID applicability validation now passes with no unresolved authority conflicts.
- Evidence-arbitration Milestone 5 is implemented as the eval and promotion/phase reporting slice.
  `applicability-eval` now has `9` seed cases with explicit arbitration expectations covering
  strong-positive plus weak auxiliary evidence, weak-only evidence, positive/negative conflicts,
  no-action/background-only evidence, and rule-template-specific trigger sufficiency. The latest
  local eval run passed `9/9` seed cases with arbitration status/effect match rates of `1.0` and
  arbitration summary counts of `1` applicable-with-weak-auxiliary, `2` weak-only
  needs-adjudication, `1` insufficient-strong-trigger needs-adjudication, and `1`
  positive/negative-conflict needs-adjudication. `applicability-gold-eval` passed `5/5` cases and
  now requires at least one gold case with explicit arbitration-field expectations.
- Latest South Plateau forest-plan context verification on 2026-05-07 reran the cached South
  Plateau compliance review, generated the `31`-item forest-plan component adjudication template,
  evaluated it in pending state, reran South Plateau phase eval at `15/17`, restored the promoted
  V1 review-scoped phase eval at `20/20`, passed non-strict promotion with
  `current_promotion_ready=true`, and proved strict expansion fails only on
  `forest_plan_reviewer_not_ready`.
- Latest NEPA 3D graph-gate verification on 2026-05-06 regenerated the source-set and V1 review
  graph exports, reran V1 review-scoped phase eval at `19/19`, and passed non-strict promotion
  suite with `22/22` required current-promotion results, `failure_category_counts={}`, and
  `expansion_failure_category_counts={}`. Latest post-V1 real-package expansion verification on
  2026-05-06 reran South Plateau review-scoped phase eval at `16/16`, restored the promoted V1
  review-scoped phase-eval artifact at `19/19`, kept non-strict current promotion green, and made
  strict expansion fail closed only on `forest_plan_reviewer_not_ready`. Focused pytest,
  architecture-contract, ruff, compileall, JSON validation, and `git diff --check` gates are the
  closeout verification for the
  tracked slice.
- The evidence-arbitration plan is complete through commit `f304e2e`. The post-V1 real-package
  expansion milestone is complete through Sequence 7 for the declared ECID preliminary-EA and South
  Plateau expansion slots. The South Plateau forest-plan context milestone is complete in the
  typed-blocker state: Custer Gallatin context is resolved, but strict expansion is intentionally
  blocked until the 31-item component adjudication queue is completed and passes eval. Future
  expansion should add a new
  verified real-package slot and matching promotion-suite review-case artifact checks rather than
  weakening the current gate.

Previous full downstream promotion snapshot was verified locally on 2026-04-30 before the rule-pack
`0.4.0` baseline expansion and before the later 186-row and 190-row catalog updates.

- Active source set: `source-set-e364ea220cffd938`
- Base phase eval: passed, `8/8` phases reviewer-ready
- Compliance phase eval: passed, `9/9` phases reviewer-ready for
  `demo-compliance-matrix-authority-v03-ecid-2026-04-30`
- Catalog: `147` source rows, `131` unique raw artifacts
- Extraction: `147/147` selected sources extracted, validation passed
- Retrieval: `13,619` chunks indexed, validation passed, reviewer-ready
- Evidence graph: `36,578` nodes, `106,182` edges, validation passed, reviewer-ready
- Retrieval-to-graph binding mismatches: `0`
- Source claim graph: `35,348` claims, `8,479` entities, `90,153` nodes, `231,214`
  edges, validation passed, reviewer-ready
- Claim eval seed: passed, `2/2` cases
- Rule-claim binding: `92` links across `20/20` authority compliance rules, `0` explicit no-claim
  gaps, validation passed, reviewer-ready
- Rule-claim eval seed: passed, `20/20` authority cases
- Compliance coverage: `20/20` rules covered by matrix rows, source-claim links, source-claim
  terms, and compliance review eval cases
- EA review smoke: `review_validation.json` passed for `smoke-ea-review-v0-hardened`
- Compliance demo review: authority-first `compliance_validation.json`, `compliance_matrix.json`,
  and `compliance_matrix.pdf` passed for
  `demo-compliance-matrix-authority-v03-ecid-2026-04-30` under the pre-`0.4.0` 20-rule pack
- Compliance review eval seed: passed, `3/3` cases
- Compliance gold eval: passed, `10/10` adjudicated cases in the pre-applicability gate; base-pack
  reruns are now diagnostic and not `promotion_ready`
- Unit suite: `132` tests passed

Post-baseline-expansion verification on 2026-04-30:

- `config/compliance_rule_pack_nepa_ea_v0.json` validates with `26` declared baseline source records
  and `44` total rules.
- `tests/test_compliance_review.py` passes with `32` tests.
- `git diff --check` passed before commit `720d75c`.
- Superseded by the 2026-05-01 current-source-set refresh above, which closed the
  `forest_service_directives_portal` / `R1EA-028` source-claim link gap and promoted coverage/gold
  eval artifacts for rule-pack `0.4.0`.

The full downstream promotion verification set for the prior 147-row source set was:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src python -m compileall src
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --review-id demo-compliance-matrix-authority-v03-ecid-2026-04-30 \
  --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id demo-compliance-matrix-authority-v03-ecid-2026-04-30
```

## Storage Model

The system stores source material in layers.

### Raw Artifacts

Path:

```text
source_library/artifacts/raw/
```

Raw artifacts are downloaded bytes saved before extraction or transformation. They are grouped by host and named with stable source/title slug information plus a SHA256 prefix. The downloader does not overwrite validated artifacts during normal resume behavior.

Artifact metadata is recorded in manifests and catalog records:

- `artifact_path`
- `artifact_sha256`
- `artifact_byte_size`
- `content_type`
- `fetch_timestamp`
- `final_url`

### Row Manifests

Path:

```text
source_library/manifests/download_<run_id>.jsonl
```

Each manifest is JSONL with one row per workbook source in that run. A row records workbook provenance, original URL, effective URL after overrides, normalized URL, final URL, artifact metadata, status, duplicate links, validation result, and failure evidence when applicable.

For full-batch operation, the parent batch ledger points to many child download manifests.

### Batch Evidence

Current parent batch path:

```text
source_library/runs/corpus-update-2026-05-01-cg-support-batches/
```

The parent batch run contains:

- `batch_plan.json`
- `batch_ledger.json`
- `summary.json`
- `operator_report.md`
- `repair_queue.csv`

Each child batch also has its own run directory under `source_library/runs/<child-run-id>/` with its own summary, report, events, failures, and acceptance gate.

### Reviewer Catalog

Path:

```text
source_library/catalog/
```

The catalog contains:

- `source_catalog.jsonl`: one reviewer-facing source record per workbook row
- `source_set_manifest.json`: versioned source-set metadata and counts
- `catalog_validation.json`: reviewer-catalog acceptance gate
- `review_sources.sqlite`: queryable index for the EA review engine
- `source_graph_nodes.jsonl`: portable graph seed nodes
- `source_graph_edges.jsonl`: portable graph seed edges

The reviewer catalog links every artifact-bearing workbook row to an artifact, including
duplicate-content rows. Scope-excluded rows remain in the catalog with `skipped_excluded` status and
no artifact link.

## Extraction, Retrieval, Review, And Graph Status

The raw source library does not store semantic chunks. A derived extraction layer is implemented
through `extract-build`; it reads the reviewer catalog, rehashes artifacts, and writes rebuildable
extracted text, chunk JSONL, and extraction diagnostics under
`source_library/derived/<source_set_id>/`.

The first retrieval layer is also implemented through `retrieval-build`. It indexes extracted
chunks into a local SQLite evidence index and supports deterministic text queries filtered by
document role, authority level, source record, review topic, citation label, and host.

The document evidence graph layer is implemented through `evidence-graph-build`. It turns extracted
chunks and retrieval metadata into graph artifacts for source documents, raw artifacts, extracted
text, sections, chunks, evidence spans, parsers, and review topics. It is a graph substrate for
auditable review; source-text legal claims are handled by the separate claim graph layer.

Source Claim Graph V0 is implemented through `claim-extract`. It extracts deterministic legal-style
claims from exact chunk text spans, links entities and authorities, validates offsets and retrieval
bindings, and writes claim graph artifacts under
`source_library/derived/<source_set_id>/claims/`.

EA Package Review V0 is implemented through `ea-review`. It extracts a local EA package, runs the
seed checklist, retrieves source-library evidence for each item, and writes package evidence,
source-library evidence, finding status, limitations, and validation artifacts.

Custer Gallatin Forest Plan Resolver V0 is implemented through `forest-plan-resolve` as the first
configured forest-plan profile. It extracts or reuses a local EA package, resolves whether the
package matches the selected profile, extracts ranger-district and project-location signals,
extracts geographic areas, management areas, and overlays from profile data, and binds resolved plan
context to profile-declared source-library records. The default Custer Gallatin profile requires the
complete plan-review bundle in the retrieval index: planning page, Land Management Plan, Record of
Decision, FEIS Volume 1, FEIS Volume 2, Biological Assessment, and Biological Opinion. Triggered
ROD, FEIS, designated-area/allocation, and ESA cues are routed to profile-declared supporting
records in addition to the primary LMP area/component evidence. Supporting routes are trigger-gated
and emit `trigger_evidence`, so broad EA section labels do not silently activate FEIS records and
uppercase acronym triggers do not match ordinary lowercase words. Generic project decision labels
such as `selected alternative`, `decision basis`, or `plan approval` do not activate the Custer
Gallatin ROD route unless the package explicitly references `Record of Decision` or `ROD`; generic
`plan consistency` labels do not activate FEIS routing unless an explicit FEIS, tiering, or
incorporation cue is present.

Forest Plan Component Evaluation V0 is implemented as a default `forest-plan-resolve` stage for
packages resolved to the selected forest-plan profile. It reads a source-set component inventory when
present, falls back to the seed inventory, validates component provenance and source-set alignment,
retrieves current plan evidence from the local retrieval index, searches package chunks for component
evidence terms, and writes
`forest_plan_component_findings.json`, `forest_plan_component_findings.md`, and
`forest_plan_reviewer_resolution_queue.json`. NFMA standard coverage V0 also writes
`forest_plan_component_inventory_coverage.json` and
`forest_plan_applicable_standard_coverage.json`; applicable standards must have plan-source evidence,
EA package evidence, and a resolved compliance status before component validation can pass. The seed
inventory
`config/forest_plan_component_inventory_seed.json` covers the first East Crazies-relevant Custer
Gallatin Crazy Mountains Backcountry Area components. Supported and partial findings require both
plan-source evidence and package evidence; gaps and stale source-set IDs become reviewer-resolution
items instead of legal conclusions.

Compliance Rule Pack + Matrix + Finding Graph V0.4 is implemented through `compliance-review`. It
identifies applicable statutory, regulatory, policy, state, executive-order, and forest-plan
authorities from `config/compliance_rule_pack_nepa_ea_v0.json`, evaluates the EA against each
applicable authority, reuses the `ea-review` package/retrieval gates, requires validated
rule-to-source-claim bindings, and writes compliance validation, a compliance review report, a
reviewer-facing compliance matrix, and a finding graph for rules, findings, source claims, source
evidence, package evidence, and package gaps.

Rule-pack `0.4.0` contains `48` rules. It declares `baseline_source_record_ids` for the 26
workbook rows where `Scope=Baseline`, and rule-pack validation enforces that each declared baseline
source record has a corresponding `applicability_mode=baseline` rule.

Applicability-First Review has a post-V1 schema contract and implemented slices for authority
universe snapshotting, package fact graph/context building, retrieval/graph tracing, deterministic
decisions, validation, and adjudication replay. `applicability-authority-universe` reads the current
catalog, base rule pack, default authority-family template config, forest-plan profiles, component
inventory, source-claim artifacts, and rule-claim links, then writes
`source_library/reviews/<review_id>/applicability/authority_universe_snapshot.json` with all
base rule-template candidates, authority-family rule-template candidates when configured, and
Forest Plan component candidates. Each candidate carries required package fact types, positive and
negative trigger groups, required source evidence, source-role filters, package-section filters,
retrieval contracts, graph-expansion contracts,
dependency/exception/supersession fields, and search coverage requirements for later
non-applicability proof. `applicability-context-build` reads the existing EA package cache and
writes `package_fact_graph.json`, `package_applicability_context.json`, and
`package_fact_graph_validation.json` with typed, span-bound package facts for project/action,
agency, NEPA level, authority signals, geography, Forest Plan areas/overlays, resource topics,
consultations, permits, public involvement, alternatives, and decision/finding signals.
Land-exchange authority signals are extracted at intake as `authority` facts before applicability
or compliance decisions are attempted: FLPMA Section 206
(`authority:flpma_section_206_land_exchange`, `R1EA-146`), land-exchange statutory authorities
(`R1EA-137`), 36 CFR part 254 regulations (`R1EA-124`), and Forest Service land-exchange
policy/project references (`R1EA-150`). It
records negative or out-of-scope location statements as negative-context facts instead of positive
geography facts, and
records weakly worded or missing common fact types as graph uncertainty rather than resolving them
as package applicability decisions. `applicability-retrieve` reads the authority universe, package
fact graph, local retrieval index, and available graph/link artifacts, then writes
`applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`, and
`applicability_retrieval_graph_diagnostics.json` with replayable per-candidate query rows, fused RRF
result rows, bounded graph paths, and retrieval/graph diagnostics. Graph trace rows now explicitly
preserve authority-category hierarchy, source-claim/rule-claim-link bindings, supporting source
records, package facts, and Forest Plan component provenance when those artifacts are available.
`applicability-determine` reads those artifacts and writes `applicability_decisions.jsonl`,
`applicable_authorities.json`, `non_applicable_authorities.json`,
`search_coverage_certificates.json`, `applicability_provenance.json`, and
`applicability_report.md` with one deterministic decision row per authority candidate. Weak or
auxiliary trigger evidence no longer blocks a decision when rule-contract-sufficient strong
positive trigger evidence is independently present; all-weak positive evidence and unresolved
positive/negative conflicts still become `needs_adjudication`. Not-applicable decisions cite search
coverage certificates with required source-index hashes. Decision rows retain inspected
source-library evidence spans or declared authority-universe source evidence when source retrieval
records coverage without selecting a source chunk. Explicit negative Forest Plan scope evidence,
such as package statements that a component area is not part of the project area, overrides broad
component-text positives instead of producing contradictory ready decisions. Provenance includes
package manifest/chunk entities.
`applicability-validate` now writes `applicability_validation.json` and fails closed on missing or
duplicated candidate decisions, unresolved or `needs_adjudication` decisions, stale artifacts,
missing retrieval/graph traceability, non-applicable decisions without coverage/adjudication, and
provenance gaps. `applicability-adjudication-template`, `applicability-adjudication-eval`, and
`applicability-adjudication-apply` provide a machine-readable replay path for resolving open
decisions into `human_adjudication` bases before validation can pass.
`applicability-generate-rule-pack` now writes and validates generated compliance rule packs from the
validated applicable-authority partition only, and reviewer-ready `compliance-review` is gated on
that generated pack plus current applicability validation, generated-pack validation,
non-applicable-authority, search-coverage, package, source-set, and provenance artifacts. The base
rule pack remains available only through an explicit non-reviewer-ready diagnostic path.
`applicability-eval` and `applicability-gold-eval` now score applicability decision quality before
compliance quality is promoted. Milestone 4 expands those evals across the `19` authority-family
templates added in Milestone 3. The seed eval now includes positive and negative cases for every
high-priority authority family, an unresolved weak-signal case, and the
`config/fixtures/applicability/region1-land-exchange-expanded-authority.txt` package fixture
covering land exchange, water/wetlands, cultural/tribal, wildlife/species, designated-area, and
forest-plan consistency triggers. The gold eval now requires positive, mixed, negative,
unresolved, and replay-adjudicated profiles, including a human-adjudication replay for a weak Clean
Water Act authority-family decision.

Compliance Review Eval V0 is implemented through `compliance-review-eval`. The current seed fixtures
target rule pack `0.4.0` and run deterministic package fixtures through the real compliance-review
path. The gate scores expected rule statuses, claim types, evidence presence, source-claim links,
expected source record IDs, expected source document roles, citation coverage, unsupported finding
IDs, failure taxonomy, compact reproduction paths, and finding-graph coverage.

Compliance Gold Eval V0.4 is implemented through `compliance-gold-eval`. It validates a structured
adjudication file, requires positive, mixed, and negative package profiles, runs ten adjudicated
package fixtures through the real compliance-review eval path, and emits `promotion_ready` only
when the rule pack is a reviewer-ready generated applicability rule pack and both adjudication
checks and generated findings pass.

Compliance Coverage V0 is implemented through `compliance-coverage`. It validates the coverage
matrix, rule-pack identity, eval-case coverage, current source-claim links, source-claim terms, and
source-record alignment for each compliance rule.

Current state:

- Raw source documents are captured and cataloged for the 190-row workbook contract, except the
  intentionally scope-excluded `R1EA-160` project page.
- Source metadata is normalized into JSONL and SQLite.
- Derived extraction builds text and chunks from the catalog. The newest source set now has a
  full-source-set extraction layer, reviewer-ready retrieval index, evidence graph, source-claim
  graph, rule-claim bindings, compliance coverage, compliance-review eval, compliance-gold eval, and
  phase-eval promotion evidence for `source-set-ba8d0feae79501b8`.
- The extraction accuracy audit verifies text hashes, raw artifact hashes, chunk offset fidelity,
  gap-free chunk coverage, eCFR section/subpart scoping, markup cleanup, and PDF token coverage.
- Retrieval builds and queries a provenance-bearing local evidence index.
- The document evidence graph builds source, artifact, extracted-text, section, chunk, evidence-span,
  parser, and review-topic nodes with health metrics.
- The source claim graph builds claim, entity, authority, and claim-evidence-span nodes with exact
  chunk and source-text offsets.
- The rule-claim binding layer links compliance rules to validated source claims and records explicit
  no-claim gaps when no validated source claim matches a rule.
- Phase eval reports catalog, extraction, retrieval, evidence-graph, claim-extraction,
  rule-claim-binding, optional compliance-coverage, optional compliance-gold-eval, and review-bound
  applicability plus compliance-review readiness separately when those artifacts exist or are
  requested.
- EA review runs deterministic checklist execution against a local package and emits JSON/Markdown
  reports plus `review_validation.json`.
- Custer Gallatin forest-plan context resolution runs against a local EA package and emits
  `forest_plan_context.json`, `forest_plan_context_validation.json`, and
  `forest_plan_context_summary.json`. The current Custer Gallatin path requires all seven
  Custer Gallatin plan/supporting records in retrieval, resolves management areas from the EA
  package, and adds `supporting_plan_evidence` routes for ROD, FEIS Volumes 1 and 2, Biological
  Assessment, and Biological Opinion triggers.
- Forest-plan component evaluation writes component findings, selected-inventory coverage,
  applicable-standard coverage, and a reviewer-resolution queue from a versioned inventory for
  packages resolved to the selected forest-plan profile. The current source-set inventory for the
  2022 Custer Gallatin Land Management Plan is generated from extracted chunks and has passing build
  coverage; the seed inventory remains only a fallback/test fixture.
- Compliance review runs a versioned rule pack and emits `compliance_validation.json`,
  `compliance_review.json`, `compliance_matrix.json`, `compliance_matrix.md`,
  `compliance_matrix.pdf`,
  `finding_graph_nodes.jsonl`, and `finding_graph_edges.jsonl`.
- Compliance review now invokes the forest-plan resolver against the same package cache. For Custer
  Gallatin packages, `forest_plan_component_gate_reviewer_ready` must pass, the matrix summary links
  to `forest_plan_review`, `compliance_matrix.json/md/pdf` render Forest Plan Compliance as a
  separate table from NEPA/generated-rule compliance, and the finding graph includes forest-plan
  review/component-evaluation nodes.
- EA review and compliance review can rerun checklist/rule evaluation against existing
  `package_manifest.jsonl` and `package_chunks.jsonl` with `--reuse-package-cache`; use this for
  rule-pack refreshes when the EA package was already extracted.
- Compliance review eval runs deterministic package fixtures and emits
  `compliance_review_eval_results.json` with failure taxonomy and reproduction paths.
- Compliance gold eval runs adjudicated positive/mixed/negative package fixtures and emits
  `compliance_gold_eval_results.json`; the current gate has ten adjudicated cases.
- Compliance coverage runs the coverage matrix against the current rule pack, rule-claim links,
  source-claim terms, and compliance review eval cases.
- V1 real-EA review eval is implemented through `v1-ea-eval`. It reads an existing East Crazy
  Inspiration Divide compliance review directory and scores required EA section detection,
  rule-to-section matches, source-record/document-role correctness, all 26 baseline source records,
  conditional applicability, applicable conditional source/section alignment, missing conditional
  expectations, Custer Gallatin forest-plan source/component/standard expectations, citation
  requirements, and reviewer-resolution queue size against `config/v1_ecid_real_ea_eval.json`.
- The first real East Crazy Inspiration Divide V1 compliance review run exists locally at
  `source_library/reviews/v1-cg-ecid-compliance-review/`. It extracted `43` package files into
  `1,265` chunks, produced compliance review/matrix/PDF/graph artifacts, and passed
  the upstream source-set phases. After the section-aware forest-plan retrieval pass, the package
  resolves to `scope_status: custer_gallatin`; forest-plan context validation passes with
  `2` geographic areas, `1` management area, `2` overlays, and `5` supporting plan evidence
  records. The retained context is Bridger/Bangtail/Crazy, Madison/Henrys Lake/Gallatin, Crazy
  Mountains BCA, Inventoried Roadless Area, and Recommended Wilderness Area. Forest-plan component
  artifacts are produced from the generated source-set inventory with `329` component findings,
  `58` standards, `12` applicable standards, and `12` applied standards. The stricter
  applicable-standard coverage gate now passes with `all_applicable_standards_applied=true`; the
  prior `AB-STD-RCREA-01` gap is supported by recreation/access package evidence for the proposed
  nonmotorized Sweet Trunk Trail. The non-standard reviewer-resolution queue is now closed:
  `forest_plan_component_findings.json` reports `79` supported findings, `250` not applicable
  findings, `0` gaps, and `0` reviewer-resolution items. The resolver now reads split Plan
  Consistency Table rows across adjacent package chunks, handles duplicated/split component-key
  cells and plain-text rows, and suppresses cross-reference pseudo-components that do not have a
  numeric component number.
  Component-level forest-plan eval runs against `config/forest_plan_component_eval_seed.json` and
  passes all `35` adjudicated cases. The eval now covers every one of the `12` applicable standards,
  `11` representative non-standard applicable components across desired conditions, goals,
  guidelines, objectives, and suitability, and `12` hard-negative not-applicable cases. Case coverage
  requirements pass, and component applicability precision/recall, applicable-standard recall,
  package-section match rate, plan-source citation correctness, package-evidence citation
  correctness, resolved compliance-status rate, compliance-status match rate, reviewer-resolution
  state match rate, false-applicable component rate, and reviewer-resolution closure rate all meet
  their strict thresholds. Non-standard component package evidence now uses strict section-family
  binding: outside explicit Plan Consistency Table determinations, desired conditions, goals,
  guidelines, objectives, and suitability components require a matching EA package section family
  plus substantive component terms. The component validation gate now fails supported package
  evidence with missing or mismatched section bindings unless the evidence is an explicit Plan
  Consistency Table determination. Current regenerated findings have `79` supported components,
  `0` gaps, zero supported package evidence entries with mismatched section binding, and `51`
  affirmative Plan Consistency Table component-row bindings marked explicitly. The prior completed
  non-standard component
  adjudication artifact classified the old `21` items as system misses; those adjudications are
  superseded by evidence-backed resolver fixes, and phase eval now rejects stale component
  adjudication evals whose queue count differs from the current queue. `phase-eval --review-id
  v1-cg-ecid-compliance-review` now reports `10/10` passing phases and `reviewer_ready=true`.
  The stricter V1 eval now passes all forest-plan expectations, including zero open standard
  reviewer-resolution items and a capped `0` total forest-plan reviewer-resolution items. It also
  passes the broader EA source/section gate after CE/FANEC conditional-applicability, baseline
  section-attribution, and programmatic-tiering section-routing repairs. `v1-ea-eval` now reports
  `passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`, empty failure-category
  counts, `failed_rule_ids=[]`, `conditional_false_positive=0`, `conditional_false_negative=0`,
  and `rule_section_match_rate=1.0`. The V1 eval contract now carries explicit policy coverage for
  `14` adjudication-pending conditional rules, so those rows are visible accepted V1 risk rather
  than a hidden pass condition.
- Forest-plan component adjudication tooling is implemented through
  `forest-plan-component-adjudication-template` and `forest-plan-component-adjudication-eval`. The
  template command exports one adjudication item for each open component reviewer-resolution queue
  item, with current status expectations, compact component/source trace refs, and
  reviewer-fillable dispositions, and writes a companion Markdown worklist for human triage. The
  eval command fails closed until every current queue item has explicit adjudication metadata,
  required trace refs, and a resolved disposition such as `true_ea_omission`, `retrieval_miss`,
  `package_section_chunking_miss`, `component_inventory_overreach`, `applicability_false_positive`,
  or `evidence_linking_miss`.
  Earlier runs against `v1-cg-ecid-compliance-review` produced `21` pending non-standard items:
  `8` desired conditions, `2` goals, `7` guidelines, `3` objectives, and `1` suitability
  component. Those items were adjudicated as system misses, then closed by the resolver and
  component-inventory fixes described above. The current generated queue has `0` items, so no
  component adjudication phase is required for the latest review artifacts. When an adjudication
  eval artifact is present in a review directory, `phase-eval --review-id` includes it as a
  `forest_plan_component_adjudication` phase and now checks it against the current queue count so
  pending, stale, or mismatched adjudication work blocks reviewer readiness at the phase gate.
- The V1 real-EA eval now records explicit diagnostic lanes in `v1_ea_eval_results.json`. The
  current East Crazies package passes the lane split with `broader_ea_passed=true`,
  `forest_plan_passed=true`, `forest_plan_component_adjudication_required=false`, and no broader-EA
  or forest-plan failure categories. `nepa_4336b_programmatic_tiering` remains visible as an
  adjudication-pending conditional rule, but its actual package sections are `alternatives` and
  `environmental_consequences`, its actual source record is `R1EA-005`, and its actual source
  document role is `law`.
- A seed retrieval eval file exists at `config/retrieval_eval_seed.json`.
- A seed claim extraction eval file exists at `config/claim_eval_seed.json`.
- A seed rule-claim binding eval file exists at `config/rule_claim_link_eval_seed.json`.
- A seed compliance review eval file exists at `config/compliance_review_eval_seed.json`.
- A seed compliance gold eval file exists at `config/compliance_gold_eval_v0.json`.
- A seed compliance coverage matrix exists at
  `config/compliance_rule_pack_coverage_nepa_ea_v0.json`.
- A seed forest-plan component eval file exists at
  `config/forest_plan_component_eval_seed.json`.
- A V1 real-EA review eval contract exists at `config/v1_ecid_real_ea_eval.json`.
- A post-V1 promotion-suite manifest exists at `config/promotion_suite_v1.json`.
- A seed EA review checklist exists at `config/ea_review_checklist_seed.json`.
- A seed NEPA EA compliance rule pack exists at `config/compliance_rule_pack_nepa_ea_v0.json`.
- Catalog graph seed files exist for source-level relationships.
- No embeddings exist yet.
- No model-generated compliance narrative is trusted without deterministic package and source
  evidence.
- Page/section offsets are available only where the selected parser can infer them; all chunks carry
  extracted-text character offsets.

The catalog graph seed is a source metadata graph. It includes relationships such as:

- source to artifact
- source to authority
- source to review topic
- source to applicability

The document evidence graph is the implemented content graph. It includes document sections, chunks,
evidence spans, parser provenance, and review-topic edges. It does not include table structure
recovery, embeddings, or vector chunks.

The source claim graph is the implemented claim/entity graph. It includes extracted source-text
claims, entities, authority nodes, claim evidence spans, and edges back to chunk/source provenance.
It is deterministic pattern extraction with strict validation, not a model-generated interpretation
of compliance meaning.

The rule-claim binding layer is the implemented bridge from compliance rules to source claims. It
uses rule-pack queries and source filters to rank validated source claims, writes exact provenance
for each link, and treats missing rule support as explicit no-claim gaps rather than silent evidence.

The finding graph is the implemented compliance-review graph. It includes rule packs, compliance
rules, findings, source-claim references, evidence-span references, and package-gap nodes. It does
not replace human reviewer adjudication.

## Accuracy Guarantees

The current downloader and catalog guarantee capture integrity, not legal interpretation.

Validated downloader/catalog guarantees for the current 190-row corpus:

- Every generated-corpus source row has one final captured status.
- The combined batch ledger covers all `190` generated-corpus workbook rows.
- The repair queue is empty after URL repairs.
- Every artifact-bearing successful row links to an artifact.
- The one scope-excluded row, `R1EA-160`, has no artifact or fetch evidence.
- Every artifact path exists.
- Artifact byte sizes match manifest metadata.
- Artifact SHA256 values recompute from saved bytes.
- Duplicate-content rows link to canonical artifacts.
- URL overrides preserve the workbook `original_url` and record the `effective_url`.
- Override metadata includes `override_url` and `override_reason`.
- The reviewer catalog matches batch manifests.
- SQLite source-artifact links match the JSONL catalog.
- The prior 38-source land-exchange delta extraction for `source-set-572d6384a59a7b2a` matched raw
  artifact hashes and manifest text hashes, but it is superseded by the current reuse-first
  extraction assembly for `source-set-ba8d0feae79501b8`.
- Chunk text matches extracted-text offset slices.
- Retrieval chunks validate against source-set IDs, content hashes, offsets, required provenance, and
  catalog linkage.
- Evidence graph chunks validate against the retrieval index before graph artifacts are marked
  reviewer-ready.
- EA review `pass` findings require both package evidence and source-library evidence.
- EA review `gap` findings require source-library evidence and explicitly mean package evidence was
  not found.
- Package evidence search requires configured package-term hits; single-word terms match whole
  tokens and phrase terms match contiguous text.
- EA review validation rejects unsupported compliance claims.
- Compliance review validates the rule pack, requires every authority rule to carry authority and
  applicability metadata, requires all declared baseline source records to be covered, requires
  every rule to be evaluated, requires all declared baseline source records to appear in findings,
  requires source citations for claim-bearing findings, and validates finding graph node/edge
  integrity.
- Rule-pack validation rejects unsafe rule-pack or rule IDs, unsupported source-filter keys, and
  empty source-filter values.
- Compliance review eval rejects unsafe case IDs, ambiguous package fixtures, unsupported filters,
  unsupported expected statuses, unsupported expected claim types, non-boolean evidence
  expectations, partial rule-pack coverage, unknown rule IDs, and status counts that do not match
  per-rule expectations.
- Compliance coverage rejects malformed matrix rows, missing matrix/eval/link coverage, and
  source-record or source-claim-term mismatches against current rule-claim links.
- Compliance gold eval rejects missing adjudication metadata, missing required profiles, duplicate
  case IDs, unsafe or escaping package fixture paths, partial rule-pack expectations, status count
  mismatches, and generated finding mismatches. Missing package fixture files are recorded as failed
  gold eval results instead of escaping without a machine-readable artifact.
- Phase eval rejects stale compliance coverage artifacts when the coverage source set or rule pack
  does not match the evaluated source set and rule-claim binding.
- Phase eval rejects stale compliance review artifacts when the review source set does not match the
  evaluated source set.

Full extraction, retrieval, evidence-graph, source-claim, rule-claim, coverage, compliance-review
eval, compliance-gold eval, and phase-eval guarantees now exist for the current 190-row source set
`source-set-ba8d0feae79501b8`.

Boundaries:

- A successful download means the source bytes were captured and validated.
- It does not prove that the source is legally current beyond the workbook metadata and retrieval evidence.
- It proves the current generated extraction artifacts pass deterministic extraction validation and
  extraction accuracy audit checks for text hashes, raw artifact hashes, chunk offsets, chunk
  coverage, scoped XML, markup cleanup, and sampled PDF token coverage.
- It proves the current retrieval, evidence graph, source-claim graph, rule-claim binding,
  compliance coverage, compliance review eval, compliance gold eval, and phase eval artifacts passed
  deterministic provenance, coverage, freshness, and binding gates.
- It proves the current EA review V0 cannot mark a finding as `pass` without both package and
  source-library evidence.
- It proves the current compliance review V0 cannot produce claim-bearing findings without
  source-library citations.
- It proves a Custer Gallatin-scoped compliance review cannot be reviewer-ready when forest-plan
  component evaluation is absent, stale, or not reviewer-ready.
- It proves component-level forest-plan accuracy can be scored against adjudicated cases for
  applicability, standard recall, package-section binding, plan-source citations, package-evidence
  citations, resolved compliance status, and reviewer-resolution closure before running additional
  real EA packages. The component eval checks review/source-set identity across every consumed
  review artifact, enforces all-applicable-standard and minimum representative-case coverage, and
  treats extra citations as citation mismatches, not harmless surplus evidence.
- It proves the profile-driven forest-plan resolver can resolve the real East Crazy Inspiration
  Divide package to Custer Gallatin scope without treating incidental references to other forests as
  ambiguity, while still failing closed when component coverage is not reviewer-ready.
- It proves forest-plan component reviewer-resolution items can be exported into a stable
  adjudication contract and evaluated for queue coverage, completion, disposition counts, and status
  expectation drift before those reviewer decisions are used as improvement data.
- It proves the current final compliance-review eval seed passes deterministic all-pass, mixed
  pass/gap, and all-gap package fixtures.
- It proves the current seed compliance-gold-eval promotion gate passes one positive, one mixed, and
  one negative adjudicated fixture profile.
- It defines a V1 real-EA eval contract for the East Crazy Inspiration Divide run, but that contract
  does not prove real-world EA review quality until `v1-ea-eval` passes against the actual review
  artifacts and the remaining component/conditional/section failures are adjudicated.
- It does not prove semantic legal interpretation of the extracted text.
- It does not prove that future web versions will remain unchanged.

## Reviewer Engine Read Path

The EA review engine should not scan `artifacts/raw/` directly as its source of truth. It should
read through the catalog, extraction outputs, and retrieval index in order.

Recommended read path:

1. Read `source_library/catalog/source_set_manifest.json`.
2. Confirm the intended `source_set_id`, `download_batch_run_id`, source counts, artifact counts, and validation status.
3. Query `source_library/catalog/review_sources.sqlite` or read `source_library/catalog/source_catalog.jsonl`.
4. Select source rows by `document_role`, `authority_level`, `review_topics`, `applies_to`, `host`, or `expected_parser`.
5. For each source row, open `artifact_path`.
6. Recompute SHA256 and byte size before parsing.
7. Parse by `expected_parser` and `content_type`.
8. Emit downstream chunks with immutable provenance fields.
9. Build `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`.
10. Retrieve evidence spans through `retrieval-query` or the retrieval module before generating any
    compliance answer.
11. For package review, run `ea-review` so each checklist item records both package evidence and
    source-library evidence, or marks the item as a gap/uncertain without unsupported claims.

Every downstream text chunk should carry:

- `source_set_id`
- `source_record_id`
- `artifact_sha256`
- `artifact_path`
- `citation_label`
- `original_url`
- `effective_url`
- `final_url`
- parser name and parser version
- extraction timestamp
- page, section, heading, byte, or character offsets when available

The review engine should cite `citation_label` and offset metadata, not raw filenames.

## EA Package Review V0

The current package-review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/review_report.json` and
`review_report.md`, `review_validation.json`, plus package extraction artifacts under
`source_library/reviews/<review_id>/package/`.
Findings use the statuses `pass`, `gap`, `uncertain`, and `not_applicable`.

A `gap` means the source library returned supporting review authority but matching package evidence
was not found. An `uncertain` finding does not make a compliance claim.
The command fails fast if the source-library retrieval index is not reviewer-ready, and rerunning a
fixed review ID replaces prior package artifacts before writing the new report.
When a package was already extracted for the same review ID, pass `--reuse-package-cache` to preserve
and reuse `package/package_manifest.jsonl` and `package/package_chunks.jsonl` instead of
re-extracting package PDFs.

`review_validation.json` is the gate-facing artifact. It checks source retrieval readiness, package
extraction, package chunk creation, valid finding statuses, dual evidence for `pass` findings, source
evidence for `gap` findings, and absence of unsupported compliance claims.

## Custer Gallatin Forest Plan Resolver V0

The first forest-plan-specific review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/forest_plan_context.json`,
`forest_plan_context_validation.json`, and `forest_plan_context_summary.json`, plus package
extraction artifacts under `source_library/reviews/<review_id>/package/`.

The default resolver profile is Custer Gallatin and preserves the V0 output contract. It returns
`scope_status=custer_gallatin`, `not_custer_gallatin`, or `ambiguous`; ambiguous `Gallatin`-only
packages are not guessed. The command now accepts `--forest-unit-id` and
`--forest-plan-profiles-path` so profile data, not Python constants, defines forest names, required
source records, area terms, overlays, and supporting evidence routes. Other configured forest
profiles are still blocking evidence when mentioned as operative project scope, but incidental
background, reference, bibliography, or coordination mentions do not force an otherwise
Custer-Gallatin package to `ambiguous`. Location evidence now carries `evidence_role` metadata and
the context includes `background_location_mentions` so reviewers can see which references were
excluded from project-location resolution. Negative package-location text such as `not part of the
project area` is also filtered before area resolution. For Custer Gallatin packages it extracts:

- forest unit and ranger district signals
- project location snippets
- Custer Gallatin geographic areas
- Custer Gallatin management areas
- overlays such as inventoried roadless areas
- package evidence and source-library LMP evidence
- triggered supporting plan evidence from the Custer Gallatin ROD, FEIS Volumes 1 and 2,
  Biological Assessment, and Biological Opinion
- trigger evidence showing why each supporting plan record was applied
- required source-record readiness for all Custer Gallatin profile-required plan/supporting records
- unresolved mentions that need human reviewer resolution

The East Crazies profile-driven fixture proves the minimum V1 forest-plan support slice: Custer
Gallatin scope, Bridger/Bangtail/Crazy Mountains Geographic Area, Crazy Mountains Backcountry Area,
all seven required Custer Gallatin source records, FEIS/BA/BO supporting routes from explicit
package evidence, and no Custer Gallatin ROD routing from generic project decision labels.

Custer Gallatin packages are reviewer-ready only when validation passes and at least one geographic
area, management area, or overlay is resolved. They also require every Custer Gallatin
profile-required plan/supporting record to be indexed. Packages that appear Custer Gallatin scoped
but lack a resolved plan area, or trigger a supporting record without source evidence, set
`needs_reviewer_resolution` instead of silently passing.

Forest-plan improvement work uses sequence discipline: each implemented sequence updates repo docs,
passes focused verification, and is committed before the next sequence starts.

## Compliance Rule Pack And Finding Graph V0

The rule-pack milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

For rule-pack-only refreshes against an existing package extraction, keep the same review ID and add
`--reuse-package-cache`.

The command writes these artifacts beside the base EA review artifacts:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/compliance_matrix.json`
- `source_library/reviews/<review_id>/compliance_matrix.md`
- `source_library/reviews/<review_id>/compliance_matrix.pdf`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

The post-V1 applicability-first artifact contract reserves
`source_library/reviews/<review_id>/applicability/` for:

- `authority_universe_snapshot.json`
- `package_fact_graph.json`
- `package_applicability_context.json`
- `package_fact_graph_validation.json`
- `applicability_retrieval_trace.jsonl`
- `applicability_graph_trace.jsonl`
- `applicability_retrieval_graph_diagnostics.json`
- `applicability_decisions.jsonl`
- `applicable_authorities.json`
- `non_applicable_authorities.json`
- `search_coverage_certificates.json`
- `applicability_validation.json`
- `applicability_provenance.json`
- `applicability_report.md`
- `generated_rule_pack.json`
- `generated_rule_pack_validation.json`

Those artifacts are the target source of truth for applicability and non-applicability. The
non-applicable authority list must not be buried only as compliance matrix rows. A not-applicable
decision must carry negative evidence, trigger-miss rationale, search coverage, or adjudication, and
a reviewer-ready compliance review consumes a generated rule pack tied to a passing applicability
validation hash plus the package fact graph, retrieval trace, graph trace, search coverage, and
provenance hashes.

The rule pack is data, not hidden code. Each rule includes identity, title, question, requirement,
severity, authority category, authority source record, applicability mode, package query and terms,
optional conditional applicability terms, optional grouped conditional applicability terms, source
query, source filters, and an evidence expectation.
The authority document role is derived from explicit rule metadata when present, otherwise from
`source_filters.document_role`.
Rule-pack `0.4.0` also declares `baseline_source_record_ids`; these are the 26
`Ingest_Checklist` rows where `Scope=Baseline`.

The finding graph contains:

- `ComplianceRulePack`
- `ComplianceReview`
- `ComplianceRule`
- `ComplianceFinding`
- `SourceLibraryEvidence`
- `PackageEvidence`
- `PackageEvidenceGap`

The compliance matrix is the first reviewer-facing matrix artifact. Its `NEPA / Authority
Compliance` table records one NEPA/generated-rule compliance row per finding: authority,
applicability mode and status, rule status, requirement, applicability basis, package evidence
citation, source evidence citation, source-claim IDs, applied source record IDs, applied source
document roles, citation-gate status, limitations, and failure category when an applicable finding is
not a supported pass. For Custer Gallatin Forest Plan reviews, the matrix also includes a separate
`Forest Plan Compliance` table from component findings and applicable-standard coverage. The
Markdown/PDF rendering now opens with a Responsible Official Readout and Accuracy Audit in plain
decision language so the signing review can distinguish pass/fail authority rows, inapplicable
authority traceability, applicable Forest Plan standards, and non-standard plan-consistency support.

`compliance_validation.json` checks rule-pack validity, base EA review validation, all-rules
coverage, valid finding statuses, dual evidence for `pass`, source evidence for `gap`, source
citations for claim-bearing findings, unsupported-claim absence, finding graph evidence-edge
coverage, and finding graph integrity.

Rule-pack IDs, rule IDs, and fixed review IDs are constrained to letters, numbers, dots,
underscores, and hyphens so review outputs cannot escape the intended review directory. Rule
`source_filters` must use supported retrieval filter keys; typoed keys fail validation instead of
silently widening retrieval.

## Derived Extraction Layer

The extraction layer builds a derived text/chunk index without modifying raw artifacts.
PDF extraction uses Docling first; born-digital PDFs that exceed the Docling timeout can fall back
to `pypdf_text_fallback`, with parser name/version preserved in manifests and chunks and fallback
metadata preserved in the extraction manifest.

Derived layout:

```text
source_library/
  derived/
    <source_set_id>/
      extracted_text/
      docling_json/
      chunks/
        chunks.jsonl
      diagnostics/
        extraction_manifest.jsonl
        extraction_validation.json
        extraction_accuracy_audit.json
        summary.json
```

Derived outputs:

- extracted text per artifact
- Docling JSON when Docling is used by the parser
- HTML/XML section extraction
- chunk JSONL with stable chunk IDs
- chunk-level SHA256 or content hash
- parser diagnostics
- extraction validation report
- chunk-to-source and chunk-to-artifact links

Derived data should always be rebuildable from raw artifacts and the reviewer catalog.

## Evidence Retrieval Layer

Retrieval layout:

```text
source_library/
  derived/
    <source_set_id>/
      retrieval/
        evidence_index.sqlite
        retrieval_manifest.json
        retrieval_validation.json
        summary.json
        retrieval_eval_results.json
```

The retrieval layer is intentionally lexical and auditable for v1. It stores the source chunk text
and the provenance required for a reviewer to verify the citation back to raw artifacts and extracted
text offsets.

Retrieval validation checks:

- extraction validation passed unless explicitly overridden
- extraction scope is complete unless `--allow-partial-extraction` is passed for diagnostics
- chunks JSONL exists and contains chunks
- catalog SQLite exists
- chunk source-set IDs match the target source set
- chunk IDs are unique
- indexed source IDs match extracted source IDs in `extraction_manifest.jsonl`
- chunk hashes match the stored text
- chunk offsets are valid
- linked artifact and extracted-text paths still exist
- required citation, artifact, URL, parser, and offset fields are present

`retrieval-build` records `reviewer_ready`. This is true only when the index validates and the
extraction summary shows complete catalog coverage for all required non-excluded sources.
Scope-excluded rows count toward selected catalog coverage but do not require chunks. A filtered
one-document slice can still be indexed with `--allow-partial-extraction`, but it remains a
diagnostic index, not a reviewer-ready corpus.

## Document Evidence Graph Layer

Evidence graph layout:

```text
source_library/
  derived/
    <source_set_id>/
      evidence_graph/
        document_graph_nodes.jsonl
        document_graph_edges.jsonl
        evidence_graph.sqlite
        evidence_graph_validation.json
        summary.json
        phase_eval_results.json
```

The evidence graph contains these node types:

- `SourceSet`
- `SourceDocument`
- `RawArtifact`
- `ExtractedText`
- `DocumentSection`
- `DocumentChunk`
- `EvidenceSpan`
- `Parser`
- `ReviewTopic`

Every `EvidenceSpan` traces to a chunk, source document, raw artifact, parser version, content
hash, citation label, URL provenance, and extracted-text offsets. The graph build also reopens the
retrieval SQLite index and requires chunk IDs, source-set IDs, provenance fields, offsets, content
hashes, text, and review topics to match before graph artifacts are persisted. The graph records
health metrics: connected components, isolated nodes, dangling edges, evidence coverage, topic
coverage, source-artifact coverage, retrieval binding mismatches, and chunk hash mismatches.

`phase-eval` keeps readiness checks phase-aligned:

- catalog capture
- extraction
- retrieval
- evidence graph
- claim extraction
- rule-claim binding
- authority universe when `--review-id` or `--review-dir` is supplied
- package fact graph when `--review-id` or `--review-dir` is supplied
- applicability retrieval trace when `--review-id` or `--review-dir` is supplied
- applicability graph trace when `--review-id` or `--review-dir` is supplied
- applicability determination when `--review-id` or `--review-dir` is supplied
- applicability validation when `--review-id` or `--review-dir` is supplied
- generated rule pack when `--review-id` or `--review-dir` is supplied
- optional compliance coverage when `compliance_coverage_results.json` exists beside the
  rule-claim outputs
- optional compliance gold eval when `compliance_gold_eval_results.json` exists under
  `source_library/reviews/compliance_gold_eval/`
- optional compliance review when `--review-id` or `--review-dir` is passed
- optional forest-plan component eval when the review directory contains
  `forest_plan_component_eval_results.json`
- optional forest-plan component adjudication when the review directory contains
  `forest_plan_component_adjudication_eval.json` or a completed
  `forest_plan_component_adjudication.json`

When a compliance coverage phase is included, `phase-eval` requires the matrix gate to pass, the
rule pack to match, and the coverage source set to match the evaluated source set. When a gold eval
phase is included, `phase-eval` requires the gold eval to pass, the rule pack to match, and the
gold eval source set to match the evaluated source set; stale or failed gold artifacts report
specific failed checks such as source-set or rule-pack mismatch. For review-bound generated rule
packs, a passing base-pack gold eval can satisfy the phase when the generated pack declares the same
base identity; the phase records this as `rule_pack_match_mode=generated_base`. When review-bound applicability
phases are included, `phase-eval` requires a current authority universe, package fact graph and
validation, retrieval and graph trace diagnostics, complete candidate decisions, complete
applicable/non-applicable partitions, search coverage certificates for non-applicable authorities,
a passing `applicability_validation.json`, and a generated rule pack whose rules exactly match the
applicable-authority partition. It also rechecks file-backed applicability-validation hashes for
decision, partition, retrieval/graph trace, search-coverage, and provenance artifacts. When a
compliance review phase is included, `phase-eval` requires
the review report to exist, validation to pass, the review ID to match when supplied, and the review
source set to match the evaluated source set. It also requires the compliance matrix artifact to
exist and match the review's schema version, review ID, source set, rule pack, row count, and status
counts. For reviewer-ready Custer Gallatin Forest Plan reviews, it also requires the separate Forest
Plan Compliance matrix section to exist and expose applicable standard rows. When a forest-plan
component eval phase is included,
`phase-eval` requires the component eval result schema version to match, pass, match the evaluated
source set, and match the supplied review ID when one is provided. The phase reports case counts,
component metrics, failed checks, and failure-category counts. When a forest-plan component
adjudication phase is included,
`phase-eval` requires the adjudication eval to exist, pass, match the evaluated source set, and match
the supplied review ID when one is provided. The phase reports queue count, resolved and pending
adjudication counts, real EA omission and system-miss counts/rates, completion rate, expectation
match rate, disposition counts, adjudication-outcome counts, and failure-category counts.

## Alignment And Next Milestone

The current implementation remains aligned with the v1 reviewer-engine goal: accurate, auditable,
verifiable compliance review against a local knowledge base. Domain knowledge lives in versioned
data artifacts such as workbook rows, review topics, eval fixtures, rule packs, and the coverage
matrix. Runtime code performs general capture, extraction, retrieval, graph construction, rule
binding, coverage validation, and phase evaluation.

Authority-universe Milestone 4 is aligned with that design because applicability quality is scored
before compliance quality: the seed eval covers positive and negative outcomes for all `19`
high-priority authority-family templates, includes an unresolved weak-signal validation-failure
case, and the gold eval replays an adjudicated Clean Water Act decision through the same
applicability adjudication artifacts used by review runs. The next authority-universe milestone is
Milestone 5: compliance review and report integration for authority-family provenance,
non-applicable authority appendices, reviewer-resolution reporting, and evidence-backed
litigation-risk summaries.

The Authority-First Compliance Matrix V0.4 milestone is implemented for the current local source-set
promotion gate. The active rule pack contains 48 authority rows and explicitly requires all 26
workbook `Scope=Baseline` source records in every EA review, with additional conditional rules for
triggered authorities. The refreshed coverage and gold gates contain ten adjudicated realistic
package profiles, expected source rows, expected source document classes, per-case failure taxonomy,
compact reproduction paths, and generated compliance matrices for the `0.4.0`/48-rule pack.

The current system has a complete 190-row downloader/catalog corpus that includes the four missed
Custer Gallatin FEIS and ESA-supporting plan documents. Full-source-set reuse-first extraction has
now been assembled for `source-set-ba8d0feae79501b8`: the current manifest has `189` extracted rows,
`1` scope-excluded row, `0` failures, and `18,822` chunks. The assembly reused `181` validated prior
extractions and `7` already-current Custer Gallatin slice records, then parsed
`R1PLAN-dakota-prairie-grasslands-02` as the only fresh extraction. Retrieval, evidence graph,
source claims, rule-claim bindings, compliance coverage, compliance-review eval, compliance-gold
eval, and phase eval have also been rebuilt and are reviewer-ready for the full current source set.
The Custer Gallatin LMP component inventory has also been generated for the current source set with
`329` components and `58` standards, and its build coverage passes with no missing or duplicate
component/standard IDs. Build coverage also records `2` suppressed component-like labels with
nonnumeric number tokens as inventory-quality issues instead of allowing rough IDs such as
`FW-GDL-VEGNF-See` into the inventory.
The prior 147-row downstream corpus remains useful for historical comparison only and should not be
treated as current promotion evidence for the expanded workbook.

The V1 CE/FANEC conditional-applicability milestone is implemented: grouped positive trigger
semantics and token-boundary matching for short acronyms now keep
`nepa_4336c_ce_adoption_screen`, `usda_nepa_ce_fanec_7cfr_1b3`, and
`usda_nepa_subcomponent_ce_7cfr_1b4` not applicable for the East Crazies package unless package
evidence shows an adopted CE, CE/FANEC screen, categorical-exclusion path, USDA CE screening, or
extraordinary-circumstances review. The milestone also carries explicit
`does_not_apply_if_package_terms` guards so negated same-chunk phrases such as a categorical
exclusion path not being used remain non-applicable evidence instead of positive CE triggers. The
live V1 eval now reports `conditional_false_positive=0` and `conditional_false_negative=0`.

The V1 baseline section-attribution milestone is implemented for `nepa_statute_chapter_55`: package
evidence routing now selects the EA purpose-and-need environmental-assessment span, and the live V1
eval reports `rule_source_section_expectations_met=true`, `rule_section_match_rate=1.0`,
`baseline_source_record_match_rate=1.0`, `baseline_document_role_match_rate=1.0`, and
`citation_requirement_match_rate=1.0`.

The V1 programmatic-tiering section-routing milestone is implemented: `nepa_4336b_programmatic_tiering`
now declares package section term groups for alternatives and environmental consequences, and
package evidence ranking uses those rule-declared groups as a context preference after the normal
tiering evidence match succeeds. The rule-pack validator and schema docs now cover these optional
section-preference fields so malformed `package_section_terms` or `package_section_term_groups`
fail validation instead of silently changing review behavior. The live V1 eval reports actual
package sections `alternatives` and `environmental_consequences`, actual source record `R1EA-005`,
actual document role `law`, `adjudication_pending=true`, and no `rule_section_mismatch`.

The V1 conditional-adjudication milestone is implemented. Each of the `18`
`conditional_source_expectations` in `config/v1_ecid_real_ea_eval.json` now has a
classification rationale, and the contract declares
`conditional_adjudication_policy.mode=accepted_pending_v1` with `accepted_pending_count=14`.
`v1-ea-eval` now emits a `conditional_adjudication` summary and full pending-results queue, fails
if accepted pending rule IDs/counts drift from the actual `adjudicate` rows, and keeps
source/section alignment enforced for actual applicable pending rows. The gap-close pass hardens
that policy contract so malformed accepted pending count/rule-ID fields fail with explicit contract
validation errors.

The V1 EA gate repair plan is complete through Milestone 6. The promoted review is
`v1-cg-ecid-compliance-review` for the East Crazy Inspiration Divide package on source set
`source-set-ba8d0feae79501b8`. The V1 eval contract still references base rule pack `nepa-ea-v0`
version `0.4.0`, while the reviewer-ready compliance review consumes the generated applicability
rule pack `generated-nepa-ea-v0-v1-cg-ecid-compliance-review` version `applicability-v0`. The gate
passes with `passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`,
`failure_category_counts={}`, `failed_rule_ids=[]`, `rule_section_match_rate=1.0`,
`conditional_false_positive=0`, `conditional_false_negative=0`, and `14` accepted-pending
conditional adjudication rows carried as explicit V1 reviewer risk. Review-bound `phase-eval` now
passes `21/21` phases with `review_packet_index` and `reviewer_ready=true`; the compliance gold
phase is satisfied by the passing base-pack gold suite through
`rule_pack_match_mode=generated_base`. Embeddings, reranking, model-assisted synthesis, and broader
Region 1 package expansion remain post-V1 work and should start under a new milestone plan.

## Verification Commands

Run all tests:

```bash
PYTHONPATH=src python -m pytest -q
```

Run captured-library integrity tests only:

```bash
PYTHONPATH=src python -m pytest tests/test_captured_library.py -q
```

Rebuild the full reviewer catalog from the current full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id corpus-update-2026-05-01-cg-support-batches
```

Build derived extraction outputs from the current reviewer catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

Inventory extraction reuse opportunities before a reuse-first rebuild:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory \
  --output-dir source_library
```

Assemble the current source set with reuse first, then parse only records without a valid current
or prior extraction candidate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library \
  --reuse-existing \
  --reuse-inventory-path source_library/derived/source-set-ba8d0feae79501b8/reuse_inventory/reuse_inventory.json
```

For a delta-only extraction, repeat `--id` for each selected source record. The 2026-04-30
land-exchange update used this mode for the 38 new artifact-bearing rows and left `R1EA-160`
unextracted because it is scope-excluded.

Build the evidence retrieval index:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library
```

Run a retrieval query:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-query \
  --output-dir source_library \
  --review-topic alternatives \
  "alternatives environmental effects"
```

Run the seed retrieval eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --eval-file config/retrieval_eval_seed.json
```

Build the evidence graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build \
  --output-dir source_library
```

Build source claims and run the seed claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
```

Build rule-claim bindings and run the seed rule-claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
```

Run the rule-pack coverage gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

Run the seed compliance review eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

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

Run the adjudicated gold eval promotion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
```

Run phase-aligned readiness evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library
```

Run the manifest-driven post-V1 promotion suite:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```
