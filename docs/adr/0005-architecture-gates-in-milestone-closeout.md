# ADR 0005: Include Architecture Gates In Milestone Closeout

Date: 2026-05-04

## Context

The codebase is increasingly operated by coding agents. Functional tests can pass while dependency
direction, command ownership, or generated artifact ownership drifts. Architecture checks need to be
part of ordinary milestone closeout, not an occasional audit.

## Decision

Milestones that move source modules, CLI registration, review/compliance boundaries,
applicability/generated-rule-pack behavior, or generated artifact ownership must run the
architecture contract test before commit:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
```

Source-moving milestones should also run the focused behavior tests for the changed workflow lane,
`PYTHONPATH=src uv run --extra dev ruff check src tests`, `python -m compileall src`, and
`git diff --check`.

## Consequences

Architecture exceptions are deliberate, named, and scheduled for removal. Reviewers can use the
contract and ADRs instead of reconstructing architecture decisions from chat history.

## Supersession

Supersede this ADR only with a stronger deterministic closeout gate that covers the same dependency
and ownership boundaries.
