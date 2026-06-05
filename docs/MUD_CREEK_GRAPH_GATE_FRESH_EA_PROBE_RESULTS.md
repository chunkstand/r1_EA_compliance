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

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
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
- selected-action scope: `selected_action_found`
- selected-action package chunks: `116`
- selected-action validation: `passed=true`
- package fact nodes: `12,881`
- package fact edges: `47,507`
- retrieval trace rows: `8,514`
- graph trace rows: `23,644`
- decisions: `38` applicable, `908` not applicable, `0` unresolved, `0`
  needs adjudication
- validation status: `passed=true`, `reviewer_ready=true`

The previously unresolved authority now resolves to absent trigger evidence:

```text
authority-family-template:nepa-ea-authority-family-rule-templates-v1:0.1.0:minerals_energy_authorities:minerals_energy_authorities_authority_template
```

- status: `not_applicable`
- basis type: `absent_trigger_evidence`
- arbitration status: `positive_trigger_absent`
- decisive trigger groups: `[]`
- package evidence spans: `0`

Generated rule pack:

- generated-rule-pack validation: `passed=true`
- generated rule count: `38`
- generated-rule-pack ready: `true`
- selected-action hash recorded: `true`

Graph gate:

- graph validation: `passed=true`
- nodes: `998`
- edges: `997`
- failed graph checks: `0`
- activation states: `75` open, `921` closed, `1` pending,
  `1` currentness-only
- gate statuses: `75` applicable, `921` not applicable, `1` candidate,
  `1` superseded
- blocked gates: `0`

Phase eval:

- `passed=false`
- `reviewer_ready=false`
- phases: `29/30` passing
- blockers:
  - `compliance_review`: validation failed and not reviewer-ready

## Finding

This fresh-EA probe still does not produce a fourth completed full-review
quality case. It now has two useful system findings:

- The package review itself is extractable and reviewer-ready.
- The initial graph-gate run correctly preserved a blocked applicability state
  instead of producing a false green.
- The selected-action slice showed that the block was not a substantive
  minerals/energy action. It was caused by broad package-context consumption:
  the old minerals-energy template accepted bare `minerals` evidence, and the
  selected alternative contains restoration language about exposing mineral
  soil for seed germination.
- `selected_action/selected_action.json` is now the package-action boundary for
  applicability. Package trigger search, retrieval, graph expansion, Forest
  Plan present-values, decisions, provenance, validation, and generated rule
  packs all carry the selected-action hash.
- After replay, the minerals-energy family is not applicable because no
  selected-action trigger group is present for mining, mineral exploration,
  mineral development, plan of operations, mineral materials, mineral
  production, energy development, surface use plan, mine reclamation,
  reclamation plan, or oil and gas.
- Applicability validation and generated-rule-pack validation now pass. The
  remaining phase-eval blocker is only the missing compliance review/matrix,
  which has not been generated for this ad hoc packet.

What this adds beyond the three already-reviewed examples: the graph-gate system
is not only a traceability/readback layer for green reviews. On a fresh EA it
first preserved a blocked applicability state, then provided the evidence needed
to tighten the applicability input boundary and replay the gate to green for
applicability without silently masking downstream compliance work.

## Boundary

This result does not prove substantive legal correctness for Mud Creek and does
not complete Mud Creek as a full fourth review case. The selected-action
applicability and generated-rule-pack gates are reviewer-ready; compliance
review and the compliance matrix remain ungenerated, and the Bitterroot Forest
Plan component resolution queue remains outside this slice.
