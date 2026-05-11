# Region 1 Forest-Plan Component Inventory Promotion Milestone Plan

Date: 2026-05-10

Status: parser/component recovery active on `source-set-5e65d845ce77e1a0`; readiness promotion now
tracks `7` validated forests and `3` typed blockers

Owner context: This is a full-canonical, source-set-level forest-plan inventory milestone. It is
not a one-package review milestone. Its job is to make the active full-canonical source set own a
validated component inventory for the repo's current tracked Region 1 forest/grassland roster, then
promote those inventories into the readiness and NEPA 3D graph surfaces without weakening existing
review, promotion, or source-truth boundaries.

## Purpose

The repository's live active catalog, full-canonical derived lane, readiness config, and
promotion-suite full-canonical contract are now aligned to the same source set:
`source-set-5e65d845ce77e1a0`.

- the active full-canonical inventory replay on `source-set-5e65d845ce77e1a0` validates
  `custer-gallatin-nf`, `bitterroot-nf`, `flathead-nf`, `helena-lewis-and-clark-nf`,
  `idaho-panhandle-nfs`, `kootenai-nf`, and `nez-perce-clearwater-nfs`;
- the same replay now stops on typed blockers for `beaverhead-deerlodge-nf`,
  `dakota-prairie-grasslands`, and `lolo-nf`;
- `config/region1_forest_plan_readiness_nepa_3d_v1.json` now promotes those seven validated
  forests and keeps the three blocked forests explicit with live blocker types;
- the active-source-set NEPA 3D graph lane now passes with `66` checks, `0` failed,
  `2,451` nodes, `4,853` edges, `region1_forest_plan_graph_ready_profile_count=7`, and
  `region1_forest_plan_blocked_profile_count=3`;
- `promotion-suite` now pins its full-canonical contract to `source-set-5e65d845ce77e1a0` and
  reports `full_canonical_corpus_ready=true`.

The remaining milestone job is no longer stale-surface repair. It is parser/component recovery on
the five blocked forests while preserving typed blocker handling, current promotion truth, and
source-set ownership gates.

## Current Evidence

- The live active full-canonical catalog source set in `source_library/catalog/` is now
  `source-set-5e65d845ce77e1a0`.
- The live active full-canonical source set `source-set-5e65d845ce77e1a0` now owns a refreshed
  full-canonical derived lane, including
  `source_library/derived/source-set-5e65d845ce77e1a0/forest_plan_components/`, with a combined
  inventory of `1003` components and `234` standards.
- The archived merged source set `source-set-8a4005c8a083af1a` remains the freshest all-green merged
  extraction/retrieval/graph surface, but it is no longer the active inventory-ownership source
  for the full-canonical lane.
- The promoted East Crazies forest-plan review lane is still Custer Gallatin-specific, but the
  refreshed active-source-set inventory replay is broader: `source-set-5e65d845ce77e1a0` now
  validates `custer-gallatin-nf`, `bitterroot-nf`, `flathead-nf`,
  `helena-lewis-and-clark-nf`, `idaho-panhandle-nfs`, `kootenai-nf`, and
  `nez-perce-clearwater-nfs`.
- The remaining blocked forests on the refreshed active-source-set replay are
  `beaverhead-deerlodge-nf`, `dakota-prairie-grasslands`, and `lolo-nf`.
  `beaverhead-deerlodge-nf` is now blocked on duplicate component/standard IDs; Dakota Prairie and
  Lolo remain blocked on label detection.
- The readiness config now tracks `10` forest/grassland profiles on the refreshed active source
  set:
  - `custer-gallatin-nf`: `validated`
  - `bitterroot-nf`: `validated`
  - `flathead-nf`: `validated`
  - `helena-lewis-and-clark-nf`: `validated`
  - `idaho-panhandle-nfs`: `validated`
  - `kootenai-nf`: `validated`
  - `nez-perce-clearwater-nfs`: `validated`
  - `beaverhead-deerlodge-nf`: blocked on duplicate IDs
  - `dakota-prairie-grasslands`: blocked on typed label detection
  - `lolo-nf`: blocked on typed label detection
- The refreshed readiness config now also carries current catalog-confirmed source requirements for
  the promoted plan and supporting-document rows that the multi-forest build actually uses.
- `config/forest_plan_profiles.json` still contains one full forest profile
  (`custer-gallatin-nf`) plus `known_other_forest_units`; the multi-forest build contract for the
  broader Region 1 roster currently lives in
  `config/r1_forest_plan_component_inventory_build_manifest.json`.
- The current `forest-plan-components-build` CLI now supports both targeted and manifest-driven
  execution:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id <source-set-id> \
  --source-record-id <plan-source-record-id> \
  --forest-unit-id <forest-unit-id> \
  --plan-version <plan-version>

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id <source-set-id> \
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json
```

- The NEPA 3D forest-plan lens now has a refreshed active-source-set graph lane:
  `source_library/catalog/source_set_manifest.json` resolves the live catalog to
  `source-set-5e65d845ce77e1a0`, and the active-source-set `nepa-knowledge-graph-export` replay now
  passes on that same source set with `2,128` nodes, `3,825` edges, and `0` failed checks.

## Goal

Re-anchor the forest-plan inventory lane to the actual live active catalog source set
`source-set-5e65d845ce77e1a0`, refresh a canonical multi-forest inventory plus derived
currentness/graph artifacts on that source set, and then promote validated forest-plan component
inventory truth for every current Region 1 forest/grassland profile tracked by the repo so the
readiness plus NEPA 3D graph surfaces no longer depend on the older
`source-set-34061d1e4bf6c460` replay or the archived Custer-only inventory path.

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
- Promotion must target the source set currently named by
  `source_library/catalog/source_set_manifest.json`. As of this re-baseline, that live
  active-source-set target is `source-set-5e65d845ce77e1a0`, not only the archived merged source
  set and not the older derived replay `source-set-34061d1e4bf6c460`.
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
- Weak point forecast: the repo mixes a newer active catalog source set with an older derived
  inventory/currentness/graph lane and accidentally promotes readiness from the wrong replay.
  Owner surface: `source_library/catalog/source_set_manifest.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`, this plan, and
  `docs/CURRENT_SYSTEM_STATE.md`
  Prevention gate: doc/config re-baseline plus active-source-set replay checks must confirm the live
  catalog source set, the manifest's `active_full_canonical` reference, and the refreshed derived
  inventory/currentness/graph artifacts all name the same `source_set_id`.
  Fail threshold: `source_library/catalog/source_set_manifest.json` points at one source set while
  the tracked inventory build contract or current-state docs still promote another as the active
  full-canonical lane.
  Controlled violation: keep the manifest pinned to `source-set-34061d1e4bf6c460` while the live
  catalog points at `source-set-5e65d845ce77e1a0`; the re-baseline gate must stop Sequence 4 before
  readiness promotion continues.
  Future-Codex misuse scenario: a future session treats the newer catalog as "just transient" and
  continues promoting readiness from an older derived replay; the alignment gate must prevent that.

## Milestone Sequence

Every sequence in this milestone closes the same way before the next sequence begins:

- align every affected durable doc surface to the just-completed sequence state, including this
  plan, `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, any affected milestone/status docs, and
  `docs/SESSION_HANDOFF.md`
- record the verification commands and the resulting repo state in the handoff for that completed
  sequence
- stage only that verified sequence slice and land one local atomic commit before moving to the next
  sequence
- stop instead of rolling uncommitted or doc-misaligned work forward if verification fails or the
  sequence slice cannot be separated from unrelated dirty worktree changes

Re-baseline note on 2026-05-10:

- Sequence 0 through Sequence 3 closeout sections below preserve the historical
  `source-set-34061d1e4bf6c460` implementation evidence that was current when those slices landed.
- The live active catalog has since advanced to `source-set-5e65d845ce77e1a0`.
- Sequence 4 was therefore no longer a pure readiness-promotion slice. It first needed to refresh
  the manifest-owned derived lane onto the live active catalog source set before readiness/config
  promotion could truthfully continue.

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

Implementation closeout on 2026-05-10:

- `forest-plan-components-build` now supports a manifest-driven batch path:
  `--manifest-path` loads the tracked Region 1 inventory build contract and emits one canonical
  source-set inventory artifact family without breaking the existing single-forest invocation
  shape
- single-forest compatibility is preserved:
  `--source-record-id` plus `--plan-version` still drives focused rebuilds, and the CLI now fails
  clearly when single-forest-only overrides are mixed with manifest-driven batch mode
- `src/usfs_r1_ea_sources/forest_plan_components.py` now emits aggregate multi-forest inventory
  coverage plus per-profile build summaries, while keeping the canonical output path at
  `source_library/derived/<source_set_id>/forest_plan_components/component_inventory.json`
- aggregate coverage now fails closed on cross-profile component-ID and standard-ID collisions even
  when each per-profile build passes in isolation
- regression coverage now proves:
  manifest-driven multi-forest builds produce one canonical inventory artifact family, selected
  forest filtering still works when loading the combined inventory, and a manifest row collision can
  fail the aggregate build without weakening per-profile checks
- stop condition reached at closeout:
  the required durable docs for this sequence (`README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md`) were already dirty with unrelated NEPA 3D viewer edits before this
  sequence started, so the repo's commit-closeout rule blocked a truthful atomic milestone commit in
  this pass

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

Implementation closeout on 2026-05-10:

- reuse-first extraction materialized the active source-set chunk layer before the build:
  `reuse-inventory` reported `349` reusable extraction rows, `0` new extraction requirements, and
  `1` excluded row, then `extract-build --reuse-existing` wrote `349/349` extracted rows with
  `75,745` chunks under `source-set-34061d1e4bf6c460`
- the live manifest-driven builder now writes the canonical active-source-set artifact family under
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/`
- the active combined build writes `587` components and `87` standards, validates
  `custer-gallatin-nf`, `helena-lewis-and-clark-nf`, and `idaho-panhandle-nfs`, and stops on typed
  blockers for `beaverhead-deerlodge-nf`, `bitterroot-nf`, `dakota-prairie-grasslands`,
  `flathead-nf`, `kootenai-nf`, `lolo-nf`, and `nez-perce-clearwater-nfs`
- the only failing aggregate build-coverage check is `all_profile_builds_pass`; every blocked
  profile currently reports `plan_component_labels_not_detected` plus
  `plan_standard_labels_not_detected`
- active-source-set graph ownership is now closed in runtime evidence:
  rerunning `nepa-knowledge-graph-export` against
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/component_inventory.json`
  passes with `66` checks, `0` failed checks, `2,047` nodes, and `3,582` edges
- the promotion suite no longer reports a full-canonical inventory-ownership failure:
  `full_canonical_corpus_ready=true` and `full_canonical_failure_category_counts={}`
- the active readiness config still records only one validated inventory, so Sequence 4 remains the
  next required boundary for promoting the three validated inventories and seven typed blockers into
  graph/readiness truth without weakening `region1_completeness_claim=false`

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

### Sequence 4 - Active-Source-Set Refresh, Readiness Promotion, And Graph Integration

Goal: refresh the full-canonical derived inventory/currentness/graph lane onto the live active
catalog source set `source-set-5e65d845ce77e1a0`, then promote validated multi-forest inventory
truth into the Region 1 readiness and NEPA 3D graph surfaces from that refreshed replay.

Implementation tasks:

- Re-baseline the tracked build contract to the live active catalog source set:
  update the `active_full_canonical` source-set reference and any paired current-state docs that
  still promote `source-set-34061d1e4bf6c460` as the active catalog.
- Refresh the active-source-set derived lane on `source-set-5e65d845ce77e1a0`, including the
  manifest-driven `forest_plan_components/` replay and the required currentness/graph artifacts
  needed for readiness and viewer truth.
- Update `config/region1_forest_plan_readiness_nepa_3d_v1.json` and any generated companion report
  surfaces so all promoted profiles record validated inventory IDs, counts, and artifact paths.
- Refresh the NEPA 3D source-set export against `source-set-5e65d845ce77e1a0` using that active
  source set's owned multi-forest inventory.
- Ensure the forest-plan lens and related graph summaries now reflect multi-forest component
  presence instead of one component-rich forest plus nine shell profiles.
- Keep `region1_completeness_claim=false` unless every in-scope readiness requirement for every
  tracked forest/grassland profile actually passes.

Acceptance signals:

- `source_library/catalog/source_set_manifest.json`, the tracked build manifest, and the refreshed
  full-canonical derived artifacts all agree on `source-set-5e65d845ce77e1a0` as the active
  full-canonical source set.
- The active graph export uses the active source-set inventory path, not the archived merged
  inventory path and not the older `source-set-34061d1e4bf6c460` replay.
- Region 1 graph promotion no longer stops at Custer Gallatin because of missing component
  inventories.
- Graph validation fails closed if a promoted profile lacks validated inventory coverage.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json

PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The live active catalog source set cannot be replayed cleanly into owned derived artifacts without
  undocumented manual source-set overrides.
- Viewer/readiness truth would overclaim all-Region-1 readiness despite remaining typed blockers.

Implementation refresh slice on 2026-05-10:

- re-anchored the tracked build contract:
  `config/r1_forest_plan_component_inventory_build_manifest.json` now points its
  `active_full_canonical` source-set reference at `source-set-5e65d845ce77e1a0`
- refreshed extraction reuse on the active source set:
  `reuse-inventory` reported `already_current_count=349`, `needs_extract_count=0`, and
  `excluded_count=1`; `extract-build --reuse-existing` then wrote `349/349` extracted rows and
  `75,745` chunks under `source-set-5e65d845ce77e1a0`
- refreshed full-canonical inventory ownership on the active source set:
  `forest-plan-components-build --manifest-path ... --source-set-id source-set-5e65d845ce77e1a0`
  now writes `668` components and `108` standards under
  `source_library/derived/source-set-5e65d845ce77e1a0/forest_plan_components/`
- passing forests improved on the refreshed active-source-set replay:
  `flathead-nf` now validates with `80` components / `20` standards and `kootenai-nf` now
  validates with `1` component / `1` standard, reducing blockers from seven forests to five
- refreshed downstream derived lane on the same source set:
  `authority-currentness` passed with `35` authority families and `207` source-currentness records;
  `retrieval-build` passed with `75,745` chunks and `reviewer_ready=true`;
  `evidence-graph-build` passed with `153,187` nodes and `533,938` edges;
  `claim-extract` passed with `101,856` claims;
  `rule-claim-link` passed with `211` links and `0` gaps;
  `nepa-knowledge-graph-export` passed with `66` checks, `0` failed checks, `2,128` nodes, and
  `3,825` edges
- remaining stale surfaces after the refresh slice:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` still records only one validated
  inventory, and `promotion-suite` still reports
  `full_canonical_source_set_id=source-set-34061d1e4bf6c460`,
  `full_canonical_corpus_ready=false`, and
  `full_canonical_failure_category_counts={\"stale_artifact\": 2}`

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
- active full-canonical multi-forest component inventory artifacts under the source set currently
  named by `source_library/catalog/source_set_manifest.json`
- per-forest and aggregate build coverage proving inventory validity
- readiness/profile contract updates reflecting validated inventory promotion
- focused multi-forest builder, resolver-compatibility, and graph-promotion tests

## Required Documentation And Handoff Updates

After each completed sequence, update every affected durable doc before commit. At minimum, review
and update the following when the sequence changes their truth:

- this plan
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`
- `docs/SESSION_HANDOFF.md`

Do not defer doc alignment to the last sequence. Sequence closeout is incomplete until the docs and
handoff that describe that sequence are aligned and committed with it.

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
the source set currently named by `source_library/catalog/source_set_manifest.json` and a refreshed
`nepa-knowledge-graph-export` replay against that same active source set.

## Acceptance Criteria

- The source set currently named by `source_library/catalog/source_set_manifest.json` owns a
  canonical multi-forest `forest_plan_components/` artifact family.
- Every currently tracked Region 1 forest/grassland profile in the readiness matrix has a tracked
  build contract and a validated component inventory, or the milestone stops on an explicit typed
  blocker.
- `component_inventory_build_required` is eliminated as the steady-state status for the current
  Region 1 roster at closeout.
- Multi-forest build coverage fails on duplicate component IDs, duplicate standards, source-set
  drift, missing component IDs, or incomplete roster coverage.
- Resolver consumers remain compatible with the canonical source-set inventory path.
- The NEPA 3D graph export uses the active source-set inventory path and no longer borrows the
  archived Custer-only inventory or an older full-canonical replay for active full-canonical
  promotion.
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

Close each completed sequence with one local atomic commit only after that sequence's verification
passes and the affected docs/handoff are aligned. Stage only the verified sequence slice. Leave
unrelated existing worktree changes alone, including the current viewer-default edits and unrelated
root-level `East_Crazies_*` draft outputs unless the user explicitly broadens scope.

Do not batch multiple completed sequences into one commit, and do not advance to the next sequence
with stale docs or an uncommitted verified slice.

## Residual Risks And Next Milestone Routing

This milestone promotes component inventory ownership and graph/readiness coverage; it does not by
itself make every Region 1 forest reviewer-ready for package review. After this milestone, the next
lane should be one of:

- deepen resolver/profile term coverage and evaluation fixtures for additional forests;
- move from inventory promotion to package-level forest-plan review promotion on selected forests;
- or close remaining source-readiness/currentness blockers that still prevent broader Region 1
  completeness claims after inventory validation is green.
