# EA Consistency Decision Support Preflight Pass 7

Date: 2026-05-06

Scope: `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` workstream 7,
CLI, Module, And Renderer Ownership.

## Result

Status: `go` for pass 7 only.

This does not complete the full Sequence 0 preflight. The next preflight pass is Fixture And
Regression Contract.

## Boundary Checked

- Review ID: `v1-cg-ecid-compliance-review`
- Source set: `source-set-ba8d0feae79501b8`
- Report output boundary for later implementation:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`
- Planned tracked synthesis owner from pass 6:
  `config/ea_consistency_decision_support_v1.json`
- Preferred command name from the preflight plan: `ea-consistency-document`

This pass chooses the implementation surface for the later milestone. It does not add the command,
module, renderer, schema, or tests.

## Worktree And Generated-Output Boundary

Command:

```bash
git status -sb
```

Observed status:

```text
## main...origin/main [ahead 4]
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.csv
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.md
?? East_Crazies_EA_Compliance_Matrix_2026-05-05.pdf
?? East_Crazies_EA_Compliance_Review_2026-05-05.md
?? East_Crazies_EA_Compliance_Review_2026-05-05.pdf
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.md
?? East_Crazies_Inverse_Compliance_Demo_WLG_2026-05-06.pdf
```

Tracked files were clean at pass start. The root-level `East_Crazies_*` files remain untracked,
non-canonical manual draft comparison material and were not used to decide implementation
ownership. No generated `source_library/` output was staged.

## Current Ownership Pattern Inspected

The current public CLI and architecture surfaces are:

- `src/usfs_r1_ea_sources/__main__.py` delegates to `cli.main`.
- `src/usfs_r1_ea_sources/cli.py` owns the public parser, imports lane-specific command
  registration modules, and dispatches to lane handlers.
- Existing lane registration files include `cli_capture.py`, `cli_derived.py`,
  `cli_applicability.py`, `cli_review.py`, `cli_compliance.py`, and `cli_eval.py`.
- `tests/test_cli.py` checks that registered commands match the command groups declared in
  `docs/architecture_contract.toml`.
- `tests/test_architecture_contract.py` requires every `src/usfs_r1_ea_sources/*.py` module to be
  assigned to one contract layer, validates layer names, and fails dependency-boundary violations
  against the contract.
- `src/usfs_r1_ea_sources/compliance_outputs.py` owns the current compliance matrix JSON-to-
  Markdown/PDF rendering pattern through `matrix_markdown()` and `write_compliance_matrix_pdf()`.
- `src/usfs_r1_ea_sources/compliance_review.py` writes `compliance_matrix.json`,
  `compliance_matrix.md`, and `compliance_matrix.pdf` from the canonical JSON matrix.
- `docs/OUTPUT_SCHEMAS.md` documents generated artifact contracts and should own the later
  decision-support artifact schema.

The current architecture contract has no decision-support layer or command group. It lists review
outputs and compliance matrix outputs, but not the future `decision_support/` artifact family.

## Ownership Decision

Pass-7 decision: create a new decision-support lane when code implementation begins.

The later implementation should use these owners:

| Surface | Owner decision |
| --- | --- |
| CLI command | `ea-consistency-document` |
| CLI registration | Add `src/usfs_r1_ea_sources/cli_decision_support.py` and register it from `src/usfs_r1_ea_sources/cli.py` |
| CLI command group | Add a `decision_support` command group to `docs/architecture_contract.toml` with command `ea-consistency-document` |
| Canonical report module | Add `src/usfs_r1_ea_sources/ea_consistency_decision_support.py` |
| Architecture layer | Add a `decision_support` layer in `docs/architecture_contract.toml` when the module is introduced |
| Generated artifact owner | Assign `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.json`, `.md`, `.pdf`, and `_manifest.json` to the `decision_support` layer |
| Config owner | Use tracked `config/ea_consistency_decision_support_v1.json` for implementation-confirmation taxonomy, residual-risk grouping, display order, and allowed caveat wording |
| Schema/docs owner | Document the artifact family in `docs/OUTPUT_SCHEMAS.md`; keep the milestone plan as sequencing guidance only |
| Fixture/test owner | Use `tests/test_ea_consistency_decision_support.py` for schema/generator/gate behavior and `tests/test_cli.py` for parser/handler wiring |

This keeps the supervisor-facing synthesis separate from compliance finding generation. Compliance
artifacts remain inputs; the decision-support layer must not override applicability decisions,
create compliance findings, or reinterpret non-applicable authorities.

## Module Boundary Decision

The future `ea_consistency_decision_support.py` module should expose a small public API:

- `run_ea_consistency_document(...)` as the command-facing entry point;
- a canonical JSON builder that reads audited review artifacts from `source_library/reviews/<review_id>/`;
- a validator that checks required artifacts, hashes, counts, section completeness, and PDF
  validity;
- Markdown and PDF renderers that render from canonical JSON only;
- a manifest writer that records input paths, hashes, generator version, validation status, and
  generated output paths.

The module should read explicit review artifacts and tracked config. It should not scan raw
artifact filenames, read root-level manual East Crazies draft exports, rerun downloader/corpus
workflows, or run compliance review internally.

Suggested command signature for Sequence 2:

```text
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --config config/ea_consistency_decision_support_v1.json
```

Optional later flags can include `--source-set-id`, `--results-dir`, and `--validate-only`, but the
first implementation should keep the command surface narrow unless tests require more.

## Architecture Contract Decision

When the first code slice is implemented, update `docs/architecture_contract.toml` atomically with
the new module and command wiring:

- add `ea_consistency_decision_support` to a new `decision_support` layer;
- add `cli_decision_support` to the existing `cli` layer;
- allow the `decision_support` layer to import `foundation`, `review`, `applicability`,
  `compliance`, and `decision_support` as needed;
- allow the `cli` layer to import `decision_support`;
- add the decision-support artifact paths under a `decision_support` artifact owner;
- add `ea-consistency-document` to a `decision_support` command group.

Do not update the architecture contract with modules before those modules exist unless the same
sequence also updates tests or adds the module. `tests/test_architecture_contract.py` intentionally
fails on contract/source mismatches.

## Renderer Decision

The later report must follow the existing compliance-output rendering pattern:

- canonical JSON is the source of truth;
- Markdown is rendered from canonical JSON;
- PDF is rendered from canonical JSON or the same normalized report model used for Markdown;
- the generated PDF must start with `%PDF-`;
- PDF generation should use the repo's built-in simple PDF writer pattern and must not introduce a
  system PDF dependency for the first report implementation.

The implementation should not import private helpers such as `_write_simple_pdf()` from
`compliance_outputs.py` as a cross-module API. Either keep a small report-specific PDF writer in
the new module while the format is narrow, or extract a public shared rendering helper in a focused
later slice if real duplication appears.

## Verification Decision

The verification path for future sequences is:

- Pass 7 docs-only closeout: `git diff --check`.
- Sequence 1 schema/fixture work: focused decision-support schema tests plus
  `tests/test_architecture_contract.py` if any module or command boundary is introduced.
- Sequence 2 generator work: focused generator/renderer tests, `tests/test_cli.py`,
  `tests/test_architecture_contract.py`, `ruff check src tests`, `python -m compileall src`, and
  `git diff --check`.
- Sequence 3 real East Crazies output: run `ea-consistency-document` for
  `v1-cg-ecid-compliance-review`, then `phase-eval --review-id v1-cg-ecid-compliance-review`, and
  keep generated `source_library/` outputs ignored unless repo policy changes.
- Sequence 4 gate work: add decision-support validation to phase/promotion gates and rerun the
  focused gate tests plus `phase-eval` and `promotion-suite`.

## Go/Stop Decision

Go condition from the plan:

> The full milestone has a clear implementation surface and verification path before code edits.

Pass-7 decision: `go`.

Rationale:

- The command name is fixed as `ea-consistency-document`.
- The canonical code owner is fixed as `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`.
- CLI wiring is fixed as a new `cli_decision_support.py` lane registered through `cli.py`.
- The architecture-contract changes needed for code implementation are identified.
- Markdown/PDF rendering will follow the existing compliance-output pattern without depending on
  private helpers or new system PDF tooling.
- Schema, config, fixture, CLI, architecture, and gate test ownership is clear.

## Stop Conditions Not Triggered

- The command surface is not ambiguous.
- The canonical module owner is not ambiguous.
- The renderer path does not require broad refactoring before Sequence 1.
- The decision-support report does not need to become part of compliance-review generation.
- The report implementation does not need to stage ignored generated outputs.
- Root-level manual East Crazies draft exports remain non-canonical comparison material.

## Next Preflight Pass

Begin pass 8: Fixture And Regression Contract.

Pass 8 should define the minimum fixture and fail-closed expectations before full Sequence 1:

- required report sections;
- required count and hash fields;
- one applicable authority row with package and source evidence;
- one non-applicable authority summary row with search coverage;
- one Forest Plan component summary;
- all `12` applicable standards in the real-review expectation;
- fail-closed cases for missing artifacts, count drift, stale hashes, missing PDF, and missing
  non-applicable authority summary.
