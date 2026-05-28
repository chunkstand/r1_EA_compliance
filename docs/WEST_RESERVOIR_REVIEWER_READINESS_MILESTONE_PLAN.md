# West Reservoir Reviewer Readiness Milestone Plan

Date: 2026-05-28
Status: Active parent packet; Milestone 0 resolved locally; Milestone 1
reduced by Flathead authority-universe scoping and source-evidence
feasibility; source-set migration is resolved through
`docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`, where Milestone
1 contract migration moved the tracked West Reservoir contract to
`source-set-f70ea11e04ae3d53` and Milestone 2 resolved the f70
authority-universe proof; parent Milestone 1 f70 applicability is now green,
the f70 forest-plan identity/source-capture child packet is resolved, and
`forest-plan-resolve` now emits current Flathead context/component artifacts
with `forest_plan_context_validation.json` passing on f70. The active parent
stop is Milestone 2 component readiness.
Owner context: Flathead forest-specific example follow-on after West Reservoir
public Pinyon package authority verification

## Purpose

Make `west-reservoir-67436` a reviewer-ready Flathead National Forest example
on the current governed replay contract without reusing stale historical green
artifacts.

The package-authority slice is already resolved: the official Flathead project
page and linked public Pinyon/Box folder have been verified against the local
review package manifest, with `12` official PDFs, `12` local package rows,
byte-size and SHA-256 matches for every document, and
`omitted_document_count=0`.

This plan starts after that provenance proof. It closes only the remaining
reviewer-readiness gap: rebuilding the current review/component/compliance
artifact spine on `source-set-f70ea11e04ae3d53`, proving the Flathead forest
plan component contract, and promoting the governed West Reservoir slot only
after the current eval gates pass.

## Intent Lock

West Reservoir is the selected Flathead governed example package. The intent is
to move the existing Flathead row from `typed_blocked_example_available` to a
reviewer-ready Flathead example after current evidence proves it.

This plan is not a source-set migration plan. The original West Reservoir
readiness contract stayed on `source-set-4fb59e9eb43045cb` until the separate
migration packet proved the all-or-nothing move. The current active contract
is now `source-set-f70ea11e04ae3d53` across replay context, V1 eval contract,
component eval contract, component coverage, and replay catalog surface. If
that migrated source set cannot support reviewer readiness, stop in the
migration or blocker packet instead of silently borrowing another source set.

This plan is also not a package-authority plan. Package authority is already
verified. Readiness work must preserve that proof while rebuilding missing
review artifacts.

## Bitter Lesson Alignment Lock

This packet follows Sutton's Bitter Lesson by making reviewer readiness depend
on general, repeatable evidence-processing loops rather than hand-authored
West Reservoir exceptions. A green closeout must come from source-set coverage,
catalog-backed retrieval, generated rule-pack validation, component eval,
compliance review, V1 eval, phase eval, and aggregate coverage gates.

Domain knowledge belongs in tracked data and artifacts:

- official package-authority verification and package manifest rows;
- replay context, forest profile, rule-pack, reconciliation, adjudication, and
  eval manifest files under `config/`;
- catalog/source-set records and generated review artifacts under
  `source_library/`; and
- current routing, current-system-state, and session handoff docs.

Implementation must not add hidden runtime branches, special-case legal
conclusions, deleted authority requirements, relaxed thresholds, or
West-Reservoir-only shortcuts to get a reviewer-ready result. If a gate fails,
the first repair path is to improve or truthfully reroute source evidence,
retrieval coverage, generated artifacts, adjudication data, eval fixtures, or
failure telemetry. Any unavoidable narrow rule must be explicit, versioned,
test-covered, visible in outputs, and owned by a tracked config or contract.

The active 4fb source-evidence blocker is therefore aligned only while it stays
fail-closed: either prove a governed same-source-set repair from catalog
evidence, or open a source-set migration packet that updates every West
Reservoir contract together. Borrowing a newer catalog, editing thresholds, or
promoting from stale green artifacts is disallowed because it replaces scalable
evidence and eval loops with local intuition.

The source-evidence blocker feasibility slice reduced the 4fb option: the
failing snapshot required `59` unique source-record IDs, `49` mapped current
rows were absent from active 4fb and present only in the later f70
current-source-gap closeout catalog. The dedicated source-set migration packet
has now resolved contract parity and the authority universe on one selected
source set, so parent work can resume on f70 without borrowing a different
catalog.

Migration packet Milestone 0 added the tracked parity gate:
`tests/test_west_reservoir_source_set_migration.py` verifies replay context,
V1 eval, component eval, and component coverage source-set IDs agree, includes
a controlled mixed-source-set case, and preserves typed-blocked status while
the parent readiness gates remain red.

Migration packet Milestone 1 then moved the tracked contract to
`source-set-f70ea11e04ae3d53` and pointed the replay context catalog surface at
the f70 current-source-gap closeout catalog. Migration packet Milestone 2
added Flathead to the f70 forest-plan component inventory batch, rebuilt that
inventory, and reran the selected f70 authority universe. The gate now reports
`passed=true`, `validation_passed=true`, `candidate_authority_count=146`,
`forest_plan_component_candidate_count=80`, and the component-inventory check
is green with `component_inventory_present=true`,
`component_inventory_count=80`, and
`selected_component_forest_unit_ids=["flathead-nf"]`.

## Current Evidence

- Current replay context:
  `config/replay_contexts/west-reservoir-67436.json`
- Current review ID:
  `west-reservoir-67436`
- Current source-set contract:
  `source-set-f70ea11e04ae3d53`
- Current forest identity:
  `flathead-nf`
- Official project page:
  `https://www.fs.usda.gov/r01/flathead/projects/67436`
- Official Pinyon/Box folder:
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/299363475796`
- Package-authority verification:
  `config/review_package_authority_verifications/west-reservoir-67436.json`
- Current V1 eval contract:
  `config/v1_west_reservoir_real_ea_eval.json`
- Current component eval contract:
  `config/forest_plan_component_evals/west-reservoir-67436.json`
- Current real-package coverage slot:
  `slot_id="west-reservoir-typed-blocked"`,
  `coverage_class_id="alternate_package_typed_blocked"`, and
  `expected_contract_status="typed_blocked"` in
  `config/v1_real_package_review_coverage_v1.json`.
- Current forest-specific registry example:
  `example_id="flathead-west-reservoir-typed-blocked"`,
  `coverage_slot_id="west-reservoir-typed-blocked"`,
  `forest_unit_id="flathead-nf"`, and
  `expected_contract_status="typed_blocked"` in
  `config/forest_specific_example_package_registry_v1.json`.
- Current Flathead forest-routing row:
  `routing_status="typed_blocked_example_available"` and
  `primary_example_id="flathead-west-reservoir-typed-blocked"`.
- Current component coverage slot:
  `slot_id="west-reservoir-flathead-review"` with
  `expected_source_set_id="source-set-f70ea11e04ae3d53"` in
  `config/forest_plan_component_eval_coverage_v1.json`.
- Pre-migration V1 eval result:
  `source_library/reviews/west-reservoir-67436/v1_ea_eval_results.json`
  reports `contract_status="typed_blocked"`,
  `actual_overall_passed=false`, `broader_ea_passed=false`, and
  `forest_plan_passed=false`.
- Current generated forest-plan artifacts now include:
  `forest_plan_context_summary.json`, `forest_plan_context.json`,
  `forest_plan_context_validation.json`,
  `forest_plan_component_findings.json`,
  `forest_plan_applicable_standard_coverage.json`, and
  `forest_plan_reviewer_resolution_queue.json` on
  `source-set-f70ea11e04ae3d53`. Context validation now passes, but these are
  not reviewer-ready proof yet: current component evaluation is not
  reviewer-ready, and the component adjudication eval is still stale from
  historical `source-set-5e65d845ce77e1a0`.
- Current missing downstream artifacts still include:
  `compliance_review.json`, `compliance_matrix.json`,
  `compliance_validation.json`, and `authority_explanation_paths.json`.
- Pre-migration component eval result:
  `source_library/reviews/west-reservoir-67436/forest_plan_component_eval_results.json`
  is aligned to `source-set-4fb59e9eb43045cb` but fails `0/27` cases.
- Pre-migration component failure categories include missing component findings,
  applicability/status mismatches, citation mismatches, reviewer-resolution
  mismatches, and `20` standard coverage gaps.
- Historical artifact warning:
  `source_library/reviews/west-reservoir-67436/phase_eval_results.json`
  currently reports a green historical run on
  `source-set-5e65d845ce77e1a0`. That artifact is not current readiness proof
  for this packet.

## Pre-Migration Blocker Map

Pre-migration V1 eval blockers on `source-set-4fb59e9eb43045cb`:

- `review_artifact_missing`: `8`
- `forest_plan_matrix_miss`: `1`
- `forest_plan_reviewer_not_ready`: `1`
- `forest_plan_scope_miss`: `1`
- broader-EA lane blockers:
  `review_artifact_missing=4`
- forest-plan lane blockers:
  `review_artifact_missing=4`, `forest_plan_matrix_miss=1`,
  `forest_plan_reviewer_not_ready=1`, and `forest_plan_scope_miss=1`

Pre-migration component eval blockers on `source-set-4fb59e9eb43045cb`:

- `component_finding_missing`: `27`
- `component_applicability_mismatch`: `27`
- `component_type_mismatch`: `27`
- `compliance_status_mismatch`: `27`
- `plan_source_citation_mismatch`: `27`
- `standard_coverage_missing`: `20`
- `reviewer_resolution_state_mismatch`: `16`
- `applicable_standard_mismatch`: `14`
- `package_evidence_citation_mismatch`: `5`
- `package_section_mismatch`: `5`

This blocker map makes the implementation intent explicit: do not solve West
Reservoir by editing thresholds first. Solve it by regenerating and, where
needed, evidence-adjudicating the missing current review artifacts until these
counts naturally fall to zero under the existing contracts.

## Goal

Close the West Reservoir Flathead reviewer-readiness lane so the current
governed review passes on `source-set-f70ea11e04ae3d53` with:

- package authority still verified against the public Flathead/Pinyon source;
- current review identity and source-set identity present in generated review
  artifacts;
- Flathead forest-plan scope resolved as `flathead_nf`;
- applicability validation and generated rule-pack validation green;
- component findings, standard coverage, and reviewer-resolution queue current;
- `forest-plan-component-eval --review-id west-reservoir-67436` passing all
  `27/27` current cases;
- compliance review, compliance matrix, and validation artifacts present and
  reviewer-ready;
- `v1-ea-eval --review-id west-reservoir-67436` passing as
  `contract_status="reviewer_ready"`;
- review-bound `phase-eval --review-id west-reservoir-67436` passing on
  `source-set-f70ea11e04ae3d53`;
- governed registry and coverage manifests updated only after those proofs are
  current.

## Non-Goals

- Do not change the official package authority or add unverified project
  documents.
- Do not stage ignored `source_library/` generated artifacts.
- Do not reuse the old green `source-set-5e65d845ce77e1a0` phase-eval result
  as current readiness proof.
- Do not mark West Reservoir reviewer-ready in registry or coverage manifests
  before current V1, component, compliance, and phase evals pass.
- Do not weaken tests, lower thresholds, add skips, or relax eval manifests to
  get green. Replacement coverage must be equivalent or stronger, and coverage
  did not get easier.
- Do not claim aggregate forest-plan component coverage is green while ECID
  source-delta remains red.
- Do not reopen unrelated Custer Gallatin, Lolo, South Otter, South Plateau,
  or ECID packets except where aggregate commands must report their unchanged
  residual status.
- Do not make legal conclusions beyond deterministic citation-bearing review
  artifacts and eval gates.

## Scope

- West Reservoir replay identity, package path, package manifest, and package
  authority verification
- Flathead forest-plan profile resolution for this review
- West Reservoir applicability, generated rule-pack, forest-plan context,
  forest-plan component, compliance, V1 eval, and phase-eval artifacts
- Tracked adjudication and eval contracts needed to make the review replayable
- Registry and aggregate coverage promotion after current readiness gates pass
- Current routing, current-system-state, and session handoff docs

## Out Of Scope

- New workbook source-row capture or full-register source-set rebuilds
- Broad downloader, extraction, catalog, graph, or review-engine refactors
- New Flathead example selection beyond `west-reservoir-67436`
- South Plateau requalification
- ECID source-delta repair, except for preserving truthful aggregate failure
  language after the West Reservoir slot is repaired

## Owner Surfaces

- Plan packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Current route and state:
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
- Replay context:
  `config/replay_contexts/west-reservoir-67436.json`
- Package authority:
  `config/review_package_authority_verifications/west-reservoir-67436.json`,
  `tests/test_west_reservoir_package_authority.py`
- V1 eval contract:
  `config/v1_west_reservoir_real_ea_eval.json`
- Component eval contract:
  `config/forest_plan_component_evals/west-reservoir-67436.json`
- Region 1 component inventory manifest:
  `config/r1_forest_plan_component_inventory_build_manifest.json`
- Applicability adjudication:
  `config/applicability_adjudications/west-reservoir-67436.json`
- Forest-plan component adjudication:
  `config/forest_plan_component_adjudications/west-reservoir-67436.json`
- Aggregate manifests:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- Ignored generated review outputs:
  `source_library/reviews/west-reservoir-67436/`
- Focused tests:
  `tests/test_replay_context.py`,
  `tests/test_west_reservoir_package_authority.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_forest_specific_example_package_registry.py`,
  `tests/test_forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_compliance_review.py`,
  `tests/test_cli_eval.py`

## Placement Rules

- Keep `review_id="west-reservoir-67436"` stable across replay context,
  generated artifacts, eval contracts, registry rows, and coverage slots.
- Keep `forest_unit_id="flathead-nf"` and forest-plan scope
  `flathead_nf`.
- Keep the current source-set identity
  `source-set-f70ea11e04ae3d53` in every readiness proof for this packet.
- Treat `source-set-5e65d845ce77e1a0` artifacts as historical only.
- Keep package bytes and generated review outputs under ignored
  `source_library/`; track only deterministic contracts, adjudications,
  manifests, tests, and docs.
- Use source-record IDs and citations from the Flathead forest-plan profile.
  Any remaining Custer Gallatin source-record reference in a West Reservoir
  contract is a bug to prove and repair, not a tolerated mismatch.
- Preserve one review package; do not add substitute documents or hidden local
  package paths.

## Required Implementation Artifacts

The implementation is not ready to promote until the current review directory
contains fresh artifacts for:

- `review_report.json`
- `applicability/applicability_validation.json`
- `applicability/generated_rule_pack.json`
- `applicability/generated_rule_pack_validation.json`
- `forest_plan_context.json`
- `forest_plan_context_summary.json`
- `forest_plan_component_findings.json`
- `forest_plan_applicable_standard_coverage.json`
- `forest_plan_reviewer_resolution_queue.json`
- `forest_plan_component_adjudication_eval.json`
- `forest_plan_component_eval_results.json`
- `compliance_review.json`
- `compliance_matrix.json`
- `compliance_matrix.md`
- `compliance_matrix.pdf`
- `compliance_validation.json`
- `authority_explanation_paths.json`
- `review_packet_index/review_packet_index.json` when required by phase eval
- `review_packet_index/review_packet_index_validation.json` when required by
  phase eval
- `v1_ea_eval_results.json`
- `phase_eval_results.json`

## Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| A stale green `phase_eval_results.json` on `source-set-5e65d845ce77e1a0` could be treated as current reviewer readiness. | `source_library/reviews/west-reservoir-67436/phase_eval_results.json`, `config/replay_contexts/west-reservoir-67436.json`, `docs/CURRENT_SYSTEM_STATE.md` | Current `phase-eval --review-id west-reservoir-67436` must report `source_set_id="source-set-f70ea11e04ae3d53"` and `passed=true`. | Any readiness claim with `source_set_id!="source-set-f70ea11e04ae3d53"` fails the milestone. | Preserve or add a negative test/result check that a `5e65...` phase artifact cannot satisfy the West Reservoir current contract. | Future Codex sees a green historical phase file and flips registry status without rerunning the current review. |
| Package-authority proof could be lost while rebuilding review artifacts. | `config/review_package_authority_verifications/west-reservoir-67436.json`, package manifest, `tests/test_west_reservoir_package_authority.py` | Package-authority test passes and manifest still has `12` verified official PDFs with `omitted_document_count=0`. | Missing, extra, or hash-mismatched package rows fail the milestone. | Corrupt one expected hash in a fixture or test copy and ensure the authority test fails. | Future Codex swaps in a local downloads folder and bypasses the official public Pinyon evidence. |
| Flathead scope could drift into Custer Gallatin source-record identity. | `config/v1_west_reservoir_real_ea_eval.json`, `config/forest_plan_profiles.json`, generated context artifacts | `forest-plan-resolve` and `v1-ea-eval` must prove `forest_unit_id="flathead-nf"` and `scope_status="flathead_nf"` with Flathead plan source citations. | Any Custer Gallatin forest-plan source record in current West Reservoir forest-plan expectations fails the milestone. | Keep a regression assertion around the known risk that `region1_forest_plan_source_records_authority_template` must not cite `R1PLAN-custer-gallatin-nf-02` for West Reservoir. | Future Codex copies a Custer Gallatin contract row because another example was recently green. |
| Component eval could be made green by lowering the case set or thresholds. | `config/forest_plan_component_evals/west-reservoir-67436.json`, `tests/test_forest_plan_component_eval.py` | `forest-plan-component-eval --review-id west-reservoir-67436` passes all `27/27` cases with existing or stronger thresholds. | Any case deletion, lower minimum, or relaxed threshold without stronger replacement coverage fails the milestone. | Remove one required applicable-standard case in a test fixture and ensure coverage/eval fails. | Future Codex marks readiness by editing the eval manifest instead of producing component findings. |
| Reviewer-resolution queue could hide open component decisions. | `forest_plan_reviewer_resolution_queue.json`, component adjudication config and eval | Component adjudication eval reports `reviewer_ready=true`, `pending=0`, and V1 forest-plan reviewer-resolution limits remain `0`. | Any open queue item or reviewer-resolution item above `0` fails the milestone. | Seed one unresolved queue item and verify `forest-plan-component-adjudication-eval` fails. | Future Codex treats unresolved reviewer judgment as an automatic pass. |
| Compliance review could pass in base-pack or diagnostic mode rather than generated-pack mode. | `compliance_review.json`, `compliance_validation.json`, generated rule pack | `compliance-review` uses the generated West Reservoir rule pack and reports `reviewer_ready=true` plus `validation_passed=true`. | Missing generated rule pack, `allow-base-rule-pack-review` reliance, or validation failure fails the milestone. | Run a validate-only generated-rule-pack check with a missing rule and ensure compliance validation blocks readiness. | Future Codex reruns compliance with broad base rules and claims the review is ready. |
| Compliance matrix output could be incomplete even when JSON exists. | `compliance_matrix.json`, `compliance_matrix.md`, `compliance_matrix.pdf`, `review_packet_index` outputs | `phase-eval --review-id west-reservoir-67436` must pass after matrix generation, and the PDF must exist as a non-empty valid PDF. | Missing MD/PDF, zero-byte PDF, invalid PDF header, or phase-eval matrix artifact failure fails the milestone. | Delete or corrupt the generated PDF in a fixture or local dry run and verify phase-eval fails. | Future Codex checks only `compliance_review.json` and misses the signer-facing matrix artifact. |
| Aggregate component coverage could still be red and described as green. | `config/forest_plan_component_eval_coverage_v1.json`, aggregate results | West Reservoir slot must pass and source-set align; aggregate text must still name any remaining ECID source-delta red status. | Any doc claiming aggregate component coverage is green while ECID remains red fails closeout. | Preserve a result fixture or doc check where ECID red keeps aggregate `passed=false` after West Reservoir improves. | Future Codex fixes West Reservoir and overstates aggregate readiness. |

## Promotion Decision Rules

Promotion is a separate decision from artifact rebuild.

Before promotion, the manifests must continue to say:

- `config/v1_real_package_review_coverage_v1.json`:
  `expected_contract_status="typed_blocked"` for
  `review_id="west-reservoir-67436"`;
- `config/forest_specific_example_package_registry_v1.json`:
  `routing_status="typed_blocked_example_available"` for `flathead-nf`;
- `config/forest_plan_component_eval_coverage_v1.json`:
  West Reservoir component slot remains required but failing until the current
  component result passes.

After promotion, all manifest language must agree:

- West Reservoir's real-package slot must expect
  `contract_status="reviewer_ready"`.
- West Reservoir must count as a `forest_specific_reviewer_ready` example, not
  an `alternate_package_typed_blocked` example.
- The Flathead forest-routing row must change from
  `typed_blocked_example_available` to `real_package_examples_available`.
- Labels, notes, example IDs, slot IDs, coverage classes, thresholds, and tests
  must no longer describe the active West Reservoir example as typed blocked.
- If a stable ID is renamed away from `flathead-west-reservoir-typed-blocked`
  or `west-reservoir-typed-blocked`, every manifest reference and focused test
  must be updated in the same commit. Do not leave orphaned IDs or mixed
  typed-blocked/reviewer-ready language.

## Per-Milestone Closeout Rules

Each milestone can be implemented as its own commit, or Milestones 0-4 can be
implemented in one continuous verified slice. Either way, the rule is the same:
status prose follows the latest gate output, not aspiration.

At the end of every implemented milestone:

- rerun the milestone's governing commands after the last relevant artifact or
  config edit;
- update `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md` when status, blockers, source-set IDs, pass
  counts, or next routing change;
- keep `source_library/` generated artifacts unstaged unless repository policy
  changes explicitly;
- stage only the verified docs/config/tests/source slice for that milestone;
- make a local atomic commit before calling that milestone complete.

## Milestone Sequence

### Milestone 0 - Current Contract Baseline And False-Green Guard

Status: Resolved locally on 2026-05-28.

Outcome label: resolved.

Freeze the current West Reservoir readiness contract before rebuilding
anything. Confirm the replay context, package-authority manifest, V1 contract,
component eval contract, and generated result files all describe the same
current target: `west-reservoir-67436` on
`source-set-4fb59e9eb43045cb`.

Required actions:

- Confirm package authority remains verified:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_west_reservoir_package_authority.py`
- Rerun current evals as baseline:
  `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436`
- Rerun current component eval as baseline:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id west-reservoir-67436`
- Record that any green `phase_eval_results.json` on
  `source-set-5e65d845ce77e1a0` is stale and cannot satisfy this packet.
- Add or update focused regression coverage if the current tests do not catch
  stale source-set readiness reuse.

Exit criteria:

- V1 eval remains typed blocked only for allowed current blocker categories.
- Component eval remains red on the current source set until artifacts are
  rebuilt.
- No docs or manifests describe West Reservoir as reviewer-ready yet.

Implementation note:

- Package-authority verification remains green:
  `tests/test_west_reservoir_package_authority.py` passed `2/2`.
- Current V1 eval rerun on `source-set-4fb59e9eb43045cb` remains a truthful
  typed-blocked baseline: `contract_status="typed_blocked"`,
  `actual_overall_passed=false`, `broader_ea_passed=false`,
  `forest_plan_passed=false`, and failure categories limited to
  `review_artifact_missing=8`, `forest_plan_matrix_miss=1`,
  `forest_plan_reviewer_not_ready=1`, and `forest_plan_scope_miss=1`.
- Current component eval rerun on `source-set-4fb59e9eb43045cb` remains red as
  expected with `passed=false`, `passed_case_count=0`,
  `failed_case_count=27`, and the existing failure categories unchanged.
- `source_library/reviews/west-reservoir-67436/phase_eval_results.json` is
  still a historical green file for `source-set-5e65d845ce77e1a0`; it is not
  readiness evidence for this packet.
- `tests/test_phase_eval_review.py` now includes a stale-result guard proving
  that a review-scoped phase-eval rerun overwrites a pre-existing green review
  result with the tracked replay-context source set.
- No registry, coverage manifest, V1 contract, component contract, or
  reviewer-ready status was promoted in Milestone 0.
- Local closeout commit:
  `d5d97ad` (`Resolve West Reservoir baseline guard`).

### Milestone 1 - Review Artifact Spine Rebuild

Status: Reduced on 2026-05-28 by f70 applicability spine refresh; blocked on
forest-plan identity reconciliation before Flathead context/component artifact
generation.

Outcome label: reduced.

Rebuild the current review identity and artifact spine from the verified local
package cache and the current source set. This milestone reduces artifact
absence and identity drift; it does not promote readiness by itself.

Required actions:

- Reuse the verified package cache:
  `source_library/reviews/west-reservoir-67436/package`
- Rerun package review with explicit identity:
  `PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/west-reservoir-67436/package --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --reuse-package-cache`
- Rebuild Flathead applicability context and validation:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53`
- Build the authority universe:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53`
- Run applicability retrieval:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53`
- Run applicability decisions:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53`
- Validate applicability:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53`
- Generate and validate the review-specific rule pack:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53`
- Resolve Flathead forest-plan context:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/west-reservoir-67436/package --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --reuse-package-cache`

Exit criteria:

- Generated review artifacts carry `review_id="west-reservoir-67436"` and
  `source_set_id="source-set-f70ea11e04ae3d53"`.
- Missing artifact count is reduced materially.
- Flathead forest-plan context exists and resolves to `flathead_nf`.
- Applicability validation has `0` unresolved and no hidden
  `needs_adjudication` decisions, or the milestone stops and records the
  precise adjudication gap.

Implementation note:

- `ea-review` reran against
  `source_library/reviews/west-reservoir-67436/package` on
  `source-set-4fb59e9eb43045cb` and rebuilt `review_report.json` with
  `reviewer_ready=true`, `validation_passed=true`, `package_file_count=12`,
  `package_chunk_count=659`, and `finding_status_counts={"pass":5}`.
- `applicability-context-build` rebuilt the package applicability context and
  package fact graph with `validation_passed=true`.
- `applicability-authority-universe` now reads
  `forest_unit_id="flathead-nf"` from the tracked replay context and records
  it in `authority_universe_snapshot.json`.
- The generated snapshot now review-scopes the base rule universe from `48` to
  `47` rules by removing `custer_gallatin_lmp_2022`, selects `80` Flathead
  component candidates, reports
  `selected_component_forest_unit_ids=["flathead-nf"]`, and uses
  `FINAL-FLAT-001` as the forest-plan source record.
- The command still stops the milestone before retrieval or determination. The
  generated snapshot reports `passed=false` and `validation_passed=false` with
  two failing checks:
  `candidates_have_source_evidence_available` (`failure_count=9`) and
  `authority_family_template_candidates_cover_config`
  (`missing_source_record_count=10`).
- The remaining blocker is not Custer Gallatin placement drift. It is the
  `source-set-4fb59e9eb43045cb` source-evidence gap for non-forest authority
  families and baseline rules. The blocker is now routed through
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md` after
  confirming the active 4fb catalog lacks the required reconciled current
  source records while the later f70 current-source-gap closeout catalog is a
  different source set. Do not silently move West Reservoir to another source
  set inside this parent packet.
- The blocker Milestone 1 feasibility slice found no governed same-source-set
  4fb repair: `49` required legacy IDs have current mappings, `0` mapped
  current IDs are present in the active 4fb catalog, and all `49` are present
  only in `source-set-f70ea11e04ae3d53`. The follow-on owner is now
  `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`.
- The migration packet is now resolved for source-set parity and migrated
  authority-universe proof across replay context, V1 eval contract, component
  eval contract, component coverage, replay catalog surface, and f70 Flathead
  component-inventory proof.
- The migration packet Milestone 2 has since resolved the f70
  authority-universe proof. Before downstream retrieval/determination, rerun
  the parent Milestone 1 f70 artifact freshness steps because
  `package_applicability_context.json` was last rebuilt on the pre-migration
  `source-set-4fb59e9eb43045cb`.
- The parent f70 artifact freshness slice then reran `ea-review`,
  `applicability-context-build`, `applicability-authority-universe`,
  `applicability-retrieve`, and `applicability-determine` on
  `source-set-f70ea11e04ae3d53`. The first f70 determination produced the
  same three authority-family conflicts as the earlier review, with current
  f70 decision IDs and evidence hashes.
- `config/applicability_adjudications/west-reservoir-67436.json` now matches
  the current f70 decision hash and carries the same evidence-backed human
  applicable resolutions for the three authority-family conflicts: Clean Air
  Act conformity/air quality, species supporting sources and overlays, and
  vegetation/wildfire/forest health authorities.
- `applicability-adjudication-eval` passed with `resolved_adjudication_count=3`,
  `pending_adjudication_count=0`, and no failure categories. The adjudication
  apply gate passed with `remaining_unresolved_authority_count=0`.
- The final f70 applicability validation passed with
  `applicable_authority_count=44`, `non_applicable_authority_count=102`,
  `needs_adjudication_authority_count=0`, `unresolved_authority_count=0`,
  `reviewer_ready=true`, and `generated_rule_pack_ready=true`.
- `applicability-generate-rule-pack` passed with `generated_rule_count=44` and
  `generated_rule_pack_ready=true`.
- `forest-plan-resolve` now generates current f70 Flathead context and
  component artifacts after the child blocker supplied the six originally
  missing required support records and the triggered monitoring-program support
  record `R1PLAN-flathead-nf-08`. The f70 retrieval readiness checks pass with
  `blocking_missing_source_record_ids=[]`, and
  `forest_plan_context_validation.json` passes on f70.
- The child blocker
  `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
  is now resolved locally. The next active slice is Milestone 2 component
  readiness in this parent packet. Do not start compliance review, V1
  promotion, phase eval, registry promotion, or aggregate promotion until
  current component adjudication and component eval pass on f70.
- Local commit anchors:
  `267ba9d` (`Scope West Reservoir authority universe to Flathead`) for the
  Flathead authority-universe scoping repair and `0773ef7` (`Open West
  Reservoir source evidence blocker`) for the blocker route. The docs-only
  Bitter Lesson alignment commit is `3a5e6b3` (`Align West Reservoir plans
  with Bitter Lesson`).

### Milestone 2 - Flathead Component Readiness

Outcome label: pending. This is the active parent slice now that f70
forest-plan context validation passes.

Produce current component findings, standard coverage, and reviewer-resolution
queue artifacts, then make the tracked West Reservoir component eval pass.

Required actions:

- Build current Flathead plan components if the review lacks current component
  source artifacts:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --forest-unit-id flathead-nf --manifest-path`
- Generate the current component adjudication template:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template --output-dir source_library --review-id west-reservoir-67436`
- Update tracked adjudication only with evidence-backed decisions:
  `config/forest_plan_component_adjudications/west-reservoir-67436.json`
- Evaluate tracked adjudication:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id west-reservoir-67436 --adjudication-file config/forest_plan_component_adjudications/west-reservoir-67436.json`
- Run current component eval:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id west-reservoir-67436`

Exit criteria:

- `forest_plan_component_findings.json`,
  `forest_plan_applicable_standard_coverage.json`, and
  `forest_plan_reviewer_resolution_queue.json` exist for the current review.
- Component adjudication eval reports `reviewer_ready=true`.
- Component eval passes `27/27` cases with `failed_case_count=0`.
- West Reservoir's component-coverage slot passes and source-set aligns.
- Any remaining aggregate component-coverage failure is limited to
  non-West-Reservoir slots and named explicitly.

### Milestone 3 - Compliance Review And V1 Readiness Promotion

Outcome label: resolved.

Run the generated-pack compliance review and promote the V1 contract only after
the current West Reservoir review is actually reviewer-ready.

Required actions:

- Run compliance review with the generated West Reservoir rule pack:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path source_library/reviews/west-reservoir-67436/package --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --reuse-package-cache`
- Build the review packet index after compliance/matrix outputs exist:
  `PYTHONPATH=src python -m usfs_r1_ea_sources review-packet-index --output-dir source_library --review-id west-reservoir-67436`
- Rerun V1 eval:
  `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436`
- Update `config/v1_west_reservoir_real_ea_eval.json` only after current
  output proves `broader_ea_passed=true` and `forest_plan_passed=true`.
- Promote West Reservoir from typed blocked to reviewer-ready in
  `config/v1_real_package_review_coverage_v1.json` and
  `config/forest_specific_example_package_registry_v1.json` only after the V1
  eval passes.

Exit criteria:

- Compliance artifacts exist and validation passes.
- `compliance_matrix.json`, `compliance_matrix.md`, and
  `compliance_matrix.pdf` exist; the PDF is non-empty and accepted by
  phase-eval.
- Review packet index outputs exist if phase-eval requires them for the
  signer-facing package surface.
- V1 eval reports `contract_status="reviewer_ready"`,
  `actual_overall_passed=true`, `broader_ea_passed=true`, and
  `forest_plan_passed=true`.
- Registry and real-package aggregate manifests remain internally consistent.

### Milestone 4 - Phase Eval, Aggregate Reporting, Docs, And Commit Closeout

Outcome label: resolved for West Reservoir reviewer readiness.

Close the packet only after review-scoped phase eval and aggregate gates agree
with the promoted status.

Required actions:

- Run current review phase eval:
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id west-reservoir-67436`
- Run real-package aggregate:
  `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`
- Run forest-specific registry aggregate:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json`
- Run component aggregate:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json`
- Update docs and handoff with exact pass/fail counts, source-set IDs, and any
  residual aggregate blockers.
- Make one atomic local commit after verification passes.

Exit criteria:

- Phase eval passes on `source-set-f70ea11e04ae3d53`.
- Real-package aggregate and forest-specific registry aggregate pass with West
  Reservoir as reviewer-ready.
- Component aggregate either passes or remains red only for explicitly named
  non-West-Reservoir blockers. If ECID source-delta remains red, docs must say
  aggregate component coverage is not fully green.
- The packet is not complete until the verified docs/config/tests slice is
  committed locally.

## Verification Gates

Run focused gates after each milestone and the full closeout set before the
final commit.

Required closeout commands:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md
PYTHONPATH=src uv run --extra dev pytest tests/test_west_reservoir_package_authority.py tests/test_replay_context.py tests/test_real_package_review_coverage_eval.py tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_v1_ea_eval.py tests/test_compliance_review.py tests/test_cli_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Required current eval commands:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources review-packet-index --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
```

Freshness check: every readiness command must be rerun after the last artifact,
contract, or adjudication change that can affect it. Do not cite an older
generated report when a tracked input has changed.

## Acceptance Criteria

- Package-authority verification remains green with `12` official PDFs,
  `12` package-manifest rows, zero hash mismatches, and
  `omitted_document_count=0`.
- Current West Reservoir review artifacts carry
  `review_id="west-reservoir-67436"` and
  `source_set_id="source-set-f70ea11e04ae3d53"`.
- Flathead forest-plan scope resolves as `flathead_nf` with Flathead plan
  source citations.
- Applicability validation reports `0` unresolved and generated-rule-pack
  validation passes.
- Component eval passes `27/27` cases with `failed_case_count=0` and the
  existing thresholds or stricter numeric minimums.
- Compliance review reports `reviewer_ready=true` and
  `validation_passed=true` using the generated West Reservoir rule pack.
- Compliance matrix JSON, Markdown, and PDF artifacts exist; the PDF is
  non-empty and phase-eval accepts it.
- V1 eval reports `contract_status="reviewer_ready"` and no failure
  categories.
- Phase eval passes on `source-set-f70ea11e04ae3d53`; any `5e65...` phase
  artifact is documented as historical.
- Real-package coverage, forest-specific registry, and component-coverage
  manifests contain no mixed typed-blocked/reviewer-ready language for the
  active West Reservoir example after promotion.
- Aggregate docs and handoff describe exactly which gates are green and which,
  if any, remain red.
- No tests are weakened and no new skips, xfails, or coverage pragmas are added
  without user approval and a debt-register entry.
- The milestone is ready-to-close only after the verified slice is committed.

## Documentation And Handoff

Update these files in the same milestone slice that changes their truth:

- `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `README.md` only if stable entrypoints or public repo contract text changes
- `docs/OUTPUT_SCHEMAS.md` only if generated artifact schemas or fields change
- `docs/TECH_DEBT_REGISTER.md` only if a user-approved temporary exception is
  introduced

Each closeout update must name:

- source-set ID;
- review ID;
- package-authority status;
- V1 eval status;
- component eval pass count;
- phase-eval source-set ID and pass count;
- aggregate coverage status and residual blockers;
- commit hash after local commit.

## Commit Closeout

This packet follows the repository milestone policy:

- stage only the verified West Reservoir reviewer-readiness slice;
- do not stage ignored `source_library/` artifacts;
- make one atomic commit per completed milestone or a single atomic closeout
  commit if Milestones 0-4 are implemented as one verified slice;
- do not push unless the user explicitly asks;
- do not mark the plan complete until the local commit exists and the handoff
  includes the commit hash.

## Stop Conditions

Stop and report the blocker instead of promoting readiness if any of these
occur:

- official package-authority verification no longer matches the local package;
- current review outputs cannot be rebuilt on
  `source-set-f70ea11e04ae3d53`;
- Flathead forest-plan scope cannot be resolved without using Custer Gallatin
  source-record identity;
- applicability, component adjudication, or compliance review has unresolved
  reviewer decisions;
- component eval cannot pass all `27/27` cases without lowering thresholds;
- V1 eval or phase eval is green only on the historical `5e65...` source set;
- required verification commands fail and cannot be fixed inside the milestone
  scope;
- a required fix would become a broad architecture, downloader, source-capture,
  or full-corpus rebuild project.

## Residual Risks And Next Routing

- West Reservoir readiness can resolve the Flathead governed-example gap, but
  it may not make aggregate forest-plan component coverage green if ECID
  source-delta remains stale or failing.
- The historical Flathead live-package proving plan closed on
  `source-set-5e65d845ce77e1a0`; this plan supersedes it for current
  reviewer-readiness routing.
- If West Reservoir closes green and ECID source-delta remains red, the next
  route should be a separate ECID source-delta/component-coverage repair packet.
- If West Reservoir cannot close without source-set rebuild work, open a new
  blocker packet rather than weakening readiness gates.

## Closeout Checklist

- [x] Milestone 0 baseline and stale-green guard resolved
- [x] Milestone 1 review/applicability artifact spine rebuilt on
      `source-set-f70ea11e04ae3d53`
- [x] Milestone 1 f70 identity blocker reduced to six Flathead source-capture
      gaps
- [x] Child Milestone 2 indexed the six originally missing Flathead required
      support records under f70
- [x] Child Milestone 3 resolved the `R1PLAN-flathead-nf-08`
      monitoring-program context gate
- [x] Milestone 1 source-evidence blocker routed through
      `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- [ ] Milestone 2 component eval passes `27/27`
- [ ] Milestone 3 compliance and V1 readiness gates pass
- [ ] Milestone 4 phase eval and aggregate gates rerun
- [x] Docs and session handoff updated with exact counts and residual blockers for Milestone 0
- [x] Verification commands recorded for Milestone 0
- [x] Stage only intended docs/config/tests/source changes for Milestone 0
- [x] Local atomic commit created for Milestone 0
- [x] Milestone 0 closeout commit recorded: `d5d97ad`
- [x] Milestone 1 Flathead scoping commit recorded: `267ba9d`
- [x] Milestone 1 source-evidence blocker route commit recorded: `0773ef7`
- [x] Docs-only Bitter Lesson alignment commit recorded: `3a5e6b3`
