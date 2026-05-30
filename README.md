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
- The repo-root catalog is the named current source-set surface. Its tracked
  pointer is `config/current_source_set_v1.json`; historical catalog gates must
  live under `source_library/runs/` and must not keep `source_library/catalog/`
  pinned to an older source set.
- Raw artifacts are source bytes plus provenance; extraction, retrieval,
  evidence graph, claims, rule-claim links, and review outputs are rebuildable
  derived layers
- Forest-specific example packages stay parallel to `Document_Register_Master`.
  For Bitterroot National Forest, the governed primary example is
  `primary_example_id="bitterroot-front-forest-specific"` with
  `review_id="region1-example-bitterroot-front-57341"` in
  `config/forest_specific_example_package_registry_v1.json`.
  For Beaverhead-Deerlodge National Forest, the governed primary example is
  `primary_example_id="bdnf-south-tobacco-roots-forest-specific"` with
  `review_id="region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"`;
  its Milestone 4 promotion is reduced only by inherited ECID source-delta
  component-coverage drift, not by the Beaverhead-owned slots.
  For Idaho Panhandle National Forests, Lacy Lemoosh is the active candidate
  packet in
  `docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`, but
  `idaho-panhandle-nfs` remains `profile_eval_guidance_only` after local
  package-authority intake and FEIS source-readiness closeout in commit
  `ba3718b`. The tracked replay context is
  `config/replay_contexts/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`;
  resolver scope now resolves to `idaho_panhandle_nfs` from package-local
  `St. Joe Ranger District` evidence, while `St. Maries Ranger District`
  remains the project-page/Box authority label. Local f70 retrieval now indexes
  `R1PLAN-idaho-panhandle-nfs-04` with `1,606` chunks and
  `R1PLAN-idaho-panhandle-nfs-05` with `991` chunks. The next blocker is
  component evaluation/adjudication refresh against the current `36`-item queue,
  not registry promotion. Do not promote the package until component refresh,
  reviewer-stack, and promotion gates pass.
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

Inventory first-class eval/trace links without mutating source artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-inventory \
  --output-dir source_library \
  --source-set-id <source-set-id> \
  --review-id <review-id> \
  --results-path /tmp/usfs-r1-eval-trace-inventory.json
```

Build the local first-class eval/trace SQLite store from an inventory:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-store-build \
  --inventory-path /tmp/usfs-r1-eval-trace-inventory.json \
  --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite \
  --summary-path /tmp/usfs-r1-system-eval-trace-summary.json
```

Export the local eval/trace store as canonical JSON and OpenInference-shaped
spans:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-export \
  --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite \
  --canonical-json-path /tmp/usfs-r1-system-eval-trace-export.json \
  --openinference-json-path /tmp/usfs-r1-openinference-traces.json
```

Promote a stored first-class eval trace/span into a tracked case fixture:

```bash
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
