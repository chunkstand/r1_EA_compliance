from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

from .forest_plan_component_eval_coverage import (
    DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
)
from .forest_plan_component_eval_coverage import resolve_forest_plan_component_eval_file
from .forest_plan_component_eval_cases import _evaluate_cases
from .forest_plan_component_eval_cases import _failure_category_counts
from .forest_plan_component_eval_cases import _metrics
from .forest_plan_component_eval_models import FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
from .forest_plan_component_eval_models import ForestPlanComponentEvalResult
from .forest_plan_component_eval_models import SAFE_REVIEW_ID_RE
from .forest_plan_component_eval_validation import _checks
from .forest_plan_component_eval_validation import _review_id
from .forest_plan_component_eval_validation import _source_set_id
from .forest_plan_component_eval_validation import _validate_contract

def run_forest_plan_component_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    review_dir: Path | None = None,
    eval_file: Path | None = None,
    manifest_path: Path = DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
    output_path: Path | None = None,
) -> ForestPlanComponentEvalResult:
    """Evaluate forest-plan component findings against adjudicated component cases."""

    resolved_eval_file = _resolve_eval_file(
        review_id=review_id,
        review_dir=review_dir,
        eval_file=eval_file,
        manifest_path=manifest_path,
    )
    contract = _read_json(resolved_eval_file)
    _validate_contract(contract)
    resolved_review_dir = _resolve_review_dir(
        output_dir=Path(output_dir),
        review_id=review_id or str(contract.get("review_id") or ""),
        review_dir=review_dir,
    )
    resolved_output_path = Path(output_path) if output_path else (
        resolved_review_dir / "forest_plan_component_eval_results.json"
    )
    artifacts = _load_review_artifacts(resolved_review_dir)
    case_results = _evaluate_cases(
        cases=contract["cases"],
        artifacts=artifacts,
    )
    metrics = _metrics(case_results)
    checks = _checks(
        contract=contract,
        artifacts=artifacts,
        case_results=case_results,
        metrics=metrics,
    )
    summary = {
        "schema_version": FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "eval_id": contract.get("eval_id"),
        "review_id": _review_id(artifacts) or contract.get("review_id"),
        "source_set_id": _source_set_id(artifacts) or contract.get("source_set_id"),
        "eval_file": str(resolved_eval_file),
        "review_dir": str(resolved_review_dir),
        "output_path": str(resolved_output_path),
        "case_count": len(case_results),
        "passed_case_count": sum(1 for result in case_results if result["passed"]),
        "failed_case_count": sum(1 for result in case_results if not result["passed"]),
        "metrics": metrics,
        "failure_category_counts": _failure_category_counts(case_results),
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
    payload = {
        "schema_version": FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "eval_id": summary["eval_id"],
        "review_id": summary["review_id"],
        "source_set_id": summary["source_set_id"],
        "passed": summary["passed"],
        "summary": summary,
        "case_results": case_results,
        "artifact_paths": artifacts["artifact_paths"],
        "contract": {
            "schema_version": contract.get("schema_version"),
            "eval_id": contract.get("eval_id"),
            "review_id": contract.get("review_id"),
            "source_set_id": contract.get("source_set_id"),
            "case_count": len(contract["cases"]),
            "metric_thresholds": contract.get("metric_thresholds", {}),
            "coverage_requirements": contract.get("coverage_requirements", {}),
        },
    }
    _write_json(resolved_output_path, payload)
    return ForestPlanComponentEvalResult(
        eval_file=resolved_eval_file,
        review_dir=resolved_review_dir,
        output_path=resolved_output_path,
        summary=summary,
    )

def _resolve_eval_file(
    *,
    review_id: str | None,
    review_dir: Path | None,
    eval_file: Path | None,
    manifest_path: Path,
) -> Path:
    if eval_file is not None:
        return Path(eval_file)
    if review_id:
        return resolve_forest_plan_component_eval_file(
            review_id=review_id,
            manifest_path=manifest_path,
        )
    raise ValueError(
        "forest-plan-component-eval requires --eval-file or a tracked --review-id in the "
        "forest-plan component coverage manifest"
    )

def _resolve_review_dir(
    *,
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
) -> Path:
    if review_dir is not None:
        return Path(review_dir)
    if not review_id:
        raise ValueError("review_id is required when review_dir is not supplied.")
    if not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ValueError(f"unsafe review_id: {review_id!r}")
    return output_dir / "reviews" / review_id

def _load_review_artifacts(review_dir: Path) -> dict[str, Any]:
    specs = {
        "component_findings": ("forest_plan_component_findings.json", True, "json"),
        "standard_coverage": ("forest_plan_applicable_standard_coverage.json", True, "json"),
        "reviewer_resolution_queue": ("forest_plan_reviewer_resolution_queue.json", True, "json"),
    }
    artifacts: dict[str, Any] = {
        "artifact_errors": [],
        "artifact_paths": {},
    }
    for name, (relative_path, required, kind) in specs.items():
        path = review_dir / relative_path
        artifacts["artifact_paths"][name] = str(path)
        if not path.exists():
            artifacts[name] = [] if kind == "jsonl" else {}
            if required:
                artifacts["artifact_errors"].append(
                    {
                        "artifact": name,
                        "path": str(path),
                        "failure_category": "review_artifact_missing",
                    }
                )
            continue
        try:
            artifacts[name] = _read_json(path)
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            artifacts[name] = {}
            artifacts["artifact_errors"].append(
                {
                    "artifact": name,
                    "path": str(path),
                    "failure_category": "review_artifact_unreadable",
                    "message": str(exc),
                }
            )
    return artifacts

def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return value

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
