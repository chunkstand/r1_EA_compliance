# Technical Debt Register

This register tracks the small number of temporary exceptions that would otherwise fail repo debt
prevention gates. New entries should be added in the same milestone that introduces the shortcut.
Resolved entries should be removed instead of left behind as history.

## TD-001 Defensive batch ledger coverage exception

- status: active
- kind: coverage_exception
- path: `src/usfs_r1_ea_sources/batches.py:215`
- token: `pragma: no cover`
- owner: capture lane
- remove_by: the first milestone that changes batch failure handling or adds direct regression
  coverage for the ledger-preservation branch
- reason: the batch ledger must still serialize failure details when an unexpected downstream
  exception escapes the reporter or validator path, but the current focused tests do not inject that
  defensive branch directly.
