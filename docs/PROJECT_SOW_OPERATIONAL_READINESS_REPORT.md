# Project SOW Operational Readiness Report

Date: 2026-05-07

## Readiness Decision

The Project SOW operationalization lane is ready for local repeated land-exchange planning use when
`project-sow-operational-gate` is green.

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \
  --output-dir source_library/project_sow_operational_gate
```

The gate is local-only for Sequence 7. It writes generated smoke/eval outputs under the selected
output directory and does not establish broader CI policy. Adding this gate to CI should be a
separate milestone because it creates generated packages and readiness reports as part of its smoke
run.

## Gate Contract

The gate must pass all of these checks before the lane is treated as operationally ready:

- minimal land-exchange template validation passes without writing package outputs;
- all proving-intake validations pass without writing package outputs;
- `project-sow-eval` passes for East Crazies, Red Rock Ridge, and Silver Creek;
- proving packages are written under the selected output directory and pass rendering/PDF smoke
  checks;
- proving eval reports `0` system misses and `0` intake omissions;
- East Crazies EA handoff smoke passes and remains stable at `27` expected future-artifact slots;
- tracked JSON inputs parse successfully;
- tracked README, architecture, current-state, output-schema, runbook, milestone, session handoff,
  architecture contract, and readiness-report docs reference the operational gate and its local-only
  boundary.
- the gate summary includes a `closeout_contract` with required green checks, generated-output
  locations, tracked doc/schema paths, local-only CI policy, and non-review/non-legal boundaries;
- the gate summary records hashes for the operational report, proving eval summary, gate summary
  content, and EA handoff smoke artifacts.

## Boundaries

The gate does not run downloader, catalog, extraction, applicability, generated rule-pack,
compliance review, phase-eval, legal sufficiency, or final agency decision workflows. Generated
outputs remain ignored local evidence under `source_library/` unless repository policy changes
explicitly.

## Latest Closeout Signal

Sequence 7 closeout gate run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \
  --output-dir /tmp/project-sow-sequence-7-operational-gate
```

Latest gate result:

- `4` validation-only intake targets passed: minimal template, East Crazies, Red Rock Ridge, and
  Silver Creek;
- `project-sow-eval` passed `3` proving cases with `0` failed cases, `0` system misses, and `0`
  intake omissions;
- East Crazies EA handoff smoke passed with `27` expected future-artifact slots and `0` handoff
  validation failures;
- tracked JSON inputs parsed successfully and required docs references were present;
- closeout contract and output hashes were present in the generated gate summary;
- generated outputs were written under `/tmp/project-sow-sequence-7-operational-gate` for closeout
  verification, not staged from `source_library/`.

The current branch handoff records the full required verification stack after closeout.
