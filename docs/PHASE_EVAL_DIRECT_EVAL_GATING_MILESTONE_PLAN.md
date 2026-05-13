# Phase Eval Direct-Eval Gating Milestone Plan

Date: 2026-05-13

Status: Proposed

Owner context: This is a refreshed standalone follow-on milestone plan. It now stacks after
`docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md`, which itself starts only after
`docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md` closes green and is committed. Because the
real-package coverage milestone depends on the gold-coverage milestone, and that milestone depends
on the downstream and upstream evaluation-coverage milestones, this plan assumes the earlier chain
has already delivered the durable evaluation coverage register, the strengthened downstream eval
contracts, the aggregate gold-coverage gate, and the tracked real-package review coverage route for
declared contract-owned reviews. If those prerequisite closeouts land equivalent artifacts under
different names, Sequence 0 of this plan must refresh the routing before code changes begin rather
than recreating the same ownership under new names.

## Purpose

Close the gap between `phase-eval` as a readiness aggregator and `phase-eval` as a governed
direct-eval-aware readiness gate.

Today `phase-eval` is useful because it rolls many subsystem artifacts into one durable readiness
surface. The problem is that its core source-set phases still mostly trust prior
`validation_passed` and `reviewer_ready` booleans. That is enough to expose structural failures,
but it is not enough to fail closed when a subsystem remains proxy-covered, when direct-eval
coverage goes missing, or when case-count and metric floors drift below the contracts established by
the prerequisite milestones.

This milestone exists to make `phase-eval` consume explicit machine-readable per-subsystem eval
summaries and fail closed when a critical subsystem:

- has only proxy or validation-only coverage where direct eval is required;
- has a missing, stale, mismatched, or schema-invalid eval summary;
- falls below declared case-count, hard-negative-count, or metric thresholds; or
- claims promotion readiness through phase counts alone while direct-eval coverage is degraded.

This milestone is not complete until the direct-eval-aware `phase-eval` contract, normalized
summary loading, focused tests, promotion wiring, docs, handoff updates, and one local atomic
commit all land together. A verified but uncommitted slice is only ready-to-close.

## Dependency And Sequence 0 Refresh Rule

- Start this milestone only after `docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md` is closed
  green and committed.
- If the real-package coverage milestone lands its tracked review-slot manifest, package-authority
  surfaces, or aggregate coverage gate under different names, Sequence 0 must adopt those artifacts
  and rewrite this plan's remaining commands before implementation continues.
- If the predecessor milestone changes which reviews are treated as declared contract-owned reviews,
  Sequence 0 must refresh the review-scoped `phase-eval` routing before code changes begin.
- If the predecessor milestone leaves review-scoped coverage intentionally blocked or partially
  implemented, this plan must preserve that state explicitly; it must not invent a second review
  roster or claim broader contract-backed promotion readiness than the predecessor artifacts prove.

## Current Evidence

- `src/usfs_r1_ea_sources/evidence_graph.py` `run_phase_aligned_eval(...)` currently builds the
  core `catalog_capture`, `extraction`, `retrieval`, `evidence_graph`, `claim_extraction`, and
  `rule_claim_binding` phases mostly from existing lane `passed` and `reviewer_ready` fields.
- The phase summary still resolves overall readiness through
  `all(phase["passed"] for phase in phases)` and
  `all(phase["reviewer_ready"] for phase in phases)`, so the governing summary does not yet
  distinguish direct-eval-backed readiness from proxy-backed readiness.
- `_phase(...)` currently emits only `phase_validation_failed` and `phase_not_reviewer_ready`
  failure reasons, which is not enough to express `missing_required_direct_eval`,
  `proxy_only_coverage`, `direct_eval_threshold_failed`, or `eval_summary_identity_mismatch`.
- `config/phase_eval_direct_eval_v1.json` does not exist at the current baseline.
- `docs/OUTPUT_SCHEMAS.md` documents the current `phase_eval_results.json` phase list and blockers,
  but it does not yet define a direct-eval coverage contract for the critical subsystem phases.
- `docs/EVALUATION_COVERAGE_REGISTER.md` currently has no explicit `phase_eval` row or equivalent
  direct-eval coverage owner for this layer.
- `config/promotion_suite_v1.json` currently treats the core `phase_eval` surface mostly as a
  count-based readiness artifact. The main source-set check locks `passed_phase_count` and
  `reviewer_ready_phase_count`, but it does not yet require `proxy_only_phase_count = 0`,
  `missing_direct_eval_phase_count = 0`, or threshold-backed direct-eval status.
- `phase-eval` already contains two useful patterns the repo can generalize:
  it consumes `compliance_coverage_results.json` with source-set and rule-pack identity checks, and
  it consumes `compliance_gold_eval_results.json` with source-set, rule-pack, and review-scope
  checks. That proves the repo already has a precedent for explicit eval-summary consumption; the
  gap is that this pattern is not yet generalized to the other critical subsystem phases.
- The prerequisite milestone chain is already routed in docs:
  `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`,
  `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`, and
  `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`.
- `docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md` now exists as the immediate predecessor
  plan for declared contract-owned reviews. This milestone should consume the tracked review-slot
  or aggregate coverage outputs from that plan rather than creating a second independent review
  roster inside `phase-eval`.
  This milestone should consume the results of the earlier chain, not recreate its contracts inside
  `phase-eval`.

## Goal

Resolve the scoped `phase-eval` weakness by turning it into a direct-eval-aware readiness gate that
consumes the explicit per-subsystem eval summaries produced by the prerequisite milestones.

Completion means all of the following are true:

- the repo has one tracked `phase-eval` direct-eval contract that names which subsystem summaries
  are required for source-set scope, review scope, and promotion-facing scope;
- `phase_eval_results.json` reports direct-eval coverage status per critical subsystem, not only
  aggregate phase counts;
- `phase-eval` fails closed when a required subsystem is proxy-only, missing its eval summary, or
  below its declared coverage and metric floors;
- review-scoped `phase-eval` can distinguish ad hoc reviews from contract-owned real-package
  reviews without pretending every review must satisfy the full multi-package gold gate; and
- promotion consumes the new direct-eval-aware `phase-eval` signals rather than relying on phase
  counts alone.

## Non-Goals

- Do not recreate the upstream direct-eval suite, the downstream direct-eval suite, or the
  gold-coverage suite inside this milestone. Consume their results and contracts instead.
- Do not rewrite retrieval, claim, rule-claim, applicability, compliance, or gold algorithms just
  to make the new `phase-eval` path pass.
- Do not create a second parallel readiness or promotion system outside `phase-eval`,
  `promotion-suite`, and the evaluation coverage register.
- Do not make `phase-eval` parse a Markdown register as the primary machine-readable truth surface.
  If prerequisite milestones did not produce a reusable machine-readable summary, add a focused
  sidecar contract instead of scraping prose.
- Do not weaken existing `phase-eval`, promotion-suite, applicability, compliance, or eval tests to
  get green. Any replacement coverage must be equivalent or broader.

## Scope

- source-set and review-scoped `phase-eval`
- one tracked machine-readable direct-eval contract for `phase-eval`
- normalized loading of upstream, downstream, and review/gold eval summaries where relevant
- direct-eval coverage classification in `phase_eval_results.json`
- promotion-suite checks that consume the new `phase-eval` direct-eval counters and failure modes
- evaluation coverage register and schema/docs alignment for the new readiness semantics

## Out Of Scope

- new upstream/downstream/gold case authoring beyond narrow fixture additions needed to prove the
  new `phase-eval` gates
- new full-corpus or full-package replays as a substitute for focused contract work
- NEPA 3D, decision-support, or project-SOW evaluator redesign except where those artifacts already
  participate in `phase-eval` and need schema-consistent direct-eval metadata later
- broad refactors of `evidence_graph.py` unrelated to the direct-eval gating seam

## Owner Surfaces

- `phase-eval` orchestration owner:
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`
- normalized direct-eval summary loading owner:
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `config/phase_eval_direct_eval_v1.json`,
  `tests/test_phase_eval_direct_eval_contracts.py`
- source-set and review gate tests:
  `tests/test_evidence_graph.py`,
  `tests/test_compliance_review.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_v1_ea_eval.py`
- promotion/register/docs owner:
  `config/promotion_suite_v1.json`,
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep the top-level `phase-eval` command and phase assembly in `evidence_graph.py`, but move new
  contract parsing, summary resolution, and normalized direct-eval result shaping into a focused
  helper such as `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`. Do not make the already-large
  `evidence_graph.py` own another monolithic block of path, schema, and threshold logic.
- Reuse the machine-readable eval summary artifacts and threshold contracts from the prerequisite
  milestones wherever possible. Do not duplicate their threshold values inside `phase-eval` unless
  the contract explicitly snapshots them for freshness-checked comparison.
- Follow the existing `compliance_coverage` and `compliance_gold_eval` pattern:
  explicit artifact path resolution, scope identity checks, schema checks, and structured failure
  details. Extend that pattern to upstream and downstream direct-eval summaries instead of adding
  a different style of ad hoc boolean gate.
- Keep ad hoc review usability intact. If a review is not one of the declared contract-owned
  real-package reviews, `phase-eval` may still run, but it must not report contract-backed
  promotion readiness for that review unless the required review-eval artifact exists and matches.
- If prerequisite milestone closeouts leave only a human-readable register, add a focused
  machine-readable sidecar under `config/` or `source_library/derived/` and make it the authoritative
  input for `phase-eval`. Do not scrape `docs/EVALUATION_COVERAGE_REGISTER.md`.

## Weak-Point Prevention Contract

- Weak point forecast: `phase-eval` gains more fields, but it still effectively trusts structural
  validation booleans for the critical lanes.
  Owner surface: `src/usfs_r1_ea_sources/evidence_graph.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `config/phase_eval_direct_eval_v1.json`
  Prevention gate: the `phase-eval` contract must mark each critical subsystem as
  `direct_eval_required`, `validation_only_allowed`, or `not_required_for_scope`, and the critical
  source-set phases must fail when a `direct_eval_required` summary is missing or proxy-only.
  Fail threshold: `phase-eval` still goes green while a critical subsystem has no direct-eval
  summary or is marked proxy-only.
  Controlled violation: remove the retrieval direct-eval summary while keeping retrieval
  validation/summaries green; `phase-eval` must fail on `missing_required_direct_eval`.
  Future-Codex misuse scenario: a later session restores old count-based checks and claims the phase
  is still governed; the direct-eval-required gate must fail.

- Weak point forecast: threshold values are duplicated or drift away from the upstream,
  downstream, or gold contracts they are supposed to enforce.
  Owner surface: `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`
  Prevention gate: `phase-eval` must read threshold-bearing eval summaries or contract-linked
  fields from the prerequisite milestone owners rather than hard-coded local numbers.
  Fail threshold: `phase-eval` can pass after a producer contract shrinks its case-count floor or
  metric threshold without updating the governing direct-eval contract.
  Controlled violation: lower a referenced case-count floor in a fixture summary without updating
  the declared contract snapshot; the direct-eval contract test must fail.
  Future-Codex misuse scenario: a later session changes only `phase-eval` thresholds to get green;
  the producer-contract identity check must fail.

- Weak point forecast: the new direct-eval logic worsens the `evidence_graph.py` hotspot and makes
  the readiness path harder to reason about.
  Owner surface: `src/usfs_r1_ea_sources/evidence_graph.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `tests/test_architecture_contract.py`
  Prevention gate: the new loader and contract logic must live in a focused helper module with
  contract tests, while `evidence_graph.py` only assembles phases from normalized results.
  Fail threshold: new direct-eval logic lands only as another large inline branch tree inside
  `evidence_graph.py` with no focused contract seam.
  Controlled violation: delete the helper module and inline the contract parser into
  `evidence_graph.py`; architecture and focused contract tests must fail.
  Future-Codex misuse scenario: a later session adds another eval-summary branch directly in
  `evidence_graph.py`; the placement rule and tests must catch the regression.

- Weak point forecast: review-scoped `phase-eval` becomes unusable for ad hoc reviews because it
  requires the full contract-owned review set for every run.
  Owner surface: `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `tests/test_compliance_review.py`,
  `tests/test_v1_ea_eval.py`
  Prevention gate: the contract must distinguish `required_for_declared_review_contract` from
  `not_required_for_ad_hoc_review`, and the summary must report that distinction explicitly.
  Fail threshold: a local review with valid structural artifacts fails only because it is not one
  of the promoted contract-owned packages.
  Controlled violation: run a fixture review without a declared real-package contract; the summary
  must stay runnable but record that contract-backed promotion readiness is unavailable.
  Future-Codex misuse scenario: a later session makes `v1-ea-eval` mandatory for every review and
  blocks routine operator use; the scoped requirement tests must fail.

- Weak point forecast: promotion continues to trust phase counts and ignores the new direct-eval
  detail fields.
  Owner surface: `config/promotion_suite_v1.json`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `tests/test_promotion_suite.py`
  Prevention gate: promotion checks must lock the new direct-eval counters and failure categories,
  not only `passed_phase_count` and `reviewer_ready_phase_count`.
  Fail threshold: promotion is green while `phase_eval_results.json` reports proxy-only or
  threshold-failed critical subsystems.
  Controlled violation: keep phase counts green but set `proxy_only_phase_count=1`; the promotion
  suite must fail.
  Future-Codex misuse scenario: a later session updates `phase-eval` but not promotion; the
  promotion-suite test must fail before commit.

## Milestone Sequence

### Sequence 0 - Post-Real-Package Preflight And Direct-Eval Contract Baseline

Outcome label: reduced

Purpose: start this lane only after the upstream, downstream, gold, and real-package coverage
milestones are truly complete, then lock the `phase-eval` direct-eval contract before loader
changes begin.

Implementation tasks:

1. Verify the prerequisite milestone chain exists and is green:
   - `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md` is closed and committed
   - `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md` is closed and committed
   - `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md` is closed and committed
   - `docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md` is closed and committed
   - the evaluation coverage register exists
   - the prerequisite milestones have durable machine-readable eval summaries or contract-owned
     equivalent artifacts for the lanes this milestone must consume
   - the real-package coverage milestone has durable tracked review-slot or aggregate coverage
     artifacts that this milestone can consume for declared contract-owned review routing
2. Add `config/phase_eval_direct_eval_v1.json` with:
   - `schema_version`
   - `contract_id`
   - source-set critical subsystem map
   - review-scope subsystem map
   - coverage class per subsystem:
     `direct_eval_required`,
     `validation_only_allowed`,
     `required_for_declared_review_contract`,
     `not_required_for_ad_hoc_review`
   - required summary identity fields such as `source_set_id`, `review_id`, `eval_id`,
     `contract_id`, `rule_pack_id`, `rule_pack_version`, and freshness markers
   - required counters such as `case_count`, `hard_negative_case_count`, and explicit metric
     threshold pass fields where the producer contract exposes them
   - a dependency reference to the tracked review-slot or aggregate review-coverage artifact created
     by the predecessor milestone, instead of a second hand-maintained review roster
3. Extend `docs/EVALUATION_COVERAGE_REGISTER.md` with a `phase_eval` or equivalent readiness row
   that records the baseline weakness as `proxy_aggregation_only` until implementation lands.
4. Add `tests/test_phase_eval_direct_eval_contracts.py` proving:
   - missing required subsystem summaries fail;
   - proxy-only critical subsystems fail;
   - mismatched summary identities fail; and
   - ad hoc reviews are still allowed to run without contract-owned review evals.
5. If the predecessor milestone shipped equivalent artifact names or commands, update this plan,
   the session handoff, and the closeout verification commands before Sequence 1 begins.

Acceptance signals:

- The repo has one tracked `phase-eval` direct-eval contract.
- Baseline tests prove the current proxy-only behavior is insufficient.
- The contract names the prerequisite summary owners instead of inventing a second truth source.
- The review-scoped contract path reuses the predecessor milestone's review-slot ownership instead
  of duplicating review identity by hand.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- One or more prerequisite milestones are not actually complete.
- The prerequisite producer outputs do not expose enough machine-readable identity or threshold
  fields to support direct-eval-aware readiness. If that happens, stop and route the missing field
  back to the producer milestone owner instead of hard-coding inference in `phase-eval`.
- The predecessor real-package coverage milestone did not leave a reusable tracked review-slot or
  aggregate coverage artifact and the only fallback is to duplicate review identity locally inside
  this milestone.

### Sequence 1 - Normalize Per-Subsystem Eval Summary Loading

Outcome label: reduced

Purpose: create one focused seam that resolves and validates eval summaries before `phase-eval`
turns them into readiness decisions.

Implementation tasks:

1. Add `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` with helpers that:
   - load the `phase-eval` direct-eval contract;
   - resolve relevant producer summaries for a given source set or review;
   - resolve declared contract-owned review metadata from the predecessor real-package coverage
     artifact or its adopted equivalent;
   - verify schema, scope identity, source-set/review binding, rule-pack binding, and freshness;
   - normalize summary outcomes into consistent fields such as
     `coverage_class`,
     `direct_eval_present`,
     `direct_eval_passed`,
     `proxy_only`,
     `case_count`,
     `hard_negative_case_count`,
     `threshold_failures`,
     `summary_path`,
     `contract_id`, and
     `failure_reasons`.
2. Reuse the existing `compliance_coverage` and `compliance_gold_eval` patterns where possible so
   the new loader speaks the same readiness language as the current explicit eval-summary phases.
3. Add focused tests for:
   - stale or mismatched source-set IDs;
   - stale or mismatched review IDs;
   - missing contract IDs or schema versions;
   - threshold-bearing summaries that report below-floor case counts; and
   - review-contract-only eval summaries on declared review IDs.

Acceptance signals:

- One normalized loader owns summary validation for the new direct-eval path.
- Summary failures are explicit and machine-readable.
- `evidence_graph.py` does not become the only place that knows how to interpret eval summaries.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The loader can only work by scraping Markdown or by duplicating all producer thresholds locally.
- The helper boundary cannot be kept focused and the logic starts turning into another monolithic
  `evidence_graph.py` branch tree.

### Sequence 2 - Make Source-Set Phase Eval Fail Closed On Proxy-Only Coverage

Outcome label: reduced

Purpose: wire the core source-set phases to the normalized direct-eval summaries so green phase
counts cannot hide degraded eval coverage.

Implementation tasks:

1. Extend the critical source-set phases in `run_phase_aligned_eval(...)`:
   - `catalog_capture`
   - `extraction`
   - `retrieval`
   - `claim_extraction`
   - `rule_claim_binding`
   so each phase records direct-eval details from the normalized loader.
2. Add new failure reasons as needed:
   - `missing_required_direct_eval`
   - `proxy_only_coverage`
   - `direct_eval_threshold_failed`
   - `direct_eval_identity_mismatch`
   - `direct_eval_schema_invalid`
3. Make a critical phase `passed=false` and `reviewer_ready=false` when structural validity is
   green but the required direct-eval summary is missing, proxy-only, mismatched, or below floor.
4. Add one explicit aggregate coverage phase or summary block, such as `evaluation_coverage`, that
   records:
   - `critical_phase_count`
   - `direct_eval_ready_phase_count`
   - `proxy_only_phase_count`
   - `missing_direct_eval_phase_count`
   - `threshold_failed_phase_count`
   - `validation_only_allowed_phase_count`
5. Update focused tests so `phase-eval` fails when:
   - retrieval validation is green but retrieval direct eval is missing;
   - extraction validation is green but upstream extraction direct eval is proxy-only; or
   - claim/rule-link summaries exist but their case-count floors are below contract.

Acceptance signals:

- Source-set `phase-eval` can no longer go green on structural booleans alone for critical lanes.
- The result artifact clearly shows which phases are direct-eval-backed and which are not.
- Count-based readiness alone is no longer enough to satisfy the phase surface.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_evidence_graph.py tests/test_phase_eval_direct_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id <active-source-set-id>
git diff --check
```

Stop conditions:

- The only way to keep legacy replays green is to mark critical phases `validation_only_allowed`.
- The implementation needs a second detached report instead of enriching `phase_eval_results.json`
  and the existing phase summary.

### Sequence 3 - Add Review-Scoped Contract Awareness And Promotion Enforcement

Outcome label: resolved

Purpose: finish the milestone by making review-scoped `phase-eval` and promotion consume the new
direct-eval-aware readiness semantics end to end.

Implementation tasks:

1. Extend review-scoped `phase-eval` so declared contract-owned reviews consume the required
   review-eval summaries, such as real-package review-contract eval output and the predecessor
   review-slot coverage artifact, while ad hoc reviews remain runnable with explicit
   `contract_backed_promotion_ready=false` semantics.
2. Update `phase_eval_results.json` for review scope to report:
   - whether the review is a declared contract-owned review;
   - which review-eval summaries were required;
   - which were present, missing, or stale; and
   - whether direct-eval-backed promotion readiness is available for that review.
3. Extend `config/promotion_suite_v1.json` so the source-set and review slots check the new
   `phase-eval` direct-eval fields, including:
   - `proxy_only_phase_count = 0`
   - `missing_direct_eval_phase_count = 0`
   - `threshold_failed_phase_count = 0`
   - `phase_eval_contract_id` or equivalent identity match
   - any required contract-backed review readiness field for the promoted review set
4. Update `README.md`, `docs/OUTPUT_SCHEMAS.md`, `docs/EVALUATION_COVERAGE_REGISTER.md`,
   `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` so operators can tell:
   - what `phase-eval` now enforces;
   - which phases still allow validation-only coverage;
   - how ad hoc reviews differ from declared contract-owned reviews; and
   - which direct-eval counters promotion relies on.

Acceptance signals:

- Review-scoped `phase-eval` distinguishes ad hoc use from contract-backed promotion use.
- Review-scoped `phase-eval` uses the predecessor real-package coverage owner rather than a second
  independent review roster.
- Promotion no longer relies on phase counts alone.
- Critical subsystem proxy coverage can no longer hide behind a green `phase-eval`.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_compliance_review.py tests/test_applicability_eval.py tests/test_v1_ea_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id <declared-review-id>
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

Stop conditions:

- Promotion cannot consume the new direct-eval counters without weakening the source-set or review
  contract.
- Review-scoped `phase-eval` can only be made green by requiring contract-only artifacts for every
  ad hoc review.

## Required Implementation Artifacts

- `config/phase_eval_direct_eval_v1.json`
- `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`
- focused updates to `src/usfs_r1_ea_sources/evidence_graph.py`
- `tests/test_phase_eval_direct_eval_contracts.py`
- focused updates to:
  `tests/test_evidence_graph.py`,
  `tests/test_compliance_review.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_promotion_suite.py`

## Required Documentation And Handoff Updates

- `README.md`
  add a short explanation that `phase-eval` now distinguishes direct-eval-backed readiness from
  proxy or validation-only readiness
- `docs/OUTPUT_SCHEMAS.md`
  document the new `phase-eval` direct-eval contract fields, per-phase detail fields, aggregate
  counters, and failure reasons
- `docs/EVALUATION_COVERAGE_REGISTER.md`
  add the `phase_eval` row, direct-eval dependency status, and routing for remaining validation-only
  phases if any remain accepted
- `docs/CURRENT_SYSTEM_STATE.md`
  update only if the live readiness or promotion claims change because of the new `phase-eval`
  contract
- `docs/SESSION_HANDOFF.md`
  route the next session to the first incomplete sequence and record the prerequisite chain
- this milestone plan with implementation status and closeout evidence

## Required Verification Gates

Minimum closeout gates for the full milestone:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_compliance_review.py tests/test_applicability_eval.py tests/test_v1_ea_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval --output-dir source_library --manifest config/gold_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id <declared-review-id>
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

If the prerequisite milestone closeouts publish machine-readable coverage summaries under different
commands or artifact paths than this plan currently names, including the predecessor real-package
coverage lane, Sequence 0 must update the closeout commands in `docs/SESSION_HANDOFF.md` before
implementation continues.

## Acceptance Criteria

- The repo has one explicit `phase-eval` direct-eval contract and one normalized eval-summary
  loader.
- `phase_eval_results.json` reports direct-eval status per critical subsystem, not only phase
  pass/reviewer-ready booleans.
- Source-set `phase-eval` fails when a critical subsystem is proxy-only, missing its direct eval,
  stale, mismatched, or below its declared case-count or metric floors.
- Review-scoped `phase-eval` distinguishes ad hoc review readiness from contract-backed promotion
  readiness.
- Promotion consumes the new direct-eval counters and failure categories rather than phase counts
  alone.
- Replacement coverage is equivalent or broader. Do not weaken existing `phase-eval`, promotion,
  applicability, compliance, or eval tests, and do not lower producer thresholds just to make the
  new gate pass.

## Stop Conditions

- The prerequisite upstream, downstream, or gold milestones are not actually complete.
- Producer eval outputs do not expose enough machine-readable identity or threshold information and
  the only proposed fallback is heuristic inference inside `phase-eval`.
- The implementation starts scraping Markdown for readiness truth instead of consuming explicit
  machine-readable artifacts.
- The only path to green is to reclassify critical subsystems as validation-only, lower producer
  thresholds, or remove contract-backed review requirements.
- The implementation starts creating a second detached readiness or promotion path outside the
  existing `phase-eval` and `promotion-suite` surfaces.

## Local Commit Closeout Policy

This milestone is not complete until:

1. all required verification gates pass;
2. the direct-eval contract, loader, `phase-eval` wiring, tests, docs, register, and handoff are
   updated together;
3. only the verified `phase-eval` direct-eval gating slice is staged; and
4. one local atomic commit lands the milestone.

Do not stage unrelated dirty files already present in the worktree. If unrelated files remain
dirty, leave them untouched and call them out in the final handoff. Do not weaken tests or lower
producer thresholds to get a passing result; any replacement coverage must be equivalent or
broader.

## Residual Risks And Next Milestone Routing

- This milestone resolves the `phase-eval` direct-eval gating gap for the prerequisite milestone
  chain, but it does not itself create new direct-eval suites for evaluator families that remain
  outside that chain.
- If, after this milestone, a remaining `phase-eval` phase is still legitimately
  `validation_only_allowed`, keep that status explicit in the evaluation coverage register and route
  the next milestone to direct-eval creation for that subsystem rather than hiding it behind phase
  counts.
- If this milestone closes green and the next evaluation weakness is still in fixture-locked NEPA
  3D, decision-support, or project-SOW lanes, route the next follow-on to those subsystem-specific
  evaluator plans rather than reopening `phase-eval`.
