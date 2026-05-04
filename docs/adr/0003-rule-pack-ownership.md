# ADR 0003: Rule-Pack Ownership Outside Compliance Review

Date: 2026-05-04

## Context

Rule packs are shared upstream data. Rule-claim binding, applicability, generated rule-pack
validation, compliance coverage, compliance eval, and compliance review all need to load and
validate rule packs. Keeping shared rule-pack utilities inside `compliance_review.py` created an
import cycle and made upstream layers depend on a downstream review module.

## Decision

Shared rule-pack constants, schema versions, loading, baseline source-record helpers, and rule-pack
validation are owned by `src/usfs_r1_ea_sources/rule_packs.py`.

Internal modules that need shared rule-pack behavior import it from `rule_packs.py`. Compatibility
re-exports from `compliance_review.py` may remain only for external import stability and must not be
used by upstream internal modules.

## Consequences

The architecture direction now matches the domain model: rule packs and rule-claim binding are
upstream of compliance review. The architecture fitness gate should fail if rule binding or
applicability starts importing shared rule-pack behavior from compliance review again.

## Verification Gate

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev pytest tests/test_rule_claim_binding.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
```

## Supersession

Supersede this ADR only if rule-pack ownership moves to another neutral upstream module with an
equivalent architecture contract.
