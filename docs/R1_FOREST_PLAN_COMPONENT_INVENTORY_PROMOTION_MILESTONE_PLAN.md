# Region 1 Forest-Plan Component Inventory Promotion Milestone Plan

Date: 2026-05-10

Status: Sequence 0 implemented; Sequence 1 implemented; Sequence 2 pending

Owner context: This is a full-canonical, source-set-level forest-plan inventory milestone. It is
not a one-package review milestone. Its job is to make the active full-canonical source set own a
validated component inventory for the repo's current tracked Region 1 forest/grassland roster, then
promote those inventories into the readiness and NEPA 3D graph surfaces without weakening existing
review, promotion, or source-truth boundaries.

## Purpose

The current system has a strong Custer Gallatin forest-plan component lane, but the broader Region 1
inventory lane is still incomplete. That incompleteness now shows up in three places:

- the active full-canonical source set `source-set-34061d1e4bf6c460` has no owned
  `forest_plan_components/` artifact family under `source_library/derived/`;
- the full-canonical NEPA 3D source-set graph is currently replayed using a forest-plan component
  inventory borrowed from the archived merged source set `source-set-8a4005c8a083af1a`;
- only `custer-gallatin-nf` is graph-promoted with validated component inventory, while the other
  tracked Region 1 profiles remain `component_inventory_build_required` and
  `forest_profile_not_ready`.

The milestone exists to build and promote component inventories for all current Region 1
forest/grassland profiles tracked by the repo so the active full-canonical source set owns its
forest-plan inventory truth directly instead of inheriting a one-forest inventory surface.

## Current Evidence

- The active full-canonical catalog source set is `source-set-34061d1e4bf6c460` and is now the
  default viewer dataset in the local NEPA 3D viewer. See [README.md](/Users/chunkstand/projects/usfs-r1-EA-sources/README.md:41).
- The archived merged source set `source-set-8a4005c8a083af1a` remains the freshest all-green merged
  extraction/retrieval/graph surface and currently owns the only generated
  `forest_plan_components/` directory on disk.
- The current promoted component inventory is still Custer Gallatin-only: the existing generated
  inventory has `329` components, `58` standards, passing build coverage, and currently supports
  the promoted East Crazies forest-plan review lane.
- The Region 1 readiness matrix currently tracks `10` forest/grassland profiles, but only `1`
  graph-ready profile:
  - `custer-gallatin-nf`: `component_inventory_validation.status="validated"`
  - `beaverhead-deerlodge-nf`: `component_inventory_build_required`
  - `bitterroot-nf`: `component_inventory_build_required`
  - `dakota-prairie-grasslands`: `component_inventory_build_required`
  - `flathead-nf`: `component_inventory_build_required`
  - `helena-lewis-and-clark-nf`: `component_inventory_build_required`
  - `idaho-panhandle-nfs`: `component_inventory_build_required`
  - `kootenai-nf`: `component_inventory_build_required`
  - `lolo-nf`: `component_inventory_build_required`
  - `nez-perce-clearwater-nfs`: `component_inventory_build_required`
- The current `config/forest_plan_profiles.json` contains one full forest profile
  (`custer-gallatin-nf`) plus `known_other_forest_units`, not full resolver/build contracts for the
  other forests.
- The current `forest-plan-components-build` CLI is single-plan oriented:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id <source-set-id> \
  --source-record-id <plan-source-record-id> \
  --forest-unit-id <forest-unit-id> \
  --plan-version <plan-version>
```

- The NEPA 3D forest-plan lens shows the resulting imbalance directly: Custer Gallatin dominates
  the component graph while other tracked forests appear only as readiness-tracking unit/plan
  shells.

## Goal

Build and promote validated forest-plan component inventories for every current Region 1
forest/grassland profile tracked by the repo, so the active full-canonical source set
`source-set-34061d1e4bf6c460` owns a canonical multi-forest component inventory and the readiness
plus NEPA 3D graph surfaces no longer depend on the archived Custer-only inventory path.

For this milestone, "all R1 National Forests" is interpreted as the repo's current tracked Region 1
forest/grassland roster in `config/region1_forest_plan_readiness_nepa_3d_v1.json`. That includes
Dakota Prairie Grasslands because it is already a first-class readiness profile in the current
system contract.

## Non-Goals

- Do not claim reviewer-ready EA package review for every Region 1 forest in this milestone.
- Do not broaden this milestone into package adjudication closure, review replay promotion, or
  full resolver area-term completion for every forest unless required for inventory correctness.
- Do not bypass the workbook/register/source-delta contract or fetch new source material outside the
  existing promoted source-row universe unless a clearly missing core plan source blocks inventory
  build.
- Do not replace the canonical source-set component inventory path with ad hoc per-forest local
  files.
- Do not weaken source-set drift, build-coverage, or reviewer-ready gates to make multi-forest
  promotion pass.
- Do not stage ignored `source_library/` artifacts unless repository policy explicitly changes.

## Scope

- Create a tracked Region 1 component-inventory build contract for every current readiness profile.
- Extend or harden the component inventory builder so one active source set can own a canonical
  multi-forest inventory artifact family.
- Build and validate inventories for all tracked Region 1 forest/grassland profiles against the
  active full-canonical source set.
- Update readiness, graph, and related tests/docs so graph promotion no longer stops at one
  validated forest.

## Out Of Scope

- Full package-level resolver geography/overlay term authoring for every forest.
- Package-specific forest-plan component adjudication for all Region 1 forests.
- New NEPA or compliance conclusions that are not directly supported by validated inventory,
  readiness, and graph artifacts.

## Owner Surfaces

- Build contract/config:
  - `config/forest_plan_profiles.json`
  - `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  - `config/r1_forest_plan_component_inventory_build_manifest.json`
  - `config/r1_forest_plan_document_register_draft.csv`
- Builder/runtime:
  - `src/usfs_r1_ea_sources/forest_plan_components.py`
  - `src/usfs_r1_ea_sources/forest_plan_inventory_build_manifest.py`
  - `src/usfs_r1_ea_sources/cli_review.py`
  - `src/usfs_r1_ea_sources/forest_plan_resolver.py`
  - `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`
- Tests:
  - `tests/test_forest_plan_components.py`
  - `tests/test_forest_plan_inventory_build_manifest.py`
  - `tests/test_forest_plan_resolver.py`
  - `tests/test_nepa_knowledge_graph_export.py`
  - `tests/test_architecture_contract.py`
- Durable docs:
  - this plan
  - `README.md`
  - `docs/CURRENT_SYSTEM_STATE.md`
  - `docs/SESSION_HANDOFF.md`
  - `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`

## Placement Rules

- Preserve the canonical source-set inventory path:
  `source_library/derived/<source_set_id>/forest_plan_components/component_inventory.json`
  remains the main inventory artifact consumed by resolver, graph, and review lanes.
- If multi-forest support needs a new tracked config, put the per-forest execution contract in a
  dedicated config file rather than hardcoding per-forest build parameters in Python.
- Keep forest-specific knowledge as data:
  source record IDs, plan versions, amendment inclusion, and any required build constraints belong
  in config, not hidden branches.
- Preserve single-forest CLI compatibility where possible; add multi-forest/batch behavior behind a
  tracked manifest contract rather than breaking the current interface abruptly.
- Promotion must target the active full-canonical source set `source-set-34061d1e4bf6c460`, not
  only the archived merged source set.
- If a forest cannot be promoted, leave an explicit typed blocker in readiness/config/report
  surfaces. Do not silently omit it from the canonical inventory.

## Weak-Point Prevention Contract

- Weak point forecast: the milestone lands a multi-forest inventory in ad hoc local files while the
  active source-set canonical inventory path remains single-forest or missing.
  Owner surface: `src/usfs_r1_ea_sources/forest_plan_components.py`, generated
  `source_library/derived/<source_set_id>/forest_plan_components/`
  Prevention gate: inventory build tests and command verification require the active full-canonical
  source set to materialize a canonical multi-forest `component_inventory.json` plus build coverage.
  Fail threshold: the active source set still lacks owned `forest_plan_components/` artifacts at
  closeout.
  Controlled violation: remove the canonical build-coverage artifact for the active source set;
  inventory coverage and graph promotion tests must fail.
  Future-Codex misuse scenario: a future session rebuilds only one forest locally and points graph
  export at an archived or alternate inventory path again; the promotion gate must fail before that
  becomes accepted truth.
- Weak point forecast: per-forest build parameters are hidden in code and future updates become
  one-off manual reruns.
  Owner surface: tracked inventory-build config plus `cli_review.py`
  Prevention gate: tests and docs require a manifest/config-driven batch contract for Region 1
  inventory promotion.
  Fail threshold: a new forest can only be built by editing Python or hand-typing undocumented
  arguments.
  Controlled violation: delete one profile entry from the manifest/config; the batch validation must
  fail on incomplete Region 1 roster coverage.
  Future-Codex misuse scenario: a future session adds another forest by copying a Custer Gallatin
  branch; config ownership prevents that.
- Weak point forecast: cross-forest component IDs or standards collide when multiple forests enter
  one canonical inventory.
  Owner surface: `forest_plan_components.py`, generated build coverage, `tests/test_forest_plan_components.py`
  Prevention gate: build coverage must fail on duplicate component IDs, duplicate standards,
  missing component IDs, or source-set drift across forests.
  Fail threshold: any promoted inventory passes with duplicate or ambiguous cross-forest identifiers.
  Controlled violation: inject duplicate component IDs across two forests in fixtures; build
  coverage must fail.
  Future-Codex misuse scenario: a later build appends a second forest and silently reuses component
  identifiers from another plan; duplicate-ID gate prevents that.
- Weak point forecast: readiness and graph promotion overclaim broader Region 1 completeness without
  validated per-forest inventories.
  Owner surface: `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `nepa_knowledge_graph_export.py`, `tests/test_nepa_knowledge_graph_export.py`
  Prevention gate: readiness and graph checks must require validated component inventory for every
  graph-promoted profile and fail closed when a profile stays `component_inventory_build_required`.
  Fail threshold: a blocked profile becomes graph-promoted without validated inventory artifacts.
  Controlled violation: mark a blocked profile promoted in config while leaving inventory absent;
  graph validation must fail.
  Future-Codex misuse scenario: a later session flips readiness status in config to clean up the
  viewer; the graph gate must catch it.

## Milestone Sequence

### Sequence 0 - Baseline Gate And Active-Source-Set Ownership

Goal: reproduce the current one-forest baseline and install a failing gate that proves the active
full-canonical source set does not yet own promoted multi-forest component inventory truth.

Implementation tasks:

- Record the current baseline:
  - active full-canonical source set `source-set-34061d1e4bf6c460`
  - archived merged source set `source-set-8a4005c8a083af1a`
  - current Custer Gallatin inventory counts `329` components / `58` standards
  - current readiness profile counts `1` validated, `9` `component_inventory_build_required`
- Add or extend focused tests so the active source set fails promotion when it lacks owned
  `forest_plan_components/` artifacts or still depends on an alternate source-set inventory path.
- Document the tracked Region 1 roster and the active-vs-archived inventory ownership gap in the
  plan/handoff baseline.

Implementation closeout on 2026-05-10:

- live baseline confirmed from local artifacts:
  - active source set `source-set-34061d1e4bf6c460` missing
    `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/component_inventory.json`
  - archived source set `source-set-8a4005c8a083af1a` owns the only local
    `forest_plan_components/component_inventory.json`
  - current readiness config still records `10` tracked profiles, `1` validated inventory, and `9`
    `component_inventory_build_required` profiles
- installed fail-closed graph-export gate:
  `nepa_3d_graph_forest_plan_inventory_owned_by_source_set` now requires the inventory input path
  and payload `source_set_id` to match the exporting source set, so archived inventory borrowing is
  a validation failure instead of silently accepted baseline truth
- added regression coverage proving a borrowed inventory can still satisfy the old forest-unit
  presence check but now fails the new ownership gate
- alignment replay result:
  after refreshing the active-source-set graph artifact, `promotion-suite` now reports
  `full_canonical_corpus_ready=false` with
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2}` until the active
  source set owns its own `forest_plan_components/` artifact family

Acceptance signals:

- The baseline clearly shows one validated forest and nine blocked profiles.
- A failing or baseline gate exists for missing active-source-set inventory ownership.
- The roster boundary is explicit and replayable from config, not chat.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The active source set cannot be distinguished cleanly from archived merged-corpus artifacts.
- The current graph/export path depends on undocumented local inventory overrides.

### Sequence 1 - Region 1 Inventory Build Contract

Goal: define a tracked, config-owned execution contract for building component inventories across the
full Region 1 roster.

Implementation tasks:

- Add a tracked Region 1 component-inventory build manifest/config that enumerates every current
  readiness profile with at least:
  - `forest_unit_id`
  - `source_set_id` policy or source-set compatibility rule
  - primary plan `source_record_id`
  - `plan_version`
  - optional amendment/supporting source records required for canonical component extraction
  - promotion eligibility and any accepted blockers
- Keep resolver identity and alias terms in `config/forest_plan_profiles.json`; do not turn the
  build manifest into a second profile resolver.
- Reconcile the readiness matrix and build manifest so every tracked profile has one explicit build
  contract row.

Implementation closeout on 2026-05-10:

- added tracked build-contract config:
  `config/r1_forest_plan_component_inventory_build_manifest.json` now enumerates all `10` current
  Region 1 readiness profiles against active full-canonical source set
  `source-set-34061d1e4bf6c460`
- build inputs now live in config instead of Python branches:
  each profile row records `plan_version`, `primary_plan_source_record_id`, grouped
  `build_source_record_ids_by_role`, and typed `promotion_eligibility`
- the manifest preserves source-surface boundaries:
  resolver identity stays in `config/forest_plan_profiles.json`, while the new manifest carries
  build-only inputs such as Dakota Prairie multipart plan anchors and Nez Perce-Clearwater's split
  currentness-vs-primary-plan sources
- installed strict validation in
  `src/usfs_r1_ea_sources/forest_plan_inventory_build_manifest.py`:
  load fails on unsupported source-set reference types, duplicate forest IDs, manifest/readiness
  roster drift, missing readiness source-record coverage, or a primary-plan source ID that is not
  present in the row's build inputs
- added regression coverage in `tests/test_forest_plan_inventory_build_manifest.py` for the new
  contract loader plus the default manifest's all-10-profile baseline
- alignment recheck confirms the default build contract matches the live repo boundary:
  the manifest's `active_full_canonical` reference points to current
  `source_library/catalog/source_set_manifest.json` source set `source-set-34061d1e4bf6c460`, and
  manifest roster coverage is `10/10` against `config/region1_forest_plan_readiness_nepa_3d_v1.json`

Acceptance signals:

- Every current Region 1 readiness profile is present in the build contract.
- No profile requires a code edit to change plan-version or source-record build inputs.
- Build contract validation fails on missing profile coverage, duplicate forest IDs, or unsupported
  source-set references.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_components.py tests/test_architecture_contract.py
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
python -m json.tool config/r1_forest_plan_component_inventory_build_manifest.json /tmp/r1_inventory_build_manifest.validated.json
git diff --check
```

Stop conditions:

- A tracked forest cannot be represented in the manifest without hardcoded runtime branching.
- The manifest duplicates information already owned by another config surface in conflicting form.

### Sequence 2 - Multi-Forest Builder Hardening

Goal: let the builder produce a canonical multi-forest source-set inventory while preserving the
current single-forest contract as a supported path.

Implementation tasks:

- Extend `forest-plan-components-build` with manifest-driven or batch-driven execution for the full
  Region 1 roster.
- Preserve current single-forest invocation compatibility for focused rebuilds.
- Make build coverage report per-forest results and aggregate source-set results, including:
  - selected chunk counts
  - component counts
  - standard counts
  - missing/duplicate component IDs
  - missing/duplicate standards
  - suppressed nonnumeric labels
  - source-set drift or unsupported source-record mismatches
- Ensure the canonical `component_inventory.json` can hold multi-forest records safely and that
  resolver consumers filter by `forest_unit_id` rather than assuming one forest only.

Acceptance signals:

- The builder can produce one canonical multi-forest inventory artifact family for a source set.
- Single-forest rebuilds still work for targeted repair paths.
- Aggregate build coverage fails closed on per-forest and cross-forest identifier collisions.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_forest_plan_resolver.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Multi-forest support can only land by changing consumers to read ad hoc per-forest files.
- Resolver compatibility breaks for the current Custer Gallatin review lane.

### Sequence 3 - Build And Validate All Region 1 Inventories On The Active Full-Canonical Source Set

Goal: materialize validated component inventories for the full Region 1 roster under
`source-set-34061d1e4bf6c460`.

Implementation tasks:

- Build inventories for all tracked Region 1 forest/grassland profiles on the active full-canonical
  source set using the tracked build contract.
- Materialize canonical artifacts under:
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/`
- Require passing build coverage for every profile before accepting the combined inventory as
  promotion-ready.
- If a profile fails because the primary plan source row is unusable, preserve a typed blocker and
  stop promotion rather than silently excluding it.

Acceptance signals:

- The active full-canonical source set owns its own `forest_plan_components/` artifact family.
- Every tracked Region 1 readiness profile has `component_inventory_validation.status="validated"`
  or the milestone stops on a typed blocker.
- The combined inventory is no longer borrowed from `source-set-8a4005c8a083af1a`.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id source-set-34061d1e4bf6c460 \
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json

PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py
git diff --check
```

Stop conditions:

- Any core plan source record needed for component extraction is missing, unreadable, or parser
  blocked in a way that prevents typed inventory generation.
- Aggregate build coverage passes only by dropping failing forests from the canonical inventory.

### Sequence 4 - Readiness Promotion And Graph Integration

Goal: promote validated multi-forest inventory truth into the Region 1 readiness and NEPA 3D graph
surfaces.

Implementation tasks:

- Update `config/region1_forest_plan_readiness_nepa_3d_v1.json` and any generated companion report
  surfaces so all promoted profiles record validated inventory IDs, counts, and artifact paths.
- Refresh the NEPA 3D source-set export against `source-set-34061d1e4bf6c460` using the active
  source-set's owned multi-forest inventory.
- Ensure the forest-plan lens and related graph summaries now reflect multi-forest component
  presence instead of one component-rich forest plus nine shell profiles.
- Keep `region1_completeness_claim=false` unless every in-scope readiness requirement for every
  tracked forest/grassland profile actually passes.

Acceptance signals:

- The active graph export uses the active source-set inventory path, not the archived merged
  inventory path.
- Region 1 graph promotion no longer stops at Custer Gallatin because of missing component
  inventories.
- Graph validation fails closed if a promoted profile lacks validated inventory coverage.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-34061d1e4bf6c460

PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Graph promotion requires undocumented manual inventory-path overrides.
- Viewer/readiness truth would overclaim all-Region-1 readiness despite remaining typed blockers.

### Sequence 5 - Evaluation, Docs, Handoff, And Closeout

Goal: make the promotion durable and safe for future review/resolver work.

Implementation tasks:

- Add or update focused evaluation fixtures so multi-forest inventories are not just present but
  structurally usable:
  - positive inventory presence checks for every tracked forest/grassland profile
  - representative hard-negative checks to prevent cross-forest contamination
  - resolver compatibility checks proving one forest’s inventory does not satisfy another’s review
- Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`,
  and `docs/SESSION_HANDOFF.md` with the new inventory ownership and Region 1 promotion state.
- Close the milestone with one atomic commit containing implementation, tests, docs, and updated
  handoff only.

Acceptance signals:

- Docs no longer describe the component lane as effectively Custer-only.
- The handoff records the active source-set inventory path, per-forest validation result, and any
  accepted residual blockers.
- The verified milestone slice is separable from unrelated dirty worktree changes.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_forest_plan_resolver.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Required verification fails.
- The milestone slice cannot be staged without unrelated viewer or draft-output changes.

## Required Implementation Artifacts

- tracked Region 1 component-inventory build manifest/config
- active full-canonical multi-forest component inventory artifacts under
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/`
- per-forest and aggregate build coverage proving inventory validity
- readiness/profile contract updates reflecting validated inventory promotion
- focused multi-forest builder, resolver-compatibility, and graph-promotion tests

## Required Documentation And Handoff Updates

- this plan
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`
- `docs/SESSION_HANDOFF.md`

## Required Verification Gates

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Operational closeout should also include a live `forest-plan-components-build` replay against
`source-set-34061d1e4bf6c460` and a refreshed `nepa-knowledge-graph-export` replay against that
same source set.

## Acceptance Criteria

- The active full-canonical source set `source-set-34061d1e4bf6c460` owns a canonical
  multi-forest `forest_plan_components/` artifact family.
- Every currently tracked Region 1 forest/grassland profile in the readiness matrix has a tracked
  build contract and a validated component inventory, or the milestone stops on an explicit typed
  blocker.
- `component_inventory_build_required` is eliminated as the steady-state status for the current
  Region 1 roster at closeout.
- Multi-forest build coverage fails on duplicate component IDs, duplicate standards, source-set
  drift, missing component IDs, or incomplete roster coverage.
- Resolver consumers remain compatible with the canonical source-set inventory path.
- The NEPA 3D graph export uses the active source-set inventory path and no longer borrows the
  archived Custer-only inventory for full-canonical replay.
- Docs and handoff identify Region 1 inventory promotion as a completed source-set milestone and
  name any residual non-inventory blockers separately.

## Stop Conditions

- A tracked forest lacks a usable core plan source row needed for component extraction.
- Cross-forest inventory collisions cannot be resolved without changing the public artifact
  contract.
- Promotion would require weakening readiness, graph, or source-set drift gates.
- The active source-set multi-forest inventory cannot be separated safely from unrelated worktree
  changes.

## Local Commit Closeout Policy

Close this milestone with one local atomic commit only after verification passes. Stage only the
verified multi-forest component inventory promotion slice. Leave unrelated existing worktree changes
alone, including the current viewer-default edits and unrelated root-level `East_Crazies_*` draft
outputs unless the user explicitly broadens scope.

## Residual Risks And Next Milestone Routing

This milestone promotes component inventory ownership and graph/readiness coverage; it does not by
itself make every Region 1 forest reviewer-ready for package review. After this milestone, the next
lane should be one of:

- deepen resolver/profile term coverage and evaluation fixtures for additional forests;
- move from inventory promotion to package-level forest-plan review promotion on selected forests;
- or close remaining source-readiness/currentness blockers that still prevent broader Region 1
  completeness claims after inventory validation is green.
