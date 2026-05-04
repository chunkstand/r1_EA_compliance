# ADR 0002: Applicability Before Compliance Review

Date: 2026-05-04

## Context

Authority applicability is not the same task as compliance finding generation. The post-V1 review
architecture now builds package facts, retrieval traces, graph traces, deterministic applicability
decisions, non-applicable authority artifacts, validation, adjudication, and generated rule packs
before reviewer-ready compliance review.

## Decision

Reviewer-ready compliance review must consume a validated generated applicability rule pack.
Compliance review must not override applicability decisions. Non-applicable authorities remain in
their own cited artifact family instead of being converted into compliance findings.

The base compliance rule pack may still be used for diagnostic fixtures and transition checks, but
base-pack diagnostic outputs are not reviewer-ready promotion artifacts.

## Consequences

Applicability quality is evaluated before compliance promotion. Generated review success is not
treated as proof that authority selection was correct. Unresolved or `needs_adjudication`
applicability decisions fail closed until validation or adjudication resolves them.

## Verification Gate

Relevant milestones should run focused applicability and compliance tests, plus the architecture
gate when module boundaries are touched:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability.py tests/test_applicability_decisions.py tests/test_applicability_retrieval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_rule_claim_binding.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
```

## Supersession

Supersede this ADR only with a new authority-applicability contract that preserves fail-closed
validation, cited non-applicability evidence, and generated-rule-pack provenance.
