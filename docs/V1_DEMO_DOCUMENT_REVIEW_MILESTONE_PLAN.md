# V1 Demo Document Review Milestone Plan

Date: 2026-05-01

## V1 Outcome

The V1 system goal is to produce a credible local demo document review for an Environmental
Assessment package. The demo must show that the system can start from an auditable source library,
use reviewer-ready evidence, evaluate an EA package against configured review criteria, and emit
traceable review outputs that a human reviewer can inspect.

The V1 demo is not a final legal sufficiency determination and is not a claim that the full expanded
190-row source set has completed downstream promotion. V1 is successful when the demo review is
repeatable, evidence-backed, and honest about unresolved items.

## Current Baseline

Already in place:

- The workbook-driven source library is captured for the current 190-row source set.
- The active catalog source set is `source-set-ba8d0feae79501b8`.
- Custer Gallatin forest-plan supporting records are present in the current catalog.
- A Custer Gallatin-focused extraction/retrieval slice exists for the seven required forest-plan
  records.
- `ea-review` can produce deterministic package checklist review outputs from reviewer-ready
  retrieval evidence.
- `compliance-review` can produce a compliance matrix and finding graph from configured rules and
  package evidence.
- `forest-plan-resolve` can resolve Custer Gallatin context through profile data, required
  source-record readiness, plan geography, overlays, and trigger-gated supporting records.
- The component-level forest-plan evaluation work is tracked in
  `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`.

Important boundary:

- The Custer Gallatin forest-plan slice is enough for the forest-plan part of the demo.
- Full-source-set extraction, retrieval, evidence graph, source-claim, rule-claim, coverage, and gold
  promotion artifacts for `source-set-ba8d0feae79501b8` are not currently the default V1 blocker.
- Rebuild full downstream artifacts only if the selected demo path requires full compliance
  promotion evidence.

## Non-Goals

- Do not rebuild the entire downstream corpus unless the selected demo review requires it.
- Do not turn the forest-plan evaluator into the whole V1 scope.
- Do not add East Crazies-specific runtime branches.
- Do not scan raw artifact filenames to decide reviewer behavior.
- Do not claim legal sufficiency or full compliance promotion without current phase/eval evidence.

## Milestone 1: Select The Demo Review Contract

Goal:
Pin down the exact V1 demo document review target before adding more evaluator or compliance
surface area.

Deliverables:

- Selected EA package path and review ID.
- Selected demo mode:
  - `ea-review` checklist demo,
  - `forest-plan-resolve` plus `ea-review` demo, or
  - `forest-plan-resolve` plus `compliance-review` demo.
- Required source-set ID, rule-pack version, and profile ID recorded in docs.
- Definition of "done" for the demo outputs: JSON, Markdown, PDF, finding graph, validation files,
  and reviewer-resolution queue as applicable.
- Explicit list of accepted residual risks for the demo.

Relevant files:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`

Required verification:

```bash
git diff --check
```

Commit boundary:
Commit only the demo contract docs and handoff update.

Stop conditions:

- The package path or demo mode is ambiguous.
- The demo requires outputs from stale source-set artifacts without clearly labeling that boundary.

## Milestone 2: Prove Forest-Plan Context For The Demo Package

Goal:
If the V1 demo uses the East Crazies/Custer Gallatin package, prove the minimum forest-plan evaluator
slice needed for the demo. This is a support milestone, not the entire V1 system.

Deliverables:

- East Crazies fixture or fixed package contract proving profile-driven resolution.
- `scope_status=custer_gallatin` resolved from selected profile names.
- Bridger, Bangtail, and Crazy Mountains Geographic Area resolved.
- Crazy Mountains Backcountry Area resolved.
- Required Custer Gallatin source records present in retrieval readiness.
- FEIS, Biological Assessment, and Biological Opinion routes triggered only from explicit package
  evidence.
- Generic decision labels do not trigger ROD routing without explicit ROD terms.
- Reviewer-ready status remains gated by both package evidence and source-library evidence.

Relevant files:

- `docs/FOREST_PLAN_REVIEW_EVALUATOR_V1.md`
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`
- `config/forest_plan_profiles.json`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `tests/test_forest_plan_resolver.py`
- `tests/test_forest_plan_profiles.py`
- optional `tests/fixtures/forest_plan_evaluator/`

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit boundary:
Commit only fixture, focused resolver/profile tests, and matching docs.

Stop conditions:

- The fixture cannot pass without an East Crazies-specific runtime branch.
- Required readiness fails because the local test source library lacks a profile-required record.
- Reviewer-ready status can pass without both package evidence and source-library evidence.

## Milestone 3: Produce The Demo Review Outputs

Goal:
Run the selected demo review path and produce the actual V1 document review artifacts.

Deliverables:

- Package extraction manifest and chunks.
- Review validation file showing pass/fail status.
- Human-readable review report.
- If using forest-plan context: `forest_plan_context.json`,
  `forest_plan_context_validation.json`, and `forest_plan_context_summary.json`.
- If using compliance review: compliance validation, compliance review JSON, compliance matrix
  JSON/Markdown/PDF, and finding graph nodes/edges.
- Reviewer-resolution items for ambiguous, missing, weak, or contradictory evidence.

Relevant commands:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path <demo-package-path> \
  --output-dir source_library \
  --review-id <demo-review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path <demo-package-path> \
  --output-dir source_library \
  --review-id <demo-review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path <demo-package-path> \
  --output-dir source_library \
  --review-id <demo-review-id>
```

Use only the commands selected in Milestone 1.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_ea_review.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Add `phase-eval` only if the demo review claims phase-level readiness for generated artifacts.

Commit boundary:
Commit code/test/docs changes and any intentionally tracked demo fixtures. Do not stage
`source_library/` outputs unless repository policy is explicitly changed.

Stop conditions:

- Demo outputs depend on stale source-set IDs without disclosure.
- The review report has findings unsupported by package evidence and source-library evidence.
- The selected demo cannot be reproduced from committed config, docs, and commands.

## Milestone 4: Tighten The Demo Report For Human Review

Goal:
Make the demo review understandable to a practitioner without weakening evidence discipline.

Deliverables:

- Report sections that separate supported findings, unresolved items, and non-goals.
- Clear source-record IDs, citation labels, package evidence, and source-library evidence for each
  supported point.
- Forest-plan context shown as review context, not a legal conclusion.
- Reviewer-resolution queue that names the next human action for every unresolved item.
- Plain-language current-state docs explaining exactly what the demo does and does not prove.

Relevant files:

- `src/usfs_r1_ea_sources/ea_review.py`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `README.md`

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_ea_review.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit boundary:
Commit report/output contract changes, focused tests, and docs together.

Stop conditions:

- Output consumers must parse prose to determine readiness.
- Findings hide source-record IDs, trigger evidence, or unresolved evidence gaps.
- The report implies legal sufficiency.

## Milestone 5: Demo Readiness Gate And Handoff

Goal:
Close V1 with a reproducible operator path and a concise readiness statement.

Deliverables:

- Final command transcript or concise run record for the selected demo path.
- Current-state update with review ID, package path, source-set ID, rule-pack/profile versions,
  validation status, and residual risk.
- Handoff that states the next recommended milestone after the demo.
- If promotion is claimed, current `phase-eval` and `compliance-gold-eval` evidence with failed
  checks shown explicitly.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Run the relevant review command and `phase-eval` when the final readiness statement depends on
generated review artifacts.

Commit boundary:
Commit final docs, handoff, and code/test changes after verification. Keep generated
`source_library/` artifacts unstaged unless explicitly approved.

Stop conditions:

- The final state cannot reproduce the demo from documented commands.
- The final state claims reviewer-ready or promotion-ready status without current validation.
- The docs blur demo readiness with full expanded-corpus compliance promotion.

## Deferred Until After V1 Demo

- Full forest-plan plan-component findings beyond what the demo needs.
- Additional Region 1 profile portability beyond minimum profile-path safety checks.
- Full-source-set downstream extraction/retrieval/graph/claim/rule-claim rebuild for
  `source-set-ba8d0feae79501b8`, unless selected demo promotion requires it.
- Expanded human adjudication set beyond the current gold eval seed.
- Embeddings or semantic reranking.

## Milestone Discipline

- Keep one milestone per commit.
- Stage only the verified milestone slice.
- Prefer focused fixtures and reuse-first evidence assembly over broad corpus rebuilds.
- Report verification as command, result, skipped checks, and residual risk.
- Update `docs/SESSION_HANDOFF.md` at the end of substantial implementation sessions.
