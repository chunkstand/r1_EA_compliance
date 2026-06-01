from __future__ import annotations

from pathlib import Path

from .artifact_utils import _read_json
from .phase_eval_support import _sha256_file


def rule_claim_path_context(
    *,
    explicit_links_path: Path | None,
    selected_eval_path: Path,
    selected_summary: dict | None,
    compliance_summary: dict,
) -> dict:
    selected_links_path = (selected_summary or {}).get("links_path")
    compliance_links_path = compliance_summary.get("rule_claim_links_path")
    failed_checks = []
    if explicit_links_path is not None and not _same_path(
        selected_links_path,
        explicit_links_path,
    ):
        failed_checks.append("explicit_rule_claim_links_path_matches_summary")
    if compliance_links_path and selected_links_path and not _same_path(
        selected_links_path,
        Path(str(compliance_links_path)),
    ):
        failed_checks.append("rule_claim_links_path_matches_compliance_review")
    if explicit_links_path is not None and compliance_links_path and not _same_path(
        explicit_links_path,
        Path(str(compliance_links_path)),
    ):
        failed_checks.append("explicit_rule_claim_links_path_matches_compliance_review")
    return {
        "explicit_rule_claim_links_path": (
            str(explicit_links_path) if explicit_links_path is not None else None
        ),
        "selected_rule_claim_links_path": selected_links_path,
        "selected_rule_claim_eval_path": str(selected_eval_path),
        "compliance_review_rule_claim_links_path": compliance_links_path,
        "rule_claim_links_are_canonical": bool(
            (selected_summary or {}).get("links_dir_is_canonical", True)
        ),
        "uses_sidecar_rule_claim_links": not bool(
            (selected_summary or {}).get("links_dir_is_canonical", True)
        ),
        "canonical_links_dir": (selected_summary or {}).get("canonical_links_dir"),
        "links_dir": (selected_summary or {}).get("links_dir"),
        "failed_path_checks": failed_checks,
    }


def with_rule_claim_direct_eval_override(
    *,
    direct_eval_coverage: dict,
    downstream_manifest: dict | None,
    downstream_manifest_path: Path,
    result_path: Path,
    source_set_id: str,
) -> dict:
    coverage = dict(direct_eval_coverage)
    statuses = dict(coverage.get("source_set_phase_statuses") or {})
    statuses["rule_claim_binding"] = _rule_claim_direct_eval_status(
        downstream_manifest=downstream_manifest,
        downstream_manifest_path=downstream_manifest_path,
        result_path=result_path,
        source_set_id=source_set_id,
    )
    coverage["source_set_phase_statuses"] = statuses
    return coverage


def _rule_claim_direct_eval_status(
    *,
    downstream_manifest: dict | None,
    downstream_manifest_path: Path,
    result_path: Path,
    source_set_id: str,
) -> dict:
    base = {
        "phase_name": "rule_claim_binding",
        "producer": "downstream_direct_evaluation",
        "coverage_class": "direct_eval_required",
        "status": "direct_eval_missing",
        "summary_present": result_path.exists(),
        "summary_path": str(result_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": ["missing_required_direct_eval"],
        "contract_id": "rule-claim-direct-eval-v1",
        "details": {"lane_id": "rule_claim_eval", "manifest_path": str(downstream_manifest_path)},
    }
    lane = _downstream_manifest_lane(downstream_manifest, "rule_claim_eval")
    if lane is None:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    contract_path = downstream_manifest_path.parent / str(lane["contract_path"])
    expected_contract_sha = _sha256_file(contract_path) if contract_path.exists() else None
    base["contract_id"] = str(lane.get("eval_id") or "")
    base["details"].update(
        {
            "contract_path": str(contract_path),
            "expected_contract_sha256": expected_contract_sha,
            "expected_eval_id": lane.get("eval_id"),
        }
    )
    result = _read_json(result_path) if result_path.exists() else None
    if not isinstance(result, dict):
        return base
    if any(key not in result for key in ("eval_id", "source_set_id", "passed", "contract")):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    actual_contract_sha = (
        result.get("contract") or {}
    ).get("sha256") if isinstance(result.get("contract"), dict) else None
    base["summary_present"] = True
    base["case_count"] = result.get("case_count")
    base["hard_negative_case_count"] = result.get("hard_negative_case_count")
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_eval_id": result.get("eval_id"),
            "actual_source_set_id": result.get("source_set_id"),
            "actual_contract_sha256": actual_contract_sha,
            "checks": result.get("checks", []),
        }
    )
    if (
        str(result.get("eval_id") or "") != str(lane.get("eval_id") or "")
        or str(result.get("source_set_id") or "") != source_set_id
        or actual_contract_sha != expected_contract_sha
    ):
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base
    if not bool(result.get("passed")):
        base["status"] = "direct_eval_failed"
        base["direct_eval_present"] = True
        base["failure_reasons"] = ["direct_eval_threshold_failed"]
        return base
    base["status"] = "direct_eval_present"
    base["direct_eval_present"] = True
    base["direct_eval_passed"] = True
    base["failure_reasons"] = []
    return base


def _downstream_manifest_lane(manifest: dict | None, lane_id: str) -> dict | None:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "downstream-direct-eval-v1":
        return None
    return next(
        (
            lane
            for lane in manifest.get("required_lanes", [])
            if isinstance(lane, dict) and str(lane.get("lane_id") or "") == lane_id
        ),
        None,
    )


def _same_path(left: object, right: Path | None) -> bool:
    if not left or right is None:
        return False
    try:
        return Path(str(left)).expanduser().resolve() == Path(right).expanduser().resolve()
    except OSError:
        return False
