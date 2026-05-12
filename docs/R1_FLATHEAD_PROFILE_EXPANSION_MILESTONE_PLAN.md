# Region 1 Flathead Profile Expansion Milestone Plan

Date: 2026-05-11
Status: implemented on 2026-05-11
Owner context: active next single-forest post-V1 expansion milestone for making Flathead reviewer-ready
for forest-plan-aware EA review on the active full-canonical corpus

## Closeout

This milestone is now implemented against a tracked proving-fixture path.

- outcome:
  `flathead-nf` is now a configured Milestone 5 added active profile, carries the full 17-row
  register-backed support/currentness contract in tracked config, resolves district/geographic
  area/focused-recreation/overlay/currentness/support-route context, and passes selected-profile
  resolver plus compliance-review proofs
- proving surface:
  closeout used tracked synthetic proving fixtures in
  `tests/test_forest_plan_resolver.py` and `tests/test_compliance_review.py`, not a live local
  Flathead EA package
- verification:
  `python -m json.tool config/forest_plan_profiles.json`,
  `python -m json.tool config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_cli.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src python -m compileall src`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  and `git diff --check` all passed on 2026-05-11
- downstream alignment:
  the live graph export now reports `region1_forest_plan_added_profile_count=2`,
  `region1_forest_plan_added_profiles_with_eval_fixture_count=2`, and
  `region1_forest_plan_blocked_profile_count=0`
- residual risk:
  this is still weaker than a closeout backed by a real local Flathead EA package, so the next
  forest-specific expansion lane should preserve the distinction between tracked-fixture proof and
  live-package proof

## Purpose

Flathead is the strongest next single-forest candidate after Beaverhead-Deerlodge because its
inventory and source-set support are already materially green, but the reviewer-facing resolver and
compliance path are not yet complete.

This milestone exists to close all remaining Flathead-specific work needed to make the Flathead
forest plan and supporting-plan document set complete in tracked config, promote Flathead from
tracking-only status into a reviewer-ready configured profile, and prove that a Flathead-selected
review can resolve project context and review EA documents on the Flathead without weakening the
default Custer path.

## Baseline Evidence At Plan Authoring

- `docs/CURRENT_SYSTEM_STATE.md` says the active full-canonical source set is
  `source-set-5e65d845ce77e1a0`, and Flathead already has a validated component inventory with
  `80` components and `20` standards.
- `config/region1_forest_plan_readiness_nepa_3d_v1.json` currently marks Flathead as
  `profile_kind="region1_tracking_only"`, `graph_promotion_status="promoted"`,
  `readiness_blockers=[]`, and `applicability_eval_coverage.status="not_started"`. Flathead is not
  yet a reviewer-ready configured profile even though its inventory is validated.
- `docs/CURRENT_SYSTEM_STATE.md` still lists Flathead as a retrieval-ready tracking-only row rather
  than a configured reviewer-ready profile.
- `config/r1_forest_plan_document_register_draft.csv` already tracks `17` Flathead rows across the
  full supporting-plan set:
  `6` core rows (`02`, `03`, `04`, `06`, `07`, `16`),
  `7` supporting rows (`05`, `08`, `11`, `12`, `13`, `14`, `15`), and
  `4` currentness rows (`01`, `09`, `10`, `17`).
- `config/forest_plan_profiles.json` currently exposes only `10` Flathead roles in the live
  profile: `01`, `02`, `03`, `04`, `05`, `06`, `07`, `10`, `12`, and `16`. The profile still omits
  `08` monitoring program, `09` latest BMER, `11` ROD cover letter, `13` FEIS volume 3 forest-plan
  amendments, `14` and `15` map appendices, and `17` BMER release letter.
- The same Flathead profile still has empty `ranger_district_terms`,
  `geographic_area_terms`, `management_area_terms`, `overlay_terms`, and
  `supporting_record_trigger_rules`, so resolver depth is effectively unimplemented.
- `docs/SESSION_HANDOFF.md` records that `R1PLAN-flathead-nf-02` is already classified as
  `document_role=forest_plan`, isolated single-forest inventory runs passed for Flathead, and a
  live Flathead Box preflight smoke passed for the primary plan PDF.
- Tracked tests do not yet prove a Flathead resolver/compliance path. Current test hits only show a
  generic CLI query string, not Flathead profile, resolver, or compliance-review coverage.
- No tracked Flathead EA review proving fixture is currently called out in docs or tests. The
  reviewer-ready claim is therefore incomplete until this milestone defines and proves one.

## Goal

Make `flathead-nf` reviewer-ready for forest-plan-aware EA review by completing the Flathead
supporting-plan document contract, enriching the Flathead resolver profile to full project-context
depth, promoting Flathead out of tracking-only status, and proving a Flathead-selected review path
against a Flathead EA package or tracked proving fixture.

## Non-Goals

- Do not widen this plan into a multi-forest roster implementation ask.
- Do not reopen downloader, catalog, source-delta capture, extraction, parser recovery, or replay
  work unless Flathead verification proves a real dependency.
- Do not weaken default Custer Gallatin behavior, ambiguity handling, or out-of-scope handling to
  make Flathead appear ready.
- Do not stage or commit `source_library/` generated artifacts unless repository policy changes or
  the user explicitly expands scope.
- Do not claim broader any-R1 reviewer readiness from a Flathead-only closeout.
- Do not silently defer missing Flathead support-document roles by leaving them outside tracked
  config.

## Scope

- `config/r1_forest_plan_document_register_draft.csv`
- `config/forest_plan_profiles.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `src/usfs_r1_ea_sources/forest_plan_profiles.py`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/compliance_review_eval.py`
- `src/usfs_r1_ea_sources/compliance_gold_eval.py`
- `src/usfs_r1_ea_sources/compliance_validation.py`
- `src/usfs_r1_ea_sources/cli_compliance.py`
- `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py` only if needed for Flathead readiness or
  profile-kind promotion surfaces
- focused tests under `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`, `tests/test_compliance_review.py`, `tests/test_cli.py`,
  `tests/test_nepa_knowledge_graph_export.py`, and `tests/test_architecture_contract.py`
- tracked Flathead EA proving fixtures if needed under the repo's existing test or config fixture
  surfaces
- durable docs and handoff updates for the Flathead milestone

## Out Of Scope

- Beaverhead, Bitterroot, Dakota Prairie, Helena-Lewis-and-Clark, Idaho Panhandle, Kootenai, Lolo,
  or Nez Perce-Clearwater expansion work
- `source_library/` bulk regeneration beyond milestone-required verification
- workbook row edits unrelated to Flathead completeness proof
- unrelated viewer work
- East Crazies replay repairs
- new authority, applicability, or rule-pack milestones outside the Flathead profile lane

## Owner Surfaces

- Flathead support-document completeness contract:
  `config/r1_forest_plan_document_register_draft.csv`,
  `config/forest_plan_profiles.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- Flathead profile parsing and validation:
  `src/usfs_r1_ea_sources/forest_plan_profiles.py`
- Flathead scope, district, geography, management-area, overlay, map, currentness, and
  supporting-route resolution:
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- Flathead selected-profile compliance gate ownership:
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/compliance_validation.py`,
  `src/usfs_r1_ea_sources/cli_compliance.py`
- Flathead readiness and reviewer-status routing:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  `tests/test_nepa_knowledge_graph_export.py`
- Regression and prevention surface:
  `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`,
  `tests/test_cli.py`,
  `tests/test_nepa_knowledge_graph_export.py`,
  `tests/test_architecture_contract.py`
- Status routing:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, this plan, and `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep Flathead-specific knowledge in tracked config, not in new runtime branches.
- Keep runtime logic generic and profile-driven. Do not add
  `if forest_unit_id == "flathead-nf"` control flow unless the logic is reusable and config-backed.
- Treat the register as the full Flathead source-completeness authority and the profile as the
  reviewer-path contract built on top of that authority.
- Every Flathead support document that matters to reviewer-ready behavior must be explicit in
  tracked config. If a document is not a reviewer-ready gate, keep it explicit as a supporting or
  currentness role rather than omitting it.
- Keep the proving package/fixture explicit and reusable. Do not claim reviewer-ready Flathead
  review from generic unit tests alone.
- Future forest-specific plans should copy this Flathead structure one forest at a time rather than
  reopening a shared roster-wide plan.

## Weak-Point Prevention Contract

### Weak point 1: Flathead completeness is claimed while seven tracked support/currentness rows remain outside the profile

- Weak point forecast: a future closeout may keep only the current 10-role readiness subset and
  still claim Flathead support-document completeness.
- Owner surface: `config/r1_forest_plan_document_register_draft.csv`,
  `config/forest_plan_profiles.json`, `tests/test_forest_plan_profiles.py`
- Prevention gate: Flathead profile completeness assertions against the register-backed 17-row
  contract
- Fail threshold: any Flathead row from `01` through `17` that is required for the milestone scope
  is still absent from tracked Flathead profile role ownership
- Controlled violation: tests fail if roles `08`, `09`, `11`, `13`, `14`, `15`, or `17` remain
  unrepresented after the milestone claims completeness
- Future-Codex misuse scenario: a future session keeps only the easiest readiness roles and calls
  the profile done; this milestone prevents that by making the omitted rows a tracked failing gate

### Weak point 2: Resolver depth remains empty while profile ownership looks complete on paper

- Weak point forecast: Flathead may gain source-role completeness but still lack districts,
  geographic areas, management areas, overlays, and trigger rules.
- Owner surface: `config/forest_plan_profiles.json`, `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`
- Prevention gate: Flathead completeness and resolver tests
- Fail threshold: any required Flathead vocabulary class or trigger route remains empty at closeout
- Controlled violation: profile tests fail if Flathead still has empty district, geography,
  management-area, overlay, or trigger arrays
- Future-Codex misuse scenario: a future session updates source roles only and reports reviewer
  readiness; this milestone requires resolver-depth categories to be explicit and non-empty

### Weak point 3: Broad Flathead terms overmatch background references or non-project context

- Weak point forecast: "Flathead" or generic FEIS/ROD/BA/BO terms may trigger support evidence
  without real project-context grounding.
- Owner surface: `config/forest_plan_profiles.json`, `forest_plan_resolver.py`,
  `tests/test_forest_plan_resolver.py`
- Prevention gate: Flathead positive and negative resolver fixtures
- Fail threshold: background-only mentions, lowercase acronyms, generic decision labels, or generic
  monitoring text resolve Flathead supporting-plan evidence that should remain unresolved
- Controlled violation: explicit negative fixtures for background-only Flathead references, generic
  "selected alternative" language, lowercase acronyms, and unsupported currentness cues
- Future-Codex misuse scenario: a future session broadens Flathead trigger terms to force
  completeness; this milestone preserves fail-closed trigger tests

### Weak point 4: Flathead becomes reviewer-ready without a proving EA review path

- Weak point forecast: the milestone may stop at config plus unit tests without proving a
  Flathead-selected review can actually review an EA package.
- Owner surface: proving fixture/package surface, `tests/test_compliance_review.py`,
  `tests/test_cli.py`, this plan
- Prevention gate: a required Flathead proving review fixture or package contract plus review-path
  verification
- Fail threshold: no Flathead proving package or tracked review fixture exists, or the Flathead
  review path never reaches a reviewer-ready pass signal
- Controlled violation: if the proving package/fixture is missing or insufficient, stop the
  milestone and reroute instead of claiming reviewer-ready status
- Future-Codex misuse scenario: a future session closes from profile data and synthetic snippets
  only; this milestone requires an end-to-end Flathead review proof

### Weak point 5: The compliance gate becomes weaker while promoting Flathead beyond tracking-only

- Weak point forecast: Flathead may be promoted to configured status without strict component and
  adjudication requirements.
- Owner surface: `compliance_validation.py`, `tests/test_compliance_review.py`,
  `tests/test_cli.py`
- Prevention gate: Flathead selected-profile compliance-review regressions and CLI coverage
- Fail threshold: a Flathead-selected review passes while its component/adjudication gate is
  unresolved or missing
- Controlled violation: keep or add tests where Flathead lacks matching component or adjudication
  evidence and must fail closed
- Future-Codex misuse scenario: a future session changes status routing to make Flathead look ready
  without strict review gates; this milestone preserves selected-profile parity

### Weak point 6: Flathead readiness surfaces drift while code/tests are green

- Weak point forecast: Flathead may be promoted in config or docs without aligning readiness/graph
  export surfaces and current-state routing.
- Owner surface: `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `tests/test_nepa_knowledge_graph_export.py`, `docs/CURRENT_SYSTEM_STATE.md`
- Prevention gate: readiness-config assertions, graph-export tests, and live verification when
  readiness surfaces change
- Fail threshold: Flathead remains `region1_tracking_only`, or the readiness/graph export surfaces
  disagree with the milestone closeout claim
- Controlled violation: tests fail if a promoted Flathead profile is still emitted as tracking-only
  or if readiness metadata is inconsistent
- Future-Codex misuse scenario: a future session updates only prose and not the machine-readable
  readiness surfaces; this milestone keeps promotion truth executable

### Weak point 7: A Flathead-only milestone closes without live all-R1 verification

- Weak point forecast: Flathead work may close from focused tests alone while another forest-plan
  inventory surface has drifted.
- Owner surface: `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Prevention gate: mandatory live `forest-plan-components-build` replay before closeout
- Fail threshold: the all-R1 inventory command does not validate all `10` tracked forest plans on
  the active full-canonical source set at closeout time
- Controlled violation: if the active source set drifts or any profile build fails, stop the
  milestone and reroute to the blocker instead of committing a partial Flathead closeout
- Future-Codex misuse scenario: a future session claims the Flathead slice is done from focused
  tests only; this milestone preserves the live all-R1 closeout requirement

## Milestone Sequence

### Sequence 0: Add the Flathead completeness and proving-package contract

Outcome label: resolved

- Add or tighten tests that define what Flathead reviewer-ready completion means.
- Require the Flathead profile contract to cover the full milestone-scoped source set:
  `17` tracked Flathead rows with explicit role ownership and explicit distinction between
  reviewer-required, supporting, and currentness-only documents.
- Guard against premature reviewer-ready claims by keeping Flathead readiness surfaces in
  tracking-only status until resolver depth, compliance parity, and the proving-review gate are
  actually implemented.
- Name the proving review surface up front: either a selected local Flathead EA package path or a
  tracked Flathead review fixture that is sufficient to prove reviewer-ready behavior.

Required implementation artifacts:

- Flathead completeness tests in `tests/test_forest_plan_profiles.py`
- Flathead readiness or promotion assertions in `tests/test_nepa_knowledge_graph_export.py`
- if needed, helper assertions in `forest_plan_profiles.py` or test helpers only

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_nepa_knowledge_graph_export.py`

### Sequence 1: Complete the Flathead support-document contract in tracked config

Outcome label: resolved

- Extend `config/forest_plan_profiles.json` so the Flathead profile explicitly owns all
  milestone-scoped support and currentness roles, not just the current 10-role readiness subset.
- Bring the currently omitted Flathead roles into tracked profile ownership:
  `forest_plan_monitoring_program`,
  `latest_biennial_monitoring_evaluation_report`,
  `record_of_decision_cover_letter`,
  `final_environmental_impact_statement_volume_3`,
  `feis_map_appendix_part_1`,
  `feis_map_appendix_part_2`, and
  `bmer_release_letter`.
- Keep the distinction between strict reviewer-ready roles and broader supporting/currentness roles
  explicit instead of flattening everything into one mandatory list.
- Do not promote Flathead's readiness row out of `region1_tracking_only` in this sequence. That
  promotion belongs only after resolver depth, compliance parity, and a Flathead-selected proving
  review actually pass.

Required implementation artifacts:

- `config/forest_plan_profiles.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/r1_forest_plan_document_register_draft.csv` only if the live Flathead role inventory
  itself needs correction
- if needed, small validation helpers in `forest_plan_profiles.py`

Required verification:

- `python -m json.tool config/forest_plan_profiles.json >/dev/null`
- `python -m json.tool config/region1_forest_plan_readiness_nepa_3d_v1.json >/dev/null`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_nepa_knowledge_graph_export.py`

### Sequence 2: Enrich Flathead resolver vocabulary and support routes

Outcome label: resolved

- Author Flathead district aliases, named geographic areas, management areas, overlays, and
  explicit support-document trigger routes from active local plan/support evidence.
- Add source-backed routing for FEIS, ROD, ESA, administrative-change, monitoring/currentness, and
  map/location support where the document set justifies them.
- Keep currentness and monitoring routes fail-closed; do not resolve them from generic plan-review
  language alone.

Required implementation artifacts:

- `config/forest_plan_profiles.json`
- only minimal generic resolver changes needed to support Flathead config-driven behavior

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py`

### Sequence 3: Prove Flathead resolver behavior

Outcome label: resolved

- Add focused Flathead resolver fixtures covering positive and negative cases.
- Prove Flathead can:
  - resolve selected forest scope from package text
  - resolve at least one district or project-location signal
  - resolve at least one geographic area, management area, or overlay
  - use map/location support where explicit project-location cues warrant it
  - route FEIS, ROD, ESA, and currentness/supporting evidence only when explicit package cues exist
- Prove Flathead still fails closed on ambiguity, background-only references, generic decision
  labels, generic monitoring language, and unselected profile references.

Required implementation artifacts:

- `tests/test_forest_plan_resolver.py`
- only minimal generic resolver changes needed to support Flathead config-driven behavior

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py`

### Sequence 4: Prove Flathead compliance-gate and CLI parity

Outcome label: resolved

- Add compliance-review fixtures proving a Flathead-selected profile is gate-required and cannot
  pass without reviewer-ready component and adjudication evidence.
- Retain existing Custer and Beaverhead proofs while adding Flathead selected-profile cases.
- Add CLI coverage proving the Flathead profile can be explicitly selected without changing default
  Custer behavior.
- Keep ambiguous and out-of-scope paths non-required.

Required implementation artifacts:

- `tests/test_compliance_review.py`
- `tests/test_cli.py`
- only generic compliance-path changes needed for Flathead selected-profile parity

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_cli.py tests/test_architecture_contract.py`

### Sequence 5: Prove Flathead reviewer-ready EA review

Outcome label: resolved if a Flathead proving review path passes reviewer-ready; reduced if only
profile depth closes but no credible Flathead EA proving package is available

- Establish the milestone's Flathead proving surface:
  - prefer an existing local Flathead EA package if one is available and in scope; otherwise
  - create a tracked Flathead review fixture that is rich enough to prove district, geography,
    management-area or overlay, FEIS/ROD/ESA, and currentness support routing
- Run the Flathead-selected review path against that proving surface.
- If that proving path passes reviewer-ready, promote Flathead's readiness row out of
  `region1_tracking_only` and record the proving coverage contract in tracked config and docs.
- Close this sequence as `resolved` only if the Flathead-selected review reaches a reviewer-ready
  pass signal with citation-bearing forest-plan context and strict component/adjudication gating.

Required implementation artifacts:

- tracked Flathead proving fixture or documented local package contract
- `tests/test_compliance_review.py`
- any minimal fixture helpers required by the existing review test surfaces

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_cli.py`
- if the milestone uses a local package or tracked runtime smoke, record the exact command and pass
  signal in `docs/SESSION_HANDOFF.md`

### Sequence 6: All-R1 verification and Flathead closeout alignment

Outcome label: resolved for the Flathead reviewer-ready profile-depth and review-path claim,
reduced for the broader any-R1 expansion claim

- Re-run the live all-R1 forest-plan inventory verification on the active full-canonical source set
  before closing the Flathead milestone.
- If Flathead readiness or profile-kind surfaces changed, verify the live NEPA knowledge-graph
  export still validates and reflects the promoted Flathead state.
- Refresh current-state docs, this plan, and the session handoff with the actual post-closeout
  state and next routing.
- Route the next step to a new forest-specific plan file rather than widening Flathead's artifact.

Required implementation artifacts:

- refreshed status docs only if the verified live state materially changed

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_cli.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`
- `git diff --check`

Closeout interpretation:

- This milestone is `resolved` only if Flathead becomes reviewer-ready for forest-plan-aware EA
  review under a selected Flathead proving surface.
- The broader post-V1 "any R1 EA package review" problem remains `reduced` until future
  forest-specific milestones and proving reviews close their own gates.

## Required Documentation And Handoff Updates

Before milestone closeout, update as applicable:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

The handoff update must record:

- the completed Flathead milestone name
- exact verification commands
- pass/fail counts
- the active source set used for all-R1 verification
- whether the proving review used a local Flathead EA package or a tracked fixture
- residual risks
- the next forest-specific milestone boundary
- the closing commit hash

## Required Verification Gates

Focused code and contract verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_architecture_contract.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_nepa_knowledge_graph_export.py`

Repository hygiene:

- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`

Mandatory live Flathead and all-R1 verification before closeout:

- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`
- acceptance signal: the build must validate all `10` tracked forest plans, and the export must
  reflect Flathead's promoted reviewer-ready state without failing graph validation

Optional but recommended if readiness or expansion-reporting surfaces materially change:

- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`

## Acceptance Criteria

- The Flathead plan/support contract is explicit and complete in tracked config:
  `17` Flathead register rows are represented with explicit role ownership, and the current omitted
  rows `08`, `09`, `11`, `13`, `14`, `15`, and `17` are no longer outside the profile-owned
  contract.
- Flathead has explicit non-empty district, geographic-area, management-area, overlay, and
  supporting-route data in `config/forest_plan_profiles.json`.
- Flathead is no longer `region1_tracking_only`; its readiness metadata reflects the reviewer-ready
  state actually proven by the milestone.
- Resolver tests prove Flathead selected-profile scope resolution, routed supporting evidence,
  project-location resolution, and ambiguity/out-of-scope failures.
- Compliance-review and CLI tests prove Flathead selected-profile review keeps
  `forest_plan_component_gate_reviewer_ready` strict and cannot pass without reviewer-ready
  component and adjudication support.
- A Flathead-selected proving review path reaches a reviewer-ready pass signal against a tracked
  Flathead package or proving fixture.
- The default Custer path remains compatible and green.
- The all-R1 forest-plan verification command validates all `10` tracked forest plans on the active
  full-canonical source set before closeout.
- Durable docs and the session handoff reflect the real post-closeout Flathead state and the next
  single-forest routing boundary.
- The milestone closes with one local atomic commit containing only the verified Flathead slice.

## Stop Conditions

- A needed Flathead support document, vocabulary set, or trigger cannot be grounded in the active
  local corpus and would require unsupported guessing.
- Flathead reviewer-ready behavior requires forest-specific runtime branching that cannot be
  expressed cleanly through config.
- No credible Flathead EA proving package or sufficient proving fixture can be established for the
  end-to-end review claim.
- The active source set or full-R1 inventory verification drifts in a way that reopens parser,
  extraction, or corpus-readiness work outside Flathead's boundary.
- Required verification fails.
- Unrelated dirty work cannot be safely separated from the Flathead slice.

## Local Commit Closeout Policy

- Stage only the verified Flathead milestone slice.
- Leave unrelated viewer changes, draft exports, and other dirty or untracked files alone.
- Include implementation, tests, plan updates, current-state updates, and handoff updates in the
  same local atomic commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until that commit exists.

## Residual Risks And Next Routing

- Flathead reviewer readiness does not imply the remaining forests can be promoted without their own
  support-document, vocabulary, and proving-review work.
- A Flathead closeout based on a tracked proving fixture is still weaker than a closeout backed by a
  high-trust local Flathead EA package; preserve that distinction in the handoff if it applies.
- If this milestone closes green, the next milestone should be a new forest-specific plan file for
  one selected remaining non-Custer forest, using the Flathead and Beaverhead sequences as the
  baseline rather than widening either document.
