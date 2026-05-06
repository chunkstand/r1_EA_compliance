# EA Consistency Decision Support Preflight Pass 6

Date: 2026-05-06

Scope: `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` workstream 6,
Residual Risk And Implementation Confirmation Source Mapping.

## Result

Status: `go` for pass 6 only.

This does not complete the full Sequence 0 preflight. The next preflight pass is CLI, Module, And
Renderer Ownership.

## Boundary Checked

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- Package path:
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`
- Report output boundary for later implementation:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`
- Planned tracked synthesis owner for Sequence 1:
  `config/ea_consistency_decision_support_v1.json`

The planned config file is not created in this pass. It is the required tracked owner for
decision-support-only taxonomy and wording, including implementation-confirmation labels,
row-grouping rules, residual-risk grouping rules, and allowed report caveat text. The generated
report must still source evidence from the artifacts listed below.

## Worktree And Generated-Output Boundary

Command:

```bash
git status -sb
```

Observed status:

```text
## main...origin/main [ahead 3]
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.csv
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.md
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.pdf
?? East_Crazies_EA_Compliance_Review_2026-05-05.md
?? East_Crazies_EA_Compliance_Review_2026-05-05.pdf
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.md
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.pdf
```

Tracked files were clean at pass start. The root-level `East_Crazies_*` files remain untracked,
non-canonical manual draft comparison material and were not used as implementation-confirmation or
residual-risk evidence.

Command:

```bash
git check-ignore -v \
  source_library/reviews/v1-cg-ecid-compliance-review/litigation_risk_summary.json \
  source_library/reviews/v1-cg-ecid-compliance-review/authority_reviewer_resolution_report.json \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_review.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json \
  source_library/reviews/v1-cg-ecid-compliance-review/package/package_chunks.jsonl
```

Observed classification:

```text
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/litigation_risk_summary.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/authority_reviewer_resolution_report.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/compliance_review.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/package/package_chunks.jsonl
```

The pass treated generated evidence as ignored local artifacts. No generated `source_library/`
output was staged.

## Artifact Parse And Hash Baseline

Commands:

```bash
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_reviewer_resolution_queue.json \
  /tmp/ecid_forest_plan_reviewer_resolution_queue.validated.json
shasum -a 256 \
  source_library/reviews/v1-cg-ecid-compliance-review/litigation_risk_summary.json \
  source_library/reviews/v1-cg-ecid-compliance-review/authority_reviewer_resolution_report.json \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_review.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_reviewer_resolution_queue.json \
  source_library/reviews/v1-cg-ecid-compliance-review/package/package_manifest.jsonl \
  source_library/reviews/v1-cg-ecid-compliance-review/package/package_chunks.jsonl
```

Current SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `litigation_risk_summary.json` | `179714b0ad701586fc610b7c0cfad717df82664dc4b567aef5d917beee43b258` |
| `authority_reviewer_resolution_report.json` | `6fd76085ed4cabda4b64d86c8c541ca25c8ccccbb3f9539df663979eacf40b3a` |
| `compliance_matrix.json` | `d02de0bc8b2357a733e9f8bb9c307fab3b086eca4e16656c6fa66f743c8c9bbc` |
| `compliance_review.json` | `89029906caeba41e11f5b8199a214f8e57385099f4c2de8d3f807a75c657a1a4` |
| `forest_plan_applicable_standard_coverage.json` | `bbd92f584f60b0a888cd779013f43acd82cd652f1e03fcf1d03003d756969145` |
| `forest_plan_component_findings.json` | `0ac3a2766446edab23806c666d9154f4c6f6e84b4e764f3cee677ac010d5d395` |
| `package_manifest.jsonl` | `d0176a5cf6c991e5a7e2356a71b30bb9ceef55fe90bd70dd1fb135118e0a1a81` |
| `package_chunks.jsonl` | `0d07dc16978652bc308c765299dfbfce1d50a0ca6a9d33f192c8c055cbd48b56` |
| `forest_plan_reviewer_resolution_queue.json` | `3e3b9d9eb9bf4dad1a82b8875faac4f98e5e5c6ec925f81a1bbd853ca7afb6f9` |

## Residual-Risk Source Mapping

The residual-risk register for the full decision-support report must be generated from these
deterministic sources:

| Report input | Deterministic owner | Current result | Report rule |
| --- | --- | --- | --- |
| Compliance finding limitations | `compliance_matrix.json` `rows[].limitations` and `compliance_review.json` `findings[].limitations` | `33/33` rows have empty limitations | Emit per-authority limitations only from the owning row. Empty lists must remain empty, not be replaced with narrative risk. |
| Deterministic litigation-risk flags | `litigation_risk_summary.json` `summary` and `risk_flags[]` | `340` flags, all `non_applicable_authority_coverage_boundary`; all `informational`; `deterministic_basis=true`; `legal_conclusion=false`; `legal_conclusion_count=0` | Summarize as non-applicable authority boundary risk and link the full appendix/search coverage. Do not convert these flags into legal conclusions or compliance findings. |
| Authority reviewer-resolution status | `authority_reviewer_resolution_report.json` `summary` | `pending_resolution_count=0`, `adjudicated_authority_count=0`, `reviewer_ready_blocked=false`, `passed=true` | Emit zero open authority-resolution items. A future nonzero pending count must block reviewer-ready report generation or become an explicit failed gate. |
| Forest Plan reviewer-resolution status | `forest_plan_reviewer_resolution_queue.json` `item_count` and `items[]` | `item_count=0` | Emit zero open Forest Plan reviewer-resolution items. A future nonzero count must block or be surfaced as a reviewer-resolution blocker. |
| Forest Plan standard limitations | `forest_plan_applicable_standard_coverage.json` `standards[].failure_reasons`, `standards[].finding_status`, and `standards[].compliance_status` | `12` applicable standards, all `complies` and `supported`, no `failure_reasons` | Emit standard-level limitations only from `failure_reasons` or failed coverage checks. Empty lists must remain empty. |
| Forest Plan component limitations | `forest_plan_component_findings.json` `summary`, `validation`, and `findings[]` | `329` findings, `79` supported, `250` not applicable, `gap_count=0`, `needs_reviewer_resolution_count=0`, `reviewer_ready=true` | Use generated Forest Plan findings and validation counts. Do not reinterpret the Plan Consistency Table manually. |
| Package and source evidence spans | `package/package_chunks.jsonl`, `compliance_matrix.json` row evidence fields, `compliance_review.json` finding evidence fields, and Forest Plan evidence fields | All applicable authority rows have package/source citations; all applicable standards have package and plan evidence | Every emitted risk or confirmation row must carry artifact path plus row selector, chunk ID, finding ID, standard ID, or candidate authority ID. |

Pass-6 inspection found no current residual-risk category that requires manual narrative judgment.
The only current risk flags are deterministic non-applicable-authority boundary flags, and the
artifact explicitly records that it is not a legal-conclusion generator.

## Implementation-Confirmation Checklist Mapping

The full milestone requires implementation confirmations for closing instruments, deed
restrictions, easements, appraisal/equalization/title file, NHPA MOA/mitigation, wetland
protections, ESA/botany/whitebark/trail controls, access terms, and construction-phase commitments.
These are report-synthesis checklist rows, not new compliance findings.

The generator must use a tracked config or fixture to own row labels, grouping, display order, and
allowed caveat wording. The current planned owner is
`config/ea_consistency_decision_support_v1.json`. The generated evidence selectors for the current
East Crazies report can come from the following sources:

| Checklist item | Current generated evidence selectors | Planned tracked owner |
| --- | --- | --- |
| Closing instruments | `package/package_chunks.jsonl`: `EA-PACKAGE-040` `chunk:0ca9dea170f2dc8a324053b1a3f1cf82`; `EA-PACKAGE-041` `chunk:e0763c496dded55f8de8121572617e15` and `chunk:34633ce2011cdaf1930e1921bc8ef41a`; `EA-PACKAGE-043` `chunk:080a57381869a0c74fca257b64c56c94` | `implementation_confirmations.closing_instruments` |
| Deed restrictions and patent reservations | `package/package_chunks.jsonl`: `EA-PACKAGE-040` chunks `chunk:0ca9dea170f2dc8a324053b1a3f1cf82`, `chunk:75bcee85e5f141d5de88963e5fa7bdff`, `chunk:96d1cdc6268e0553fb7b998f4cbe688e`; `EA-PACKAGE-041` `chunk:e0763c496dded55f8de8121572617e15`; `compliance_matrix.json` row `eo_11990_wetlands` | `implementation_confirmations.deed_restrictions` |
| Easements and reserved rights | `package/package_chunks.jsonl`: `EA-PACKAGE-040` `chunk:dfb41b44b7834c258650d6629dfa7725` and `chunk:61f087312869ed391c840f04b7bdc823`; `EA-PACKAGE-043` `chunk:080a57381869a0c74fca257b64c56c94`; Forest Plan standard `AB-STD-RCREA-01` in `forest_plan_applicable_standard_coverage.json` | `implementation_confirmations.easements` |
| Appraisal, equalization, mineral/title, and water-right file | `package/package_chunks.jsonl`: `EA-PACKAGE-002` chunks `chunk:dedcacf3e7f7c2b780c3020b503dbf9f`, `chunk:0b160f410213225e488200f9f2448345`, `chunk:9fe20ca4b96e5b2aaf136ecf6452e572`, `chunk:d3ca9b130709b29a39791146c4f1c468`, `chunk:a829dd67c4b06c31f44ce946905104d0`; `EA-PACKAGE-003` `chunk:0bc971166d3ad29f9cf5c802bd188ea6`; `EA-PACKAGE-005` package record for mineral potential | `implementation_confirmations.appraisal_equalization_title` |
| NHPA, SHPO, MOA, and cultural-resource mitigation | `compliance_matrix.json` row `montana_shpo_review`; `package/package_chunks.jsonl`: `EA-PACKAGE-002` chunks `chunk:f4346f9a5862b7ce03ff2c15f5e97322` and `chunk:e7fb14c4619e8701b46439993f12a446`; `EA-PACKAGE-003` `chunk:6c7da82e50972f9d58ca97578221d95b`; `EA-PACKAGE-009` `chunk:99bf7c6d81864df40bce2a4fce1c75e0`; `EA-PACKAGE-041` `chunk:34633ce2011cdaf1930e1921bc8ef41a` | `implementation_confirmations.nhpa_moa_mitigation` |
| Wetland protections | `compliance_matrix.json` row `eo_11990_wetlands`; `package/package_chunks.jsonl`: `EA-PACKAGE-041` `chunk:e0763c496dded55f8de8121572617e15`; `package/package_manifest.jsonl` records `EA-PACKAGE-014`, `EA-PACKAGE-031`, and `EA-PACKAGE-032`; Forest Plan standard `FW-STD-RMZ-01` in `forest_plan_applicable_standard_coverage.json` | `implementation_confirmations.wetland_protections` |
| ESA, botany, whitebark pine, wildlife, and trail controls | `compliance_matrix.json` rows `esa_section_7`, `fsm_2670_species_policy`, and `region1_species_of_conservation_concern`; `package/package_manifest.jsonl` records `EA-PACKAGE-007` and `EA-PACKAGE-015`; `forest_plan_applicable_standard_coverage.json` standards `FW-STD-PRISK-01`, `FW-STD-WLGB-01`, `FW-STD-RWA-01`, `AB-STD-RCREA-01`, and `BC-STD-CMBCA-01`; `package/package_chunks.jsonl` Plan Consistency Table selectors for those standard rows | `implementation_confirmations.esa_botany_whitebark_trail_controls` |
| Access terms | `forest_plan_applicable_standard_coverage.json` standard `AB-STD-RCREA-01`; `package/package_chunks.jsonl`: `EA-PACKAGE-002` `chunk:8a3f50bce9e17ca5bc2032b3bae70d99`; `package/package_manifest.jsonl` records `EA-PACKAGE-012`, `EA-PACKAGE-035`, and `EA-PACKAGE-043`; `compliance_matrix.json` row `planning_rule_36cfr_21915_consistency` for Forest Plan consistency | `implementation_confirmations.access_terms` |
| Construction-phase commitments | `forest_plan_applicable_standard_coverage.json` standards `FW-STD-RMZ-01`, `FW-STD-ROS-01`, `FW-STD-IRA-01`, `FW-STD-RWA-01`, `AB-STD-RCREA-01`, and `BC-STD-CMBCA-01`; `package/package_chunks.jsonl`: `EA-PACKAGE-003` `chunk:c3caf75859f944ad93e9db3cd4803fb0`; `EA-PACKAGE-042` chunks `chunk:1f553ff325c15cc99950d9dc9910b5a4`, `chunk:36fa423ff8795b3edbe71dc582789ee3`, and `chunk:8472a8487482d848f0f57d9de21b1804` | `implementation_confirmations.construction_phase_commitments` |

The report generator should treat those selectors as evidence pointers. It should not claim that an
implementation confirmation is complete unless the owning generated artifact or future tracked
config explicitly marks the item as complete. Draft closing language must remain a confirmation
item, not proof of final closing.

## Source-Mapping Rules For Sequence 1

Sequence 1 should add a tracked report contract or fixture with these minimum constraints:

- every implementation-confirmation item has an ID, display label, source selectors, evidence
  status, and allowed report wording;
- every residual-risk row has a source artifact path, source selector, category, severity,
  `deterministic_basis`, and `legal_conclusion`;
- rows derived from `litigation_risk_summary.json` must preserve `legal_conclusion=false`;
- rows derived from compliance or Forest Plan limitations must preserve the owning finding,
  standard, component, or candidate-authority ID;
- empty limitation arrays and empty reviewer-resolution queues must render as empty/zero, not as
  speculative risk prose;
- future generated reports must fail closed if a config-owned checklist selector does not resolve
  to current package evidence, compliance evidence, Forest Plan evidence, or tracked fixture data.

## Go/Stop Decision

Go condition from the plan:

> Every checklist item and residual-risk row has a deterministic source path or a planned tracked
> configuration owner.

Pass-6 decision: `go`.

Rationale:

- Residual-risk rows are owned by `litigation_risk_summary.json`,
  `authority_reviewer_resolution_report.json`, compliance limitation fields, Forest Plan limitation
  fields, and Forest Plan reviewer-resolution artifacts.
- The current risk state is deterministic: `340` informational non-applicable-boundary flags,
  `0` legal-conclusion flags, `0` open authority-resolution items, `0` open Forest Plan
  reviewer-resolution items, no compliance limitations, and no applicable-standard failure reasons.
- Every required implementation-confirmation checklist item has current generated evidence selectors
  and a planned tracked configuration owner for Sequence 1.
- The full decision-support generator can source these sections from audited artifacts and tracked
  config without using manual root-level draft prose.

## Stop Conditions Not Triggered

- The report does not need manual narrative judgment for current residual-risk rows.
- The report does not need to convert implementation confirmations into new compliance findings.
- The report does not need root-level manual draft exports as canonical evidence.
- The report does not need generated `source_library/` files to be staged.
- There are no open reviewer-resolution items that would block a current East Crazies
  decision-support report.

## Next Preflight Pass

Begin pass 7: CLI, Module, And Renderer Ownership.

Pass 7 should choose and document the implementation surface for the full milestone:

- preferred CLI command name: `ea-consistency-document`;
- canonical JSON owner module under `src/usfs_r1_ea_sources/`;
- Markdown/PDF rendering path, preferably reusing the existing compliance-matrix rendering pattern;
- schema/docs owner under `docs/OUTPUT_SCHEMAS.md` and the milestone plan;
- focused schema/generator/gate tests plus `tests/test_architecture_contract.py` when code
  boundaries change.
