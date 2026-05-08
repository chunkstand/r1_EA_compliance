from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.review_packet_index import (
    LAND_EXCHANGE_RULE_SOURCES,
    PACKET_INDEX_SCHEMA_VERSION,
    RENDER_MANIFEST_SCHEMA_VERSION,
    ROW_INVENTORY_SCHEMA_VERSION,
    VALIDATION_SCHEMA_VERSION,
    run_review_packet_index,
)


def test_review_packet_index_generates_row_inventory_manifest_and_packet() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-1"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)

        result = run_review_packet_index(output_dir=output_dir, review_id=review_id)

        assert result.summary["passed"] is True
        assert result.row_inventory_path.exists()
        assert result.render_manifest_path.exists()
        assert result.packet_index_path.exists()
        assert result.packet_index_pdf_path.read_bytes().startswith(b"%PDF-")

        inventory = _read_json(result.row_inventory_path)
        render_manifest = _read_json(result.render_manifest_path)
        packet = _read_json(result.packet_index_path)
        validation = _read_json(result.validation_path)

        assert inventory["schema_version"] == ROW_INVENTORY_SCHEMA_VERSION
        assert render_manifest["schema_version"] == RENDER_MANIFEST_SCHEMA_VERSION
        assert packet["schema_version"] == PACKET_INDEX_SCHEMA_VERSION
        assert validation["schema_version"] == VALIDATION_SCHEMA_VERSION
        assert inventory["summary"]["applicable_authority_count"] == 1
        assert inventory["summary"]["land_exchange_row_count"] == 0
        assert inventory["summary"]["non_applicable_authority_count"] == 1
        assert inventory["summary"]["forest_plan_component_row_count"] == 1
        assert inventory["summary"]["applicable_standard_count"] == 1
        assert render_manifest["summary"]["authority_row_count"] == 1
        assert render_manifest["summary"]["forest_plan_row_count"] == 1
        assert packet["applicable_authority_rows"][0]["render_markdown_marker"] == (
            "matrix-row:authority:purpose_need"
        )
        assert validation["summary"]["failure_category_counts"] == {}


def test_review_packet_index_exposes_land_exchange_rows_as_first_class_section() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-1"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)
        _append_land_exchange_rows(review_dir, review_id=review_id)

        result = run_review_packet_index(output_dir=output_dir, review_id=review_id)

        assert result.summary["passed"] is True
        assert result.summary["land_exchange_row_count"] == len(LAND_EXCHANGE_RULE_SOURCES)

        inventory = _read_json(result.row_inventory_path)
        packet = _read_json(result.packet_index_path)
        validation = _read_json(result.validation_path)
        inventory_markdown = result.row_inventory_markdown_path.read_text(encoding="utf-8")
        packet_markdown = result.packet_index_markdown_path.read_text(encoding="utf-8")

        expected_sources = dict(LAND_EXCHANGE_RULE_SOURCES)
        assert inventory["summary"]["land_exchange_row_count"] == len(expected_sources)
        assert {
            row["rule_id"]: row["authority_source_record_id"]
            for row in packet["land_exchange_rows"]
        } == expected_sources
        assert "## Land-Exchange Rows" in inventory_markdown
        assert "## Land-Exchange Rows" in packet_markdown
        assert (
            _validation_check(validation, "land_exchange_rows_first_class_in_packet_index")[
                "passed"
            ]
            is True
        )


def test_review_packet_index_fails_when_final_qa_drops_applicable_row() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-1"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)
        _write_json(
            review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
            {
                "review_id": review_id,
                "source_set_id": "source-set-test",
                "finding_qa": {"findings": []},
                "residual_blockers_and_stop_conditions": {"blockers": []},
            },
        )

        result = run_review_packet_index(output_dir=output_dir, review_id=review_id)

        assert result.summary["passed"] is False
        assert result.summary["failure_category_counts"] == {
            "missing_applicable_authority_row": 1
        }


def _write_minimal_review(review_dir: Path, *, review_id: str) -> None:
    matrix = {
        "schema_version": "compliance-matrix-v0",
        "review_id": review_id,
        "source_set_id": "source-set-test",
        "summary": {"row_count": 1, "reviewer_ready": True},
        "rows": [
            {
                "row_id": f"matrix:{review_id}:purpose_need",
                "rule_id": "purpose_need",
                "rule_title": "Purpose and need",
                "authority_category": "regulation",
                "authority_source_record_id": "R1EA-001",
                "authority_family_ids": ["unit_purpose_need"],
                "candidate_authority_id": "candidate:purpose_need",
                "applicability_decision_id": "decision:purpose_need",
                "applicability_status": "applicable",
                "applicability_mode": "baseline",
                "status": "pass",
                "ea_package_citation": "EA-PACKAGE-001",
                "source_library_citation": "R1EA-001",
                "source_claim_ids": ["claim-1"],
            }
        ],
        "forest_plan_compliance": {
            "schema_version": "forest-plan-compliance-matrix-v0",
            "summary": {"row_count": 1, "applicable_standard_row_count": 1},
            "rows": [
                {
                    "row_id": f"forest-plan-matrix:{review_id}:component-1",
                    "component_id": "component-1",
                    "component_key": "FW-STD-1",
                    "component_type": "standard",
                    "applicability_status": "applicable",
                    "compliance_status": "complies",
                    "finding_status": "supported",
                    "standard_applied": True,
                }
            ],
        },
    }
    _write_json(review_dir / "compliance_matrix.json", matrix)
    (review_dir / "compliance_matrix.md").write_text(
        "\n".join(
            [
                "# Compliance Matrix",
                "<!-- matrix-row:authority:purpose_need -->",
                "<!-- matrix-row:forest-plan:component-1 -->",
            ]
        ),
        encoding="utf-8",
    )
    (review_dir / "compliance_matrix.pdf").write_bytes(b"%PDF-1.4\n")
    _write_json(
        review_dir / "compliance_review.json",
        {"review_id": review_id, "source_set_id": "source-set-test", "findings": matrix["rows"]},
    )
    _write_json(
        review_dir / "applicability" / "applicable_authorities.json",
        {
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "authorities": [
                {
                    "rule_template": {"rule_id": "purpose_need"},
                    "candidate_authority_id": "candidate:purpose_need",
                    "decision_id": "decision:purpose_need",
                    "status": "applicable",
                    "authority_category": "regulation",
                    "authority_family_ids": ["unit_purpose_need"],
                }
            ],
        },
    )
    _write_json(
        review_dir / "applicability" / "generated_rule_pack.json",
        {
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "rules": [{"id": "purpose_need"}],
        },
    )
    _write_json(
        review_dir / "applicability" / "non_applicable_authorities.json",
        {
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "authorities": [
                {
                    "candidate_authority_id": "candidate:not-applicable",
                    "decision_id": "decision:not-applicable",
                    "authority_category": "law",
                    "authority_family_ids": ["unit_not_applicable"],
                    "source_record_ids": ["R1EA-002"],
                    "search_coverage_certificate_ids": ["coverage:not-applicable"],
                }
            ],
        },
    )
    _write_json(
        review_dir / "applicability" / "search_coverage_certificates.json",
        {
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "certificates": [{"coverage_certificate_id": "coverage:not-applicable"}],
        },
    )
    _write_json(review_dir / "non_applicable_authority_appendix.json", {"authorities": []})
    _write_json(
        review_dir / "forest_plan_component_findings.json",
        {
            "summary": {"reviewer_ready": True},
            "findings": [
                {
                    "component_id": "component-1",
                    "component_type": "standard",
                    "applicability_status": "applicable",
                    "compliance_status": "complies",
                    "finding_status": "supported",
                }
            ],
        },
    )
    _write_json(
        review_dir / "forest_plan_applicable_standard_coverage.json",
        {
            "passed": True,
            "standards": [
                {
                    "component_id": "component-1",
                    "component_key": "FW-STD-1",
                    "applicability_status": "applicable",
                    "compliance_status": "complies",
                    "finding_status": "supported",
                    "standard_applied": True,
                }
            ],
        },
    )
    _write_json(
        review_dir / "decision_support" / "ea_consistency_decision_support.json",
        {
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "authority_findings": [{"rule_id": "purpose_need"}],
            "implementation_confirmation_checklist": [],
            "residual_risk_register": [],
        },
    )
    _write_json(
        review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
        {
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "finding_qa": {"findings": [{"rule_id": "purpose_need"}]},
            "residual_blockers_and_stop_conditions": {"blockers": []},
        },
    )


def _append_land_exchange_rows(review_dir: Path, *, review_id: str) -> None:
    matrix_path = review_dir / "compliance_matrix.json"
    matrix = _read_json(matrix_path)
    markers = []
    rows = []
    for rule_id, source_record_id in LAND_EXCHANGE_RULE_SOURCES.items():
        row = {
            "row_id": f"matrix:{review_id}:{rule_id}",
            "rule_id": rule_id,
            "rule_title": rule_id.replace("_", " ").title(),
            "authority_category": "law",
            "authority_source_record_id": source_record_id,
            "authority_family_ids": ["land_exchange_statutory_authorities"],
            "candidate_authority_id": f"candidate:{rule_id}",
            "applicability_decision_id": f"decision:{rule_id}",
            "applicability_status": "applicable",
            "applicability_mode": "conditional",
            "status": "pass",
            "ea_package_citation": "EA-PACKAGE-002",
            "source_library_citation": source_record_id,
            "source_claim_ids": [f"claim:{rule_id}"],
        }
        rows.append(row)
        markers.append(f"<!-- matrix-row:authority:{rule_id} -->")
    matrix["rows"].extend(rows)
    _write_json(matrix_path, matrix)

    markdown_path = review_dir / "compliance_matrix.md"
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8") + "\n" + "\n".join(markers) + "\n",
        encoding="utf-8",
    )

    compliance_review = _read_json(review_dir / "compliance_review.json")
    compliance_review["findings"].extend(rows)
    _write_json(review_dir / "compliance_review.json", compliance_review)

    applicable = _read_json(review_dir / "applicability" / "applicable_authorities.json")
    applicable["authorities"].extend(
        {
            "rule_template": {"rule_id": row["rule_id"]},
            "candidate_authority_id": row["candidate_authority_id"],
            "decision_id": row["applicability_decision_id"],
            "status": "applicable",
            "authority_category": "law",
            "authority_family_ids": row["authority_family_ids"],
            "source_record_ids": [row["authority_source_record_id"]],
        }
        for row in rows
    )
    _write_json(review_dir / "applicability" / "applicable_authorities.json", applicable)

    generated = _read_json(review_dir / "applicability" / "generated_rule_pack.json")
    generated["rules"].extend({"id": row["rule_id"]} for row in rows)
    _write_json(review_dir / "applicability" / "generated_rule_pack.json", generated)

    decision_support = _read_json(
        review_dir / "decision_support" / "ea_consistency_decision_support.json"
    )
    decision_support["authority_findings"].extend(
        {"rule_id": row["rule_id"]} for row in rows
    )
    _write_json(
        review_dir / "decision_support" / "ea_consistency_decision_support.json",
        decision_support,
    )

    final_qa = _read_json(
        review_dir / "final_qa" / "east_crazies_final_qa_certification.json"
    )
    final_qa["finding_qa"]["findings"].extend({"rule_id": row["rule_id"]} for row in rows)
    _write_json(review_dir / "final_qa" / "east_crazies_final_qa_certification.json", final_qa)


def _validation_check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
