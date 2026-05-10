# NEPA 3D Readiness Blocker Clarity Milestone Plan

Date: 2026-05-10

Status: Completed

Closeout status on 2026-05-10: the contract/exporter/viewer slice is implemented, the archived
merged source-set export for `source-set-8a4005c8a083af1a` has been refreshed under the new
contract with `validation_passed=true`, `65` checks, `0` failed checks, `1,789` nodes, and
`2,808` edges, and a local browser smoke verified the legend, filters, blocked-domain-node detail
rail, and explicit-blocker-edge detail rail against that refreshed export.

Owner context: This is a bounded post-Milestone-7 NEPA 3D follow-on. It applies only to readiness
semantics for graph-visible red nodes and edges in the exporter contract, exporter implementation,
viewer rendering, tests, and supporting docs.

## Purpose

The current NEPA 3D graph uses red for three different things:

- synthetic `readiness_blocker:*` nodes created by `_add_blocker(...)` in
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`;
- normal domain nodes that are `display_status="readiness_blocked"`, especially blocked Region 1
  forest-plan surfaces and currentness-failed authority families;
- relationship edges that are shown red either because they are explicit
  `HAS_READINESS_BLOCKER` edges or because the exporter marked an otherwise normal domain edge as
  `display_status="readiness_blocked"`.

That overloading is enough to preserve raw readiness truth, but it is not explicit enough for a
reviewer-facing graph. A reviewer can currently see that something is red without being able to
reliably answer whether the red item is:

- the blocker itself;
- a blocked domain surface that remains important to inspect; or
- a relationship edge that is only red because an owning node is blocked.

This milestone exists to make that distinction explicit, exported, testable, and viewer-visible
without weakening the repo's existing readiness boundary. Review update on 2026-05-10: the live
graph surface needs one tighter distinction than the original draft implied. Explicit blocker edges
are not limited to `HAS_READINESS_BLOCKER`; review and currentness surfaces can also emit red edges
such as `NEEDS_ADJUDICATION` or `BLOCKED_BY` when they target a blocker record. The implementation
therefore uses one contract-owned `readiness_semantic_class` field that separates synthetic blocker
nodes, blocked domain nodes, explicit blocker edges, and blocked relationship edges while
preserving the existing `readiness_blockers` taxonomy.

## Current Evidence

- `config/nepa_3d_graph_contract_v1.json` defines the allowed blocker taxonomy at lines `469-481`,
  including `missing_source`, `official_source_gap`, `stale_artifact`,
  `adjudication_needed`, `package_fixture_missing`, `forest_profile_not_ready`, and
  `fsh_chapter_delta_required`.
- `_add_blocker(...)` in `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py:1975-2008` creates
  synthetic `readiness_blocker` nodes and `HAS_READINESS_BLOCKER` edges, both with
  `display_status="readiness_blocked"`.
- Region 1 forest-plan nodes and relationship edges inherit the same blocked display status from
  `_region1_profile_display(...)` and `_region1_profile_readiness_blockers(...)`, then apply that
  status to `forest_unit`, `forest_plan`, `HAS_FOREST_PLAN`, and `HAS_SOURCE_RECORD` in
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py:999-1104`.
- Authority families can also become `display_status="readiness_blocked"` when currentness fails in
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py:2414-2433`.
- The viewer currently colors all blocked nodes from one shared `STATUS_COLORS.readiness_blocked`
  value in `viewer/nepa-3d/app.js:19-30`, and colors all blocked edges red when either
  `edge_type === "HAS_READINESS_BLOCKER"` or `display_status === "readiness_blocked"` in
  `viewer/nepa-3d/app.js:2152-2158`.
- Current tests prove that blocker nodes and blocked nodes exist, but they do not yet fail closed
  when red semantics are ambiguous across synthetic blocker nodes, blocked domain nodes, and blocked
  relationship edges.

## Goal

Export and render readiness semantics so every red node and edge in the NEPA 3D graph can be
distinguished as one of these classes:

- synthetic blocker node;
- blocked domain node;
- explicit blocker edge;
- blocked relationship edge.

Completion requires the distinction to be contract-governed, exported by the builder, visible in the
viewer legend/detail/filter surfaces, and locked by fixtures plus focused tests.

## Non-Goals

- Do not resolve the underlying readiness blockers themselves in this milestone.
- Do not broaden this work into Beaverhead inventory completion, source-gap recovery,
  applicability adjudication closure, or review replay promotion.
- Do not let the viewer invent readiness semantics that are not present in the exported graph.
- Do not change the source-of-truth boundary away from catalog, currentness, readiness, and review
  artifacts.
- Do not rerun broad downloader or corpus workflows unless a narrowly scoped graph export refresh is
  required for verification.
- Do not stage ignored `source_library/` artifacts unless repository policy changes explicitly.

## Scope

- NEPA 3D graph contract surfaces for readiness-blocked node and edge semantics.
- `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py` readiness export behavior for blocker
  nodes, blocked domain nodes, and blocked relationship edges.
- `viewer/nepa-3d/` legend, tooltip, detail-rail, and filter semantics for the red classes.
- Focused fixtures and tests that fail closed if those classes drift together again.
- Docs and handoff updates that explain the meaning of red in the graph.

## Out Of Scope

- New blocker types beyond the existing contract unless current exported evidence proves one is
  missing.
- Changes to applicability, compliance, or promotion verdict logic.
- Cosmetic-only viewer restyling that does not improve blocker semantics.
- Replacing the broader `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md`; this milestone should be
  tracked as a focused follow-on, not a rewrite of the full NEPA 3D roadmap.

## Owner Surfaces

- Contract: `config/nepa_3d_graph_contract_v1.json`,
  `src/usfs_r1_ea_sources/nepa_3d_graph_contract.py`,
  `tests/test_nepa_3d_graph_contract.py`,
  `tests/fixtures/nepa_3d_graph/`
- Exporter: `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  `tests/test_nepa_knowledge_graph_export.py`
- Viewer: `viewer/nepa-3d/app.js`, `viewer/nepa-3d/index.html`,
  `viewer/nepa-3d/styles.css`, `tests/test_nepa_3d_viewer.py`
- Durable docs: `docs/NEPA_3D_READINESS_BLOCKER_CLARITY_MILESTONE_PLAN.md`,
  `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md`, `docs/CURRENT_SYSTEM_STATE.md`, `README.md`,
  `docs/OUTPUT_SCHEMAS.md`, `docs/SESSION_HANDOFF.md`

## Placement Rules

- Readiness semantics must be exporter-owned and contract-governed. The viewer may render or explain
  them, but it must not infer the semantic class of a red item only from `display_status`.
- Synthetic blocker nodes must continue to be explicit graph records, not a viewer-only overlay.
- If a new readiness-semantics payload is added, it must be a contract-validated export field or a
  contract-validated structured metadata surface. Do not hide it in free-form viewer copy.
- Blocked relationship edges must preserve the owning subject and blocker types that caused the edge
  to render as blocked.
- Keep current readiness blocker types as data. Do not hardcode forest-specific or family-specific
  color logic in the viewer.
- Preserve existing readiness and promotion truth. This milestone clarifies graph semantics; it does
  not promote additional units, families, reviews, or source sets.

## Weak-Point Prevention Contract

- Weak point forecast: red semantics remain overloaded even after the milestone because the contract
  still lacks an explicit semantic class for blocked graph items.
  Owner surface: `config/nepa_3d_graph_contract_v1.json`, `tests/test_nepa_3d_graph_contract.py`,
  `tests/fixtures/nepa_3d_graph/`
  Prevention gate: contract fixtures and contract tests require an explicit readiness-semantic class
  for every exported synthetic blocker node and every exported blocked node or edge.
  Fail threshold: any red node or edge validates without an explicit semantic class.
  Controlled violation: remove the semantic class from one blocker node fixture and one blocked edge
  fixture; validation must fail.
  Future-Codex misuse scenario: a future session reverts to relying on `display_status` alone; the
  contract gate must fail before that lands.
- Weak point forecast: blocked domain nodes stay disconnected from the blocker type or owning
  subject that caused the blocked state.
  Owner surface: `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  `tests/test_nepa_knowledge_graph_export.py`
  Prevention gate: exporter tests require blocked forest-plan and authority-family nodes to export
  their blocker types and, where applicable, the owning node or readiness source that explains the
  blocked state.
  Fail threshold: a blocked domain node renders red but cannot explain which blocker types caused
  the state.
  Controlled violation: strip blocker metadata from a blocked forest unit and a currentness-failed
  authority family in fixtures; focused tests must fail.
  Future-Codex misuse scenario: a future session colors a node red because it is blocked but drops
  the actual blocker reason; exporter tests must catch that.
- Weak point forecast: blocked relationship edges remain indistinguishable from explicit
  `HAS_READINESS_BLOCKER` edges in the viewer.
  Owner surface: `viewer/nepa-3d/app.js`, `tests/test_nepa_3d_viewer.py`
  Prevention gate: viewer tests require distinct legend/detail/filter language for synthetic blocker
  edges versus blocked domain relationships.
  Fail threshold: the viewer still treats all red edges as one class without exposing whether the
  edge is a blocker edge or an inherited blocked relationship.
  Controlled violation: remove the distinct legend or detail-rail language for one blocked
  relationship class; viewer tests must fail.
  Future-Codex misuse scenario: a future session changes the palette or edge rendering and quietly
  collapses both edge classes back together; viewer tests must catch that.
- Weak point forecast: docs drift and future operators misread red as a legal or review conclusion
  instead of a readiness state.
  Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md`, `docs/SESSION_HANDOFF.md`
  Prevention gate: docs review plus `git diff --check` prove the red taxonomy is documented in the
  same closeout as the code/tests.
  Fail threshold: implementation lands without one durable doc that defines the three red classes.
  Controlled violation: remove the taxonomy section from docs during closeout; docs review should
  fail the milestone.
  Future-Codex misuse scenario: a later session changes viewer behavior and updates code only; the
  closeout policy below keeps docs and handoff as an explicit gate.

## Milestone Sequence

### Sequence 0 - Contract The Red Taxonomy Before Code Changes

Goal: add a contract-level readiness taxonomy that distinguishes synthetic blocker nodes, blocked
domain nodes, and blocked relationship edges before viewer or exporter behavior changes.

Implementation tasks:

- Extend the NEPA 3D graph contract to require an explicit semantic class for all red graph items.
- Add minimal source-set/review fixtures that cover:
  - one synthetic blocker node plus `HAS_READINESS_BLOCKER` edge;
  - one blocked forest-plan node;
  - one currentness-failed authority-family node;
  - one blocked forest-plan relationship edge that is not itself a blocker node edge.
- Add negative fixtures or targeted mutations that prove the contract fails when red semantics are
  absent or inconsistent.

Acceptance signals:

- Contract validation distinguishes blocker-node, blocked-node, and blocked-edge cases.
- Minimal fixtures still validate only when semantic classes are present.
- Contract docs or schema notes name the three red classes explicitly.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py
git diff --check
```

Stop conditions:

- A semantics payload cannot be expressed without breaking the existing graph contract in a way that
  needs a broader versioning decision.
- The implementation can only represent the distinction in viewer-local code without contract
  support.

### Sequence 1 - Export Explicit Red Semantics From The Builder

Goal: make the exporter emit the distinction instead of relying on viewer inference.

Implementation tasks:

- Update `_add_blocker(...)` to stamp explicit synthetic-blocker semantics onto blocker nodes and
  blocker edges.
- Update blocked Region 1 forest-plan nodes and their blocked relationship edges so they export a
  blocked-domain or blocked-relationship semantic class plus the blocker types that caused the
  state.
- Update currentness-failed authority-family nodes so they export the same explicit blocked-domain
  semantics instead of relying on `display_status` alone.
- Keep the existing `readiness_blockers` list, but ensure the new semantic class is separate from
  the blocker-type list.

Acceptance signals:

- Every exported synthetic blocker node has an explicit blocker semantic class and blocker type.
- Every exported blocked domain node has an explicit blocked-domain semantic class and blocker type
  list.
- Every exported blocked relationship edge has an explicit blocked-edge semantic class and can point
  back to the owning blocked subject or equivalent readiness cause.
- Exporter tests fail when any red item is missing its semantic class or cause chain.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Export changes require scanning raw artifact paths instead of catalog/currentness/readiness
  surfaces.
- A blocked relationship edge cannot preserve enough exported cause data to explain why it is red.

### Sequence 2 - Make The Viewer Explain The Red Taxonomy

Goal: make the viewer distinguish red classes in legend, detail, filter, and styling without
changing readiness truth.

Implementation tasks:

- Update viewer rendering so synthetic blocker nodes, blocked domain nodes, and blocked
  relationship edges are distinguishable by legend and detail-rail language, and by styling when
  that can be done without implying new legal meaning.
- Stop relying on `edge_type === "HAS_READINESS_BLOCKER"` or
  `display_status === "readiness_blocked"` alone as the only way to infer edge meaning in the UI.
- Add or extend a filter surface so reviewers can isolate synthetic blocker nodes separately from
  blocked domain surfaces and blocked relationships.
- Update tooltips/detail panels so a reviewer can tell whether a selected red item is:
  - the blocker record itself;
  - a blocked forest or authority surface; or
  - a blocked relationship inherited from an upstream blocked owner.

Acceptance signals:

- The viewer legend names the red classes instead of showing one undifferentiated blocked status.
- The detail rail for a selected red item states which red class it belongs to and which blocker
  types apply.
- A reviewer can filter down to blocker nodes without losing the ability to inspect blocked domain
  nodes and blocked relationships separately.
- Viewer tests fail if the taxonomy collapses back to one undifferentiated red class.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_viewer.py
git diff --check
```

If the viewer implementation changes behavior materially, also run the local browser verification
workflow against the current graph-capable dataset and confirm that the legend, filters, and detail
panel expose the new taxonomy on desktop and mobile without blank-canvas regressions.

Stop conditions:

- The only way to distinguish the red classes is by adding non-exported viewer heuristics.
- Viewer changes make a blocked relationship edge look like an independent blocker node.

### Sequence 3 - Refresh Durable Docs And Handoff In The Same Slice

Goal: keep the graph/exporter/viewer semantics documented so later sessions do not undo the work.

Implementation tasks:

- Update `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md` with this milestone as a focused follow-on
  to the existing NEPA 3D ladder.
- Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/OUTPUT_SCHEMAS.md` so the meaning
  of red is explicit in current system documentation.
- Update `docs/SESSION_HANDOFF.md` with the finished taxonomy, verification commands, and next
  blocker-reduction route.

Acceptance signals:

- One durable doc explicitly defines the three red classes.
- README/current-state/schema docs align with the implemented exporter and viewer behavior.
- Session handoff names the exact tests and any residual ambiguity left for a later milestone.

Required verification:

```bash
git diff --check
```

Stop conditions:

- The milestone can only be explained in chat and not in repo docs.
- Docs would need to claim that blockers are resolved rather than merely clarified.

### Sequence 4 - Closeout Gate

Goal: close the milestone only when the semantic distinction is testable, documented, and isolated
from unrelated worktree noise.

Implementation tasks:

- Run the focused contract, exporter, viewer, and architecture verification stack.
- Stage only the verified blocker-clarity slice.
- Leave unrelated dirty or untracked files alone, including current root-level `East_Crazies_*`
  drafts and `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`.

Acceptance signals:

- Focused tests pass.
- Docs and handoff updates are in the same closeout slice.
- No unrelated local reports or ignored `source_library/` outputs are staged.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py tests/test_nepa_knowledge_graph_export.py tests/test_nepa_3d_viewer.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Required verification fails.
- The blocker-clarity slice cannot be separated safely from unrelated worktree changes.

## Required Implementation Artifacts

- contract updates for explicit readiness semantics
- minimal graph fixtures and negative mutations that fail closed on ambiguity
- exporter updates for blocker-node, blocked-node, and blocked-edge semantics
- viewer legend/detail/filter changes driven by exported readiness semantics
- focused contract/exporter/viewer tests

## Required Documentation And Handoff Updates

- this plan file
- `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `README.md`
- `docs/SESSION_HANDOFF.md`

## Required Verification Gates

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py
PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_viewer.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

If viewer behavior changes materially, also verify the local viewer through the browser workflow on
the current graph-capable dataset.

## Acceptance Criteria

- Every red node or edge in the exported graph has an explicit semantic class that distinguishes
  blocker node, blocked domain node, or blocked relationship edge.
- The exporter still preserves the existing readiness blocker types, but blocker type and semantic
  class are no longer the same concept.
- A blocked forest unit, forest plan, or authority family can explain which blocker types caused
  its red state.
- A blocked relationship edge can explain whether it is an explicit blocker edge or an inherited
  blocked domain relationship.
- The viewer legend, detail rail, and filters expose the distinction without inventing new
  readiness truth.
- Focused tests fail closed when the distinction is removed or collapsed.
- Closeout lands with docs and handoff updates in the same verified milestone slice.

## Stop Conditions

- The distinction cannot be represented in exported graph data without a broader versioning or
  compatibility decision.
- Implementation would require weakening current readiness or promotion gates.
- Implementation would require broad corpus reruns unrelated to this graph/export/viewer slice.
- Required tests or viewer verification expose ambiguity that cannot be resolved within this
  milestone's bounded scope.

## Local Commit Closeout Policy

Close the milestone with one local atomic commit only after the focused verification stack passes.
Stage only the blocker-clarity implementation, tests, docs, and handoff updates. Do not stage
unrelated dirty or untracked files already present in the repo.

## Residual Risks And Next Milestone Routing

This milestone clarifies red semantics; it does not reduce the blocker counts. Residual risk remains
that the graph can now explain blockers more clearly while the underlying Region 1 and review-scoped
blockers still exist. After this milestone, the next lane should be one of:

- reduce actual readiness blockers, such as Beaverhead component-inventory completion, official
  source-gap closure, or currentness recovery; or
- add blocker-summary/reporting surfaces if reviewer workflows need grouped blocker counts by forest,
  authority family, or review phase after the semantic distinction is stable.
