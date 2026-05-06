# EA Consistency Decision Support Preflight Pass 2

Date: 2026-05-06

Scope: `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` workstream 2,
Artifact Freshness And Hash Baseline.

## Result

Status: `go` for pass 2 only.

This does not complete the full Sequence 0 preflight. The next preflight pass is current gate
replay.

## Boundary Checked

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- EA package:
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`
- Forest Plan consistency package record: `EA-PACKAGE-042`
- Source-set manifest hash:
  `c979c07b71257a42672c72d3bca7fdf2083b05f21446b5d5559b91124b82d22a`

The source-set manifest reports `source-set-ba8d0feae79501b8`, `190` source rows, `160`
artifacts, and workbook
`usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx`.

## Required Artifact Summary

All required pass-2 artifacts existed and parsed with the expected basic parser for their file type.

| Artifact | Type | Parse status | SHA-256 | Boundary or validation signal | Report input |
| --- | --- | --- | --- | --- | --- |
| `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json` | JSON | `json_ok` | `d02de0bc8b2357a733e9f8bb9c307fab3b086eca4e16656c6fa66f743c8c9bbc` | review/source-set/package match; `reviewer_ready=true`; `validated=true` | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.md` | Markdown | `text_ok` | `96e023ac330820e58ee5fa38da194466be906567a7c8d1b321073204d0e55a1e` | generated matrix rendering present | manifest, render comparison |
| `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.pdf` | PDF | `pdf_header_ok` | `31c47e3e0156c09a4798e7b404ab072114cdd4ed6076b9debc843b774d500c4a` | generated matrix PDF present | manifest, render comparison |
| `source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json` | JSON | `json_ok` | `ab6d5534cf57459d6d7b27750d53e72519ef46260e0bc4ffd5bf11e5957668ad` | review/source-set match; `33` authorities | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json` | JSON | `json_ok` | `ed47def14fee3158e6fba1cb8892c878aaecab82aeaa069a31931d2a2542199b` | review/source-set match; `340` authorities | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json` | JSON | `json_ok` | `639bd77243e48d9620ba7356bb5ca64be4de6c7a54e93de346ff04641d2ab68e` | review/source-set match; `340` certificates | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicability_validation.json` | JSON | `json_ok` | `d84d6b77adaa1fd9f86181aa8685f9545b63248ff07d7fcdc56616cdfc63bd56` | `passed=true`; `reviewer_ready=true`; `generated_rule_pack_ready=true` | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json` | JSON | `json_ok` | `c56d97d700e7fc8c27a95d4e5e93e14c26be3fb5edbf066b7c628cba60f53bb3` | review/source-set match; `33` generated rules | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack_validation.json` | JSON | `json_ok` | `8f5197fa14fb6a83b0556b8c0f27a93a2c89cebde6c27dbde4531dd344bface0` | `passed=true`; `generated_rule_pack_ready=true` | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json` | JSON | `json_ok` | `0ac3a2766446edab23806c666d9154f4c6f6e84b4e764f3cee677ac010d5d395` | review/source-set match; validation passed; `329` findings | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.md` | Markdown | `text_ok` | `f6150a286bf2d1a8282b8f6f36a1c67041741ea47d272d31f6724eed1ca87cfa` | generated component rendering present | manifest, render comparison |
| `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json` | JSON | `json_ok` | `bbd92f584f60b0a888cd779013f43acd82cd652f1e03fcf1d03003d756969145` | `passed=true`; `12/12` applicable standards applied | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json` | JSON | `json_ok` | `d8c1fbd04f0a019f9911a2d82e3c9d84f06b805e069a46cdb265319e1f81e178` | `scope_status=custer_gallatin`; `reviewer_ready=true`; `validation_passed=true` | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.md` | Markdown | `text_ok` | `d1ebb9043183e70fb1ad248bd9e2aeea509abfe990109737271df52c14dd46c5` | generated non-applicable appendix present | Markdown, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/authority_reviewer_resolution_report.json` | JSON | `json_ok` | `6fd76085ed4cabda4b64d86c8c541ca25c8ccccbb3f9539df663979eacf40b3a` | review/source-set match; `0` pending resolution items | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/litigation_risk_summary.json` | JSON | `json_ok` | `179714b0ad701586fc610b7c0cfad717df82664dc4b567aef5d917beee43b258` | review/source-set match; validation passed; `340` risk flags | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/package/package_manifest.jsonl` | JSONL | `jsonl_ok` | `d0176a5cf6c991e5a7e2356a71b30bb9ceef55fe90bd70dd1fb135118e0a1a81` | `43` package records; `EA-PACKAGE-042` present once | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/package/package_chunks.jsonl` | JSONL | `jsonl_ok` | `0d07dc16978652bc308c765299dfbfce1d50a0ca6a9d33f192c8c055cbd48b56` | `1,265` chunks; `312` chunks for `EA-PACKAGE-042` | JSON, manifest |
| `source_library/reviews/v1-cg-ecid-compliance-review/package/extracted_text/EA-PACKAGE-042_bebc890bc3da89c0.txt` | Text | `text_ok` | `07c688a0a68511ee652e9af22cbf39d03a7917d9365d1b18519efdf38e1a7564` | Plan Consistency Table extracted text present | JSON, manifest |

## Freshness Checks

The current file hashes matched the recorded validation hashes for these validation-owned inputs:

- `applicability_validation.hashes`: applicable authorities, non-applicable authorities, search
  coverage certificates, package manifest, and package chunks all matched current files.
- `generated_rule_pack.artifact_hashes`: applicability validation, applicable authorities,
  non-applicable authorities, search coverage certificates, package manifest, and package chunks all
  matched current files.
- `generated_rule_pack_validation.summary`: generated rule pack, expected generated rule pack,
  applicability validation, applicable authorities, non-applicable authorities, search coverage
  certificates, package manifest, and package chunks all matched current files.

No validation-owned hash mismatch was found.

## Count And Boundary Baseline

Pass 2 confirmed the artifact-level count and boundary baseline needed before gate replay:

- Compliance matrix rows: `33`
- Applicable authorities: `33`
- Non-applicable authorities: `340`
- Search coverage certificates: `340`
- Total applicability candidates recorded by validation: `373`
- Generated rules: `33`
- Forest Plan component findings: `329`
- Supported/applicable Forest Plan components: `79`
- Not-applicable Forest Plan components: `250`
- Custer Gallatin standards in source-set inventory: `58`
- Applicable Forest Plan standards: `12`
- Applied Forest Plan standards: `12`
- Authority reviewer-resolution pending items: `0`
- Forest Plan reviewer-resolution items: `0`

All JSON artifacts that record review/source-set identity agree on
`v1-cg-ecid-compliance-review` and `source-set-ba8d0feae79501b8`. The compliance matrix records the
expected package path:

```text
source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)
```

The package manifest and package chunks use the package-local source-set label
`ea-package-v1-cg-ecid-compliance-review`, which is expected for EA package extraction artifacts.

## Plan Consistency Table Hash Note

`EA-PACKAGE-042` is present once in `package_manifest.jsonl` as `Plan Consistency Table.pdf` with
`312` package chunks and extracted text path:

```text
source_library/reviews/v1-cg-ecid-compliance-review/package/extracted_text/EA-PACKAGE-042_bebc890bc3da89c0.txt
```

Two hash shapes are relevant:

- Raw extracted text file hash for the future decision-support manifest:
  `07c688a0a68511ee652e9af22cbf39d03a7917d9365d1b18519efdf38e1a7564`
- Package manifest `text_sha256`, matching normalized text without the trailing newline:
  `cbdd674285c2ea145fdcd3287b19877924f41dd6651d51d9125905af74f4118b`

Future stale-hash checks should compare each field against the matching hash shape.

## Commands Run

```bash
git status -sb
python -m json.tool source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json /tmp/ecid_compliance_matrix.validated.json
python -m json.tool source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json /tmp/ecid_applicable_authorities.validated.json
python -m json.tool source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json /tmp/ecid_non_applicable_authorities.validated.json
python -m json.tool source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json /tmp/ecid_forest_plan_component_findings.validated.json
```

Additional read-only Python inspections parsed all required JSON/JSONL/text/PDF inputs, computed
SHA-256 hashes, checked review/source-set/package fields, and compared validation-owned recorded
hashes against current files.

## Go/Stop Decision

Go condition from the plan:

> All required artifacts exist, parse cleanly, and agree on the review/source-set/package boundary.

Pass-2 decision: `go`.

Rationale:

- All required artifacts exist.
- JSON and JSONL inputs parsed cleanly.
- Markdown and extracted text inputs are nonempty UTF-8 text.
- The compliance matrix PDF has a valid PDF header and EOF marker.
- Validation-owned artifact hashes match current files.
- Review/source-set/package boundaries agree, with the expected package-local source-set label in
  package extraction artifacts.

## Stop Conditions Not Triggered

- No required artifact was missing.
- No required artifact was unparsable.
- No validation-owned hash mismatch was detected.
- No required artifact was tied to a different review, source set, or package boundary.

## Next Preflight Pass

Begin pass 3: current gate replay.

Pass 3 should run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

The pass should stop if the current proving review is not reviewer-ready, if phase eval no longer
passes `16/16`, or if promotion readiness fails for the current proving review.
