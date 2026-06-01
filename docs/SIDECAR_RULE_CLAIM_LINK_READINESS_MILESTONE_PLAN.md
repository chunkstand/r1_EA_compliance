# Sidecar Rule Claim Link Readiness Milestone Plan

Date: 2026-06-01
Status: Resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: extraction/chunking/retrieval accuracy sidecar branch

## Purpose And Current Evidence

The sidecar branch now has validated `chunks_v2`, sidecar retrieval eval, isolated graph/claim
previews, a graph/claim promotion-readiness eval, and guarded graph/claim canonical adoption. The
next downstream risk is proving that rule-claim binding can consume a sidecar claim preview and
write isolated rule-link artifacts without mutating the canonical `rule_claim_links/` lane.

Current evidence:

- `claim-extract --claims-dir` can write reviewer-ready sidecar claim artifacts under
  `claims_sidecar/`.
- Current routing listed rule-link sidecar adoption as the next downstream packet after graph/claim
  canonical adoption.
- `rule-claim-eval` previously assumed canonical `rule_claim_links/<rule_pack>/<version>/` paths.

## Goal, Non-Goals, And Scope

Goal: add an opt-in sidecar rule-claim link preview path that reads sidecar claims, writes
noncanonical rule-link artifacts, and lets `rule-claim-eval` score those artifacts.

Non-goals:

- Do not promote sidecar rule-claim links into canonical `rule_claim_links/`.
- Do not change compliance review, phase-eval, reviewer package, or knowledge-graph consumers.
- Do not mutate ignored production `source_library/` during closeout verification.

Scope:

- Add `rule-claim-link --links-dir` for isolated rule-link preview outputs.
- Allow rule-claim eval to infer source-set and output-root identity from sidecar link summaries.
- Keep sidecar claims path support limited to source-library-derived `claims_sidecar/` previews.
- Update tests, architecture contract, output schema docs, current-state docs, routing, and handoff.

## Intent Hierarchy

Invariant: canonical rule-claim outputs remain the default reviewer contract.

Optimization target: make sidecar claim consumers testable through rule-link and rule-link eval
without requiring canonical mutation.

Acceptable tradeoffs: sidecar links may require explicit `--claims-path` and `--links-dir`; broader
consumer adoption can stay in later packets.

Explicit non-negotiables: custom link outputs must not point at or inside canonical
`rule_claim_links/`, and eval must revalidate the current sidecar artifacts before scoring.

Intent lock: this packet creates a sidecar preview/eval path only, not rule-link promotion or
compliance/phase-eval adoption.

## Owner Surfaces And Placement

- `src/usfs_r1_ea_sources/rule_claim_binding.py` owns sidecar link output selection, canonical-dir
  refusal, summary identity fields, and validation reuse.
- `src/usfs_r1_ea_sources/rule_claim_binding_eval.py` owns sidecar link summary resolution during
  eval.
- `src/usfs_r1_ea_sources/claim_extraction_eval.py` owns the compatible `claims_sidecar/` claim
  eval path inference.
- `src/usfs_r1_ea_sources/cli_derived_registration.py` and `src/usfs_r1_ea_sources/cli_derived.py`
  own the public `--links-dir` argument and dispatch.
- `docs/architecture_contract.toml` owns sidecar rule-link artifact patterns.
- `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
  `docs/SESSION_HANDOFF.md` own durable contract and route truth.

## Risk And Weak-Point Prevention

- Weak point: accidental canonical mutation. Owner surface: `rule_claim_binding.py`. Prevention:
  custom `--links-dir` is rejected when it points at or inside canonical
  `rule_claim_links/<rule_pack>/<version>/`. Fail threshold: a sidecar test creates canonical
  rule-link artifacts.
- Weak point: eval path assumptions. Owner surface: `rule_claim_binding_eval.py`. Prevention:
  `rule-claim-eval` reads source-set and output-root identity from sidecar `summary.json` before
  revalidating. Fail threshold: a sidecar link eval cannot pass on freshly built sidecar links.
- Weak point: unsupported claim path shapes. Owner surface: `claim_extraction_eval.py`.
  Prevention: claim eval accepts `claims_sidecar/` only when it lives under
  `source_library/derived/<source_set_id>/`. Fail threshold: arbitrary claim paths are treated as
  reviewer-ready source-library claims.
- Weak point: architecture drift in the derived CLI dispatcher. Owner surface: `cli_derived.py`.
  Prevention: keep `cli_derived.py` below the 800-line route-doc gate and run architecture
  quality/probe checks. Fail threshold: derived CLI exceeds the file-size gate or architecture
  contracts fail.
- Weak point: scope creep. Owner surface: current routing and output-schema docs. Prevention: docs
  and tests state compliance, phase-eval, reviewer package, and knowledge-graph sidecar adoption
  remain future packets. Fail threshold: this packet writes those downstream artifacts.

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing claim, rule-claim,
phase-eval, sidecar, or architecture tests to close this packet.

## Milestone Sequence

Milestone 1: Sidecar rule-claim link preview and eval

- Add `--links-dir` support and noncanonical output refusal.
- Add sidecar link eval source-set/output-root resolution from summaries.
- Add tests for sidecar claims to sidecar links to sidecar eval, canonical-dir refusal, and CLI
  argument propagation.
- Update architecture contract, output schemas, current-state docs, routing, and handoff.
- Outcome label: resolved when focused tests, lint, compile, architecture gates, CLI smoke, parity
  sweep, and local commit closeout pass.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_rule_claim_binding.py tests/test_rule_claim_binding_validation.py tests/test_rule_claim_binding_runtime.py tests/test_claim_extraction.py tests/test_claim_extraction_eval.py tests/test_cli_derived.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`
- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20 --fail-on-cycles`
- Temp CLI smoke with fixture-backed source library only; do not mutate ignored production
  `source_library/`.

## Acceptance Criteria

- `rule-claim-link --claims-path <claims_sidecar/claims.jsonl> --links-dir <rule_claim_links_sidecar/...>`
  writes link, gap, SQLite, validation, and summary artifacts outside canonical `rule_claim_links/`.
- Sidecar link summaries record canonical and actual link directories plus whether the output is
  canonical.
- `rule-claim-eval --links-path <rule_claim_links_sidecar/.../rule_claim_links.jsonl>` revalidates
  and scores the sidecar links.
- Custom `--links-dir` at or inside canonical rule-claim output directories is rejected.
- Existing canonical rule-claim behavior and eval paths remain backward compatible.
- Docs and handoff state that compliance, phase-eval, reviewer package, and knowledge-graph sidecar
  adoption remain future packets.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/CURRENT_ROUTING.md`, and
`docs/SESSION_HANDOFF.md` with the new sidecar link path, eval behavior, verification status, and
residual downstream adoption route.

## Stop Conditions

- Stop if sidecar rule-link preview requires writing canonical rule-link, compliance, review,
  phase-eval, or knowledge-graph artifacts.
- Stop if eval cannot revalidate sidecar links without weakening rule-claim validation.
- Stop if architecture ownership requires a broad layer exception.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified packet slice after implementation, focused verification, architecture
probe, CLI smoke, closeout parity sweep, and docs/handoff updates pass. Do not stage ignored
`source_library/`.

## Closeout Outcome Record

Status: resolved locally.

- Focused test result:
  rule-claim binding, validation, runtime, claim extraction, claim extraction eval, CLI derived,
  architecture contract, and architecture quality tests passed.
- Lint result: source and test Ruff check passed.
- Compile result: source compileall passed.
- Plan lint result: strict milestone-plan lint passed.
- Architecture probe result: 515 code files, 17 above 800, no Python or JS/TS import cycles, and no
  source module above the 20 fan-out gate.
- CLI smoke result:
  fixture-backed source library wrote sidecar claims, sidecar rule-claim links, and sidecar
  rule-claim eval artifacts under `/tmp/usfs-r1-sidecar-rule-claim.1d_jiwfh/` without creating
  canonical rule-link outputs.
- Docs freshness check: whitespace check and closeout parity sweep passed.
- Commit identifier: the Git commit containing this closeout record.
- Residual risk: compliance review, phase-eval, reviewer package, and knowledge-graph adoption
  remain future work.

## Residual Risks And Next Routing

After this packet, sidecar claim previews can feed sidecar rule-claim link previews and direct
rule-link eval. Compliance review, phase-eval, reviewer package, and knowledge-graph consumers still
need separate bounded packets before they can depend on sidecar-backed rule links.
