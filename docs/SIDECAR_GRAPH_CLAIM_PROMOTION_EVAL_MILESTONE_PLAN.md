# Sidecar Graph Claim Promotion Eval Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The sidecar branch now has validated `chunks_v2`, sidecar retrieval eval, and isolated graph/claim
preview paths. The next promotion risk is deciding whether those preview consumers preserve
downstream graph and claim quality before any canonical graph or claim adoption.

Current evidence:

- `chunk-sidecar-retrieval-eval` compares sidecar retrieval against the baseline retrieval index.
- `evidence-graph-build` and `claim-extract` can consume sidecar chunks and retrieval summaries
  while writing isolated preview directories.
- Current-state and handoff docs explicitly say canonical graph/claim promotion still needs a new
  bounded packet with direct eval thresholds.

## Goal, Non-Goals, And Scope

Goal: add an opt-in sidecar graph/claim promotion-readiness eval gate that builds sidecar graph and
claim previews, compares their metrics to existing baseline summaries, and writes a deterministic
result artifact.

Non-goals:

- Do not promote `chunks_v2` as the canonical graph or claim input.
- Do not rebuild production canonical graph, claim, rule-link, compliance, review, or phase-eval
  artifacts.
- Do not add model scoring or change retrieval ranking.

Scope:

- Add a `chunk-sidecar-consumer-eval` command and Python API.
- Refuse canonical graph/claim output directories for this eval.
- Compare sidecar graph and claim coverage metrics against baseline graph/claim summaries.
- Add focused tests, architecture ownership, output schema docs, current-state docs, and handoff
  closeout.

## Intent Hierarchy

Invariant: the canonical reviewer spine remains the default production contract.

Optimization target: convert sidecar graph/claim previews from manual smoke evidence into a
repeatable fail-closed promotion-readiness artifact.

Acceptable tradeoffs: diagnostic partial runs may pass validation checks while still reporting
reviewer readiness as false; canonical promotion remains blocked until a later packet.

Explicit non-negotiables: sidecar eval must not write to canonical `evidence_graph/` or `claims/`;
it must not weaken existing retrieval, graph, claim, or architecture validation.

Intent lock: this packet creates a promotion-readiness gate only, not promotion itself.

## Owner Surfaces And Placement

- `src/usfs_r1_ea_sources/sidecar_consumer_eval.py` owns the new sidecar consumer eval runtime.
- `src/usfs_r1_ea_sources/cli_derived_registration.py` owns command registration, and
  `src/usfs_r1_ea_sources/cli_sidecar_eval.py` owns sidecar eval command argument adaptation.
- `docs/architecture_contract.toml` owns the new module layer, command group entry, and result
  artifact path.
- `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
  `docs/SESSION_HANDOFF.md` own user-visible contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: accidental canonical mutation. Prevention: the runtime rejects sidecar chunk,
  retrieval, result, graph, or claim paths that point at or inside canonical derived output
  directories. Fail threshold: a test or smoke writes canonical sidecar eval output.
- Weak point: weak comparison semantics. Prevention: compare graph coverage rates, claim coverage
  rates, dangling graph counts, and claim count against baseline summaries. Fail threshold: missing
  baseline summaries or worse sidecar metrics.
- Weak point: architecture drift. Prevention: add an explicit sidecar eval layer and artifact owner,
  then run architecture contract and probe gates. Fail threshold: architecture contract or probe
  fails.
- Weak point: overclaiming promotion. Prevention: docs must keep canonical promotion, rule-link,
  compliance, and phase-eval adoption in future routing. Fail threshold: docs claim reviewer-ready
  canonical adoption from this packet.

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing sidecar, retrieval,
graph, claim, phase-eval, or architecture tests to close this packet.

## Milestone Sequence

Milestone 1: Sidecar graph/claim promotion-readiness eval

- Add the sidecar consumer eval runtime and command.
- Add tests for successful sidecar graph/claim metric comparison and canonical-dir refusal.
- Update architecture contract, output schema docs, current-state, routing, and handoff.
- Outcome label: resolved when focused tests, lint, compile, architecture gates, live smoke,
  parity sweep, and local commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_sidecar_consumer_eval.py tests/test_sidecar_consumer_preview.py tests/test_sidecar_retrieval_eval.py tests/test_evidence_graph.py tests/test_cli.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- Live smoke with ignored f70 corpus read-only and sidecar outputs under `/tmp`.

## Acceptance Criteria

- `chunk-sidecar-consumer-eval` builds or reuses `chunks_v2`, builds sidecar retrieval, graph, and
  claim previews, and writes `chunk_sidecar_consumer_eval_results.json` outside canonical derived
  output directories.
- The result records baseline graph/claim summaries, sidecar graph/claim summaries, metric
  comparisons, and fail-closed checks.
- The command rejects sidecar chunk, retrieval, result, graph, and claim paths that point at or
  inside canonical `chunks/`, `retrieval/`, `evidence_graph/`, or `claims/` directories.
- Focused tests prove both the passing comparison path and canonical-dir refusal path.
- Architecture contract covers the new module, command, and artifact owner.
- Docs and handoff state that canonical graph/claim promotion remains future work.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md` for the new result artifact and command behavior. Update
`docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` with the
resolved packet, verification status, live-smoke boundary, and residual future promotion route.

## Stop Conditions

- Stop if passing the packet requires overwriting canonical graph, claim, rule-link, compliance,
  review, or phase-eval artifacts.
- Stop if comparison gates require lowering existing validation.
- Stop if architecture ownership cannot be represented without a broad layer exception.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified packet slice after implementation, focused verification, architecture
probe, live smoke, closeout parity sweep, and docs/handoff updates pass. Do not stage ignored
`source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  sidecar consumer eval, sidecar preview, sidecar retrieval eval, evidence graph, CLI,
  architecture contract, and architecture quality tests passed.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 513 code files, 17 above 800, no Python or JS/TS import cycles, and no
  source module above the 20 fan-out gate.
- Live smoke artifact path:
  `/tmp/usfs-r1-sidecar-consumer-eval.0SK6sj/consumer_sidecar_eval/chunk_sidecar_consumer_eval_results.json`.
- Gap closeout:
  sidecar retrieval and consumer eval commands now reject sidecar chunk, retrieval, result, graph,
  or claim paths inside canonical derived output directories, with focused regression coverage.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: canonical graph/claim promotion, rule-link/compliance adoption, phase-eval
  binding, and reviewer package adoption remain future work.

## Residual Risks And Next Routing

After this packet, canonical graph/claim promotion still needs an explicit adoption packet. Rule-link,
compliance, phase-eval, and reviewer package adoption remain out of scope until canonical promotion
is approved and evaluated.
