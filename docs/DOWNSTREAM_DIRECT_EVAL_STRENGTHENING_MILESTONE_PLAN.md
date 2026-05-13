# Downstream Direct Eval Strengthening Milestone Plan

Date: 2026-05-12

Status: Closed (resolved) on 2026-05-13

Closeout summary:

- Implemented tracked downstream direct-eval governance in `config/downstream_direct_eval_v1.json`
  plus contract-object shipped seed files for retrieval, claims, rule-claim links, and
  compliance review.
- Added shared threshold/contract helpers in `src/usfs_r1_ea_sources/eval_metrics.py`, fail-closed
  downstream readiness routing in `src/usfs_r1_ea_sources/evidence_graph.py`, and focused contract
  tests.
- Expanded the shipped downstream suites to live coverage floors of retrieval `12` cases, claims
  `10`, rule-claim links `24`, and compliance review `5`, including hard negatives, multi-source
  cases, and conditional base-vs-generated review coverage.
- Closeout replay on `source-set-5e65d845ce77e1a0` passed retrieval `12/12`, claims `10/10`,
  rule-claim `24/24`, compliance review `5/5`, `compliance-coverage`, and source-set
  `phase-eval` `9/9` with `downstream_direct_evaluation` present and passing.
- Architecture guardrail check from
  `/Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py`
  completed without introducing a new hotspot class or module cycle in this milestone slice.

Owner context: This is a fresh standalone follow-on milestone plan. It does not append to
`docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`; it starts only after that milestone is
closed green and committed. This plan assumes the upstream closeout has already delivered the
durable direct-eval register and readiness wiring called for there, including
`docs/EVALUATION_COVERAGE_REGISTER.md`. If the upstream closeout lands those artifacts under a
different name, Sequence 0 of this plan must update the routing before code changes begin.

## Purpose

Close the downstream direct-eval gap in the retrieval-to-review chain. Today the shipped
retrieval, claim, and rule-claim evals mostly prove that some relevant hit exists with provenance.
That is better than no eval, but it does not fail closed on ranking regressions, partial recall,
false positives, or easy positive-only suites. The default retrieval, claim, and compliance-review
seed sets are also too small to serve as durable ongoing coverage.

This milestone exists to turn those direct-eval lanes into contract-based, coverage-checked, and
thresholded gates that can prevent quality drift over time.

This milestone is not complete until the stronger direct-eval contracts, shipped seed suites,
readiness/register wiring, required docs, handoff updates, and one local atomic commit all land
together. A verified but uncommitted slice is only ready-to-close.

## Current Evidence

- `src/usfs_r1_ea_sources/retrieval.py` `run_retrieval_eval(...)` currently passes cases when
  minimum hits, one expected source hit, expected terms, and provenance are present. It already
  supports `expect_no_hits`, but the shipped default seed does not use that negative-path capability.
- `src/usfs_r1_ea_sources/claim_extraction.py` `run_claim_eval(...)` currently passes cases when
  some hit satisfies source, claim type, term, minimum count, and provenance checks. It does not
  track ranked recall, false positives, or missing-required-source rates.
- `src/usfs_r1_ea_sources/rule_claim_binding.py` `run_rule_claim_link_eval(...)` follows the same
  permissive pattern for rule-to-claim links.
- `config/retrieval_eval_seed.json` currently ships only `3` cases.
- `config/claim_eval_seed.json` currently ships only `2` cases.
- `config/compliance_review_eval_seed.json` currently ships only `3` cases.
- `config/rule_claim_link_eval_seed.json` is broader than the other seeds, but it is still mostly
  positive-path and does not declare hard-negative or rank-quality thresholds.
- `tests/test_retrieval.py` already proves the retrieval layer can score deterministic zero-hit
  negative cases, but that capability is not enforced in the shipped default contract.
- `src/usfs_r1_ea_sources/forest_plan_component_eval.py` and
  `config/forest_plan_component_eval_seed.json` already show the stronger pattern this repo should
  reuse: explicit `coverage_requirements`, explicit `metric_thresholds`, case-level results, and
  aggregate gating.

## Goal

Resolve the scoped downstream direct-eval weakness by making the shipped default retrieval, claim,
rule-claim, and compliance-review eval suites:

- contract-based rather than bare lists;
- large enough to include hard negatives, multi-source recall checks, and conditional/no-hit cases;
- measured by rank-quality, recall, and false-positive metrics instead of only "some relevant hit";
- visible in the upstream-created evaluation coverage register and the same readiness route rather
  than left as unit-test-only truth.

Completion means all of the following are true:

- the default shipped downstream eval files declare coverage requirements and metric thresholds;
- retrieval, claim, and rule-claim eval results include `recall@k`, reciprocal-rank style rank
  metrics, `nDCG@k`, `false_positive_rate`, and `missing_required_source_rate`;
- hard negatives are first-class shipped cases, not only unit-test fixtures;
- compliance-review eval coverage expands beyond the current three-case proving surface and records
  zero unexpected-positive and zero missing-required-source rule drift on the shipped suite;
- the evaluation coverage register and the same readiness gate introduced by the upstream milestone
  fail closed when downstream direct-eval coverage or thresholds drift.

## Non-Goals

- Do not re-open capture, catalog, extraction, or upstream direct-eval work covered by the
  prerequisite upstream milestone except where this plan explicitly consumes its register/gate.
- Do not rewrite core retrieval, claim-extraction, or rule-linking algorithms just to optimize a
  score if the real issue is thin eval coverage.
- Do not widen this milestone into applicability-gold, forest-plan component, NEPA 3D, or full V1
  review redesign beyond narrow readiness/register integration.
- Do not depend on broad network refreshes, full corpus regeneration, or new off-repo package
  replays as the normal proof path.
- Do not weaken, narrow, skip, or delete existing tests to get the new eval suites green. Any
  replacement coverage must be equivalent or stronger.

## Scope

- `retrieval-eval`, `claim-eval`, `rule-claim-eval`, and `compliance-review-eval`
- the default shipped seed/config contracts for those commands
- shared ranking/coverage helpers, if needed
- focused tests that prove positive-path, hard-negative, multi-source, and false-positive behavior
- downstream rows in `docs/EVALUATION_COVERAGE_REGISTER.md`
- the same readiness route chosen by the upstream milestone so downstream direct-eval drift cannot
  hide behind structural-validity booleans

## Out Of Scope

- new downloader or extraction fixtures
- new real-package proving reviews beyond the shipped compliance-review eval fixtures
- ad hoc review-local eval files as a substitute for strengthening the shipped default suites
- a second parallel evaluation register or a second unrelated readiness route

## Owner Surfaces

- Retrieval eval owner:
  `src/usfs_r1_ea_sources/retrieval.py`,
  `src/usfs_r1_ea_sources/cli_derived.py`,
  `config/retrieval_eval_seed.json`,
  `tests/test_retrieval.py`
- Claim eval owner:
  `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/cli_derived.py`,
  `config/claim_eval_seed.json`,
  `tests/test_claim_extraction.py`
- Rule-claim eval owner:
  `src/usfs_r1_ea_sources/rule_claim_binding.py`,
  `src/usfs_r1_ea_sources/cli_derived.py`,
  `config/rule_claim_link_eval_seed.json`,
  `tests/test_rule_claim_binding.py`
- Compliance-review eval owner:
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/cli_compliance.py`,
  `config/compliance_review_eval_seed.json`,
  `tests/test_compliance_review.py`
- Cross-lane contract/gating owner:
  `config/downstream_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/eval_metrics.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `tests/test_downstream_direct_eval_contracts.py`
- Docs and routing owner:
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep lane-specific scoring and result-shaping inside the lane owner modules. Do not create one
  monolithic downstream evaluator that owns retrieval, claims, links, and compliance logic.
- If shared metric helpers are needed, place them in a small reusable module such as
  `src/usfs_r1_ea_sources/eval_metrics.py`. Do not duplicate `recall@k`, reciprocal-rank, or
  `nDCG@k` formulas across three different lane owners.
- Promote the shipped default eval files from bare JSON lists to explicit contract objects with
  `schema_version`, `eval_id`, `coverage_requirements`, `metric_thresholds`, and `cases`.
- If backward compatibility for ad hoc legacy list files is retained, make it explicit and
  test-covered. The shipped default files must not silently fall back to legacy list semantics.
- Reuse the single evaluation coverage register and the same readiness gate introduced by the
  upstream milestone. Do not invent a second register, second report family, or second promotion
  path.
- Keep hard negatives and forbidden-hit expectations visible in config as data. Do not bury them in
  code-only special cases.

## Weak-Point Prevention Contract

- Weak point forecast: case counts increase, but the repo still passes on "some relevant hit"
  without detecting degraded ranking, missing required sources, or false positives.
  Owner surface: `src/usfs_r1_ea_sources/retrieval.py`,
  `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding.py`,
  `config/downstream_direct_eval_v1.json`
  Prevention gate: each lane contract must require hard-negative coverage, multi-source coverage,
  `recall@k`, reciprocal-rank, `nDCG@k`, `false_positive_rate`, and
  `missing_required_source_rate`.
  Fail threshold: a lane can pass while a hard-negative case returns hits, a required source is
  absent from top-k, or a non-relevant result outranks the first relevant result below the locked
  threshold.
  Controlled violation: demote a relevant result below a non-relevant result or add a forbidden hit;
  the eval must fail.
  Future-Codex misuse scenario: a later session pads the suite with more easy positives and claims
  the pass rate improved; the contract must fail on missing negative/multi-source coverage and on
  unchanged false-positive drift.

- Weak point forecast: contract-object metadata is added, but loaders silently ignore it or break
  legacy eval-file handling in a way that hides the drift.
  Owner surface: `config/retrieval_eval_seed.json`,
  `config/claim_eval_seed.json`,
  `config/rule_claim_link_eval_seed.json`,
  `config/compliance_review_eval_seed.json`,
  `tests/test_downstream_direct_eval_contracts.py`
  Prevention gate: the default shipped files must be parsed as contract objects and validated for
  required coverage/threshold keys; if legacy list support remains, it must stay explicit and
  covered by tests.
  Fail threshold: the default file loads without contract validation, or a contract missing
  thresholds/hard-negative counts is accepted.
  Controlled violation: delete `metric_thresholds` or `coverage_requirements` from a shipped
  contract fixture; the loader test must fail.
  Future-Codex misuse scenario: a later session swaps the default file back to a bare list to get
  green faster; the contract test must fail before commit.

- Weak point forecast: claim and rule-claim metrics rely on unstable runtime order instead of stable
  relevance matchers, so rank signals become noisy or meaningless.
  Owner surface: `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding.py`,
  `src/usfs_r1_ea_sources/eval_metrics.py`
  Prevention gate: rank metrics must key off stable relevance matchers such as source record,
  claim type, rule ID, and deterministic text/hash matchers rather than raw output order alone.
  Fail threshold: the same current artifacts produce different eval metrics without a real artifact
  change, or rank metrics cannot distinguish the correct claim/link from a nearby false positive.
  Controlled violation: mutate one claim/link matcher so the wrong source still looks lexically
  plausible; the metric and per-case mismatch details must fail.
  Future-Codex misuse scenario: a later session counts any first returned result as relevant even
  when the source or claim identity is wrong; the matcher-based gate must fail.

- Weak point forecast: compliance-review stays tiny and happy-path-heavy, so lower-layer retrieval
  or claim regressions still pass the terminal review fixture.
  Owner surface: `config/compliance_review_eval_seed.json`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `tests/test_compliance_review.py`
  Prevention gate: the shipped compliance-review eval contract must require at least one
  all-authorities control package, at least two hard-negative or unrelated-package cases, at least
  two targeted conditional-subset cases, and zero unexpected-positive or missing-required-source
  rule drift.
  Fail threshold: the shipped review suite drops back to three easy cases or passes while a rule
  reports a positive finding without the required supporting source family.
  Controlled violation: remove the unrelated-package case or strip the required land-exchange
  source expectation from a conditional case; the eval must fail.
  Future-Codex misuse scenario: a later session keeps only the all-authorities package and calls
  the lane covered; the coverage contract must fail.

- Weak point forecast: downstream direct-eval strengthening lands in code and tests, but the
  register/readiness route still looks only at `passed=true` booleans or ignores missing result
  files entirely.
  Owner surface: `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/SESSION_HANDOFF.md`
  Prevention gate: reuse the same register-aware readiness integration delivered by the upstream
  milestone, and extend it with downstream rows for case-count, hard-negative-count, and threshold
  drift.
  Fail threshold: readiness can go green when a downstream result file is stale, missing, below the
  minimum case-count floor, or below a locked metric threshold.
  Controlled violation: delete a downstream eval result file or drop a hard-negative case count
  below the declared minimum; the readiness route must fail.
  Future-Codex misuse scenario: a later session updates tests only and forgets the operator-facing
  truth surface; the register/readiness gate must fail before commit.

## Milestone Sequence

### Sequence 0 - Post-Upstream Preflight And Contract Baseline

Outcome label: reduced

Purpose: start this lane only after the upstream milestone is truly complete, then lock the new
downstream coverage contract before scoring changes begin.

Implementation tasks:

1. Verify the prerequisite upstream closeout exists and is green:
   - `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md` is closed and committed
   - `docs/EVALUATION_COVERAGE_REGISTER.md` exists
   - the upstream-created readiness route distinguishes direct eval from structural validation
2. Add `config/downstream_direct_eval_v1.json` with:
   - the four governed lanes: `retrieval`, `claims`, `rule_claim_links`, `compliance_review`
   - minimum shipped case-count floors:
     - retrieval: `case_count >= 12`, `hard_negative_case_count >= 3`,
       `multi_source_case_count >= 3`
     - claims: `case_count >= 10`, `hard_negative_case_count >= 3`,
       `multi_source_or_type_confusion_case_count >= 3`
     - rule-claim links: `case_count >= 20`, `hard_negative_case_count >= 4`,
       `multi_source_case_count >= 4`
     - compliance review: `case_count >= 5`, `hard_negative_package_case_count >= 2`,
       `conditional_subset_case_count >= 2`, `all_authorities_control_case_count >= 1`
   - locked metric-threshold keys for each lane
   - freshness requirements for any readiness gate that consumes result files
3. Extend `docs/EVALUATION_COVERAGE_REGISTER.md` with downstream rows marked at baseline as
   `coverage_thin` or equivalent, referencing the current default commands and seed files.
4. Add `tests/test_downstream_direct_eval_contracts.py` proving:
   - missing coverage requirements fail
   - missing threshold keys fail
   - case-count floors fail
   - the shipped default contracts cannot silently fall back to legacy list-only parsing
5. Run a freshness check on the current active source set and lock the baseline before changing
   thresholds. If the active source set changes during implementation, rerun the freshness check and
   update the locked baseline before closeout.

Acceptance signals:

- The repo has one downstream direct-eval contract and one downstream register extension, not a
  second parallel governance path.
- Missing thresholds, missing hard-negative coverage, or stale baseline assumptions fail in tests.
- The sequence records freshness expectations explicitly before implementation broadens the suites.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The upstream milestone is not actually complete, or its register/readiness artifacts do not exist.
- The new contract can only be expressed by loosening or bypassing the upstream register/readiness
  route.
- The baseline can only be made green by lowering floors or removing negative cases.

### Sequence 1 - Strengthen Retrieval Eval Coverage And Ranking Signals

Outcome label: resolved

Purpose: make retrieval direct eval fail on ranking degradation, false positives, and missing
required sources instead of only on total absence of a relevant hit.

Implementation tasks:

1. Promote `config/retrieval_eval_seed.json` from a bare list to a contract object with
   `schema_version`, `eval_id`, `coverage_requirements`, `metric_thresholds`, and `cases`.
2. Expand the shipped retrieval suite to include:
   - at least `3` hard-negative `expect_no_hits` cases
   - at least `3` multi-source recall cases
   - filtered cases across source role, authority level, topic, or citation routing
   - at least one forbidden-source case where lexical overlap exists but the source must not rank
3. Extend `run_retrieval_eval(...)` to emit per-case and aggregate:
   - `recall_at_k`
   - `first_relevant_rank`
   - `mrr`
   - `ndcg_at_k`
   - `false_positive_rate`
   - `missing_required_source_rate`
   - `hard_negative_pass_rate`
4. Record per-case missing required sources, forbidden returned sources, relevant ranks, and metric
   contributions in `retrieval_eval_results.json`.
5. If shared metric helpers are needed, add them in `src/usfs_r1_ea_sources/eval_metrics.py`
   rather than duplicating the formulas elsewhere.

Metric thresholds for the shipped retrieval contract:

- `hard_negative_pass_rate = 1.0`
- `false_positive_rate = 0.0`
- `missing_required_source_rate = 0.0`
- `recall_at_k = 1.0` on required-source cases
- `mrr >=` the fresh Sequence 0 locked baseline and never below `0.90`
- `ndcg_at_k >=` the fresh Sequence 0 locked baseline and never below `0.90`

Acceptance signals:

- The shipped retrieval suite no longer passes on a single easy positive hit.
- A negative case that returns any result fails.
- A case that omits a required source in top-k fails and reports the missing source explicitly.
- Rank-quality drift appears in the output summary, not only in unit-test assertions.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id <active-source-set-id>
git diff --check
```

Stop conditions:

- Retrieval can only meet the new thresholds by shrinking `top_k`, narrowing queries, or deleting
  hard negatives.
- The active corpus cannot support stable multi-source cases without a documented blocker and a new
  routed follow-up milestone.

### Sequence 2 - Strengthen Claim Eval Coverage And Ranked Recall

Outcome label: resolved

Purpose: make claim eval measure complete relevant-claim recovery and false-positive drift rather
than only source/type/term presence.

Implementation tasks:

1. Promote `config/claim_eval_seed.json` to the same contract-object shape as retrieval.
2. Expand the shipped claim suite to include:
   - at least `3` hard-negative cases
   - at least `3` multi-source or claim-type confusion cases
   - at least one case where the correct source is present but the wrong claim type should fail
3. Extend `run_claim_eval(...)` to support hard-negative/no-hit cases and to compute:
   - `recall_at_k`
   - `first_relevant_rank`
   - `mrr`
   - `ndcg_at_k`
   - `false_positive_rate`
   - `missing_required_source_rate`
   - `hard_negative_pass_rate`
4. Use stable relevance matchers for claims, such as source record plus claim type and a
   deterministic claim-text/hash matcher, rather than raw output order alone.
5. Record per-case missing required claims/sources, wrong-type hits, forbidden hits, and rank
   details in `claim_eval_results.json`.

Metric thresholds for the shipped claim contract:

- `hard_negative_pass_rate = 1.0`
- `false_positive_rate = 0.0`
- `missing_required_source_rate = 0.0`
- `recall_at_k = 1.0` on required-claim cases
- `mrr >=` the fresh Sequence 0 locked baseline and never below `0.90`
- `ndcg_at_k >=` the fresh Sequence 0 locked baseline and never below `0.90`

Acceptance signals:

- A claim from the wrong source or wrong claim type is visible as a false positive, not hidden
  behind `source_hit=true`.
- The shipped claim suite is no longer only two happy-path cases.
- Current claim artifacts still fail closed when tampered before scoring begins.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_claim_extraction.py tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval --output-dir source_library --source-set-id <active-source-set-id>
git diff --check
```

Stop conditions:

- Claim metrics depend on unstable runtime ordering instead of deterministic claim identity.
- The suite only turns green by removing type-confusion or negative-path cases.

### Sequence 3 - Strengthen Rule-Claim Eval Coverage And Link Ranking

Outcome label: resolved

Purpose: make rule-claim eval detect wrong-source and wrong-claim links, not just the presence of
 any plausible link for a rule.

Implementation tasks:

1. Promote `config/rule_claim_link_eval_seed.json` to a contract object while preserving or
   increasing the current case count floor of `20`.
2. Expand the shipped rule-claim suite to include:
   - at least `4` hard-negative cases
   - at least `4` multi-source or source-family recall cases
   - at least one case where a lexically similar but wrong source should be treated as a false
     positive
3. Extend `run_rule_claim_link_eval(...)` to compute:
   - `recall_at_k`
   - `first_relevant_rank`
   - `mrr`
   - `ndcg_at_k`
   - `false_positive_rate`
   - `missing_required_source_rate`
   - `hard_negative_pass_rate`
4. Use stable relevance matchers for rule-to-claim links, such as rule ID plus deterministic claim
   identity and source identity, instead of only `rule_id` plus any returned link.
5. Record per-case missing required links/sources, forbidden links, and rank contributions in
   `rule_claim_link_eval_results.json`.

Metric thresholds for the shipped rule-claim contract:

- `hard_negative_pass_rate = 1.0`
- `false_positive_rate = 0.0`
- `missing_required_source_rate = 0.0`
- `recall_at_k = 1.0` on required-link cases
- `mrr >=` the fresh Sequence 0 locked baseline and never below `0.90`
- `ndcg_at_k >=` the fresh Sequence 0 locked baseline and never below `0.90`

Acceptance signals:

- A rule can no longer pass because one plausible claim link exists somewhere in top-k.
- Wrong-source or wrong-claim links are surfaced explicitly in per-case output.
- The shipped rule-claim suite keeps its existing breadth and adds negative-path coverage instead
  of replacing breadth with a smaller easier set.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_rule_claim_binding.py tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval --output-dir source_library --source-set-id <active-source-set-id>
git diff --check
```

Stop conditions:

- Rule-claim coverage can only pass by lowering the current case-count floor below `20`.
- The lane relies on a hidden source-ID shortcut instead of explicit contract data.

### Sequence 4 - Expand Compliance-Review Eval Coverage And Wire Downstream Readiness

Outcome label: resolved

Purpose: keep the terminal review lane aligned with the stronger lower-layer eval contracts and
make downstream direct-eval drift visible in the same readiness route introduced upstream.

Implementation tasks:

1. Promote `config/compliance_review_eval_seed.json` to a contract object and expand it to at
   least `5` cases:
   - one all-authorities control package
   - two hard-negative or unrelated-package cases
   - two targeted conditional-subset cases
2. Extend `run_compliance_review_eval(...)` to record aggregate downstream drift metrics including:
   - `unexpected_positive_finding_rate`
   - `missing_required_source_rule_rate`
   - existing status/source-record/source-role/citation coverage metrics
3. Keep the compliance-review suite aligned with `compliance-coverage` so rule-pack eval-case
   coverage stays explicit and does not get easier.
4. Extend the upstream-created `docs/EVALUATION_COVERAGE_REGISTER.md` and the same readiness gate
   it feeds so downstream rows fail when:
   - result files are missing or stale
   - case-count floors are not met
   - hard-negative coverage floors are not met
   - a metric threshold falls below its contract
5. Update docs and handoff so operators can tell which lanes are direct-eval-governed and what the
   current downstream threshold contract is.

Metric thresholds for the shipped compliance-review contract:

- `unexpected_positive_finding_rate = 0.0`
- `missing_required_source_rule_rate = 0.0`
- `status_match_rate = 1.0`
- `source_record_match_rate = 1.0`
- `source_document_role_match_rate = 1.0`
- `citation_coverage_rate = 1.0`
- `graph_coverage_rate = 1.0`

Acceptance signals:

- The shipped review suite is no longer only three proving cases.
- A positive finding without its required supporting source family fails explicitly.
- The operator-facing register/readiness route exposes downstream eval drift, not just downstream
  artifact existence.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library
git diff --check
```

Stop conditions:

- The new compliance-review suite only goes green by dropping the unrelated-package or
  conditional-subset cases.
- Readiness wiring requires a second parallel report family instead of the upstream-created register
  route.

## Required Implementation Artifacts

- `config/downstream_direct_eval_v1.json`
- `config/retrieval_eval_seed.json`
- `config/claim_eval_seed.json`
- `config/rule_claim_link_eval_seed.json`
- `config/compliance_review_eval_seed.json`
- `src/usfs_r1_ea_sources/eval_metrics.py`
- `tests/test_downstream_direct_eval_contracts.py`
- focused lane-test updates in:
  `tests/test_retrieval.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_rule_claim_binding.py`,
  `tests/test_compliance_review.py`

## Required Documentation And Handoff Updates

- `README.md`
  add a short explanation that the default downstream direct-eval suites are contract-based and
  register-backed
- `docs/OUTPUT_SCHEMAS.md`
  document the new contract object shape, new result metrics, hard-negative semantics, and any
  freshness fields used by the readiness route
- `docs/EVALUATION_COVERAGE_REGISTER.md`
  extend the register with downstream rows, thresholds, status, and next-owner routing
- `docs/CURRENT_SYSTEM_STATE.md`
  update only if live readiness or current promoted coverage claims change in the repo
- `docs/SESSION_HANDOFF.md`
  route the next session to the first incomplete sequence and record the verification state

## Required Verification Gates

Minimum closeout gates for the full milestone:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_claim_extraction.py tests/test_rule_claim_binding.py tests/test_compliance_review.py tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library
git diff --check
```

If the same readiness route introduced by the upstream milestone is review-scoped rather than
source-set-scoped for the downstream rows, rerun `phase-eval` with the relevant `--review-id`
before closeout and record that exact command in `docs/SESSION_HANDOFF.md`.

## Acceptance Criteria

- The repo has one explicit downstream direct-eval contract and one downstream register extension.
- The shipped default retrieval, claim, rule-claim, and compliance-review eval files are contract
  objects, not only bare case lists.
- Hard negatives are first-class shipped cases in retrieval, claim, rule-claim, and
  compliance-review coverage where appropriate.
- Retrieval, claim, and rule-claim outputs all record `recall@k`, reciprocal-rank, `nDCG@k`,
  `false_positive_rate`, and `missing_required_source_rate`.
- The shipped downstream suites meet or exceed the declared case-count floors.
- The shipped downstream suites meet all zero-drift thresholds:
  `hard_negative_pass_rate=1.0`,
  `false_positive_rate=0.0`,
  `missing_required_source_rate=0.0`,
  `unexpected_positive_finding_rate=0.0`,
  `missing_required_source_rule_rate=0.0`.
- Any rank-quality threshold based on the fresh Sequence 0 baseline is locked at or above that
  refreshed baseline and never reduced later just to make a test pass.
- Replacement coverage is equivalent or broader. Do not weaken the existing lane tests, skip new
  hard negatives, or narrow the shipped suites just to get green.
- The same readiness gate introduced by the upstream milestone fails when downstream direct-eval
  coverage or thresholds drift.

## Stop Conditions

- The upstream prerequisite milestone is not actually closed green and committed.
- The active source set or readiness route changes mid-implementation and the baseline is not
  refreshed before continuing.
- Stronger metrics can only be met by deleting negative cases, lowering thresholds, or shrinking
  the case-count floors.
- The implementation starts creating a second parallel downstream readiness/register system.
- The milestone uncovers a corpus or source-identity blocker that cannot be resolved without a new
  explicit follow-on milestone. In that case, stop, mark the issue `reduced`, and route the blocker
  in docs and handoff instead of weakening the contract.

## Local Commit Closeout Policy

This milestone is not complete until:

1. all required verification gates pass;
2. the contract files, code, tests, docs, register, and handoff are updated together;
3. only the verified downstream direct-eval slice is staged; and
4. one local atomic commit lands the milestone.

Do not stage unrelated dirty files already present in the worktree. If unrelated files remain
dirty, leave them untouched and call them out in the final handoff. Do not weaken tests or lower
thresholds to get a passing result; any replacement coverage must be equivalent or stronger.

## Residual Risks And Next Milestone Routing

- This milestone resolves the shipped downstream direct-eval contract gap, but it does not by
  itself create new adjudicated gold review suites for every future forest or review family.
- If this milestone exposes real retrieval-quality limits in the active corpus, the next milestone
  should be a corpus or ranking-quality improvement milestone, not a contract-relaxation pass.
- If compliance-review eval expands cleanly but review-local gold coverage is still narrow, route
  the next follow-on to a separate real-package or multi-forest gold-eval expansion plan rather than
  widening this milestone after the fact.
