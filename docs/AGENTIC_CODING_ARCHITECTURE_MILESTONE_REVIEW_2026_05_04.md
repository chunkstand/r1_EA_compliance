# Agentic Coding Architecture Milestone Review

Date: 2026-05-04

Scope: review the committed architecture hardening sequence against
`docs/AGENTIC_CODING_ARCHITECTURE_MILESTONE_PLAN.md`, close concrete gaps, and check the result
against the expert lenses named in the plan.

## Milestone Evidence

| Plan Milestone | Commit | Review Status |
| --- | --- | --- |
| 1. Add the architecture map | `d735b6e` | Complete. Added `docs/ARCHITECTURE.md`, `docs/architecture_contract.toml`, and ADR 0001. |
| 2. Add the first architecture fitness gate | `7adfc84` | Complete. Added AST-based import cycle and dependency-boundary tests. |
| 3. Split rule-pack ownership from compliance review | `d78bf55` | Complete. Added `rule_packs.py`, removed the rule-pack/compliance cycle, and kept compatibility reexports out of upstream imports. |
| 4. Group CLI registration by workflow lane | `ce93ebb` | Complete. Kept `cli.py` as the public entrypoint and split lane registration/dispatch modules. |
| 5. Rank hotspots and plan the first reduction | `15e0984` | Complete. Selected `compliance_review.py` from size, churn, and reviewer-risk evidence. |
| 6. Codify architecture decisions and safety boundaries | `339bcc9` | Complete. Added ADRs for applicability-before-compliance, rule-pack ownership, untrusted evidence, and architecture gates. |
| 7. Make architecture gates part of milestone closeout | `b4afa1f` | Complete. Added architecture-gate commands to repo and milestone closeout docs. |

Milestone 0 had no checkpoint commit because the work started from a clean baseline and proceeded
directly into the documented checkpoint sequence.

## Gaps Closed In This Review

The review found two contract precision gaps and one test gap:

- `reuse_inventory.py` was grouped under extraction, which forced the entire extraction layer to
  allow imports from review. That made the dependency gate too broad. The contract now assigns
  `reuse_inventory.py` to a narrower `review_support` layer, so extraction no longer has a blanket
  downstream review allowance.
- Retrieval artifact paths were listed under extraction ownership, and extraction artifact paths
  did not match the implemented `diagnostics/` and `chunks/` directories. The contract now records
  extraction, retrieval, and review-support artifact ownership separately with implemented paths.
- The CLI smoke test only checked that contract commands were registered. It now requires equality
  between the public parser commands and the contract, so future public commands must be added to
  the command-group contract.

## Expert-Lens Alignment

Simon Brown: the architecture map and contract now make the current system shape and ownership
boundaries legible at the module, artifact, and CLI-command levels. The review-support correction
keeps a cross-cutting helper explicit instead of hiding it in a broad extraction boundary.

Neal Ford, Rebecca Parsons, and Patrick Kua: the architecture intent is enforced by a small fitness
function that parses actual imports and command registration. The tightened extraction boundary and
CLI equality assertion make the gate more evolutionary because drift now fails automatically.

Titus Winters and Google Engineering Practices: CLI behavior remains stable while command ownership
is split into reviewable lane modules. The contract now prevents undocumented command growth, which
keeps the public interface easier to review over time.

Adam Tornhill: the hotspot milestone used measured size and churn signals to select
`compliance_review.py` as the next reduction target. This review does not move that hotspot code;
it preserves the planned next slice as a bounded, test-backed future milestone.

## Residual Risk

- The architecture gate enforces source-level imports and public command registration, not runtime
  artifact compatibility. Behavior-changing refactors still need focused behavior tests and evals.
- `compliance_review.py` remains the selected hotspot. The next reduction should move matrix and
  report rendering helpers into `compliance_outputs.py` only after the focused tests named in
  `docs/HOTSPOT_REPORT_2026_05_04.md` are in scope.
- Ignored `source_library/` evidence artifacts were not regenerated or validated by this review.
