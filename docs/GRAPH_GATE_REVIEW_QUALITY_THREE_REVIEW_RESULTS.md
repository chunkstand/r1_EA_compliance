# Graph-Gate Review-Quality Three-Review Results

Date: 2026-06-04 local / 2026-06-05 UTC

Command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources graph-gate-review-quality-eval --manifest config/graph_gate_review_quality_eval_v1.json --output-dir source_library
```

Generated result:
`source_library/evaluations/graph_gate_review_quality/graph_gate_review_quality_results.json`

## Outcome

- `experiment_status= hypothesis_supported`
- `hypothesis_supported=true`
- `case_count=3`
- `complete_case_count=3`
- `distinct_review_count=3`
- `positive_delta_case_count=3`
- `critical_regression_count=0`
- `threshold_failures=[]`
- `net_quality_delta=9.428571`

The supported claim is scoped to artifact-derived full-review metrics. It proves
that graph-gated readback adds deterministic gate evidence, consistency
readback, and traceability across the three frozen reviews without changing the
underlying review/source-set/compliance/phase-eval inputs. It does not adopt
runtime compliance-review or phase-eval graph-gate blocking.

## Case Metrics

| Review | Citation gaps | Unsupported gate pass | Gate gap | Readiness blockers | Gate consistency | Traceability | Gate nodes/edges | Net delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `west-reservoir-67436` | `0 -> 0` | `1 -> 0` | `1 -> 0` | `0 -> 0` | `0 -> 1` | `0.857143 -> 1.0` | `0/0 -> 659/658` | `3.142857` |
| `region1-example-lolo-tylers-kitchen-66344` | `1 -> 1` | `1 -> 0` | `1 -> 0` | `0 -> 0` | `0 -> 1` | `0.857143 -> 1.0` | `0/0 -> 1122/1121` | `3.142857` |
| `region1-example-helena-lewis-and-clark-bonanza-66532` | `1 -> 1` | `1 -> 0` | `1 -> 0` | `0 -> 0` | `0 -> 1` | `0.857143 -> 1.0` | `0/0 -> 537/536` | `3.142857` |

## Boundary

The result supports widening discussion only as a follow-on packet. The next
runtime packet must still preserve the stop conditions: no post-hoc threshold
tuning, no new applicability or legal conclusions, no hidden domain heuristics,
and no runtime compliance/phase-eval graph-gate adoption without its own scoped
implementation and verification gate.
