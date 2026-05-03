# V1 EA Gate Repair Milestone Plan

Date: 2026-05-03

This plan fixes the remaining `v1-ea-eval` blockers for the East Crazy Inspiration Divide V1
compliance review. It is intentionally scoped to the broader EA gate. Forest-plan scope,
component coverage, standard coverage, component adjudication, and phase-eval readiness are already
passing for the current review and should not be refactored as part of this sequence.

Current review contract:

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- Rule pack: `config/compliance_rule_pack_nepa_ea_v0.json`, `nepa-ea-v0` version `0.4.0`
- V1 eval contract: `config/v1_ecid_real_ea_eval.json`
- Original gate status: `v1-ea-eval` fails with `conditional_false_positive=3` and
  `rule_section_mismatch=2`

Current failing expectations:

- `nepa_statute_chapter_55`: baseline rule section mismatch. The rule is present and source-aligned
  to `R1EA-001`, but actual package section IDs are empty where the contract expects
  `purpose_need`.
- `nepa_4336b_programmatic_tiering`: conditional rule section mismatch. Applicability is
  adjudication-pending and source-aligned to `R1EA-005`, but actual sections are
  `biological_resources` and `cultural_resources` where the contract expects `alternatives` and
  `environmental_consequences`.
- `nepa_4336c_ce_adoption_screen`: conditional false positive. The review marks it applicable
  where the V1 contract expects `not_applicable`.
- `usda_nepa_ce_fanec_7cfr_1b3`: conditional false positive. The review marks it applicable where
  the V1 contract expects `not_applicable`.
- `usda_nepa_subcomponent_ce_7cfr_1b4`: conditional false positive. The review marks it applicable
  where the V1 contract expects `not_applicable`.

Progress through Milestone 3:

- Milestone 2 closed the three CE/FANEC conditional false positives without introducing conditional
  false negatives.
- Milestone 3 routes `nepa_statute_chapter_55` package evidence to purpose-and-need
  environmental-assessment text. The live V1 eval now reports `rule_source_section_expectations_met`
  passing and leaves only the `nepa_4336b_programmatic_tiering` section mismatch for Milestone 4.

## Sequence Rules

- Do not relax `config/v1_ecid_real_ea_eval.json` to make the gate pass.
- Do not remove the failing conditional expectations unless review evidence proves the contract is
  wrong and the correction is documented with package/source citations.
- Do not weaken rule-source, document-role, citation, forest-plan, component, or phase-eval gates.
- Do not regenerate or stage ignored `source_library/` artifacts unless repository policy changes.
- Commit each completed milestone as an atomic slice after verification passes.
- Push only when explicitly requested.

## Milestone 1: Lock The Failure Reproduction

Goal:
Make the current V1 EA failures easy to reproduce and diagnose before changing rule behavior.

Non-goals:

- Do not change applicability logic, rule-pack trigger terms, or section routing.
- Do not update generated review artifacts.

Relevant files or surfaces:

- `source_library/reviews/v1-cg-ecid-compliance-review/v1_ea_eval_results.json`
- `config/v1_ecid_real_ea_eval.json`
- `src/usfs_r1_ea_sources/v1_ea_eval.py`
- `tests/test_v1_ea_eval.py`
- `docs/SESSION_HANDOFF.md`

Deliverables:

- A compact diagnostic test or helper assertion that names the five current failing expectations.
- If needed, a small `v1-ea-eval` output summary improvement that surfaces failed rule IDs without
  requiring manual `jq` inspection.
- Handoff note confirming the repair baseline: three CE false positives and two section mismatches.

Required eval signal:

- `v1-ea-eval` still fails for the same five reasons.
- No new failure category appears.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_v1_ea_eval.py
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
git diff --check
```

Commit policy:
Commit the diagnostic/documentation slice only after the focused test passes and `v1-ea-eval`
confirms the unchanged failure baseline.

Stop conditions:

- The current generated review no longer matches `review_id`, `source_set_id`, or rule-pack version.
- `v1-ea-eval` reports different failures than the current known baseline.

## Milestone 2: Fix CE Conditional Applicability

Goal:
Stop categorical-exclusion authority rows from becoming applicable merely because the package
mentions categorical exclusions, FANEC, extraordinary circumstances, FONSI, or level-of-review
language in a non-CE EA context.

Non-goals:

- Do not make CE rules unreachable. They must still trigger when a package actually adopts,
  evaluates, or relies on a CE/FANEC path.
- Do not make package text absence the only basis for `not_applicable`; require explicit negative
  or non-triggering evidence where possible.

Relevant files or surfaces:

- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/compliance_rule_pack_coverage_nepa_ea_v0.json`
- `config/compliance_review_eval_seed.json`
- `config/compliance_gold_eval_v0.json`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `tests/test_compliance_review.py`
- `tests/test_v1_ea_eval.py`

Implementation direction:

- Add explicit trigger semantics for CE rules: distinguish an EA discussing why CE is not the chosen
  path from a package that actually uses, adopts, or must screen a CE/FANEC.
- Require stronger positive cues for:
  - `nepa_4336c_ce_adoption_screen`
  - `usda_nepa_ce_fanec_7cfr_1b3`
  - `usda_nepa_subcomponent_ce_7cfr_1b4`
- Preserve negative fixtures proving those three rules remain `not_applicable` for the East
  Crazies EA.
- Preserve positive fixtures proving the same rules still become applicable for CE/FANEC packages.

Required eval signal:

- The three CE false positives are gone.
- Conditional false negatives remain `0`.
- Compliance review eval and gold eval still pass.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_v1_ea_eval.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
git diff --check
```

Commit policy:
Commit this slice only if CE false positives are removed without breaking positive CE/FANEC
coverage fixtures.

Stop conditions:

- Any baseline authority disappears from the compliance matrix.
- Any CE/FANEC positive fixture stops triggering without an adjudicated rule-pack change.
- The V1 gate replaces CE false positives with CE false negatives.

## Milestone 3: Fix Baseline Rule Section Attribution

Goal:
Bind `nepa_statute_chapter_55` to the package section evidence expected by the V1 contract instead
of reporting no package section.

Non-goals:

- Do not special-case the rule ID only to satisfy the V1 contract.
- Do not infer a section from document title alone when package evidence has no supporting text.

Relevant files or surfaces:

- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/v1_ea_eval.py`
- `config/compliance_rule_pack_nepa_ea_v0.json`
- `config/v1_ecid_real_ea_eval.json`
- `tests/test_compliance_review.py`
- `tests/test_v1_ea_eval.py`

Implementation direction:

- Trace why the current finding for `nepa_statute_chapter_55` has package evidence but no recognized
  `purpose_need` section.
- Prefer a general section attribution repair, such as carrying normalized package section families
  from package evidence into the compliance matrix and finding graph.
- If the existing package evidence is too generic, tighten the rule's package query/terms so the
  finding selects the purpose-and-need evidence already detected by the V1 section detector.
- Add a regression test proving the baseline rule section is recovered from evidence text, not from
  rule ID.

Required eval signal:

- `nepa_statute_chapter_55` passes with `actual_package_section_ids` containing `purpose_need`.
- Baseline source-record and document-role match rates remain `1.0`.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_v1_ea_eval.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
git diff --check
```

Commit policy:
Commit only the general section-attribution repair, targeted tests, and any matching rule-pack/doc
updates.

Stop conditions:

- The repair broadens section matching so unrelated rules pass through incidental section terms.
- `citation_requirement_match_rate` drops below `1.0`.

## Milestone 4: Fix Programmatic-Tiering Section Routing

Goal:
Route `nepa_4336b_programmatic_tiering` evidence to the alternatives/environmental-consequences
context expected by the V1 contract instead of biological/cultural sections.

Non-goals:

- Do not force a final legal applicability conclusion. The current contract marks applicability as
  `adjudicate`.
- Do not drop the rule just to avoid the section mismatch.

Relevant files or surfaces:

- `config/compliance_rule_pack_nepa_ea_v0.json`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/v1_ea_eval.py`
- `tests/test_compliance_review.py`
- `tests/test_v1_ea_eval.py`

Implementation direction:

- Inspect the selected package evidence for tiering/programmatic cues and identify why biological
  and cultural chunks outrank alternatives or environmental-consequences chunks.
- Strengthen package evidence ranking with section-aware boosts for rule-declared expected sections.
- Keep `adjudication_pending=true` where the contract requires human review, but require source and
  section alignment for any actual applicable conditional result.
- Add a regression fixture where a conditional rule has correct source evidence but wrong package
  section; the V1 gate must fail until routing is fixed.

Required eval signal:

- `nepa_4336b_programmatic_tiering` still appears for adjudication, remains source-aligned to
  `R1EA-005`, and passes section alignment.
- The broader EA lane has no remaining `rule_section_mismatch`.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_v1_ea_eval.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
git diff --check
```

Commit policy:
Commit only after the programmatic-tiering mismatch is fixed and Milestone 2/3 regressions remain
closed.

Stop conditions:

- The rule disappears rather than becoming correctly section-aligned.
- The actual applicable conditional source-record match rate drops below `1.0`.

## Milestone 5: Close Conditional Adjudication Coverage

Goal:
Turn the current conditional-rule state from sparse adjudication into a reviewable, gate-facing
contract for the real EA.

Non-goals:

- Do not require legal conclusions from the system.
- Do not block V1 on broad Region 1 production readiness.

Relevant files or surfaces:

- `config/v1_ecid_real_ea_eval.json`
- `src/usfs_r1_ea_sources/v1_ea_eval.py`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/SESSION_HANDOFF.md`
- `tests/test_v1_ea_eval.py`

Implementation direction:

- Review all 18 conditional expectations and classify each as `applicable`, `not_applicable`, or
  `adjudicate` with a source/package evidence rationale.
- Decide whether the V1 gate should allow an `adjudicate` expectation to pass with pending status
  when source and section alignment are correct, or whether V1 requires an explicit adjudication
  artifact for every pending conditional.
- If conditional adjudication remains pending, make the pending count an explicit accepted V1 risk
  in docs and output. If not accepted, add a conditional-adjudication artifact/eval loop analogous
  to the forest-plan component adjudication loop.

Required eval signal:

- No false positives or false negatives remain.
- No unclassified conditional rules remain hidden behind a pass result.
- Any remaining `adjudicate` rows are explicit and visible in V1 output.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_v1_ea_eval.py
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
git diff --check
```

Commit policy:
Commit after the conditional adjudication policy is encoded in the eval contract, tests, and docs.

Stop conditions:

- Pending conditional adjudications are treated as resolved without explicit evidence.
- The V1 gate can pass while hiding material applicability uncertainty.

## Milestone 6: Final V1 Gate Promotion

Goal:
Regenerate the current review artifacts and promote the V1 EA gate only after the broader EA and
forest-plan lanes both pass.

Non-goals:

- Do not broaden the claim to all Region 1 forests.
- Do not stage generated `source_library/` outputs unless repository policy changes.

Relevant files or surfaces:

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`
- `README.md`
- Focused source/test/config changes from prior milestones

Required eval signal:

- `v1-ea-eval` reports `passed=true`, `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `phase-eval --review-id v1-cg-ecid-compliance-review` still reports all phases passing.
- Compliance review eval and gold eval remain promotion-ready.

Required tests:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/forest_plan_component_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit docs, tests, configs, and implementation changes that describe and prove the V1 gate repair.
Do not include ignored generated review artifacts unless the repository policy is changed explicitly.

Stop conditions:

- Any source-set, rule-pack, compliance validation, forest-plan, phase-eval, or V1 EA eval identity
  check fails.
- `v1-ea-eval` passes only because expectations were weakened rather than because evidence routing
  and applicability improved.
- Full tests or lint fail for reasons related to the V1 repair.
