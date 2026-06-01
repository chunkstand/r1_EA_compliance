# Sidecar Graph Claim Canonical Adoption Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The sidecar branch has `chunks_v2`, sidecar retrieval eval, isolated graph/claim previews, and a
sidecar graph/claim promotion-readiness eval. The remaining graph/claim gap is that canonical
`evidence_graph/` and `claims/` outputs still cannot adopt the passed sidecar layer through a
governed, auditable command.

Current evidence:

- `chunk-sidecar-consumer-eval` writes a fail-closed graph/claim promotion-readiness result.
- Current routing says canonical graph/claim promotion requires a new bounded packet.
- Rule-link, compliance, phase-eval, reviewer package, and knowledge-graph adoption remain
  downstream of canonical graph/claim adoption.

## Goal, Non-Goals, And Scope

Goal: add an opt-in canonical graph/claim adoption command that rebuilds canonical graph and claim
outputs from a passed full sidecar consumer eval.

Non-goals:

- Do not promote rule-claim links, compliance review, review packets, phase-eval, or knowledge
  graph artifacts.
- Do not make sidecar adoption automatic.
- Do not mutate ignored production `source_library/` during closeout verification.

Scope:

- Add `chunk-sidecar-consumer-promote`.
- Default to dry-run readiness output; require `--apply` for canonical mutation and
  `--replace-canonical` before replacing existing canonical graph/claim directories.
- Require passed, non-partial, reviewer-ready sidecar retrieval, graph, and claim eval evidence.
- Update tests, architecture contract, output schema docs, current-state docs, routing, and handoff.

## Intent Hierarchy

Invariant: canonical graph and claim outputs may only adopt sidecar chunks through an explicit,
auditable command backed by a passed full sidecar consumer eval.

Optimization target: make graph/claim adoption reproducible and reversible enough for generated
artifact workflows without opening rule-link/compliance/phase-eval adoption in the same packet.

Acceptable tradeoffs: the command may require explicit replacement flags and backup existing
canonical graph/claim directories; production adoption can stay unrun in this code packet.

Explicit non-negotiables: no automatic canonical mutation, no partial-eval promotion, and no
downstream reviewer-ready claim beyond graph/claim outputs.

Intent lock: this packet advances canonical graph/claim adoption only; it does not make downstream
rule-link, compliance, phase-eval, reviewer package, or knowledge-graph outputs sidecar-backed.

## Owner Surfaces And Placement

- `src/usfs_r1_ea_sources/sidecar_consumer_promotion.py` owns promotion preflight, apply, backup,
  and result summaries.
- `src/usfs_r1_ea_sources/cli_sidecar_eval.py` owns sidecar eval command argument adaptation.
- `src/usfs_r1_ea_sources/cli_derived_registration.py` and `src/usfs_r1_ea_sources/cli_derived.py`
  own command registration and dispatch.
- `docs/architecture_contract.toml` owns the sidecar eval module, command, and result artifact.
- `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
  `docs/SESSION_HANDOFF.md` own durable user-visible contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: accidental canonical mutation. Owner surface:
  `sidecar_consumer_promotion.py`. Prevention gate: dry-run is default; `--apply` is required and
  replacing existing canonical outputs also requires `--replace-canonical`. Fail threshold: tests
  show canonical outputs changed without `--apply`.
- Weak point: promoting partial smoke evidence. Owner surface:
  `sidecar_consumer_promotion.py` promotion checks. Prevention gate: promotion requires non-partial
  eval mode and sidecar retrieval, graph, and claims reviewer readiness. Fail threshold: a partial
  eval can produce `promotion_ready=true`.
- Weak point: stale or wrong source-set evidence. Owner surface: sidecar promotion result checks.
  Prevention gate: promotion checks eval schema, source-set identity, sidecar summary presence, and
  path existence. Fail threshold: mismatched eval source-set promotes canonical outputs.
- Weak point: scope creep. Owner surface: command implementation and current docs. Prevention gate:
  command only rebuilds canonical graph/claim outputs from sidecar chunks/retrieval. Fail threshold:
  rule-link, compliance, phase-eval, review, or knowledge-graph outputs are written by this packet.

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing sidecar, graph,
claim, phase-eval, or architecture tests to close this packet.

## Milestone Sequence

Milestone 1: Graph/claim canonical adoption command

- Add sidecar promotion runtime and CLI command.
- Add dry-run, apply, replacement, and partial-eval regression tests.
- Update architecture contract, output schema docs, current-state docs, routing, and handoff.
- Outcome label: resolved when focused tests, lint, compile, architecture gates, smoke validation,
  parity sweep, and local commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_sidecar_consumer_promotion.py tests/test_sidecar_consumer_eval.py tests/test_sidecar_consumer_preview.py tests/test_sidecar_retrieval_eval.py tests/test_evidence_graph.py tests/test_cli.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- Temp smoke with fixture-backed source library only; do not mutate ignored production
  `source_library/`.

## Acceptance Criteria

- `chunk-sidecar-consumer-promote` writes a deterministic promotion result artifact.
- Dry-run mode reports promotion readiness without changing canonical graph/claim outputs.
- Apply mode requires a passed non-partial sidecar consumer eval, sidecar reviewer readiness, and
  explicit replacement consent when canonical graph/claim directories already exist.
- Applied promotion rebuilds canonical graph and claim outputs from sidecar chunks and sidecar
  retrieval paths, and records canonical summaries in the result.
- Docs and handoff state that rule-link, compliance, phase-eval, reviewer package, and knowledge
  graph adoption remain future work.

## Documentation And Handoff

Update `README.md`, `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`,
`docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` with the new command, safety flags,
verification status, and residual downstream adoption route.

## Stop Conditions

- Stop if promotion would require changing rule-link, compliance, review, phase-eval, or
  knowledge-graph artifacts in this packet.
- Stop if passing promotion requires weakening sidecar eval checks.
- Stop if canonical mutation cannot be opt-in and replace-gated.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified packet slice after implementation, focused verification, architecture
probe, smoke validation, closeout parity sweep, and docs/handoff updates pass. Do not stage ignored
`source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  sidecar promotion, sidecar consumer eval, sidecar preview, sidecar retrieval eval, evidence graph,
  CLI, architecture contract, and architecture quality tests passed.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 515 code files, 17 above 800, no Python or JS/TS import cycles, and no
  source module above the 20 fan-out gate.
- Smoke result:
  `/tmp/usfs-r1-sidecar-consumer-promote.rQ06OT/` fixture-backed CLI apply smoke passed with
  reviewer-ready canonical graph and claim summaries rebuilt from sidecar inputs.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: rule-link, compliance, phase-eval, reviewer package, and knowledge-graph adoption
  remain future work.

## Residual Risks And Next Routing

After this packet, graph and claim outputs have an explicit canonical adoption command. Downstream
rule-link, compliance, phase-eval, reviewer package, and knowledge-graph sidecar adoption still
need separate bounded packets with their own eval thresholds and contract updates.
