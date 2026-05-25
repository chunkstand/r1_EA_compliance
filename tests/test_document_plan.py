from __future__ import annotations

from pathlib import Path
import json

from usfs_r1_ea_sources.document_plan import DEFAULT_LANE_REGISTRY_PATH
from usfs_r1_ea_sources.document_plan import DEFAULT_REQUEST_SCHEMA_PATH
from usfs_r1_ea_sources.document_plan import load_document_lane_registry
from usfs_r1_ea_sources.document_plan import load_document_request
from usfs_r1_ea_sources.document_plan import plan_document_request
from usfs_r1_ea_sources.document_plan import run_document_plan
from usfs_r1_ea_sources.document_plan import validate_document_lane_registry
from usfs_r1_ea_sources.document_plan import validate_document_request


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "document_plan"


def test_document_lane_registry_is_generic_and_scoped_to_three_generator_lanes() -> None:
    registry = load_document_lane_registry(REPO_ROOT / DEFAULT_LANE_REGISTRY_PATH)

    assert validate_document_lane_registry(registry) == []
    assert [lane["lane_id"] for lane in registry["lanes"]] == [
        "project_sow_requirements_package",
        "decision_support_report",
        "reviewed_draft_packet",
    ]
    assert {entry["lane_id"] for entry in registry["scoped_out_lanes"]} == {
        "review_packet_index",
        "final_qa_certification",
    }
    assert all(lane["expected_output_files"] for lane in registry["lanes"])
    registry_text = (REPO_ROOT / DEFAULT_LANE_REGISTRY_PATH).read_text(encoding="utf-8")
    assert "v1-cg-ecid-compliance-review" not in registry_text
    assert "source-set-4fb59e9eb43045cb" not in registry_text


def test_document_request_schema_accepts_supported_and_refusal_fixtures() -> None:
    schema = _read_json(REPO_ROOT / DEFAULT_REQUEST_SCHEMA_PATH)
    for fixture_name in (
        "project_sow_request.json",
        "decision_support_request.json",
        "reviewed_draft_request.json",
        "legal_sufficiency_request.json",
    ):
        request = _read_json(FIXTURE_DIR / fixture_name)
        assert validate_document_request(request, schema) == [], fixture_name


def test_document_request_schema_rejects_supported_lane_with_wrong_input_mode() -> None:
    schema = _read_json(REPO_ROOT / DEFAULT_REQUEST_SCHEMA_PATH)
    request = _read_json(FIXTURE_DIR / "project_sow_request.json")
    request["input_mode"] = "review_id"

    errors = validate_document_request(request, schema)

    assert errors
    assert any("project_sow_intake" in error for error in errors)


def test_plan_document_request_routes_supported_lanes() -> None:
    registry = load_document_lane_registry(REPO_ROOT / DEFAULT_LANE_REGISTRY_PATH)
    cases = (
        ("project_sow_request.json", "project_sow_requirements_package", "project-sow-package"),
        ("decision_support_request.json", "decision_support_report", "ea-consistency-document"),
        ("reviewed_draft_request.json", "reviewed_draft_packet", "draft-generate"),
    )

    for fixture_name, expected_lane_id, expected_command in cases:
        request = load_document_request(
            FIXTURE_DIR / fixture_name,
            schema_path=REPO_ROOT / DEFAULT_REQUEST_SCHEMA_PATH,
        )
        decision = plan_document_request(request, registry)

        assert decision.status == "planned", fixture_name
        assert decision.lane_id == expected_lane_id, fixture_name
        assert expected_command in str(decision.generator_command_preview), fixture_name
        assert decision.validation_command_preview is not None, fixture_name
        assert decision.refusal_category is None, fixture_name


def test_plan_document_request_refuses_unsupported_legal_conclusion_request() -> None:
    registry = load_document_lane_registry(REPO_ROOT / DEFAULT_LANE_REGISTRY_PATH)
    request = load_document_request(
        FIXTURE_DIR / "legal_sufficiency_request.json",
        schema_path=REPO_ROOT / DEFAULT_REQUEST_SCHEMA_PATH,
    )

    decision = plan_document_request(request, registry)

    assert decision.status == "refused"
    assert decision.lane_id is None
    assert decision.refusal_category == "unsupported_legal_conclusion"
    assert "does not generate legal sufficiency determinations" in str(decision.refusal_reason)


def test_plan_document_request_refuses_missing_required_identifier() -> None:
    registry = load_document_lane_registry(REPO_ROOT / DEFAULT_LANE_REGISTRY_PATH)
    request = load_document_request(
        FIXTURE_DIR / "decision_support_request.json",
        schema_path=REPO_ROOT / DEFAULT_REQUEST_SCHEMA_PATH,
    )
    request["inputs"] = {}

    decision = plan_document_request(request, registry)

    assert decision.status == "refused"
    assert decision.lane_id == "decision_support_report"
    assert decision.refusal_category == "missing_required_identifier"
    assert decision.missing_inputs == ("review_id",)


def test_run_document_plan_writes_artifacts_for_supported_request(tmp_path: Path) -> None:
    request_path = FIXTURE_DIR / "project_sow_request.json"

    result = run_document_plan(
        request_path=request_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is True
    assert result.plan_path.exists()
    assert result.markdown_path.exists()
    assert result.request_copy_path.exists()

    payload = _read_json(result.plan_path)
    assert payload["status"] == "planned"
    assert payload["selected_lane"]["lane_id"] == "project_sow_requirements_package"
    assert "project_sow_package.json" in payload["selected_lane"]["expected_output_files"]
    assert payload["next_commands"]["generator_command"].endswith("project-sow-package --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json --output-dir source_library")
    assert not any(result.results_dir.glob("project_sow_package.json"))


def test_run_document_plan_writes_refusal_artifacts_for_unsupported_request(tmp_path: Path) -> None:
    request_path = FIXTURE_DIR / "legal_sufficiency_request.json"

    result = run_document_plan(
        request_path=request_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is False
    payload = _read_json(result.plan_path)
    assert payload["status"] == "refused"
    assert payload["refusal"]["category"] == "unsupported_legal_conclusion"
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "## Refusal" in markdown
    assert "unsupported_legal_conclusion" in markdown


def test_run_document_plan_writes_invalid_request_artifacts(tmp_path: Path) -> None:
    request_path = tmp_path / "invalid_request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": "document-request-v1",
                "request_id": "invalid-request",
                "request_summary": "Missing the required request class.",
                "input_mode": "review_id",
                "requested_output": "Need a route.",
                "inputs": {"review_id": "v1-cg-ecid-compliance-review"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_document_plan(
        request_path=request_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is False
    payload = _read_json(result.plan_path)
    assert payload["status"] == "invalid_request"
    assert payload["refusal"]["category"] == "invalid_request"
    assert payload["selected_lane"] is None


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
