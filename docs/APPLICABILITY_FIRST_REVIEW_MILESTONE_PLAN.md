# Applicability-First Review Milestone Plan

Date: 2026-05-04

This plan defines the post-V1 architecture change needed to make legal-authority applicability a
first-class, pre-review stage. The critical system function is not merely to evaluate a static rule
pack. The system must first determine which laws, regulations, policies, Forest Plan requirements,
and supporting authorities apply to the EA package, produce auditable artifacts for both applicable
and non-applicable authorities, validate those determinations, generate the review rule pack from
the validated applicability result, and only then run the compliance review.

## Target Invariant

No compliance review should run directly from the standing authority corpus or from a hand-selected
rule pack. The review sequence must be:

```text
EA package + source library + authority universe
  -> applicability determination
  -> applicable_authorities artifact
  -> non_applicable_authorities artifact
  -> applicability validation and adjudication gate
  -> generated review rule pack
  -> compliance review
```

The compliance review stage must consume the generated review rule pack and the validated
applicability run identity. It must not decide whether laws, regulations, or policies apply.

## Current Gap

The current V1 path is authority-first, but applicability is still coupled to `compliance-review`.
The command reads `config/compliance_rule_pack_nepa_ea_v0.json`, evaluates baseline rules, marks
conditional rules applicable or not applicable, and emits a matrix that includes both review
findings and not-applicable authority rows.

That is not strong enough for the final reviewer. Applicability needs to be promoted into its own
reviewable phase with durable outputs and gates before compliance findings are generated.

## System Requirements

- The authority universe must be explicit. It should include every candidate law, regulation,
  policy, Forest Plan component, source record, authority category, document role, trigger
  contract, currentness metadata, and required source-claim linkage available to the reviewer.
- Applicability determination must be a separate command and artifact family. It should inspect the
  EA package, source-library authority evidence, forest-plan profile, package context, and package
  sections before any compliance status is evaluated.
- Applicable authorities must be written to a first-class artifact with one decision record per
  authority and cited evidence for why the authority applies.
- Non-applicable authorities must be written to a separate first-class artifact with one decision
  record per authority and cited affirmative negative evidence, absence rationale, explicit trigger
  miss, or reviewer adjudication for why the authority does not apply.
- Unresolved authorities must block review. The system may emit an adjudication queue, but it must
  not silently treat unresolved applicability as applicable or not applicable.
- The generated review rule pack must be derived from the validated applicable-authorities artifact.
  It should include only authorities approved for review, plus metadata linking back to the
  applicability run, source set, package identity, authority universe version, and validation hash.
- `compliance-review` must refuse to run unless the generated rule pack and applicability validation
  are present, current, and mutually consistent.
- The compliance matrix should evaluate compliance only for generated applicable rules. A combined
  reviewer report can link to not-applicable authorities, but non-applicability should not be buried
  as ordinary compliance rows.

## New Artifact Contract

All artifacts should live under:

```text
source_library/reviews/<review_id>/applicability/
```

Required artifacts:

- `authority_universe_snapshot.json`
  - candidate authority set considered for the package
  - source set ID, catalog hash, authority source records, rule-template IDs, Forest Plan profile
    IDs, component inventory IDs, and currentness metadata
- `package_applicability_context.json`
  - extracted package facts used for applicability
  - package manifest hash, package section map, project type, federal action signals, forest unit,
    geography, management areas, overlays, consultations, permits, public involvement, decision
    posture, and supporting document signals
- `applicability_decisions.jsonl`
  - one row per candidate authority
  - decision status: `applicable`, `not_applicable`, `unresolved`, or `needs_adjudication`
  - decision basis, evidence spans, negative evidence spans, missing evidence, source-record IDs,
    package chunk IDs, confidence classification, and adjudication state
- `applicable_authorities.json`
  - only authorities selected for review
  - evidence-backed applicability basis and generated-rule metadata
- `non_applicable_authorities.json`
  - only authorities excluded from review
  - cited non-applicability basis, negative trigger evidence, absent-trigger rationale, or
    adjudicator decision
- `applicability_validation.json`
  - machine gate proving complete candidate coverage, artifact consistency, source freshness,
    evidence requirements, no unresolved decisions, and generated-rule-pack readiness
- `applicability_report.md`
  - reviewer-facing summary of applicable, non-applicable, unresolved, and adjudicated decisions
- `generated_rule_pack.json`
  - the only rule pack accepted by the downstream compliance review

Optional but expected once adjudication is introduced:

- `applicability_adjudication_template.json`
- `applicability_adjudication_worklist.md`
- `applicability_adjudication_eval.json`

## Milestone 1: Applicability Contract And Schemas

Goal:
Define the artifact contract and gate semantics before implementation.

Non-goals:

- Do not change `compliance-review` behavior yet.
- Do not regenerate source-library artifacts.
- Do not broaden the authority corpus in this milestone.

Relevant files or surfaces:

- `docs/OUTPUT_SCHEMAS.md`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`
- `config/compliance_rule_pack_nepa_ea_v0.json`

Deliverables:

- Document the new artifact schemas listed above.
- Define decision statuses, required evidence fields, and freshness/hash fields.
- Define the generated rule-pack identity fields:
  - `base_rule_pack_id`
  - `base_rule_pack_version`
  - `generated_rule_pack_id`
  - `applicability_run_id`
  - `applicability_validation_sha256`
  - `authority_universe_sha256`
  - `package_manifest_sha256`
  - `source_set_id`
  - `review_id`
- Define hard validation failures:
  - candidate authority missing from both applicable and non-applicable artifacts
  - authority present in both artifacts
  - unresolved or needs-adjudication authority still present
  - non-applicable authority has no basis
  - applicable authority has no package/source basis unless explicitly baseline-required and
    baseline-required status is itself evidenced
  - generated rule pack does not match applicable-authorities artifact
  - generated rule pack is stale relative to package, source set, or authority universe

Required eval signal:

- The plan and schema docs make clear that applicability happens before compliance review.
- The non-applicable artifact is separate from the review matrix.

Required tests:

```bash
git diff --check
```

Commit policy:
Commit this docs-only contract as an atomic planning slice.

Stop conditions:

- The schema still allows `compliance-review` to be the first place where applicability is decided.
- The non-applicable artifact is optional or merged only into the compliance matrix.

## Milestone 2: Authority Universe Snapshot

Goal:
Build the complete candidate authority universe used by applicability determination.

Non-goals:

- Do not decide package applicability in this milestone.
- Do not run compliance review.
- Do not fetch new sources unless a missing source blocks the authority universe contract.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/cli.py`
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/forest_plan_profiles.json`
- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/derived/<source_set_id>/claims/claims.jsonl`
- `source_library/derived/<source_set_id>/rule_claim_links/`
- `tests/test_compliance_review.py`

Implementation direction:

- Add an authority-universe builder that reads the base rule pack, catalog authority metadata,
  forest-plan profile, component inventory, source-claim links, and source currentness.
- Emit `authority_universe_snapshot.json` with one candidate authority record per rule-template or
  Forest Plan component candidate.
- Include all candidate authorities, not only baseline or likely-triggered authorities.
- Validate that every candidate has source-record identity, document role, authority category,
  source evidence availability, and a deterministic applicability test contract.

Required eval signal:

- The current `44` authority rules are represented in the snapshot.
- Custer Gallatin Forest Plan candidates are represented through profile/component inventory
  references rather than hardcoded runtime branches.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the authority-universe implementation, tests, and schema docs together.

Stop conditions:

- Candidate authorities are inferred by scanning raw filenames.
- The universe omits conditional authorities because they are not expected to apply.
- A candidate lacks source-record provenance or an applicability test contract.

## Milestone 3: Applicability Determination Command

Goal:
Add a pre-review command that determines applicability and writes all first-class applicability
artifacts without producing compliance findings.

Non-goals:

- Do not evaluate compliance status.
- Do not emit `pass`, `gap`, or `uncertain` compliance findings.
- Do not allow unresolved applicability decisions through as review-ready.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/cli.py`
- new applicability module under `src/usfs_r1_ea_sources/`
- existing package extraction and section-detection helpers
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `tests/test_compliance_review.py`
- new focused applicability tests

Implementation direction:

- Add a command such as:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id <source-set-id> \
  --review-id <review-id>
```

- Reuse package extraction/cache and forest-plan context resolution, but keep the output under
  `applicability/`.
- Emit:
  - `package_applicability_context.json`
  - `applicability_decisions.jsonl`
  - `applicable_authorities.json`
  - `non_applicable_authorities.json`
  - `applicability_report.md`
- Record separate bases for:
  - mandatory baseline applicability
  - positive package triggers
  - explicit negative package evidence
  - absent trigger evidence
  - forest-plan profile resolution
  - Forest Plan component applicability
  - human adjudication
- Treat weak or contradictory evidence as `needs_adjudication`, not as a reviewable decision.

Required eval signal:

- The East Crazy package produces applicable and non-applicable artifacts before review.
- The current CE/FANEC non-applicable decisions are recorded in
  `non_applicable_authorities.json`, not only as matrix rows.
- The `14` currently pending conditional rows become explicit `needs_adjudication` or adjudicated
  decisions and block generated-rule-pack readiness until resolved.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the command, focused tests, and docs only after the command produces first-class
applicability artifacts.

Stop conditions:

- Applicability output depends on compliance findings.
- Non-applicable authorities lack evidence or explicit no-trigger rationale.
- Pending conditional applicability is accepted as review-ready.

## Milestone 4: Applicability Validation And Adjudication Gate

Goal:
Make applicability validation a hard gate that must pass before a generated rule pack can be used.

Non-goals:

- Do not rely on manual inspection without a machine-readable adjudication record.
- Do not downgrade unresolved authorities to not-applicable for convenience.
- Do not let `compliance-review` override the applicability gate.

Relevant files or surfaces:

- applicability artifacts from Milestone 3
- `phase-eval`
- `compliance-review-eval`
- new applicability eval fixture under `config/`
- focused tests for validation failure modes

Implementation direction:

- Add `applicability-validate`.
- Add `applicability-adjudication-template` and `applicability-adjudication-eval` if unresolved
  decisions exist.
- Validation must prove:
  - every authority in the universe has exactly one decision row
  - applicable and non-applicable artifacts partition the candidate universe after adjudication
  - no unresolved authority remains
  - every applicable decision has source and package evidence or an explicitly validated mandatory
    basis
  - every non-applicable decision has negative evidence, no-trigger evidence, or adjudication
  - Forest Plan profile/component applicability has required source and package context
  - artifact hashes match current package/source-set inputs
- Add failure taxonomy:
  - `missing_candidate_decision`
  - `duplicate_decision`
  - `applicable_evidence_gap`
  - `non_applicable_basis_gap`
  - `contradictory_package_evidence`
  - `forest_plan_scope_unresolved`
  - `source_set_stale`
  - `package_cache_stale`
  - `adjudication_missing`

Required eval signal:

- A package with pending conditional rows fails validation until adjudicated.
- A non-applicable decision without evidence or rationale fails validation.
- A stale applicability artifact fails validation.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit validation, adjudication tooling, tests, and schema updates together.

Stop conditions:

- Validation passes with unresolved applicability decisions.
- Validation passes when a candidate authority is absent from both first-class artifacts.
- Adjudication cannot be replayed deterministically.

## Milestone 5: Generated Rule Pack

Goal:
Generate the review rule pack from the validated applicable-authorities artifact.

Non-goals:

- Do not hand-edit generated rule packs.
- Do not include non-applicable authorities in the generated review rule pack.
- Do not preserve baseline rules by default unless their applicability decision has passed the
  applicability gate.

Relevant files or surfaces:

- `config/compliance_rule_pack_nepa_ea_v0.json`
- applicability artifacts
- `validate_rule_pack`
- rule-claim binding validation
- compliance coverage validation

Implementation direction:

- Add `applicability-generate-rule-pack`.
- The generated rule pack should contain only validated applicable authorities.
- Each generated rule must carry:
  - base rule ID
  - generated rule ID if transformed
  - applicability decision ID
  - applicability evidence references
  - source-record IDs
  - document roles
  - source-claim link requirements
  - package-section expectations
  - Forest Plan component references when relevant
- Emit `generated_rule_pack.json` under the applicability directory.
- Emit `generated_rule_pack_validation.json`.
- Preserve a hash of the exact applicable-authorities artifact used to generate it.
- Fail if source-claim links are missing for claim-bearing generated rules.

Required eval signal:

- Generated rule-pack rule count equals validated applicable-authority count.
- Non-applicable authorities are absent from generated rules and present only in
  `non_applicable_authorities.json`.
- Rule-pack validation fails if the generated pack is edited by hand or stale relative to
  applicability artifacts.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack source_library/reviews/<review_id>/applicability/generated_rule_pack.json \
  --eval-file config/rule_claim_link_eval_seed.generated.json
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit generated-rule-pack implementation and tests after validation proves derived identity and
staleness checks.

Stop conditions:

- Generated pack can drift from applicability artifacts without detection.
- Non-applicable authorities can appear in generated rules.
- Review can run against the base rule pack instead of the generated pack.

## Milestone 6: Gate Compliance Review Behind Generated Rule Pack

Goal:
Refactor `compliance-review` so review can only occur after applicability validation and generated
rule-pack creation.

Non-goals:

- Do not remove the base authority rule pack. It remains the candidate authority template.
- Do not lose the ability to produce a combined reviewer-facing report.
- Do not use the review matrix as the source of truth for non-applicability.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/cli.py`
- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `tests/test_compliance_review.py`

Implementation direction:

- Replace direct review use of `--rule-pack config/...` with a generated-pack path plus
  applicability-run reference.
- For transition, allow an explicit diagnostic flag such as `--allow-base-rule-pack-review`, but
  keep it non-reviewer-ready and excluded from promotion gates.
- Make `compliance-review` validate:
  - generated rule pack exists
  - applicability validation passed
  - generated pack hash matches applicability validation
  - package manifest hash matches
  - source set matches
  - non-applicable artifact exists and validates
- Change compliance matrix semantics:
  - compliance findings evaluate generated applicable rules only
  - matrix summary links to `non_applicable_authorities.json`
  - combined Markdown/PDF report may include a separate non-applicable section, but it must cite the
    applicability artifact as source of truth

Required eval signal:

- `compliance-review` refuses to run against the base pack in reviewer-ready mode.
- `compliance-review` refuses to run when non-applicable artifacts are missing.
- The existing V1 package can complete the new sequence only after applicability artifacts,
  validation, and generated pack exist.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:
Commit the review gate refactor only after the full local sequence passes.

Stop conditions:

- `compliance-review` still decides applicability.
- A review can be promoted without validated non-applicable artifacts.
- The matrix can be mistaken as the source artifact for non-applicability.

## Milestone 7: Applicability Evaluation And Promotion Gates

Goal:
Add eval coverage that proves applicability decisions are correct before compliance quality is
scored.

Non-goals:

- Do not treat generated review success as proof of applicability correctness.
- Do not rely only on synthetic all-authorities fixtures.
- Do not broaden Region 1 readiness without real-package adjudication.

Relevant files or surfaces:

- new `config/applicability_eval_seed.json`
- new `config/applicability_gold_eval_v0.json`
- `phase-eval`
- `v1-ea-eval`
- `compliance-review-eval`
- `compliance-gold-eval`

Implementation direction:

- Add `applicability-eval` for deterministic seed packages.
- Add `applicability-gold-eval` for adjudicated real or realistic packages.
- Each eval case must cover:
  - full candidate authority universe
  - expected applicable authorities
  - expected non-applicable authorities
  - expected unresolved/adjudication cases when allowed by the fixture
  - source-record and document-role alignment
  - package-section alignment
  - negative evidence and no-trigger rationale
  - generated rule-pack identity and counts
- Update `phase-eval` to include:
  - `authority_universe`
  - `applicability_determination`
  - `applicability_validation`
  - `generated_rule_pack`
  - then existing compliance phases

Required eval signal:

- Applicability eval fails on false positives, false negatives, missing non-applicable rows, stale
  artifacts, and generated-rule-pack mismatch.
- Compliance eval no longer needs to score non-applicable rows as compliance findings.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/applicability_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit eval fixtures, commands, phase gates, docs, and focused tests together.

Stop conditions:

- Applicability eval can pass without checking the non-applicable artifact.
- Phase eval can report reviewer-ready when applicability validation is missing or stale.
- Generated rule-pack coverage is not tied back to applicable-authority decisions.

## Milestone 8: Real-Package Expansion And Operating Runbook

Goal:
Prove the applicability-first architecture on a broader set of real EA packages and document the
operator workflow.

Non-goals:

- Do not claim full Region 1 production readiness from one package.
- Do not add more forest profiles without profile-specific source readiness and eval coverage.
- Do not use model prose as an adjudication substitute.

Relevant files or surfaces:

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- real package intake directories under `source_library/reviews/_intake/`
- applicability and compliance eval artifacts

Implementation direction:

- Select a small real-package set covering:
  - Custer Gallatin
  - at least one additional Region 1 forest profile once implemented
  - ESA/NHPA/MBTA/Roadless/wetlands negative and positive cases
  - missing or ambiguous package evidence
  - Forest Plan component positives and hard negatives
- Run the full sequence for each package.
- Adjudicate applicability before reviewing compliance.
- Record false positives, false negatives, retrieval misses, source gaps, and ambiguous evidence.
- Update docs with exact command sequence and current readiness boundary.

Required eval signal:

- At least one package passes the full applicability-first plus compliance-review sequence.
- At least one adjudicated package intentionally fails readiness because applicability remains
  unresolved.
- Metrics report applicability precision/recall, non-applicable correctness, generated rule-pack
  consistency, and downstream compliance review quality separately.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit code/docs/eval fixtures as one milestone slice. Do not stage ignored generated
`source_library/` artifacts unless repository policy changes.

Stop conditions:

- Real-package coverage exposes unadjudicated applicability uncertainty that the system cannot
  represent.
- Operator docs imply generated compliance findings are legal conclusions.
- Forest Plan profile expansion lacks source readiness or validation artifacts.

## Target CLI Sequence

The final operator path should look like this:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --package-path /path/to/ea-package \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id <source-set-id> \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id <review-id>

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /path/to/ea-package \
  --output-dir source_library \
  --rule-pack source_library/reviews/<review_id>/applicability/generated_rule_pack.json \
  --source-set-id <source-set-id> \
  --review-id <review-id> \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id <review-id>
```

## Completion Definition

This architecture is complete when:

- every candidate authority is represented in the authority universe;
- every candidate authority has exactly one validated applicability decision;
- applicable authorities and non-applicable authorities are separate durable artifacts;
- unresolved applicability blocks review;
- generated review rule packs are derived only from validated applicable authorities;
- compliance review refuses reviewer-ready execution without a valid applicability run;
- phase eval includes applicability and generated-rule-pack gates before compliance gates; and
- real-package evals score applicability quality separately from compliance-review quality.
