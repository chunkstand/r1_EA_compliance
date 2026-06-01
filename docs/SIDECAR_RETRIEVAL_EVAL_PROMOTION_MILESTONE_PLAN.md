# Sidecar Retrieval Eval Promotion Milestone Plan

Date: 2026-06-01
Status: resolved locally
Plan class: implementation
High-risk implementation: yes
Owner context: `codex/extraction-chunking-retrieval-accuracy` in `/Users/chunkstand/projects/usfs-r1-EA-sources-extraction-chunking-retrieval-accuracy`

## Purpose And Current Evidence

The extraction/chunking accuracy brief identified that baseline `chunks/chunks.jsonl` is a stable spine, but retrieval accuracy needs opt-in atomic chunks, structure-aware fields, parent windows, and evals that prove those fields help before any graph or compliance surface is rewired. The previous sidecar packet added `chunks_v2`; this packet promotes a measurable retrieval comparison gate over that sidecar.

## Goal, Non-Goals, And Scope

Goal: add a bounded `chunk-sidecar-retrieval-eval` command that builds or reuses `chunks_v2`, builds a noncanonical sidecar retrieval index, runs the tracked retrieval eval against sidecar and baseline indexes, and writes a comparison result artifact.

Non-goals: do not replace canonical `chunks/chunks.jsonl`; do not make graph, claim, rule-binding, or compliance commands consume sidecar chunks; do not mutate ignored `source_library/` evidence except in explicit temp smoke paths.

Intent Lock: advance measurement and promotion readiness for sidecar retrieval only. The tempting nearby work, routing reviewer engines or graph artifacts to `chunks_v2`, remains a later packet.

## Intent Hierarchy

Invariant: preserve canonical corpus and baseline retrieval behavior unless an explicit sidecar path is provided.

Optimization target: make the sidecar gate falsifiable with atomic chunk recall, structure hit rate, parent-window coverage, citation correctness, and not-worse-than-baseline metric checks.

Acceptable tradeoffs: sidecar smoke may use `/tmp` artifacts and a narrow eval fixture if it exercises real f70 chunks and writes machine-readable comparison results.

Non-negotiables: no graph/review promotion in this packet, no test weakening, no skipped or relaxed eval assertions to make the sidecar pass, and no production `source_library/` mutation during smoke.

## Owner Surfaces And Placement

Code owners: `src/usfs_r1_ea_sources/sidecar_retrieval_eval.py`, retrieval CLI registration, retrieval index path resolution, and `chunk_layers.py` ID validation.

Config and contracts: `config/chunk_sidecar_retrieval_eval_v1.json`, `docs/architecture_contract.toml`, retrieval tests, and durable docs/handoff.

Generated artifact policy: sidecar eval writes under `source_library/derived/<source_set_id>/retrieval_sidecar_eval/` by default, but full-corpus verification must use `/tmp` paths unless the user explicitly asks to update ignored corpus outputs.

## Weak-Point Prevention

- Owner surface: `chunk_layers.py`. Prevention gate: chunk-layer validation must fail when atomic chunk IDs are not unique. Fail threshold: any duplicate atomic `chunk_id`.
- Owner surface: `retrieval_common.py`. Prevention gate: retrieval eval must infer source-set identity from index metadata for noncanonical sidecar index locations. Fail threshold: sidecar index under `/tmp` cannot be evaluated.
- Owner surface: `config/chunk_sidecar_retrieval_eval_v1.json`. Prevention gate: eval config must require atomic chunk IDs, structure types, citation labels, parent windows, and a hard negative. Fail threshold: sidecar can pass with only source-record recall.
- Owner surface: docs and handoff. Prevention gate: docs must state that sidecar retrieval remains opt-in and not yet promoted into graph or compliance consumers. Fail threshold: docs imply `chunks_v2` is the active graph or reviewer spine.

Anti-test-weakening rule: do not delete, skip, xfail, relax, or narrow existing tests or eval thresholds to make this packet green.

## Milestone Sequence

1. Implement sidecar retrieval eval runtime, CLI command, config, architecture contract entries, and focused tests.
2. Fix sidecar chunk ID uniqueness and noncanonical retrieval index source-set inference.
3. Run focused unit/contract verification.
4. Run full f70 read-only smoke using main checkout `source_library/` as input and `/tmp` for sidecar chunks, sidecar index, and eval results. Outcome label: resolved.
5. Update README, output schemas, current-state, and session handoff with the verified boundary and residual route.
6. Commit the verified implementation and docs as one atomic packet.

## Verification Gates

- `PYTHONPATH=src uv run --extra dev pytest tests/test_sidecar_retrieval_eval.py tests/test_retrieval.py tests/test_retrieval_eval.py tests/test_cli.py tests/test_architecture_contract.py -q`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources chunk-sidecar-retrieval-eval --output-dir /Users/chunkstand/projects/usfs-r1-EA-sources/source_library --source-set-id source-set-f70ea11e04ae3d53 --chunks-v2-dir /tmp/<packet>/chunks_v2 --sidecar-index-dir /tmp/<packet>/retrieval_sidecar --results-dir /tmp/<packet>/results --top-k 10`
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/SIDECAR_RETRIEVAL_EVAL_PROMOTION_MILESTONE_PLAN.md --strict`
- `git diff --check`

## Acceptance Criteria

- Sidecar eval command returns `passed: true` for the f70 smoke with sidecar atomic/structure/parent-window metrics at `1.0`.
- Baseline comparison completes and is retained even when baseline fails sidecar-specific atomic/structure/parent expectations.
- Canonical retrieval index paths are not created when a sidecar `--index-dir` is provided.
- Docs and handoff state the sidecar boundary and next promotion work.

## Documentation And Handoff

Refresh `README.md`, `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` before commit. Do not claim graph, claims, compliance, or reviewer routing promotion.

## Commit Closeout

Commit policy: one local atomic commit after verification and docs closeout. Push policy: do not push unless the user asks.

## Closeout Outcome Record

Outcome label: resolved locally.

Verification recorded: focused pytest/architecture contract pass, ruff pass, strict milestone-plan lint, `git diff --check`, and f70 `/tmp` sidecar retrieval eval smoke with sidecar metrics not worse than baseline.

Forecast hits: duplicate sidecar chunk IDs and noncanonical index source-set inference both surfaced during full-corpus smoke and were fixed in scope.

## Stop Conditions

Stop if sidecar metrics are worse than baseline, source-set identity cannot be proven from sidecar index metadata, duplicate atomic IDs remain, or full-corpus smoke requires mutating tracked/ignored corpus outputs outside `/tmp`.

## Residual Risks And Next Routing

Residual work after this packet is sidecar promotion into graph/claims/compliance read paths, broader eval coverage, and threshold tuning over more forest-plan examples. Those require a new packet because they change downstream consumer contracts.
