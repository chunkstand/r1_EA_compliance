# Sidecar Compliance Review Adoption Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The sidecar branch now has validated sidecar chunks, sidecar retrieval eval, isolated graph/claim
previews, graph/claim canonical adoption, and sidecar rule-claim link preview/eval. The next
downstream risk is proving that compliance review can consume validated sidecar rule-claim links
without rebuilding or mutating canonical `rule_claim_links/`.

Current evidence:

- `rule-claim-link --links-dir` can write reviewer-ready sidecar links under
  `rule_claim_links_sidecar/<rule_pack_id>/<version>/`.
- `rule-claim-eval` revalidates sidecar link summaries before scoring.
- Current routing listed compliance review as the next downstream sidecar adoption packet after
  rule-link preview/eval.

## Goal, Non-Goals, And Scope

Goal: add an opt-in compliance-review path that consumes an explicit validated
`rule_claim_links.jsonl` artifact, records whether the rule-link directory is canonical, and passes
that path through compliance review eval and gold eval.

Non-goals:

- Do not promote sidecar rule-claim links into canonical `rule_claim_links/`.
- Do not change phase-eval, reviewer package, or knowledge-graph consumers.
- Do not mutate ignored production `source_library/` during closeout verification.
- Do not weaken rule-claim validation, compliance review validation, or generated rule-pack gates.

Scope:

- Add `--rule-claim-links-path` to `compliance-review`, `compliance-review-eval`, and
  `compliance-gold-eval`.
- Revalidate explicit rule-link artifacts with their sibling summary, validation, gap, and SQLite
  artifacts before compliance findings use them.
- Require source-set, rule-pack ID/version/path, reviewer-readiness, and top-k compatibility.
- Update tests, output schema docs, current-state docs, routing, and handoff.

## Intent Hierarchy

Invariant: canonical compliance-review behavior remains unchanged when no explicit
`--rule-claim-links-path` is supplied.

Optimization target: let reviewer-facing compliance paths run against sidecar-backed rule links
without forcing canonical mutation.

Acceptable tradeoffs: explicit sidecar adoption requires a caller-supplied link path and matching
effective rule pack; phase-eval and package/KG adoption stay in later packets.

Explicit non-negotiables: explicit links must be complete, reviewer-ready, identity-matched, and
freshly revalidated before findings consume them.

Intent lock: this packet adopts sidecar rule links into compliance review only, not phase-eval,
reviewer package, knowledge-graph, or canonical promotion.

## Owner Surfaces And Placement

- `src/usfs_r1_ea_sources/compliance_review.py` owns explicit rule-link artifact loading,
  identity checks, revalidation, and fallback to canonical reuse/build behavior.
- `src/usfs_r1_ea_sources/compliance_review_eval.py` and
  `src/usfs_r1_ea_sources/compliance_gold_eval.py` own pass-through of the explicit links path.
- `src/usfs_r1_ea_sources/cli_compliance.py` owns the public CLI argument.
- `src/usfs_r1_ea_sources/compliance_validation.py` owns reviewer-visible canonical-vs-sidecar
  path reporting in summaries and validation details.
- `tests/test_compliance_review.py`, `tests/test_compliance_review_eval.py`, and
  `tests/test_cli.py` own regression coverage for sidecar consumption and CLI propagation.
- `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
  `docs/SESSION_HANDOFF.md` own durable contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: stale or incomplete sidecar links bypass compliance readiness. Owner surface:
  `compliance_review.py`. Prevention: require summary, validation, links, gaps, and SQLite
  artifacts and call the rule-claim eval validator before use. Fail threshold: compliance review
  consumes explicit links that current validation rejects.
- Weak point: wrong source set or rule pack. Owner surface: `compliance_review.py`. Prevention:
  compare source set when supplied, rule-pack ID/version/path, reviewer-ready flags, and top-k.
  Fail threshold: a mismatched sidecar path produces compliance findings instead of raising.
- Weak point: eval wrapper drift. Owner surface: `compliance_review_eval.py` and
  `compliance_gold_eval.py`. Prevention: pass the explicit path through the same core review
  function and test eval output summaries. Fail threshold: direct review works but review eval or
  gold eval silently rebuilds canonical links.
- Weak point: reviewer-visible provenance ambiguity. Owner surface: `compliance_validation.py` and
  `docs/OUTPUT_SCHEMAS.md`. Prevention: compliance summaries and validation details report actual
  link dir, canonical link dir, and whether the consumed dir is canonical. Fail threshold: reports
  omit the sidecar/canonical distinction.
- Weak point: CLI or file-size drift. Owner surface: `cli_compliance.py` and architecture gates.
  Prevention: keep changes in the existing compliance CLI helper and run architecture quality/probe
  checks. Fail threshold: route-doc/file-size gates or architecture contracts fail.

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing compliance,
rule-claim, eval, or architecture tests to close this packet.

## Milestone Sequence

Milestone 1: Sidecar rule-link adoption for compliance review

- Add explicit rule-link path loading and revalidation to compliance review.
- Pass `--rule-claim-links-path` through compliance review eval and gold eval.
- Add sidecar consumption tests that prove canonical rule links are not rebuilt.
- Update output schema docs, current-state docs, routing, and handoff.
- Outcome label: resolved when focused tests, lint, compile, architecture gates, CLI smoke,
  plan lint, parity sweep, and local commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_compliance_review_eval.py tests/test_compliance_gold_eval.py tests/test_compliance_coverage.py tests/test_cli.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/SIDECAR_COMPLIANCE_REVIEW_ADOPTION_MILESTONE_PLAN.md --strict`
- Temp CLI smoke with fixture-backed source library only; do not mutate ignored production
  `source_library/`.
- Closeout parity sweep for docs, handoff, and route truth.

## Acceptance Criteria

- `compliance-review --rule-claim-links-path <rule_claim_links_sidecar/.../rule_claim_links.jsonl>`
  consumes validated sidecar rule links and does not create canonical rule-link outputs.
- `compliance-review-eval` and `compliance-gold-eval` pass the explicit link path through to each
  generated compliance review.
- Explicit link paths fail closed on missing sibling artifacts, source-set mismatch, rule-pack
  mismatch, insufficient top-k, failed validation, or non-reviewer-ready summaries.
- `compliance_review.json` and `compliance_validation.json` expose actual link directory, canonical
  link directory, and canonical-vs-sidecar status.
- Existing canonical compliance-review behavior remains backward compatible.
- Docs and handoff state that phase-eval, reviewer package, and knowledge-graph sidecar adoption
  remain future packets.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
`docs/SESSION_HANDOFF.md` with the new explicit rule-link path, eval behavior, verification status,
and residual downstream adoption route.

## Stop Conditions

- Stop if compliance review must promote or overwrite canonical rule-link artifacts to consume
  sidecar links.
- Stop if explicit sidecar consumption cannot reuse current rule-claim validation.
- Stop if phase-eval, reviewer package, or knowledge-graph adoption becomes necessary to prove this
  packet.
- Stop if architecture ownership requires a broad layer exception.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified packet slice after implementation, focused verification, architecture
probe, CLI smoke, closeout parity sweep, and docs/handoff updates pass. Do not stage ignored
`source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  compliance review, compliance review eval, compliance gold eval, compliance coverage, CLI,
  architecture contract, and architecture quality tests passed.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 515 code files, 17 above 800 lines, no Python or JS/TS import cycles,
  and no source module above the 20-import fan-out gate.
- CLI smoke result:
  fixture-backed temp source library ran `compliance-review --rule-claim-links-path` against
  sidecar rule links, reported `rule_claim_links_are_canonical=false`, and did not create canonical
  rule-link outputs.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: phase-eval, reviewer package, and knowledge-graph sidecar adoption remain future
  bounded packets.

## Residual Risks And Next Routing

After this packet, sidecar rule-link artifacts can feed compliance review and the compliance review
eval stack. Phase-eval, reviewer package, and knowledge-graph consumers still need separate bounded
packets before they can depend on sidecar-backed compliance artifacts.
