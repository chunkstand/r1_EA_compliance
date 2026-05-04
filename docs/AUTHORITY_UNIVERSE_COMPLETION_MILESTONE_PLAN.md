# Authority Universe Completion Milestone Plan

Date: 2026-05-04

This milestone completes the legal and policy authority universe used by applicability-first
Environmental Assessment review. The objective is not to make more compliance findings by default.
The objective is to make the system prove that it considered the full bounded universe of USDA
Forest Service Region 1 EA-relevant laws, statutes, regulations, executive orders, agency policies,
forest-plan requirements, project-specific authorities, and litigation doctrines before it generates
an applicable rule pack for a specific EA package.

## Goal

Complete and validate the authority universe so every reviewer-ready EA compliance review can show:

- which authority families were considered;
- which current source records support each family;
- which rule templates and applicability predicates represent the family;
- which families were applicable, not applicable, unresolved, or adjudicated for the package;
- which package facts, source passages, graph paths, and search coverage certificates support each
  decision;
- why the generated rule pack is a complete derivative of the validated authority universe for the
  review package.

## Non-Goals

- Do not provide legal advice or substitute the system for a qualified NEPA/USFS reviewer.
- Do not add hidden code heuristics for one project type or one known EA package.
- Do not mark every authority as applicable. Completion means every authority family is represented,
  searchable, and decidable or explicitly unresolved.
- Do not rerun broad live downloads or regenerate the full corpus unless source additions require it
  and the run is scoped through the downloader/catalog gates.
- Do not weaken current generated-rule-pack gates. Compliance review must still consume validated
  applicable authorities only.
- Do not collapse workbook rows, duplicate URLs, or source records only because they support the
  same authority family.

## Relevant Surfaces

- Active workbook:
  `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx`
- Existing rule pack:
  `config/compliance_rule_pack_nepa_ea_v0.json`
- Existing coverage matrix:
  `config/compliance_rule_pack_coverage_nepa_ea_v0.json`
- Applicability eval seeds:
  `config/applicability_eval_seed.json`
- Gold/compliance eval seeds:
  `config/compliance_gold_eval_v0.json`,
  `config/compliance_review_eval_seed.json`
- Source catalog:
  `source_library/catalog/source_catalog.jsonl`,
  `source_library/catalog/review_sources.sqlite`,
  `source_library/catalog/source_set_manifest.json`
- Applicability implementation:
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_decisions.py`,
  `src/usfs_r1_ea_sources/applicability_retrieval.py`
- Package fact graph:
  `src/usfs_r1_ea_sources/package_fact_graph.py`
- Compliance review:
  `src/usfs_r1_ea_sources/compliance_review.py`
- Output schemas and state docs:
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`

## Current Baseline

The current active rule pack is `nepa-ea-v0` version `0.4.0` with `44` rules and `26` declared
baseline source records. Its rule categories are:

- `agency_policy`: 5
- `case_law`: 1
- `executive_order`: 2
- `forest_plan`: 1
- `law`: 15
- `regulation`: 19
- `state_requirement`: 1

The current source-set and downstream review artifacts are strong enough to prove the V1 Custer
Gallatin land-exchange review path. The post-V1 applicability machinery can build an authority
universe, package fact graph, retrieval trace, graph trace, decision ledger, non-applicable
authority artifact, coverage certificates, and generated rule pack.

The remaining gap is authority-universe completeness. Several common USFS EA authority families are
not yet represented as first-class active authority families in the generated review path, even
where the package fact graph already detects related cues.

## Implementation Status

- Milestone 1 is complete in `config/authority_universe_families_nepa_ea_v1.json`.
- Milestone 2 is complete through `config/authority_source_addition_decisions_nepa_ea_v1.json` and
  the derived `authority-currentness` gate. The latest local report for
  `source-set-ba8d0feae79501b8` validates `35` families, `207` family/source currentness records,
  `33` source-currentness-confirmed families, `1` documented candidate non-addition, and `1`
  superseded replacement-source family with `21` Milestone 2 families closed or documented and `0`
  failed families.
- Milestone 3 is complete through `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/authority_family_rule_template_coverage_nepa_ea_v1.json`, package fact graph cue
  coverage for designated areas, and authority-universe builder support for
  `authority_family_rule_template` candidates. A current source-set contract build validates `19`
  expanded authority-family templates alongside the `44` base rule templates and `329` forest-plan
  component candidates.
- The next milestone is Milestone 4: add independent applicability eval and adjudication coverage
  for the expanded authority universe.

## Required Authority Families

This milestone should produce an explicit authority-family inventory. Each family must have one of
these statuses:

- `active`: source records, rule templates, trigger contracts, evidence filters, and eval coverage
  are implemented.
- `source_only`: source records exist, but rule templates or applicability predicates are missing.
- `candidate`: the family is identified as potentially relevant but source records still need to be
  added or confirmed.
- `out_of_scope`: the family is intentionally excluded for Region 1 EA review, with a documented
  reason and reviewer-visible rationale.
- `superseded`: the family or authority source has been replaced, reserved, repealed, or otherwise
  superseded, with the replacement link recorded.

Minimum authority families to inventory and close:

- Core NEPA statute, USDA NEPA procedures, Forest Service NEPA directives, EA/FONSI requirements,
  categorical exclusion/FANEC screening, applicant/third-party document requirements, tiering,
  programmatic documents, and sponsor-prepared document constraints.
- NFMA, 36 CFR Part 219, project consistency under 36 CFR 219.15, forest-plan components, species
  of conservation concern, and Region 1 forest-plan overlays.
- Administrative review and final agency action authorities, including 36 CFR Part 218, 36 CFR Part
  214 where written instruments apply, legal notice, objection periods, decision notice/FONSI, and
  Administrative Procedure Act final agency action.
- ESA Section 7, ESA implementing regulations, biological assessment/evaluation expectations,
  informal/formal consultation, concurrence, biological opinion, and Forest Service sensitive
  species policy.
- NHPA Section 106, 36 CFR Part 800, SHPO/THPO consultation, historic properties, adverse effects,
  mitigation, and cultural-resource documentation.
- Clean Water Act Sections 401, 402, and 404; wetlands and waters of the United States;
  stormwater/NPDES where relevant; water-quality certification; and Corps/EPA/state permit cues.
- Clean Air Act authority, including smoke, prescribed fire, conformity, state implementation plan
  cues, and air-quality permit or coordination triggers where relevant.
- Executive Order 11988 floodplain management and Executive Order 11990 wetlands protection as
  separate but related authorities.
- Environmental justice and civil-rights authorities, including Title VI and current federal
  environmental-justice executive/policy requirements that apply to USDA/Forest Service review.
- Tribal consultation and trust-responsibility authorities, including Executive Order 13175,
  government-to-government consultation, treaty rights, sacred sites under Executive Order 13007,
  THPO coordination, and confidentiality of sensitive cultural information.
- Archaeological and cultural protection authorities that can matter in EA records, including ARPA,
  NAGPRA, AIRFA, and RFRA when project facts trigger them.
- Migratory Bird Treaty Act, Executive Order 13186, Bald and Golden Eagle Protection Act, and
  species/resource-specific wildlife obligations.
- Roadless Rule, inventoried roadless areas, recommended wilderness, designated wilderness,
  wilderness study areas, Wild and Scenic Rivers, eligible or suitable wild and scenic rivers,
  National Trails System, and other congressionally or administratively designated areas.
- Multiple-Use Sustained-Yield Act, Organic Administration Act, National Forest roads/access
  authorities, travel management authorities, and special-use authorities when project facts trigger
  them.
- Land-exchange-specific authorities, including 36 CFR Part 254, Federal Land Policy and Management
  Act exchange provisions where applicable, valuation/appraisal, public-interest determination,
  equal-value or cash-equalization requirements, mineral/reservation constraints, title evidence,
  hazardous-substance due diligence, and public notice.
- Hazardous materials and site-condition authorities, including CERCLA-related due diligence or
  all-appropriate-inquiry style record checks where a land acquisition, disposal, facility, or mine
  feature creates the trigger.
- Invasive species, noxious weeds, pesticide/herbicide, soil productivity, watershed, riparian,
  fisheries, and state/local permit families needed for common Region 1 EA project types.
- Litigation doctrine and review-risk authorities, including hard look, reasonable alternatives,
  cumulative effects, segmentation, connected actions, stale science, tiering, mitigation
  enforceability, site-specific analysis, public-comment response, forest-plan consistency, and
  independent ESA/NHPA compliance.

## Work Plan

### Milestone 1: Authority Inventory And Crosswalk

Goal:
Create a machine-readable authority-family inventory that crosswalks every required authority family
to workbook rows, source catalog records, rule IDs, applicability predicates, package fact types,
coverage requirements, and eval cases.

Required outputs:

- `config/authority_universe_families_nepa_ea_v1.json`
- inventory summary in `docs/CURRENT_SYSTEM_STATE.md`
- schema section in `docs/OUTPUT_SCHEMAS.md`

Acceptance criteria:

- Every required authority family has a status, source-record mapping, and rationale.
- Existing `0.4.0` rules map to authority families without orphan rules.
- Existing workbook baseline and conditional rows map to authority families without orphan source
  records unless explicitly excluded.
- Superseded or reserved authorities, such as reserved Forest Service NEPA regulations, are marked
  with replacement/current-source evidence.

### Milestone 2: Source Additions And Currentness Gate

Goal:
Add or confirm source records for missing `candidate` and `source_only` families, then validate
that the active source set contains current authoritative sources.

Status:
Implemented. The environmental-justice/civil-rights candidate has a documented non-addition rather
than silent current-source coverage, because revoked environmental-justice executive orders are not
accepted as current controlling sources. The current source set passes the authority-currentness
gate without counting excluded, failed, reserved, repealed, or superseded records as current
authority.

Required outputs:

- workbook/source additions or documented non-additions;
- updated `config/url_overrides.toml` only where manual URL repair is needed;
- updated source catalog/source-set after scoped downloader and catalog runs when additions are
  made;
- `authority_currentness_report.json` under the derived source-set or review validation layer.

Acceptance criteria:

- Currentness report records source title, citation, URL, effective date when available, capture
  date, supersession status, source record ID, and authority-family ID.
- Reserved, repealed, or superseded sources cannot silently satisfy current authority requirements.
- Live web failures, challenge pages, blocked pages, empty bodies, and unsupported content types do
  not count as successful authority capture.

### Milestone 3: Rule Templates And Applicability Contracts

Goal:
Represent each active authority family as data-backed rule templates and applicability predicates,
with positive triggers, negative triggers, package fact requirements, source evidence requirements,
retrieval filters, graph expansion contracts, dependencies, exceptions, and supersession links.

Status:
Implemented. The source-currentness-confirmed former `source_only` families are now active through
`19` Milestone 3 authority-family rule templates. The base `nepa-ea-v0` rule pack remains stable;
the expanded templates are loaded into `applicability-authority-universe` through
`--authority-family-templates-path` and are materialized into generated rule packs only after
applicability validation marks the corresponding candidate authority applicable.

Required outputs:

- new builder input: `config/authority_family_rule_templates_nepa_ea_v1.json`;
- new coverage matrix: `config/authority_family_rule_template_coverage_nepa_ea_v1.json`;
- updated applicability authority-universe builder support for `authority_family_rule_template`;
- updated package fact graph term specs for reusable designated-area cues;
- updated inventory/docs/tests reflecting `33` active families and `0` remaining Milestone 3
  template gaps.

Acceptance criteria:

- No family is active without source evidence and at least one applicability predicate.
- No package fact trigger is hidden only in code when it should be a data-backed authority-family
  predicate.
- Clean Water Act, floodplain, tribal consultation, wilderness/designated area, and land-exchange
  cues in the package fact graph map to active authority families or explicit out-of-scope
  decisions.
- Generated rule packs contain only validated applicable authorities.

### Milestone 4: Applicability Eval And Adjudication Coverage

Goal:
Add independent applicability-quality tests for the expanded authority universe before compliance
quality is scored.

Required outputs:

- expanded `config/applicability_eval_seed.json`;
- expert-adjudicated gold cases for applicable, not-applicable, unresolved, and adjudicated
  decisions;
- package snippets or real package fixtures covering the new authority families;
- promotion-suite requirements for authority-universe completion.

Acceptance criteria:

- Applicability precision, recall, unresolved handling, and negative-proof coverage are scored
  separately from compliance findings.
- At least one positive and one negative case exists for every high-priority authority family.
- At least one real package fixture exercises land exchange, water/wetlands, cultural/tribal,
  wildlife/species, designated-area, and forest-plan consistency triggers.
- Failed retrieval, low-confidence retrieval, excessive graph fan-out, or insufficient coverage
  creates a validation failure or explicit reviewer-resolution item.

### Milestone 5: Compliance Review And Report Integration

Goal:
Make authority-universe completion visible in reviewer outputs without turning non-applicable
authorities into compliance findings.

Required outputs:

- compliance matrix additions for authority-family provenance;
- non-applicable authority appendix or report section;
- reviewer-resolution report for unresolved or adjudicated families;
- litigation-risk summary artifact tied to evidence and authority families.

Acceptance criteria:

- Compliance findings cite generated applicable authority IDs and authority-family IDs.
- Non-applicable authorities remain visible with coverage certificates and rationale.
- Unresolved authority families block reviewer-ready status unless adjudicated.
- Litigation-risk flags are evidence-backed risk categories, not model-generated legal
  conclusions.

## Required Verification

Run the narrowest focused checks during each slice, then close the milestone with:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_package_fact_graph.py
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

Do not use `promotion-suite --strict-expansion` as a required closeout gate until the authority
inventory/eval milestones intentionally update or fill the expansion slots in
`config/promotion_suite_v1.json`. In the current manifest, strict expansion is designed to fail on
two open real-package slots with `package_fixture_missing`; that is broader real-package readiness,
not evidence that an authority-universe slice failed.

If source records are added, also run the downloader/catalog acceptance and integrity gates named in
`DOWNLOADER_RULES.md`.

## Commit Policy

Commit each completed slice atomically:

1. authority inventory and schemas;
2. source additions and currentness gate;
3. rule templates and applicability predicates;
4. eval/adjudication coverage;
5. report and promotion-suite integration.

Stage only the verified slice. Do not stage generated `source_library/` artifacts unless repository
policy is explicitly changed for the artifact family.

## Stop Conditions

Stop and report the blocker instead of proceeding when:

- a required source authority cannot be captured from an authoritative source;
- workbook/source-record identity cannot be preserved;
- a superseded authority conflicts with an apparently current source;
- applicability decisions require legal judgment not represented by data, evidence, or adjudication;
- broad corpus regeneration would be needed without approval;
- focused tests or validation gates fail after the relevant slice.

## Completion Definition

This milestone is complete when a reviewer-ready applicability run can show a complete
authority-family inventory, current source coverage, validated applicable and non-applicable
decisions for every family, expanded eval coverage, and generated review rule packs that derive only
from validated applicable authorities. At that point, the system can make a defensible claim that it
considered the full bounded USFS Region 1 EA authority universe for a package, while still making no
unauthorized legal conclusion beyond the evidence-backed review artifacts.
