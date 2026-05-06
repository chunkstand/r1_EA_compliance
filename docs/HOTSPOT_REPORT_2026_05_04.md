# Hotspot Report: Architecture Hardening Sequence

Date: 2026-05-04

This report ranked the next refactoring target using size, recent churn, documented test/eval pain,
and reviewer risk. The first bounded split has now moved compliance matrix and PDF rendering into
`src/usfs_r1_ea_sources/compliance_outputs.py` without changing output artifact contracts.

## Evidence Commands

```bash
git log --name-only --since="90 days ago" -- src tests
wc -l src/usfs_r1_ea_sources/*.py
rg -n "failed|gap|hotspot|pain|large|compliance_review.py|forest_plan_components.py|applicability_validation.py|cli.py|phase-eval --review-id" docs/SESSION_HANDOFF.md docs/CURRENT_SYSTEM_STATE.md docs/AGENTIC_CODING_ARCHITECTURE_RESEARCH.md
```

## Size And Churn Signals

Largest source files after the CLI split and before the compliance-output split:

| Module | Lines | Recent Churn Signal | Notes |
| --- | ---: | ---: | --- |
| `forest_plan_components.py` | 3,302 | 10 commits | Largest module; prior component-resolution misses were closed by resolver/component evidence fixes. |
| `compliance_review.py` | 3,262 | 16 commits | Central reviewer-ready gate; still owns review orchestration, matrix rendering, PDF rendering, validation, eval fixture loading, and graph output. |
| `evidence_graph.py` | 2,548 | 16 commits | Large graph builder/validator; important but currently has fewer active architectural changes queued. |
| `applicability_validation.py` | 2,490 | 3 commits in top churn output, more in applicability sequence history | Validation-heavy and important, but recent Milestone 9 pass is already strongly gated. |
| `extract.py` | 2,156 | 4 commits | Important parser surface, less active than review/compliance lanes. |
| `claim_extraction.py` | 2,126 | 5 test-file churn around claims | Stable enough to defer. |
| `cli.py` | small after Milestone 4 | 39 historical commits | Already reduced in this architecture sequence into lane modules. |

The recent churn command ranked `cli.py`, `tests/test_compliance_review.py`,
`evidence_graph.py`, and `compliance_review.py` highest among source/test paths. The CLI risk has
already been reduced by Milestone 4. `tests/test_compliance_review.py` remains highly active
because compliance behavior is the promoted review gate.

## Reviewer Pain Signals

Current docs and handoffs point to these pain categories:

- Compliance review is the central gate for generated applicability rule packs, base-pack
  diagnostic behavior, non-applicable authority linkage, matrices, PDF artifacts, finding graphs,
  coverage checks, compliance eval, and gold eval promotion readiness.
- `phase-eval --review-id v1-cg-ecid-compliance-review` currently fails closed on missing ignored
  applicability artifacts, which is expected but keeps compliance/review readiness logic central to
  operator interpretation.
- Prior V1 gate repairs and applicability milestones repeatedly touched compliance-review behavior:
  base-rule-pack gating, conditional applicability, section routing, generated-pack validation, and
  promotion readiness.
- `forest_plan_components.py` is large, but its current promoted component eval passes and its
  earlier reviewer-resolution queue is closed.

## Selected Next Target

Selected target: `compliance_review.py`.

Reason: it combines high size, high recent churn, a highly active test surface, and central
promotion/readiness risk. It also has a bounded extraction opportunity that does not change public
CLI behavior or generated artifact contracts.

## Bounded Split Plan

Implemented first refactor: move compliance matrix and report rendering helpers from
`compliance_review.py` into `src/usfs_r1_ea_sources/compliance_outputs.py`.

Initial ownership for the new module:

- `_compliance_matrix`
- `_matrix_row`
- `_compact_evidence`
- `_finding_source_record_ids`
- `_finding_source_document_roles`
- `_matrix_failure_category`
- `_matrix_markdown`
- `_write_compliance_matrix_pdf`
- PDF pagination, escaping, and object-writing helpers
- Markdown/PDF cell helpers used only by matrix/report rendering

Non-goals for that split:

- Do not change compliance finding selection, validation, generated-rule-pack gating, rule-claim
  binding, forest-plan component evaluation, or eval case scoring.
- Do not rename output files or alter compliance matrix JSON/Markdown/PDF schema.
- Do not stage generated `source_library/` artifacts.

Focused verification for the split:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
git diff --check
```

Optional live artifact check, only if the ignored review package artifacts are present and the next
milestone explicitly allows local generated-output rewrites:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --allow-base-rule-pack-review \
  --docling-timeout-seconds 180
```

## Stop Conditions For The Next Split

- Matrix/PDF output changes beyond ordering-preserving helper relocation.
- Any compliance validation, generated-pack gate, or reviewer-ready status change without an
  explicit test and milestone decision.
- New architecture-contract exception required to make the split pass.
- Need to rewrite ignored generated corpus/review artifacts without explicit approval.

## 2026-05-06 Sequence 0 Baseline And Contract Lock

This follow-up pass locks the next hotspot-reduction sequence after the completed
`compliance_outputs.py` split. It does not move code or change generated artifact contracts.

Current line-count baseline:

| Surface | Lines | Sequence 0 interpretation |
| --- | ---: | --- |
| `src/usfs_r1_ea_sources/compliance_review.py` | 3,575 | Still the first refactor target. |
| `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py` | 3,391 | Defer until compliance review risk is reduced. |
| `src/usfs_r1_ea_sources/forest_plan_components.py` | 3,302 | Defer; promoted component eval is currently green. |
| `src/usfs_r1_ea_sources/ea_consistency_decision_support.py` | 3,090 | Defer; decision-support gate is newly closed. |
| `viewer/nepa-3d/app.js` | 2,202 | Defer; viewer work is outside this compliance hotspot sequence. |
| `src/usfs_r1_ea_sources/compliance_outputs.py` | 1,019 | Existing rendering split remains the model for narrow ownership. |

Sequence 1 target:

Create `src/usfs_r1_ea_sources/compliance_inputs.py` and move only compliance-review input and
identity/gate-context helpers out of `compliance_review.py`. The intended ownership is path and
artifact loading for generated applicability rule packs, generated-pack validation, applicability
validation, non-applicable authority artifacts, search coverage artifacts, package manifest/chunk
hash checks, optional artifact-path resolution, and small JSON/JSONL read helpers needed only by
that input boundary.

Sequence 1 non-goals:

- Do not change finding selection, compliance status decisions, generated rule-pack semantics,
  Forest Plan component evaluation, matrix/PDF output, finding graph output, eval scoring, CLI flags,
  or generated artifact schemas.
- Do not move renderer code already owned by `compliance_outputs.py`.
- Do not stage ignored `source_library/` outputs or root-level manual East Crazies draft exports.

Sequence 1 required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Sequence 0 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py`: `55 passed`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py`:
  `11 passed`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `git diff --check`: passed

Sequence 0 worktree note: unrelated untracked root-level East Crazies manual draft exports and
`docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf` were present at baseline and intentionally
left untouched.

## 2026-05-06 Sequence 1 Compliance Input Split

Sequence 1 creates `src/usfs_r1_ea_sources/compliance_inputs.py` and moves the compliance-review
input and identity/gate-context helpers out of `compliance_review.py`. The split owns generated
applicability rule-pack gate loading, generated-pack validation checks, applicability validation
and non-applicable/search-coverage artifact loading, optional artifact-path resolution, package
manifest/chunk hash checks, and JSON/JSONL helpers used by that input boundary.

Current post-split source line counts:

| Surface | Lines | Sequence 1 interpretation |
| --- | ---: | --- |
| `src/usfs_r1_ea_sources/compliance_review.py` | 3,060 | Review orchestration remains large, but no longer owns the input gate helper set. |
| `src/usfs_r1_ea_sources/compliance_inputs.py` | 561 | New narrow owner for generated applicability/compliance input artifacts and gate context. |

Sequence 1 preserves the existing generated artifact contracts: no finding selection, compliance
status decision, generated rule-pack semantic, matrix/PDF output, finding graph output, eval scoring,
CLI flag, or schema behavior is intentionally changed.

Sequence 1 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py`: `55 passed`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py`:
  `11 passed`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `git diff --check`: passed

Sequence 2 target:

Extract compliance validation/report assembly helpers only after Sequence 1 verification is green.
Keep the same boundary rule: one ownership slice, no output schema change, and no downstream
compliance-review execution unless explicitly requested.

## 2026-05-06 Sequence 2 Compliance Validation Split

Sequence 2 creates `src/usfs_r1_ea_sources/compliance_validation.py` and moves compliance validation
and review-summary assembly helpers out of `compliance_review.py`. The split owns validation
constants, compliance validation report checks, reviewer-ready summary assembly, forest-plan summary
projection for compliance outputs, validation check-name helpers, and finding-graph ID helpers used
by validation and report assembly.

Current post-split source line counts:

| Surface | Lines | Sequence 2 interpretation |
| --- | ---: | --- |
| `src/usfs_r1_ea_sources/compliance_review.py` | 2,329 | Review orchestration, finding construction, graph construction, authority integration, eval, and file writes remain. |
| `src/usfs_r1_ea_sources/compliance_validation.py` | 762 | New narrow owner for compliance validation checks and review-summary assembly. |
| `src/usfs_r1_ea_sources/compliance_inputs.py` | 561 | Sequence 1 input/gate owner remains unchanged. |

Sequence 2 preserves the existing generated artifact contracts: no compliance finding construction,
status decision, generated rule-pack semantic, matrix/PDF output, finding graph output, eval scoring,
CLI flag, or schema behavior is intentionally changed.

Sequence 2 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py`: `55 passed`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py`:
  `11 passed`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `git diff --check`: passed

Sequence 3 target:

Extract authority-integration artifact assembly for authority provenance, non-applicable appendix,
reviewer-resolution report, and deterministic litigation-risk summary. Keep the same boundary rule:
one ownership slice, no output schema change, and no downstream compliance-review execution unless
explicitly requested.
