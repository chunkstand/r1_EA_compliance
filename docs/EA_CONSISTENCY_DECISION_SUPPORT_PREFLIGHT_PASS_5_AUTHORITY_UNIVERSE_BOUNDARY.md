# EA Consistency Decision Support Preflight Pass 5

Date: 2026-05-06

Scope: `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` workstream 5,
Authority Universe Boundary.

## Result

Status: `go` for pass 5 only.

This does not complete the full Sequence 0 preflight. The next preflight pass is Residual Risk And
Implementation Confirmation Source Mapping.

## Boundary Checked

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- Applicability run:
  `applicability-determine:v1-cg-ecid-compliance-review:source-set-ba8d0feae79501b8`
- Generated rule pack: `generated-nepa-ea-v0-v1-cg-ecid-compliance-review`
- Generated rule pack version: `applicability-v0`

## Worktree And Generated-Output Boundary

Command:

```bash
git status -sb
```

Observed status:

```text
## main...origin/main [ahead 1]
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.csv
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.md
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.pdf
?? East_Crazies_EA_Compliance_Review_2026-05-05.md
?? East_Crazies_EA_Compliance_Review_2026-05-05.pdf
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.md
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.pdf
```

Tracked files were clean at pass start. The branch was ahead of `origin/main` by the completed
pass-4 commit. The root-level `East_Crazies_*` files remain untracked, non-canonical manual draft
exports and were not used as authority-universe evidence.

Command:

```bash
git check-ignore -v \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack_validation.json \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json \
  source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.md
```

Observed classification:

```text
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack_validation.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.md
```

The pass treated authority artifacts as ignored local generated evidence. No generated
`source_library/` output was staged.

## Artifact Parse And Hash Baseline

Commands:

```bash
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json \
  /tmp/ecid_pass5_applicable_authorities.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json \
  /tmp/ecid_pass5_non_applicable_authorities.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json \
  /tmp/ecid_pass5_search_coverage.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack_validation.json \
  /tmp/ecid_pass5_generated_rule_pack_validation.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json \
  /tmp/ecid_pass5_compliance_matrix.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.json \
  /tmp/ecid_pass5_non_applicable_authority_appendix.json
shasum -a 256 \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack_validation.json \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json \
  source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.json \
  source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.md \
  source_library/reviews/v1-cg-ecid-compliance-review/authority_family_provenance.json \
  source_library/reviews/v1-cg-ecid-compliance-review/authority_reviewer_resolution_report.json
```

Parse results:

- `applicable_authorities.json`: `json_ok`
- `non_applicable_authorities.json`: `json_ok`
- `search_coverage_certificates.json`: `json_ok`
- `generated_rule_pack_validation.json`: `json_ok`
- `compliance_matrix.json`: `json_ok`
- `non_applicable_authority_appendix.json`: `json_ok`
- `non_applicable_authority_appendix.md`: nonempty Markdown, `349` lines and `83178` bytes

Current SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `applicable_authorities.json` | `ab6d5534cf57459d6d7b27750d53e72519ef46260e0bc4ffd5bf11e5957668ad` |
| `non_applicable_authorities.json` | `ed47def14fee3158e6fba1cb8892c878aaecab82aeaa069a31931d2a2542199b` |
| `search_coverage_certificates.json` | `639bd77243e48d9620ba7356bb5ca64be4de6c7a54e93de346ff04641d2ab68e` |
| `generated_rule_pack.json` | `c56d97d700e7fc8c27a95d4e5e93e14c26be3fb5edbf066b7c628cba60f53bb3` |
| `generated_rule_pack_validation.json` | `8f5197fa14fb6a83b0556b8c0f27a93a2c89cebde6c27dbde4531dd344bface0` |
| `compliance_matrix.json` | `d02de0bc8b2357a733e9f8bb9c307fab3b086eca4e16656c6fa66f743c8c9bbc` |
| `non_applicable_authority_appendix.json` | `41c1dce781c2722c68aa28187fc1d73ec7080e91bb33507366153a8e383ad4b9` |
| `non_applicable_authority_appendix.md` | `d1ebb9043183e70fb1ad248bd9e2aeea509abfe990109737271df52c14dd46c5` |
| `authority_family_provenance.json` | `f93bf7d018845870960e56ae6716563a59929bec51e390297f83cb0bd6731f26` |
| `authority_reviewer_resolution_report.json` | `6fd76085ed4cabda4b64d86c8c541ca25c8ccccbb3f9539df663979eacf40b3a` |

## Applicable Authority Side

`applicable_authorities.json` remains the canonical applicable-authority partition:

- schema: `applicable-authorities-v0`
- applicable authorities: `33`
- review/source-set match:
  `v1-cg-ecid-compliance-review` / `source-set-ba8d0feae79501b8`
- unique applicable candidate authority IDs: `33`
- unique applicable decision IDs: `33`

Applicable authority categories:

| Category | Count |
| --- | ---: |
| `law` | `12` |
| `regulation` | `12` |
| `agency_policy` | `5` |
| `executive_order` | `2` |
| `state_requirement` | `1` |
| `case_law` | `1` |

Generated compliance outputs remain aligned to this applicable partition:

- `generated_rule_pack.json` records `33` applicable authorities and `33` generated rules.
- Every generated rule candidate authority ID maps to an applicable authority decision.
- `compliance_matrix.json` contains `33` rows, all with `applicability_status=applicable` and
  `status=pass`.
- Every compliance matrix candidate authority ID maps to an applicable authority decision.
- Every applicable authority decision has a matching compliance matrix row.
- `authority_family_provenance.json` contains `33` finding-authority provenance rows, all mapping
  back to applicable authority decisions.

## Non-Applicable Authority Side

`non_applicable_authorities.json` remains the canonical non-applicable-authority partition:

- schema: `non-applicable-authorities-v0`
- non-applicable authorities: `340`
- review/source-set match:
  `v1-cg-ecid-compliance-review` / `source-set-ba8d0feae79501b8`
- unique non-applicable candidate authority IDs: `340`
- unique non-applicable decision IDs: `340`

Non-applicable authority categories:

| Category | Count |
| --- | ---: |
| `forest_plan` | `330` |
| `regulation` | `7` |
| `law` | `3` |

Non-applicable basis and coverage classes:

| Basis or coverage class | Count |
| --- | ---: |
| `negative_package_evidence` | `329` |
| `absent_trigger_evidence` | `11` |

`search_coverage_certificates.json` remains the search-coverage owner for non-applicable
authorities:

- schema: `search-coverage-certificates-v0`
- certificates: `340`
- unique certificate IDs: `340`
- coverage result: `sufficient` for all `340`
- every non-applicable authority references a search coverage certificate
- every referenced certificate exists
- every certificate covers exactly non-applicable candidate/decision IDs in this review partition

`non_applicable_authority_appendix.json/.md` remains the reviewer-facing non-applicable appendix:

- schema: `non-applicable-authority-appendix-v0`
- appendix authorities: `340`
- appendix rows align exactly to the `340` non-applicable authority IDs
- summary reports `all_have_coverage_certificates=true`
- summary reports `all_have_rationale=true`
- Markdown appendix is nonempty and points back to the generated non-applicable authority artifact
  and search coverage certificates

## Partition And Generated-Rule Checks

Structured inspection found:

- applicable/non-applicable candidate-authority overlap: `0`
- applicable plus non-applicable candidate-authority total: `373`
- non-applicable authorities without matching coverage certificates: `0`
- coverage certificates not tied to non-applicable authorities: `0`
- applicable authorities without generated rules: `0`
- generated rules without applicable authority decisions: `0`
- compliance matrix rows without applicable authority decisions: `0`
- applicable authority decisions without compliance matrix rows: `0`
- non-applicable authorities missing from the appendix: `0`
- appendix rows outside the non-applicable authority partition: `0`
- applicable authorities missing from authority-family provenance: `0`
- provenance rows outside the applicable authority partition: `0`

The generated-rule-pack validation also passed these relevant checks:

- `applicability_validation_passed`
- `generated_rule_count_matches_applicable_authority_count`
- `all_generated_rules_trace_to_applicable_decisions`
- `generated_rules_carry_required_applicability_metadata`
- `non_applicable_authorities_are_absent_from_generated_rules`
- `generated_rule_pack_hashes_match_current_applicability_artifacts`

The applicability validation also passed these relevant checks:

- `applicable_and_non_applicable_partition_candidate_universe`
- `no_unresolved_or_needs_adjudication_decisions`
- `non_applicable_decisions_have_basis_or_adjudication`
- `artifact_hashes_match_current_inputs`
- `provenance_covers_required_applicability_artifacts`

## Compliance Matrix Boundary

`compliance_matrix.json` keeps the non-applicable side out of compliance findings:

- matrix row count: `33`
- applicable row count: `33`
- not-applicable matrix row count: `0`
- compliance status: all `33` generated compliance findings are `pass`
- generated rule pack ID: `generated-nepa-ea-v0-v1-cg-ecid-compliance-review`
- generated rule pack version: `applicability-v0`
- matrix summary links the non-applicable authority source artifacts:
  - `source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json`
  - `source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json`
  - `source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.json`
  - `source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.md`

This proves the full decision-support report must summarize non-applicable authorities from their
own artifacts and appendix, not by recreating them as compliance matrix rows or collapsing them into
a generic disclaimer.

## Go/Stop Decision

Go condition from the plan:

> The full report can show both sides of the authority boundary with counts, categories, coverage,
> and artifact pointers.

Pass-5 decision: `go`.

Rationale:

- Applicable authorities are a first-class generated artifact with `33` unique applicable
  decisions.
- Non-applicable authorities are a first-class generated artifact with `340` unique
  non-applicable decisions.
- The two partitions are disjoint and cover all `373` current candidate authorities.
- Search coverage certificates and the non-applicable appendix align exactly to the
  non-applicable authority partition.
- The generated rule pack and compliance matrix include only validated applicable authorities.
- The compliance matrix links to non-applicable authority artifacts instead of double-counting or
  burying non-applicability.

## Stop Conditions Not Triggered

- The full report does not need to omit non-applicable authorities.
- Non-applicable authorities are not double-counted as compliance findings.
- Search-coverage traceability is intact for all `340` non-applicable authorities.
- Manual root-level East Crazies prose is not needed to summarize the authority universe boundary.

## Next Preflight Pass

Begin pass 6: Residual Risk And Implementation Confirmation Source Mapping.

Pass 6 should decide where each implementation-confirmation and residual-risk entry will come from:

- generated compliance limitations;
- `litigation_risk_summary.json`;
- `authority_reviewer_resolution_report.json`;
- Forest Plan applicable-standard limitations;
- package evidence spans and source evidence spans;
- a new tracked config or fixture if a risk or checklist item is needed but is not already
  represented in current generated artifacts.
