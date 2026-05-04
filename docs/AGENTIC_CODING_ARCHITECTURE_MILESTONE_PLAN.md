# Agentic Coding Architecture Continuous Milestone Plan

Date: 2026-05-04

This plan turns `docs/AGENTIC_CODING_ARCHITECTURE_RESEARCH.md` into a continuous implementation
run for this repository. Once the user says to proceed, the plan should be executed start to finish
in one Codex turn unless a stop condition is hit. The milestone labels below are checkpoint commits,
not separate conversations or handoffs.

The plan is organized around four review lenses:

- Simon Brown: architecture legibility.
- Neal Ford, Rebecca Parsons, and Patrick Kua: evolutionary architecture and fitness functions.
- Titus Winters and Google Engineering Practices: code health over time.
- Adam Tornhill: hotspot-driven code review and refactoring.

The goal is not a broad rewrite. The goal is to make the existing workbook-driven, artifact-first,
eval-gated system easier for humans and coding agents to understand, change, test, and govern.

## Continuous Execution Model

Run this as a single continuous architecture hardening session:

- Start only after establishing a clean or explicitly accepted baseline.
- Execute milestones in order without returning to the user between milestones.
- Treat each milestone as an internal checkpoint: implement, verify, commit the verified slice, then
  continue to the next milestone in the same turn.
- Do not batch all changes into one large commit. Atomic checkpoint commits keep rollback,
  review, and blame usable even though the run is continuous.
- Push only if the user explicitly asks for push or publish.
- If a stop condition is hit, stop immediately, preserve the worktree, and write a concise handoff
  explaining the completed checkpoints, failed command, and next safe action.

Preferred task packet for the run:

```text
Goal: execute the architecture hardening sequence start to finish in one Codex turn.
Non-goals: corpus regeneration, network download scaling, behavior migrations outside the listed
  architecture scope, and unrelated cleanup.
Relevant files or surfaces: docs architecture artifacts, architecture tests, rule-pack ownership,
  CLI registration, selected hotspot modules, ADRs, and milestone closeout docs.
Required eval signal: architecture gate passes with no hidden exceptions; focused behavior tests
  pass after each code-moving checkpoint.
Required tests: each milestone-specific verification block below, plus the final closeout block.
Commit/push policy: commit each verified milestone slice; do not push unless asked.
Stop conditions: unrelated dirty baseline, generated-corpus requirement, failing verification,
  unclear behavior migration, or a dependency violation that requires a design decision.
```

## Current Boundary

- Preserve the workbook contract, source-row identity, artifact hashes, citation labels, and
  generated evidence surfaces described in `AGENTS.md`, `README.md`, `DOWNLOADER_RULES.md`, and
  `docs/CURRENT_SYSTEM_STATE.md`.
- Preserve public CLI command names and generated artifact contracts unless a milestone explicitly
  defines a migration.
- Keep `source_library/` ignored and treat it as generated local evidence unless repository policy
  changes.
- Keep domain knowledge in workbook rows, catalog metadata, rule packs, eval fixtures, generated
  ledgers, and reports rather than hidden runtime branches.
- Stage and commit only the verified milestone slice. Do not stage unrelated dirty worktree changes.
- Continue automatically after each successful checkpoint commit until the full sequence is done.

## Readiness Notes

These notes are part of the implementation contract for the first run:

- The current known source-level import cycle is
  `compliance_review -> rule_claim_binding -> compliance_review`. Milestone 2 may record this as a
  temporary contract exception only if it names the owner and removal milestone. Milestone 3 must
  remove the exception by moving shared rule-pack ownership to `rule_packs.py`.
- The architecture contract should be `docs/architecture_contract.toml` and should be parsed with
  Python's standard-library `tomllib` in `tests/test_architecture_contract.py`. Do not add a YAML
  parser dependency solely for this gate.
- `tests/test_cli.py` does not exist yet. Milestone 4 owns creating it as the parser smoke-test
  surface.
- Any placeholder command in Milestone 5 must be replaced by concrete focused tests in the hotspot
  report before the milestone can be closed.

## Four-Lens Alignment

| Lens | What It Asks | Local Application |
| --- | --- | --- |
| Simon Brown | Can reviewers and agents see the system shape at useful levels of detail? | Add a compact architecture map and machine-readable contract for workflow layers, generated artifacts, and ownership boundaries. |
| Ford, Parsons, and Kua | Can architecture rules evolve through automated fitness functions? | Add import-cycle and dependency-boundary tests beside existing pytest, ruff, compileall, phase-eval, and artifact validation gates. |
| Winters and Google | Will this code still be reviewable after many changes? | Split large command and orchestration surfaces only where it reduces future review risk while preserving behavior. |
| Tornhill | Which code should change first based on complexity and change history? | Use size, churn, and eval/test-failure history to rank hotspots before refactoring large modules. |

## Milestone 0: Settle The Baseline

Goal: start architecture work from a clean, known baseline.

Non-goals:

- Do not refactor architecture in the same commit as unrelated applicability, corpus, downloader,
  or review-engine work.
- Do not regenerate `source_library/` or run large network workflows.

Work:

- Run `git status -sb` and identify any existing dirty files.
- If dirty work exists, either finish and commit that lane first, or park it outside the
  architecture milestone.
- Re-check `docs/SESSION_HANDOFF.md` and `docs/CURRENT_SYSTEM_STATE.md` before making readiness or
  corpus-state claims.

Required verification:

```bash
git status -sb
git diff --check
```

Stop conditions:

- The worktree contains unrelated dirty code that overlaps architecture targets.
- A generated-corpus operation would be required to proceed.
- A clean architecture baseline cannot be established without deciding ownership of unrelated work.

Checkpoint action:

- If the baseline is clean or explicitly accepted, continue immediately to Milestone 1.
- If it is not clean, stop and write a handoff rather than mixing unrelated work into the
  architecture run.

## Milestone 1: Add The Architecture Map

Primary lens: Simon Brown.

Goal: make the pipeline architecture explicit, searchable, and agent-legible.

Work:

- Add `docs/ARCHITECTURE.md` with a C4-style map for the local CLI system:
  workbook/config, capture, catalog, extraction, retrieval, evidence graph, claims, rule packs,
  applicability, EA review, compliance review, eval, and CLI entrypoints.
- Add `docs/architecture_contract.toml` with workflow layers, allowed import direction, owned
  artifact surfaces, and current public command groups.
- Add a short ADR under `docs/adr/` explaining why architecture is enforced through small fitness
  checks rather than broad rewrites.

Required verification:

```bash
git diff --check
```

Done when:

- A future agent can inspect the architecture map and contract before editing code.
- The docs identify which module family owns each generated artifact surface.

Checkpoint action:

- Commit the docs-only architecture map slice, then continue immediately to Milestone 2.

## Milestone 2: Add The First Architecture Fitness Gate

Primary lens: Ford, Parsons, and Kua.

Goal: turn architecture intent into an automated test.

Work:

- Add `tests/test_architecture_contract.py`.
- Parse source imports with Python AST rather than string matching.
- Fail on new source-level import cycles.
- Parse `docs/architecture_contract.toml` with `tomllib` rather than adding a new parser
  dependency.
- Fail on direct dependency violations against `docs/architecture_contract.toml`.
- If the current baseline has a known violation, record the exact temporary exception in the
  contract with an owner and removal milestone instead of hiding it in test code. The only expected
  exception at the start of this run is the `compliance_review -> rule_claim_binding ->
  compliance_review` cycle. Discovery of additional source cycles is a stop condition unless the
  user explicitly accepts broadening the architecture run.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
git diff --check
```

Done when:

- The architecture gate passes on the current baseline.
- New cycles or forbidden downstream imports fail deterministically.
- Any temporary exception is visible, named, and scheduled for removal.

Checkpoint action:

- Commit the architecture-contract and test slice, then continue immediately to Milestone 3.

## Milestone 3: Split Rule-Pack Ownership From Compliance Review

Primary lenses: Simon Brown; Ford, Parsons, and Kua.

Goal: align dependency direction with the domain model by moving shared rule-pack concerns upstream
of compliance review.

Work:

- Add `src/usfs_r1_ea_sources/rule_packs.py`.
- Move shared rule-pack constants, schema loading, `load_rule_pack`, `validate_rule_pack`, and
  helper validation out of `compliance_review.py`.
- Update rule binding, applicability rule-pack generation, compliance review, eval modules, and
  tests to import shared rule-pack behavior from `rule_packs.py`.
- Keep public CLI and generated artifact behavior stable. If a short compatibility re-export from
  `compliance_review.py` is needed for external import stability, it must not be used by upstream
  internal modules and must be documented in the architecture contract.
- Remove the temporary architecture exception for the rule-pack/compliance-review dependency if it
  was needed in Milestone 2.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev pytest tests/test_rule_claim_binding.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability.py tests/test_applicability_decisions.py tests/test_applicability_retrieval.py
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
git diff --check
```

Done when:

- Rule binding no longer imports downstream compliance-review behavior for shared rule-pack logic.
- The architecture fitness gate has no exception for this boundary.
- Public compliance-review and applicability outputs remain unchanged except for expected
  provenance metadata if explicitly updated.

Checkpoint action:

- Commit the rule-pack ownership split, then continue immediately to Milestone 4.

## Milestone 4: Group CLI Registration By Workflow Lane

Primary lens: Titus Winters and Google Engineering Practices.

Goal: keep the CLI as a stable public interface while reducing review friction in `cli.py`.

Work:

- Keep `src/usfs_r1_ea_sources/cli.py` as the public entrypoint.
- Move command registration and dispatch helpers into workflow-lane modules such as capture,
  catalog/extraction, applicability, review, compliance, and eval.
- Add `tests/test_cli.py` with parser smoke tests for command existence and critical option
  propagation.
- Include a regression test for options that gate review authority, including
  `--allow-base-rule-pack-review` if that option remains part of the command surface.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
git diff --check
```

Done when:

- Existing commands, option names, and dispatch behavior are preserved.
- Future workflow changes can edit a narrow CLI module rather than the whole command surface.

Checkpoint action:

- Commit the CLI grouping slice, then continue immediately to Milestone 5.

## Milestone 5: Rank Hotspots And Plan The First Reduction

Primary lens: Adam Tornhill.

Goal: use behavioral evidence to choose the next refactoring target and define a bounded,
test-backed reduction plan.

Work:

- Generate a hotspot report that combines source file size, recent git churn, test/eval failures,
  and reviewer pain points.
- Start with likely candidates only as hypotheses: `compliance_review.py`,
  `forest_plan_components.py`, `evidence_graph.py`, `applicability_validation.py`,
  `claim_extraction.py`, `extract.py`, and `cli.py`.
- Select one module family for a bounded split plan.
- Define behavior-preserving tests before moving code.
- Do not move hotspot code in this milestone unless the selected split is small enough to complete,
  verify, and commit without expanding scope. If it is not that small, the output is the hotspot
  report plus the concrete next-milestone test list.

Required verification:

```bash
git log --name-only --since="90 days ago" -- src tests
wc -l src/usfs_r1_ea_sources/*.py
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
git diff --check
```

Done when:

- The next refactor target is justified by size plus change evidence, not preference.
- The milestone output includes a small split plan and focused verification list.
- Any code movement performed in this milestone has concrete focused tests named in the hotspot
  report and those tests have passed.

Checkpoint action:

- Commit the hotspot report and selected split plan, then continue immediately to Milestone 6.

## Milestone 6: Codify Architecture Decisions And Safety Boundaries

Primary lenses: Simon Brown; Winters and Google.

Goal: make important review decisions durable and easy to enforce later.

Work:

- Add ADRs for:
  - applicability-before-compliance review;
  - rule-pack ownership outside compliance review;
  - untrusted source content as evidence data, not privileged instructions;
  - architecture fitness gates as required milestone checks.
- Link ADRs from `docs/ARCHITECTURE.md`, `docs/AGENTIC_CODING_ARCHITECTURE_RESEARCH.md`, and
  `docs/SESSION_HANDOFF.md` when they become operationally relevant.

Required verification:

```bash
git diff --check
```

Done when:

- Future code-review discussions can point to durable decisions instead of reconstructing context
  from chat history.

Checkpoint action:

- Commit the ADR slice, then continue immediately to Milestone 7.

## Milestone 7: Make Architecture Gates Part Of Milestone Closeout

Primary lenses: Ford, Parsons, Kua; Winters and Google.

Goal: include architecture checks in normal completion criteria.

Work:

- Add architecture-gate commands to the relevant repo docs once the tests exist.
- Update milestone plans so architecture checks are required for module-boundary, CLI,
  review-engine, applicability, and compliance changes.
- Keep docs-only changes lightweight: do not claim corpus or downstream readiness unless verified
  from manifests, catalog, SQLite, or eval artifacts.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

Done when:

- Architecture fitness checks are part of the standard review vocabulary for future milestones.
- `AGENTS.md`, `README.md`, and active milestone plans point future module-boundary, CLI,
  review-engine, applicability, and compliance changes at
  `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py`.

Checkpoint action:

- Commit the closeout-docs slice, then run the final continuous-run closeout below.

## Continuous Start-To-Finish Run

When the user says to proceed, run the full sequence in this order inside one turn:

1. Establish the baseline. Stop only if unrelated dirty work cannot be safely isolated.
2. Implement Milestone 1, verify it, commit it, and continue.
3. Implement Milestone 2, verify it, commit it, and continue.
4. Implement Milestone 3, verify it, commit it, and continue.
5. Implement Milestone 4, verify it, commit it, and continue.
6. Implement Milestone 5, verify it, commit it, and continue.
7. Implement Milestone 6, verify it, commit it, and continue.
8. Implement Milestone 7, verify it, commit it, and run final closeout.

Do not ask for approval between successful milestones. The only normal pauses are failed
verification, unclear ownership of unrelated dirty work, or a design decision that would expand the
scope beyond this plan.

Final closeout:

```bash
git status -sb
git log --oneline --max-count=12
git diff --check
```

Report the checkpoint commits, verification results, skipped checks, and residual risk. If tests
were skipped because a milestone was docs-only, say that explicitly.

## Review Checklist

Use this checklist when reviewing future architecture milestones:

- Does this change preserve workbook row identity and generated artifact contracts?
- Does this change keep source evidence and model/agent instructions separated?
- Does this change reduce architecture ambiguity for future agents?
- Does an automated test or eval now enforce the intended boundary?
- Is any domain knowledge represented as data, config, rule pack, fixture, or report rather than
  hidden code?
- Is the changed surface small enough for a focused review?
- If a large module is split, was it selected because it is a measured hotspot?
