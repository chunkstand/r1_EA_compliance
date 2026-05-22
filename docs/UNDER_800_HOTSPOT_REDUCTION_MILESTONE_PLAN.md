# Under-800 Hotspot Reduction Milestone Plan

Date: 2026-05-21

Status: Milestone `0` resolved 2026-05-21 through live baseline recheck; Milestone `1` resolved
2026-05-21 through exact oversized-file inventory gate hardening; next routed slice Milestone `2`
for the Project SOW package family

Owner context: The resolved umbrella architecture packet closed at a count-only large-file guard of
`24` code files above `800` lines. This follow-on packet resolves the remaining repo-wide
reviewability debt by driving the live oversized-file inventory to `0` without reopening the
resolved umbrella, weakening tests, or hiding new hotspots behind count-only gates. The repo's
default active implementation packet remains
`docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; this architecture packet is a
queued explicit follow-on, not the default active route.

## Purpose

Resolve the remaining large-file and hotspot concentration debt after the umbrella architecture
closeout. The immediate weakness is no longer missing architecture direction. The weakness is that:

- `24` live code files still exceed the repo's `800`-line reviewability threshold;
- the current architecture quality gate ratchets only the total oversized-file count, so hotspot
  substitution can occur without reopening the resolved umbrella; and
- the current dirty worktree overlaps one of the remaining oversized families
  (`compliance_review_eval.py`), so future implementation must start with isolation rather than
  pretend the baseline is clean.

## Current Evidence

### Live baseline

- `git status -sb` at the Milestone `0` recheck now shows only this packet's planning slice:
  `docs/CURRENT_ROUTING.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
  The earlier planning-time compliance/eval overlap is now historical context, not a current
  blocker for Milestone `1`.
- Fresh architecture probe
  (`python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20`)
  reports `344` code files, `24` code files above `800` lines, no Python cycles, no JS/TS cycles,
  no local module above the `20`-import fan-out gate, and top hotspot
  `src/usfs_r1_ea_sources/project_sow_package.py` at score `104370`.
- `tests/test_architecture_quality.py` currently enforces only
  `MAX_ALLOWED_OVERSIZED_FILES = 24`. That guard fails if the count grows, but it does not fail
  when one closed owner family grows back above `800` and another file drops below `800`.
- `config/architecture_large_file_inventory_v1.json` is the governed Milestone `1` inventory
  surface that must replace count-only large-file routing with exact path membership.
- The resolved umbrella plan remains historically correct for its closeout point, but it is no
  longer a sufficient live routing surface for oversized-file ownership because the exact live
  inventory has shifted while the count stayed flat at `24`.

### Exact live oversized-file inventory

| Family | Live files over `800` lines |
| --- | --- |
| Project SOW package | `4970` `src/usfs_r1_ea_sources/project_sow_package.py` |
| Knowledge graph and decision support | `4837` `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`; `3306` `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`; `988` `src/usfs_r1_ea_sources/nepa_3d_graph_contract.py` |
| Forest-plan runtime | `4279` `src/usfs_r1_ea_sources/forest_plan_components.py`; `1829` `src/usfs_r1_ea_sources/forest_plan_resolver.py`; `1770` `src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py`; `997` `src/usfs_r1_ea_sources/forest_plan_component_adjudication.py`; `886` `src/usfs_r1_ea_sources/forest_plan_component_eval.py` |
| Extraction, retrieval, and review artifacts | `3170` `src/usfs_r1_ea_sources/extract.py`; `2442` `src/usfs_r1_ea_sources/final_qa_certification.py`; `1956` `src/usfs_r1_ea_sources/draft_generation.py`; `1922` `src/usfs_r1_ea_sources/retrieval.py`; `1307` `src/usfs_r1_ea_sources/review_packet_index.py` |
| Capture, catalog, and source-register | `1496` `src/usfs_r1_ea_sources/catalog.py`; `1347` `src/usfs_r1_ea_sources/authority_currentness.py`; `1181` `src/usfs_r1_ea_sources/source_register_proving.py`; `1064` `src/usfs_r1_ea_sources/source_register.py`; `914` `src/usfs_r1_ea_sources/download.py`; `859` `src/usfs_r1_ea_sources/preflight.py` |
| Compliance and eval | `1714` `src/usfs_r1_ea_sources/compliance_review_eval.py`; `1686` `src/usfs_r1_ea_sources/compliance_outputs.py`; `824` `src/usfs_r1_ea_sources/compliance_validation.py` |
| Viewer | `2547` `viewer/nepa-3d/app.js` |

### Architecture gate blind spot

The next architecture milestone cannot start by splitting a large file directly. The first live
weak point is governance drift:

- the current count-only gate does not encode the exact oversized-file set;
- the current test couples live closeout truth to the resolved umbrella plan rather than to an
  explicit queued follow-on register; and
- future Codex sessions could close a family milestone while silently shifting the hotspot into a
  new `>800` helper module or a different previously-green file.

Milestone `1` in this packet exists to close that blind spot before any large-file work starts.

## Goal

Drive the live oversized-file inventory from `24` to `0` while preserving:

- current public CLI command names;
- workbook, catalog, and generated-artifact contracts;
- architecture contract direction and no-cycle status;
- active review, compliance, and eval semantics; and
- the repo's current fail-closed governance style.

## Non-Goals

- Do not reopen the resolved umbrella packet as if it were the active implementation lane.
- Do not absorb the active full-canonical compliance-gold packet into this architecture plan.
- Do not weaken tests, add skips, loosen assertions, or relax architecture gates to make line
  counts look green.
- Do not regenerate the full corpus or run broad network workflows just to prove a refactor.
- Do not introduce generic dumping-ground modules such as `helpers2.py`, `misc.py`, or unlabeled
  `support.py` files that merely move the hotspot.
- Do not stage `source_library/` outputs unless repo policy changes explicitly.

## Scope

In scope:

- the exact live `24`-file oversized inventory above;
- architecture gate hardening for exact oversized-file membership and no-substitution ratchets;
- owner-family splits that reduce every current `>800` code file to `<=800`;
- matching `docs/architecture_contract.toml`, focused boundary tests, and durable routing updates;
- viewer modularization only to the extent required to get `viewer/nepa-3d/app.js` under `800`
  lines without changing viewer behavior.

Out of scope:

- broader forest-plan, compliance-gold, or corpus-promotion behavior changes not required by the
  split;
- redesign of the viewer experience;
- package-path or environment cleanup unrelated to the oversized-file lane;
- large historical doc rewrites beyond the routing and closeout docs required by this packet.

## Owner Surfaces

| Family | Primary owner files | Focused verification surfaces |
| --- | --- | --- |
| Project SOW package | `project_sow_package.py` | `tests/test_project_sow_package.py`, `tests/test_project_sow_package_validation.py`, `tests/test_project_sow_adjudication.py`, `tests/test_project_sow_intake.py`, `tests/test_project_sow_package_test_boundary.py` |
| Knowledge graph and decision support | `nepa_knowledge_graph_export.py`, `ea_consistency_decision_support.py`, `nepa_3d_graph_contract.py` | `tests/test_nepa_knowledge_graph_export.py`, `tests/test_nepa_knowledge_graph_export_review.py`, `tests/test_nepa_knowledge_graph_export_readiness.py`, `tests/test_nepa_knowledge_graph_export_test_boundary.py`, `tests/test_nepa_3d_graph_contract.py`, `tests/test_ea_consistency_decision_support.py`, `tests/test_ea_consistency_decision_support_report.py`, `tests/test_ea_consistency_decision_support_validation.py`, `tests/test_ea_consistency_decision_support_test_boundary.py` |
| Forest-plan runtime | `forest_plan_components.py`, `forest_plan_resolver.py`, `forest_plan_source_delta_readiness.py`, `forest_plan_component_adjudication.py`, `forest_plan_component_eval.py` | `tests/test_forest_plan_components.py`, `tests/test_forest_plan_components_manifest.py`, `tests/test_forest_plan_components_inventory.py`, `tests/test_forest_plan_components_coverage.py`, `tests/test_forest_plan_components_test_boundary.py`, `tests/test_forest_plan_resolver.py`, `tests/test_forest_plan_resolver_profiles.py`, `tests/test_forest_plan_resolver_scope.py`, `tests/test_forest_plan_resolver_test_boundary.py`, `tests/test_forest_plan_source_delta_readiness.py`, `tests/test_forest_plan_component_adjudication.py`, `tests/test_forest_plan_component_eval.py`, `tests/test_forest_plan_component_eval_coverage.py`, `tests/test_forest_plan_component_retrieval_eval.py` |
| Extraction, retrieval, and review artifacts | `extract.py`, `final_qa_certification.py`, `draft_generation.py`, `retrieval.py`, `review_packet_index.py` | `tests/test_extract.py`, `tests/test_extract_reuse.py`, `tests/test_extract_pdf_fallbacks.py`, `tests/test_extract_test_boundary.py`, `tests/test_final_qa_certification.py`, `tests/test_final_qa_certification_report.py`, `tests/test_final_qa_certification_validation.py`, `tests/test_final_qa_certification_test_boundary.py`, `tests/test_draft_generation.py`, `tests/test_draft_generation_eval.py`, `tests/test_retrieval.py`, `tests/test_retrieval_validation.py`, `tests/test_retrieval_eval.py`, `tests/test_retrieval_test_boundary.py`, `tests/test_review_packet_index.py` |
| Capture, catalog, and source-register | `catalog.py`, `authority_currentness.py`, `source_register_proving.py`, `source_register.py`, `download.py`, `preflight.py` | `tests/test_catalog.py`, `tests/test_authority_currentness.py`, `tests/test_source_register_proving.py`, `tests/test_source_register_loader.py`, `tests/test_source_register_schema.py`, `tests/test_download.py`, `tests/test_preflight.py` |
| Compliance and eval | `compliance_review_eval.py`, `compliance_outputs.py`, `compliance_validation.py` | `tests/test_compliance_review_eval.py`, `tests/test_compliance_review.py`, `tests/test_compliance_review_contracts.py`, `tests/test_compliance_review_test_boundary.py`, `tests/test_compliance_gold_eval.py`, `tests/test_gold_coverage_eval.py`, `tests/test_promotion_suite.py`, `tests/test_real_package_review_coverage_eval.py`, `tests/test_v1_ea_eval.py`, `tests/test_v1_ea_eval_contracts.py`, `tests/test_v1_ea_eval_forest_plan.py` |
| Viewer | `viewer/nepa-3d/app.js` | `tests/test_nepa_3d_viewer.py` |

## Placement Rules

- Preserve existing public module entry points until each owner family closes. If a large file is a
  public facade today, reduce it to a thin facade rather than deleting it mid-family.
- New modules must live beside their owner family under `src/usfs_r1_ea_sources/` or
  `viewer/nepa-3d/`, named for the capability they own. Do not create generic overflow files.
- When a split creates a new owned module or boundary, update `docs/architecture_contract.toml` and
  the relevant focused boundary tests in the same milestone.
- If a file already has `*_test_boundary.py` coverage, extend that boundary test rather than adding
  overlapping generic tests.
- The viewer split must keep behavior stable from the user's point of view; only the internal module
  layout may change.
- The current gold packet owns live semantic changes in compliance scoring. This architecture packet
  may only touch the compliance/eval family after Milestone `0` confirms the overlap is isolated.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | Work begins on a dirty overlapping family and silently mixes architecture work with active gold fixes | `git status -sb`, `docs/SESSION_HANDOFF.md`, `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md` | `git status -sb`; handoff readback; fresh architecture probe readback | Any targeted owner family is dirty or the active gold packet would be mutated implicitly | Prove the baseline gate reports the current dirty overlap before any code movement starts | A future session starts splitting `compliance_review_eval.py` while unrelated gold fixes are still uncommitted |
| `1` | Count-only ratchet hides hotspot substitution or reopens a previously-closed owner | `tests/test_architecture_quality.py`; new oversized-file inventory artifact | Architecture quality test plus architecture probe exact-inventory match | Any new `>800` file appears without being routed; any closed file reopens above `800`; live assertions remain tied only to the resolved umbrella prose | Add a loader/test case that fails when the live oversized set differs from the inventory artifact | A future session removes one hotspot but creates another and still claims the repo stayed flat at `24` |
| `2` | `project_sow_package.py` is replaced by one or more new `>800` helper files | Project SOW family modules and boundary tests | Focused Project SOW tests plus architecture quality gate | `project_sow_package.py` or any new sibling stays above `800`; public behavior changes without a named contract update | Boundary test proves imports stay within the selected owner surfaces | A future session creates `project_sow_support.py` at `1200` lines and calls it progress |
| `3` | Knowledge-graph or decision-support splits leak cross-owner concerns and create new fan-out | `nepa_knowledge_graph_export*`, `ea_consistency_decision_support*`, `nepa_3d_graph_contract*` | Focused family tests plus architecture contract and quality gates | Any family file remains above `800`; new module fan-out exceeds `20`; review/readiness semantics drift | Add or extend boundary tests for export/review/readiness and decision-support test boundaries | A future session moves readiness logic into a random sibling file and bypasses the contract |
| `4` | Forest-plan work turns one giant module into several unlabeled medium-large modules with unclear ownership | Forest-plan family modules and test-boundary suites | Focused forest-plan tests plus architecture gates | Any targeted forest-plan owner stays above `800`; ownership is not reflected in `docs/architecture_contract.toml` | Extend `tests/test_forest_plan_components_test_boundary.py` and `tests/test_forest_plan_resolver_test_boundary.py` to catch cross-owner drift | A future session extracts helpers without updating the owner map and leaves the queue opaque |
| `5` | Extraction/retrieval splits shift the hotspot into shared artifact helpers and weaken fixture coverage | `extract*`, `retrieval*`, `final_qa_certification*`, `draft_generation*`, `review_packet_index*` | Focused family tests plus architecture quality gate | Any targeted file remains above `800`; extraction/retrieval contract coverage drops; new helper exceeds `800` | Extend existing `*_test_boundary.py` suites and keep fixture contracts explicit | A future session hides extraction logic in an oversized artifact helper and removes direct coverage |
| `6` | Capture/source-register splits disturb workbook or catalog contracts while chasing size | `catalog*`, `authority_currentness*`, `source_register*`, `download*`, `preflight*` | Focused family tests plus architecture contract and quality gates | Any workbook/catalog/schema contract changes without matching tests/docs; any targeted file remains above `800` | Use schema/loader tests to prove unchanged register semantics | A future session renames or reroutes source-register behavior under the cover of a size split |
| `7` | Compliance/eval size work reopens the active gold lane or changes red/green semantics without bounded proof | `compliance_review_eval*`, `compliance_outputs*`, `compliance_validation*` and gold-eval docs | Focused compliance tests, architecture gates, bounded gold replay, bounded coverage replay | Any active gold expectation shifts without explicit evidence; any targeted file remains above `800`; current dirty overlap was not isolated first | Run a bounded replay that proves the refactor changed no semantics beyond the intended owner split | A future session uses the architecture packet to smuggle in scoring changes from the active gold lane |
| `8` | Viewer modularization becomes a redesign or leaves a new oversized JS controller | `viewer/nepa-3d/app.js` and viewer tests | `tests/test_nepa_3d_viewer.py` plus architecture quality gate | Any new viewer file exceeds `800`; behavior changes without a named viewer contract | Keep a thin top-level shell and fail if the routed controller/file count regresses above the agreed budget | A future session turns `app.js` into `viewer_shell.js` plus a `1500`-line `viewer_controller.js` |
| `9` | Closeout leaves stale docs, stale inventory counts, or an unresolved queued route | this plan, `docs/SESSION_HANDOFF.md`, `docs/CURRENT_ROUTING.md`, `README.md`, `docs/CURRENT_SYSTEM_STATE.md` when touched | Final architecture probe, doc readback, `git diff --check` | Probe still finds any `>800` code file; docs disagree about the active baseline or next route | Readback must fail if any closeout doc still says `24` after the inventory reaches `0` | A future session treats the queue as closed while the docs still point to stale counts or stale next packets |

## Milestone Sequence

| Milestone | Scoped owner family | Live oversized files in scope | Expected repo oversized count after closeout | Outcome label |
| --- | --- | --- | --- | --- |
| `0` | Freshness lock and overlap isolation | baseline only | `24` | `resolved` |
| `1` | Exact inventory gate and follow-on routing | governance only | `24` | `resolved` |
| `2` | Project SOW package family | `1` | `23` | `resolved` |
| `3` | Knowledge graph and decision-support family | `3` | `20` | `resolved` |
| `4` | Forest-plan runtime family | `5` | `15` | `resolved` |
| `5` | Extraction, retrieval, and review-artifact family | `5` | `10` | `resolved` |
| `6` | Capture, catalog, and source-register family | `6` | `4` | `resolved` |
| `7` | Compliance and eval family | `3` | `1` | `resolved` |
| `8` | Viewer family | `1` | `0` | `resolved` |
| `9` | Final zero-oversized rebaseline and closeout | closeout only | `0` | `resolved` |

### Milestone `0`: Freshness lock and overlap isolation

Outcome label: `resolved`

Work:

- Re-run `git status -sb` and the architecture probe before editing code.
- Record the exact dirty-overlap surfaces in `docs/SESSION_HANDOFF.md`.
- Explicitly decide whether the current active gold lane is complete, parked, or still blocking the
  compliance/eval family.
- If any target family is already dirty, route that family later or stop; do not mix implementation.

Required verification:

```bash
git status -sb
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

Progress after Milestone `0` on 2026-05-21:

- `git status -sb` recheck no longer showed the planning-time compliance/eval overlap. The only
  dirty files at milestone start were this packet's docs-routing slice.
- The fresh architecture probe remained at `344` code files, `24` code files above `800`, no
  Python cycles, no JS/TS cycles, and no local module above the `20`-import fan-out gate.
- Milestone `0` therefore resolved the baseline-isolation question without reopening the active
  gold packet. The next safe implementation slice was the governance-only Milestone `1`.

### Milestone `1`: Exact inventory gate and queued follow-on routing

Outcome label: `resolved`

Work:

- Add the machine-readable oversized-file inventory artifact
  `config/architecture_large_file_inventory_v1.json`, which records:
  path, live line count, owner family, target milestone, and required focused tests.
- Update `tests/test_architecture_quality.py` so the live oversized-file set must match the queued
  inventory artifact exactly. The gate must fail if a closed file reopens, a new file grows above
  `800`, or live closeout assertions remain tied only to the resolved umbrella plan.
- Keep `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md` historical. Move live oversized-file
  routing truth into this packet and the inventory artifact instead of rewriting the umbrella.
- Append the queued follow-on route to `docs/SESSION_HANDOFF.md` and keep `docs/CURRENT_ROUTING.md`
  short while making the new packet discoverable.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_architecture_quality.py tests/test_architecture_contract.py
PYTHONPATH=src python -m compileall tests/test_architecture_quality.py tests/test_architecture_contract.py
git diff --check
```

Progress after Milestone `1` on 2026-05-21:

- `config/architecture_large_file_inventory_v1.json` now governs the exact live oversized-file
  queue: `24` code files grouped by owner family, target milestone, and focused verification
  surface.
- `tests/test_architecture_quality.py` now fail-closes on exact oversized-file membership instead
  of count-only drift, and it also checks that the under-`800` follow-on packet remains routed from
  the plan, handoff, and short current route.
- `README.md` and `docs/CURRENT_SYSTEM_STATE.md` now align with the active gold packet's
  generated-diagnostic wording, restoring the existing cross-doc gold-alignment gate without
  weakening the assertion.
- Milestone `1` resolves the governance blind spot. The next routed implementation slice in this
  packet is Milestone `2` on `src/usfs_r1_ea_sources/project_sow_package.py`.

### Milestone `2`: Project SOW package family under `800`

Outcome label: `resolved`

Work:

- Reduce `src/usfs_r1_ea_sources/project_sow_package.py` to `<=800` by extracting named owner
  modules that match the existing coverage split: intake, validation, adjudication, assembly, and
  rendering/package-write seams.
- Keep `project_sow_package.py` as the public facade until the family closes.
- Extend or add boundary tests so the family cannot regrow a hidden oversized sibling.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_project_sow_package.py tests/test_project_sow_package_validation.py tests/test_project_sow_adjudication.py tests/test_project_sow_intake.py tests/test_project_sow_package_test_boundary.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `3`: Knowledge graph and decision-support family under `800`

Outcome label: `resolved`

Work:

- Reduce `nepa_knowledge_graph_export.py`, `ea_consistency_decision_support.py`, and
  `nepa_3d_graph_contract.py` to `<=800` through named owner splits, not generic helper spillover.
- Keep the split aligned to the existing test taxonomy:
  export runtime, review overlay/readiness, graph contract, decision-support validation, and report
  assembly.
- Update `docs/architecture_contract.toml` if new owner modules become first-class boundaries.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py tests/test_nepa_knowledge_graph_export_review.py tests/test_nepa_knowledge_graph_export_readiness.py tests/test_nepa_knowledge_graph_export_test_boundary.py tests/test_nepa_3d_graph_contract.py tests/test_ea_consistency_decision_support.py tests/test_ea_consistency_decision_support_report.py tests/test_ea_consistency_decision_support_validation.py tests/test_ea_consistency_decision_support_test_boundary.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `4`: Forest-plan runtime family under `800`

Outcome label: `resolved`

Work:

- Reduce the five live oversized forest-plan owners to `<=800`:
  `forest_plan_components.py`,
  `forest_plan_resolver.py`,
  `forest_plan_source_delta_readiness.py`,
  `forest_plan_component_adjudication.py`, and
  `forest_plan_component_eval.py`.
- Prefer owner splits that follow the existing family test boundaries:
  component inventory/manifest/coverage, resolver profile/scope/runtime, and adjudication/eval
  outputs.
- Do not create new unlabeled cross-family forest-plan support modules; every new surface must map
  back to one existing owner family and contract test.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_forest_plan_components_manifest.py tests/test_forest_plan_components_inventory.py tests/test_forest_plan_components_coverage.py tests/test_forest_plan_components_test_boundary.py tests/test_forest_plan_resolver.py tests/test_forest_plan_resolver_profiles.py tests/test_forest_plan_resolver_scope.py tests/test_forest_plan_resolver_test_boundary.py tests/test_forest_plan_source_delta_readiness.py tests/test_forest_plan_component_adjudication.py tests/test_forest_plan_component_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_forest_plan_component_retrieval_eval.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `5`: Extraction, retrieval, and review-artifact family under `800`

Outcome label: `resolved`

Work:

- Reduce `extract.py`, `final_qa_certification.py`, `draft_generation.py`, `retrieval.py`, and
  `review_packet_index.py` to `<=800`.
- Reuse the existing owner seams already visible in tests:
  extract runtime/reuse/PDF fallback, retrieval runtime/validation/eval, final-QA report and
  validation, and review-packet index assembly.
- Keep public command and artifact behavior stable. Any owner split that changes artifact fields or
  filenames must land with explicit contract-test updates in the same milestone.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py tests/test_extract_reuse.py tests/test_extract_pdf_fallbacks.py tests/test_extract_test_boundary.py tests/test_final_qa_certification.py tests/test_final_qa_certification_report.py tests/test_final_qa_certification_validation.py tests/test_final_qa_certification_test_boundary.py tests/test_draft_generation.py tests/test_draft_generation_eval.py tests/test_retrieval.py tests/test_retrieval_validation.py tests/test_retrieval_eval.py tests/test_retrieval_test_boundary.py tests/test_review_packet_index.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `6`: Capture, catalog, and source-register family under `800`

Outcome label: `resolved`

Work:

- Reduce `catalog.py`, `authority_currentness.py`, `source_register_proving.py`,
  `source_register.py`, `download.py`, and `preflight.py` to `<=800`.
- Preserve workbook-driven semantics, source-row identity, catalog row cardinality, and source
  register schema behavior.
- Keep these splits aligned to existing capture/shared-owner seams such as `capture_run_support.py`
  and the source-register loader/schema test family rather than inventing new cross-family facades.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_authority_currentness.py tests/test_source_register_proving.py tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_download.py tests/test_preflight.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `7`: Compliance and eval family under `800`

Outcome label: `resolved`

Work:

- Start only after Milestone `0` confirms the dirty overlap is isolated.
- Reduce `compliance_review_eval.py`, `compliance_outputs.py`, and `compliance_validation.py` to
  `<=800` without changing live gold semantics unintentionally.
- Keep semantic scoring or expectation changes out of scope. This family owns only boundary,
  assembly, rendering, and validation size reduction unless the active gold packet explicitly
  expands scope.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review_eval.py tests/test_compliance_review.py tests/test_compliance_review_contracts.py tests/test_compliance_review_test_boundary.py tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_real_package_review_coverage_eval.py tests/test_v1_ea_eval.py tests/test_v1_ea_eval_contracts.py tests/test_v1_ea_eval_forest_plan.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_under800
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `8`: Viewer family under `800`

Outcome label: `resolved`

Work:

- Reduce `viewer/nepa-3d/app.js` to `<=800` by splitting controllers, rendering, and state
  ownership into named viewer modules under `viewer/nepa-3d/`.
- Keep the public viewer behavior and test contract stable.
- Do not mix viewer redesign with architecture reduction.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_viewer.py tests/test_architecture_quality.py -q
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `9`: Zero-oversized rebaseline and closeout

Outcome label: `resolved`

Work:

- Re-run the architecture probe and prove the live oversized-file inventory is `0`.
- Update this plan with final counts, closeout hashes, and the exact last owner family closed.
- Update `docs/SESSION_HANDOFF.md` and `docs/CURRENT_ROUTING.md` so the queued follow-on no longer
  reads as active debt.
- Update `README.md` and any other live architecture fact surface touched by the milestone so they
  no longer say the repo has `24` files over `800`.
- Keep the resolved umbrella plan historical; do not rewrite it as if it closed this new packet.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py tests/test_architecture_contract.py tests/test_debt_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

## Required Implementation Artifacts

- One machine-readable oversized-file inventory artifact created in Milestone `1`.
- Updated `tests/test_architecture_quality.py` that enforces exact oversized-file membership, not
  just total count.
- Any new owner-family modules created during the splits.
- Updated `docs/architecture_contract.toml` whenever a new boundary or owner module becomes
  first-class.
- Updated focused `*_test_boundary.py` suites for families that already use them.

## Required Documentation And Handoff Updates

For every implementation milestone:

- Update this plan with the exact post-milestone oversized count, the files closed, the commit hash,
  and the next owner family.
- Append a closeout note to `docs/SESSION_HANDOFF.md` with:
  milestone number, outcome label, exact verification run, and the next routed slice.
- Update `docs/CURRENT_ROUTING.md` only when the active short route should change; keep it under the
  enforced line cap.
- Update `README.md` and `docs/CURRENT_SYSTEM_STATE.md` only when their live architecture facts or
  user-visible entrypoint guidance are affected by the milestone.

## Required Verification Gates

Every implementation milestone in this packet must run all of:

- the focused family pytest slice named above;
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q`;
- `PYTHONPATH=src uv run --extra dev ruff check src tests`;
- `PYTHONPATH=src python -m compileall src`;
- fresh `architecture_probe.py --max-file-lines 800 --max-fan-out 20`;
- `git diff --check`.

Milestone `7` additionally requires a bounded `compliance-gold-eval` replay because the owner
family overlaps the active gold lane.

## Acceptance Criteria

- The live architecture probe reports `0` code files above `800` lines.
- No Python or JS/TS import cycle is introduced.
- No local module exceeds the `20`-import fan-out gate unless an explicit architecture-contract
  exception is added, justified, tested, and routed in the same milestone.
- The exact oversized-file inventory is machine-checked from Milestone `1` onward. A new
  `>800` file, a reopened closed owner, or a hidden sibling hotspot fails the architecture gate.
- Every current live oversized file listed in this plan is reduced to `<=800` without replacing it
  with another unlabeled oversized helper.
- Public CLI names, workbook semantics, catalog semantics, and review/eval artifact contracts stay
  stable unless the milestone explicitly owns a documented contract change.
- Durable docs and handoff routing identify the next active or queued packet truthfully after each
  closeout.

## Stop Conditions

- The current dirty worktree overlaps the family about to be edited and cannot be parked or
  committed cleanly.
- A split requires a broad rewrite, schema migration, or corpus regeneration beyond the bounded
  owner family.
- The only way to pass is to weaken tests, add skips, loosen assertions, or raise the
  `800`-line threshold.
- A proposed extraction would create a new `>800` sibling file or require a broad architecture
  exception that the current milestone does not own.
- Milestone `7` changes live compliance-gold semantics without a bounded replay proving the exact
  intended effect.

## Local Commit Closeout Policy

- Close one milestone or one explicitly named family sequence per atomic commit.
- Stage only the verified family slice: code, tests, architecture contract, this plan, handoff, and
  any required routing/current-state doc updates.
- Do not stage unrelated dirty files from the active gold or claims lanes.
- Do not stage `source_library/` outputs unless repo policy changes explicitly.

## Residual Risks And Next Routing

- The active default repo route remains
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md` until that packet is closed or
  explicitly parked. This architecture packet stays queued behind it except for planning work.
- The compliance/eval family remains the highest overlap risk because the current dirty baseline
  already touches that owner family.
- The viewer family is intentionally last because it is isolated from the Python lane and should not
  disrupt higher-value repo runtime work while the under-`800` gate is still being hardened.
- If any family cannot be reduced to `<=800` without broadening scope, split that family into
  explicitly named sequences inside this packet. Do not create a new anonymous follow-on packet
  unless the user asks for a narrower separate lane.
