# ADR 0001: Enforce Architecture With Small Fitness Gates

Date: 2026-05-04

## Context

The system already has strong functional gates: pytest, ruff, compileall, downloader/catalog
validation, phase evals, compliance evals, gold evals, and generated artifact validation. The next
risk is structural drift. Large modules and broad CLI surfaces make it easy for agents to make
localized changes that pass behavior tests while weakening ownership boundaries.

## Decision

Architecture will be enforced through a small machine-readable contract and focused tests:

- `docs/ARCHITECTURE.md` explains the current system shape for humans and agents.
- `docs/architecture_contract.toml` owns module layers, generated artifact surfaces, public command
  groups, and temporary exceptions.
- `tests/test_architecture_contract.py` parses Python imports with AST, rejects source import
  cycles, and rejects imports outside the contract.

Temporary exceptions must be explicit in the contract with an owner and removal milestone. They
must not be hidden inside the test implementation.

## Consequences

This avoids a broad rewrite and gives future milestones a cheap, deterministic architecture signal.
The first gate is intentionally narrow: it catches cycles and dependency-boundary drift, but it does
not replace functional tests, evals, or reviewer validation artifacts.

## Verification Gate

Architecture-affecting milestones should run:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
git diff --check
```

Source-moving milestones should also run focused behavior tests, `ruff check src tests`, and
`python -m compileall src`.

## Supersession

Supersede this ADR only with a new ADR that preserves automated architecture enforcement or explains
why another deterministic gate has replaced it.
