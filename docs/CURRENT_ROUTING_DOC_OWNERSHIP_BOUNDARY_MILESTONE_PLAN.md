# Current Routing Doc Ownership Boundary Milestone Plan

Date: 2026-05-26

Status: resolved locally 2026-05-26 inside the broader architecture-governance rebaseline; the
short-route contract is restored, `README.md` is back to a stable public entrypoint, and volatile
live state now routes back through `docs/CURRENT_SYSTEM_STATE.md` plus
`docs/SESSION_HANDOFF.md`

Owner context: This is a fresh standalone child packet. It does not append more work into
`docs/CURRENT_ROUTING.md` itself, and it does not reopen the full
`docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md` umbrella. It narrows that broader
governance packet to one exact issue: restore a truthful ownership boundary between
`docs/CURRENT_ROUTING.md`, `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
`docs/SESSION_HANDOFF.md`.

## Purpose

Restore the repo's short-route contract and remove duplicated live-state narration from the wrong
docs.

The current weakness is not only that `docs/CURRENT_ROUTING.md` is too long. The deeper problem is
that repo state ownership has drifted:

- `docs/CURRENT_ROUTING.md` now mixes short routing, deep live counts, packet history, and current
  operational detail;
- `README.md` duplicates live routed-state prose instead of staying a stable public entrypoint; and
- `tests/test_architecture_quality.py` currently encodes a brittle cross-doc alignment pattern that
  rewards synchronized repeated prose instead of one canonical source of current truth.

This packet exists to make freshness cheap again: route docs should route, current-state docs should
own volatile truth, and the architecture-quality gate should enforce that boundary directly.

## Current Evidence

### Live boundary drift on 2026-05-26

- `docs/CURRENT_ROUTING.md` is `277` lines long even though it declares itself the short first stop.
- `README.md` still contains a dated `Current routed state on 2026-05-25:` section plus broader
  distributed live replay, corpus, and architecture status details.
- `tests/test_architecture_quality.py` currently enforces:
  - `docs/CURRENT_ROUTING.md` line-count plus link presence via
    `test_current_routing_doc_stays_short_and_linked()`
  - a cross-doc volatile-text alignment assertion via
    `test_full_canonical_gold_docs_stay_aligned()`, which currently expects
    `README.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
    `docs/SESSION_HANDOFF.md` to all carry the same live gold-state phrases
- The current gate shape makes the ownership problem worse:
  - it does not prevent `README.md` from becoming a second current-state log
  - it only weakly constrains `docs/CURRENT_ROUTING.md` beyond length
  - it treats repeated volatile prose across multiple docs as a success condition
- The selected architecture finding is therefore correct: freshness currently depends on repeated
  synchronized prose edits instead of a single canonical owner for live state.

### Intended durable ownership after this packet

- `docs/CURRENT_ROUTING.md`: short first-stop route only
- `README.md`: stable public entrypoint that links to current route and deeper state docs instead
  of carrying distributed live source-set and replay-state narration
- `docs/CURRENT_SYSTEM_STATE.md`: canonical tracked owner for volatile current repo state
- `docs/SESSION_HANDOFF.md`: canonical fresh-session owner for current packet, current blocker, and
  next truthful slice

## Goal

Re-establish a fail-closed documentation ownership contract in which:

- `docs/CURRENT_ROUTING.md` stays under `40` lines and acts only as a route index;
- `README.md` links to live state instead of duplicating it;
- `docs/CURRENT_SYSTEM_STATE.md` and the top of `docs/SESSION_HANDOFF.md` own volatile current
  architecture and replay status; and
- `tests/test_architecture_quality.py` enforces those roles directly instead of asserting repeated
  volatile text across multiple docs.

## Non-Goals

- Do not resolve the live `9` oversized-file backlog in this packet.
- Do not rewrite the active replay-repair packet or alter replay semantics.
- Do not turn `docs/CURRENT_ROUTING.md` into another current-state summary while trying to shorten
  it.
- Do not move live state into chat-only explanations; the result must stay repo-grounded.
- Do not weaken or delete the architecture-quality gate to get green.
- Do not rewrite historical milestone outcomes just to hide later drift.

## Scope

In scope:

- `docs/CURRENT_ROUTING.md`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/AGENT_START_HERE.md` if link ownership needs to stay aligned
- `tests/test_architecture_quality.py`
- narrowly-related helper extraction if needed to keep the test readable

Out of scope:

- `config/architecture_large_file_inventory_v1.json` and the oversized-file inventory contents
- source/runtime/test hotspot splits
- replay/eval semantic state beyond moving its ownership to the correct docs
- broad architecture-doc rewording outside the selected route/ownership issue

## Owner Surfaces

| Surface | Required role after closeout | Required verification |
| --- | --- | --- |
| `docs/CURRENT_ROUTING.md` | short route only; no deep live-state narration | `wc -l`, focused pytest, targeted grep |
| `README.md` | stable public entrypoint; links to route/current-state docs instead of duplicating volatile state | focused pytest, targeted grep |
| `docs/CURRENT_SYSTEM_STATE.md` | tracked canonical owner for volatile current repo state | focused pytest, targeted grep |
| `docs/SESSION_HANDOFF.md` | fresh-session current owner for active packet, blocker, and next slice | focused pytest, targeted grep |
| `docs/AGENT_START_HERE.md` | entrypoint doc that points document work back through `docs/CURRENT_ROUTING.md` | focused pytest readback |
| `tests/test_architecture_quality.py` | machine-check the ownership boundary and keep the short-route contract honest | focused pytest, ruff, compileall |

## Placement Rules

- `docs/CURRENT_ROUTING.md` may contain start order, active packet pointers, and links to deeper
  docs only. It must not carry a `## Live Facts`-style state section after closeout.
- `README.md` may explain the product, public entrypoints, and where current state lives, but it
  must not own a dated routed-state block, live source-set IDs, or replay-status counters.
- Volatile counts, replay mismatches, source-set IDs, blocker counts, and next truthful slice text
  belong in `docs/CURRENT_SYSTEM_STATE.md` and the top section of `docs/SESSION_HANDOFF.md`.
- The test gate must prefer ownership assertions over repeated token assertions. If the same live
  sentence is required in four docs, the boundary is wrong.
- Keep the fix docs-only and gate-focused. If a broader architecture-control-plane issue appears,
  route it back to `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md` instead of silently
  expanding this packet.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | The packet starts from stale or mis-scoped evidence and only trims prose cosmetically | this plan, `docs/CURRENT_ROUTING.md`, `README.md`, `tests/test_architecture_quality.py` | baseline `wc -l`, focused pytest, targeted grep for duplicated live-state blocks | the baseline does not reproduce the long route doc, dated README state block, and current brittle test shape | the pre-edit baseline must still show the duplicated-state problem before any rewrite starts | a future session shortens one paragraph but leaves the ownership boundary broken |
| `1` | `docs/CURRENT_ROUTING.md` is shortened, but the deep state is merely hidden or moved into another route doc | `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md` | focused pytest, `wc -l`, grep for disallowed route sections/tokens | `docs/CURRENT_ROUTING.md` remains above `40` lines, still has `## Live Facts`, or still carries volatile state blocks | require a failing negative-path assertion for long or state-heavy current-routing content | a future session keeps adding packet facts back into `docs/CURRENT_ROUTING.md` because the line cap alone is easy to game |
| `2` | `README.md` keeps duplicating volatile state because the gate only checks links and not ownership | `README.md`, `tests/test_architecture_quality.py` | focused pytest plus targeted grep for dated routed-state blocks and live source-set markers | `README.md` still contains a dated routed-state section, live source-set IDs, or deep replay-state prose after closeout | require a negative-path assertion that fails when README owns a dated or distributed live current-state section | a future session updates live counts in README because the current-state doc feels too deep |
| `3` | The test gate still encodes repeated volatile phrases across multiple docs instead of one canonical owner | `tests/test_architecture_quality.py` | focused pytest, controlled test rewrite review | the gate still requires the same live volatile phrases in `README.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` | replace the repeated-token assertion with ownership-based assertions and prove the old pattern would fail | a future session greens the suite by copying one more live phrase into another doc |
| `4` | Closeout leaves no explicit owner for live state or no explicit next architecture routing | `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, this plan | focused pytest, targeted grep, `git diff --check` | current state is no longer duplicated, but the volatile truth is not clearly owned in tracked current-state docs | targeted readback must confirm both owner docs still carry the live state after route/README cleanup | a future session removes duplicated state everywhere and accidentally strands the live route with no canonical current owner |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Boundary baseline and current owner declaration | `resolved` |
| `1` | Short-route contract restoration | `resolved` |
| `2` | README ownership reduction | `resolved` |
| `3` | Architecture-quality gate conversion from repeated-text alignment to owner-boundary enforcement | `resolved` |
| `4` | Current-state and handoff closeout alignment | `resolved` |

### Milestone `0`: Boundary baseline and current owner declaration

Outcome label: `resolved`

Work:

- Reproduce the current failure with:
  - `wc -l docs/CURRENT_ROUTING.md`
  - focused architecture-quality pytest
  - targeted grep for the dated routed-state block in `README.md`
- Record the intended owner surfaces in this plan before editing any doc copy.

Required verification:

```bash
git status -sb
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
wc -l docs/CURRENT_ROUTING.md
rg -n "Current routed state on|## Live Facts|five still-unmapped live authorities|zero-link structural surface|generated diagnostic" README.md docs/CURRENT_ROUTING.md tests/test_architecture_quality.py
git diff --check
```

Closeout on 2026-05-26:

- The baseline was reproduced before edits: `docs/CURRENT_ROUTING.md` was `277` lines, `README.md`
  still owned a dated routed-state block, and the architecture-quality gate still rewarded
  repeated volatile prose across multiple docs.

### Milestone `1`: Short-route contract restoration

Outcome label: `resolved`

Work:

- Reduce `docs/CURRENT_ROUTING.md` to a true route index at `<= 40` lines.
- Keep only:
  - start order
  - active implementation packet
  - this doc-boundary follow-on packet
  - links to deeper current-state docs
- Remove route-local deep state narration, packet history, and live counts from `docs/CURRENT_ROUTING.md`.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
wc -l docs/CURRENT_ROUTING.md
rg -n "## Live Facts|candidate_authority_count|reviewer_ready_slot_count|source-set-" docs/CURRENT_ROUTING.md
git diff --check
```

Closeout on 2026-05-26:

- `docs/CURRENT_ROUTING.md` is now `32` lines and no longer carries a `## Live Facts` section,
  live source-set counts, or replay-state tokens.

### Milestone `2`: README ownership reduction

Outcome label: `resolved`

Work:

- Remove the dated routed-state block and the remaining distributed live
  corpus/replay baselines from `README.md`.
- Replace it with a stable pointer to:
  - `docs/CURRENT_ROUTING.md` for the short route
  - `docs/CURRENT_SYSTEM_STATE.md` for tracked current state
  - `docs/SESSION_HANDOFF.md` for fresh-session live packet status
- Preserve the README's public product description and entrypoint guidance.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
wc -l README.md
rg -n "Current routed state on" README.md
rg -n "Canonical source-register refoundation status on|Historical local import baseline on|current_promotion_ready|reviewer_ready=true|source-set-[0-9a-f]{16}" README.md
rg -n "docs/CURRENT_ROUTING.md|docs/CURRENT_SYSTEM_STATE.md|docs/SESSION_HANDOFF.md" README.md
git diff --check
```

Closeout on 2026-05-26:

- `README.md` is now back to a stable public-entrypoint role. It no longer owns the dated
  routed-state block or distributed live source-set/replay baselines, and it points readers back
  to `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
  the tracked architecture inventory.

### Milestone `3`: Architecture-quality gate conversion

Outcome label: `resolved`

Work:

- Replace the brittle repeated-text alignment expectation in
  `tests/test_architecture_quality.py` with ownership-boundary assertions such as:
  - `docs/CURRENT_ROUTING.md` stays short and free of deep-state sections
  - `README.md` stays concise and does not own dated or distributed live current-state prose
  - `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md` remain the canonical owners for
    volatile current-state wording
- If helper extraction is needed, keep the negative-path assertions at least as strong as the
  current live drift checks.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests/test_architecture_quality.py
git diff --check
```

Closeout on 2026-05-26:

- `tests/test_architecture_quality.py` now checks ownership boundaries directly: short-route
  limits, README stable-entrypoint ownership, current-state/handoff ownership of volatile
  architecture text, and exact inventory truth.

### Milestone `4`: Current-state and handoff closeout alignment

Outcome label: `resolved`

Work:

- Ensure the removed duplicated state still exists in the correct owners:
  - `docs/CURRENT_SYSTEM_STATE.md`
  - top section of `docs/SESSION_HANDOFF.md`
- Record this child packet in the handoff as a resolved closeout child inside the broader
  architecture-governance rebaseline.
- Keep the broader architecture governance packet as umbrella context only.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
rg -n "docs/CURRENT_ROUTING_DOC_OWNERSHIP_BOUNDARY_MILESTONE_PLAN.md|candidate_authority_count|reviewer_ready_slot_count|actual_contract_status" docs/SESSION_HANDOFF.md docs/CURRENT_SYSTEM_STATE.md
git diff --check
```

Closeout on 2026-05-26:

- `docs/CURRENT_SYSTEM_STATE.md` and the top of `docs/SESSION_HANDOFF.md` retain the live
  architecture state removed from `README.md` and `docs/CURRENT_ROUTING.md`.
- This child packet is now recorded in the handoff as a resolved closeout child rather than a
  queued next step.

## Required Implementation Artifacts

- updated `docs/CURRENT_ROUTING.md`
- updated `README.md`
- updated `docs/CURRENT_SYSTEM_STATE.md`
- updated `docs/SESSION_HANDOFF.md`
- updated `tests/test_architecture_quality.py`
- this plan file

## Required Documentation And Handoff Updates

- keep this plan current with milestone status and final closeout wording
- update the top section of `docs/SESSION_HANDOFF.md` to record this child as a resolved closeout
  inside the broader architecture-governance rebaseline
- update `docs/CURRENT_SYSTEM_STATE.md` if live state text is relocated out of route/README surfaces
- keep `docs/AGENT_START_HERE.md` aligned if its link guidance changes indirectly

## Required Verification Gates

```bash
git status -sb
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests/test_architecture_quality.py
wc -l docs/CURRENT_ROUTING.md
wc -l README.md
rg -n "Current routed state on|## Live Facts|five still-unmapped live authorities|zero-link structural surface|generated diagnostic" README.md docs/CURRENT_ROUTING.md
rg -n "Canonical source-register refoundation status on|Historical local import baseline on|current_promotion_ready|reviewer_ready=true|source-set-[0-9a-f]{16}" README.md
git diff --check
```

## Acceptance Criteria

- `docs/CURRENT_ROUTING.md` is `<= 40` lines and no longer contains a deep live-state section.
- `README.md` no longer contains a dated routed-state block.
- `README.md` no longer carries distributed live source-set IDs or replay-status counters.
- `README.md` still points users to `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md`.
- `tests/test_architecture_quality.py` passes while enforcing doc ownership roles directly.
- The architecture-quality gate no longer requires the same volatile live-state phrases across
  `README.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md`.
- `docs/CURRENT_SYSTEM_STATE.md` and the top of `docs/SESSION_HANDOFF.md` still carry the live
  volatile state removed from `README.md` and `docs/CURRENT_ROUTING.md`.
- The closeout is docs-only and stages only the verified ownership-boundary slice.

## Stop Conditions

- Stop if shrinking `docs/CURRENT_ROUTING.md` would require replay-logic or current-state semantic
  changes rather than doc ownership cleanup.
- Stop if the architecture-quality gate cannot be rewritten without weakening the negative-path
  protection that caught this drift.
- Stop if the same packet starts absorbing the oversized-file inventory or other broader governance
  work from the umbrella architecture plan.

## Local Commit Closeout Policy

- Stage only the verified doc-ownership boundary slice.
- Leave unrelated runtime, corpus, and inventory work untouched.
- Include the updated route doc, README, current-state/hand-off docs, focused architecture test,
  and this plan in the same local atomic commit.
- Record the parent implementation closeout commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the packet as incomplete until that local commit exists.

## Residual Risks And Next Milestone Routing

If this packet closes correctly, the remaining architecture issue is no longer route/README
duplication. The remaining issue is the separately routed oversized-file backlog:

- source-owner backlog beginning with
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `src/usfs_r1_ea_sources/extract_runtime.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`, and
  `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`
- then the reopened oversized test owners from `config/architecture_large_file_inventory_v1.json`

Those remaining owner-reduction issues now start from the resolved umbrella packet
`docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md` and its live inventory artifact rather
than from this child packet.

Parent implementation closeout commit:

- `182bfd6` (`Rebaseline architecture governance control plane`)
