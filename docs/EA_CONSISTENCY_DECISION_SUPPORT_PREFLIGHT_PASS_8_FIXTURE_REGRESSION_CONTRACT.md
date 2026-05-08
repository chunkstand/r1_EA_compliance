# EA Consistency Decision Support Preflight Pass 8

Date: 2026-05-06

Scope: `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` workstream 8,
Fixture And Regression Contract.

## Result

Status: `go` for pass 8.

This completes the manual Sequence 0 preflight. The next implementation boundary is Sequence 1:
Report Contract And Fixtures in `docs/EA_CONSISTENCY_DECISION_SUPPORT_MILESTONE_PLAN.md`.

## Boundary Checked

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- Report output boundary for later implementation:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`
- Planned report config owner:
  `config/ea_consistency_decision_support_v1.json`
- Planned real-review expectation fixture:
  `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
- Planned minimal schema fixture:
  `tests/fixtures/decision_support/minimal_decision_support_report.json`
- Planned focused test file:
  `tests/test_ea_consistency_decision_support.py`

This pass defines the fixture and regression contract only. It does not add the schema, fixtures,
generator, renderer, or validation gate.

## Worktree And Generated-Output Boundary

Command:

```bash
git status -sb
```

Observed status:

```text
## main...origin/main [ahead 5]
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.csv
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.md
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.pdf
?? East_Crazies_EA_Compliance_Review_2026-05-05.md
?? East_Crazies_EA_Compliance_Review_2026-05-05.pdf
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.md
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.pdf
```

Tracked files were clean at pass start. The root-level `East_Crazies_*` files remain untracked,
non-canonical manual draft comparison material and were not used as fixture sources. No generated
`source_library/` output was staged.

## Required Report Sections

The canonical decision-support JSON must contain these top-level report sections, and Markdown/PDF
renderings must be generated from those JSON sections:

1. `executive_determination`
2. `record_and_artifact_inventory`
3. `applicable_authority_summary`
4. `authority_findings`
5. `forest_plan_consistency`
6. `applicable_forest_plan_standards`
7. `non_applicable_authority_boundary`
8. `implementation_confirmation_checklist`
9. `residual_risk_register`
10. `validation_and_replay`

The schema must keep these concepts distinct:

- applicability status, sourced from applicability artifacts;
- compliance status, sourced from compliance findings or Forest Plan standard coverage;
- implementation-confirmation status, sourced from report config plus evidence selectors;
- residual-risk category and `legal_conclusion`, sourced from generated risk/resolution artifacts.

## Required Count Fields

The real-review expected-summary fixture must lock these count fields for
`v1-cg-ecid-compliance-review`:

| Field | Expected value |
| --- | ---: |
| `applicable_authority_count` | `34` |
| `non_applicable_authority_count` | `340` |
| `candidate_authority_count` | `374` |
| `authority_finding_count` | `34` |
| `authority_finding_status_counts.pass` | `34` |
| `non_applicable_search_coverage_certificate_count` | `340` |
| `forest_plan_component_finding_count` | `329` |
| `forest_plan_supported_component_count` | `79` |
| `forest_plan_not_applicable_component_count` | `250` |
| `forest_plan_gap_count` | `0` |
| `forest_plan_standard_count` | `58` |
| `forest_plan_applicable_standard_count` | `12` |
| `forest_plan_applied_standard_count` | `12` |
| `authority_reviewer_resolution_pending_count` | `0` |
| `forest_plan_reviewer_resolution_item_count` | `0` |
| `litigation_risk_flag_count` | `340` |
| `litigation_risk_legal_conclusion_count` | `0` |
| `package_file_count` | `43` |
| `package_chunk_count` | `1265` |

The report validation must fail on count drift unless the fixture is intentionally updated in the
same sequence as a verified upstream rerun.

## Required Hash Fields

The real-review fixture and generated report manifest must carry these input hash fields at minimum:

| Field | Current SHA-256 |
| --- | --- |
| `package_manifest_sha256` | `d0176a5cf6c991e5a7e2356a71b30bb9ceef55fe90bd70dd1fb135118e0a1a81` |
| `package_chunks_sha256` | `0d07dc16978652bc308c765299dfbfce1d50a0ca6a9d33f192c8c055cbd48b56` |
| `compliance_matrix_sha256` | `d02de0bc8b2357a733e9f8bb9c307fab3b086eca4e16656c6fa66f743c8c9bbc` |
| `compliance_review_sha256` | `89029906caeba41e11f5b8199a214f8e57385099f4c2de8d3f807a75c657a1a4` |
| `applicability_validation_sha256` | `d84d6b77adaa1fd9f86181aa8685f9545b63248ff07d7fcdc56616cdfc63bd56` |
| `applicable_authorities_sha256` | `ab6d5534cf57459d6d7b27750d53e72519ef46260e0bc4ffd5bf11e5957668ad` |
| `non_applicable_authorities_sha256` | `ed47def14fee3158e6fba1cb8892c878aaecab82aeaa069a31931d2a2542199b` |
| `search_coverage_certificates_sha256` | `639bd77243e48d9620ba7356bb5ca64be4de6c7a54e93de346ff04641d2ab68e` |
| `generated_rule_pack_sha256` | `c56d97d700e7fc8c27a95d4e5e93e14c26be3fb5edbf066b7c628cba60f53bb3` |
| `generated_rule_pack_validation_sha256` | `8f5197fa14fb6a83b0556b8c0f27a93a2c89cebde6c27dbde4531dd344bface0` |
| `forest_plan_component_findings_sha256` | `0ac3a2766446edab23806c666d9154f4c6f6e84b4e764f3cee677ac010d5d395` |
| `forest_plan_applicable_standard_coverage_sha256` | `bbd92f584f60b0a888cd779013f43acd82cd652f1e03fcf1d03003d756969145` |
| `forest_plan_context_summary_sha256` | `d8c1fbd04f0a019f9911a2d82e3c9d84f06b805e069a46cdb265319e1f81e178` |
| `non_applicable_authority_appendix_sha256` | `41c1dce781c2722c68aa28187fc1d73ec7080e91bb33507366153a8e383ad4b9` |
| `non_applicable_authority_appendix_markdown_sha256` | `d1ebb9043183e70fb1ad248bd9e2aeea509abfe990109737271df52c14dd46c5` |
| `authority_reviewer_resolution_report_sha256` | `6fd76085ed4cabda4b64d86c8c541ca25c8ccccbb3f9539df663979eacf40b3a` |
| `litigation_risk_summary_sha256` | `179714b0ad701586fc610b7c0cfad717df82664dc4b567aef5d917beee43b258` |
| `plan_consistency_table_text_sha256` | `07c688a0a68511ee652e9af22cbf39d03a7917d9365d1b18519efdf38e1a7564` |

The later report manifest should also record the SHA-256 for
`config/ea_consistency_decision_support_v1.json` once that tracked config exists.

## Required Fixture Rows

Sequence 1 should use these current artifact selectors as the real-review fixture anchors.

### Applicable Authority Row

Use `compliance_matrix.json` row `rule_id=eo_11990_wetlands`:

- `rule_title`: `Executive Order 11990 wetlands protection is addressed`
- `authority_category`: `executive_order`
- `authority_source_record_id`: `R1EA-104`
- `candidate_authority_id`: `rule-template:nepa-ea-v0:0.4.0:eo_11990_wetlands`
- `applicability_decision_id`: `58cf914cba81bea1d55591a5`
- `status`: `pass`
- `applicability_status`: `applicable`
- `applicability_mode`: `conditional`
- `ea_package_citation`: `EA-PACKAGE-041 (0094fc10f807)`
- `source_library_citation`: `R1EA-104 (9460e145d1df)`
- `source_claim_ids`: `claim:20c258ed3bb784c5d791bff6`,
  `claim:a39e467f45a3458336600433`, `claim:1c6fbe5bc4336cd16d1e9dbd`
- `limitations`: empty list

The schema test must require both `ea_package_evidence` and `source_library_evidence` with
`chunk_id`, `source_record_id`, `citation_label`, `artifact_sha256`, `content_sha256`, and text
span fields.

### Non-Applicable Authority Summary Row

Use `non_applicable_authority_appendix.json` row
`candidate_authority_id=rule-template:nepa-ea-v0:0.4.0:directives_notice_comment_36cfr_216`:

- `decision_id`: `4798417e93d038b92991762f`
- `authority_category`: `regulation`
- `basis_type`: `absent_trigger_evidence`
- `status`: `not_applicable`
- `source_record_ids`: `R1EA-027`
- `search_coverage_certificate_ids`: `1a2043fba159114bdbc8d610`
- `rationale`: `Required positive package trigger groups were not found within the recorded search boundary.`

The matching certificate in `search_coverage_certificates.json` must include:

- `coverage_certificate_id`: `1a2043fba159114bdbc8d610`
- `coverage_class`: `absent_trigger_evidence`
- `coverage_result`: `sufficient`
- `covered_candidate_authority_ids`: the selected candidate authority ID
- `covered_decision_ids`: `4798417e93d038b92991762f`
- `missing_query_variants`: empty list

The report must summarize this row as non-applicable boundary evidence, not as a compliance
finding.

### Forest Plan Component And Standard Row

Use `compliance_matrix.json` `forest_plan_compliance.rows[]` where
`component_id=R1PLAN-custer-gallatin-nf-02-FW-STD-RMZ-01`:

- `component_key`: `FW-STD-RMZ-01`
- `component_type`: `standard`
- `applicability_status`: `applicable`
- `compliance_status`: `complies`
- `finding_status`: `supported`
- `ea_package_citation`: `EA-PACKAGE-042 (bebc890bc3da)`
- `forest_plan_citation`: `R1PLAN-custer-gallatin-nf-02 (ff30e8b4530e)`
- `determination.source`: `ea_plan_consistency_table`
- `determination.review_section`: `Plan Consistency Table.pdf`

The schema test must require package evidence and Forest Plan evidence for this row.

### Applicable Standard Set

The real-review fixture must require exactly these `12` applicable standards:

| Component key | Component ID | Compliance status | Finding status |
| --- | --- | --- | --- |
| `FW-STD-RMZ-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-RMZ-01` | `complies` | `supported` |
| `FW-STD-PRISK-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-PRISK-01` | `complies` | `supported` |
| `FW-STD-WL-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-WL-01` | `complies` | `supported` |
| `FW-STD-WLBAT-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-WLBAT-01` | `complies` | `supported` |
| `FW-STD-WLGB-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-WLGB-01` | `complies` | `supported` |
| `FW-STD-TRIBAL-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-TRIBAL-01` | `complies` | `supported` |
| `FW-STD-ROS-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-ROS-01` | `complies` | `supported` |
| `FW-STD-IRA-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-IRA-01` | `complies` | `supported` |
| `FW-STD-RWA-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-RWA-01` | `complies` | `supported` |
| `FW-STD-BCA-01` | `R1PLAN-custer-gallatin-nf-02-FW-STD-BCA-01` | `complies` | `supported` |
| `AB-STD-RCREA-01` | `R1PLAN-custer-gallatin-nf-02-AB-STD-RCREA-01` | `complies` | `supported` |
| `BC-STD-CMBCA-01` | `R1PLAN-custer-gallatin-nf-02-BC-STD-CMBCA-01` | `complies` | `supported` |

The test must fail if any standard is missing, duplicated, has a non-`complies` status, lacks
package evidence, or lacks Forest Plan source evidence.

## Minimal Schema Fixture Contract

`tests/fixtures/decision_support/minimal_decision_support_report.json` should be small and
synthetic. It should include:

- one applicable authority row with both package and source evidence;
- one non-applicable authority summary row with search coverage;
- one Forest Plan component row;
- one applicable Forest Plan standard row;
- one implementation-confirmation row sourced from config plus package evidence selectors;
- one residual-risk row with `deterministic_basis=true` and `legal_conclusion=false`;
- validation metadata with `passed=true`;
- a manifest-shaped input hash map.

The fixture should not copy full East Crazies evidence text. It exists to prove schema boundaries
before the generator exists.

## Fail-Closed Regression Contract

Sequence 1 and Sequence 2 tests should cover these failure categories:

| Failure category | Required trigger |
| --- | --- |
| `missing_required_artifact` | Any required input artifact is absent. |
| `unparseable_required_artifact` | Required JSON/JSONL/Markdown/PDF input cannot be parsed or checked. |
| `review_source_set_mismatch` | Any input artifact names a different review ID or source set. |
| `input_hash_mismatch` | Current input hash differs from the manifest or validation-owned hash. |
| `count_drift` | Applicable authority, non-applicable authority, Forest Plan component, standard, resolution, or risk counts differ from the fixture without an explicit fixture update. |
| `missing_applicable_authority_row` | A required applicable authority is absent from the report. |
| `duplicate_applicable_authority_row` | A required applicable authority appears more than once. |
| `applicable_authority_missing_dual_evidence` | Applicable authority row lacks package evidence or source-library evidence. |
| `non_applicable_summary_missing` | Non-applicable authority summary or appendix pointer is absent. |
| `non_applicable_missing_search_coverage` | Non-applicable summary row lacks a sufficient search coverage certificate. |
| `non_applicable_promoted_to_finding` | A non-applicable authority appears as a compliance finding. |
| `forest_plan_component_summary_missing` | Forest Plan component summary is absent. |
| `applicable_standard_missing` | Any of the `12` applicable standards is absent. |
| `applicable_standard_missing_evidence` | Applicable standard lacks package evidence or Forest Plan source evidence. |
| `reviewer_resolution_open` | Authority or Forest Plan reviewer-resolution queue is nonzero. |
| `implementation_confirmation_selector_unresolved` | Config-owned checklist selector does not resolve to package, compliance, Forest Plan, or fixture evidence. |
| `residual_risk_legal_conclusion` | Residual-risk row has `legal_conclusion=true`. |
| `manual_draft_dependency` | Report input references root-level `East_Crazies_*` manual draft exports as canonical evidence. |
| `missing_report_pdf` | Decision-support PDF is absent when validation requires rendered outputs. |
| `invalid_report_pdf_header` | Decision-support PDF does not start with `%PDF-`. |

Tests should assert both the failure category and the failed source selector so failures are
debuggable without inspecting the whole report.

## Sequence 1 Acceptance Contract

Sequence 1 should be accepted when:

- `docs/OUTPUT_SCHEMAS.md` documents the decision-support artifact family and required fields;
- `config/ea_consistency_decision_support_v1.json` exists and owns synthesis-only labels,
  grouping, display order, caveats, and implementation-confirmation selectors;
- `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json` locks the real
  East Crazies counts, hashes, required sections, sample selectors, applicable standards, and
  fail-closed expectations;
- `tests/fixtures/decision_support/minimal_decision_support_report.json` exercises the schema
  without depending on full generated East Crazies evidence text;
- focused schema tests prove the contract distinguishes applicability, compliance,
  implementation confirmation, and residual risk;
- no generator, renderer, or generated `source_library/` report is required yet.

## Go/Stop Decision

Go condition from the plan:

> The first implementation sequence can add schema/fixture tests without needing to design the
> contract during generator implementation.

Pass-8 decision: `go`.

Rationale:

- Required report sections are fixed.
- Required count fields and current expected values are fixed.
- Required input hash fields and current hashes are fixed.
- Representative applicable, non-applicable, and Forest Plan fixture selectors are fixed.
- The complete applicable-standard set is fixed.
- Fail-closed categories for missing artifacts, count drift, stale hashes, missing PDF, missing
  non-applicable summary, unresolved implementation-confirmation selectors, and manual-draft
  dependency are fixed.

## Stop Conditions Not Triggered

- The test contract can distinguish applicability status from compliance status.
- The test contract can distinguish implementation confirmations from compliance findings.
- The test contract can distinguish residual-risk rows from legal conclusions.
- The test contract does not require root-level manual draft prose.
- The test contract does not require staging ignored generated artifacts.

## Next Implementation Boundary

Begin Sequence 1: Report Contract And Fixtures.

Sequence 1 should add the tracked schema docs, config, fixtures, and focused tests described above.
It should not implement the full report generator or write the real
`source_library/reviews/v1-cg-ecid-compliance-review/decision_support/` output yet.
