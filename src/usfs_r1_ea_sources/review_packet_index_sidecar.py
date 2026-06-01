from __future__ import annotations

from pathlib import Path
from typing import Any

from .review_packet_index_common import _Artifact
from .review_packet_index_common import _dict
from .review_packet_index_common import _dict_list


def build_sidecar_lineage(artifacts: dict[str, _Artifact]) -> dict[str, Any]:
    compliance = _dict(artifacts["compliance_review"].payload)
    compliance_summary = _dict(compliance.get("summary"))
    phase_artifact = artifacts.get("phase_eval")
    phase_eval = _dict(phase_artifact.payload if phase_artifact is not None else None)
    rule_claim_phase = _phase_by_name(phase_eval, "rule_claim_binding")
    rule_claim_details = _dict(rule_claim_phase.get("details"))
    compliance_links_path = _string_or_none(compliance_summary.get("rule_claim_links_path"))
    phase_links_path = _string_or_none(rule_claim_details.get("selected_rule_claim_links_path"))
    selected_eval_path = _string_or_none(rule_claim_details.get("selected_rule_claim_eval_path"))
    direct_eval_path = _string_or_none(rule_claim_details.get("direct_eval_summary_path"))
    sidecar_used = bool(
        (compliance_links_path and not bool(compliance_summary.get("rule_claim_links_are_canonical", True)))
        or rule_claim_details.get("uses_sidecar_rule_claim_links")
    )
    path_checks = _strings(rule_claim_details.get("failed_path_checks"))
    checks = {
        "phase_eval_present_for_sidecar": bool(
            not sidecar_used or (phase_artifact and phase_artifact.exists and phase_artifact.parse_ok)
        ),
        "phase_eval_rule_claim_phase_present": bool(not sidecar_used or rule_claim_phase),
        "compliance_review_uses_sidecar_rule_claim_links": bool(
            not sidecar_used
            or (compliance_links_path and not compliance_summary.get("rule_claim_links_are_canonical", True))
        ),
        "phase_eval_uses_sidecar_rule_claim_links": bool(
            not sidecar_used or rule_claim_details.get("uses_sidecar_rule_claim_links")
        ),
        "phase_eval_rule_claim_links_match_compliance": bool(
            not sidecar_used or _same_path(phase_links_path, compliance_links_path)
        ),
        "phase_eval_rule_claim_path_checks_passed": not path_checks,
        "phase_eval_rule_claim_direct_eval_present": bool(
            not sidecar_used or rule_claim_details.get("direct_eval_status") == "direct_eval_present"
        ),
        "phase_eval_rule_claim_direct_eval_matches_selected_eval": bool(
            not sidecar_used or not selected_eval_path or _same_path(direct_eval_path, selected_eval_path)
        ),
        "phase_eval_rule_claim_phase_reviewer_ready": bool(
            not sidecar_used
            or (rule_claim_phase.get("passed") is True and rule_claim_phase.get("reviewer_ready") is True)
        ),
        "selected_rule_claim_links_path_exists": bool(
            not sidecar_used or (phase_links_path and Path(phase_links_path).exists())
        ),
        "selected_rule_claim_eval_path_exists": bool(
            not sidecar_used or (direct_eval_path and Path(direct_eval_path).exists())
        ),
    }
    return {
        "sidecar_rule_claim_links_used": sidecar_used,
        "compliance_review_rule_claim_links_path": compliance_links_path,
        "phase_eval_selected_rule_claim_links_path": phase_links_path,
        "phase_eval_selected_rule_claim_eval_path": selected_eval_path,
        "phase_eval_direct_eval_summary_path": direct_eval_path,
        "phase_eval_path": str(phase_artifact.path) if phase_artifact is not None else None,
        "rule_claim_links_are_canonical": bool(
            compliance_summary.get("rule_claim_links_are_canonical", True)
        ),
        "canonical_links_dir": compliance_summary.get("rule_claim_canonical_links_dir"),
        "links_dir": compliance_summary.get("rule_claim_links_dir"),
        "phase_eval_failed_path_checks": path_checks,
        "checks": checks,
        "failed_checks": sorted(name for name, passed in checks.items() if not passed),
    }


def sidecar_lineage_validation_checks(lineage: dict[str, Any]) -> list[dict[str, Any]]:
    if not lineage.get("sidecar_rule_claim_links_used"):
        return []
    return [
        {
            "name": f"sidecar_rule_claim_lineage_{name}",
            "passed": bool(passed),
            "failure_category": None if passed else "sidecar_rule_claim_lineage_mismatch",
            "details": {
                "sidecar_rule_claim_links_used": True,
                "compliance_review_rule_claim_links_path": lineage.get(
                    "compliance_review_rule_claim_links_path"
                ),
                "phase_eval_selected_rule_claim_links_path": lineage.get(
                    "phase_eval_selected_rule_claim_links_path"
                ),
                "phase_eval_direct_eval_summary_path": lineage.get(
                    "phase_eval_direct_eval_summary_path"
                ),
                "failed_checks": lineage.get("failed_checks", []),
            },
        }
        for name, passed in sorted(_dict(lineage.get("checks")).items())
    ]


def _phase_by_name(summary: dict[str, Any], name: str) -> dict[str, Any]:
    return next(
        (
            phase
            for phase in _dict_list(summary.get("phases"))
            if str(phase.get("name") or "") == name
        ),
        {},
    )


def _same_path(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    try:
        return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()
    except OSError:
        return False


def _string_or_none(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []
