# Project SOW Operationalization Acceptance Matrix

Date: 2026-05-07

This matrix is the tracked milestone-closeout map for
`docs/PROJECT_SOW_OPERATIONALIZATION_MILESTONE_PLAN.md`. It records how each operationalization
sequence satisfies its acceptance criteria and which verification surfaces prove the claim. It is a
Project SOW planning-lane artifact only; it does not create applicability decisions, generated rule
packs, compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions.

## Acceptance Matrix

| Sequence | Acceptance criteria | Verification evidence | Status |
| --- | --- | --- | --- |
| Sequence 1: Intake schema, template, and validation-only command | Minimal template and East Crazies intake validate without writing package outputs; invalid nested intake rows fail closed. | `tests/test_project_sow_package.py`; `project-sow-operational-gate` validation-only targets for template and proving intakes. | Met |
| Sequence 2: Intake authoring assistant for proposed actions | Drafts preserve source path/hash and remain unreviewed until reviewer confirmation clears uncertainty flags. | `tests/test_project_sow_package.py` draft-generation, ambiguity, unexpected-failure, and reviewer-confirmed replay tests. | Met |
| Sequence 3: Multi-project calibration and eval harness | East Crazies, Red Rock Ridge, and Silver Creek run in one proving eval with `0` system misses and `0` intake omissions. | `project-sow-eval`; `project-sow-operational-gate` proving eval summary. | Met |
| Sequence 4: Contract-ready resource SOW content | Selected scopes carry assumptions, dependencies, required/optional deliverables, acceptance criteria, reviewer role, timing, and signoff fields; optional deliverables do not satisfy required-deliverable gates. | `tests/test_project_sow_package.py`; `project-sow-eval` contract-readiness metrics. | Met |
| Sequence 5: Reviewer adjudication loop | East Crazies worklist exports `37` adjudication items; stale, pending, invalid, duplicated, missing, or identity-tampered rows fail; completed replay writes adjudicated intake metadata. | `tests/test_project_sow_package.py` adjudication-template/eval/apply tests; handoff verification in `docs/SESSION_HANDOFF.md`. | Met |
| Sequence 6: Downstream EA package assembly handoff | Handoff derives from canonical package JSON, keeps future artifacts as not-required-now checklist slots, emits `27` East Crazies slots, and fails malformed handoff rules before writing outputs. | `tests/test_project_sow_package.py`; `project-sow-operational-gate` EA handoff smoke. | Met |
| Sequence 7: Operational gate and release closeout | Local-only gate validates all proving intakes, runs proving eval, verifies package/rendering and handoff smoke, checks durable docs/schema, records hashes, and emits a closeout contract. | `project-sow-operational-gate`; `tests/test_project_sow_package.py`; `docs/PROJECT_SOW_OPERATIONAL_READINESS_REPORT.md`. | Met |

## Closeout Verification

The current milestone-closeout verification set is:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_project_sow_package.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src uv run --extra dev python -m compileall src
PYTHONPATH=src uv run --extra dev python -m json.tool docs/schemas/project_sow_intake_v0.schema.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/templates/project_sow_land_exchange_intake_template.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/project_sow_resource_scopes_v1.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/project_sow_ea_handoff_rules_v1.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/project_sow_eval_proving_intakes_v1.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/fixtures/project_sow/east_crazies_land_exchange_intake.json
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate --output-dir /tmp/project-sow-milestone-closeout-gate
git diff --check
```

`docs/SESSION_HANDOFF.md` records the latest observed command counts after the closeout run.
