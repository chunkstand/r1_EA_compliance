# Overall Architecture Refactor Milestone Plan

Date: 2026-05-20

Status: Milestones 0-5 complete; Milestone 6 active after Sequence 16

Owner context: This is the active repo-wide architecture refactor packet after the closed
`docs/AGENT_LEGIBILITY_ENTRYPOINT_MILESTONE_PLAN.md` lane. Milestones 0-5 are now closed, the
document-plan runtime slice remains historical state from `1435cdb`, Milestone 5 has now closed a
bounded shared-helper split across the capture and extraction/retrieval owner family, and
Milestone 6 is now active on the applicability, claims, and evidence hotspot surfaces.

## Purpose

Route the repo's structural architecture debt into a governed, hotspot-driven refactor sequence that
reduces the largest brittle surfaces without weakening tests, current-state gates, or the
artifact-first reviewer pipeline.

The repo already has strong architectural intent:

- the workbook is the source contract;
- derived artifacts are explicit and auditable;
- architecture boundaries are documented in `docs/ARCHITECTURE.md` and
  `docs/architecture_contract.toml`; and
- the architecture probe currently reports no Python or JS cycles.

The weak point is not missing direction. The weak point is that too much runtime and test logic is
still concentrated in a small number of very large files, some governance surfaces only just became
cheap automated checks, and several operational truths still depend on large append-only docs or
machine-local state.

## Current Evidence

### Live repo state

- The routed agent-entrypoint packet is now complete:
  `docs/AGENT_LEGIBILITY_ENTRYPOINT_MILESTONE_PLAN.md` says `Status: complete`, and the public
  `document-plan` plus `docs/AGENT_START_HERE.md` surfaces closed in `1435cdb`.
- The shared document-output PDF seam closed in Milestone 3, and Milestone 4 now closes the first
  bounded graph-and-review owner split:
  `review_package_support.py` owns the shared review-package cache/search/readiness seam for
  `ea_review.py`, `forest_plan_resolver.py`, and `forest_plan_components.py`, while
  `nepa_3d_graph_contract.py` now owns NEPA graph lens metadata and validation failure-category
  annotation consumed by `nepa_knowledge_graph_export.py`.
- Milestone 5 now closes the first bounded source-capture and extraction/retrieval helper split:
  `capture_run_support.py` owns shared capture manifest/report serialization for
  `download.py`, `preflight.py`, `report.py`, `validate_run.py`, and `catalog.py`, while
  `source_set_support.py` owns the shared derived-output path and support-document-role helpers
  now used directly by `extract.py`, `retrieval.py`, `extraction_accuracy.py`,
  `claim_extraction.py`, `evidence_graph.py`, `phase_eval.py`, and `rule_claim_binding.py`.
- Milestone 6 sequence 16 now closes the `claim-runtime` owner seam:
  `claim_extraction_runtime.py` now owns deterministic claim-pattern definitions, sentence/window
  handling, claim record assembly, IDs/hashes, and extraction metrics, while
  `claim_extraction.py` is reduced to the public claim-extraction facade plus orchestration
  support. The next executable slice now advances to `rule_claim_binding.py` inside Milestone 6.

### Architecture probe current baseline

From
`python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20`:

- `230` code files detected;
- `52` code files exceed `800` lines;
- no Python import cycles detected;
- no JS/TS import cycles detected;
- top hotspot:
  `src/usfs_r1_ea_sources/project_sow_package.py` with score `104370`;
- highest local fan-out:
  `src.usfs_r1_ea_sources.cli_derived` imports `22` local modules;
- new shared helper fan-in:
  `src.usfs_r1_ea_sources.capture_run_support` is already imported by `5` local modules;
- new applicability and claims owner surfaces:
  `src.usfs_r1_ea_sources.applicability_adjudication` is `740` lines,
  `src.usfs_r1_ea_sources.applicability_adjudication_apply` is `443` lines,
  `src.usfs_r1_ea_sources.applicability_validation_artifacts` is `173` lines,
  `src.usfs_r1_ea_sources.applicability_validation_checks` is `791` lines,
  `src.usfs_r1_ea_sources.applicability_validation_freshness` is `304` lines,
  `src.usfs_r1_ea_sources.applicability_validation_support` is `171` lines,
  `src.usfs_r1_ea_sources.applicability_authority_family_templates` is `417` lines and
  `src.usfs_r1_ea_sources.applicability_authority_universe_contracts` is `594` lines,
  `src.usfs_r1_ea_sources.applicability_contract_support` is `113` lines,
  `src.usfs_r1_ea_sources.applicability_candidate_assembly` is `722` lines,
  `src.usfs_r1_ea_sources.applicability_decision_arbitration` is `349` lines,
  `src.usfs_r1_ea_sources.applicability_decision_coverage` is `227` lines,
  `src.usfs_r1_ea_sources.applicability_decision_evidence` is `590` lines,
  `src.usfs_r1_ea_sources.applicability_decision_forest_plan` is `128` lines,
  `src.usfs_r1_ea_sources.applicability_decision_outputs` is `375` lines,
  `src.usfs_r1_ea_sources.applicability_decisions` is down to `793` lines from the post-sequence-8
  `916`-line baseline, `src.usfs_r1_ea_sources.applicability_validation` is down to `178` lines
  from the post-sequence-11 `607`-line baseline, post-sequence-10 `1502`-line baseline, and
  pre-sequence `2494`-line baseline, and `src/usfs_r1_ea_sources.applicability.py`
  remains a `48`-line public facade after falling from the pre-sequence `2315`-line baseline
  without introducing a new `>800` line file; `src.usfs_r1_ea_sources.claim_extraction.py`
  is down to `458` lines from the post-sequence-15 `783`-line baseline, the post-sequence-14
  `1328`-line baseline, the post-sequence-13 `2084`-line baseline, and the pre-sequence
  `2503`-line baseline, `src.usfs_r1_ea_sources.claim_extraction_runtime.py` now owns the bounded
  extraction runtime surface at `342` lines, `src.usfs_r1_ea_sources.claim_extraction_validation.py`
  now owns the bounded validation surface at `614` lines, `src.usfs_r1_ea_sources.claim_extraction_eval.py`
  remains at the `800`-line gate, and `src.usfs_r1_ea_sources.claim_extraction_graph.py` remains
  below the gate at `457` lines;
- suggested gates:
  `large-active-files`, `high-fan-out-modules`, and `hotspot-review`.

### Current brittle places

- Giant orchestration modules dominate active edit risk:
  `project_sow_package.py`, `nepa_knowledge_graph_export.py`, `forest_plan_components.py`,
  `ea_consistency_decision_support.py`, `extract.py`, `v1_ea_eval.py`, and the applicability family
  are all far above the repo's reviewable size threshold.
- Shared-helper ownership is better, but not finished:
  `capture_run_support.py` now removes the cross-owner manifest/report helpers previously mixed
  across `download.py`, `preflight.py`, `report.py`, `validate_run.py`, and `catalog.py`, and
  `source_set_support.py` now removes the direct `retrieval.py -> extract.py` private-helper seam
  and the remaining in-repo `extract._source_derived_dir` wrapper consumers; direct helper coverage
  now lives in `tests/test_source_set_support.py`. The remaining issue is not helper routing but
  file size: `extract.py` and `retrieval.py` still remain large.
- Test monoliths are also large and highly active:
  `tests/test_promotion_suite.py`, `tests/test_cli.py`, `tests/test_compliance_review.py`,
  `tests/test_forest_plan_resolver.py`, `tests/test_project_sow_package.py`, and
  `tests/test_extract.py`.
- Debt governance and cheap architecture gates are now green, but the large-file count remains at
  `52` code files over `800` lines and still requires owner-family reduction instead of more
  policy work.
- The compliance-output family still has oversized verification ownership:
  `tests/test_compliance_review.py` is still a large mixed-owner file at `1418` lines, but the
  stale review-helper import from `ea_review.py` and the stale Flathead primary-plan fixture drift
  are now closed and the full file passes again; the remaining issue is test-owner size and
  coupling, not a blocked Flathead readiness seam or a shared-review-helper regression.
- Durable context is high quality but expensive to scan:
  `docs/SESSION_HANDOFF.md` is `11035` lines and append-only;
  `docs/CURRENT_SYSTEM_STATE.md` is `4759` lines.
- Architecture doc routing needs an explicit canonical-path guard:
  on this macOS checkout the lowercase path aliases the tracked uppercase file, so path drift must
  be prevented by policy and tests rather than by maintaining two physical docs.
- Hermeticity is incomplete for at least one governed proving lane:
  `docs/CURRENT_SYSTEM_STATE.md` still declares the preserved West Reservoir replay-context package
  path under `/Users/chunkstand/Downloads/West Reservoir (67436)`.
- The low-level line/PDF writer is now centralized:
  `pdf_object_writer.py` owns the shared object serializer plus the common
  line-oriented PDF renderers used by
  `project_sow_package.py`,
  `compliance_outputs.py`,
  `ea_consistency_decision_support.py`,
  `final_qa_certification.py`, and
  `review_packet_index.py`;
  broader owner-family and test-family splits still remain.

## Goal

Reduce the repo's highest architecture risk surfaces while preserving current public behavior,
artifact contracts, review/eval truth, and fail-closed governance.

This umbrella plan is successful when the repo has:

- a clean and explicit agent cold-start entrypoint;
- green debt and architecture governance surfaces;
- materially fewer `>800` line hotspots and less concentrated orchestration logic;
- tighter public CLI and shared-helper ownership;
- smaller, more reviewable tests and fixtures; and
- no required proving lane that depends on an undeclared machine-local package path.

## Non-Goals

- Do not rewrite the repo into a new framework or service architecture.
- Do not regenerate the entire corpus or broad `source_library/` outputs unless a bounded milestone
  explicitly requires it.
- Do not weaken tests, add skips, add broad coverage pragmas, or loosen assertions to make the
  sequence look green.
- Do not change workbook semantics, downloader rules, citation-bearing reviewer output semantics, or
  evaluation meaning unless a bounded milestone explicitly owns that contract change.
- Do not silently absorb already-closed routed narrow packets into the broad refactor without an
  explicit rebaseline.
- Do not treat line-count reduction alone as success; every extraction must preserve or strengthen
  the owning gate.

## Scope

In scope:

- architecture-governance repairs and new size/fan-out gates;
- agent entrypoint completion and cold-start doc routing;
- hotspot-driven splits for oversized runtime families;
- test and fixture hotspot reduction;
- CLI fan-out and shared helper ownership cleanup;
- documentation routing cleanup for architecture/current-state/handoff entrypoints; and
- replay hermeticity work where a live repo claim still depends on a user-home path.

Out of scope:

- arbitrary style-only refactors;
- broad domain-rule redesign not justified by hotspot ownership;
- viewer redesign beyond boundary cleanup needed to reduce `viewer/nepa-3d/app.js` concentration;
- new source capture or review promotion claims unrelated to the architecture-owner work; and
- large network or package reruns used only to re-prove already known behavior.

## Weak-Point Register

This plan acts as the current repo-wide architecture weak-point register until the sequence closes.

| Weak point | Current evidence | Owner surface | Prevention gate | Status | Next milestone |
| --- | --- | --- | --- | --- | --- |
| Dirty baseline overlap | pre-closeout worktree overlap is limited to this packet's architecture-governance docs; the document-plan lane already closed in `1435cdb` | `docs/SESSION_HANDOFF.md`, this plan, active worktree | `git status -sb` plus plan/handoff readback must show no runtime overlap from the closed packet | resolved | closed |
| Large-file concentration | `54` code files over `800` lines | hotspot families listed in this plan | `tests/test_architecture_quality.py` plus architecture probe readback | guarded | Milestones 3-8 |
| High-fan-out orchestration | `cli_derived` fan-out `22`; `cli_eval` and `phase_eval` also broad | `cli_*.py`, eval orchestration modules | `tests/test_architecture_quality.py` plus architecture probe readback | guarded | Milestones 3, 7 |
| Debt-register drift | pre-closeout `TD-001` stale line reference against `batches.py:223` | `docs/TECH_DEBT_REGISTER.md`, debt tests | `tests/test_debt_contract.py` | resolved | closed |
| Incomplete agent entrypoint | closed in `63e1160` and `1435cdb` | `document_plan.py`, CLI, agent docs | focused document-plan and CLI tests | resolved | closed |
| Missing dependency declaration | closed by the current planner contract, which validates requests without a new external schema runtime dependency | document-planning surfaces | focused planner/CLI tests | resolved | closed |
| Cold-start doc sprawl | handoff `11035` lines; current state `4759` lines | `docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`, start-here docs | doc routing readback plus handoff routing review | reduced | Milestone 9 |
| Architecture doc path drift | uppercase path is canonical, but the checkout still needs a guard against lowercase-path drift | architecture docs and references | `tests/test_architecture_quality.py` plus doc readback | resolved | closed |
| Non-hermetic proving dependency | West Reservoir replay context points at `/Users/chunkstand/Downloads/...` | replay-context and proving docs/config | proving-lane contract tests and docs readback | deferred | Milestone 9 |
| Duplicated PDF/rendering helpers | shared PDF object and line renderer ownership now lives in `pdf_object_writer.py`; the owner-family split risk is narrower but not the same as the broader document-owner hotspot | reporting/document-output family | focused helper contract tests plus owner-family readback | resolved | closed |
| Oversized test/fixture owners | multiple `tests/*.py` and `tests/support/*.py` files over threshold | test families and support fixtures | architecture probe plus focused pytest slices | deferred | Milestone 8 |

## Large-File Inventory Over 800 Lines

### Priority A - primary runtime hotspots

- `4970` `src/usfs_r1_ea_sources/project_sow_package.py`
- `4837` `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`
- `4279` `src/usfs_r1_ea_sources/forest_plan_components.py`
- `3306` `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`
- `3170` `src/usfs_r1_ea_sources/extract.py`
- `2662` `src/usfs_r1_ea_sources/v1_ea_eval.py`
- `2655` `src/usfs_r1_ea_sources/applicability_eval.py`
- `2384` `src/usfs_r1_ea_sources/final_qa_certification.py`
- `2017` `src/usfs_r1_ea_sources/rule_claim_binding.py`
- `1956` `src/usfs_r1_ea_sources/draft_generation.py`
- `1893` `src/usfs_r1_ea_sources/retrieval.py`
- `1862` `src/usfs_r1_ea_sources/phase_eval.py`
- `1829` `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `1770` `src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py`
- `1741` `src/usfs_r1_ea_sources/applicability_retrieval.py`
- `1686` `src/usfs_r1_ea_sources/compliance_outputs.py`
- `1675` `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`
- `1496` `src/usfs_r1_ea_sources/catalog.py`
- `1469` `src/usfs_r1_ea_sources/package_fact_graph.py`
- `1440` `src/usfs_r1_ea_sources/applicability_rule_pack.py`
- `1347` `src/usfs_r1_ea_sources/compliance_review_eval.py`
- `1347` `src/usfs_r1_ea_sources/authority_currentness.py`
- `1307` `src/usfs_r1_ea_sources/review_packet_index.py`
- `1271` `src/usfs_r1_ea_sources/upstream_evaluation.py`
- `1205` `src/usfs_r1_ea_sources/evidence_graph.py`
- `1181` `src/usfs_r1_ea_sources/source_register_proving.py`
- `1167` `src/usfs_r1_ea_sources/promotion_suite.py`
- `1064` `src/usfs_r1_ea_sources/source_register.py`
- `997` `src/usfs_r1_ea_sources/forest_plan_component_adjudication.py`
- `914` `src/usfs_r1_ea_sources/download.py`
- `886` `src/usfs_r1_ea_sources/forest_plan_component_eval.py`
- `859` `src/usfs_r1_ea_sources/preflight.py`
- `824` `src/usfs_r1_ea_sources/compliance_validation.py`

### Priority B - test and fixture hotspots

- `2618` `tests/test_forest_plan_resolver.py`
- `2138` `tests/test_applicability_decisions.py`
- `2090` `tests/test_promotion_suite.py`
- `1892` `tests/test_v1_ea_eval.py`
- `1878` `tests/test_cli.py`
- `1768` `tests/test_project_sow_package.py`
- `1754` `tests/test_forest_plan_components.py`
- `1646` `tests/test_extract.py`
- `1429` `tests/test_nepa_knowledge_graph_export.py`
- `1418` `tests/test_compliance_review.py`
- `1351` `tests/test_final_qa_certification.py`
- `1236` `tests/test_retrieval.py`
- `1174` `tests/test_ea_consistency_decision_support.py`
- `1102` `tests/support/compliance_review_fixtures.py`
- `954` `tests/test_phase_eval.py`
- `893` `tests/test_applicability.py`
- `872` `tests/support/compliance_component_fixtures.py`
### Priority C - viewer hotspot

- `2547` `viewer/nepa-3d/app.js`

## Owner Surfaces

- `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/TECH_DEBT_REGISTER.md`
- `docs/architecture_contract.toml`
- `pyproject.toml`
- `src/usfs_r1_ea_sources/cli.py`
- `src/usfs_r1_ea_sources/cli_*.py`
- `src/usfs_r1_ea_sources/project_sow_package.py`
- `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`
- `src/usfs_r1_ea_sources/draft_generation.py`
- `src/usfs_r1_ea_sources/final_qa_certification.py`
- `src/usfs_r1_ea_sources/review_packet_index.py`
- `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`
- `src/usfs_r1_ea_sources/forest_plan_*.py`
- `src/usfs_r1_ea_sources/extract.py`
- `src/usfs_r1_ea_sources/retrieval.py`
- `src/usfs_r1_ea_sources/catalog.py`
- `src/usfs_r1_ea_sources/download.py`
- `src/usfs_r1_ea_sources/preflight.py`
- `src/usfs_r1_ea_sources/source_register*.py`
- `src/usfs_r1_ea_sources/applicability.py`
- `src/usfs_r1_ea_sources/applicability_authority_family_templates.py`
- `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`
- `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`
- `src/usfs_r1_ea_sources/applicability_contract_support.py`
- `src/usfs_r1_ea_sources/applicability_*.py`
- `src/usfs_r1_ea_sources/rule_claim_binding.py`
- `src/usfs_r1_ea_sources/evidence_graph.py`
- `src/usfs_r1_ea_sources/phase_eval*.py`
- `src/usfs_r1_ea_sources/v1_ea_eval.py`
- `src/usfs_r1_ea_sources/promotion_suite.py`
- `tests/`
- `viewer/nepa-3d/app.js`

## Placement Rules

- Do not add another branch to a monolith when a milestone can instead extract a smaller owned
  module in the same family.
- New helper modules must be owner-named and adjacent to the boundary they serve. Do not create
  vague catch-all files such as `helpers2.py`, `utils_misc.py`, or `architecture_fixups.py`.
- Public CLI modules stay thin. Argument parsing and dispatch may live in `cli*.py`; domain logic
  must stay in owned runtime modules.
- Shared rendering or PDF writing logic should move into one narrow reporting helper owned by the
  reporting/document-output family rather than remain copied across multiple document producers.
- Tests should split by contract or behavior family, not by arbitrary line budget alone.
- Fixture helpers should move to focused support modules only when the split increases reuse and
  keeps the scenario ownership clear.
- `docs/ARCHITECTURE.md` should remain the canonical architecture path. On this case-insensitive
  checkout, do not try to maintain a second physical lowercase file; guard the canonical tracked
  path with tests and references instead.
- `docs/AGENT_START_HERE.md` must stay short and route outward. It is not allowed to become another
  append-only state dump.
- Any new module, CLI family, or dependency-boundary exception must land with matching updates to
  `docs/architecture_contract.toml` and focused contract tests.

## Weak-Point Prevention Contract

### Weak point 1 - broad refactor starts from a dirty overlapping worktree

- Weak point forecast: a future session edits the overall refactor on top of the in-flight
  document-plan slice and produces an unreviewable mixed milestone.
- Owner surface: `git status -sb`, `docs/SESSION_HANDOFF.md`, this plan.
- Prevention gate: re-run `git status -sb` before Milestone 0 closeout and require the refactor
  owner surfaces to be isolated from the existing document-plan changes.
- Fail threshold: any architecture-refactor milestone stages or edits the document-plan lane
  without explicitly closing or parking that lane first.
- Controlled violation: leave `document_plan.py` and the broad refactor edits in the same milestone;
  the milestone must be treated as blocked.
- Future-Codex misuse scenario: a future session sees the hotspot backlog and starts splitting code
  immediately; this plan prevents that by making worktree isolation the first milestone.

### Weak point 2 - gates improve on paper but do not prevent new concentration

- Weak point forecast: the repo adds more architecture prose without adding measurable prevention.
- Owner surface: `docs/architecture_contract.toml`, architecture probe usage, focused governance
  tests.
- Prevention gate: the sequence must add or adopt explicit large-file and fan-out governance checks
  before large family splits begin.
- Fail threshold: a hotspot family milestone closes while `57` remains untracked only as prose and
  there is no live gate watching growth.
- Controlled violation: intentionally grow a known owner above the threshold in a local check and
  prove the new gate reports it.
- Future-Codex misuse scenario: a future session cites "better architecture" without a threshold;
  the gate turns that into a measurable failure.

### Weak point 3 - extracting code moves behavior but weakens coverage

- Weak point forecast: a monolith gets smaller only because coverage narrows.
- Owner surface: each runtime family and its focused test family.
- Prevention gate: every extraction milestone must run the focused tests for the owner family plus
  architecture and debt gates.
- Fail threshold: line count goes down but focused behavior or negative-path coverage disappears,
  loosens, or becomes skipped.
- Controlled violation: remove a negative-path assertion or route a failure branch around coverage;
  the focused tests must fail.
- Future-Codex misuse scenario: a future session deletes hard-to-maintain tests to unlock the split;
  this plan explicitly forbids that tradeoff.

### Weak point 4 - agent-facing surfaces ship without runtime completeness

- Weak point forecast: the repo exposes new agent commands or docs while missing dependencies or
  refusal behavior.
- Owner surface: `pyproject.toml`, `document_plan.py`, CLI registration, `docs/AGENT_START_HERE.md`.
- Prevention gate: focused document-plan and CLI tests plus help-text readback.
- Fail threshold: `document-plan` lands or stays routed as live while `tests/test_document_plan.py`
  still fails to import, the command is not visible, or unsupported requests do not fail closed.
- Controlled violation: remove the dependency or CLI registration and prove the tests/help readback
  detect the break.
- Future-Codex misuse scenario: a future session adds a prompt-facing entrypoint but forgets the
  package dependency or public CLI registration.

### Weak point 5 - doc routing becomes another large append-only surface

- Weak point forecast: the answer to large docs is another large doc.
- Owner surface: `docs/AGENT_START_HERE.md`, `docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`.
- Prevention gate: doc routing readback must show a short start-here surface that links outward and
  does not duplicate the long-form state docs.
- Fail threshold: the new entrypoint duplicates current-state or handoff content instead of routing
  to it.
- Controlled violation: copy large blocks from current-state docs into the start-here doc; the
  review/readback should fail the milestone.
- Future-Codex misuse scenario: a future session treats "make it legible" as "paste more summary".

### Weak point 6 - family splits create new ambiguous helper ownership

- Weak point forecast: extracted code lands in vague shared helpers that become the next monolith.
- Owner surface: new family helper modules.
- Prevention gate: review extracted paths against the placement rules and architecture contract.
- Fail threshold: the split creates a generic dump module or new hidden dependency direction.
- Controlled violation: attempt to place family logic in a generic `helpers.py` catch-all; reject
  the change during milestone review.
- Future-Codex misuse scenario: a future session solves a hotspot by inventing a new unlabeled
  dumping ground.

### Weak point 7 - hermeticity debt stays hidden behind green historical prose

- Weak point forecast: docs or eval results continue to imply replay readiness even though a proving
  lane depends on a user-home package path.
- Owner surface: replay contexts, proving docs, review-coverage docs, current-state docs.
- Prevention gate: readback over West Reservoir references plus the focused proving/eval contract
  surface.
- Fail threshold: the lane is still required for repo truth but remains dependent on
  `/Users/chunkstand/Downloads/...` without an explicit owner milestone.
- Controlled violation: remove the explicit disclosure from current-state docs and verify the
  routing review catches the omission.
- Future-Codex misuse scenario: a future session cites old green prose and assumes the lane is
  portable.

## Milestone Sequence

### Milestone 0 - Rebaseline And Isolate The Current Worktree

Outcome label: `reduced`
Status: complete

Purpose: stop the broad architecture sequence from starting on top of unrelated in-progress work.

Implementation:

1. Resolve, commit, or park the current document-plan lane before broad refactor implementation.
2. Refresh `git status -sb`, the architecture probe, the large-file inventory, and the top handoff
   routing section.
3. Record the fresh baseline in this plan and `docs/SESSION_HANDOFF.md`.

Remaining issue after closeout:

- the architecture backlog remains open, but the starting point is clean and current.

Closeout on 2026-05-20:

- The document-plan runtime lane was already closed in `1435cdb`; this milestone rebaselines the
  umbrella packet against that committed state instead of treating the lane as still in flight.
- The fresh baseline records `187` code files, `57` code files above `800` lines, no Python or
  JS/TS import cycles, top hotspot `project_sow_package.py` at score `101300`, and
  `cli_derived` fan-out `22`.
- The remaining pre-closeout overlap is limited to architecture-governance docs owned by this
  packet; no runtime implementation surfaces from the closed agent-entrypoint packet remain mixed
  into the broad refactor baseline.

### Milestone 1 - Repair Governance And Add Cheap Prevention Gates

Outcome label: `resolved`
Status: complete

Purpose: make architecture and debt governance trustworthy before large splits begin.

Implementation:

1. Fix `TD-001` in `docs/TECH_DEBT_REGISTER.md` so the live line reference is correct.
2. Keep `tests/test_debt_contract.py` green.
3. Add or wire a lightweight architecture quality gate that fails on:
   - large-file growth above the approved threshold;
   - high-fan-out growth above the approved threshold; and
   - new architecture-doc path drift.
4. Declare `docs/ARCHITECTURE.md` the canonical path and guard against lowercase-path drift in the
   checkout rather than maintaining a duplicate file on a case-insensitive filesystem.

Resolved scope after closeout:

- the debt register is trustworthy again;
- architecture drift has a cheap automated check; and
- architecture-doc routing is canonical.

Closeout on 2026-05-20:

- `TD-001` now points at `src/usfs_r1_ea_sources/batches.py:223`, and
  `tests/test_debt_contract.py` is green again.
- `tests/test_architecture_quality.py` now blocks large-file count growth above the current
  `57`-file `>800` baseline, blocks new `>20` fan-out source modules beyond the existing
  `cli_derived` outlier, and pins `docs/ARCHITECTURE.md` as the canonical tracked architecture
  doc path.
- `docs/ARCHITECTURE.md` now declares the canonical path explicitly, which keeps future doc routing
  aligned with the new guard.

### Milestone 2 - Finish The Agent Entrypoint Packet

Outcome label: `resolved`
Status: complete via routed packet

Purpose: close the current cold-start gap for agents and operators.

Implementation:

1. Complete the routed work in `docs/AGENT_LEGIBILITY_ENTRYPOINT_MILESTONE_PLAN.md`.
2. Add the missing runtime dependency declarations for the document-plan lane.
3. Expose `document-plan` on the public CLI.
4. Add `docs/AGENT_START_HERE.md` as the short entrypoint doc.
5. Update architecture/current-state/handoff docs so the new entrypoint is the first routed
   surface for prompt-to-document work.

Resolved scope after closeout:

- the repo has one concise cold-start path for document-routing work;
- the environment matches the routed surface; and
- unsupported request classes still fail closed.

Closeout on 2026-05-20:

- The routed agent-entrypoint packet is already complete through `63e1160` and `1435cdb`.
- `document-plan`, `docs/AGENT_START_HERE.md`, the lane registry, the normalized request schema,
  and the focused planner/CLI/architecture tests are now historical closeout state, not open work
  inside this umbrella packet.

### Milestone 3 - Split Project Planning And Document Output Hotspots

Outcome label: `reduced`
Status: complete

Purpose: reduce the highest document-generation concentration risk.

Owner family:

- `project_sow_package.py`
- `ea_consistency_decision_support.py`
- `draft_generation.py`
- `final_qa_certification.py`
- `review_packet_index.py`
- `compliance_outputs.py`

Implementation:

1. Extract one shared document-output PDF helper that owns the low-level object serializer and the
   repeated line-oriented renderer contract.
2. Rewire `project_sow_package.py`, `ea_consistency_decision_support.py`,
   `compliance_outputs.py`, `review_packet_index.py`, and `final_qa_certification.py` to consume
   that helper without changing their public commands or artifact families.
3. Add focused helper contract tests and the matching architecture-contract coverage in the same
   slice.
4. Route the broader owner-module and large-test decomposition work forward explicitly instead of
   pretending this seam extraction closes the entire document family.

Closeout on 2026-05-20:

- `src/usfs_r1_ea_sources/pdf_object_writer.py` now owns the shared PDF object writer, the shared
  single-page line renderer, and the shared paginated line renderer for the document-output family.
- `project_sow_package.py` shrank from `5065` to `4970` lines, `ea_consistency_decision_support.py`
  from `3401` to `3306`, `compliance_outputs.py` from `1781` to `1686`,
  `review_packet_index.py` from `1349` to `1307`, and `final_qa_certification.py` from `2425` to
  `2384`.
- `tests/test_pdf_object_writer.py` now pins the shared writer contract directly, and the existing
  producer-family tests still validate PDF headers and generated artifact wiring through their
  public surfaces.
- A wider run that included the full `tests/test_compliance_review.py` file still hit the unrelated
  Flathead `forest_plan_resolver` retrieval-readiness gate, which confirms the remaining
  verification coupling lives in the oversized test owner rather than in the new shared PDF helper.
- The architecture probe still reports `57` code files above `800` lines, no Python or JS/TS
  import cycles, and no new fan-out hotspot; the next architecture slice should therefore move to
  the graph and forest-plan family rather than keep reworking the same renderer seam.

Remaining issue after closeout:

- `draft_generation.py`, the remaining project-planning/document-output owner boundaries, and the
  oversized test-family splits still need follow-on work, but the duplicated PDF/rendering seam is
  now removed, the current owner files are smaller and clearer, and the unresolved compliance-suite
  coupling is explicitly routed as test-owner debt rather than being left as an ambiguous renderer
  regression.

### Milestone 4 - Split NEPA Graph And Forest-Plan Review Hotspots

Outcome label: `reduced`

Purpose: reduce concentration in the graph export and forest-plan review family.

Owner family:

- `nepa_knowledge_graph_export.py`
- `forest_plan_components.py`
- `forest_plan_resolver.py`
- `forest_plan_component_eval.py`
- `forest_plan_component_adjudication.py`
- `ea_review.py`
- `viewer/nepa-3d/app.js`

Implementation:

1. Separate graph-contract assembly, export serialization, summary/report formatting, and CLI-facing
   orchestration in the NEPA graph family.
2. Split forest-plan parsing, component normalization, adjudication, and evaluation ownership into
   smaller modules.
3. Reduce `viewer/nepa-3d/app.js` concentration by extracting bounded viewer modules without
   changing the operator-facing artifact contract.

Milestone 4 closeout:

- Runtime closeout commit:
  `b58f956` (`Reduce architecture refactor Milestone 4 review and graph seams`)
- `review_package_support.py` now owns the shared review-package cache lifecycle, extraction reuse,
  retrieval-artifact lookup, and deterministic package-search helpers reused by
  `ea_review.py`, `forest_plan_resolver.py`, and `forest_plan_components.py`.
- `nepa_3d_graph_contract.py` now owns lens metadata assembly and validation failure-category
  annotation/counting consumed by `nepa_knowledge_graph_export.py`.
- Flathead forest-plan resolver fixtures now align to the governed primary-plan identity
  `FINAL-FLAT-001`, matching the earlier identity-reconciliation packet instead of the retired
  `R1PLAN-flathead-nf-02` alias.

Remaining issue after closeout:

- graph and forest-plan surfaces may still remain large, but the core owner boundaries are explicit
  and no longer dominated by a few multi-thousand-line files.

### Milestone 5 - Split Extraction, Retrieval, And Capture Hotspots

Outcome label: `reduced`

Purpose: reduce concentration across source capture and evidence-prep families.

Owner family:

- `extract.py`
- `retrieval.py`
- `catalog.py`
- `download.py`
- `preflight.py`
- `source_register.py`
- `source_register_proving.py`
- `authority_currentness.py`
- `forest_plan_source_delta_readiness.py`

Implementation:

1. `capture_run_support.py` now owns the shared capture manifest-record builder, JSONL writer,
   failure CSV writer, failure-status classifier, and manifest-path resolution contract used by
   `download.py`, `preflight.py`, `report.py`, `validate_run.py`, and `catalog.py`.
2. `source_set_support.py` now owns the shared derived-output path and support-document-role helper
   contract used directly by `extract.py`, `retrieval.py`, `extraction_accuracy.py`,
   `claim_extraction.py`, `evidence_graph.py`, `phase_eval.py`, and `rule_claim_binding.py`,
   removing both the private `retrieval.py -> extract.py` helper seam and the temporary
   in-repo compatibility dependence on `extract._source_derived_dir`.
3. Focused tests now pin the shared helper contracts directly in
   `tests/test_capture_run_support.py` and `tests/test_source_set_support.py`, while the existing
   download, preflight, catalog, validate-run, extraction, retrieval, claim, evidence-graph,
   phase-eval, and rule-claim tests still verify the public workflow behavior end to end.

Remaining issue after closeout:

- `extract.py` and `retrieval.py` remain large, and broader chunking/ranking/report owner splits
  still remain for later packets.

### Milestone 6 - Split Applicability, Claims, And Evidence Hotspots

Outcome label: `reduced`
Status: active after Sequence 16

Purpose: reduce the largest concentration in the applicability decision family and the adjacent
claims/evidence hotspots without weakening downstream gates.

Owner family:

- `applicability.py`
- `applicability_adjudication.py`
- `applicability_adjudication_apply.py`
- `applicability_validation_artifacts.py`
- `applicability_validation_checks.py`
- `applicability_validation_freshness.py`
- `applicability_validation_support.py`
- `applicability_authority_family_templates.py`
- `applicability_authority_universe_builder.py`
- `applicability_authority_universe_contracts.py`
- `applicability_candidate_assembly.py`
- `applicability_contract_support.py`
- `applicability_decision_arbitration.py`
- `applicability_decision_coverage.py`
- `applicability_decision_evidence.py`
- `applicability_decision_forest_plan.py`
- `applicability_decision_outputs.py`
- `applicability_decisions.py`
- `applicability_validation.py`
- `applicability_eval.py`
- `applicability_retrieval.py`
- `applicability_rule_pack.py`
- `claim_extraction.py`
- `claim_extraction_eval.py`
- `claim_extraction_graph.py`
- `claim_extraction_runtime.py`
- `claim_extraction_validation.py`
- `rule_claim_binding.py`
- `package_fact_graph.py`
- `evidence_graph.py`

Implementation:

1. Separate decision inputs, retrieval traces, decision logic, validation/adjudication, and report
   formatting into narrower owner modules.
2. Keep rule-pack generation and rule-claim binding explicit and test-covered.
3. Split matching test files so the family can evolve without one giant test owner per subsystem.

Progress after Sequence 16 on 2026-05-20:

- `claim_extraction_runtime.py` now owns deterministic claim-pattern definitions, sentence/window
  handling, claim record assembly, IDs/hashes, and extraction metrics that previously remained
  inside `claim_extraction.py`.
- `tests/test_claim_extraction_runtime.py` now pins the extracted runtime seam directly, while
  `tests/test_claim_extraction.py` still verifies the public claim-extraction workflow end to end.
- `claim_extraction.py` is reduced to `458` lines from the post-sequence-15 `783`-line baseline,
  `claim_extraction_runtime.py` lands at `342` lines, `tests/test_claim_extraction.py` is reduced
  to `712` lines, and the fresh architecture probe reports `230` code files, `52` files above
  `800`, and no Python or JS/TS cycles.

Progress after Sequence 15 on 2026-05-20:

- `claim_extraction_validation.py` now owns claim-artifact validation, retrieval-index
  readability/loading, claim provenance/type/offset consistency checks, claim-graph integrity and
  health checks, and partial-retrieval gating that previously remained inside
  `claim_extraction.py`.
- `tests/test_claim_extraction_validation.py` now pins the extracted validation seam directly,
  while `tests/test_claim_extraction.py` still verifies the public claim-extraction workflow end
  to end.
- `tests/test_architecture_quality.py` now tightens the oversized-file guard to the fresh
  `52`-file architecture-probe baseline so the milestone does not leave a stale regression budget.
- `claim_extraction.py` is reduced to `783` lines from the post-sequence-14 `1328`-line baseline,
  `claim_extraction_validation.py` lands at `617` lines, `tests/test_claim_extraction.py` is
  reduced to `781` lines, and the fresh architecture probe reports `228` code files, `52` files
  above `800`, and no Python or JS/TS cycles.

Progress after Sequence 14 on 2026-05-20:

- `claim_extraction_eval.py` now owns deterministic claim eval scoring, legacy/current eval
  contract loading, coverage and metric-threshold checks, and claim-readiness revalidation that
  previously remained inside `claim_extraction.py`.
- `tests/test_claim_extraction_eval.py` now pins the extracted eval-contract and query/ranking seam
  directly, while `tests/test_claim_extraction.py` still verifies the public claim-extraction and
  claim-eval workflow end to end.
- `claim_extraction.py` is reduced to `1328` lines from the post-sequence-13 `2084`-line baseline,
  `claim_extraction_eval.py` lands at the `800`-line gate, and the fresh architecture probe reports
  `226` code files, `54` files above `800`, and no Python or JS/TS cycles.

Progress after Sequence 13 on 2026-05-20:

- Sequence 13 closeout commit:
  `a3363ca` (`Reduce architecture refactor Milestone 6 claim-graph seam`).

- `claim_extraction_graph.py` now owns entity extraction and aggregation, claim graph
  node/edge assembly, and the claim-graph SQLite writer/checks that previously remained inside
  `claim_extraction.py`.
- `tests/test_claim_extraction_graph.py` now pins the extracted claim-graph seam directly, while
  `tests/test_claim_extraction.py` still verifies the public claim-extraction workflow end to end.
- `claim_extraction.py` is reduced to `2084` lines from the pre-sequence `2503`-line baseline, and
  the new `claim_extraction_graph.py` seam remains below the `800`-line gate at `457` lines.
- The fresh architecture probe reports `224` code files, `54` files above `800`, and no Python or
  JS/TS cycles.

Progress after Sequence 12 on 2026-05-20:

- Sequence 12 closeout commit:
  `46d0d6b` (`Reduce architecture refactor Milestone 6 validation-facade seam`).

- `applicability_validation_artifacts.py` now owns validation artifact-path resolution, artifact
  loading, artifact-hash summary assembly, and source-set/run-id inference that previously remained
  inside `applicability_validation.py`.
- `applicability_validation_freshness.py` now owns artifact-freshness and provenance validation
  that previously remained inside `applicability_validation.py`.
- `tests/test_applicability_validation_artifacts.py` now pins the extracted artifact and
  freshness/provenance seams directly, while the existing validation-check, applicability decision,
  and adjudication tests still verify the public validation workflow end to end.
- `applicability_validation.py` is reduced to `178` lines from the post-sequence-11 `607`-line
  baseline, `applicability_validation_artifacts.py` stays at `173` lines, and
  `applicability_validation_freshness.py` stays at `304` lines.
- The fresh architecture probe reports `222` code files, `54` files above `800`, and no Python or
  JS/TS cycles.

- Sequence 11 closeout commit:
  `8493946` (`Reduce architecture refactor Milestone 6 validation-check seam`).

- `applicability_validation_checks.py` now owns the required-artifact, identity, package-fact
  validation, candidate/partition, evidence-basis, traceability, forest-plan scope,
  contradiction, and adjudication-replay checks that previously remained inside
  `applicability_validation.py`.
- `applicability_validation_support.py` now owns the shared validation candidate/status helpers,
  JSON read/write utilities, safe-segment validation, and deterministic timestamp/hash helpers used
  by the validation facade and the new validation-check owner.
- `tests/test_applicability_validation_checks.py` now pins the extracted validation-check seam
  directly, while the existing applicability decision and adjudication tests still verify the
  public validation workflow end to end.
- `applicability_validation.py` is reduced to `607` lines from the post-sequence-10 `1502`-line
  baseline, the new `applicability_validation_checks.py` seam remains below the `800`-line gate at
  `791` lines, and `applicability_validation_support.py` stays at `171` lines.
- The fresh architecture probe reports `219` code files, `54` files above `800`, and no Python or
  JS/TS cycles.

- `applicability_adjudication.py` now owns adjudication template assembly, worklist rendering,
  adjudication evaluation, and replayability item checks that previously remained inside
  `applicability_validation.py`.
- `applicability_adjudication_apply.py` now owns adjudication replay, decision-ledger rewrite,
  applicable/non-applicable partition refresh, applicability report regeneration, and provenance
  update logic that previously remained inside `applicability_validation.py`.
- `tests/test_applicability_adjudication.py` now pins the extracted adjudication seam directly,
  while the existing applicability decision tests still verify the public validation and
  adjudication workflow end to end.
- `applicability_validation.py` is reduced to `1502` lines from the pre-sequence `2494`-line
  baseline, and the new `applicability_adjudication.py` and
  `applicability_adjudication_apply.py` seams remain below the `800`-line gate at `740` and `443`
  lines.
- The fresh architecture probe reports `216` code files, `55` files above `800`, and no Python or
  JS/TS cycles.

- `applicability_decision_forest_plan.py` now owns Forest Plan component predicate evaluation that
  previously remained inside `applicability_decisions.py`.
- `applicability_decision_coverage.py` now also owns candidate-row grouping support used by the
  decision builder before per-candidate coverage evaluation.
- `tests/test_applicability_decision_forest_plan.py` now pins the extracted forest-plan predicate
  seam directly, while `tests/test_applicability_decision_coverage.py` now also covers the moved
  candidate-row grouping helper.
- `applicability_decisions.py` is reduced to `793` lines from the post-sequence-8 `916`-line
  baseline, bringing the public decision facade below the `800`-line gate; the new
  `applicability_decision_forest_plan.py` seam remains below the gate at `128` lines.
- The fresh architecture probe reports `213` code files, `55` files above `800`, and no Python or
  JS/TS cycles.

- Sequence 8 closeout commit:
  `b316e20` (`Reduce architecture refactor Milestone 6 decision-coverage seam`).
- `applicability_decision_coverage.py` now owns search-coverage boundary evaluation plus
  search-coverage certificate assembly/rationale that previously remained inside
  `applicability_decisions.py`.
- `tests/test_applicability_decision_coverage.py` now pins the extracted decision-coverage seam
  directly.
- `applicability_decisions.py` is reduced to `916` lines from the post-sequence-7 `1123`-line
  baseline, and the new `applicability_decision_coverage.py` seam remains below the `800`-line
  gate at `219` lines.
- The fresh architecture probe reports `211` code files, `56` files above `800`, and no Python or
  JS/TS cycles.

- `applicability_decision_evidence.py` now owns trigger matching, evidence-span assembly,
  source-library evidence fallback, retrieval lineage support, and decision-evidence text/window
  helpers that previously remained inside `applicability_decisions.py`.
- `tests/test_applicability_decision_evidence.py` now pins the extracted decision-evidence seam
  directly.
- `applicability_decisions.py` is reduced to `1123` lines from the post-sequence-6 `1710`-line
  baseline, and the new `applicability_decision_evidence.py` seam remains below the `800`-line gate
  at `590` lines.
- The fresh architecture probe reports `209` code files, `56` files above `800`, and no Python or
  JS/TS cycles.

- `applicability_decision_arbitration.py` now owns trigger-group normalization, rule-contract
  arbitration, missing-trigger extraction, and arbitration summary/effect assembly that previously
  remained inside `applicability_decisions.py`.
- `tests/test_applicability_decision_arbitration.py` now pins the extracted decision-arbitration
  seam directly.
- `applicability_decisions.py` is reduced to `1710` lines from the post-sequence-5 `2036`-line
  baseline, and the new `applicability_decision_arbitration.py` seam remains below the `800`-line
  gate at `349` lines.
- The fresh architecture probe reports `207` code files, `56` files above `800`, and no Python or
  JS/TS cycles.

- `applicability_decision_outputs.py` now owns decision partition records, provenance payload
  assembly, summary aggregation, and applicability report rendering that previously remained inside
  `applicability_decisions.py`.
- `tests/test_applicability_decision_outputs.py` now pins the extracted decision-output seam
  directly.
- `applicability_decisions.py` is reduced to `2036` lines from the post-sequence-4 `2374`-line
  baseline, and the new `applicability_decision_outputs.py` seam remains below the `800`-line gate
  at `375` lines.
- The fresh architecture probe reports `205` code files, `56` files above `800`, and no Python or
  JS/TS cycles.

- `applicability_authority_universe_builder.py` now owns the remaining authority-universe snapshot
  orchestration, catalog/template loading, hashing, and snapshot artifact writing that previously
  remained inside `applicability.py`.
- `tests/test_applicability_authority_universe_builder.py` now pins the extracted
  authority-universe builder and loader support seam directly.
- `applicability.py` is now a thin public authority-universe snapshot facade at `48` lines.
- The fresh architecture probe reports `203` code files, `56` files above `800`, no Python or
  JS/TS cycles, `applicability_authority_universe_builder.py` at `501` lines, and
  `applicability.py` reduced again from the post-sequence-3 `501`-line baseline to `48` lines.

- `applicability_authority_family_templates.py` now owns authority-family template candidate
  assembly, source-evidence availability, and retrieval/graph/dependency/search-coverage contract
  construction previously embedded inside `applicability.py`.
- `applicability_authority_universe_contracts.py` now owns the authority-universe snapshot
  validation checks and summary contract that previously remained inside `applicability.py`.
- `applicability_contract_support.py` now owns the shared authority-document-role, source-record,
  string-normalization, and source-record-summary helpers used by `applicability.py` and the new
  authority-family template module.
- `applicability_candidate_assembly.py` now owns rule-template and forest-plan-component candidate
  assembly plus the required package-fact, retrieval, graph-expansion, dependency, and
  search-coverage contract builders that previously remained inside `applicability.py`.
- `tests/test_applicability_authority_universe_contracts.py` now pins the extracted
  authority-universe validation and summary contract directly.
- `tests/test_applicability_candidate_assembly.py` now pins the extracted rule-template and
  forest-plan-component candidate surface directly, while the existing applicability snapshot tests
  still verify the public authority-universe behavior end to end.
- `tests/test_applicability_authority_family_templates.py` now pins the extracted authority-family
  contract surface directly, while `tests/test_applicability.py` still verifies the public
  authority-universe snapshot behavior end to end.
- The fresh architecture probe reports `201` code files, `56` files above `800`, no Python or
  JS/TS cycles, `applicability.py` reduced to `501` lines, and the new
  `applicability_authority_universe_contracts.py` and
  `applicability_candidate_assembly.py` seams remain under the `800`-line gate at `594` and `722`
  lines.

Remaining issue after closeout:

- The applicability validation family is now reduced to explicit owners, and the claim-graph,
  claim-eval, claim-validation, and claim-runtime seams are now closed, but the broader
  claims/evidence hotspot family remains open inside Milestone 6. The next routed slice advances
  to `rule_claim_binding.py`,
  `evidence_graph.py`, `package_fact_graph.py`, `applicability_retrieval.py`,
  `applicability_rule_pack.py`, and `applicability_eval.py` before the umbrella packet can route
  forward to Milestone 7.

### Milestone 7 - Split Eval And Promotion Orchestration Hotspots

Outcome label: `reduced`

Purpose: reduce concentration in the eval layer and high-fan-out orchestration surfaces.

Owner family:

- `phase_eval.py`
- `phase_eval_direct_eval.py`
- `v1_ea_eval.py`
- `promotion_suite.py`
- `upstream_evaluation.py`
- `cli_eval.py`
- `cli_derived.py`

Implementation:

1. Separate manifest loading, gate calculation, result aggregation, and CLI/report wiring.
2. Reduce broad fan-out in CLI/eval orchestrators while keeping the stable public command surface.
3. Preserve current eval semantics and historical manifest behavior.

Remaining issue after closeout:

- eval orchestration remains central, but the central owner files become smaller and their
  dependencies are more deliberate.

### Milestone 8 - Split Oversized Tests And Support Fixtures

Outcome label: `resolved`

Purpose: restore test reviewability without weakening coverage.

Implementation:

1. Split oversized test files by contract family after their corresponding runtime families are
   narrowed.
2. Split support fixtures only when the split increases ownership clarity.
3. Keep or strengthen negative-path coverage for all extracted families.

Resolved scope after closeout:

- the test suite no longer depends on a small number of giant owner files for major architecture
  families.

### Milestone 9 - Remove Mechanical Drift And Non-Hermetic Replay Debt

Outcome label: `reduced`

Purpose: close the remaining mechanical architecture debt that keeps the repo harder to reproduce
and navigate than it should be.

Implementation:

1. Replace or explicitly route the West Reservoir user-home package dependency so the proving lane
   is hermetic or clearly quarantined.
2. Reduce cold-start doc cost with a short start-here route and smaller live-routing summaries
   instead of appending more broad prose.
3. Ensure the architecture/current-state/handoff docs point at the same canonical next-step truth.

Remaining issue after closeout:

- some historical append-only context will remain by policy, but current routing and proving truth
  are concise, canonical, and reproducible.

### Milestone 10 - Final Architecture Rebaseline And Closeout

Outcome label: `resolved`

Purpose: prove that the full umbrella plan reduced architecture debt without shifting it elsewhere.

Implementation:

1. Re-run the architecture probe and compare against the Milestone 0 baseline.
2. Re-run debt, architecture, CLI, and family-focused tests.
3. Re-read the top routed docs and ensure they agree on the current live state.
4. Record final counts, residual risks, and remaining owner-family backlog in
   `docs/SESSION_HANDOFF.md`.

Resolved scope after closeout:

- this umbrella plan is complete and the remaining debt, if any, is explicitly rerouted into
  narrower owner-family packets rather than left implicit.

## Required Implementation Artifacts

- a fresh architecture-quality gate or equivalent probe-driven contract for size/fan-out drift;
- canonical architecture-doc routing;
- the completed agent entrypoint packet artifacts;
- narrower owner modules for each hotspot family that is split;
- focused regression tests proving no weakened protection;
- updated plan/handoff/current-state docs for each closed milestone; and
- any required replay-context or proving-lane artifacts needed to remove the West Reservoir
  user-home dependency.

## Required Documentation And Handoff Updates

Every implementation milestone under this umbrella must update the relevant subset of:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/TECH_DEBT_REGISTER.md`
- this plan
- any narrower follow-on plan spawned from this umbrella
- `docs/SESSION_HANDOFF.md`

At minimum, each milestone closeout must state:

- outcome label `resolved` or `reduced`;
- exact verification commands run;
- current hotspot or fan-out change for the owner family;
- whether any residual risk remains and where it is routed next.

## Required Verification Gates

Baseline gates for all architecture-refactor milestones:

```bash
git status -sb
PYTHONPATH=src .venv/bin/python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py . --max-file-lines 800 --format markdown
PYTHONPATH=src .venv/bin/python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py . --max-fan-out 20 --format markdown
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev pytest tests/test_debt_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Milestone-specific additions:

- Milestone 2:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_document_plan.py tests/test_cli.py -q`
  and
  `PYTHONPATH=src python -m usfs_r1_ea_sources --help`
- Milestones 3-7:
  the focused owner-family tests plus the architecture probe readback for the changed family
- Milestone 8:
  the split test families plus the owning runtime family tests
- Milestone 9:
  the focused proving/eval commands and docs readback that prove the West Reservoir dependency is
  removed or explicitly quarantined

If a milestone touches CLI routing, architecture boundaries, or generated artifact ownership, the
matching contract tests and durable docs must be updated in the same slice.

## Acceptance Criteria

This umbrella plan is complete only when all milestone closeouts pass and the final rebaseline shows
all of the following:

- no Python or JS/TS import cycles;
- `tests/test_architecture_contract.py` is green;
- `tests/test_debt_contract.py` is green;
- the agent entrypoint packet is either fully closed or explicitly retired in favor of a better
  routed surface;
- the repo has one canonical architecture doc path and one short cold-start doc path;
- the proving lane truth no longer depends on an undeclared user-home package path for required repo
  verification;
- the large-file count above `800` lines is reduced from the current baseline of `57` to `45` or
  fewer;
- no milestone increased the top hotspot score or fan-out in its owner family without an explicit,
  documented, and green follow-on gate; and
- every remaining residual hotspot is explicitly routed in durable docs rather than left as implied
  debt.

## Stop Conditions

- Stop if the current document-plan lane is still overlapping the owner surfaces for a broad
  architecture milestone.
- Stop if a proposed split requires weakening tests or introducing new untracked debt markers.
- Stop if a milestone needs broad corpus regeneration or network-heavy reproving that is outside the
  scoped owner family.
- Stop if current-state docs, handoff routing, and live code disagree and the milestone would have
  to guess which truth is authoritative.
- Stop if a family split starts generating a new vague shared helper dumping ground.
- Stop if a proving-lane claim depends on local machine state that cannot be refreshed or isolated
  inside the repo's declared contract.

## Local Commit Closeout Policy

- Do not treat a milestone as complete until its code, tests, docs, and handoff updates are all
  committed together in one local atomic commit.
- Stage only the verified milestone slice.
- Do not commit unrelated pre-existing worktree changes.
- Use `resolved` only when the milestone's scoped issue is actually closed by the governing gate or
  artifact.
- Use `reduced` only when the remaining issue is named explicitly and routed to the next owner
  milestone.

## Residual Risks And Next Routing

- Milestone 2 is already closed through the separate agent-entrypoint packet and should remain
  treated as historical closeout state, not reopened inside later hotspot milestones.
- The largest runtime families are big enough that several of the milestones above may need
  narrower subplans before implementation begins.
- The repo's append-only handoff policy is useful, but it means doc-routing cleanup must be
  deliberate and ongoing rather than one-time.
- The next bounded slice after this closeout is Milestone 6 on the applicability, claims, and
  evidence hotspot family.
