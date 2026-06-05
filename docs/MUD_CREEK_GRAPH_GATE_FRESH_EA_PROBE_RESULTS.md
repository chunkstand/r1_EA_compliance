# Mud Creek Graph-Gate Fresh-EA Probe Results

Date: 2026-06-05

## Scope

This probe continues the graph-gate review-quality experiment with a fresh EA
package that was not one of the three completed readback cases.

Selected authority:

- project page: `https://www.fs.usda.gov/r01/bitterroot/projects/55744`
- project title: `Mud Creek Vegetation Management Project`
- project ID: `55744`
- public Pinyon/Box root:
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158226071402`
- Box root label: `Mud Creek Vegetation Management Project (55744)`
- forest: `bitterroot-nf`
- ranger district: `West Fork Ranger District`
- expected analysis type: `Environmental Assessment`
- review ID: `region1-example-bitterroot-mud-creek-55744`

The full Box root is broad and includes a multi-GB project-file archive. The
probe intentionally downloaded the direct final EA PDFs and final decision
documents only.

## Commands

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources box-folder-intake \
  --root-folder-url https://usfs-public.app.box.com/v/PinyonPublic/folder/159090049757 \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --output-dir source_library \
  --intake-dir source_library/reviews/_intake/region1-example-bitterroot-mud-creek-55744/analysis_final_ea \
  --download \
  --include-relative-path-prefix 'Mud Creek Final Environmental Assessment - July 2021.pdf' \
  --include-relative-path-prefix 'Appendix E - Roads and Trails.pdf' \
  --include-relative-path-prefix 'Appendix D - Forest Plan Amendment Discussion.pdf' \
  --include-relative-path-prefix 'Appendix B - Implementation Process.pdf' \
  --include-relative-path-prefix 'Appendix A - Design Features.pdf'

PYTHONPATH=src python -m usfs_r1_ea_sources box-folder-intake \
  --root-folder-url https://usfs-public.app.box.com/v/PinyonPublic/folder/190115997893 \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --output-dir source_library \
  --intake-dir source_library/reviews/_intake/region1-example-bitterroot-mud-creek-55744/final_decision_documents \
  --download

PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path source_library/reviews/_intake/region1-example-bitterroot-mud-creek-55744 \
  --output-dir source_library \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --docling-timeout-seconds 180

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path source_library/reviews/_intake/region1-example-bitterroot-mud-creek-55744 \
  --output-dir source_library \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --forest-unit-id bitterroot-nf \
  --reuse-package-cache \
  --docling-timeout-seconds 180

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --forest-unit-id bitterroot-nf

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --package-path source_library/reviews/_intake/region1-example-bitterroot-mud-creek-55744

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gate-graph \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-bitterroot-mud-creek-55744
```

## Metrics

Package intake:

- Final EA intake: `5` selected PDFs downloaded, `0` failures,
  `12,265,741` bytes.
- Final decision intake: `6` PDFs downloaded, `0` failures,
  `7,687,257` bytes.
- Combined scoped package: `11` PDFs and `19,952,998` bytes.

EA review:

- package files: `11`
- extracted files: `11`
- package failures: `0`
- package chunks: `1,167`
- checklist findings: `5`
- unsupported findings: `0`
- reviewer ready: `true`

Forest Plan resolve:

- scope status: `bitterroot_nf`
- management areas: `10`
- project-location signal count: `1`
- component candidates evaluated: `880`
- standards represented: `390`
- component findings needing reviewer resolution: `880`
- reviewer ready: `false`

Applicability:

- authority-universe candidates: `946`
- base rules: `47`
- authority-family rule-template candidates: `19`
- Forest Plan component candidates: `880`
- package fact nodes: `12,881`
- package fact edges: `47,507`
- retrieval trace rows: `8,514`
- graph trace rows: `23,649`
- decisions: `59` applicable, `886` not applicable, `1` needs adjudication
- validation status: `passed=false`, `reviewer_ready=false`

The unresolved authority is:

```text
authority-family-template:nepa-ea-authority-family-rule-templates-v1:0.1.0:minerals_energy_authorities:minerals_energy_authorities_authority_template
```

Graph gate:

- graph validation: `passed=true`
- nodes: `998`
- edges: `997`
- failed graph checks: `0`
- activation states: `102` open, `892` closed, `2` blocked, `1` pending,
  `1` currentness-only
- gate statuses: `102` applicable, `892` not applicable,
  `2` needs adjudication, `1` candidate, `1` superseded

Phase eval:

- `passed=false`
- `reviewer_ready=false`
- phases: `27/30` passing
- blockers:
  - `applicability_validation`: validation failed and not reviewer-ready
  - `generated_rule_pack`: validation failed and not reviewer-ready
  - `compliance_review`: validation failed and not reviewer-ready

Rule-pack generation correctly stopped:

```text
Cannot generate a rule pack because applicability_validation.json has not passed.
```

## Finding

This fresh-EA probe did not produce a fourth completed full-review quality case.
It produced a stronger fail-closed result:

- The package review itself is extractable and reviewer-ready.
- The Forest Plan and applicability layers expose real unresolved review work.
- The graph gate structurally validates while carrying blocked and pending gate
  states.
- The system does not convert an unresolved authority-family conflict into a
  generated rule pack, compliance review, or green phase-eval.

What this adds beyond the three already-reviewed examples: the graph-gate system
is not only a traceability/readback layer for green reviews. On a fresh EA it
preserves a blocked applicability state and prevents a false green downstream
review.

## Boundary

This result does not prove substantive legal correctness for Mud Creek and does
not justify manual or hidden adjudication. Completing this EA as a full fourth
case requires a separate human-review/adjudication packet for the
`minerals_energy_authorities` conflict and the Bitterroot Forest Plan component
resolution queue.
