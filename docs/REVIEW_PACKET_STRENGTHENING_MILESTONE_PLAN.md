# Review Packet Strengthening And Matrix Row Completeness Milestone Plan

Date: 2026-05-08
Status: implemented; closeout verified on 2026-05-08

This milestone strengthens the East Crazy Inspiration Divide review packet so every applicable
authority and Forest Plan row is visible, traceable, and validated across the canonical review
artifacts. The immediate problem is not that the current V1 packet is failing. The current packet is
green. The gap is that the gates now protect selected first-class rows and aggregate counts, but do
not yet prove row-for-row that every applicable authority shown by intake and applicability is also
shown in the rendered compliance matrix and carried into the signer-facing review packet.

The milestone is scoped to `v1-cg-ecid-compliance-review` and source set
`source-set-ba8d0feae79501b8`. It uses the canonical review artifacts under
`source_library/reviews/v1-cg-ecid-compliance-review/` and does not rely on root-level
`East_Crazies_*` drafts.

## Goal

Produce a deterministic review-packet row ledger and gate contract that proves all applicable rows
are present in the compliance matrix and review packet.

Completion means:

- every applicable authority decision has exactly one first-class compliance matrix authority row;
- every generated compliance finding is represented in the matrix JSON and rendered matrix outputs;
- every applicable authority row is carried into decision support, final QA, and the signer-facing
  packet index;
- every applicable Forest Plan component row and every applicable Forest Plan standard remains
  visible as a distinct Forest Plan review surface;
- non-applicable authority coverage remains visible as a boundary artifact without being promoted
  into false compliance findings;
- land-exchange rows, including FLPMA Section 206, statutory, regulatory, and Forest Service
  policy/project-reference rows, remain first-class rows rather than narrative-only notes;
- phase evaluation and promotion checks fail closed if a row is missing from a required surface.

## Non-Goals

- Do not rerun downloader, catalog, source capture, or extraction workflows unless a baseline
  freshness check fails and a later sequence explicitly scopes that recovery.
- Do not broaden the claim beyond the East Crazy Inspiration Divide / Custer Gallatin proving
  review.
- Do not resolve South Plateau expansion blockers in this milestone.
- Do not stage ignored `source_library/` outputs unless repository policy changes.
- Do not turn the packet into legal advice, legal sufficiency certification, counsel approval, or a
  responsible-official decision.
- Do not collapse Forest Plan rows into the NEPA/authority matrix or authority rows into the Forest
  Plan matrix. They must stay distinct and cross-linked.
- Do not use root-level `East_Crazies_*` exports as current or canonical packet inputs.

## Current Baseline

The current promoted East Crazies packet has the right ingredients:

- review ID: `v1-cg-ecid-compliance-review`;
- source set: `source-set-ba8d0feae79501b8`;
- candidate authorities: `377`;
- applicable authorities: `37`;
- non-applicable authorities: `340`;
- compliance matrix authority rows: `37`;
- generated compliance findings: `37`, all `pass`;
- generated-pack rule-claim links: `162`;
- rule-claim gaps: `0`;
- Forest Plan component findings: `329`;
- Forest Plan applicable component rows carried into the matrix: `79`;
- Forest Plan applicable standards: `12/12`, all applied;
- review packet index validation: `30/30`;
- final QA validation: `196/196`;
- review-scoped phase eval: `21/21`;
- current-promotion suite: `31/31`, with South Plateau blockers kept expansion-only.

The latest gap-close added a fail-closed `required_applicable_authority_rows` contract for the four
current land-exchange rows:

- `flpma_section_206_land_exchange` from `R1EA-146`;
- `land_exchange_statutory_authorities` from `R1EA-137`;
- `land_exchange_regulatory_requirements` from `R1EA-124`;
- `land_exchange_fs_policy_and_project_references` from `R1EA-150`.

The implemented contract now covers the full applicable row universe, not just selected required
rows or aggregate counts.

## Closeout Evidence

The implemented artifact family is:

- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/review_packet_row_inventory.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/review_packet_row_inventory.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/compliance_matrix_render_manifest.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/review_packet_index.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/review_packet_index.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/review_packet_index.pdf`
- `source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/review_packet_index_validation.json`

Closeout replay:

- `review-packet-index`: passed, `30` checks, `0` failures.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `21/21`.
- `promotion-suite --manifest config/promotion_suite_v1.json`: current promotion passed `31/31`;
  South Plateau remains expansion-only with `forest_plan_reviewer_not_ready`.
- `final-qa-certification --validate-only`: passed `196/196`.

## Acceptance Criteria Alignment Matrix

| Acceptance criterion | Evidence artifact or gate | Closeout status |
| --- | --- | --- |
| Applicable authority row-set equality across applicability, generated rule pack, compliance review, compliance matrix, decision support, final QA, and packet index | `review_packet_row_inventory.json` `authority_row_comparisons`; `review_packet_index_validation.json` row-set checks | Met |
| Rendered matrix completeness for every authority and Forest Plan matrix row | `compliance_matrix_render_manifest.json`; deterministic Markdown row markers; `%PDF-` matrix header check | Met |
| Land-exchange first-class status for FLPMA Section 206, statutory, regulatory, and Forest Service policy/project-reference rows | `review_packet_row_inventory.json` and `review_packet_index.json` dedicated `land_exchange_rows`; `land_exchange_rows_first_class_in_packet_index` validation check | Met |
| Forest Plan first-class status for applicable component rows and applicable standards | `forest_plan_component_rows`, `applicable_forest_plan_standard_rows`, and render-manifest Forest Plan row-set checks | Met |
| Non-applicable boundary remains summarized and coverage-backed without becoming findings | `non_applicable_authority_boundary` and `non_applicable_boundary_present` validation check | Met |
| Canonical artifact boundary excludes root-level `East_Crazies_*` drafts | `non_canonical_root_drafts_not_referenced` validation check and packet quarantine statement | Met |
| Promotion readiness remains green while South Plateau blockers stay typed and separate | `phase-eval` `21/21`, current `promotion-suite` `31/31`, expansion blocker category `forest_plan_reviewer_not_ready` | Met |

## Gap To Close

The packet needs a row-level completeness contract across artifacts:

1. Applicability can identify `37` applicable authority rows, but the gate should prove the exact
   row IDs match the compliance matrix rows, not only the count.
2. The compliance matrix JSON has `37` authority rows, but rendered Markdown/PDF proof should be
   represented by a deterministic render manifest or equivalent row marker contract.
3. Decision support and final QA validate required counts and selected row contracts, but they
   should validate a complete row ledger for every applicable authority row.
4. Forest Plan rows should remain first-class review rows, with all `79` applicable component rows
   and all `12` applicable standards visible through the packet index.
5. The non-applicable boundary should stay reviewable: `340` non-applicable authorities should be
   summarized and linked to the non-applicable authority appendix and search coverage artifacts.
6. Reviewers need a single signer-facing index showing what is in the packet, where each row appears,
   what artifact proves it, and which residual risks or implementation confirmations remain.

## Target Artifact Family

Add a generated packet-strengthening artifact family under:

```text
source_library/reviews/<review_id>/review_packet_index/
```

Required generated outputs:

- `review_packet_row_inventory.json`
- `review_packet_row_inventory.md`
- `compliance_matrix_render_manifest.json`
- `review_packet_index.json`
- `review_packet_index.md`
- `review_packet_index.pdf`
- `review_packet_index_validation.json`

The JSON files are the machine-readable contracts. Markdown and PDF are reviewer-facing renderings
from those JSON contracts. The validation sidecar records row-set comparisons, artifact hashes,
schema versions, and fail-closed checks.

## Row Ledger Contract

Each row ledger entry should carry enough selectors to connect back to the canonical review:

- `row_ledger_id`
- `row_class`: `applicable_authority`, `non_applicable_authority_boundary`,
  `forest_plan_component`, `forest_plan_standard`, `implementation_confirmation`, or
  `residual_risk`
- `rule_id` or Forest Plan component ID where applicable
- `candidate_authority_id` and applicability `decision_id` where applicable
- source record IDs and authority family IDs
- compliance status and applicability status
- EA/package evidence selectors
- source-library evidence selectors and source-claim IDs
- canonical artifact paths and JSON selectors
- rendered Markdown anchor or table-row marker
- PDF/render manifest marker
- final QA and decision-support selectors
- validation status and fail-closed reason when any selector is missing

The row ledger is not a new source of legal truth. It is an index over existing audited artifacts.

## Sequence 0: Baseline Row Inventory And Drift Audit

Goal:
Prove the current review packet has a stable row universe before changing renderers or gates.

Implementation scope:

- Add a read-only row inventory builder for the East Crazies review artifacts.
- Compare row IDs and source selectors across:
  - `applicability/applicable_authorities.json`;
  - `applicability/generated_rule_pack.json`;
  - `compliance_review.json`;
  - `compliance_matrix.json`;
  - `decision_support/ea_consistency_decision_support.json`;
  - `final_qa/east_crazies_final_qa_certification.json`;
  - `forest_plan_component_findings.json`;
  - `forest_plan_applicable_standard_coverage.json`;
  - `non_applicable_authority_appendix.json`.
- Emit `review_packet_row_inventory.json` and `.md`.
- Record the exact baseline row counts and row-set hashes.

Acceptance criteria:

- The inventory proves `37` applicable authority rows and `37` compliance matrix authority rows
  with no missing, duplicate, or extra applicable authority rows.
- The inventory proves the four land-exchange rows are present with expected source records.
- The inventory proves `79` applicable Forest Plan component rows and `12` applicable Forest Plan
  standards are visible as Forest Plan rows, not authority rows.
- The inventory proves `340` non-applicable authorities remain represented through boundary
  artifacts and coverage selectors.
- Any row drift blocks later sequences until the drift is explained.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_ea_consistency_decision_support.py tests/test_final_qa_certification.py
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
git diff --check
```

Commit policy:
Commit Sequence 0 as a focused inventory-builder, tests, docs, and handoff commit.

## Sequence 1: Compliance Matrix Render Manifest

Goal:
Make rendered matrix completeness a first-class artifact, not an inferred property of the Markdown
or PDF body text.

Implementation scope:

- Extend the compliance matrix renderer to emit `compliance_matrix_render_manifest.json`.
- Include one manifest entry for every authority matrix row and every Forest Plan matrix row.
- Record row order, section, table identity, Markdown anchor or deterministic row marker, PDF output
  identity, source selectors, and row hash.
- Validate the manifest against `compliance_matrix.json`.
- Keep Markdown and PDF generated from the canonical matrix JSON; do not make the render manifest a
  separate source of row content.

Acceptance criteria:

- Every applicable authority row in `compliance_matrix.json` has a render manifest entry.
- Every Forest Plan row in `compliance_matrix.json.forest_plan_compliance.rows` has a render
  manifest entry.
- Markdown rendering exposes deterministic row markers or anchors for all manifest rows.
- PDF validity remains checked by `%PDF-` header and render-manifest freshness, avoiding brittle
  full-PDF text assertions.
- Removing one applicable authority row from the matrix or manifest causes validation failure.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
git diff --check
```

Commit policy:
Commit Sequence 1 as a focused compliance-matrix renderer and validation contract commit.

## Sequence 2: Signer-Facing Review Packet Index

Goal:
Generate one reviewer-order index that shows what the packet contains and where each row is proven.

Implementation scope:

- Add a `review-packet-index` generator or integrate the index into the existing final-QA generator
  if that is cleaner with the current architecture.
- Generate JSON, Markdown, PDF, and validation sidecar files under `review_packet_index/`.
- Include these sections:
  1. review boundary and canonical artifact inventory;
  2. all applicable authority rows;
  3. all land-exchange rows as first-class rows;
  4. non-applicable authority boundary summary and appendix selectors;
  5. Forest Plan applicable component rows;
  6. Forest Plan applicable standards;
  7. implementation-confirmation checklist;
  8. residual risk register;
  9. validation and replay commands;
  10. root-level draft quarantine statement.

Acceptance criteria:

- The index carries all `37` applicable authority rows.
- The index carries the `340` non-applicable authority boundary as a summary plus artifact links,
  without converting non-applicable authorities into findings.
- The index carries all `79` applicable Forest Plan component rows and the `12` applicable standards
  as distinct Forest Plan artifacts.
- Every row links back to a canonical JSON selector and a rendered matrix or packet marker.
- The PDF is generated and valid.
- No index input path points to a root-level `East_Crazies_*` draft.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_ea_consistency_decision_support.py tests/test_final_qa_certification.py
PYTHONPATH=src python -m usfs_r1_ea_sources review-packet-index --output-dir source_library --review-id v1-cg-ecid-compliance-review
git diff --check
```

Commit policy:
Commit Sequence 2 as a focused packet-index generator, schema, tests, docs, and handoff commit.

## Sequence 3: Decision Support And Final QA Gate Integration

Goal:
Make the row ledger and packet index mandatory for decision-support and final-QA readiness.

Implementation scope:

- Add row-ledger and render-manifest inputs to decision-support validation.
- Add row-ledger, render-manifest, and packet-index inputs to final-QA validation.
- Extend expected-summary fixtures to pin row-set hashes and required row counts.
- Add fail-closed categories such as:
  - `missing_applicable_authority_row`;
  - `missing_matrix_render_row`;
  - `missing_packet_index_row`;
  - `missing_forest_plan_row`;
  - `missing_non_applicable_boundary`;
  - `non_canonical_draft_dependency`.

Acceptance criteria:

- Decision-support validation fails if any applicable authority row is absent from the matrix,
  render manifest, or packet index.
- Final-QA validation fails if the row ledger, render manifest, or packet index is missing, stale,
  hash-mismatched, or incomplete.
- Existing land-exchange required-row checks remain present and become a subset of the full row-set
  contract.
- Fixture tests prove a deliberately missing row produces the expected fail-closed category.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_ea_consistency_decision_support.py tests/test_final_qa_certification.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review --validate-only
git diff --check
```

Commit policy:
Commit Sequence 3 as a focused gate-integration and fixture commit.

## Sequence 4: Phase Evaluation, Promotion, And Packet Closeout

Goal:
Make row completeness part of the outer reviewer-ready signal.

Implementation scope:

- Add a `review_packet_index` or `matrix_row_completeness` phase to review-scoped `phase-eval`, or
  extend the existing compliance/final-QA phase if that preserves a cleaner phase model.
- Add packet-index and render-manifest artifacts to `config/promotion_suite_v1.json` for the
  current East Crazies promotion lane.
- Regenerate the ignored canonical artifacts in the correct dependency order:
  1. compliance review and matrix render manifest;
  2. review packet row inventory;
  3. review packet index;
  4. decision-support packet;
  5. final-QA packet;
  6. phase-eval results;
  7. promotion-suite results;
  8. final-QA validate-only replay.
- Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/OUTPUT_SCHEMAS.md`, and
  `docs/SESSION_HANDOFF.md` where the implemented behavior changes those contracts.

Acceptance criteria:

- `phase-eval` passes with the new packet-row completeness gate included.
- Promotion remains current-ready and keeps South Plateau expansion blockers separate.
- The final-QA validate-only replay passes after phase and promotion outputs are refreshed.
- The tracked docs describe the new packet-row completeness contract and current replay state.
- Ignored generated outputs remain unstaged unless repository policy changes.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --manifest config/promotion_suite_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review --validate-only
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_ea_consistency_decision_support.py tests/test_final_qa_certification.py tests/test_promotion_suite.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit Sequence 4 as the closeout commit with implementation, tests, updated docs, and session
handoff. Push only if the user asks for publish.

## Overall Acceptance Standard

The milestone is complete only when the canonical packet can prove all of the following:

- Applicable authority row set equality:
  `applicable_authorities` equals generated rule pack applicable rows equals compliance review
  findings equals compliance matrix authority rows equals decision-support authority rows equals
  final-QA finding rows equals packet-index applicable-authority rows.
- Rendered matrix completeness:
  every compliance matrix authority row and Forest Plan row has a deterministic render manifest
  entry tied to Markdown/PDF output.
- Land-exchange first-class status:
  all four current land-exchange rows remain explicitly present and validated.
- Forest Plan first-class status:
  all applicable Forest Plan component rows and standards remain visible and separately reviewed.
- Non-applicable boundary:
  all non-applicable authorities remain summarized, linked, and coverage-backed without being
  inflated into compliance findings.
- Canonical artifact boundary:
  no validation path depends on root-level `East_Crazies_*` drafts.
- Promotion readiness:
  current East Crazies promotion remains green, while South Plateau expansion blockers remain typed
  and separate.

## Residual Risks

- PDF row-level proof can be brittle if asserted through extracted PDF text. Prefer renderer-owned
  manifest entries plus basic PDF validity checks.
- Hash cascades are expected. Compliance matrix changes will refresh decision-support, final-QA,
  phase-eval, and promotion-suite hashes.
- The packet index must remain an index over audited artifacts, not a second reviewer engine with
  independent legal conclusions.
- Row identity must use stable review selectors, not rendered row order alone.
- The `37`/`340`/`79`/`12` baseline counts may drift after deliberate source or rule changes. Drift
  is acceptable only when a sequence documents and verifies the new row universe.
