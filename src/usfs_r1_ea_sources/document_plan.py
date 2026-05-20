from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


DOCUMENT_LANE_REGISTRY_SCHEMA_VERSION = "document-lanes-v1"
DOCUMENT_REQUEST_SCHEMA_VERSION = "document-request-v1"
DEFAULT_LANE_REGISTRY_PATH = Path("config/document_lanes_v1.json")
DEFAULT_REQUEST_SCHEMA_PATH = Path("docs/schemas/document_request_v1.schema.json")
PLANNED_REQUEST_CLASSES = {
    "decision_support_report",
    "project_sow_requirements_package",
    "reviewed_draft_packet",
}
PROVING_BINDING_MARKERS = (
    "source-set-ba8d0feae79501b8",
    "v1-cg-ecid-compliance-review",
)
UNSUPPORTED_REQUEST_REFUSALS = {
    "final_agency_decision": (
        "unsupported_final_agency_decision",
        "This repository does not issue final agency decisions. Route requests to human decision makers after audited review artifacts exist.",
    ),
    "legal_sufficiency_determination": (
        "unsupported_legal_conclusion",
        "This repository does not generate legal sufficiency determinations. Route legal-conclusion requests to counsel after audited artifacts exist.",
    ),
    "responsible_official_approval": (
        "unsupported_responsible_official_approval",
        "This repository does not create responsible-official approval artifacts. Use audited decision support only.",
    ),
}


@dataclass(frozen=True)
class DocumentRouteDecision:
    request_id: str
    status: str
    lane_id: str | None
    required_inputs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    authoritative_config_paths: tuple[str, ...]
    authoritative_doc_paths: tuple[str, ...]
    prerequisite_artifact_hints: tuple[str, ...]
    canonical_output_dir_family: str | None
    generator_command_preview: str | None
    validation_command_preview: str | None
    refusal_category: str | None
    refusal_reason: str | None


def load_document_lane_registry(
    path: Path = DEFAULT_LANE_REGISTRY_PATH,
) -> dict[str, Any]:
    registry = _read_json(Path(path))
    errors = validate_document_lane_registry(registry)
    if errors:
        raise ValueError("Invalid document lane registry:\n- " + "\n- ".join(errors))
    return registry


def validate_document_lane_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != DOCUMENT_LANE_REGISTRY_SCHEMA_VERSION:
        errors.append("schema_version must be document-lanes-v1")

    lanes = registry.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        errors.append("lanes must be a non-empty list")
        return errors

    lane_ids: set[str] = set()
    planned_request_classes: set[str] = set()
    for index, lane in enumerate(lanes):
        prefix = f"lanes[{index}]"
        lane_id = lane.get("lane_id")
        if not isinstance(lane_id, str) or not lane_id:
            errors.append(f"{prefix}.lane_id must be a non-empty string")
        elif lane_id in lane_ids:
            errors.append(f"{prefix}.lane_id duplicates {lane_id}")
        else:
            lane_ids.add(lane_id)

        supported_request_classes = lane.get("supported_request_classes")
        if not isinstance(supported_request_classes, list) or not supported_request_classes:
            errors.append(f"{prefix}.supported_request_classes must be a non-empty list")
        else:
            for request_class in supported_request_classes:
                if request_class in planned_request_classes:
                    errors.append(
                        f"{prefix}.supported_request_classes duplicates routed request class {request_class}"
                    )
                planned_request_classes.add(request_class)

        for key in (
            "allowed_input_modes",
            "supported_decision_postures",
            "required_inputs",
            "refusal_categories",
            "authoritative_config_paths",
            "authoritative_doc_paths",
            "prerequisite_artifact_hints",
        ):
            value = lane.get(key)
            if not isinstance(value, list) or not value:
                errors.append(f"{prefix}.{key} must be a non-empty list")

        output_dir_family = lane.get("canonical_output_dir_family")
        if not isinstance(output_dir_family, str) or not output_dir_family:
            errors.append(f"{prefix}.canonical_output_dir_family must be a non-empty string")

        for command_key in ("generator_command", "validation_command"):
            command = lane.get(command_key)
            if not isinstance(command, dict):
                errors.append(f"{prefix}.{command_key} must be an object")
                continue
            if not isinstance(command.get("command"), str) or not command.get("command"):
                errors.append(f"{prefix}.{command_key}.command must be a non-empty string")
            if not isinstance(command.get("args"), list):
                errors.append(f"{prefix}.{command_key}.args must be a list")

    if planned_request_classes != PLANNED_REQUEST_CLASSES:
        errors.append(
            "lanes must route exactly the first-packet request classes: "
            + ", ".join(sorted(PLANNED_REQUEST_CLASSES))
        )

    scoped_out = registry.get("scoped_out_lanes")
    if not isinstance(scoped_out, list) or len(scoped_out) != 2:
        errors.append("scoped_out_lanes must list review_packet_index and final_qa_certification")
    else:
        scoped_out_ids = {
            entry.get("lane_id")
            for entry in scoped_out
            if isinstance(entry, dict)
        }
        if scoped_out_ids != {"review_packet_index", "final_qa_certification"}:
            errors.append(
                "scoped_out_lanes must contain review_packet_index and final_qa_certification"
            )

    payload_text = json.dumps(registry, indent=2, sort_keys=True)
    for marker in PROVING_BINDING_MARKERS:
        if marker in payload_text:
            errors.append(f"registry must not hardcode proving binding marker {marker}")

    return errors


def load_document_request(
    request_path: Path,
    *,
    schema_path: Path = DEFAULT_REQUEST_SCHEMA_PATH,
) -> dict[str, Any]:
    request = _read_json(Path(request_path))
    schema = _read_json(Path(schema_path))
    errors = validate_document_request(request, schema)
    if errors:
        raise ValueError("Invalid document request:\n- " + "\n- ".join(errors))
    return request


def validate_document_request(
    request: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    del schema

    errors: list[str] = []
    allowed_request_classes = {
        "project_sow_requirements_package",
        "decision_support_report",
        "reviewed_draft_packet",
        "legal_sufficiency_determination",
        "final_agency_decision",
        "responsible_official_approval",
    }
    allowed_decision_postures = {
        "planning_support",
        "review_support",
        "legal_conclusion",
        "final_agency_decision",
        "responsible_official_approval",
    }
    allowed_input_modes = {"project_sow_intake", "review_id"}
    allowed_input_keys = {
        "intake_path",
        "project_id",
        "results_dir",
        "review_id",
        "source_set_id",
    }
    required_top_level_fields = (
        "schema_version",
        "request_id",
        "request_class",
        "requested_decision_posture",
        "input_mode",
        "request_summary",
        "inputs",
    )

    for field in required_top_level_fields:
        if field not in request:
            errors.append(f"$.{field}: is required")

    if set(request) - set(required_top_level_fields):
        for field in sorted(set(request) - set(required_top_level_fields)):
            errors.append(f"$.{field}: additional properties are not allowed")

    if request.get("schema_version") != DOCUMENT_REQUEST_SCHEMA_VERSION:
        errors.append(
            f"$.schema_version: expected {DOCUMENT_REQUEST_SCHEMA_VERSION!r}"
        )

    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        errors.append("$.request_id: must be a non-empty string")

    request_class = request.get("request_class")
    if request_class not in allowed_request_classes:
        errors.append(
            "$.request_class: must be one of "
            + ", ".join(sorted(allowed_request_classes))
        )

    requested_decision_posture = request.get("requested_decision_posture")
    if requested_decision_posture not in allowed_decision_postures:
        errors.append(
            "$.requested_decision_posture: must be one of "
            + ", ".join(sorted(allowed_decision_postures))
        )

    input_mode = request.get("input_mode")
    if input_mode not in allowed_input_modes:
        errors.append(
            "$.input_mode: must be one of " + ", ".join(sorted(allowed_input_modes))
        )

    request_summary = request.get("request_summary")
    if not isinstance(request_summary, str) or len(request_summary) < 10:
        errors.append("$.request_summary: must be a string with at least 10 characters")

    inputs = request.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("$.inputs: must be an object")
        return errors

    unknown_input_keys = sorted(set(inputs) - allowed_input_keys)
    for key in unknown_input_keys:
        errors.append(f"$.inputs.{key}: additional properties are not allowed")

    for key, value in inputs.items():
        if key not in allowed_input_keys:
            continue
        if not isinstance(value, str) or not value:
            errors.append(f"$.inputs.{key}: must be a non-empty string")

    if request_class == "project_sow_requirements_package":
        if requested_decision_posture != "planning_support":
            errors.append(
                "$.requested_decision_posture: project_sow_requirements_package requires planning_support"
            )
        if input_mode != "project_sow_intake":
            errors.append(
                "$.input_mode: project_sow_requirements_package requires project_sow_intake"
            )
        if not str(inputs.get("intake_path") or "").strip():
            errors.append("$.inputs.intake_path: is required for project_sow_intake")

    if request_class in {"decision_support_report", "reviewed_draft_packet"}:
        if requested_decision_posture != "review_support":
            errors.append(
                "$.requested_decision_posture: review-backed request classes require review_support"
            )
        if input_mode != "review_id":
            errors.append("$.input_mode: review-backed request classes require review_id")
        if not str(inputs.get("review_id") or "").strip():
            errors.append("$.inputs.review_id: is required for review-backed request classes")

    if request_class == "legal_sufficiency_determination":
        if requested_decision_posture != "legal_conclusion":
            errors.append(
                "$.requested_decision_posture: legal_sufficiency_determination requires legal_conclusion"
            )
        if not str(inputs.get("review_id") or "").strip():
            errors.append("$.inputs.review_id: is required for legal_sufficiency_determination")

    if request_class == "final_agency_decision":
        if requested_decision_posture != "final_agency_decision":
            errors.append(
                "$.requested_decision_posture: final_agency_decision requires final_agency_decision"
            )
        if not str(inputs.get("review_id") or "").strip():
            errors.append("$.inputs.review_id: is required for final_agency_decision")

    if request_class == "responsible_official_approval":
        if requested_decision_posture != "responsible_official_approval":
            errors.append(
                "$.requested_decision_posture: responsible_official_approval requires responsible_official_approval"
            )
        if not str(inputs.get("review_id") or "").strip():
            errors.append("$.inputs.review_id: is required for responsible_official_approval")

    return errors


def plan_document_request(
    request: dict[str, Any],
    lane_registry: dict[str, Any],
) -> DocumentRouteDecision:
    registry_errors = validate_document_lane_registry(lane_registry)
    if registry_errors:
        raise ValueError("Invalid document lane registry:\n- " + "\n- ".join(registry_errors))

    request_id = str(request.get("request_id") or "")
    request_class = str(request.get("request_class") or "")
    if request_class in UNSUPPORTED_REQUEST_REFUSALS:
        refusal_category, refusal_reason = UNSUPPORTED_REQUEST_REFUSALS[request_class]
        return _refused_decision(
            request_id=request_id,
            refusal_category=refusal_category,
            refusal_reason=refusal_reason,
        )

    candidate_lanes = [
        lane
        for lane in lane_registry["lanes"]
        if request_class in lane["supported_request_classes"]
    ]
    if not candidate_lanes:
        return _refused_decision(
            request_id=request_id,
            refusal_category="unsupported_request_class",
            refusal_reason=f"Unsupported document request class: {request_class}",
        )

    requested_decision_posture = str(request.get("requested_decision_posture") or "")
    posture_matches = [
        lane
        for lane in candidate_lanes
        if requested_decision_posture in lane["supported_decision_postures"]
    ]
    if not posture_matches:
        return _refused_decision(
            request_id=request_id,
            refusal_category="unsupported_decision_posture",
            refusal_reason=(
                f"Request class {request_class} does not support decision posture "
                f"{requested_decision_posture}."
            ),
        )

    input_mode = str(request.get("input_mode") or "")
    input_mode_matches = [
        lane
        for lane in posture_matches
        if input_mode in lane["allowed_input_modes"]
    ]
    if not input_mode_matches:
        return _refused_decision(
            request_id=request_id,
            refusal_category="unsupported_input_mode",
            refusal_reason=(
                f"Request class {request_class} does not support input mode {input_mode}."
            ),
        )

    if len(input_mode_matches) != 1:
        return _refused_decision(
            request_id=request_id,
            refusal_category="ambiguous_supported_lane",
            refusal_reason=f"Expected exactly one routed lane for request class {request_class}.",
        )

    lane = input_mode_matches[0]
    inputs = request.get("inputs") or {}
    missing_inputs = tuple(
        field
        for field in lane["required_inputs"]
        if not str(inputs.get(field) or "").strip()
    )
    if missing_inputs:
        return DocumentRouteDecision(
            request_id=request_id,
            status="refused",
            lane_id=lane["lane_id"],
            required_inputs=tuple(lane["required_inputs"]),
            missing_inputs=missing_inputs,
            authoritative_config_paths=tuple(lane["authoritative_config_paths"]),
            authoritative_doc_paths=tuple(lane["authoritative_doc_paths"]),
            prerequisite_artifact_hints=tuple(lane["prerequisite_artifact_hints"]),
            canonical_output_dir_family=lane["canonical_output_dir_family"],
            generator_command_preview=None,
            validation_command_preview=None,
            refusal_category="missing_required_identifier",
            refusal_reason="Missing required inputs: " + ", ".join(missing_inputs),
        )

    return DocumentRouteDecision(
        request_id=request_id,
        status="planned",
        lane_id=lane["lane_id"],
        required_inputs=tuple(lane["required_inputs"]),
        missing_inputs=(),
        authoritative_config_paths=tuple(lane["authoritative_config_paths"]),
        authoritative_doc_paths=tuple(lane["authoritative_doc_paths"]),
        prerequisite_artifact_hints=tuple(lane["prerequisite_artifact_hints"]),
        canonical_output_dir_family=lane["canonical_output_dir_family"],
        generator_command_preview=render_command_preview(
            lane["generator_command"],
            inputs=request.get("inputs") or {},
        ),
        validation_command_preview=render_command_preview(
            lane["validation_command"],
            inputs=request.get("inputs") or {},
        ),
        refusal_category=None,
        refusal_reason=None,
    )


def render_command_preview(
    command: dict[str, Any],
    *,
    inputs: dict[str, Any],
    output_dir: str = "source_library",
) -> str:
    format_values = _SafeFormatDict(
        {
            "output_dir": output_dir,
            **{key: str(value) for key, value in inputs.items() if value is not None},
        }
    )
    parts = [
        "PYTHONPATH=src",
        "python",
        "-m",
        "usfs_r1_ea_sources",
        str(command["command"]),
    ]
    for token in command.get("args", []):
        parts.append(str(token).format_map(format_values))
    return " ".join(parts)


def _refused_decision(
    *,
    request_id: str,
    refusal_category: str,
    refusal_reason: str,
) -> DocumentRouteDecision:
    return DocumentRouteDecision(
        request_id=request_id,
        status="refused",
        lane_id=None,
        required_inputs=(),
        missing_inputs=(),
        authoritative_config_paths=(),
        authoritative_doc_paths=(),
        prerequisite_artifact_hints=(),
        canonical_output_dir_family=None,
        generator_command_preview=None,
        validation_command_preview=None,
        refusal_category=refusal_category,
        refusal_reason=refusal_reason,
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class _SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
