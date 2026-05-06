# EA Consistency Decision Support Milestone Plan

Date: 2026-05-06

This milestone closes the gap between the current reviewer-ready evidence artifacts and a single
Forest Supervisor-facing decision-support document for the East Crazy Inspiration Divide EA. The
current system has the defensible evidence base: generated applicability artifacts, a generated
compliance matrix, Forest Plan component findings, applicable-standard coverage, non-applicable
authority artifacts, reviewer-resolution reports, and validation gates. The missing product is a
generated, auditable synthesis that a Custer Gallatin National Forest decision maker can read as a
complete EA consistency support document.

The milestone is scoped to report synthesis over existing audited artifacts. It does not reopen the
EA decision, rerun network capture, broaden Region 1 readiness, or replace responsible official,
line officer, counsel, or specialist judgment.

## Goal

Generate a supervisor-facing EA consistency decision-support document for
`v1-cg-ecid-compliance-review` that tracks every law, regulation, executive order, policy,
state/SHPO requirement, case-law review lens, and Forest Plan component the system considered, while
clearly separating:

- applicable authorities with compliance findings;
- non-applicable authorities with search coverage and rationale;
- Forest Plan components and applicable standards;
- implementation confirmations and residual risks;
- machine evidence from reviewer-facing synthesis.

The output should be suitable as decision support for a Forest Supervisor on the Custer Gallatin
National Forest because it is complete, traceable, bounded, and candid about implementation
conditions.

## Non-Goals

- Do not create legal advice or a final legal sufficiency determination.
- Do not treat manual root-level exports as canonical pipeline outputs.
- Do not overwrite generated review evidence unless the implementation explicitly regenerates the
  decision-support report from current artifacts.
- Do not rerun downloader, catalog, extraction, retrieval, source-claim, or compliance workflows
  unless a later implementation sequence proves the current artifacts are stale.
- Do not broaden claims beyond the East Crazy Inspiration Divide proving review.
- Do not stage ignored `source_library/` outputs unless repository policy changes explicitly.
- Do not hide non-applicable authorities or collapse them into a sentence-level disclaimer.

## Current Gap

The current repository already proves the core review state for
`v1-cg-ecid-compliance-review`:

- `33` generated applicable authority findings, all passing;
- `340` non-applicable authorities retained in the applicability artifacts and appendix;
- `329` Custer Gallatin Land Management Plan component findings;
- `79` applicable/supported Forest Plan components and `250` not-applicable components;
- `12` applicable Forest Plan standards and `12` applied standards;
- no current reviewer-resolution items for the promoted V1 review;
- passing review, compliance, applicability, generated-rule-pack, Forest Plan context, component
  eval, V1 EA eval, phase-eval, and promotion gates in the current system-state record.

The gap is presentation and contract ownership:

- the root-level East Crazies narrative and matrix are useful manual drafts, but they explicitly say
  they are not repo pipeline outputs;
- the generated `compliance_matrix.md/.pdf` is auditable but reads like a raw evidence matrix;
- the Forest Plan component findings are complete but too large and too granular to function alone
  as an executive decision-support document;
- implementation confirmations and residual risks are not yet a first-class generated report
  section tied to source artifacts;
- non-applicable authority coverage is not summarized in a way a supervisor can quickly inspect
  without losing the full appendix.

## Preflight Prerequisite

Before Sequence 1 begins, complete
`docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md`. That preflight is the Sequence 0 gate for
this milestone. It verifies the current review boundary, required artifact presence, artifact hash
baseline, count baseline, phase-eval and promotion-suite readiness, Plan Consistency Table
ownership, manual-draft quarantine, residual-risk/checklist source mapping, and the chosen
CLI/module/renderer implementation surface.

Do not start the report contract or generator work if the preflight result is `stop`. Convert the
blocker into a scoped follow-up milestone instead of patching around it inside the decision-support
report.

## Target Artifact Contract

Implement a generated artifact family under:

```text
source_library/reviews/<review_id>/decision_support/
```

Required files:

- `ea_consistency_decision_support.json`
- `ea_consistency_decision_support.md`
- `ea_consistency_decision_support.pdf`
- `ea_consistency_decision_support_manifest.json`

The JSON is the canonical machine-readable report. Markdown and PDF are renderings from the JSON.
The manifest records input artifact paths, source-set ID, review ID, package manifest hash,
applicability artifact hashes, compliance matrix hash, Forest Plan component artifact hash,
non-applicable authority artifact hash, generation timestamp, generator version, and validation
status.

The document must include these sections:

1. Executive determination:
   concise status, review boundary, and decision-use caveat.
2. Record and artifact inventory:
   EA package records, source set, generated rule pack, review ID, and validation state.
3. Applicable authority summary:
   grouped counts and rows for laws, regulations, executive orders, agency policies, state/SHPO
   requirements, and case-law review lenses.
4. Authority findings:
   every applicable authority with source record, authority family, applicability basis,
   compliance status, EA evidence citation, source evidence citation, source-claim IDs, limitations,
   and required implementation confirmation if any.
5. Forest Plan consistency:
   Plan Consistency Table source identity; component counts; applicable component counts by type;
   topic/designation summary; and trace links to all Forest Plan component findings.
6. Applicable Forest Plan standards:
   all applicable standards, compliance status, package evidence, plan source evidence, and
   implementation commitment.
7. Non-applicable authority boundary:
   summary by authority family/category plus a pointer to the full non-applicable authority
   appendix and coverage certificates.
8. Implementation confirmation checklist:
   closing instruments, deed restrictions, easements, appraisal/equalization/title file,
   NHPA MOA/mitigation, wetland protections, ESA/botany/whitebark/trail controls, access terms,
   and any construction-phase commitments.
9. Residual risk register:
   decision-support risks separated from compliance findings, with each risk tied to evidence or a
   stated implementation confirmation.
10. Validation and replay instructions:
   commands and artifact hashes needed to verify the report was generated from current review
   artifacts.

## Defensibility Standard

The report is defensible when an independent reviewer can answer these questions from the report and
linked artifacts:

- What authority universe was considered?
- Which authorities applied and why?
- Which authorities did not apply and what coverage supports that boundary?
- What Forest Plan components and standards were considered?
- Which plan components were applicable, not applicable, or standards requiring compliance status?
- What EA package evidence and source-library evidence support each finding?
- What implementation commitments remain before closing or construction?
- What residual risks are evidence-backed decision-support notes rather than unsupported legal
  conclusions?
- Can the document be regenerated from durable artifacts without relying on manual prose?

The report must fail closed when required current artifacts are missing, stale, hash-mismatched, or
not reviewer-ready.

## Sequence 1: Report Contract And Fixtures

Goal:
Define the decision-support report schema and lock the East Crazies proving expectations.

Implementation scope:

- Add or extend output schema documentation for the decision-support artifact family.
- Add a small fixture or expected-summary contract for `v1-cg-ecid-compliance-review`.
- Define report fields for authority rows, Forest Plan rows, applicable standards, non-applicable
  authority summaries, implementation confirmations, residual risks, and validation metadata.

Acceptance criteria:

- Schema documents required files, required fields, source artifact dependencies, and fail-closed
  conditions.
- Tests validate the contract with a small fixture before the real report generator exists.
- The schema distinguishes compliance status, applicability status, implementation confirmation,
  and residual risk.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest <focused decision-support schema tests>
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

Commit policy:
Commit Sequence 1 as a focused schema/fixture/doc commit.

## Sequence 2: Report Generator

Status: complete.

Goal:
Implement a deterministic generator that reads existing audited review artifacts and writes the
decision-support JSON/Markdown/PDF family.

Implementation scope:

- Add a CLI command such as `ea-consistency-document` or
  `decision-support-report`.
- Read only review/corpus surfaces, not raw artifact filename scans.
- Require passing current artifacts:
  - `compliance_matrix.json`;
  - `applicability/applicable_authorities.json`;
  - `applicability/non_applicable_authorities.json`;
  - `applicability/search_coverage_certificates.json`;
  - `applicability/applicability_validation.json`;
  - `applicability/generated_rule_pack_validation.json`;
  - `forest_plan_component_findings.json`;
  - `forest_plan_applicable_standard_coverage.json`;
  - `forest_plan_context_summary.json`;
  - `authority_reviewer_resolution_report.json`;
  - `litigation_risk_summary.json` or successor residual-risk artifact.
- Render Markdown and PDF from the canonical JSON.

Acceptance criteria:

- The generator fails if the review is not reviewer-ready.
- Every applicable authority row carries EA package evidence and source-library evidence.
- Every applicable Forest Plan standard carries plan-source and package evidence.
- Non-applicable authorities are summarized without dropping the full appendix pointer.
- The PDF exists and starts with `%PDF-`.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest <focused decision-support generator tests>
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit Sequence 2 as a focused implementation/test/docs commit.

Implemented surface:

- CLI command: `ea-consistency-document`
- Command lane: `src/usfs_r1_ea_sources/cli_decision_support.py`
- Generator module: `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`
- Architecture owner: `decision_support` layer, command group, and generated artifact family in
  `docs/architecture_contract.toml`

The generator validates all Sequence 2 required inputs, compares the Sequence 1 expected
hash/count baseline, keeps root-level manual `East_Crazies_*` drafts out of the source path, writes
canonical JSON plus Markdown/PDF/manifest outputs under the review `decision_support/` directory,
and returns nonzero through the CLI when fail-closed checks do not pass.

## Sequence 3: East Crazies Generated Decision-Support Report

Status:
Complete for the promoted East Crazies review.

Goal:
Generate the first real supervisor-facing report for the promoted East Crazies review.

Implementation scope:

- Run the generator against `v1-cg-ecid-compliance-review`.
- Use the Plan Consistency Table as the guide for the Forest Plan section, but source the generated
  report from current `forest_plan_component_findings.json` and applicable-standard coverage.
- Keep any generated files under `source_library/reviews/v1-cg-ecid-compliance-review/`.
- Do not replace root-level manual draft exports unless explicitly requested.

Acceptance criteria:

- Report includes all `33` applicable authority findings.
- Report includes all Forest Plan component coverage counts and all `12` applicable standards.
- Report links the Plan Consistency Table as `EA-PACKAGE-042`.
- Report summarizes the `340` non-applicable authorities and points to full coverage artifacts.
- Report includes a concise implementation confirmation checklist and residual risk register.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
git diff --check
```

Commit policy:
Do not stage generated `source_library/` files unless the repository policy changes or the user
explicitly asks to track the generated report. Commit any code, tests, schemas, and docs that make
the generated output reproducible.

Closeout result:
The 2026-05-06 local run wrote the ignored report family under
`source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`:

- `ea_consistency_decision_support.json`
- `ea_consistency_decision_support.md`
- `ea_consistency_decision_support.pdf`
- `ea_consistency_decision_support_manifest.json`

The generated report validation passed with all `33` applicable authority findings rendered as
`pass`, all `340` non-applicable authorities summarized with search coverage, all `329` Forest Plan
component rows represented, the `EA-PACKAGE-042` Plan Consistency Table linked, all `12/12`
applicable Forest Plan standards covered with package and plan evidence, `9` implementation
confirmation rows with evidence, `3` residual-risk notes, `0` legal-conclusion risk flags, and a
valid `%PDF-` output header. `phase-eval` for `v1-cg-ecid-compliance-review` passed `16/16` phases
with `reviewer_ready=true`. The report remains a generated local artifact until Sequence 4 promotes
it into a validation gate.

## Sequence 4: Decision-Support Gate

Goal:
Make the report a checked readiness artifact instead of an optional side output.

Implementation scope:

- Add a validation command or phase-eval check for the decision-support artifact family.
- Check input hashes, required sections, applicable authority count, non-applicable authority count,
  Forest Plan component counts, applicable-standard count, PDF validity, and reviewer-ready source
  artifact status.
- Add promotion-suite manifest checks for the East Crazies proving report when the output is present.

Acceptance criteria:

- The gate fails on missing report, stale hashes, missing required sections, missing non-applicable
  summary, missing applicable standards, or invalid PDF.
- The gate does not convert decision-support residual risk notes into compliance findings.
- Promotion can show whether the supervisor-facing report is current without claiming broader
  Region 1 readiness.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest <focused decision-support gate tests>
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Commit Sequence 4 as a focused gate/test/docs commit after verification passes.

## Sequence 5: Supervisor Review Polish

Goal:
Make the Markdown/PDF suitable for actual decision-support reading while preserving machine
traceability.

Implementation scope:

- Tighten headings, executive summary, table ordering, residual-risk language, and implementation
  confirmation wording.
- Add a short "How to use this document" note that states the document supports review but does not
  replace responsible official or counsel judgment.
- Add concise table summaries before long appendices.
- Preserve complete citations and artifact pointers.

Acceptance criteria:

- A reviewer can find the bottom-line determination, authority categories, Forest Plan consistency
  basis, applicable standards, non-applicable boundary, residual risks, and implementation checklist
  within the first few pages.
- Long evidence tables remain available without overwhelming the summary.
- No paragraph asserts a legal conclusion without a linked generated finding, source evidence, or
  stated decision-support caveat.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources <decision-support-command> \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
git diff --check
```

Commit policy:
Commit Sequence 5 as a focused renderer/report-polish commit.

## Final Definition Of Done

The milestone is complete when:

- a deterministic command generates the East Crazies EA consistency decision-support report from
  current audited review artifacts;
- the generated JSON, Markdown, and PDF report family exists locally under the review directory;
- validation proves report freshness, section completeness, authority counts, Forest Plan counts,
  applicable-standard coverage, non-applicable authority coverage, and PDF validity;
- `phase-eval --review-id v1-cg-ecid-compliance-review` includes or accepts the
  decision-support-report phase;
- `promotion-suite` can report decision-support readiness separately from broader Region 1
  expansion readiness;
- repository docs state the report is a decision-support artifact, not legal advice or a final
  agency decision;
- all code/docs/tests are committed as small verified sequence commits.

## Stop Conditions

Stop and report before implementation continues if:

- the current generated review artifacts are stale or fail validation;
- the report would need to rely on root-level manual draft prose as canonical evidence;
- the report would require staging ignored generated artifacts without explicit approval;
- Forest Plan component counts, applicable-standard counts, or applicability counts drift from the
  current review without a rerun and validation explanation;
- implementation requires network/download or corpus-regeneration work outside this milestone.
