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

| Subsystem | Owner Surfaces | Structural Validation | Direct Eval Status | Current Command | Notes |
| --- | --- | --- | --- | --- | --- |
| `retrieval_eval` | `src/usfs_r1_ea_sources/retrieval.py` | `retrieval_validation.json` | `direct_eval_strengthening_planned` | `retrieval-eval` | Existing direct eval exists, but contract breadth is routed to `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`. |
| `claim_eval` | `src/usfs_r1_ea_sources/claim_extraction.py` | `claim_validation.json` | `direct_eval_strengthening_planned` | `claim-eval` | Existing direct eval exists, but the next milestone expands hard negatives and broader recall/precision coverage. |
| `rule_claim_eval` | `src/usfs_r1_ea_sources/rule_claim_binding.py` | `rule_claim_link_validation.json` | `direct_eval_strengthening_planned` | `rule-claim-eval` | Existing direct eval exists, but breadth and false-positive coverage remain a follow-on milestone. |
| `compliance_review_eval` | `src/usfs_r1_ea_sources/compliance_review.py` | `compliance_validation.json`; `compliance_matrix.json`; `compliance_matrix.pdf` | `direct_eval_strengthening_planned` | `compliance-review-eval` | Existing direct eval exists, but wider seeded coverage remains routed after the upstream closeout. |
