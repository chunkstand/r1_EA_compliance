# Evaluation Coverage Register

Updated: 2026-05-13

This register separates structural validation from direct-eval coverage.

Status meanings:

- `direct_eval_present`: tracked deterministic direct-eval cases exist and the aggregate gate is green.
- `direct_eval_strengthening_planned`: a direct-eval command exists, but broader contract depth or metrics are explicitly routed to a follow-on milestone.
- `direct_eval_missing`: no tracked direct-eval lane exists yet.

## Upstream Lanes

| Subsystem | Owner Surfaces | Structural Validation | Direct Eval Status | Direct Eval Command | Coverage Categories | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `preflight` | `src/usfs_r1_ea_sources/preflight.py` | `validation_report.json` | `direct_eval_present` | `upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream` | `challenge_page_http200`; `not_found_body_http200`; `duplicate_url_row_preservation` | Fixture-backed coverage proves tricky `200 OK` false positives and duplicate-row preservation separately from structural validation. |
| `validate_run` | `src/usfs_r1_ea_sources/validate_run.py` | `acceptance_gate.json` | `direct_eval_present` | `upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream` | `duplicate_content_canonical_link`; `url_override_provenance_drift` | Direct eval now distinguishes acceptance-gate coverage from simple unit-test truth. |
| `catalog_validation` | `src/usfs_r1_ea_sources/catalog.py` | `catalog_validation.json` | `direct_eval_present` | `upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream` | `batch_ledger_manifest_mismatch`; `catalog_partition_or_not_in_run_drift` | Aggregate fixture runs now make batch-ledger and merged-catalog drift visible without live corpus regeneration. |
| `extraction_accuracy` | `src/usfs_r1_ea_sources/extract.py`; `src/usfs_r1_ea_sources/extraction_accuracy.py` | `extraction_validation.json`; `diagnostics/extraction_accuracy_audit.json` | `direct_eval_present` | `upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream` | `ocr_heavy_pdf_extraction`; `table_dense_pdf_extraction`; `appendix_content_extraction`; `section_boundary_extraction` | The aggregate lane reuses the accuracy audit where it is the structural truth producer and adds tracked category markers plus controlled violations. |

## Downstream Lanes

| Subsystem | Owner Surfaces | Structural Validation | Direct Eval Status | Current Command | Coverage Categories | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `retrieval_eval` | `src/usfs_r1_ea_sources/retrieval.py`; `config/retrieval_eval_seed.json` | `retrieval_validation.json` | `direct_eval_present` | `retrieval-eval` | `hard_negative`; `multi_source`; `rank_quality_thresholds`; `false_positive_guard`; `missing_required_source_guard` | Governed by `config/downstream_direct_eval_v1.json`; the shipped contract floor is `12` cases with `3` hard negatives and `3` multi-source cases plus locked `recall@k`, `mrr`, `nDCG@k`, false-positive, and missing-required-source thresholds. |
| `claim_eval` | `src/usfs_r1_ea_sources/claim_extraction.py`; `config/claim_eval_seed.json` | `claim_validation.json` | `direct_eval_present` | `claim-eval` | `hard_negative`; `multi_source_or_type_confusion`; `rank_quality_thresholds`; `false_positive_guard`; `missing_required_source_guard` | Governed by `config/downstream_direct_eval_v1.json`; the shipped contract floor is `10` cases with `3` hard negatives and `3` multi-source-or-type-confusion cases plus locked `recall@k`, `mrr`, `nDCG@k`, false-positive, and missing-required-source thresholds. |
| `rule_claim_eval` | `src/usfs_r1_ea_sources/rule_claim_binding.py`; `config/rule_claim_link_eval_seed.json` | `rule_claim_link_validation.json` | `direct_eval_present` | `rule-claim-eval` | `hard_negative`; `multi_source`; `rank_quality_thresholds`; `false_positive_guard`; `missing_required_source_guard` | Governed by `config/downstream_direct_eval_v1.json`; the shipped contract floor is `20` cases with `4` hard negatives and `4` multi-source cases plus locked `recall@k`, `mrr`, `nDCG@k`, false-positive, and missing-required-source thresholds. |
| `compliance_review_eval` | `src/usfs_r1_ea_sources/compliance_review.py`; `config/compliance_review_eval_seed.json`; `config/compliance_rule_pack_coverage_nepa_ea_v0.json` | `compliance_validation.json`; `compliance_matrix.json`; `compliance_matrix.pdf`; `compliance_coverage_results.json` | `direct_eval_present` | `compliance-review-eval` | `all_authorities_control`; `unrelated_package_hard_negative`; `conditional_subset`; `unexpected_positive_guard`; `missing_required_source_rule_guard` | Governed by `config/downstream_direct_eval_v1.json`; the shipped contract floor is `5` cases with `1` all-authorities control, `2` unrelated-package hard negatives, and `2` conditional-subset cases. `compliance-coverage` is the supporting fail-closed rule-pack/seed/link alignment gate for this lane. |
