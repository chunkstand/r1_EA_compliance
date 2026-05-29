from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .eval_trace_gate import EVAL_TRACE_GATE_SCHEMA_VERSION
from .promotion_suite_artifacts import _artifact_result
from .promotion_suite_artifacts import _review_case_result
from .promotion_suite_artifacts import _rule_pack_result
from .promotion_suite_current import _current_promotion_contract_result
from .promotion_suite_expansion import _expansion_slot_result
from .promotion_suite_report import _markdown_report
from .promotion_suite_summary import _expansion_failure_category_counts
from .promotion_suite_summary import _failure_category_counts
from .promotion_suite_summary import _full_canonical_failure_category_counts
from .promotion_suite_support import DEFAULT_PROMOTION_SUITE_PATH as _DEFAULT_PROMOTION_SUITE_PATH
from .promotion_suite_support import (
    PROMOTION_SUITE_RESULTS_SCHEMA_VERSION as _PROMOTION_SUITE_RESULTS_SCHEMA_VERSION,
)
from .promotion_suite_support import (
    PROMOTION_SUITE_SCHEMA_VERSION as _PROMOTION_SUITE_SCHEMA_VERSION,
)
from .promotion_suite_support import _manifest_context
from .promotion_suite_support import _read_json
from .promotion_suite_support import _utc_now
from .promotion_suite_support import _write_json
from .promotion_suite_validation import _validate_manifest


PROMOTION_SUITE_SCHEMA_VERSION = _PROMOTION_SUITE_SCHEMA_VERSION
PROMOTION_SUITE_RESULTS_SCHEMA_VERSION = _PROMOTION_SUITE_RESULTS_SCHEMA_VERSION
DEFAULT_PROMOTION_SUITE_PATH = _DEFAULT_PROMOTION_SUITE_PATH


@dataclass(frozen=True)
class PromotionSuiteResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    markdown_path: Path
    summary: dict[str, Any]


def run_promotion_suite(
    *,
    output_dir: Path = Path("source_library"),
    manifest_path: Path = DEFAULT_PROMOTION_SUITE_PATH,
    results_dir: Path | None = None,
    strict_expansion: bool = False,
) -> PromotionSuiteResult:
    """Check manifest-declared promotion evidence and write an aggregate readiness report."""

    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    suite_id = str(manifest["id"])
    suite_output_dir = (
        Path(results_dir)
        if results_dir is not None
        else output_dir / "reviews" / "promotion_suite" / suite_id
    )
    output_path = suite_output_dir / "promotion_suite_results.json"
    markdown_path = suite_output_dir / "promotion_suite_report.md"

    context = _manifest_context(manifest, output_dir)
    rule_pack_result = _rule_pack_result(manifest, manifest_path)
    review_results = [
        _review_case_result(case, context=context, output_dir=output_dir)
        for case in manifest.get("review_cases", [])
    ]
    suite_results = [
        _artifact_result(spec, context=context, output_dir=output_dir)
        for spec in manifest.get("suite_results", [])
    ]
    expansion_slots = [
        _expansion_slot_result(slot, output_dir=output_dir)
        for slot in manifest.get("expansion_slots", [])
    ]

    required_review_results = [
        result
        for case in review_results
        for result in case["results"]
        if result["required_for_current_promotion"]
    ]
    required_suite_results = [
        result for result in suite_results if result["required_for_current_promotion"]
    ]
    required_full_canonical_results = [
        result for result in suite_results if result["required_for_full_canonical_corpus"]
    ]
    required_expansion_review_results = [
        result
        for case in review_results
        for result in case["results"]
        if result["required_for_expansion"]
    ]
    required_expansion_suite_results = [
        result for result in suite_results if result["required_for_expansion"]
    ]
    current_promotion_contract = _current_promotion_contract_result(
        manifest=manifest,
        manifest_path=manifest_path,
        context=context,
        output_dir=output_dir,
        rule_pack_result=rule_pack_result,
        review_results=review_results,
        suite_results=suite_results,
    )
    eval_trace_gate_summary = _eval_trace_gate_summary(
        review_results=review_results,
        suite_results=suite_results,
    )
    current_promotion_ready = (
        current_promotion_contract["passed"]
        if current_promotion_contract is not None
        else (
            rule_pack_result["passed"]
            and all(result["passed"] for result in required_review_results)
            and all(result["passed"] for result in required_suite_results)
        )
    )
    current_promotion_ready = (
        current_promotion_ready and eval_trace_gate_summary["current_promotion_passed"]
    )
    full_canonical_corpus_ready = bool(context["full_canonical_source_set_id"]) and bool(
        required_full_canonical_results
    ) and all(result["passed"] for result in required_full_canonical_results)
    expansion_artifacts_ready = all(
        result["passed"]
        for result in required_expansion_review_results + required_expansion_suite_results
    )
    expansion_ready = (
        all(slot["ready"] for slot in expansion_slots) and expansion_artifacts_ready
    )
    promotion_ready = current_promotion_ready and (expansion_ready if strict_expansion else True)
    failure_category_counts = Counter(
        _failure_category_counts(
            rule_pack_result=rule_pack_result,
            review_results=review_results,
            suite_results=suite_results,
            expansion_slots=expansion_slots,
            current_promotion_contract=current_promotion_contract,
            strict_expansion=strict_expansion,
        )
    )
    if not eval_trace_gate_summary["current_promotion_passed"]:
        failure_category_counts.update(
            {"eval_trace_gate_failed": eval_trace_gate_summary["failed_current_gate_count"]}
        )
    failure_category_counts = dict(sorted(failure_category_counts.items()))
    expansion_failure_category_counts = _expansion_failure_category_counts(
        review_results=review_results,
        suite_results=suite_results,
        expansion_slots=expansion_slots,
    )
    full_canonical_failure_category_counts = _full_canonical_failure_category_counts(
        suite_results=suite_results
    )
    summary = {
        "schema_version": PROMOTION_SUITE_RESULTS_SCHEMA_VERSION,
        "suite_schema_version": manifest.get("schema_version"),
        "suite_id": suite_id,
        "suite_label": manifest.get("label"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(suite_output_dir),
        "output_path": str(output_path),
        "markdown_path": str(markdown_path),
        "source_set_id": context["source_set_id"],
        "current_promotion_source_set_id": context["source_set_id"],
        "full_canonical_source_set_id": context["full_canonical_source_set_id"],
        "rule_pack_path": manifest.get("rule_pack_path"),
        "rule_pack_id": manifest.get("rule_pack_id"),
        "rule_pack_version": manifest.get("rule_pack_version"),
        "strict_expansion": strict_expansion,
        "current_promotion_ready": current_promotion_ready,
        "full_canonical_corpus_ready": full_canonical_corpus_ready,
        "expansion_ready": expansion_ready,
        "promotion_ready": promotion_ready,
        "review_case_count": len(review_results),
        "suite_result_count": len(suite_results),
        "expansion_slot_count": len(expansion_slots),
        "required_current_result_count": len(required_review_results)
        + len(required_suite_results)
        + 1,
        "passed_required_current_result_count": sum(
            1 for result in required_review_results + required_suite_results if result["passed"]
        )
        + int(rule_pack_result["passed"]),
        "required_expansion_result_count": len(required_expansion_review_results)
        + len(required_expansion_suite_results)
        + len(expansion_slots),
        "passed_required_expansion_result_count": sum(
            1
            for result in required_expansion_review_results
            + required_expansion_suite_results
            if result["passed"]
        )
        + sum(1 for slot in expansion_slots if slot["ready"]),
        "required_full_canonical_result_count": len(required_full_canonical_results),
        "passed_required_full_canonical_result_count": sum(
            1 for result in required_full_canonical_results if result["passed"]
        ),
        "expansion_artifacts_ready": expansion_artifacts_ready,
        "failure_category_counts": failure_category_counts,
        "reference_canary_failure_category_counts": dict(
            sorted(
                (
                    current_promotion_contract or {}
                ).get("reference_canary_failure_category_counts", {}).items()
            )
        ),
        "full_canonical_failure_category_counts": dict(
            sorted(full_canonical_failure_category_counts.items())
        ),
        "expansion_failure_category_counts": dict(
            sorted(expansion_failure_category_counts.items())
        ),
        "open_expansion_slot_count": sum(1 for slot in expansion_slots if not slot["ready"]),
        "open_expansion_artifact_count": sum(
            1
            for result in required_expansion_review_results + required_expansion_suite_results
            if not result["passed"]
        ),
        "rule_pack_result": rule_pack_result,
        "eval_trace_gate_summary": eval_trace_gate_summary,
        "current_promotion_contract": current_promotion_contract,
        "review_cases": review_results,
        "suite_results": suite_results,
        "expansion_slots": expansion_slots,
    }
    suite_output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, summary)
    markdown_path.write_text(_markdown_report(summary), encoding="utf-8")
    return PromotionSuiteResult(
        manifest_path=manifest_path,
        output_dir=suite_output_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        summary=summary,
    )


def _eval_trace_gate_summary(
    *,
    review_results: list[dict[str, Any]],
    suite_results: list[dict[str, Any]],
) -> dict[str, Any]:
    artifacts = []
    for result in suite_results:
        artifact = _phase_eval_gate_artifact(
            result=result,
            scope="suite",
            review_case_id=None,
            review_id=None,
        )
        if artifact is not None:
            artifacts.append(artifact)
    for case in review_results:
        for result in case["results"]:
            artifact = _phase_eval_gate_artifact(
                result=result,
                scope="review",
                review_case_id=str(case["id"]),
                review_id=str(case["review_id"]),
            )
            if artifact is not None:
                artifacts.append(artifact)

    current_gates = [
        artifact
        for artifact in artifacts
        if artifact["required_for_current_promotion"] and artifact["gate_reported"]
    ]
    failed_current_gates = [
        artifact
        for artifact in current_gates
        if artifact["mode"] == "ratcheted" and not artifact["passed"]
    ]
    return {
        "schema_version": "promotion-eval-trace-gate-summary-v1",
        "eval_trace_gate_schema_version": EVAL_TRACE_GATE_SCHEMA_VERSION,
        "phase_eval_artifact_count": len(artifacts),
        "reported_gate_count": sum(1 for artifact in artifacts if artifact["gate_reported"]),
        "ratcheted_gate_count": sum(
            1 for artifact in artifacts if artifact["mode"] == "ratcheted"
        ),
        "failed_current_gate_count": len(failed_current_gates),
        "current_promotion_passed": not failed_current_gates,
        "failed_current_gates": failed_current_gates,
        "artifacts": artifacts,
    }


def _phase_eval_gate_artifact(
    *,
    result: dict[str, Any],
    scope: str,
    review_case_id: str | None,
    review_id: str | None,
) -> dict[str, Any] | None:
    path = Path(str(result.get("path") or ""))
    if path.name != "phase_eval_results.json":
        return None
    gate: dict[str, Any] = {}
    if result.get("exists"):
        payload = _read_json(path)
        raw_gate = payload.get("eval_trace_gate")
        if isinstance(raw_gate, dict):
            gate = raw_gate
    return {
        "id": str(result["id"]),
        "scope": scope,
        "review_case_id": review_case_id,
        "review_id": review_id,
        "path": str(path),
        "exists": bool(result.get("exists")),
        "required_for_current_promotion": bool(
            result.get("required_for_current_promotion")
        ),
        "gate_reported": bool(gate),
        "mode": str(gate.get("mode") or "not_reported"),
        "ratchet_scope_enabled": bool(gate.get("ratchet_scope_enabled")),
        "passed": bool(gate.get("passed")) if gate else None,
        "failure_reasons": list(gate.get("failure_reasons") or []) if gate else [],
    }
