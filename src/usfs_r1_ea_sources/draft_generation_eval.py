from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .draft_generation import DEFAULT_CONFIG_PATH as DEFAULT_DRAFT_GENERATION_CONFIG_PATH
from .draft_generation import VALIDATION_FILENAME
from .draft_generation import build_draft_generation_bundle
from .draft_generation import load_draft_generation_context


DEFAULT_EVAL_PATH = Path("config/draft_generation_eval_v1.json")
EVAL_SCHEMA_VERSION = "draft-generation-eval-results-v1"
DEFAULT_REPORT_FILENAME = "draft_generation_eval_results.json"


@dataclass(frozen=True)
class DraftGenerationEvalResult:
    output_path: Path
    summary: dict[str, Any]


def run_draft_generation_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    eval_path: Path = DEFAULT_EVAL_PATH,
    config_path: Path = DEFAULT_DRAFT_GENERATION_CONFIG_PATH,
    results_dir: Path | None = None,
) -> DraftGenerationEvalResult:
    eval_payload = json.loads(Path(eval_path).read_text(encoding="utf-8"))
    context = load_draft_generation_context(
        output_dir=output_dir,
        review_id=review_id or str(eval_payload.get("review_id") or ""),
        config_path=config_path,
    )
    review_results_dir = (
        Path(results_dir) if results_dir is not None else context.review_dir / "draft_generation"
    )
    live_validation_path = review_results_dir / VALIDATION_FILENAME
    live_validation = (
        json.loads(live_validation_path.read_text(encoding="utf-8"))
        if live_validation_path.exists()
        else None
    )
    cases = [
        _run_case(context=context, eval_case=eval_case)
        for eval_case in eval_payload.get("cases", [])
        if isinstance(eval_case, dict)
    ]
    passed_case_count = sum(case["passed"] for case in cases)
    summary = {
        "passed": all(case["passed"] for case in cases)
        and bool((live_validation or {}).get("summary", {}).get("passed")),
        "case_count": len(cases),
        "passed_case_count": passed_case_count,
        "live_validation_present": live_validation is not None,
        "live_validation_passed": bool((live_validation or {}).get("summary", {}).get("passed")),
        "output_path": str(review_results_dir / DEFAULT_REPORT_FILENAME),
    }
    body = {
        "schema_version": EVAL_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "eval_contract_path": str(Path(eval_path)),
        "config_path": str(Path(config_path)),
        "live_validation_path": str(live_validation_path),
        "cases": cases,
        "summary": summary,
    }
    output_path = review_results_dir / DEFAULT_REPORT_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return DraftGenerationEvalResult(output_path=output_path, summary=summary)


def _run_case(*, context, eval_case: dict[str, Any]) -> dict[str, Any]:
    mutation = str(eval_case.get("mutation") or "")
    requested_output_ids = None
    config_override = deepcopy(context.config)
    context_override = _clone_context(context)

    if mutation == "request_unsupported_legal_conclusion":
        requested_output_ids = list(config_override.get("section_order", [])) + [
            "legal_sufficiency_determination"
        ]
    elif mutation == "drop_citations_from_first_finding":
        _drop_citations_from_first_finding(context_override)
    elif mutation == "mark_authority_paths_stale":
        _dict(context_override.artifacts["authority_explanation_paths"].payload)["summary"][
            "validation_passed"
        ] = False
    elif mutation == "conflict_first_finding_status":
        first_row = _first_row(_dict(context_override.artifacts["compliance_review"].payload).get("findings"))
        if first_row:
            first_row["status"] = "gap"
    elif mutation == "retain_reviewer_warning_inputs":
        pass
    else:
        raise ValueError(f"Unsupported draft-generation eval mutation: {mutation}")

    bundle = build_draft_generation_bundle(
        context=context_override,
        requested_output_ids=requested_output_ids,
        config_override=config_override,
    )
    summary = _dict(bundle.validation.get("summary"))
    failure_categories = set(_dict(summary.get("failure_category_counts")).keys())
    refusal_categories = {
        str(entry.get("category") or "")
        for entry in _dict_list(bundle.refusals.get("refusals"))
    }
    unresolved_section = next(
        (
            section
            for section in _dict_list(bundle.package.get("sections"))
            if section.get("section_id") == "unresolved_issue_statements"
        ),
        {},
    )
    warning_inserted = any(
        bool(paragraph.get("warning_inserted"))
        for paragraph in _dict_list(unresolved_section.get("paragraphs"))
    )

    checks = []
    required_failure_category = eval_case.get("required_failure_category")
    if required_failure_category:
        checks.append(
            {
                "name": "required_failure_category_present",
                "passed": str(required_failure_category) in failure_categories,
                "expected": required_failure_category,
                "actual": sorted(failure_categories),
            }
        )
    required_refusal_category = eval_case.get("required_refusal_category")
    if required_refusal_category:
        checks.append(
            {
                "name": "required_refusal_category_present",
                "passed": str(required_refusal_category) in refusal_categories,
                "expected": required_refusal_category,
                "actual": sorted(refusal_categories),
            }
        )
    if eval_case.get("warning_required"):
        checks.append(
            {
                "name": "reviewer_warning_inserted",
                "passed": warning_inserted,
                "expected": True,
                "actual": warning_inserted,
            }
        )
    expected_validation_passed = eval_case.get("expected_validation_passed")
    if expected_validation_passed is not None:
        checks.append(
            {
                "name": "validation_passed_matches_expectation",
                "passed": bool(summary.get("passed")) is bool(expected_validation_passed),
                "expected": bool(expected_validation_passed),
                "actual": bool(summary.get("passed")),
            }
        )
    passed = all(check["passed"] for check in checks)
    return {
        "case_id": str(eval_case.get("case_id") or mutation),
        "mutation": mutation,
        "passed": passed,
        "checks": checks,
        "failure_categories": sorted(failure_categories),
        "refusal_categories": sorted(refusal_categories),
        "validation_passed": bool(summary.get("passed")),
    }


def _clone_context(context):
    cloned_artifacts = {
        key: artifact.__class__(
            key=artifact.key,
            path=artifact.path,
            required=artifact.required,
            exists=artifact.exists,
            parse_ok=artifact.parse_ok,
            payload=deepcopy(artifact.payload),
            sha256=artifact.sha256,
            error=artifact.error,
        )
        for key, artifact in context.artifacts.items()
    }
    return context.__class__(
        output_dir=context.output_dir,
        review_dir=context.review_dir,
        review_id=context.review_id,
        source_set_id=context.source_set_id,
        config_path=context.config_path,
        config=deepcopy(context.config),
        artifacts=cloned_artifacts,
    )


def _drop_citations_from_first_finding(context) -> None:
    decision_support = _dict(context.artifacts["decision_support"].payload)
    finding = _first_row(decision_support.get("authority_findings"))
    if finding:
        _first_row(finding.get("ea_package_evidence")).pop("citation_label", None)
        _first_row(finding.get("source_library_evidence")).pop("citation_label", None)


def _first_row(value: Any) -> dict[str, Any]:
    rows = _dict_list(value)
    return rows[0] if rows else {}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
