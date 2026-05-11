# Replay Context Contract Hardening Milestone Plan

Date: 2026-05-10
Status: implemented
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources`; active catalog source set `source-set-5e65d845ce77e1a0`; archived merged replay source set `source-set-8a4005c8a083af1a`; frozen proving review `v1-cg-ecid-compliance-review`; current replay review `v1-cg-ecid-source-delta-review`

## Purpose

Add one durable, tracked replay-context authority for noncanonical review replays so replay-scoped
evaluation cannot silently fall back to the active catalog.

This milestone is an architecture-hardening slice, not the immediate next reviewer-readiness slice
for the current East Crazies replay. The current handoff already routes immediate replay-readiness
work to applicability adjudications, forest-plan component-gap repair, and then replayed
compliance-review regeneration. This plan must not claim those content blockers are solved.

## Current Evidence

- The active catalog source set is `source-set-5e65d845ce77e1a0`.
- The archived merged replay target for `v1-cg-ecid-source-delta-review` is
  `source-set-8a4005c8a083af1a`, with the archived merged catalog gate under
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`.
- `run_phase_aligned_eval(...)` falls back to the active catalog source set when `source_set_id` is
  omitted, and separately defaults `catalog_dir` to `source_library/catalog/` when it is omitted.
  That leaves a real mixed-context risk for archived replays.
- `phase-eval` already accepts `--catalog-dir`, and
  `applicability-authority-universe` already accepts explicit archived replay surfaces through
  `--catalog-path` and `--source-set-manifest-path`. The missing piece is one durable replay-context
  authority instead of operator memory.
- The current replay is still blocked on content work:
  `phase_eval_results.json` reports `12/17` phases passing with `reviewer_ready=false`,
  `applicability_validation` failing, `compliance_review` absent, and
  `forest_plan_component_eval` failing `9/35`.
- The current handoff routes the next replay-readiness work to:
  `7` applicability adjudications, remaining East Crazies forest-plan component gaps, and only
  then rerunning replay-scoped `compliance-review` and `phase-eval`.
- `config/forest_plan_component_eval_seed.json` is the only tracked forest-plan component eval
  contract. It is pinned to the frozen proving review
  `v1-cg-ecid-compliance-review` on `source-set-ba8d0feae79501b8`.
- The live current replay artifact still records `eval_file=config/forest_plan_component_eval_seed.json`,
  confirming that the repo does not yet have a separate tracked replay eval contract.
- `source_library/` is ignored and not staged by default, so a review-local-only replay manifest
  cannot satisfy this repo's atomic milestone closeout model.

## Goal

Create one tracked replay-context contract for archived review lanes and make replay-scoped phase
evaluation fail closed when that context is missing or mismatched.

Completion means:

- the canonical replay-context authority is tracked under `config/`, not only in ignored review
  directories;
- review-local replay context, if generated, is explicitly derivative and never the authority;
- the plan names one concrete mixed-context reproduction that fails before a misleading replay
  result is accepted;
- replay-scoped phase evaluation can load or validate the tracked replay context and reject active
  catalog fallback for archived replays;
- the current East Crazies replay is used only as the first deterministic consumer of the replay
  context contract, not as a green success gate;
- the milestone leaves replay content repair, replay-specific forest-plan eval promotion, and
  compliance-review regeneration routed to later milestones.

## Non-Goals

- Do not resolve the current replay's `7` applicability adjudications in this milestone.
- Do not resolve the current replay's remaining East Crazies forest-plan component gaps in this
  milestone.
- Do not regenerate or certify replay `compliance-review` artifacts as complete in this milestone.
- Do not add a replay-specific forest-plan component eval contract yet.
- Do not generalize `config/forest_plan_component_eval_seed.json` to cover both the frozen proving
  lane and the current replay in this milestone.
- Do not make `source_library/reviews/<review_id>/` the sole replay-context authority.
- Do not hardcode CGNF-specific wording, forest names, or runtime branches in generic replay logic.
- Do not change ignored-artifact staging policy for `source_library/`.

## Scope

In scope:

- one tracked replay-context schema and canonical location under `config/`;
- one tracked replay-context file for `v1-cg-ecid-source-delta-review`;
- one concrete mixed-context failing reproduction for archived replay phase evaluation;
- fail-closed replay-context loading and validation in the review-scoped phase-eval path;
- focused tests and docs for replay-context authority, mismatch rejection, and override semantics;
- explicit routing that keeps replay content blockers outside this milestone's success claim.

Out of scope:

- applicability adjudication repair;
- forest-plan component extraction/binding repair;
- compliance-review regeneration and reviewer-facing replay artifacts;
- downloader, capture, or catalog rebuild beyond replay-context validation;
- unrelated viewer worktree changes and root-level East Crazies draft exports already present in the
  repo.

## Owner Surfaces

Allowed tracked implementation surfaces:

- `src/usfs_r1_ea_sources/evidence_graph.py`
- `src/usfs_r1_ea_sources/cli_eval.py`
- `src/usfs_r1_ea_sources/cli_review.py` if replay-context loading is shared there
- a new generic helper such as `src/usfs_r1_ea_sources/replay_context.py`
- `config/replay_contexts/`
- `tests/test_cli.py`
- `tests/test_v1_ea_eval.py`
- focused replay-context tests under `tests/`
- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this milestone plan

Ignored or generated surfaces that may be read but not staged by default:

- `source_library/reviews/v1-cg-ecid-source-delta-review/`
- `source_library/reviews/v1-cg-ecid-compliance-review/`
- `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`

## Placement Rules

- The canonical replay-context authority for archived replays must live in tracked config under
  `config/replay_contexts/<review_id>.json`.
- A generated review-local resolved manifest under `source_library/reviews/<review_id>/` is allowed
  only as a derived echo of the tracked config. It cannot be the authority, the only copy, or the
  closeout artifact.
- Drop review-local-only manifest as an implementation option in this milestone.
- The replay-context file must be data-only and review-scoped. Do not encode routing through
  forest-named runtime branches.
- If explicit CLI overrides are accepted, they must either match the tracked replay context or fail
  closed.
- `config/forest_plan_component_eval_seed.json` remains the frozen proving contract in this
  milestone. Do not add `config/<current-replay-forest-plan-eval>.json` here.
- Preserve the distinction between:
  - active catalog truth;
  - frozen proving review truth;
  - archived current replay truth.

## Weak-Point Prevention Contract

### Weak point 1: mixed replay context

- Weak point forecast: archived replay phase evaluation can read replay-derived artifacts from
  `source-set-8a4005c8a083af1a` while silently reading catalog validation from the active
  `source_library/catalog/` lane.
- Owner surface: `evidence_graph.py`, `cli_eval.py`, replay-context loader
- Prevention gate: one concrete negative reproduction using
  `review_id=v1-cg-ecid-source-delta-review` with an explicit active-catalog `catalog_dir`
  override, plus focused tests for mismatch rejection.
- Fail threshold: archived replay phase evaluation succeeds or returns a normal-looking result
  without rejecting the active-catalog fallback.
- Controlled violation: a focused test or reproduction fixture proves the command fails before a
  mixed-context replay result is accepted.
- Future-Codex misuse scenario: a later session passes only `--review-id` or only `--source-set-id`
  and assumes archived replay context is implied; this milestone prevents that by making tracked
  replay context authoritative and mismatch-aware.

### Weak point 2: unstaged review-local authority drift

- Weak point forecast: a replay-local manifest under ignored `source_library/` becomes the only copy
  of replay context, leaving the architecture undocumented in the milestone commit.
- Owner surface: `config/replay_contexts/`, docs, handoff
- Prevention gate: placement-rule review, focused tests, and acceptance criteria that require the
  tracked config file in the verified local commit.
- Fail threshold: the milestone's replay-context authority exists only under
  `source_library/reviews/<review_id>/`.
- Controlled violation: add a negative test or review check proving the loader requires tracked
  config and does not depend on ignored review-local state as the sole authority.
- Future-Codex misuse scenario: a later session writes a convenient local replay manifest and treats
  it as durable truth; this milestone prevents that by making tracked config the only authority.

### Weak point 3: replay eval contract ambiguity

- Weak point forecast: the milestone could quietly invent a new replay eval contract or broaden the
  proving contract without deciding whether that is architecturally correct.
- Owner surface: `config/forest_plan_component_eval_seed.json`, replay-context docs, handoff
- Prevention gate: explicit non-goal plus acceptance criteria stating that replay-context hardening
  does not add or promote a replay-specific forest-plan eval contract.
- Fail threshold: the milestone introduces a new replay eval file or repurposes the proving contract
  without a separate adjudication/component-repair milestone.
- Controlled violation: review the closeout diff and reject any added replay eval file or proving
  contract rewrite in this milestone.
- Future-Codex misuse scenario: a later session tries to make replay-context hardening look green by
  swapping eval contracts; this milestone prevents that by freezing eval-contract scope explicitly.

### Weak point 4: sequencing drift

- Weak point forecast: this architecture milestone could be misreported as the next replay-readiness
  slice even though live blockers remain in applicability, forest-plan content, and compliance
  regeneration.
- Owner surface: milestone plan, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Prevention gate: scope text, acceptance criteria, and handoff routing that explicitly preserve the
  existing next steps for adjudications, component-gap repair, and replay compliance regeneration.
- Fail threshold: the milestone claims current replay reviewer readiness improved without repairing
  those live blockers.
- Controlled violation: add or update docs so the replay-context milestone is described as
  architecture hardening, while the handoff still routes replay-readiness to the current blocked
  lanes.
- Future-Codex misuse scenario: a later session sees a new replay-context config and assumes the
  replay is now ready; this milestone prevents that by keeping readiness routing explicit.

### Weak point 5: stale resolver-owned forest-plan artifacts

- Status: accepted
- Why accepted here: stale resolver-owned findings and queue artifacts are real, but they belong to
  the current replay repair milestone with applicability/component-gap work, not to this replay
  context authority milestone.
- Owner surface: `forest_plan_resolver.py`, `forest_plan_component_eval.py`, replay repair milestone
- Prevention gate: route the issue explicitly to the replay repair milestone and do not claim this
  milestone closes it.
- Fail threshold: this milestone claims forest-plan artifact freshness is solved without adding the
  resolver-regeneration gate.
- Next milestone: current East Crazies replay repair for adjudications, component gaps, and replay
  compliance regeneration.

## Milestone Sequence

### Sequence 0: Narrow The Replay-Context Authority

Outcome label: resolved

Purpose: remove invalid storage options before implementation starts.

Actions:

1. Choose tracked config under `config/replay_contexts/<review_id>.json` as the canonical
   replay-context authority.
2. Allow an optional generated review-local resolved manifest only as a derivative echo, never as
   the sole authority.
3. Define the minimum tracked replay-context fields:
   - `review_id`
   - `source_set_id`
   - `catalog_dir`
   - optional `package_path` only when a later replay-regeneration milestone needs it
4. Derive `source_catalog_path`, `source_set_manifest_path`, and `catalog_sqlite_path` from the
   tracked `catalog_dir` inside the loader instead of treating them as separate authority fields.
   If those child paths are ever emitted as debug echoes or review-local derived metadata, they
   must exactly match the loader-derived paths or fail closed.
5. Document that replay eval contract changes are out of scope for this milestone.

Sequence 0 is complete only after:

- review-local-only manifest is removed as an implementation option;
- one tracked replay-context authority shape is chosen and documented;
- the chosen shape is durable in tracked files and docs, not chat-only guidance.

### Sequence 1: Add The Failing Mixed-Context Reproduction First

Outcome label: resolved

Purpose: pin one concrete failing reproduction before adding new loading logic.

Actions:

1. Add a focused negative reproduction for archived replay phase evaluation using the current CGNF
   replay identity:
   `review_id=v1-cg-ecid-source-delta-review`,
   tracked replay-context auto-resolution,
   and an explicit active-catalog `catalog_dir` override.
2. Record the current mismatch facts behind that reproduction:
   the replay expects archived merged catalog gate
   `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`,
   while the default active catalog remains `source_library/catalog/` on
   `source-set-5e65d845ce77e1a0`.
3. Make the post-repair expectation fail closed:
   the reproduction must raise or return an explicit replay-context mismatch instead of accepting a
   mixed-context result.

Sequence 1 is complete only after:

- the milestone has one concrete negative-path reproduction, not only a generalized architectural
  concern;
- the reproduction is executable from tracked code and docs;
- the reproduction fails before a misleading mixed-context replay result can be accepted.

### Sequence 2: Implement Replay-Context Loading And Validation

Outcome label: resolved

Purpose: make archived replay phase evaluation use tracked replay context and reject mismatches.

Actions:

1. Add a generic replay-context loader/validator for tracked config under `config/replay_contexts/`.
2. Wire that loader into the replay-scoped phase-eval path.
3. Reject mismatch between tracked replay context and any explicit CLI override for:
   - `review_id`
   - `source_set_id`
   - `catalog_dir`
4. Make the replay-context loader the only authority for child catalog artifacts used by replay
   phase-eval. Do not accept independent replay overrides for `source_catalog_path`,
   `source_set_manifest_path`, or `catalog_sqlite_path` in this milestone.
5. Preserve active-catalog behavior for non-replay runs that do not declare tracked replay context.

Sequence 2 is complete only after:

- replay-scoped phase evaluation can resolve tracked replay context without relying on operator
  memory;
- explicit override mismatch fails closed;
- non-replay active-catalog behavior remains unchanged.

### Sequence 3: Commit The Current Replay Context Without Claiming Replay Readiness

Outcome label: resolved

Purpose: use the East Crazies merged replay as the first real consumer of the replay-context
 contract while keeping live replay blockers outside the milestone's success claim.

Actions:

1. Add the tracked replay-context file for `v1-cg-ecid-source-delta-review`.
2. Prove that replay-scoped phase evaluation can run from the tracked replay context and archived
   merged catalog gate without falling back to the active catalog.
3. Keep `config/forest_plan_component_eval_seed.json` frozen as the proving contract and do not add
   a replay-specific eval file here.
4. Update docs and handoff so the current replay remains routed to:
   applicability adjudications, forest-plan component-gap repair, and replay compliance
   regeneration.

Sequence 3 is complete only after:

- one tracked replay-context file exists for the current replay;
- the correct archived replay context executes without fallback;
- the milestone does not claim the replay is green or reviewer-ready.

### Sequence 4: Lock The Pattern Into Durable Docs And Routing

Outcome label: resolved

Purpose: make future archived replay work use one stable pattern and preserve the current readiness
 routing.

Actions:

1. Update durable docs to distinguish active-catalog mode from tracked replay-context mode.
2. Document the canonical replay-context location and override semantics.
3. Update the handoff so future sessions know this milestone hardened replay context only, while the
   next replay-readiness work remains adjudications, component-gap repair, and replayed
   compliance-review regeneration.

Sequence 4 is complete only after:

- durable docs describe one tracked replay-context workflow;
- replay examples stop implying that `--review-id` alone is enough for archived replay safety;
- replay-readiness routing remains explicit and unchanged where live blockers still exist.

## Required Implementation Artifacts

- `config/replay_contexts/` schema and ownership documentation
- one tracked replay-context file for `v1-cg-ecid-source-delta-review`
- one generic replay-context loader/validator
- one concrete negative-path mixed-context reproduction and focused tests
- replay-scoped phase-eval support for tracked replay-context validation
- direct `run_phase_aligned_eval(...)` regression coverage in `tests/test_evidence_graph.py`
- updated docs and handoff reflecting the narrowed milestone scope

## Required Documentation And Handoff Updates

- update this milestone plan if implementation changes the replay-context field set or routing
- update `README.md` with the tracked replay-context workflow and override rules
- update `docs/OUTPUT_SCHEMAS.md` with the replay-context schema and authority semantics
- update `docs/CURRENT_SYSTEM_STATE.md` to distinguish replay-context hardening from replay-readiness
  repair
- update `docs/SESSION_HANDOFF.md` so the next replay-readiness work remains adjudications,
  component-gap repair, and replayed compliance-review regeneration

## Required Verification Gates

Focused tracked-code verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_cli.py \
  tests/test_evidence_graph.py \
  tests/test_v1_ea_eval.py \
  tests/test_replay_context.py \
  tests/test_architecture_contract.py

PYTHONPATH=src uv run --extra dev ruff check src tests

PYTHONPATH=src python -m compileall src
```

Replay-context negative-path verification:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval

try:
    run_phase_aligned_eval(
        output_dir=Path("source_library"),
        review_id="v1-cg-ecid-source-delta-review",
        catalog_dir=Path("source_library/catalog"),
    )
except Exception as exc:
    print(type(exc).__name__)
else:
    raise AssertionError("expected replay-context mismatch failure")
PY
```

Replay-context positive-path verification:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval
from usfs_r1_ea_sources.replay_context import load_replay_context

context = load_replay_context(
    Path("config/replay_contexts/v1-cg-ecid-source-delta-review.json")
)
assert context.review_id == "v1-cg-ecid-source-delta-review"
assert context.source_set_id == "source-set-8a4005c8a083af1a"
assert str(context.catalog_dir).endswith(
    "source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate"
)

result = run_phase_aligned_eval(
    output_dir=Path("source_library"),
    review_id="v1-cg-ecid-source-delta-review",
)
assert result.summary["review_id"] == context.review_id
assert result.summary["source_set_id"] == context.source_set_id
assert result.summary["catalog_dir"].endswith(
    "source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate"
)
print(f"overall_reviewer_ready={result.summary['reviewer_ready']}")
PY
```

Frozen proving-lane regression check:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/forest_plan_component_eval_seed.json
```

Plan/doc closeout checks:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py \
  docs/CGNF_CURRENT_REPLAY_REPAIR_MILESTONE_PLAN.md \
  --strict

git diff --check
```

## Acceptance Criteria

- The canonical replay-context authority for archived review runs is tracked under
  `config/replay_contexts/`.
- `catalog_dir` is the only tracked catalog-location authority in replay context for this
  milestone; child catalog artifact paths are loader-derived or consistency-validated echoes, not
  independent authority fields.
- Review-local replay context, if generated, is explicitly derivative and not the only authority.
- Review-local-only replay manifest is no longer a valid implementation path in this milestone.
- The milestone includes one concrete mixed-context negative reproduction for
  `v1-cg-ecid-source-delta-review` and that reproduction fails closed after the repair.
- Replay-scoped phase evaluation auto-resolves tracked archived replay context from review identity
  and rejects mismatched explicit overrides instead of silently using active-catalog defaults.
- A tracked replay-context file exists for `v1-cg-ecid-source-delta-review` and binds the replay to
  `source-set-8a4005c8a083af1a` plus the archived merged catalog gate.
- Replay-scoped positive-path proof exercises replay-context auto-resolution from review identity;
  it does not manually pass archived `catalog_dir` just to make the gate green.
- `config/forest_plan_component_eval_seed.json` remains the only tracked forest-plan component eval
  contract in this milestone; no replay-specific forest-plan eval contract is added or promoted.
- The milestone does not claim current replay reviewer readiness, replay compliance regeneration, or
  replay content repair.
- Durable docs and handoff explicitly preserve the next replay-readiness work:
  applicability adjudications, forest-plan component-gap repair, and replay compliance regeneration.
- Coverage did not get easier to produce a green result. Any changed test, fixture, or validation
  rule must prove equivalent or stronger replacement coverage, including at least one negative path
  that fails before the repair and passes after the repair.
- No CGNF-specific runtime branch, replay heuristic keyed by forest name, or hidden wording template
  is introduced.
- The milestone is not complete until the verified implementation, tests, docs, and handoff updates
  land in one local atomic commit. Before commit, the milestone is ready-to-close, not complete.

## Stop Conditions

- Stop if the only workable replay-context authority is review-local-only under ignored
  `source_library/`.
- Stop if implementing replay-context validation requires changing forest-plan eval contracts in this
  milestone.
- Stop if the only proof path depends on making the current replay green or reviewer-ready.
- Stop if replay-context hardening cannot be isolated from applicability adjudication repair,
  forest-plan component-gap repair, or replay compliance regeneration.
- Stop if no concrete mixed-context negative reproduction can be written from the current archived
  replay surfaces.
- Stop if the only positive-path proof requires manually threading archived `catalog_dir` into
  `run_phase_aligned_eval(...)` instead of proving replay-context auto-resolution by review
  identity.
- Stop if unrelated existing worktree changes would be pulled into the milestone commit.

## Local Commit Closeout Policy

- Stage only the verified replay-context contract slice. Do not stage unrelated viewer changes,
  root-level East Crazies draft exports, or ignored `source_library/` artifacts.
- Keep the closeout commit local unless the user explicitly asks for push or publish.
- The local atomic commit must include tracked config, code, focused tests, docs, and
  `docs/SESSION_HANDOFF.md` together.
- If any verification gate fails, do not commit a partial replay-context path. Record the blocker in
  the handoff and stop at the failed sequence.

## Residual Risks And Next Milestone Routing

- Current replay reviewer readiness remains blocked by applicability adjudications, forest-plan
  component-gap repair, and replay compliance regeneration.
- Replay-specific forest-plan eval promotion or creation remains a later decision after current
  replay content repair is complete.
- Resolver-owned forest-plan artifact freshness remains intentionally routed to the replay repair
  milestone, not solved here.
- If this milestone succeeds, the next architecture-adjacent follow-on is extending tracked replay
  context consumption beyond phase-eval to any other replay-sensitive review commands that still
  depend on manual archived-path flags.
