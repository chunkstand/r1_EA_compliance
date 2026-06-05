# USFS Region 1 EA Sources

Local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA Forest Service Region 1
source material. The workbook is the source-of-truth input; the system captures workbook-defined
source rows into an auditable `source_library/` and builds deterministic extraction, retrieval,
evidence-graph, claim, rule-binding, and EA-review artifacts on top of that corpus.

This is not a generic scraper or ad hoc document folder. Preserve workbook row identity, artifact
provenance, citation labels, validation gates, and rebuildable derived layers.

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
  `review_sources.sqlite`, `source_catalog.jsonl`, and `source_set_manifest.json`
- The repo-root catalog is the named current source-set surface. Its tracked
  pointer is `config/current_source_set_v1.json`; historical catalog gates must
  live under `source_library/runs/` and must not keep `source_library/catalog/`
  pinned to an older source set.
- Raw artifacts are source bytes plus provenance; extraction, retrieval,
  evidence graph, claims, rule-claim links, and review outputs are rebuildable
  derived layers
- Forest-specific example packages stay parallel to `Document_Register_Master`. Runtime
  forest-plan scope is mandatory; current governed examples, aggregate gate counts, and residual
  boundaries are owned by current-state/handoff docs, with routes in `docs/CURRENT_ROUTING.md`.
- Forest Plan review uses active source-set component inventories as authority. Management areas are
  first-class inventory and package fact graph scope, with resolver package evidence promoted from
  `forest_plan_context.json`; reviewer-ready status fails closed on stale/missing inventory,
  unresolved applicable standards, or missing Forest Plan compliance matrix evidence for resolved
  forest contexts. Generated Forest Plan component findings can only satisfy compliance support
  through component-inventory-backed authority evidence, not profile-stuffed terms or
  forest-specific runtime branches.
- Forest-specific reviewer-ready slots also fail closed unless forest-plan context summaries carry
  decision/admin title-page identity evidence for the governing forest or grassland, ranger
  district, county, state, and no competing title-page forest unit.
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
- `config/current_source_set_v1.json`
- `config/promotion_suite_v1.json`
- `config/gold_coverage_v1.json`
- `config/v1_real_package_review_coverage_v1.json`
- `config/forest_specific_example_package_registry_v1.json`
- `config/source_register_queue_resolution_ledger_v1.json`
- `config/forest_plan_profiles.json`
- `config/forest_plan_component_inventory_seed.json`
- `config/forest_plan_component_eval_coverage_v1.json`
- `config/applicability_gate_graph_nepa_ea_v1.json`
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/project_sow_ea_handoff_rules_v1.json`; `config/context_graph_contract_v1.json`
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
6. Build the review-scoped NEPA applicability Gate Graph when applicability
   hierarchy or Forest Plan subgate visibility is needed.
7. Run review, compliance, and evaluation commands against catalog-backed
   surfaces.

For document-generation work, use `document-plan` first and route through
`docs/AGENT_START_HERE.md`.

## Common Commands

Use `PYTHONPATH=src` for direct module commands. The repo-local
`AGENTS.md`, `DOWNLOADER_RULES.md`, and current-state docs carry the full
operator context.

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --limit 10
PYTHONPATH=src python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id <run-id>
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --batch-run-id <batch-run-id>
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources document-plan --request /tmp/document_request.json --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id <review-id>
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gate-graph \
  --output-dir source_library \
  --review-id <review-id>
PYTHONPATH=src python -m usfs_r1_ea_sources graph-gate-review-quality-eval \
  --manifest config/graph_gate_review_quality_eval_v1.json \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources semantic-graph-eval --output-dir source_library --source-set-id <source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources knowledge-graph-query FED-001 --output-dir source_library --source-set-id <source-set-id> --query-type source_record
```

First-class eval/trace workflow:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-inventory \
  --output-dir source_library \
  --source-set-id <source_set_id> \
  --review-id <review-id> \
  --results-path /tmp/usfs-r1-eval-trace-inventory.json
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-store-build \
  --inventory-path /tmp/usfs-r1-eval-trace-inventory.json \
  --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite \
  --summary-path /tmp/usfs-r1-system-eval-trace-summary.json
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-export \
  --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite \
  --canonical-json-path /tmp/usfs-r1-system-eval-trace-export.json \
  --openinference-json-path /tmp/usfs-r1-openinference-traces.json
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-case-promote \
  --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite \
  --case-file config/eval_trace_cases/system_eval_trace_cases_v1.json \
  --trace-id <trace-id> \
  --span-id <span-id> \
  --owner <owner-surface> \
  --risk-level high \
  --tag first-class-eval-trace \
  --assertion "trace remains linked to source artifacts" \
  --review-condition "review when scorer schema changes" \
  --removal-condition "remove only after a superseding case exists"
```
Focused review, extraction, and sidecar adoption helpers:
```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-record-identity-gate \
  --output-dir source_library \
  --catalog-dir <catalog-dir> \
  --eval-file <v1-ea-eval-contract.json>
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-quality-audit --output-dir source_library --source-set-id <source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-layer-build --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-sidecar-retrieval-eval --output-dir source_library --source-set-id <source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-sidecar-consumer-eval --output-dir source_library --source-set-id <source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources chunk-sidecar-consumer-promote --output-dir source_library --source-set-id <source-set-id>
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
