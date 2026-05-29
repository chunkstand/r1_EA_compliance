# Technical Debt Register

This register tracks the small number of temporary exceptions that would otherwise fail repo debt
prevention gates. New entries should be added in the same milestone that introduces the shortcut.
Resolved entries should be removed instead of left behind as history.

## TD-001 Defensive batch ledger coverage exception

- status: active
- kind: coverage_exception
- path: `src/usfs_r1_ea_sources/batches.py:223`
- token: `pragma: no cover`
- owner: capture lane
- remove_by: the first milestone that changes batch failure handling or adds direct regression
  coverage for the ledger-preservation branch
- reason: the batch ledger must still serialize failure details when an unexpected downstream
  exception escapes the reporter or validator path, but the current focused tests do not inject that
  defensive branch directly.

## TD-002 First-class eval trace LLM-judge deferral

- status: active
- kind: accepted_limitation
- path: `src/usfs_r1_ea_sources/eval_trace_case_promote.py`
- token: `llm_judge.status="reserved_deferred"`
- owner: first-class eval trace lane
- remove_by: an approved model-judge milestone that adds calibration examples, prompt/rubric
  hashes, judge model/version/temperature, examples hash, and precision/recall checks against
  human labels
- reason: Milestone 5 intentionally promotes deterministic trace-to-case fixtures first. Allowing
  uncalibrated LLM judge scores to satisfy gates would weaken the local deterministic eval contract.
