# East Crazies Final QA And Certification Replay Milestone Plan

Date: 2026-05-07
Status: active; Sequence 2 deterministic generator/CLI work is complete and Sequence 3 gate integration is next

This plan adds a focused final QA and certification replay for the promoted East Crazy Inspiration
Divide EA compliance review. It is a replay over existing audited artifacts, not a new compliance
review, legal sufficiency determination, or Region 1 expansion pass.

## Goal

Produce a deterministic final QA packet that proves the canonical East Crazy review artifacts are
fresh, complete, citation-bearing, internally consistent, and bounded to the current source set.

Completion means:

- the promoted review ID remains `v1-cg-ecid-compliance-review`;
- the source set remains `source-set-ba8d0feae79501b8`;
- all replayed gates pass from existing generated artifacts;
- the final QA packet records the exact artifact hashes, counts, gate results, source pointers, and
  accepted V1 reviewer risks that support the reviewer-ready claim;
- the packet clearly separates machine validation from human reviewer certification;
- no hidden legal conclusion is introduced beyond citation-bearing evidence and validation gates.

## Non-Goals

- Do not rerun downloader, catalog, extraction, or broad package review workflows unless a freshness
  gate fails and a later sequence explicitly scopes that regeneration.
- Do not broaden the claim beyond the East Crazy Inspiration Divide / Custer Gallatin proving EA.
- Do not resolve the South Plateau strict-expansion blocker in this milestone.
- Do not treat root-level `East_Crazies_*` draft exports as canonical review artifacts.
- Do not stage ignored `source_library/` outputs unless repository policy changes.
- Do not convert the `14` accepted V1 conditional adjudication rows into hidden pass findings.
- Do not label the packet as final legal sufficiency, responsible-official approval, or counsel
  certification.

## Current Baseline

The final QA replay starts from the current promoted review state:

- review ID: `v1-cg-ecid-compliance-review`;
- source set: `source-set-ba8d0feae79501b8`;
- package extraction: `43` package manifest rows and `1,265` chunks;
- baseline source records evaluated: `26`;
- authority universe: `373` candidate authorities;
- applicability validation: `33` applicable authorities, `340` non-applicable authorities, `0`
  unresolved authorities, `generated_rule_pack_ready=true`;
- generated compliance findings: `33`, all currently `pass`;
- rule-claim binding: `142` rule-claim links and `0` rule-claim gaps;
- compliance matrix: `33` generated authority rows plus `79` forest-plan compliance rows;
- forest-plan context: Custer Gallatin reviewer-ready context;
- forest-plan component inventory: `329` components, `58` standards;
- applicable standards: `12/12` Custer Gallatin standards applied;
- forest-plan component eval: passing for the current seed;
- decision-support report: JSON, Markdown, PDF, and manifest under the review `decision_support/`
  directory validate from existing artifacts;
- review-scoped `phase-eval`: `19/19` phases pass with `reviewer_ready=true`;
- current-promotion suite: current V1 promotion remains green while expansion-only South Plateau
  blockers remain separate.

These counts are acceptance inputs, not free text. If any count drifts, the final QA replay must
fail closed until the drift is explained by a deliberate reviewed sequence.

## Proposed Output Surfaces

Generated outputs stay under ignored review artifacts:

- `source_library/reviews/v1-cg-ecid-compliance-review/final_qa/east_crazies_final_qa_certification.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/final_qa/east_crazies_final_qa_certification.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/final_qa/east_crazies_final_qa_certification.pdf`
- `source_library/reviews/v1-cg-ecid-compliance-review/final_qa/east_crazies_final_qa_certification_manifest.json`

Tracked implementation surfaces should be added only when their sequence starts:

- `config/east_crazies_final_qa_certification_v1.json`
- `config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json`
- `tests/fixtures/final_qa/minimal_final_qa_certification_report.json`
- `tests/test_final_qa_certification.py`
- `src/usfs_r1_ea_sources/final_qa_certification.py`
- `src/usfs_r1_ea_sources/cli_final_qa.py`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`

The command should be review-scoped, for example:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
```

The implementation should also support validation without rewriting generated outputs:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only
```

## Required Packet Sections

The JSON, Markdown, and PDF should include the same reviewed sections:

1. Review boundary: review ID, source set, package path, source-record boundary, package cache
   boundary, generated artifact root, and non-canonical draft exclusion.
2. Gate replay summary: applicability validation, generated rule-pack validation, compliance
   validation, compliance matrix, forest-plan context, forest-plan component eval, decision-support
   validation, phase-eval, V1 EA eval, and current-promotion suite results.
3. Artifact freshness ledger: required input files, schema versions, artifact hashes, modified
   times where useful, and source selectors.
4. Applicability partition: `33` applicable, `340` non-applicable, `0` unresolved, and explicit
   search-coverage support for the non-applicable boundary.
5. Finding QA: `33` generated findings, status counts, citation/source selectors, package-evidence
   selectors, rule-claim link counts, and zero rule-claim gaps.
6. Forest-plan QA: Custer Gallatin context basis, applicable standards, component inventory counts,
   component eval result, limitations, and reviewer-resolution status.
7. Decision-support QA: existing decision-support packet validation result, supervisor-readable
   rendering checks, residual-risk rows, implementation-confirmation rows, and legal-conclusion
   safeguards.
8. Accepted V1 risk ledger: `14` conditional adjudication rows carried as explicit accepted V1
   reviewer risk, with links to their source artifacts and eval rationale.
9. Certification statement: machine replay status, reviewer signoff fields, date fields, and a
   caveat that the packet supports review but does not replace responsible official, line officer,
   counsel, or specialist judgment.
10. Residual blockers and stop conditions: any missing/stale artifact, count drift, unresolved
   reviewer item, non-canonical draft dependency, invalid PDF, or legal-conclusion leak.

## Sequence 0: Baseline Replay And Drift Check

Purpose: prove the current East Crazy artifact family is still the correct canonical baseline before
adding a new generator.

Status: complete as of the 2026-05-07 Sequence 0 replay. The existing East Crazy review validated
from current generated artifacts, review-scoped `phase-eval` passed `19/19` with
`reviewer_ready=true`, and the non-strict promotion suite kept current promotion green with
`22/22` required current-promotion results passed. The only replay limitation is that `phase-eval`
and `promotion-suite` have normal write behavior for their ignored generated result files; no
tracked files or root-level `East_Crazies_*` draft exports were staged or made canonical.

Sequence 1 fixture decision: pin semantic counts, source selectors, and current artifact hashes,
and add selected Markdown/PDF rendering requirements for required headings, caveats, table-summary
markers, and PDF-header validity. Do not pin full Markdown/PDF body text because that would make
the fixture brittle without improving the replay boundary.

Actions:

1. Re-read the current review artifacts, decision-support manifest, graph validation outputs,
   promotion-suite outputs, and phase-eval results.
2. Confirm that root-level `East_Crazies_*` drafts are non-canonical and remain unstaged.
3. Record the exact current baseline counts and artifact paths in the handoff.
4. Decide whether the final QA fixture should pin only semantic counts/hashes or also selected
   rendered Markdown/PDF text requirements.

Acceptance:

- The promoted East Crazy review still validates from current generated artifacts.
- Any count drift is either explained and documented or blocks implementation.
- No generated artifact is rewritten during baseline replay unless a command explicitly has no
  validate-only mode and the sequence records that limitation.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --manifest config/promotion_suite_v1.json

git diff --check
```

Stop if the generated review directory is missing, stale, non-reviewer-ready, or no longer matches
the documented promoted source set.

## Sequence 1: Final QA Contract And Fixtures

Purpose: define the report schema, fixture expectations, and fail-closed categories before writing
the generator.

Status: complete as of the 2026-05-07 Sequence 1 pass. The tracked contract now lives in
`config/east_crazies_final_qa_certification_v1.json`, the current East Crazies expected-summary
fixture lives in `config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json`, and the
synthetic schema fixture lives in `tests/fixtures/final_qa/minimal_final_qa_certification_report.json`.
`docs/OUTPUT_SCHEMAS.md` documents the artifact family and fail-closed categories before generator
code exists. The Sequence 1 gap-close pass tightened the contract so every scalar expected-summary
count must appear in `required_count_fields`, config and expected-summary section/output/failure
contracts must stay aligned, and `validation_expectations` explicitly maps the acceptance criteria
to fail-closed categories before runtime validation exists.

Sequence 2 added `src/usfs_r1_ea_sources/final_qa_certification.py`,
`src/usfs_r1_ea_sources/cli_final_qa.py`, CLI registration, and generated JSON/Markdown/PDF/manifest
writing under the review `final_qa/` directory. It reads the Sequence 1 config/fixtures and
existing audited review artifacts only.

Actions:

1. Add `config/east_crazies_final_qa_certification_v1.json` to own section order, expected review
   IDs, required gate names, required count fields, artifact selectors, caveat text, and reviewer
   signoff fields.
2. Add a real-review expected-summary fixture for the current East Crazy counts, representative
   applicable authority row, representative non-applicable authority row, representative
   forest-plan standard, representative decision-support residual-risk row, and the accepted V1
   risk ledger.
3. Add a minimal synthetic report fixture to lock the schema boundary without depending on local
   `source_library/`.
4. Document the artifact family in `docs/OUTPUT_SCHEMAS.md`.

Acceptance:

- The contract can reject missing gate sections, stale hashes, count drift, missing citations,
  missing non-applicable boundary evidence, unresolved reviewer items, invalid PDF output, and
  legal-conclusion wording.
- The fixture makes it clear that certification means deterministic replay readiness plus optional
  human signoff, not legal sufficiency.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_final_qa_certification.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

Stop if the expected-summary fixture cannot be grounded in current generated artifacts.

## Sequence 2: Deterministic Generator And CLI

Purpose: build the final QA replay command as a deterministic reader over existing audited
artifacts.

Status: complete as of the 2026-05-07 Sequence 2 pass. The `final-qa-certification` command writes
and validates the JSON/Markdown/PDF/manifest family under the ignored review `final_qa/` directory,
and `--validate-only` replays the same `155` checks without rewriting outputs. The implementation
keeps final QA as a configured artifact reader over existing audited outputs; it does not rerun
downloader, extraction, compliance review, phase eval, or promotion suite workflows.

Actions:

1. Implement `final_qa_certification.py` as a pure artifact reader and validator.
2. Implement `cli_final_qa.py` and register a `final-qa-certification` command.
3. Read only catalog/review surfaces and tracked config/fixtures; do not scan raw artifact filenames
   to infer semantic state.
4. Validate required artifact schemas, hashes, review ID, source set, reviewer-ready flags, status
   counts, source selectors, trace IDs, PDF headers, and required Markdown/PDF sections.
5. Write JSON, Markdown, PDF, and manifest outputs under the review `final_qa/` directory.
6. Add `--validate-only` so later closeout can prove the existing packet without rewriting it.

Acceptance:

- The command writes the final QA packet for `v1-cg-ecid-compliance-review`.
- The generated packet carries exact source pointers and artifact selectors for every supported
  claim.
- The command fails closed when any required artifact is missing, stale, mismatched, not
  reviewer-ready, or dependent on non-canonical root-level drafts.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only

PYTHONPATH=src uv run --extra dev pytest tests/test_final_qa_certification.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop if implementation requires model-generated synthesis, hidden legal interpretation, or
root-level draft files to satisfy the packet.

## Sequence 3: Gate Integration

Purpose: make the final QA replay visible to the existing promotion/readiness gates without
changing the underlying review result.

Actions:

1. Add a `final_qa_certification_report` optional phase to `phase-eval` when the final QA artifact
   family exists.
2. Add current-promotion-suite required artifacts for the final QA JSON, manifest, PDF, and
   validation result.
3. Keep South Plateau expansion failures separate from current East Crazy final QA readiness.
4. Add tests that fail when the phase or promotion suite treats expansion-only blockers as current
   East Crazy final QA blockers.

Acceptance:

- `phase-eval --review-id v1-cg-ecid-compliance-review` includes the final QA phase after the
  packet is generated.
- Current promotion remains green only when the final QA packet validates.
- Strict expansion can still fail on South Plateau without downgrading the East Crazy final QA
  packet.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval.py tests/test_promotion_suite.py
git diff --check
```

Stop if the gate integration hides expansion blockers, hides accepted V1 risk, or weakens existing
phase-eval readiness checks.

## Sequence 4: Final Review Packet QA And Closeout

Purpose: replay the full certification path, inspect the rendered packet, update durable docs, and
commit the verified slice.

Actions:

1. Regenerate the final QA packet once, then rerun `--validate-only`.
2. Inspect the generated Markdown/PDF for reviewer usability, table fit, required caveats, source
   pointers, and absence of unsupported legal conclusions.
3. Rerun the full current-promotion gate stack.
4. Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
   `docs/OUTPUT_SCHEMAS.md` with the implemented status and final command set.
5. Leave ignored `source_library/` outputs unstaged unless repository policy changes.
6. Commit only the verified final QA implementation slice.

Acceptance:

- Final QA JSON, Markdown, PDF, and manifest validate from existing audited artifacts.
- `phase-eval`, `v1-ea-eval`, and non-strict `promotion-suite` pass for current promotion.
- The packet makes every residual risk and accepted V1 risk explicit.
- The repo docs and handoff match the verified artifact state.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --eval-file config/v1_ecid_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest tests/test_final_qa_certification.py tests/test_phase_eval.py tests/test_promotion_suite.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop if any current-promotion gate fails, if generated outputs cannot be validated without
rewriting, or if the rendered packet cannot preserve the difference between evidence-backed QA and
human legal/project approval.

## Milestone Commit Policy

Each implementation sequence should close with one atomic commit after its verification passes.
Stage only the sequence's implementation, tests, configs, docs, handoff updates, and any tracked
fixtures. Leave unrelated dirty files and ignored generated outputs alone.

Push only when the user explicitly asks for push or PR publication.
