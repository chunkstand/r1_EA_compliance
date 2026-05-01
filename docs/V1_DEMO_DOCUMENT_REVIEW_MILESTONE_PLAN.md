# V1 System Plan: Custer Gallatin EA Compliance Review

Date: 2026-05-01

This is the canonical V1 system plan for the USFS Region 1 EA reviewer engine.

V1 exists to produce a repeatable, evidence-backed compliance review for an Environmental
Assessment package on the Custer Gallatin National Forest. The Custer Gallatin / East Crazy
Inspiration Divide package is the proving ground that demonstrates the system can start from an
auditable source library, evaluate an EA against the applicable authority set, and emit review
artifacts a human reviewer can inspect.

V1 is not the final Region 1 product boundary. Custer Gallatin is the first concrete proving case;
the system architecture must remain profile-driven, source-driven, and reusable for other forests
and EA packages.

## V1 Goals

- Produce a local compliance review for a Custer Gallatin National Forest EA package.
- Use the current workbook-backed source library and preserve source-record identity, hashes,
  citation labels, offsets, and source-set IDs throughout the review.
- Evaluate the EA against the configured NEPA EA compliance rule pack, including every baseline
  workbook authority rule and triggered conditional authorities.
- Make NFMA forest-plan consistency review a mandatory Custer Gallatin review phase when the package
  resolves to the Custer Gallatin profile.
- Evaluate Custer Gallatin plan components under `36 CFR 219.15` with distinct handling for goals,
  desired conditions, objectives, standards, guidelines, and suitability.
- Emit machine-readable and reviewer-facing outputs: validation files, JSON review reports,
  Markdown reports, PDF compliance matrices, finding graphs, and reviewer-resolution queues.
- Block reviewer-ready status when evidence is missing, stale, ambiguous, unsupported, or dependent
  on an unresolved human judgment.
- Keep findings evidence-backed and operationally useful without pretending to replace responsible
  official judgment, counsel review, or final legal sufficiency review.

## V1 Non-Goals

- Do not claim broad Region 1 production readiness from the Custer Gallatin proving case.
- Do not hardcode East Crazies or Custer Gallatin runtime branches; forest-specific facts belong in
  profiles, inventories, rule packs, catalog metadata, and source records.
- Do not scan raw artifact filenames to decide reviewer behavior.
- Do not use model-generated prose as the source of truth for readiness, compliance status, or
  authority applicability.
- Do not mark a finding supported without both source-library evidence and EA package evidence.
- Do not mark NFMA forest-plan review complete from a broad statement that the project is consistent
  with the Forest Plan.
- Do not stage generated `source_library/` outputs unless repository policy is explicitly changed.
- Do not treat V1 as legal advice or a replacement for agency/counsel review.

## Expert-Informed Design Constraints

These are source-informed product lenses, not quoted personal requirements.

### Scott Vandegrift Lens

Public basis:
Scott Vandegrift is USDA's Chief Environmental Review and Permitting Officer contact for USDA's
2026 NEPA final rule. USDA's current NEPA procedures emphasize efficient and effective reviews,
proposal records, traceability, and unique review identifiers. His Forest Service engineering
profile also emphasizes communication, efficiency, and prioritizing practical needs on the ground.

System implications:

- Treat V1 as an operator workflow, not a one-off demo transcript.
- Make every run trackable by `review_id`, `source_set_id`, package path/hash, rule-pack version,
  profile ID, component inventory version, and validation status.
- Preserve a proposal-record-style trace: inputs considered, evidence selected, rationale, rejected
  or unresolved issues, and reviewer next actions.
- Keep reports concise enough for decision support, with deeper provenance available in machine
  artifacts.
- Prefer reuse-first extraction and targeted rebuilds when hashes prove source artifacts are current.

### Chuck Nicholson Lens

Public basis:
Chuck Nicholson chairs NAEP's NEPA Practice Group and has decades of environmental and NEPA
compliance experience preparing EAs, EISs, and CEs. NAEP's NEPA Practice Committee emphasizes best
practices, emerging regulatory changes, and helping practitioners understand NEPA's role in project
development.

System implications:

- Make the review read like practitioner-grade NEPA QA/QC.
- Tie findings to purpose and need, proposed action, alternatives, affected environment,
  environmental consequences, mitigation, consultation, coordination, public involvement, and
  decision context when those package sections exist.
- Make screening criteria visible. A reviewer should see why a rule or plan component was
  applicable, not applicable, uncertain, or unresolved.
- Keep review proportional to likely issues while still proving that mandatory baseline authorities
  and applicable standards were not skipped.
- Turn gaps into actionable reviewer tasks instead of vague warnings.

### Liz Esposito Lens

Public basis:
Liz Esposito's public bio describes her as a natural resources attorney with NEPA/CEQA and forestry
expertise, a former USFS NEPA planner, and a former USDA Office of the General Counsel attorney
advising the Forest Service on natural resources and land management issues. Her public experience
emphasizes legal adequacy review, permitting strategy, litigation, and defending USFS environmental
decisions involving NEPA, CWA, ESA, and NFMA.

System implications:

- Build for administrative-record defensibility from the first V1 run.
- Separate evidence-backed reviewer signals from legal conclusions.
- Preserve exact source and package citations, hashes, offsets, pages when available, source-record
  IDs, and source-set IDs.
- Treat stale authorities, source-set drift, missing claim links, and missing package evidence as
  blockers, not cosmetic warnings.
- Model `36 CFR 219.15` directly: goals/desired conditions/objectives, standards, guidelines, and
  suitability require different tests.
- Mark sensitive, privileged, missing, or unresolved material explicitly instead of smoothing it into
  prose.

## Current Baseline

Already in place:

- The workbook-driven source library is captured for the current 190-row source set.
- The active catalog source set is `source-set-ba8d0feae79501b8`.
- The current catalog contains the Custer Gallatin planning page, 2022 Land Management Plan, Record
  of Decision, FEIS Volumes 1 and 2, Biological Assessment, and Biological Opinion.
- A Custer Gallatin-focused extraction/retrieval slice exists for those seven required forest-plan
  records.
- `ea-review` can produce deterministic package checklist outputs from reviewer-ready retrieval
  evidence.
- `compliance-review` can produce compliance review JSON, compliance matrix JSON/Markdown/PDF, and
  finding graph artifacts from configured rules and package evidence.
- `forest-plan-resolve` can resolve Custer Gallatin context through profile data, required
  source-record readiness, plan geography, overlays, and trigger-gated supporting records.
- Forest-plan component evaluation V0 has a generated current-source-set component inventory,
  structured findings, and a reviewer-resolution queue contract.

Current readiness state after the 2026-05-01 downstream promotion:

- Full-source-set downstream artifacts for `source-set-ba8d0feae79501b8` are promoted through
  extraction, retrieval, evidence graph, claim extraction, rule-claim binding, coverage, gold eval,
  and phase eval.
- The current Custer Gallatin LMP component inventory for `source-set-ba8d0feae79501b8` has passing
  build coverage with `331` components, `58` standards, `0` missing component or standard IDs, and
  `0` duplicate component or standard IDs.
- `compliance-review` now invokes forest-plan context/component evaluation against the same package
  cache, requires the forest-plan component gate for Custer Gallatin packages, links
  `forest_plan_review` from the matrix summary, and adds forest-plan review/component-evaluation
  nodes to the finding graph.
- The prior `forest_service_directives_portal` / `R1EA-028` source-claim gap is closed through a
  general structural-definition claim pattern and refreshed rule-claim binding.
- Phase eval passes `8/8` phases with `reviewer_ready: true` for the active source set.

Remaining blockers to complete V1 Custer Gallatin real-package readiness:

- The real Custer Gallatin proving package still needs to be run through the updated
  `compliance-review` path and adjudicated before V1 can be called reviewer-ready for that EA.
- Component retrieval precision/recall and real-package failure taxonomy remain to be measured
  against the proving package.
- No generated V1 review artifact should be called fully reviewer-ready until current validation
  proves source-set, rule-pack, component, package, and finding graph alignment for that package.

## V1 Definition Of Done

V1 is done when the repository can reproduce a Custer Gallatin EA compliance review with these
properties:

- The package resolves to the Custer Gallatin profile or fails closed with an explicit out-of-scope or
  ambiguous status.
- The review uses the current active source set and validates that all required Custer Gallatin
  source records are indexed.
- Every baseline authority in the rule pack is evaluated.
- Every triggered conditional authority is evaluated or explicitly marked not applicable with a
  package-evidence basis.
- Every applicable Custer Gallatin plan standard has a compliance-status row.
- Every active component inventory record has an applicability status.
- Supported findings carry both source-library evidence and package evidence.
- Claim-bearing findings carry validated source-claim links, or they fail reviewer-ready status.
- The review emits JSON, Markdown, PDF, graph, validation, and reviewer-resolution artifacts.
- `phase-eval` passes for the selected V1 review ID, or every failed check is documented as a V1
  blocker rather than accepted residual risk.
- The final current-state docs and handoff identify exact review ID, package path, source-set ID,
  rule-pack version, profile ID, component inventory version, commands, verification results, and
  residual risks.

## Milestone 1: Pin The V1 Review Contract

Goal:
Define the exact Custer Gallatin EA package review that V1 must produce.

Non-goals:

- Do not add new code in this milestone.
- Do not choose multiple proving packages.
- Do not blur a demo-ready review with full Region 1 production readiness.

Deliverables:

- Confirmed package path:
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`.
- Confirmed V1 review mode:
  `forest-plan-resolve` plus `compliance-review`, with `ea-review` package extraction/review
  surfaces reused where the compliance review requires them.
- Stable review ID, source-set ID, rule-pack path/version, forest-plan profile ID, and component
  inventory path/version.
- Accepted residual risks for the first V1 run, if any.
- Updated `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md` if the selected contract
  changes current status or next steps.

Verification:

```bash
git diff --check
```

Stop conditions:

- The package path, source set, or review mode is ambiguous.
- The selected review would rely on stale source-set artifacts without explicit labeling.

## Milestone 2: Current Source-Set Downstream Readiness

Goal:
Promote the active 190-row source set far enough that compliance review can rely on current
authority evidence.

Non-goals:

- Do not redownload existing successful source rows unless artifact validation fails.
- Do not weaken retrieval, claim, or rule-link gates to make the review pass.
- Do not treat the Custer Gallatin seven-source retrieval slice as a complete compliance-review
  source index.

Deliverables:

- Reuse-first extraction assembly for `source-set-ba8d0feae79501b8`, including the one
  `needs_extract` source and all reusable prior extractions whose artifact hashes still match.
- Full retrieval index for the active source set with `reviewer_ready: true`.
- Evidence graph artifacts for the active source set.
- Source claim graph artifacts for the active source set.
- Rule-claim links for rule pack `nepa-ea-v0` version `0.4.0`.
- Resolved `R1EA-028` / `forest_service_directives_portal` source-claim support.
- Current `rule-claim-eval`, `compliance-coverage`, compliance-review-eval, compliance-gold-eval,
  and `phase-eval` evidence for the active source set.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_captured_library.py tests/test_retrieval.py tests/test_claim_extraction.py tests/test_rule_claim_link.py
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Retrieval summary remains `reviewer_ready: false`.
- Any baseline source record lacks current extraction/retrieval/claim support needed by its rule.
- Rule-claim binding records point to the old source set.

## Milestone 3: Complete Custer Gallatin Forest-Plan Component Inventory

Goal:
Create a current, source-traced Custer Gallatin component inventory sufficient for the East Crazies
NFMA project consistency review.

Non-goals:

- Do not handwrite only the components the EA happens to mention.
- Do not collapse multiple standards into broad topic records.
- Do not infer compliance status in the inventory itself.

Deliverables:

- Rebuildable component extraction or inventory-build command under
  `source_library/derived/<source_set_id>/forest_plan_components/`.
- `components.jsonl` and `components.sqlite` with one record per reviewable component in the active
  Custer Gallatin scope.
- First-class records for every applicable standard in the active plan scope.
- Records for guidelines, suitability, goals, desired conditions, objectives, monitoring direction,
  plan amendments, geographic areas, management areas, overlays, resource topics, and activity tags
  where relevant.
- `component_inventory_coverage.json` proving no skipped, duplicate, stale, or collapsed standard
  records.
- Tests proving stale source-set IDs and missing source chunks fail closed.

Current status:

- Implemented for the active Custer Gallatin LMP source record through `forest-plan-components-build`.
- Current generated inventory for `source-set-ba8d0feae79501b8` has `331` components and `58`
  standards from `536` selected chunks, with build coverage passing and no missing or duplicate
  component/standard IDs.
- Overlapping extraction chunks are merged when they carry the same component text from adjacent
  chunks; true duplicate labels in the same chunk still fail build coverage.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
git diff --check
```

Stop conditions:

- The inventory cannot prove that all standards in the active Custer Gallatin scope were captured.
- Component records cannot be traced to exact source text and source-record IDs.
- The inventory stores East Crazies conclusions instead of plan authority components.

## Milestone 4: Component Retrieval, Applicability, And NFMA Coverage Gates

Goal:
Prove the system can retrieve, select, and evaluate applicable Custer Gallatin plan components before
writing final findings.

Non-goals:

- Do not make broad `Forest Plan` or `plan consistency` language sufficient for applicability.
- Do not let unresolved candidate components disappear from outputs.
- Do not use graph links as decoration; they must support validation or reviewer navigation.

Deliverables:

- Component-aware retrieval over `components.sqlite` and the evidence index.
- `component_retrieval_eval.json` with positive and negative fixture cases.
- Component graph nodes/edges connecting forest unit, component, geography, management area, overlay,
  source record, package evidence, and finding.
- Applicability statuses for every inventory component:
  `applicable`, `candidate`, `not_applicable`, or `needs_reviewer_resolution`.
- `applicable_standard_coverage.json` proving every applicable standard has a package-evidence basis
  or reviewer-resolution item.
- Tests proving applicable standards are not omitted and non-applicable components are not pulled in
  merely because the package is on the Custer Gallatin.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_retrieval.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Component retrieval returns only document-level evidence.
- Applicable-standard recall is not measured independently.
- A missing component-source snippet can still produce a reviewer-ready finding.

## Milestone 5: Evidence-Backed NFMA Findings And Matrix

Goal:
Emit structured NFMA forest-plan findings for the Custer Gallatin EA package.

Non-goals:

- Do not present legal sufficiency conclusions.
- Do not mark a standard `complies` from a broad consistency assertion alone.
- Do not omit PDF output when claiming reviewer-ready NFMA matrix output.

Deliverables:

- `forest_plan_component_findings.json`
- `forest_plan_component_findings.md`
- `forest_plan_reviewer_resolution_queue.json`
- `forest_plan_nfma_compliance_matrix.json`
- `forest_plan_nfma_compliance_matrix.md`
- `forest_plan_nfma_compliance_matrix.pdf`
- Summary fields in `forest_plan_context_summary.json` for component count, applicable count,
  applicable standard count, compliance-status counts, reviewer-resolution count, and
  all-applicable-standards-applied status.
- Finding statuses:
  `supported`, `partial`, `gap`, `not_applicable`, `needs_reviewer_resolution`.
- Compliance statuses:
  `complies`, `potential_noncompliance`, `insufficient_evidence`, `not_applicable`,
  `needs_reviewer_resolution`, `guideline_equivalent_design`, `suitability_silent`.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- Markdown contains more complete readiness information than JSON.
- A supported/partial finding lacks either package evidence or plan-source evidence.
- Potential inconsistency is hidden without a reviewer-resolution item.

## Milestone 6: Integrate Forest-Plan Review Into Compliance Review

Goal:
Make Custer Gallatin NFMA component review a required phase of V1 `compliance-review`.

Non-goals:

- Do not keep forest-plan outputs as an optional side report when the EA resolves to Custer Gallatin.
- Do not duplicate package extraction unnecessarily when `--reuse-package-cache` is valid.
- Do not allow compliance review to pass when forest-plan component gates fail.

Deliverables:

- `compliance-review` invokes or consumes the forest-plan resolver/component evaluation for packages
  resolved to the selected profile.
- Compliance matrix output links to the forest-plan review/component artifacts through the
  `forest_plan_review` summary.
- Finding graph links the compliance review to `ForestPlanReview` and
  `ForestPlanComponentEvaluation` nodes where applicable.
- `compliance_validation.json` fails when required forest-plan component artifacts are missing,
  stale, or not reviewer-ready.
- Tests covering reviewer-ready, package-evidence gap, stale-source-set, and no-Custer-Gallatin or
  ambiguous-scope cases.

Current status:

- Implemented for selected-profile packages. The compliance review reuses the EA package cache,
  runs forest-plan resolution/component evaluation, and exposes
  `forest_plan_component_gate_reviewer_ready` in `compliance_validation.json`.
- Focused tests cover non-Custer/ambiguous scope, Custer reviewer-ready component evaluation, and
  stale component inventory fail-close behavior.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- `compliance-review` can pass while mandatory Custer Gallatin component gates fail.
- Forest-plan rows cannot be traced back to component IDs and source-record IDs.
- Existing non-forest-plan compliance review behavior regresses.

## Milestone 7: Run The Custer Gallatin V1 Compliance Review

Goal:
Produce the actual V1 compliance review artifacts for the East Crazy Inspiration Divide EA package.

Non-goals:

- Do not call the run complete if any current validation gate fails.
- Do not stage generated `source_library/` artifacts without an explicit repository-policy change.
- Do not hide unresolved reviewer work in the narrative report.

Required run:

```bash
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --docling-timeout-seconds 180
```

Deliverables:

- Package extraction manifest and chunks.
- Base EA review validation/report artifacts.
- Forest-plan context validation and summary.
- Forest-plan component findings, NFMA matrix, and reviewer-resolution queue.
- Compliance validation, compliance review JSON, compliance matrix JSON/Markdown/PDF, and finding
  graph nodes/edges.
- Concise run record with command, package path, review ID, source set, rule pack, profile, component
  inventory, validation result, and unresolved items.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src uv run --extra dev pytest tests/test_ea_review.py tests/test_compliance_review.py tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- `phase-eval` reports stale source-set, stale rule-pack, missing PDF, missing graph, or failed
  forest-plan component readiness.
- Any supported finding lacks source-library evidence, package evidence, or required source-claim
  links.
- The reviewer-resolution queue is empty only because unresolved evidence was omitted.

## Milestone 8: Practitioner Report And Handoff

Goal:
Close V1 with a practitioner-readable report and durable implementation handoff.

Non-goals:

- Do not rewrite generated evidence by hand.
- Do not claim legal sufficiency.
- Do not turn unresolved reviewer tasks into accepted residual risk unless the operator explicitly
  approves that boundary.

Deliverables:

- Report sections for supported findings, gaps, uncertain/candidate items, forest-plan component
  results, unresolved reviewer work, and residual risk.
- Plain-language summary that distinguishes source capture, reviewer-ready derived artifacts, V1
  Custer Gallatin proving-ground readiness, and deferred Region 1 production work.
- Updated `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/OUTPUT_SCHEMAS.md`, and
  `docs/SESSION_HANDOFF.md` as needed.
- Final verification record with commands, pass/fail counts, skipped checks, and residual risk.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- The final report implies the system replaces responsible official or counsel review.
- The final docs blur Custer Gallatin V1 readiness with full Region 1 production readiness.
- The final state cannot be reproduced from documented commands.

## Deferred Until After V1

- Additional Region 1 forest profiles beyond the profile-driven safety checks needed for Custer
  Gallatin.
- Broad real-world EA package adjudication beyond the V1 proving package and current seed/gold evals.
- Embeddings, semantic reranking, or model-generated synthesis trusted beyond deterministic evidence
  gates.
- Full operational UI or hosted service.
- Automated legal sufficiency determinations.

## Milestone Discipline

- Keep one milestone per commit.
- Stage only the verified milestone slice.
- Prefer current repo artifacts and generated validation over chat history.
- Prefer reuse-first, hash-verified rebuilds before broad redownloads.
- Report verification as command, result, skipped checks, and residual risk.
- Update `docs/SESSION_HANDOFF.md` at the end of substantial implementation sessions.

## Reference Sources For Expert Lenses

- USDA NEPA final rule, 91 FR 17062, effective April 3, 2026:
  https://www.federalregister.gov/documents/2026/04/03/2026-06537/national-environmental-policy-act
- USDA NEPA procedures, `7 CFR Part 1b`:
  https://www.ecfr.gov/current/title-7/subtitle-A/part-1b
- NFMA project/activity consistency, `36 CFR 219.15`:
  https://www.ecfr.gov/current/title-36/chapter-II/part-219/subpart-A/section-219.15
- Scott Vandegrift Forest Service engineering profile:
  https://www.fs.usda.gov/t-d/pubs/htmlpubs/htm14712830/page01.htm
- NAEP NEPA Practice Committee:
  https://www.naep.org/environmental-policy-committee
- NAEP NEPA speaker bio for Chuck Nicholson:
  https://naep.memberclicks.net/nepa-speaker-bios
- Liz Esposito public bio:
  https://www.bhfs.com/people/elisabeth-esposito/
