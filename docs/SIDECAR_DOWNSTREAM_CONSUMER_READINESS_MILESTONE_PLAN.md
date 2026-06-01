# Sidecar Downstream Consumer Readiness Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The extraction/chunking/retrieval accuracy branch already has opt-in `chunks_v2` layers and a
sidecar retrieval eval promotion gate. The remaining accuracy risk is downstream consumer
readiness: graph and claim builders still default to the canonical `chunks/` and `retrieval/`
spines, so a sidecar retrieval win cannot be inspected by the next consumer layer without either
copying files into canonical locations or broadening promotion scope.

Current evidence:

- `chunk-layer-build` writes validated `chunks_v2` atomic chunks, structural chunks, and parent
  windows without replacing `chunks/chunks.jsonl`.
- `retrieval-build --index-dir` writes validated sidecar retrieval indexes and summaries outside
  canonical `retrieval/`.
- `chunk-sidecar-retrieval-eval` proves sidecar retrieval metrics without graph, claim, rule-link,
  review, compliance, or knowledge-graph mutation.

## Goal, Non-Goals, And Scope

Goal: allow `evidence-graph-build` and `claim-extract` to consume explicit sidecar chunk and
retrieval paths and write isolated preview artifacts, while preserving canonical defaults.

Non-goals:

- Do not promote `chunks_v2` as the active canonical chunk spine.
- Do not rebuild canonical graph, claim, rule-link, review, compliance, or knowledge-graph outputs.
- Do not add model-generated legal conclusions, hosted services, or new retrieval scoring logic.

Scope:

- Add optional CLI/Python arguments for sidecar chunk, retrieval validation, retrieval summary, and
  isolated graph/claim output directories.
- Keep existing default command behavior byte-path compatible for canonical runs.
- Add focused tests proving sidecar preview outputs do not create canonical graph/claim outputs.
- Update architecture ownership and durable docs for the new sidecar preview surface.

## Intent Hierarchy

Invariant: canonical `chunks/`, `retrieval/`, `evidence_graph/`, and `claims/` defaults remain the
production contract unless a later promotion packet changes them.

Optimization target: make sidecar downstream inspection explicit and reproducible through command
arguments, focused tests, and architecture-owned artifact paths.

Acceptable tradeoffs: preview commands may require explicit sidecar path arguments and may stay
diagnostic-only even when sidecar retrieval metrics are stronger than baseline.

Explicit non-negotiables: no canonical graph or claim output is written during sidecar preview
tests; no validation gate is relaxed; no downstream promotion is implied.

Intent lock: this packet advances sidecar consumer preview readiness only. It does not authorize
canonical graph or claim promotion from `chunks_v2`.

## Owner Surfaces And Placement

- `src/usfs_r1_ea_sources/evidence_graph.py` owns graph preview path resolution and validation.
- `src/usfs_r1_ea_sources/claim_extraction.py` owns claim preview path resolution and validation.
- `src/usfs_r1_ea_sources/cli_derived_registration.py` and
  `src/usfs_r1_ea_sources/cli_derived.py` own command arguments and dispatch.
- `docs/architecture_contract.toml` owns sidecar graph and claim artifact path patterns.
- `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
  `docs/SESSION_HANDOFF.md` own user-visible contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: accidental canonical mutation. Prevention: require explicit `--graph-dir` or
  `--claims-dir` for isolated previews and assert canonical output paths are absent in tests. Fail
  threshold: any preview test creates canonical graph or claim artifacts.
- Weak point: sidecar retrieval/chunk identity drift. Prevention: pass sidecar chunk, retrieval
  validation, and retrieval summary paths into existing validation checks instead of bypassing them.
  Fail threshold: validation passes without the explicit sidecar retrieval summary/index binding.
- Weak point: undocumented architecture ownership. Prevention: add sidecar artifact patterns to the
  architecture contract and run architecture contract plus architecture quality gates. Fail
  threshold: architecture contract or architecture probe fails.
- Weak point: scope creep into promotion. Prevention: current-state and handoff boundaries must
  state that rule-link, compliance, phase-eval, and production `source_library` mutation remain
  future work. Fail threshold: docs claim canonical promotion or reviewer readiness beyond preview.

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing retrieval, graph,
claim, phase-eval, or architecture tests to close this packet. New tests must add sidecar preview
coverage without reducing canonical-path coverage.

## Milestone Sequence

Milestone 1: Sidecar consumer preview paths

- Add optional sidecar path arguments to graph and claim builder APIs.
- Wire matching CLI flags into `evidence-graph-build` and `claim-extract`.
- Add focused unit coverage for sidecar graph and claim previews.
- Update architecture contract and durable docs.
- Outcome label: resolved when focused tests, architecture gates, docs parity, live smoke, and local
  commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_sidecar_consumer_preview.py tests/test_evidence_graph.py tests/test_cli.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- Live smoke with ignored f70 corpus read-only and sidecar outputs under `/tmp`.

## Acceptance Criteria

- `evidence-graph-build` accepts `--chunks-path`, `--retrieval-validation-path`,
  `--retrieval-summary-path`, and `--graph-dir`.
- `claim-extract` accepts `--chunks-path`, `--retrieval-validation-path`,
  `--retrieval-summary-path`, and `--claims-dir`.
- Sidecar graph preview writes validation, summary, node, edge, and SQLite artifacts to the explicit
  preview directory and does not create canonical `evidence_graph/` artifacts.
- Sidecar claim preview writes validation, summary, claim, entity, node, edge, and SQLite artifacts
  to the explicit preview directory and does not create canonical `claims/` artifacts.
- Architecture contract tests recognize sidecar graph and claim output ownership.
- Current-state and handoff docs separate packet-local preview readiness from future promotion.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md` for sidecar consumer arguments and read/write paths. Update
`docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` with the
resolved packet, verification status, live-smoke boundary, and residual future promotion route.

## Stop Conditions

- Stop if canonical graph, claim, rule-link, review, compliance, or knowledge-graph artifacts must
  be rewritten to pass the packet.
- Stop if validation requires relaxing existing retrieval, graph, or claim checks.
- Stop if architecture contract changes would assign sidecar artifacts to a different owner layer
  than their canonical consumer.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

This milestone follows repo commit discipline. Stage only the verified packet slice after
implementation, focused verification, architecture probe, live smoke, closeout parity sweep, and
docs/handoff updates pass. Do not stage ignored `source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  focused sidecar consumer, evidence graph, CLI, architecture contract, and architecture quality
  tests passed 50/50.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 510 code files, 17 above 800, no Python or JS/TS import cycles, and no
  source module above the 20 fan-out gate.
- Live smoke artifact paths:
  `/tmp/usfs-r1-sidecar-consumer.PnUBBe/retrieval_sidecar/summary.json`,
  `/tmp/usfs-r1-sidecar-consumer.PnUBBe/evidence_graph_sidecar/summary.json`, and
  `/tmp/usfs-r1-sidecar-consumer.PnUBBe/claims_sidecar/summary.json`.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: canonical graph/claim promotion, rule-link/compliance adoption, and phase-eval
  binding remain future work.

## Residual Risks And Next Routing

After this packet, a later promotion milestone must still define downstream direct eval thresholds
before `chunks_v2` can become the canonical graph or claim input. Rule-link, compliance, phase-eval,
and reviewer package adoption remain out of scope until that promotion packet exists.
