# Sidecar Review Packet Adoption Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The sidecar branch can now build validated sidecar chunks, retrieval, graph and claim previews,
sidecar rule-claim links, sidecar-backed compliance review, and sidecar-aware phase-eval. The next
downstream risk was that reviewer package artifacts still treated canonical compliance outputs as a
self-contained ledger and did not preserve or validate the sidecar rule-claim lineage that produced
those outputs.

Current evidence:

- Sidecar-backed compliance review records the consumed rule-link path, canonical-vs-sidecar status,
  canonical link directory, and actual link directory.
- Review-scoped phase-eval records the selected sidecar rule-link path, selected sidecar direct-eval
  result, path-check failures, and rule-claim binding readiness.
- Current routing listed reviewer package sidecar adoption as the next bounded packet after
  phase-eval adoption.

## Goal, Non-Goals, And Scope

Goal: make `review-packet-index` preserve and fail-closed validate sidecar rule-claim lineage across
compliance review and review-scoped phase-eval, without changing canonical packet behavior when no
sidecar rule links are present.

Non-goals:

- Do not promote sidecar rule-claim links into canonical `rule_claim_links/`.
- Do not change knowledge-graph consumers.
- Do not mutate ignored production `source_library/` during closeout verification.
- Do not weaken review packet, phase-eval, compliance review, or architecture gates.

Scope:

- Load optional review-scoped `phase_eval_results.json` in the review packet artifact inventory.
- Add a review-packet-owned sidecar lineage helper that compares compliance review and phase-eval
  sidecar rule-link evidence.
- Record sidecar lineage in `review_packet_row_inventory.json`, `review_packet_index.json`, and
  `review_packet_index_validation.json`.
- Report sidecar lineage status through the review-scoped phase-eval `review_packet_index` phase.
- Update focused tests, architecture contract, output-schema docs, current-state docs, routing, and
  handoff.

## Intent Hierarchy

Invariant: canonical review packet behavior remains unchanged when no sidecar-backed rule links are
present.

Optimization target: make reviewer packages auditable against the exact sidecar-backed rule links
and direct-eval evidence used by compliance review and phase-eval.

Acceptable tradeoffs: the packet validates rule-claim lineage only; knowledge-graph sidecar adoption
stays in a later packet.

Explicit non-negotiables: sidecar lineage must fail closed when compliance review and phase-eval
select different rule-link paths, when phase-eval is missing or not reviewer-ready, or when selected
sidecar paths are missing.

Intent lock: this packet adopts sidecar rule-claim lineage into review packet artifacts only, not
knowledge-graph artifacts or canonical promotion.

## Owner Surfaces And Placement

- `src/usfs_r1_ea_sources/review_packet_index_artifacts.py` owns optional phase-eval artifact
  loading without making it required for canonical packets.
- `src/usfs_r1_ea_sources/review_packet_index_sidecar.py` owns sidecar rule-claim lineage
  extraction and validation-check construction.
- `src/usfs_r1_ea_sources/review_packet_index_inventory.py` owns row-inventory and packet-index
  lineage fields.
- `src/usfs_r1_ea_sources/review_packet_index_outputs.py` owns validation summary integration.
- `src/usfs_r1_ea_sources/phase_eval_optional_phases.py` owns the review-scoped phase-eval details
  surfaced for the review packet phase.
- `docs/architecture_contract.toml` owns the new helper module in the existing project-planning
  layer.
- `tests/test_review_packet_index_sidecar.py` owns sidecar lineage success and mismatch coverage.
- `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
  `docs/SESSION_HANDOFF.md` own durable contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: reviewer packages drop sidecar provenance. Owner surface:
  `review_packet_index_inventory.py`. Prevention gate: write the same lineage object to row
  inventory and packet index. Fail threshold: sidecar-backed packets omit selected
  compliance/phase-eval paths.
- Weak point: compliance review and phase-eval silently point at different sidecar links. Owner
  surface: `review_packet_index_sidecar.py`. Prevention gate: compare resolved selected paths and
  emit a failed validation check. Fail threshold: mismatched paths pass packet validation.
- Weak point: optional phase-eval breaks canonical packet indexing. Owner surface:
  `review_packet_index_artifacts.py`. Prevention gate: missing optional phase-eval passes for
  canonical packets, but an existing unparsable optional artifact fails. Fail threshold: canonical
  fixture packets require phase-eval.
- Weak point: sidecar direct-eval or path-check failures are hidden. Owner surface:
  `review_packet_index_sidecar.py`. Prevention gate: require phase-eval rule-claim binding
  readiness, no path-check failures, selected direct-eval presence, matching direct-eval path, and
  existing selected paths. Fail threshold: a non-ready sidecar phase produces a passing packet.
- Weak point: review packet owners grow past architecture budgets. Owner surface:
  `review_packet_index_sidecar.py` and review-packet boundary tests. Prevention gate: isolate
  sidecar lineage in a small helper and add explicit line-budget coverage. Fail threshold: focused
  boundary or architecture contract tests fail.

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing review packet,
phase-eval, compliance review, or architecture tests to close this packet.

## Milestone Sequence

Milestone 1: Sidecar review packet lineage adoption

- Add optional phase-eval artifact loading and sidecar lineage extraction.
- Persist lineage into row inventory and packet index outputs.
- Fail closed through validation checks and phase-eval review-packet phase details.
- Update architecture contract, output schemas, current-state docs, routing, and handoff.
- Outcome label: resolved when focused tests, lint, compile, architecture gates, CLI smoke, plan
  lint, parity sweep, and local commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_review_packet_index.py tests/test_review_packet_index_sidecar.py tests/test_review_packet_index_test_boundary.py tests/test_compliance_phase_eval.py tests/test_phase_eval_review.py tests/test_cli.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/SIDECAR_REVIEW_PACKET_ADOPTION_MILESTONE_PLAN.md --strict`
- Temp CLI smoke with fixture-backed source library only; do not mutate ignored production
  `source_library/`.
- Closeout parity sweep for docs, handoff, and route truth.

## Acceptance Criteria

- `review-packet-index` loads review-scoped `phase_eval_results.json` as an optional artifact.
- Sidecar-backed packets record compliance review rule-link path, phase-eval selected rule-link
  path, selected eval path, direct-eval path, canonical link dir, actual link dir, sidecar flag, path
  checks, and failed lineage checks.
- Validation fails closed when sidecar compliance review and phase-eval paths mismatch.
- Validation fails closed when sidecar phase-eval evidence is missing, not reviewer-ready, has path
  check failures, lacks selected direct-eval evidence, or points at missing selected paths.
- Existing canonical review packet behavior remains backward compatible.
- Docs and handoff state that knowledge-graph sidecar adoption remains the next downstream packet.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
`docs/SESSION_HANDOFF.md` with the new review packet sidecar lineage contract, verification status,
and residual downstream knowledge-graph adoption route.

## Stop Conditions

- Stop if review packet indexing must promote or overwrite canonical rule-link artifacts to prove
  sidecar lineage.
- Stop if phase-eval would need to become mandatory for canonical review packets.
- Stop if knowledge-graph adoption becomes necessary to prove this packet.
- Stop if architecture ownership requires a broad layer exception.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified packet slice after implementation, focused verification, architecture
probe, CLI smoke, closeout parity sweep, and docs/handoff updates pass. Do not stage ignored
`source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  review packet, review packet sidecar, review packet boundary, compliance phase-eval, phase-eval
  review, CLI, architecture contract, and architecture quality tests passed.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 521 code files, 17 above 800 lines, no Python or JS/TS import cycles,
  and no source module above the 20-import fan-out gate.
- CLI smoke result:
  fixture-backed temp source library under
  `/var/folders/7x/dm39gsxj38z2p2xtn3hqlj2h0000gn/T/usfs-r1-sidecar-review-packet.gd2_t06m/`
  ran `review-packet-index --review-id review-packet-sidecar-smoke`, recorded sidecar rule-claim
  lineage in row inventory and packet index, and kept sidecar lineage failed-check count at `0`.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: knowledge-graph sidecar adoption remains a future bounded packet.

## Residual Risks And Next Routing

After this packet, review packet artifacts can preserve and validate sidecar rule-claim lineage from
compliance review through phase-eval without canonical mutation. Knowledge-graph consumers still
need a separate bounded packet before they can depend on sidecar-backed compliance artifacts.
