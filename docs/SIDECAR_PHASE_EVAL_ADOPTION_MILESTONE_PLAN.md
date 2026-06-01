# Sidecar Phase Eval Adoption Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The sidecar branch can now build validated sidecar chunks, retrieval, graph and claim previews,
sidecar rule-claim links, sidecar rule-claim direct eval, and sidecar-backed compliance review.
The remaining phase-eval risk was that source-set readiness still resolved the
`rule_claim_binding` phase and direct-eval status from canonical `rule_claim_links/`, even when a
review-scoped compliance review consumed noncanonical sidecar links.

Current evidence:

- The compliance-review explicit rule-link path records the consumed rule-link path, sibling summary,
  validation path, canonical link directory, and canonical-vs-sidecar status.
- Rule-claim eval writes `rule_claim_link_eval_results.json` beside sidecar
  rule-claim link artifacts.
- Current routing listed phase-eval sidecar adoption as the next downstream packet after compliance
  review adoption.

## Goal, Non-Goals, And Scope

Goal: make phase-eval select and evaluate the rule-claim link artifacts actually consumed by a
review-scoped compliance review, including noncanonical sidecar rule-link paths and their sibling
direct-eval result.

Non-goals:

- Do not promote sidecar rule-claim links into canonical `rule_claim_links/`.
- Do not change reviewer package or knowledge-graph consumers.
- Do not mutate ignored production `source_library/` during closeout verification.
- Do not weaken phase-eval, compliance review, rule-claim, direct-eval, or architecture gates.

Scope:

- Add explicit rule-claim link path support to phase-eval for sidecar selection.
- Auto-follow noncanonical rule-link paths from review-scoped compliance review summaries.
- Fail closed when an explicit sidecar path conflicts with the compliance review path.
- Report selected rule-link path, selected eval path, sidecar/canonical status, and failed path
  checks in the rule-claim binding phase.
- Update focused tests, output-schema docs, current-state docs, routing, and handoff.

## Intent Hierarchy

Invariant: canonical source-set phase-eval behavior remains unchanged when no review-scoped
sidecar path is present.

Optimization target: make phase-eval readiness align with the sidecar-backed rule-link and
compliance path actually under review.

Acceptable tradeoffs: the sidecar direct-eval override is limited to rule-claim binding; broader
reviewer package and knowledge-graph adoption stay in later packets.

Explicit non-negotiables: explicit rule-link paths must match the selected rule-link summary and,
when a compliance review is present, the compliance review's recorded rule-link path.

Intent lock: this packet adopts sidecar rule-link evidence into phase-eval only, not reviewer
package generation, knowledge-graph artifacts, or canonical promotion.

## Owner Surfaces And Placement

- src/usfs_r1_ea_sources/phase_eval.py owns source-set/review path selection and CLI-facing
  rule-claim link path propagation.
- src/usfs_r1_ea_sources/phase_eval_sidecar.py owns sidecar rule-link path context, mismatch
  checks, and the sidecar rule-claim direct-eval status override.
- src/usfs_r1_ea_sources/phase_eval_source_set_phases.py owns rule-claim binding phase details
  and fail-closed path-check integration.
- src/usfs_r1_ea_sources/cli_eval.py owns the public phase-eval explicit rule-link argument.
- docs/architecture_contract.toml owns the new phase-eval sidecar helper module in the existing
  phase-eval layer.
- tests/test_phase_eval_sidecar.py owns sidecar phase-eval behavior, mismatch failure, and CLI
  propagation coverage.
- tests/test_phase_eval_source_set.py and tests/test_compliance_review_sidecar.py own the
  boundary-preserving test splits needed to keep architecture gates green.
- docs/OUTPUT_SCHEMAS.md, docs/CURRENT_SYSTEM_STATE.md, docs/CURRENT_ROUTING.md, and
  docs/SESSION_HANDOFF.md own durable contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: phase-eval reports canonical readiness while review evidence used sidecar links.
  Owner surface: `phase_eval.py`. Prevention: when compliance review summary records a noncanonical
  rule-link path, read the sibling sidecar summary, validation, and eval result. Fail threshold:
  sidecar-backed compliance review leaves rule-claim binding pointed at canonical eval output.
- Weak point: explicit path drift hides a stale or mismatched sidecar artifact. Owner surface:
  phase_eval_sidecar.py. Prevention: compare explicit path to selected summary and compliance
  review summary, then add failed path checks that make rule-claim binding non-ready. Fail
  threshold: mismatched explicit and compliance paths still pass.
- Weak point: direct-eval coverage remains canonical. Owner surface: `phase_eval_sidecar.py`.
  Prevention: override only the rule-claim binding direct-eval status with the selected sidecar
  `rule_claim_link_eval_results.json` and validate eval ID, source set, and contract SHA. Fail
  threshold: sidecar direct eval is ignored or accepted with wrong identity.
- Weak point: helper growth worsens already-large phase-eval owners. Owner surface:
  phase_eval_sidecar.py and phase-eval test split suites. Prevention: put sidecar helper logic in
  a new layer-owned module and split inherited oversized tests into focused suites. Fail threshold:
  architecture line-budget or module-roster gates fail.
- Weak point: reviewer-visible provenance ambiguity. Owner surface: phase_eval_source_set_phases.py
  and docs/OUTPUT_SCHEMAS.md. Prevention: emit selected path, explicit path, compliance review
  path, canonical link dir, actual link dir, sidecar flag, and failed path checks. Fail threshold:
  phase output omits enough path context to audit sidecar use.

Anti-test-weakening rule: test moves must preserve or strengthen behavioral coverage. The moved
eval-trace phase-eval assertion now matches the direct eval-trace gate contract for a matching
optional store (`evidence_status=passed`).

## Milestone Sequence

Milestone 1: Sidecar phase-eval adoption

- Add phase-eval sidecar rule-link path selection and direct-eval override.
- Add explicit mismatch failure and CLI propagation tests.
- Preserve architecture boundaries with focused sidecar and source-set test suites.
- Update output schema docs, current-state docs, routing, and handoff.
- Outcome label: resolved when focused tests, lint, compile, architecture gates, CLI smoke, plan
  lint, parity sweep, and local commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_sidecar.py tests/test_compliance_review_sidecar.py tests/test_phase_eval.py tests/test_phase_eval_source_set.py tests/test_phase_eval_test_boundary.py tests/test_compliance_review_test_boundary.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/SIDECAR_PHASE_EVAL_ADOPTION_MILESTONE_PLAN.md --strict`
- Temp CLI smoke with fixture-backed source library only; do not mutate ignored production
  `source_library/`.
- Closeout parity sweep for docs, handoff, and route truth.

## Acceptance Criteria

- Review-scoped phase-eval auto-follows a compliance review's noncanonical
  `rule_claim_links_sidecar/.../rule_claim_links.jsonl` path.
- Phase-eval explicit rule-link path selection uses the sidecar sibling summary,
  validation, and direct-eval result.
- Explicit sidecar paths fail `rule_claim_binding` when they conflict with the review's recorded
  compliance-review rule-link path.
- `rule_claim_binding.details` reports selected, explicit, and compliance-review rule-link paths;
  selected eval path; canonical link dir; actual link dir; sidecar/canonical status; and failed path
  checks.
- `rule_claim_binding` direct-eval status points at the selected sidecar
  `rule_claim_link_eval_results.json` and validates eval ID, source set, and contract SHA.
- Existing canonical phase-eval behavior remains backward compatible.
- Docs and handoff state that reviewer package and knowledge-graph sidecar adoption remain future
  packets.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
`docs/SESSION_HANDOFF.md` with the new phase-eval sidecar path, direct-eval behavior, verification
status, and residual downstream adoption route.

## Stop Conditions

- Stop if phase-eval must promote or overwrite canonical rule-link artifacts to consume sidecar
  links.
- Stop if sidecar direct-eval identity cannot be checked against the committed downstream manifest.
- Stop if reviewer package or knowledge-graph adoption becomes necessary to prove this packet.
- Stop if architecture ownership requires a broad layer exception.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified packet slice after implementation, focused verification, architecture
probe, CLI smoke, closeout parity sweep, and docs/handoff updates pass. Do not stage ignored
`source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  phase-eval sidecar, compliance sidecar, core phase-eval, phase-eval source-set split, phase-eval
  boundary, compliance boundary, architecture contract, and architecture quality tests passed.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 519 code files, 17 above 800 lines, no Python or JS/TS import cycles,
  and no source module above the 20-import fan-out gate.
- CLI smoke result:
  fixture-backed temp source library ran phase-eval for `phase-sidecar-smoke` after a
  sidecar-backed compliance review, auto-selected sidecar rule links, used the sidecar
  `rule_claim_link_eval_results.json`, and kept `rule_claim_binding` passed and reviewer-ready.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: reviewer package and knowledge-graph sidecar adoption remain future bounded
  packets.

## Residual Risks And Next Routing

After this packet, phase-eval can evaluate sidecar-backed rule-link/compliance paths without
canonical mutation. Reviewer package and knowledge-graph consumers still need separate bounded
packets before they can depend on sidecar-backed compliance artifacts.
