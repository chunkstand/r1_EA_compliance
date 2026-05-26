# Applicability Compliance Replay Owner Boundary Milestone Plan

Date: 2026-05-26

Status: queued standalone child packet opened 2026-05-26 for applicability/compliance owner
concentration inside the active replay-repair lane; no implementation milestones are closed yet

Owner context: this is a bounded child packet under
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`. It exists because the live replay lane
still runs through `build_applicability_decisions(...)` and `run_compliance_review(...)`, but those
facades still own too many responsibilities. This packet does not claim that owner splitting alone
resolves the live ECID broader-EA mismatch or the South Plateau forest-plan replay blocker. Those
behavioral blockers remain owned by the parent replay packet unless this child packet proves they
change as a direct result of the split.

## Purpose

Restore narrow orchestration ownership in the replay family that future ECID and South Plateau
repair work still depends on.

The exact weakness is not simply that two functions are long. The deeper problem is that the active
review-local replay lane still depends on broad owners that mix artifact loading, freshness and
identity checks, decision or review execution, artifact emission, and reviewer-facing reporting.
That makes every replay repair in this family more likely to regrow the same modules instead of
landing in smaller owned helpers with explicit gates.

This packet exists to keep the replay lane editable without weakening the artifact contracts that
the current reviewer-ready slots depend on.

## Current Evidence

### Live owner concentration on 2026-05-26

- `src/usfs_r1_ea_sources/applicability_decisions.py` is `793` lines.
- `build_applicability_decisions(...)` begins at line `55` and currently owns:
  - applicability artifact path/default resolution
  - authority-universe, package-graph, and trace loading
  - source-set and freshness derivation
  - per-candidate loop control
  - search-coverage certificate emission
  - partition payload assembly
  - provenance and report writing
- `_decision_for_candidate(...)` begins at line `341` and still mixes trigger arbitration,
  evidence selection, forest-plan signals, coverage status, and final decision-record assembly.
- `src/usfs_r1_ea_sources/compliance_review.py` is `451` lines.
- `run_compliance_review(...)` begins at line `71` and currently owns:
  - rule-pack existence/load/validation
  - review/output path preparation
  - applicability gate setup and evaluation rule-pack write
  - rule-claim binding invocation
  - EA review invocation
  - forest-plan resolver invocation
  - authority integration and explanation assembly
  - finding-graph assembly
  - matrix markdown/PDF/render-manifest output
  - final validation and review artifact writing
- `tests/test_applicability_decisions.py` (`526` lines) and `tests/test_compliance_review.py`
  (`644` lines) are the current behavioral sentinels for these public facades.

### Live replay routing that makes this debt active

- `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md` both show the same current truth:
  aligned ECID applicability and compliance replay are green on
  `source-set-f70ea11e04ae3d53`, while the next truthful runtime blockers are ECID broader-EA
  review-local artifact alignment and South Plateau forest-plan replay on that same source set.
- That means the selected debt is active rather than cosmetic: future replay fixes still have to
  change code in the exact applicability/compliance owner family named above.

### Historical split precedent that should continue here

- `docs/HOTSPOT_REPORT_2026_05_04.md` records the earlier bounded `compliance_review.py` sequence
  that extracted rendering, validation, authority-integration, finding-graph, and eval-harness
  owners out of the central module while preserving generated artifact contracts.
- This packet continues that existing owner-splitting pattern. It does not reopen the already-closed
  `compliance_review_eval.py` extraction or the test-boundary packet.

## Goal

Close this owner-concentration debt by making both public facades narrow orchestration owners while
preserving replay behavior and generated artifact contracts.

Completion means all of the following are true:

- `build_applicability_decisions(...)` remains the public applicability-decision facade, but no
  longer directly owns raw artifact loading, the full decision-ledger loop, and output-writing
  concerns in one place.
- `run_compliance_review(...)` remains the public compliance-review facade, but no longer directly
  owns review bootstrap, downstream review execution, graph/integration assembly, and output-writing
  concerns in one place.
- CLI behavior, output paths, schema versions, replay-context behavior, and reviewer-visible
  artifacts remain compatible.
- The parent replay packet still reports truthful runtime status after the split, whether that
  status stays green or remains blocked for broader-EA / South Plateau reasons.

## Non-Goals

- Do not claim to resolve ECID broader-EA replay drift or South Plateau forest-plan replay in this
  packet unless a direct, verified bug fix is discovered during the owner split.
- Do not change applicability decision semantics, generated rule-pack semantics, compliance finding
  semantics, or reviewer-ready thresholds just to make the split easier.
- Do not weaken tests, add skips/xfails, or relax architecture gates to hide owner drift.
- Do not stage ignored `source_library/` outputs unless repository policy changes or the user
  explicitly expands scope.
- Do not reopen the closed `compliance_review_eval.py` or compliance test-boundary packets except as
  historical precedent.

## Scope

In scope:

- `src/usfs_r1_ea_sources/applicability_decisions.py`
- existing `applicability_decision_*` helper family modules plus any new adjacent owner module that
  stays in that naming family
- `src/usfs_r1_ea_sources/compliance_review.py`
- existing `compliance_*` helper family modules plus any new adjacent owner module that stays in the
  compliance-review naming family
- `src/usfs_r1_ea_sources/cli_applicability.py` and `src/usfs_r1_ea_sources/cli_compliance.py` only
  if import surfaces must move while preserving public command behavior
- `docs/architecture_contract.toml`
- focused tests and fixtures for applicability, compliance, CLI, architecture contract, and replay
  eval compatibility
- parent replay packet and current-state docs only where closeout routing must record the split

Out of scope:

- broader replay artifact repair beyond compatibility proof
- source-set rebinds, downloader/catalog changes, or large corpus reruns
- unrelated hotspot work in extraction, phase-eval direct-eval, or broader evaluation owners
- public command renames or artifact schema-version bumps unless the user explicitly expands scope

## Owner Surfaces

| Surface | Required role after closeout | Required verification |
| --- | --- | --- |
| `src/usfs_r1_ea_sources/applicability_decisions.py` | thin public orchestration facade for applicability decision replay | focused pytest, owner-boundary checks, compileall |
| `src/usfs_r1_ea_sources/applicability_decision_*` family | owns artifact loading, decision-ledger execution, evidence/coverage helpers, and output emission in bounded modules | focused pytest, owner-boundary checks |
| `src/usfs_r1_ea_sources/compliance_review.py` | thin public orchestration facade for compliance review replay | focused pytest, owner-boundary checks, compileall |
| existing `src/usfs_r1_ea_sources/compliance_*` family plus any new adjacent peer | owns review bootstrap, downstream execution, authority/graph assembly, and output emission in bounded modules | focused pytest, owner-boundary checks |
| `src/usfs_r1_ea_sources/cli_applicability.py` | preserves `applicability-determine` command surface and summary behavior | CLI parse tests plus focused runtime test |
| `src/usfs_r1_ea_sources/cli_compliance.py` | preserves `compliance-review` command surface and summary behavior | CLI parse tests plus focused runtime test |
| `docs/architecture_contract.toml` | records any new helper-module boundaries introduced by the split | architecture contract pytest |
| `tests/test_applicability_decisions.py` | behavioral compatibility sentinel for applicability outputs | focused pytest |
| `tests/test_compliance_review.py` | behavioral compatibility sentinel for compliance outputs | focused pytest |
| focused owner-boundary tests under `tests/` | fail closed if the broad facades absorb disallowed responsibilities again | focused pytest |
| `docs/TECH_DEBT_REGISTER.md` | records any user-approved temporary escape hatch introduced during the split | grep plus doc readback |
| `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md` | truthful routing and current-state closeout for the owner split | targeted grep, doc readback, `git diff --check` |

## Placement Rules

- Keep `build_applicability_decisions(...)` as the public facade for `applicability-determine`.
  Do not move public CLI semantics into a new generic helper.
- New applicability helpers must live in the existing `applicability_decision_*` family or an
  equivalently explicit adjacent owner module. Do not create generic `utils.py` or `helpers.py`
  files.
- Keep raw applicability artifact I/O, freshness shaping, and report writing out of the thin public
  facade after closeout.
- Keep `run_compliance_review(...)` as the public facade for `compliance-review`.
- Prefer extending existing `compliance_inputs.py`, `compliance_outputs.py`,
  `compliance_validation.py`, `compliance_authority_integration.py`,
  `compliance_explanation_paths.py`, and `compliance_finding_graph.py` before inventing vague new
  helpers. If a new peer is necessary, name it for the exact owner role.
- Preserve output paths, filenames, dataclass return contracts, schema versions, and summary keys
  unless a separate governed contract change is opened.
- If a new module is introduced, update `docs/architecture_contract.toml` and the matching focused
  contract test in the same milestone.
- If a temporary shortcut is truly unavoidable and the user explicitly approves it, record it in
  `docs/TECH_DEBT_REGISTER.md` in the same milestone. Do not leave it undocumented.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | The packet starts from stale replay truth or vague split goals and later claims owner improvement without proving compatibility | this plan, parent replay plan, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md` | baseline focused tests, replay-state readback, targeted grep | the baseline does not reproduce the current broad-owner surfaces and current replay state before edits begin | pre-edit baseline must still show ECID aligned compliance green and the broader-EA / South blockers still open | a future session claims the split fixed replay debt without checking the live parent packet route |
| `1` | Applicability work moves code around but preserves the same catch-all facade or drifts decision/provenance artifact contracts | `applicability_decisions.py`, adjacent `applicability_decision_*` helpers, focused tests | focused pytest, owner-boundary test, architecture contract test, compileall | the public facade still directly owns broad file I/O plus loop execution plus output writing; or applicability artifact paths/schema/summary drift without an approved contract packet | add a negative owner-boundary test that fails when the facade directly calls disallowed raw load/write helpers again | a future session adds one more artifact write or freshness branch back into `build_applicability_decisions(...)` because the tests only check end results |
| `2` | Compliance work regrows a broad orchestrator or silently changes review artifact behavior | `compliance_review.py`, adjacent `compliance_*` helpers, focused tests | focused pytest, owner-boundary test, CLI parse tests, architecture contract test, compileall | the public facade still directly owns bootstrap plus downstream execution plus graph/integration plus writes; or compliance output behavior drifts without a governed reason | add a negative owner-boundary test that fails when `run_compliance_review(...)` directly takes back disallowed low-level responsibilities | a future session fixes one replay issue by adding another branch inside `run_compliance_review(...)` instead of placing it in the right owner |
| `3` | The split passes unit tests but breaks the live replay lane or changes the blocker shape silently | ECID live replay lane, parent replay packet docs | focused live replay commands plus downstream eval readback | ECID aligned applicability/compliance replay is no longer green, or the parent packet blocker family changes without a proved bug fix | rerun the bounded ECID replay chain and confirm the expected green applicability/compliance stage plus unchanged broader-EA blocker shape | a future session trusts fixture tests only and ships a split that breaks the real replay lane |
| `4` | Closeout forgets to route the remaining behavioral blockers truthfully or leaves undocumented debt exceptions | current-state docs, handoff, tech debt register | targeted grep, `git diff --check`, doc readback | current-state docs imply the replay blocker is closed just because the owner split is done; or a temporary exception exists without a debt-register entry | closeout review must show whether the parent packet remains broader-EA / South blocked after the split | a future session treats architecture cleanup as proof of runtime readiness and closes the wrong packet |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Baseline lock and owner-boundary gate design | `resolved` |
| `1` | Applicability decision owner split | `resolved` |
| `2` | Compliance review owner split | `resolved` |
| `3` | Bounded live replay compatibility proof | `resolved` |
| `4` | Docs, handoff, and debt-register closeout | `resolved` |

### Milestone `0`: Baseline lock and owner-boundary gate design

Outcome label: `resolved`

Work:

- Reproduce the current broad-owner baseline before any extraction:
  - line counts for the two owner modules
  - public function entry points
  - focused behavior tests
  - current replay state from `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md`
- Add or update owner-boundary tests before broad refactoring so the split fails closed if the
  public facades re-absorb low-level work later.
- Define the exact disallowed direct responsibilities for each facade:
  - `build_applicability_decisions(...)` must not directly own raw input loading plus full decision
    loop plus output writing after closeout
  - `run_compliance_review(...)` must not directly own bootstrap plus downstream execution plus
    graph/integration plus output writing after closeout

Required verification:

```bash
git status -sb
wc -l src/usfs_r1_ea_sources/applicability_decisions.py src/usfs_r1_ea_sources/compliance_review.py
rg -n "^def build_applicability_decisions|^def _decision_for_candidate|^def run_compliance_review" src/usfs_r1_ea_sources/applicability_decisions.py src/usfs_r1_ea_sources/compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py tests/test_compliance_review.py tests/test_architecture_contract.py tests/test_cli.py -q
rg -n "broader-EA|broader_ea_passed|South Plateau|source-set-f70ea11e04ae3d53|compliance-review" docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md
git diff --check
```

### Milestone `1`: Applicability decision owner split

Outcome label: `resolved`

Work:

- Extract applicability input/default-path resolution and freshness preparation out of
  `build_applicability_decisions(...)`.
- Extract the candidate decision-ledger loop into a bounded owner that coordinates per-candidate
  execution without making the public facade a catch-all.
- Either narrow `_decision_for_candidate(...)` directly or split its remaining concerns so trigger
  arbitration, evidence/coverage shaping, and final record assembly are not one unbroken owner.
- Keep output writing and report/provenance emission in the existing output family or a clearly
  named adjacent peer.
- Preserve:
  - `ApplicabilityDecisionResult`
  - `applicability-determine` command behavior
  - artifact filenames and schema versions
  - current summary keys and validation expectations

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py tests/test_architecture_contract.py tests/test_cli.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

### Milestone `2`: Compliance review owner split

Outcome label: `resolved`

Work:

- Extract rule-pack/bootstrap/output-path preparation out of `run_compliance_review(...)`.
- Extract the downstream execution bundle that coordinates rule-claim binding, EA review, and
  forest-plan resolution into a bounded owner surface.
- Extract or narrow the authority-integration, explanation, finding-graph, and artifact-write
  assembly so the public facade remains orchestration-only.
- Keep output assembly in the existing compliance family where possible rather than inventing a
  second generic review utility layer.
- Preserve:
  - `ComplianceReviewResult`
  - `compliance-review` command behavior
  - output filenames and schema versions
  - reviewer-ready summary semantics and current validation shape

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_architecture_contract.py tests/test_cli.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

### Milestone `3`: Bounded live replay compatibility proof

Outcome label: `resolved`

Work:

- Re-run the current aligned ECID applicability/compliance chain on
  `source-set-f70ea11e04ae3d53` to prove the split did not break the live replay family:
  - `applicability-determine`
  - `applicability-validate`
  - `applicability-generate-rule-pack`
  - `compliance-review`
  - `v1-ea-eval`
  - `phase-eval`
- Confirm the expected truth after the split:
  - aligned ECID applicability validation still passes
  - aligned ECID compliance review still reports `reviewer_ready=true`
  - ECID `v1-ea-eval` remains broader-EA blocked rather than reopening a compliance-review failure
  - `phase-eval` does not regress `compliance_review` as a failing phase
- If the compliance split touched shared failure-shaping or matrix-output logic that also affects the
  South slot, rerun the bounded South replay readback needed to prove the blocker remains the known
  forest-plan / broader-EA family rather than a new applicability/compliance regression.

Required verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-determine --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources compliance-review --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" --output-dir source_library --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json --source-set-id source-set-f70ea11e04ae3d53 --review-id v1-cg-ecid-compliance-review --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
```

### Milestone `4`: Docs, handoff, and debt-register closeout

Outcome label: `resolved`

Work:

- Update `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` with the owner-boundary outcome
  and whether the live replay blocker changed or stayed the same.
- Update `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md` so future sessions know:
  - this child packet closed
  - whether ECID/South runtime blockers changed
  - whether any residual replay work routes back to the parent packet
- Update `docs/architecture_contract.toml` if new helper modules were introduced.
- If any temporary escape hatch was explicitly approved, record it in `docs/TECH_DEBT_REGISTER.md`
  with owner, reason, and removal condition in the same milestone.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py tests/test_compliance_review.py tests/test_architecture_contract.py tests/test_cli.py tests/test_v1_ea_eval.py tests/test_v1_ea_eval_contracts.py tests/test_phase_eval.py tests/test_real_package_review_coverage_eval.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Required Implementation Artifacts

- narrowed `src/usfs_r1_ea_sources/applicability_decisions.py`
- narrowed `src/usfs_r1_ea_sources/compliance_review.py`
- any new adjacent owner modules in the existing applicability/compliance naming families
- focused owner-boundary tests that fail when broad responsibilities return to the public facades
- updated CLI/contract imports only if new helper modules require them
- updated `docs/architecture_contract.toml` when new modules are introduced

## Required Documentation And Handoff Updates

- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this child plan with milestone status updates if execution starts here
- `docs/TECH_DEBT_REGISTER.md` only if an approved temporary shortcut is introduced

## Required Verification Gates

- Focused behavior:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py tests/test_compliance_review.py -q`
- CLI and boundary:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py -q`
- Downstream replay/eval compatibility:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_v1_ea_eval.py tests/test_v1_ea_eval_contracts.py tests/test_phase_eval.py tests/test_real_package_review_coverage_eval.py -q`
- Static quality:
  - `PYTHONPATH=src uv run --extra dev ruff check src tests`
  - `PYTHONPATH=src python -m compileall src`
  - `git diff --check`
- Bounded live replay:
  - the ECID aligned replay chain in Milestone `3`

## Acceptance Criteria

- A focused owner-boundary gate exists and fails closed if `build_applicability_decisions(...)`
  again directly owns raw artifact loading plus broad loop execution plus output writing.
- A focused owner-boundary gate exists and fails closed if `run_compliance_review(...)` again
  directly owns bootstrap plus downstream execution plus graph/integration plus output writing.
- `tests/test_applicability_decisions.py`, `tests/test_compliance_review.py`, `tests/test_cli.py`,
  and `tests/test_architecture_contract.py` pass without weaker assertions, skips, or broadened
  tolerances.
- If new modules are introduced, `docs/architecture_contract.toml` and the focused architecture
  contract tests are updated in the same milestone.
- The bounded ECID replay check still yields the same governed truth after the split:
  aligned applicability validation passes, aligned compliance review is reviewer-ready, ECID
  remains broader-EA blocked rather than compliance-blocked, and `phase-eval` does not reopen the
  compliance phase as red.
- If a South replay readback is required, it confirms the blocker remains the known South
  forest-plan / broader-EA family unless a direct bug fix proves otherwise.
- No new temporary shortcut lands without a same-milestone `docs/TECH_DEBT_REGISTER.md` entry.
- Closeout docs route any remaining behavioral work back to
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` truthfully.

## Stop Conditions

- Stop if the split would require a public command rename, output filename change, schema-version
  change, or replay-context contract change that belongs in a separate governed packet.
- Stop if live current-state docs no longer show `source-set-f70ea11e04ae3d53` as the aligned
  reviewer-facing source set for the ECID/South replay lane; refresh the baseline first.
- Stop if the only path to green tests is weaker assertions, new skips/xfails, or undocumented
  temporary debt.
- Stop if proving compatibility would require broad downloader/catalog/extraction reruns instead of
  the bounded replay commands listed here.
- Stop if new helper placement would violate `docs/architecture_contract.toml` in a way that cannot
  be explained and tested in the same milestone.

## Local Commit Closeout Policy

- Complete one milestone at a time.
- For each milestone, stage only the verified owner-split slice:
  - source changes
  - matching tests
  - architecture-contract updates
  - current-state and handoff updates
  - debt-register entry only if one is required
- Make one local atomic commit per completed milestone after all required verification passes.
- Do not stage unrelated dirty files or ignored `source_library/` artifacts.

## Residual Risks And Next Milestone Routing

- If Milestone `1` closes but Milestone `2` has not started, the remaining work stays in this child
  packet as compliance owner concentration.
- If both owner splits close and the ECID/South replay blockers still remain behaviorally red, route
  the next truthful work back to `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  beginning with ECID broader-EA review-local artifact / source-record alignment and then South
  Plateau forest-plan replay.
- If a direct bug fix is discovered during the split, route that behavioral change through the
  parent replay packet docs as part of closeout rather than silently claiming architecture-only
  work fixed runtime readiness.
