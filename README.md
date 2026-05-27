# USFS Region 1 EA Sources

Local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA
Forest Service Region 1 source material.

The workbook is the source-of-truth input for the knowledge base. The system
captures workbook-defined source rows into a local, auditable `source_library/`
and builds deterministic extraction, retrieval, evidence-graph, claim,
rule-binding, and EA-review artifacts on top of that corpus.

This repository is not a generic scraper or ad hoc document folder. Preserve
workbook row identity, artifact provenance, citation labels, validation gates,
and rebuildable derived layers.

## Start Here

- Live repo routing: `docs/CURRENT_ROUTING.md`
- Current volatile repo state: `docs/CURRENT_SYSTEM_STATE.md`
- Active packet and next truthful slice: `docs/SESSION_HANDOFF.md`
- Agent-driven document work: `docs/AGENT_START_HERE.md`
- Downloader, catalog, and source-capture rules: `DOWNLOADER_RULES.md`
- Architecture map and boundaries: `docs/ARCHITECTURE.md`
- Output contracts and schemas: `docs/OUTPUT_SCHEMAS.md`

Live counts, source-set IDs, replay status, and current blocker text are owned
by `docs/CURRENT_SYSTEM_STATE.md` and the top of `docs/SESSION_HANDOFF.md`.
They are intentionally not duplicated here.

## Stable Repo Contract

- Active workbook: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Active load-bearing table: `Document_Register_Master`
- `Direct_File_Capture_Queue`, `Removed_Not_Applicable_Final`, and workbook
  audit sheets are not default download targets
- `source_library/` is the local evidence store and is intentionally ignored by
  git unless the repo policy changes explicitly
- Reviewer logic reads catalog surfaces, not raw artifact filenames:
  - `source_library/catalog/review_sources.sqlite`
  - `source_library/catalog/source_catalog.jsonl`
  - `source_library/catalog/source_set_manifest.json`
- Raw artifacts are source bytes plus provenance; extraction, retrieval,
  evidence graph, claims, rule-claim links, and review outputs are rebuildable
  derived layers
- For the canonical workbook contract and downloader constraints, use
  `DOWNLOADER_RULES.md` together with `docs/CURRENT_SYSTEM_STATE.md`

## Key Paths

- Source code: `src/usfs_r1_ea_sources/`
- Tests: `tests/`
- Configuration and eval seeds: `config/`
- Current-state and milestone docs: `docs/`
- Generated local corpus and derived outputs: `source_library/`
- Static viewer: `viewer/`
- Capabilities briefs: `docs/capabilities/`

## Current Inputs

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `DOWNLOADER_RULES.md`
- `config/downloader.toml`
- `config/url_overrides.toml`
- `config/promotion_suite_v1.json`
- `config/forest_plan_profiles.json`
- `config/forest_plan_component_inventory_seed.json`
- `config/forest_plan_component_eval_coverage_v1.json`
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/project_sow_ea_handoff_rules_v1.json`
- `docs/schemas/document_request_v1.schema.json`
- `docs/schemas/project_sow_intake_v0.schema.json`

## Stored Data

Generated outputs are written under `source_library/`:

- Raw artifacts: `source_library/artifacts/raw/`
- Download manifests: `source_library/manifests/`
- Run ledgers and reports: `source_library/runs/<run_id>/`
- Reviewer catalog: `source_library/catalog/`
- Derived source-set outputs: `source_library/derived/<source_set_id>/`
- Review outputs: `source_library/reviews/<review_id>/`
- Project SOW outputs: `source_library/projects/<project_id>/`
- Document-planning outputs: `source_library/document_plans/<request_id>/`
- Evaluation outputs: `source_library/evaluations/`

## Reviewer Engine Entry Points

The EA review engine should start from catalog surfaces rather than scanning
artifact filenames:

- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`

The normal layer order is:

1. Capture workbook-defined source rows.
2. Build the reviewer-facing catalog.
3. Build extraction and chunk artifacts.
4. Build retrieval and evidence-graph layers.
5. Build claim and rule-binding layers.
6. Run review, compliance, and evaluation commands against catalog-backed
   surfaces.

For document-generation work, use `document-plan` first and route through
`docs/AGENT_START_HERE.md`.

## Common Commands

Validate the active canonical source register:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
```

Dry-run workbook parsing without network access:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library
```

Preflight URL reachability without saving artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --limit 10
```

Validate a download run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id <run-id>
```

Build the catalog from a controlled batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --batch-run-id <batch-run-id>
```

Build extraction outputs from the active catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

Plan document work without generating canonical outputs:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources document-plan \
  --request /tmp/document_request.json \
  --output-dir source_library
```

Run review-scoped phase evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id <review-id>
```

Validate replay-facing source-record identity against a target catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-record-identity-gate \
  --output-dir source_library \
  --catalog-dir <catalog-dir> \
  --eval-file <v1-ea-eval-contract.json>
```

Use the Docling-specific environment only for extraction and review paths that
require it:

```bash
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library
```

## Development

Run the focused repo checks with the project development environment:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Use targeted tests for the surface you changed. Do not weaken tests or gates to
get green.

## Go Deeper

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md`
- `docs/FOREST_PLAN_REVIEW_EVALUATOR_V1.md`
- `docs/TECH_DEBT_REGISTER.md`
