# EA Consistency Decision Support Preflight Pass 4

Date: 2026-05-06

Scope: `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` workstream 4,
Forest Plan Consistency Baseline.

## Result

Status: `go` for pass 4 only.

This does not complete the full Sequence 0 preflight. The next preflight pass is Authority Universe
Boundary.

## Boundary Checked

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- Forest Plan profile: promoted Custer Gallatin profile, recorded as
  `scope_status=custer_gallatin`
- Forest Plan consistency package record: `EA-PACKAGE-042`
- Forest Plan consistency package title: `Plan Consistency Table.pdf`

## Worktree And Generated-Output Boundary

Command:

```bash
git status -sb
```

Observed status:

```text
## main...origin/main
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.csv
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.md
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.pdf
?? East_Crazies_EA_Compliance_Review_2026-05-05.md
?? East_Crazies_EA_Compliance_Review_2026-05-05.pdf
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.md
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.pdf
```

Tracked files were clean at pass start. The root-level `East_Crazies_*` files remain untracked,
non-canonical manual draft exports and were not used as Forest Plan consistency evidence.

Command:

```bash
git check-ignore -v \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json \
  source_library/reviews/v1-cg-ecid-compliance-review/package/extracted_text/EA-PACKAGE-042_bebc890bc3da89c0.txt
```

Observed classification:

```text
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json
.git/info/exclude:8:/source_library	source_library/reviews/v1-cg-ecid-compliance-review/package/extracted_text/EA-PACKAGE-042_bebc890bc3da89c0.txt
```

The pass treated these as ignored local evidence artifacts. No generated `source_library/` output
was staged.

## Artifact Parse And Hash Baseline

Commands:

```bash
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json \
  /tmp/ecid_forest_plan_component_findings.pass4.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json \
  /tmp/ecid_forest_plan_standard_coverage.pass4.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json \
  /tmp/ecid_forest_plan_context_summary.pass4.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json \
  /tmp/ecid_forest_plan_component_eval_results.pass4.json
shasum -a 256 \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json \
  source_library/reviews/v1-cg-ecid-compliance-review/package/extracted_text/EA-PACKAGE-042_bebc890bc3da89c0.txt
```

Parse results:

- `forest_plan_component_findings.json`: `json_ok`
- `forest_plan_applicable_standard_coverage.json`: `json_ok`
- `forest_plan_context_summary.json`: `json_ok`
- `forest_plan_component_eval_results.json`: `json_ok`
- `EA-PACKAGE-042_bebc890bc3da89c0.txt`: nonempty extracted text, `551` lines and `437229`
  bytes

Current SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `forest_plan_component_findings.json` | `0ac3a2766446edab23806c666d9154f4c6f6e84b4e764f3cee677ac010d5d395` |
| `forest_plan_applicable_standard_coverage.json` | `bbd92f584f60b0a888cd779013f43acd82cd652f1e03fcf1d03003d756969145` |
| `forest_plan_context_summary.json` | `d8c1fbd04f0a019f9911a2d82e3c9d84f06b805e069a46cdb265319e1f81e178` |
| `EA-PACKAGE-042_bebc890bc3da89c0.txt` | `07c688a0a68511ee652e9af22cbf39d03a7917d9365d1b18519efdf38e1a7564` |

These hashes match the pass-2 artifact freshness baseline for the overlapping Forest Plan and Plan
Consistency Table inputs.

## Plan Consistency Table Evidence

`EA-PACKAGE-042` is present exactly once in `package_manifest.jsonl`:

- title: `Plan Consistency Table.pdf`
- status: `extracted`
- citation label: `EA-PACKAGE-042 (bebc890bc3da)`
- package source-set label: `ea-package-v1-cg-ecid-compliance-review`
- artifact hash:
  `bebc890bc3da89c03d0cf8d906b4c9c9b7b29fe7a9abe2237bd17605c1db300c`
- package-manifest normalized text hash:
  `cbdd674285c2ea145fdcd3287b19877924f41dd6651d51d9125905af74f4118b`
- raw extracted-text file hash:
  `07c688a0a68511ee652e9af22cbf39d03a7917d9365d1b18519efdf38e1a7564`
- package chunks: `312`, with chunk indexes `0` through `311`

The Plan Consistency Table is therefore available as package evidence for generated Forest Plan
findings. It is not the owner of Forest Plan consistency conclusions for the full decision-support
report.

## Generated Forest Plan Artifact Ownership

`forest_plan_component_findings.json` remains the component-level owner:

- schema: `forest-plan-component-findings-v0`
- validation schema: `forest-plan-component-findings-validation-v0`
- validation: `passed=true`
- reviewer-ready: `true`
- review/source-set match:
  `v1-cg-ecid-compliance-review` / `source-set-ba8d0feae79501b8`
- component findings: `329`
- supported/applicable findings: `79`
- not-applicable findings: `250`
- gap findings: `0`
- reviewer-resolution items: `0`
- provenance-complete findings: `329`

Relevant validation checks passed:

- `supported_findings_have_package_and_plan_evidence`
- `supported_package_evidence_section_bindings_match`
- `component_inventory_coverage_passes`
- `all_applicable_standards_applied`

The artifact records `293` generated package component determinations sourced from
`EA-PACKAGE-042` and `ea_plan_consistency_table`: `92` affirmative table determinations and `201`
negative table determinations. Package evidence records use the Plan Consistency Table heavily
(`310` package evidence records from `EA-PACKAGE-042`), while generated findings remain the
canonical owner of component status, compliance status, plan-source evidence, package evidence, and
reviewer-resolution state.

`forest_plan_applicable_standard_coverage.json` remains the applicable-standard owner:

- schema: `forest-plan-applicable-standard-coverage-v0`
- validation: `passed=true`
- review/source-set match:
  `v1-cg-ecid-compliance-review` / `source-set-ba8d0feae79501b8`
- standards in inventory: `58`
- applicable standards: `12`
- applied standards: `12`
- not-applicable standards: `46`
- all applicable standards applied: `true`

The `12` applicable standards are:

```text
FW-STD-RMZ-01, FW-STD-PRISK-01, FW-STD-WL-01, FW-STD-WLBAT-01,
FW-STD-WLGB-01, FW-STD-TRIBAL-01, FW-STD-ROS-01, FW-STD-IRA-01,
FW-STD-RWA-01, FW-STD-BCA-01, AB-STD-RCREA-01, BC-STD-CMBCA-01
```

All `12` applicable standards carry plan-source evidence from
`R1PLAN-custer-gallatin-nf-02 (ff30e8b4530e)` and all `12` are marked applied. Eleven applicable
standards carry `EA-PACKAGE-042` Plan Consistency Table package evidence directly. The remaining
applicable standard, `AB-STD-RCREA-01`, is owned by the same generated coverage artifact and is
supported by EA/recreation-access package evidence rather than a direct Plan Consistency Table row.

`forest_plan_context_summary.json` remains the selected-profile context owner:

- schema: `forest-plan-context-summary-v0`
- `scope_status=custer_gallatin`
- `reviewer_ready=true`
- `validation_passed=true`
- `needs_reviewer_resolution=false`
- package files/chunks: `43` files and `1265` chunks
- selected context: `2` geographic areas, `1` management area, and `2` overlays
- supporting plan evidence records: `5`

Selected generated context:

- geographic areas: Bridger, Bangtail, and Crazy Mountains; Madison, Henrys Lake, and Gallatin
  Mountains
- management area: Crazy Mountains Backcountry Area
- overlays: Inventoried Roadless Area; Recommended Wilderness Area
- supporting plan evidence: Custer Gallatin ROD, FEIS Volume 1, FEIS Volume 2, Biological
  Assessment, and Biological Opinion

The current `forest_plan_component_eval_results.json` was parsed as existing generated evidence and
reports `passed=true` for `35` cases, `0` failed cases, all metric thresholds met, package-section
match rate `1.0`, plan-source citation correctness `1.0`, package-evidence citation correctness
`1.0`, and reviewer-resolution closure rate `1.0`. This pass did not rerun
`forest-plan-component-eval`.

## Go/Stop Decision

Go condition from the plan:

> The preflight can map the Plan Consistency Table to generated Forest Plan findings and applicable
> standards without relying on manual root-level prose.

Pass-4 decision: `go`.

Rationale:

- `EA-PACKAGE-042` exists once, is extracted, and is chunked as package evidence.
- Generated component findings own the component-level Forest Plan consistency baseline.
- Generated applicable-standard coverage owns the `58` standard inventory, the `12` applicable
  standards, and the `12/12` applied-standard result.
- Generated context summary owns the promoted Custer Gallatin profile context and remains
  reviewer-ready.
- Validation checks prove supported findings carry package evidence, plan-source evidence, and
  acceptable section bindings.
- No root-level East Crazies manual prose is needed to establish the Forest Plan consistency
  baseline.

## Stop Conditions Not Triggered

- Forest Plan consistency does not require hand-authored conclusions.
- No uncited standard is needed for the full report.
- The promoted Custer Gallatin profile remains the selected forest-plan profile.
- Manual root-level East Crazies prose remains non-canonical comparison material only.

## Next Preflight Pass

Begin pass 5: Authority Universe Boundary.

Pass 5 should confirm that applicable and non-applicable authorities are both first-class inputs:

- applicable authority rows come from generated compliance findings and applicable-authority
  artifacts;
- non-applicable authorities come from `non_applicable_authorities.json`,
  `search_coverage_certificates.json`, and `non_applicable_authority_appendix.md`;
- generated-rule-pack validation proves the compliance review used validated applicable
  authorities only;
- no report section may collapse the `340` non-applicable authorities into a generic disclaimer.
