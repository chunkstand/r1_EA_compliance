# Deemer-Henry Fresh EA Review Results

Date: 2026-06-05 local / 2026-06-06 UTC

## Scope

This ad hoc fresh-EA review starts from the user-supplied public Pinyon/Box
folder and runs the existing reviewer pipeline without changing runtime code or
tracked review contracts.

Selected authority:

- project page: `https://www.fs.usda.gov/project/?project=59556`
- project title: `Deemer-Henry`
- project ID: `59556`
- public Pinyon/Box root:
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158228778486`
- Box root label: `Deemer-Henry (59556)`
- forest: `lolo-nf`
- ranger district: `Plains/Thompson Falls Ranger District`
- county/state: `Sanders County`, `Montana`
- expected analysis type: `Environmental Assessment`
- review ID: `region1-example-lolo-deemer-henry-59556`
- source set: `source-set-f70ea11e04ae3d53`

The Box root is small enough for complete first-pass package intake. It
contains Analysis, Decision, and Scoping folders with five PDFs total.

## Commands

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources box-folder-intake \
  --root-folder-url https://usfs-public.app.box.com/v/PinyonPublic/folder/158228778486 \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --output-dir source_library \
  --download

PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path source_library/reviews/_intake/region1-example-lolo-deemer-henry-59556 \
  --output-dir source_library \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --docling-timeout-seconds 180

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path source_library/reviews/_intake/region1-example-lolo-deemer-henry-59556 \
  --output-dir source_library \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --forest-unit-id lolo-nf \
  --reuse-package-cache \
  --docling-timeout-seconds 180

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --forest-unit-id lolo-nf

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --package-path source_library/reviews/_intake/region1-example-lolo-deemer-henry-59556

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gate-graph \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path source_library/reviews/_intake/region1-example-lolo-deemer-henry-59556 \
  --output-dir source_library \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --review-id region1-example-lolo-deemer-henry-59556 \
  --forest-unit-id lolo-nf \
  --rule-pack source_library/reviews/region1-example-lolo-deemer-henry-59556/applicability/generated_rule_pack.json \
  --reuse-package-cache \
  --docling-timeout-seconds 180

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-deemer-henry-59556
```

## Metrics

Package intake:

- downloaded `5/5` PDFs with `0` failures
- total package bytes: `6,633,421`
- folders: Analysis, Decision, Scoping

Base EA review:

- package files: `5`
- extracted files: `5`
- package failures: `0`
- package chunks: `267`
- parser counts: `4` pypdf text fallback, `1` Apple Vision PDF raster
- base checklist: `5` pass findings, `0` unsupported findings
- reviewer ready: `true`

Forest Plan context:

- scope status: `lolo_nf`
- title/admin evidence resolves to Lolo National Forest, Plains/Thompson Falls
  Ranger District, Sanders County, Montana
- management areas: `5`
- final component evaluation after applicability filter: `911` Lolo component
  candidates, all `911` not applicable, `0` applicable standards
- Forest Plan reviewer-ready: `true`

Applicability:

- authority-universe candidates: `977`
- base rules: `47`
- authority-family templates: `19`
- Forest Plan component candidates: `911`
- selected-action scope: `selected_action_found`
- selected-action package chunks: `36`
- package fact nodes: `2,421`
- retrieval trace rows: `8,793`
- graph trace rows: `24,400`
- decisions: `36` applicable, `941` not applicable, `0` unresolved, `0`
  needs adjudication
- validation status: `passed=true`, `reviewer_ready=true`

Generated rule pack and gate graph:

- generated rule count: `36`
- generated-rule-pack validation: `passed=true`
- gate graph validation: `passed=true`
- gate graph nodes: `1,029`
- gate graph edges: `1,028`
- failed graph checks: `0`

Compliance review:

- reviewer ready: `true`
- validation passed: `true`
- findings: `36`
- finding statuses: `25` pass, `10` uncertain, `1` gap
- unsupported findings: `0`
- rule-claim links: `168`
- rule-claim gaps: `1`
- rule without claim links:
  `forest_service_planning_handbook_amendments_authority_template`
- outputs: `compliance_review.json`, `compliance_matrix.json`,
  `compliance_matrix.md`, and `compliance_matrix.pdf`

Phase eval:

- `passed=true`
- `reviewer_ready=true`
- phases: `30/30` passing
- blockers: `[]`
- critical phases: `10`
- direct-eval-ready phases: `10`
- review direct-eval status: `not_required_for_ad_hoc_review`
- declared review contract: `false`
- contract-backed promotion ready: `false`

## Finding

Deemer-Henry is now started and reviewer-ready as an ad hoc EA review against
the current f70 source set. The run is evidence-backed through intake,
extraction, Forest Plan context, applicability, generated rule-pack validation,
compliance matrix generation, and phase-eval.

This is not a governed forest-specific example promotion yet. It has no tracked
V1 review-eval contract, no registry entry, no promoted component eval case
file, and no contract-backed promotion readiness. The one substantive review
residual inside the generated compliance artifacts is the single gap finding
and ten uncertain findings, with the lone rule-claim gap on
`forest_service_planning_handbook_amendments_authority_template`.
