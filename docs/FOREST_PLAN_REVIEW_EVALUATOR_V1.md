# Forest Plan Review Evaluator V1

This brief defines the first build contract for a generic forest-plan review evaluator. Custer
Gallatin and the East Crazies package are the first proving case, not the architecture boundary.

The evaluator must stay aligned with the Bitter Lesson: review quality should improve through better
source coverage, structured metadata, retrieval, evidence extraction, evaluation fixtures, and failure
telemetry. Runtime logic must not depend on handwritten Custer Gallatin or East Crazies exceptions.

## Goal

Build a reusable forest-plan review evaluator that can:

- identify the applicable forest or grassland plan profile for an EA package;
- verify that required plan and supporting source records are indexed;
- resolve package geography, management areas, overlays, and action context from evidence;
- retrieve applicable plan components from cataloged source-library records;
- map EA package evidence to applicable plan components;
- emit citation-bearing findings, gaps, and reviewer-resolution items; and
- feed the full EA/compliance review path without converting evidence retrieval into unsupported
  legal conclusions.

The system-level V1 demo milestone plan is tracked in
`docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`; the evaluator is a support slice for
forest-plan-aware demos, not the whole V1 scope. The component-level forest-plan evaluation plan is
tracked in `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`.

## Non-Goals

- Do not build Custer Gallatin-specific runtime control flow.
- Do not infer forest-plan consistency from broad mentions of "Forest Plan" or "Land Management
  Plan."
- Do not rebuild the full 190-row downstream corpus solely for this milestone.
- Do not treat the evaluator output as a final legal sufficiency determination.
- Do not scan raw artifact filenames to decide reviewer behavior.

## Generic Forest Plan Profile Schema

The evaluator should read forest-specific facts from data/config/catalog surfaces. A profile should be
expressive enough to support Custer Gallatin now and other Region 1 forest plans later.

Minimum profile fields:

- `forest_unit_id`: stable forest or grassland identifier.
- `forest_unit_names`: names and aliases that indicate forest-unit scope.
- `ambiguous_unit_terms`: terms that require reviewer resolution when they appear without a
  disambiguating forest-unit signal.
- `active_plan_source_record_id`: source record for the governing land management plan.
- `supporting_source_record_ids_by_role`: source records for planning page, record of decision,
  FEIS volumes, biological assessment, biological opinion, amendments, monitoring reports, or other
  profile-specific supporting roles.
- `required_readiness_source_roles`: roles that must be indexed before review can be reviewer-ready.
- `ranger_district_terms`: ranger district and administrative-unit signals.
- `geographic_area_terms`: plan geography vocabulary.
- `management_area_terms`: management area and allocation vocabulary.
- `overlay_terms`: inventoried roadless areas, recommended wilderness, recreation emphasis areas,
  conservation watersheds, or other plan overlays.
- `plan_component_types`: supported component classes, including desired conditions, objectives,
  standards, guidelines, suitability, monitoring, and plan-amendment records.
- `supporting_record_trigger_rules`: data-driven trigger rules for when supporting source records
  should be retrieved, with trigger terms, package-evidence requirements, and target source roles.
- `review_topics`: profile-specific retrieval topics derived from catalog metadata.

Profile records should be versioned and should preserve source-record IDs. If profile data is derived
from the workbook, catalog, or source documents, the derivation path should be documented.

## East Crazies Proving Case

The first fixture is the East Crazy/Inspiration Divide EA package:

```text
package_path:
source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)

source_set_id:
source-set-ba8d0feae79501b8

current smoke review_id:
cg-live-smoke
```

Expected V1 review shape:

- The evaluator resolves the package to the Custer Gallatin profile using profile data.
- Required Custer Gallatin plan/supporting records are present in retrieval before review proceeds.
- The package resolves to the Bridger, Bangtail, and Crazy Mountains Geographic Area.
- The package resolves to the Crazy Mountains Backcountry Area.
- FEIS, Biological Assessment, and Biological Opinion supporting routes are triggered only from
  explicit package evidence.
- Any ROD route must be triggered only from explicit package evidence, not from generic decision
  labels.
- The plan-component review maps package evidence to applicable plan components and records gaps
  when the package does not support a component.
- No forest-plan review finding is marked supported without both source-library evidence and EA
  package evidence.
- Unresolved geography, missing supporting records, weak trigger evidence, or contradictory package
  evidence become reviewer-resolution items.
- The component-evaluation path writes `forest_plan_component_findings.json`,
  `forest_plan_component_findings.md`, and `forest_plan_reviewer_resolution_queue.json` for packages
  resolved to the selected forest-plan profile.
- The current source-set Custer Gallatin LMP inventory is generated from extracted chunks and has
  passing build coverage with `329` components and `58` standards. The seed inventory remains only a
  fallback/test fixture.

## Expert Alignment Checks

After each forest-plan milestone, check the result against this panel.

### Scott Vandegrift Alignment

The evaluator should support efficient, predictable environmental review:

- reuse existing reliable source records and extracted text when hashes match;
- keep review outputs concise and structured;
- preserve a proposal-record trace for source records, package records, rationale, and decisions;
- make readiness explicit instead of hiding partial corpus state; and
- avoid duplicative full-corpus rebuilds unless promotion requires them.

### Chuck Nicholson Alignment

The evaluator should read like practitioner-grade NEPA QA/QC:

- tie review to purpose and need, proposed action, alternatives, and decision context when available;
- keep analysis proportional to the project and likely issues;
- make screening criteria transparent;
- explain why plan components are applicable or not applicable;
- preserve consultation, coordination, and public-involvement signals when they affect review; and
- turn gaps into actionable reviewer tasks.

### Liz Esposito Alignment

The evaluator should be legally defensible without pretending to be counsel:

- anchor project consistency review to `36 CFR 219.15`;
- distinguish goals, desired conditions, objectives, standards, guidelines, and suitability;
- preserve exact source and package citations, hashes, offsets, pages, and source-record IDs;
- mark sensitive, privileged, missing, or unresolved material rather than smoothing it over;
- separate evidence-backed findings from legal conclusions; and
- make litigation or administrative-record review easier by showing the basis for every assertion.

## Acceptance Gates

The first build milestone is complete only when the repository has:

- a generic forest-plan profile loader or equivalent data-driven contract;
- a Custer Gallatin profile expressed as data, not runtime branching;
- an East Crazies fixture or fixed run contract;
- focused tests proving the generic profile path resolves the East Crazies case;
- focused tests proving Custer Gallatin-specific behavior is profile-driven;
- validation output with source-readiness, context-resolution, supporting-route, and citation checks;
- a machine-readable reviewer-resolution queue; and
- docs updated to describe implemented behavior and residual risk.

The component-evaluation slice now satisfies the output-contract, queue, generated-inventory, and
compliance-review gate portions for current source-set artifacts. It does not yet prove real-package
promotion readiness for the Custer Gallatin proving EA.

Suggested focused verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

## Residual Risks To Preserve

- Current Custer Gallatin resolver behavior is implemented as V0 and now reads forest names,
  required source records, area terms, overlays, and supporting evidence routes from profile data.
  Follow-on sequences still need to expose profile metadata in outputs and add East Crazies
  profile-path fixture coverage before broad use.
- The current Custer Gallatin retrieval slice is intentionally partial for the 190-row source set, but
  it is sufficient for this forest-plan proving case because all required profile source records are
  indexed and retrieval validation passes.
- Full compliance promotion remains separate. Existing downstream promotion gaps, such as unrelated
  source-claim link failures, should not block the generic forest-plan evaluator unless they prevent
  the full EA review path from consuming the evaluator output.
