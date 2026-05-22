from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .artifact_utils import _dict
from .artifact_utils import _dict_list
from .artifact_utils import _read_json
from .draft_generation_common import _Artifact
from .draft_generation_common import _check
from .draft_generation_common import DEFAULT_CONFIG_PATH
from .draft_generation_common import DraftGenerationContext


def load_draft_generation_context(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> DraftGenerationContext:
    output_dir = Path(output_dir)
    config_path = Path(config_path)
    config = _read_json(config_path)
    resolved_review_id = str(review_id or config.get("review_id") or "")
    if not resolved_review_id:
        raise ValueError("draft-generation config must declare review_id when --review-id is omitted")
    review_dir = output_dir / "reviews" / resolved_review_id
    artifacts = _load_artifacts(review_dir=review_dir)
    source_set_id = _resolve_source_set_id(config=config, artifacts=artifacts)
    return DraftGenerationContext(
        output_dir=output_dir,
        review_dir=review_dir,
        review_id=resolved_review_id,
        source_set_id=source_set_id,
        config_path=config_path,
        config=config,
        artifacts=artifacts,
    )


def _load_artifacts(*, review_dir: Path) -> dict[str, _Artifact]:
    specs = {
        "compliance_review": (review_dir / "compliance_review.json", True),
        "compliance_validation": (review_dir / "compliance_validation.json", True),
        "authority_explanation_paths": (review_dir / "authority_explanation_paths.json", True),
        "decision_support": (
            review_dir / "decision_support" / "ea_consistency_decision_support.json",
            True,
        ),
        "review_packet_index": (
            review_dir / "review_packet_index" / "review_packet_index.json",
            True,
        ),
        "non_applicable_authority_appendix": (
            review_dir / "non_applicable_authority_appendix.json",
            True,
        ),
        "litigation_risk_summary": (review_dir / "litigation_risk_summary.json", True),
        "authority_reviewer_resolution_report": (
            review_dir / "authority_reviewer_resolution_report.json",
            False,
        ),
        "final_qa": (
            review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
            False,
        ),
    }
    return {
        key: _load_json_artifact(key=key, path=path, required=required)
        for key, (path, required) in specs.items()
    }


def _load_json_artifact(*, key: str, path: Path, required: bool) -> _Artifact:
    if not path.exists():
        return _Artifact(
            key=key,
            path=path,
            required=required,
            exists=False,
            parse_ok=False,
            payload=None,
            sha256=None,
            error=f"Missing artifact: {path}",
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _Artifact(
            key=key,
            path=path,
            required=required,
            exists=True,
            parse_ok=False,
            payload=None,
            sha256=digest,
            error=str(exc),
        )
    return _Artifact(
        key=key,
        path=path,
        required=required,
        exists=True,
        parse_ok=isinstance(payload, dict),
        payload=payload if isinstance(payload, dict) else None,
        sha256=digest,
        error=None if isinstance(payload, dict) else f"Artifact did not parse as JSON object: {path}",
    )


def _resolve_source_set_id(*, config: dict[str, Any], artifacts: dict[str, _Artifact]) -> str:
    if config.get("source_set_id"):
        return str(config["source_set_id"])
    for key in (
        "authority_explanation_paths",
        "decision_support",
        "final_qa",
        "review_packet_index",
    ):
        payload = artifacts[key].payload if artifacts[key].parse_ok else {}
        if isinstance(payload, dict) and payload.get("source_set_id"):
            return str(payload["source_set_id"])
    return ""


def _input_checks(*, context: DraftGenerationContext, config: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "draft_generation_config_schema",
            config.get("schema_version") == "draft-generation-config-v1",
            "stale_authority",
            {"actual": config.get("schema_version"), "expected": "draft-generation-config-v1"},
        )
    )
    checks.append(
        _check(
            "draft_generation_review_id_matches_config",
            context.review_id == str(config.get("review_id") or context.review_id),
            "review_source_set_mismatch",
            {"review_id": context.review_id, "config_review_id": config.get("review_id")},
        )
    )
    checks.append(
        _check(
            "draft_generation_source_set_matches_config",
            not config.get("source_set_id") or context.source_set_id == str(config.get("source_set_id")),
            "review_source_set_mismatch",
            {"source_set_id": context.source_set_id, "config_source_set_id": config.get("source_set_id")},
        )
    )
    for artifact in context.artifacts.values():
        checks.append(
            _check(
                f"{artifact.key}_exists",
                artifact.exists or not artifact.required,
                "missing_required_artifact",
                {"path": str(artifact.path), "required": artifact.required},
            )
        )
        if artifact.exists:
            checks.append(
                _check(
                    f"{artifact.key}_parses",
                    artifact.parse_ok,
                    "missing_required_artifact",
                    {"path": str(artifact.path), "error": artifact.error},
                )
            )
    for key in (
        "compliance_review",
        "authority_explanation_paths",
        "decision_support",
        "review_packet_index",
    ):
        payload = context.payload(key)
        if not payload:
            continue
        review_id = payload.get("review_id")
        if review_id is not None:
            checks.append(
                _check(
                    f"{key}_review_id_matches",
                    str(review_id) == context.review_id,
                    "review_source_set_mismatch",
                    {"artifact_review_id": review_id, "review_id": context.review_id},
                )
            )
        source_set_id = payload.get("source_set_id")
        if source_set_id is not None and context.source_set_id:
            checks.append(
                _check(
                    f"{key}_source_set_matches",
                    str(source_set_id) == context.source_set_id,
                    "review_source_set_mismatch",
                    {
                        "artifact_source_set_id": source_set_id,
                        "source_set_id": context.source_set_id,
                    },
                )
            )
    compliance_validation = context.payload("compliance_validation")
    checks.append(
        _check(
            "compliance_validation_passed",
            bool(compliance_validation.get("passed")),
            "stale_authority",
            {"path": str(context.artifacts["compliance_validation"].path), "passed": compliance_validation.get("passed")},
        )
    )
    authority_paths = context.payload("authority_explanation_paths")
    authority_summary = _dict(authority_paths.get("summary"))
    checks.append(
        _check(
            "authority_explanation_paths_validation_passed",
            bool(authority_summary.get("validation_passed")),
            "stale_authority",
            {
                "path": str(context.artifacts["authority_explanation_paths"].path),
                "validation_passed": authority_summary.get("validation_passed"),
            },
        )
    )
    decision_support = context.payload("decision_support")
    decision_validation = _dict(decision_support.get("validation_and_replay"))
    checks.append(
        _check(
            "decision_support_validation_passed",
            bool(decision_validation.get("passed")),
            "stale_authority",
            {
                "path": str(context.artifacts["decision_support"].path),
                "validation_passed": decision_validation.get("passed"),
            },
        )
    )
    executive = _dict(decision_support.get("executive_determination"))
    checks.append(
        _check(
            "decision_support_legal_conclusion_false",
            executive.get("legal_conclusion") is False,
            "unsupported_legal_conclusion",
            {"legal_conclusion": executive.get("legal_conclusion")},
        )
    )
    final_qa = context.payload("final_qa")
    if final_qa:
        checks.append(
            _check(
                "final_qa_legal_conclusion_false",
                _dict(final_qa.get("decision_support_qa")).get("legal_conclusion") is False,
                "unsupported_legal_conclusion",
                {"legal_conclusion": _dict(final_qa.get("decision_support_qa")).get("legal_conclusion")},
            )
        )
    return checks


def _build_finding_index(context: DraftGenerationContext) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    compliance_findings = {
        str(row.get("rule_id") or row.get("id") or ""): row
        for row in _dict_list(context.payload("compliance_review").get("findings"))
        if str(row.get("rule_id") or row.get("id") or "").strip()
    }
    explanation_rows = {
        str(row.get("finding_id") or row.get("rule_id") or ""): row
        for row in _dict_list(context.payload("authority_explanation_paths").get("finding_explanation_paths"))
        if str(row.get("finding_id") or row.get("rule_id") or "").strip()
    }
    packet_rows = {
        str(row.get("rule_id") or ""): row
        for row in _dict_list(context.payload("review_packet_index").get("applicable_authority_rows"))
        if str(row.get("rule_id") or "").strip()
    }
    decision_rows = {
        str(row.get("rule_id") or ""): row
        for row in _dict_list(context.payload("decision_support").get("authority_findings"))
        if str(row.get("rule_id") or "").strip()
    }
    bundles: dict[str, dict[str, Any]] = {}
    for rule_id, decision_row in decision_rows.items():
        compliance_row = compliance_findings.get(rule_id)
        explanation_row = explanation_rows.get(rule_id)
        packet_row = packet_rows.get(rule_id)
        checks.append(
            _check(
                f"{rule_id}_has_compliance_review_row",
                compliance_row is not None,
                "contradictory_evidence",
                {"rule_id": rule_id},
            )
        )
        checks.append(
            _check(
                f"{rule_id}_has_authority_explanation_row",
                explanation_row is not None,
                "contradictory_evidence",
                {"rule_id": rule_id},
            )
        )
        checks.append(
            _check(
                f"{rule_id}_has_review_packet_row",
                packet_row is not None,
                "contradictory_evidence",
                {"rule_id": rule_id},
            )
        )
        if compliance_row is None or explanation_row is None or packet_row is None:
            continue
        checks.extend(_bundle_consistency_checks(rule_id, compliance_row, explanation_row, decision_row, packet_row))
        bundles[rule_id] = {
            "rule_id": rule_id,
            "compliance": compliance_row,
            "explanation": explanation_row,
            "decision_support": decision_row,
            "packet": packet_row,
        }
    return {
        "checks": checks,
        "bundles": bundles,
        "land_exchange_rows": _dict_list(context.payload("review_packet_index").get("land_exchange_rows")),
        "non_applicable_boundary": _dict(
            context.payload("review_packet_index").get("non_applicable_authority_boundary")
        ),
        "implementation_confirmations": _dict_list(
            context.payload("decision_support").get("implementation_confirmation_checklist")
        ),
        "residual_risks": _dict_list(context.payload("decision_support").get("residual_risk_register")),
        "accepted_risks": _dict_list(
            _dict(context.payload("final_qa").get("accepted_v1_risk_ledger")).get("risks")
        ),
        "pending_resolution_paths": _dict_list(
            context.payload("authority_explanation_paths").get("pending_resolution_paths")
        ),
        "reviewer_resolution_items": _dict_list(
            context.payload("authority_reviewer_resolution_report").get("pending_resolution_items")
        ),
        "non_applicable_rows": _dict_list(
            context.payload("non_applicable_authority_appendix").get("authorities")
        ),
    }


def _bundle_consistency_checks(
    rule_id: str,
    compliance_row: dict[str, Any],
    explanation_row: dict[str, Any],
    decision_row: dict[str, Any],
    packet_row: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = []
    checks.append(
        _check(
            f"{rule_id}_compliance_status_consistent",
            str(compliance_row.get("status") or "") == str(decision_row.get("compliance_status") or "")
            == str(packet_row.get("compliance_status") or ""),
            "contradictory_evidence",
            {
                "compliance_review": compliance_row.get("status"),
                "decision_support": decision_row.get("compliance_status"),
                "review_packet": packet_row.get("compliance_status"),
            },
        )
    )
    checks.append(
        _check(
            f"{rule_id}_applicability_status_consistent",
            str(compliance_row.get("applicability_status") or "") == str(decision_row.get("applicability_status") or "")
            == str(packet_row.get("applicability_status") or "")
            == str(explanation_row.get("applicability_status") or ""),
            "contradictory_evidence",
            {
                "compliance_review": compliance_row.get("applicability_status"),
                "decision_support": decision_row.get("applicability_status"),
                "review_packet": packet_row.get("applicability_status"),
                "authority_explanation": explanation_row.get("applicability_status"),
            },
        )
    )
    checks.append(
        _check(
            f"{rule_id}_authority_source_consistent",
            str(compliance_row.get("authority_source_record_id") or "")
            == str(decision_row.get("authority_source_record_id") or "")
            == str(packet_row.get("authority_source_record_id") or "")
            == str(explanation_row.get("authority_source_record_id") or ""),
            "contradictory_evidence",
            {
                "compliance_review": compliance_row.get("authority_source_record_id"),
                "decision_support": decision_row.get("authority_source_record_id"),
                "review_packet": packet_row.get("authority_source_record_id"),
                "authority_explanation": explanation_row.get("authority_source_record_id"),
            },
        )
    )
    return checks
