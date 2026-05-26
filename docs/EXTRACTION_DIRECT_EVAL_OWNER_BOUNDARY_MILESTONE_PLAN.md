# Extraction Direct-Eval Owner Boundary Milestone Plan

Date: 2026-05-26

Status: queued standalone child packet opened 2026-05-26 for the remaining extraction/direct-eval
owner monoliths; no implementation milestones are closed yet

Owner context: this is a fresh child packet opened from the 2026-05-26 architecture audit and
stacked under `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`. It must preserve two
historical closeouts as already true:

- `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md` already closed the dedicated
  `extraction-fidelity-eval` contract and artifact owner.
- `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` already closed the
  `phase_eval_direct_eval.py` seam and direct-eval-aware `phase-eval` contract surface.

This packet does not reopen those contracts. It narrows the remaining large producer owners under
them: `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` and
`src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`. Because the latter still feeds the
live ECID review-bound `phase-eval` blocker family, the packet also needs bounded replay/readiness
compatibility proof against the current runtime route.

## Purpose

Remove the remaining monolithic owners from the extraction/direct-eval verification lane without
changing the verified contract surfaces they already serve.

The exact weakness is not only that two files are large. The deeper problem is that the remaining
implementation owners still mix too many responsibilities:

- the extraction fidelity producer mixes manifest governance, temporary-workspace scenario
  execution, extraction/audit orchestration, metric shaping, category rollups, and Markdown report
  rendering; and
- the source-set direct-eval adapter mixes one dispatch seam with several large producer-specific
  status builders, so new source-set phase coverage or replay-contract changes still fan out across
  one file.

That makes future eval additions, replay repairs, and metric changes expensive and more likely to
regrow the same hotspot class.

## Current Evidence

### Live owner concentration on 2026-05-26

- `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` is `1144` lines and is one of the live
  `>800` code files reopened by the architecture audit.
- `run_extraction_fidelity_eval(...)` starts at line `52` and currently owns:
  - manifest loading and normalization
  - contract validation
  - case execution orchestration
  - output summary assembly
  - schema-field validation
  - durable JSON and Markdown output writes
- additional large owner blocks in that file include:
  - `_validate_manifest_contract(...)` at `249`
  - `_run_extraction_case(...)` at `517`
  - `_metric_results(...)` at `654`
  - `_category_summaries(...)` at `824`
  - `_markdown_report(...)` at `922`
- `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py` is `839` lines and is also one of
  the live `>800` code files reopened by the architecture audit.
- `resolve_source_set_phase_statuses(...)` starts at line `25`, but the file still carries several
  large producer-specific status builders:
  - `_upstream_phase_status(...)` at `140`
  - `_extraction_fidelity_phase_status(...)` at `223`
  - `_downstream_phase_status(...)` at `290`
  - `_forest_plan_profile_phase_status(...)` at `416`
  - `_forest_plan_component_retrieval_phase_status(...)` at `555`
- `tests/test_extraction_fidelity_eval.py` (`478` lines),
  `tests/test_phase_eval_direct_eval_contracts.py` (`713` lines),
  `tests/test_cli_eval.py` (`608` lines), and `tests/test_phase_eval.py` (`757` lines) are the
  current behavioral sentinels for these surfaces.

### Closed contracts that must stay closed

- `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md` already records the dedicated
  `extraction-fidelity-eval` command, `config/extraction_fidelity_eval_v1.json`, tracked fixtures,
  `tests/test_extraction_fidelity_eval.py`, and durable outputs under
  `source_library/evaluations/extraction_fidelity/` as resolved local truth.
- `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` already records
  `config/phase_eval_direct_eval_v1.json`, `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  direct-eval-aware `phase-eval`, and promotion/readiness wiring as resolved local truth.
- The new packet must preserve those public artifacts and facades rather than recreate their
  ownership under new names.

### Live replay linkage that makes this debt active

- `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md` both report that aligned ECID
  `compliance-review` is green on `source-set-f70ea11e04ae3d53`, but review-bound
  `phase-eval --review-id v1-cg-ecid-compliance-review` remains red with
  `review_direct_eval_status="direct_eval_identity_mismatch"`.
- The current blocker family there is retrieval, claim extraction, rule-claim binding, downstream
  direct evaluation, and related packet-local replay debt, not extraction-fidelity or compliance
  owner drift.
- That makes `phase_eval_direct_eval_source_set.py` an active owner surface: future repair work in
  the live replay lane still depends on that adapter staying readable and fail-closed while the
  behavioral blockers remain elsewhere.

## Goal

Resolve the scoped owner-boundary debt by splitting the remaining large extraction/direct-eval
verification owners into explicit helper families while preserving contract behavior.

Completion means all of the following are true:

- `run_extraction_fidelity_eval(...)` remains the public extraction-fidelity facade, but no longer
  directly owns contract validation, full case execution, metrics, category rollups, and report
  rendering in one file.
- `resolve_source_set_phase_statuses(...)` remains the source-set direct-eval dispatch surface
  under `phase_eval_direct_eval.py`, but no longer carries all producer-specific status builders in
  one large module.
- `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` and
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py` both fall below the repo's `800`
  line oversized threshold, and the public facade/dispatch modules become meaningfully smaller than
  that threshold.
- The dedicated extraction-fidelity artifact contract and the direct-eval-aware `phase-eval`
  contract stay behaviorally compatible.
- The live ECID replay lane keeps the same truthful blocker family after the split unless a direct,
  separately-verified bug fix is discovered.

## Non-Goals

- Do not reopen or rename the public `extraction-fidelity-eval` command, its manifest, or its
  result schema.
- Do not reopen or redesign `phase_eval_direct_eval.py`, `config/phase_eval_direct_eval_v1.json`,
  or the already-closed direct-eval seam unless a separate contract packet is opened.
- Do not claim to resolve ECID broader-EA replay drift, retrieval/claim/rule-claim direct-eval
  gaps, or South Plateau forest-plan replay in this packet unless a direct verified bug fix is
  discovered during the split.
- Do not weaken tests, add skips/xfails, or hide the hotspot behind looser routing.
- Do not stage ignored `source_library/` outputs unless repository policy changes or the user
  explicitly expands scope.

## Scope

In scope:

- `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`
- new adjacent `extraction_fidelity_eval_*` helper modules if needed
- `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`
- new adjacent `phase_eval_direct_eval_source_set_*` helper modules if needed
- `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` only where imports must move while preserving
  its public coverage/facade behavior
- `src/usfs_r1_ea_sources/cli_eval.py` only where import wiring must stay aligned
- `docs/architecture_contract.toml`
- focused tests and docs that govern extraction-fidelity, direct-eval source-set coverage, CLI
  routing, phase-eval compatibility, and promotion/readiness compatibility

Out of scope:

- new extraction fidelity categories or broader downstream direct-eval case authoring beyond narrow
  negative/owner-boundary coverage required by the split
- new source-set replay semantics
- broader `phase_eval.py` or `promotion_suite.py` redesign
- unrelated hotspot work in extraction runtime, claim extraction, rule-claim binding, or other
  evaluation families

## Owner Surfaces

| Surface | Required role after closeout | Required verification |
| --- | --- | --- |
| `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` | thin public facade for extraction-fidelity evaluation | focused pytest, boundary tests, compileall |
| `src/usfs_r1_ea_sources/extraction_fidelity_eval_*` family | explicit owners for contract validation, case execution, metrics, summaries, and reporting | focused pytest, boundary tests |
| `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` | keep the closed contract/coverage facade stable | focused pytest, architecture contract |
| `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py` | thin source-set dispatch surface only | focused pytest, boundary tests, compileall |
| `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set_*` family | explicit owners for upstream, extraction-fidelity, downstream, forest-plan profile, and component-retrieval source-set status resolution | focused pytest, boundary tests |
| `src/usfs_r1_ea_sources/cli_eval.py` | preserve `extraction-fidelity-eval` and `phase-eval` command wiring | CLI parser/handler tests |
| `docs/architecture_contract.toml` | record any new helper-module boundaries introduced by the split | architecture contract pytest |
| `tests/test_extraction_fidelity_eval.py` | behavioral contract sentinel for extraction-fidelity outputs | focused pytest |
| `tests/test_phase_eval_direct_eval_contracts.py` | contract sentinel for source-set direct-eval coverage semantics | focused pytest |
| `tests/test_cli_eval.py` | CLI contract sentinel for eval commands | focused pytest |
| `tests/test_phase_eval.py` | runtime/readiness compatibility sentinel for phase-eval integration | focused pytest |
| `tests/test_promotion_suite_full_canonical.py` and `tests/test_promotion_suite.py` | promotion/readiness compatibility where extraction-fidelity and evaluation coverage participate | focused pytest when touched |
| `docs/TECH_DEBT_REGISTER.md` | records any explicitly approved temporary shortcut introduced during the split | grep plus doc readback |
| `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and this plan | truthful current routing and closeout state | targeted grep, `git diff --check` |

## Placement Rules

- Keep `run_extraction_fidelity_eval(...)` in `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`
  as the public facade. New internal owners should live in explicit peer modules such as
  `extraction_fidelity_eval_contract.py`, `extraction_fidelity_eval_cases.py`,
  `extraction_fidelity_eval_metrics.py`, and `extraction_fidelity_eval_report.py` if those splits
  are needed. Do not create vague `eval_utils.py` helpers.
- Preserve `config/extraction_fidelity_eval_v1.json`,
  `source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_results.json`, and
  `source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_report.md` as the
  durable contract surfaces.
- Keep `resolve_source_set_phase_statuses(...)` in
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py` as the source-set dispatch entry
  point under `phase_eval_direct_eval.py`.
- Move producer-specific source-set status logic into explicit peer modules such as
  `phase_eval_direct_eval_source_set_upstream.py`,
  `phase_eval_direct_eval_source_set_extraction.py`,
  `phase_eval_direct_eval_source_set_downstream.py`,
  `phase_eval_direct_eval_source_set_forest_plan_profile.py`, and
  `phase_eval_direct_eval_source_set_component_retrieval.py` if those splits are needed. Do not
  push more producer logic into `phase_eval_direct_eval.py`, `phase_eval.py`, or generic helpers.
- Preserve canonical direct-eval owner paths. Source-set `retrieval`, `claim_extraction`, and
  `rule_claim_binding` must continue to consume the canonical downstream contract outputs rather
  than review-local substitutes.
- If new modules are introduced, update `docs/architecture_contract.toml` and the matching focused
  contract tests in the same milestone.
- If a temporary shortcut is unavoidable and explicitly approved, record it in
  `docs/TECH_DEBT_REGISTER.md` in the same milestone.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | The packet starts from stale routing and accidentally reopens already-closed extraction-fidelity or phase-eval seam work | this plan, historical milestone plans, current-state docs | baseline doc readback, focused tests, targeted grep | the baseline does not reproduce the current oversized owners and current replay truth before edits begin | pre-edit baseline must still show the dedicated extraction-fidelity artifact and closed `phase_eval_direct_eval.py` seam as historical truth | a future session rewrites the contract layer instead of splitting the remaining large owners underneath it |
| `1` | Extraction-fidelity code is moved around but the public facade remains a catch-all owner or output behavior drifts | `extraction_fidelity_eval.py`, new `extraction_fidelity_eval_*` peers, focused tests | focused pytest, boundary test, CLI test, compileall | the facade still directly owns contract validation plus scenario execution plus metrics plus report writing; or output artifact/schema behavior drifts | add a boundary test that monkeypatches extracted helper owners and fails if the facade no longer delegates to them | a future session adds one more metric or reporting branch back into the facade because tests only check end results |
| `2` | Source-set direct-eval code is split superficially but producer-specific status logic stays concentrated or semantic routing drifts | `phase_eval_direct_eval_source_set.py`, new `phase_eval_direct_eval_source_set_*` peers, focused tests | focused pytest, boundary test, architecture contract test, compileall | the dispatch module still directly owns multiple large producer-specific builders; or required producer semantics/path handling drift | add a boundary test that monkeypatches extracted producer-status owners and fails if dispatch stops routing through them | a future session patches a new source-set producer by adding another 100-line branch to the dispatch file |
| `3` | The split passes unit tests but breaks runtime readiness or changes the current ECID blocker family | extraction-fidelity artifact, source-set phase-eval status, review-bound phase-eval | focused live commands plus result readback | `extraction-fidelity-eval` no longer reproduces its governed artifact contract, source-set `phase-eval` regresses, or review-bound ECID `phase-eval` changes blocker family without a proved bug fix | rerun the dedicated extraction-fidelity command, full-canonical source-set `phase-eval`, and ECID review-bound `phase-eval` and confirm the expected statuses | a future session trusts fixtures only and ships a split that breaks the live phase-eval route |
| `4` | Closeout routes the remaining work incorrectly or lands undocumented debt exceptions | current-state docs, handoff, tech debt register | targeted grep, `git diff --check`, doc readback | docs imply the replay blocker is closed just because the owner split finished; or a shortcut exists without a debt entry | closeout review must state whether the current ECID direct-eval blocker family stayed the same after the split | a future session treats architecture cleanup as proof of replay readiness and closes the wrong packet |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Baseline lock and owner-boundary gate design | `resolved` |
| `1` | Extraction-fidelity internal owner split | `resolved` |
| `2` | Source-set direct-eval producer split | `resolved` |
| `3` | Bounded compatibility and live replay proof | `resolved` |
| `4` | Docs, handoff, and debt-register closeout | `resolved` |

### Milestone `0`: Baseline lock and owner-boundary gate design

Outcome label: `resolved`

Work:

- Reproduce the current line counts, entry points, and focused test baseline for the two large
  owner modules.
- Record the preserved contract surfaces from the closed extraction-fidelity and direct-eval seam
  packets before any implementation begins.
- Add or update owner-boundary tests first so the later split fails closed if the public
  facade/dispatch surfaces re-absorb low-level work.

Required verification:

```bash
git status -sb
wc -l src/usfs_r1_ea_sources/extraction_fidelity_eval.py src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py
rg -n "^def run_extraction_fidelity_eval|^def resolve_source_set_phase_statuses|^def _upstream_phase_status|^def _extraction_fidelity_phase_status|^def _downstream_phase_status|^def _forest_plan_profile_phase_status|^def _forest_plan_component_retrieval_phase_status" src/usfs_r1_ea_sources/extraction_fidelity_eval.py src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py
PYTHONPATH=src uv run --extra dev pytest tests/test_extraction_fidelity_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_cli_eval.py tests/test_phase_eval.py tests/test_architecture_contract.py -q
rg -n "extraction_fidelity_eval_results.json|phase_eval_direct_eval.py|review_direct_eval_status|source-set-f70ea11e04ae3d53" docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md
git diff --check
```

### Milestone `1`: Extraction-fidelity internal owner split

Outcome label: `resolved`

Work:

- Extract manifest-contract validation and fixture-shape validation out of
  `run_extraction_fidelity_eval(...)`.
- Extract case execution and temporary-workspace orchestration into explicit internal owners.
- Extract metrics, category rollups, and Markdown reporting into explicit internal owners.
- Keep `ExtractionFidelityEvalResult`, the command surface, the manifest, and the output filenames
  unchanged.
- Reduce `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` to a thin public facade with a target
  closeout budget of `<= 400` lines.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_extraction_fidelity_eval.py tests/test_cli_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
wc -l src/usfs_r1_ea_sources/extraction_fidelity_eval.py
git diff --check
```

### Milestone `2`: Source-set direct-eval producer split

Outcome label: `resolved`

Work:

- Keep `resolve_source_set_phase_statuses(...)` and `_source_set_phase_status(...)` as the dispatch
  seam only.
- Extract producer-specific status builders into explicit peer owners for:
  - upstream evaluation
  - extraction fidelity
  - downstream direct evaluation
  - forest-plan profile evaluation
  - forest-plan component retrieval evaluation
- Keep `phase_eval_direct_eval.py` as the contract facade that calls the source-set resolver.
- Preserve phase status shapes, failure reasons, identity checks, threshold-failure details, and
  canonical result-path behavior.
- Reduce `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py` to a thin dispatch module
  with a target closeout budget of `<= 250` lines.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_cli_eval.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
wc -l src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py
git diff --check
```

### Milestone `3`: Bounded compatibility and live replay proof

Outcome label: `resolved`

Work:

- Re-run the dedicated extraction-fidelity producer to prove its contract and durable outputs remain
  intact after the split.
- Re-run source-set `phase-eval` on the full-canonical source set so the full source-set producer
  family is exercised, including full-canonical-only source-set phases.
- Re-run review-bound `phase-eval` for ECID so the live current blocker family is re-read after the
  split.
- Confirm the expected truth after the split:
  - `extraction-fidelity-eval` still writes the same durable artifact family
  - the full-canonical source-set `phase-eval` still consumes the direct-eval source-set owners
  - ECID review-bound `phase-eval` remains blocked by the same direct-eval/replay family unless a
    separately-proved bug fix changes that state

Required verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extraction-fidelity-eval --manifest config/extraction_fidelity_eval_v1.json --output-dir source_library
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
```

### Milestone `4`: Docs, handoff, and debt-register closeout

Outcome label: `resolved`

Work:

- Update `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md` so future sessions know:
  - this owner-boundary child packet closed
  - the dedicated extraction-fidelity and phase-eval direct-eval contract surfaces remain preserved
  - whether the current ECID direct-eval blocker family changed or stayed the same
- Update `docs/architecture_contract.toml` if new helper modules were introduced.
- If any explicit temporary shortcut was approved, record it in `docs/TECH_DEBT_REGISTER.md` in the
  same milestone.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_extraction_fidelity_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_cli_eval.py tests/test_phase_eval.py tests/test_promotion_suite.py tests/test_promotion_suite_full_canonical.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Required Implementation Artifacts

- narrowed `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`
- narrowed `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`
- any new adjacent `extraction_fidelity_eval_*` and `phase_eval_direct_eval_source_set_*` helper
  modules
- focused owner-boundary tests proving public facades dispatch into extracted helpers
- updated `docs/architecture_contract.toml` if new modules are introduced

## Required Documentation And Handoff Updates

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this child plan with milestone status updates if execution starts here
- `docs/TECH_DEBT_REGISTER.md` only if an approved shortcut is introduced

## Required Verification Gates

- Focused behavior and contract tests:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_extraction_fidelity_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_cli_eval.py tests/test_phase_eval.py tests/test_architecture_contract.py -q`
- Promotion/readiness compatibility when touched:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_promotion_suite_full_canonical.py -q`
- Static quality:
  - `PYTHONPATH=src uv run --extra dev ruff check src tests`
  - `PYTHONPATH=src python -m compileall src`
  - `git diff --check`
- Bounded live compatibility:
  - `extraction-fidelity-eval`
  - source-set `phase-eval --source-set-id source-set-4fb59e9eb43045cb`
  - review-bound `phase-eval --review-id v1-cg-ecid-compliance-review`

## Acceptance Criteria

- `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` is reduced below `800` lines and its target
  closeout budget of `<= 400` lines is met.
- `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py` is reduced below `800` lines and
  its target closeout budget of `<= 250` lines is met.
- Boundary tests prove that `run_extraction_fidelity_eval(...)` delegates to extracted internal
  owners rather than retaining contract validation, scenario execution, metrics, and reporting in
  one file.
- Boundary tests prove that `resolve_source_set_phase_statuses(...)` dispatches to extracted
  producer-specific owners rather than retaining multiple large status builders in one file.
- `tests/test_extraction_fidelity_eval.py`, `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_cli_eval.py`, `tests/test_phase_eval.py`, and `tests/test_architecture_contract.py`
  pass without weaker assertions, skips, or broadened tolerances.
- If new helper modules are introduced, `docs/architecture_contract.toml` and the matching
  architecture contract tests are updated in the same milestone.
- The bounded live verification still produces the same governed truth after the split unless a
  separately-proved bug fix changes it:
  - dedicated extraction-fidelity artifact remains present and valid
  - full-canonical source-set `phase-eval` still exercises the source-set direct-eval owners
  - ECID review-bound `phase-eval` does not invent a new blocker family
- No new temporary shortcut lands without a same-milestone `docs/TECH_DEBT_REGISTER.md` entry.

## Stop Conditions

- Stop if the split would require renaming the public `extraction-fidelity-eval` command, changing
  its manifest/result schemas, or redesigning the already-closed `phase_eval_direct_eval.py` seam.
- Stop if the live current-state docs no longer show `source-set-f70ea11e04ae3d53` as the active
  ECID review-bound replay lane or `source-set-4fb59e9eb43045cb` as the current full-canonical
  source-set phase-eval anchor; refresh the plan baseline first.
- Stop if the only path to green is weaker assertions, new skips/xfails, or undocumented temporary
  debt.
- Stop if preserving compatibility would require broad downloader/catalog/extraction reruns beyond
  the bounded commands listed here.
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
  packet as source-set direct-eval producer concentration.
- If both owner splits close and the live ECID review-bound `phase-eval` blocker family remains
  behaviorally red, route the next truthful runtime work back to
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`.
- If future architecture work still needs to address the other reopened `>800` files after this
  child packet closes, route that remaining backlog through
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`.
