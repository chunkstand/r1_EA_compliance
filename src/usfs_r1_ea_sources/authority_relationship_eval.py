from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .source_register_proving import default_proving_output_path
from .source_register_proving import load_proving_report


AUTHORITY_RELATIONSHIP_EVAL_SCHEMA_VERSION = "authority-relationship-eval-report-v1"
DEFAULT_AUTHORITY_RELATIONSHIP_EVAL_PATH = Path("config/authority_relationship_eval_v1.json")
DEFAULT_AUTHORITY_RELATIONSHIP_TYPES_PATH = Path("config/authority_relationship_types_v1.json")
DEFAULT_AUTHORITY_ONTOLOGY_PATH = Path("config/authority_document_ontology_v1.json")


@dataclass(frozen=True)
class AuthorityRelationshipEvalResult:
    output_path: Path
    summary: dict


def run_authority_relationship_eval(
    *,
    output_dir: Path,
    report_path: Path | None = None,
    eval_path: Path = DEFAULT_AUTHORITY_RELATIONSHIP_EVAL_PATH,
    relationship_types_path: Path = DEFAULT_AUTHORITY_RELATIONSHIP_TYPES_PATH,
    ontology_path: Path = DEFAULT_AUTHORITY_ONTOLOGY_PATH,
    output_path: Path | None = None,
) -> AuthorityRelationshipEvalResult:
    output_dir = Path(output_dir)
    report = load_proving_report(output_dir, report_path)
    eval_payload = json.loads(Path(eval_path).read_text(encoding="utf-8"))
    relationship_types_payload = json.loads(
        Path(relationship_types_path).read_text(encoding="utf-8")
    )
    ontology_payload = json.loads(Path(ontology_path).read_text(encoding="utf-8"))
    allowed_relationship_types = {
        entry["relationship_type"]: entry
        for entry in relationship_types_payload.get("relationship_types", [])
    }
    parent_class_by_id = {
        entry["class_id"]: entry.get("parent_class_id")
        for entry in ontology_payload.get("classes", [])
        if entry.get("class_id")
    }
    relationships = list(report["semantic_relationships"]["relationships"])
    relationship_types_present = {row["relationship_type"] for row in relationships}
    path_patterns_present = {row["path_pattern_id"] for row in relationships}
    missing_required_provenance = [
        {
            "relationship_id": relationship["relationship_id"],
            "missing_fields": sorted(
                field
                for field in allowed_relationship_types.get(
                    relationship["relationship_type"], {}
                ).get("required_provenance_fields", [])
                if field == "supporting_source_record_ids"
                and not relationship.get("supporting_source_record_ids")
            ),
        }
        for relationship in relationships
    ]
    missing_required_provenance = [
        entry for entry in missing_required_provenance if entry["missing_fields"]
    ]
    endpoint_violations = []
    for relationship in relationships:
        rule = allowed_relationship_types.get(relationship["relationship_type"])
        if rule is None:
            endpoint_violations.append(
                {
                    "relationship_id": relationship["relationship_id"],
                    "reason": "unknown_relationship_type",
                }
            )
            continue
        if not _class_matches_allowed(
            relationship["source_class_id"],
            set(rule.get("source_class_ids", [])),
            parent_class_by_id,
        ):
            endpoint_violations.append(
                {
                    "relationship_id": relationship["relationship_id"],
                    "reason": "source_class_not_allowed",
                    "source_class_id": relationship["source_class_id"],
                }
            )
        if not _class_matches_allowed(
            relationship["target_class_id"],
            set(rule.get("target_class_ids", [])),
            parent_class_by_id,
        ):
            endpoint_violations.append(
                {
                    "relationship_id": relationship["relationship_id"],
                    "reason": "target_class_not_allowed",
                    "target_class_id": relationship["target_class_id"],
                }
            )
    selected_source_record_ids = set(report["slice"]["load_ready_source_record_ids"])
    unsupported_supporting_source_ids = sorted(
        {
            source_record_id
            for relationship in relationships
            for source_record_id in relationship.get("supporting_source_record_ids", [])
            if source_record_id not in selected_source_record_ids
        }
    )

    minimum_proving_types = set(
        eval_payload.get("minimum_proving_slice_relationship_types", [])
    )
    required_path_patterns = set(eval_payload.get("required_path_patterns", []))
    checks = [
        _check(
            "relationship_eval_contract_loaded",
            eval_payload.get("schema_version") == "authority-relationship-eval-v1",
            "authority-relationship-eval-v1",
            eval_payload.get("schema_version"),
        ),
        _check(
            "relationship_types_contract_loaded",
            relationship_types_payload.get("schema_version") == "authority-relationship-types-v1",
            "authority-relationship-types-v1",
            relationship_types_payload.get("schema_version"),
        ),
        _check(
            "minimum_proving_relationship_types_covered",
            minimum_proving_types.issubset(relationship_types_present),
            sorted(minimum_proving_types),
            sorted(relationship_types_present),
        ),
        _check(
            "required_path_patterns_covered",
            required_path_patterns.issubset(path_patterns_present),
            sorted(required_path_patterns),
            sorted(path_patterns_present),
        ),
        _check(
            "relationships_use_allowed_endpoint_classes",
            not endpoint_violations,
            [],
            endpoint_violations,
        ),
        _check(
            "required_relationship_provenance_present",
            not missing_required_provenance,
            [],
            missing_required_provenance,
        ),
        _check(
            "supporting_source_record_ids_stay_within_proving_slice",
            not unsupported_supporting_source_ids,
            [],
            unsupported_supporting_source_ids,
        ),
    ]
    passed = all(check["passed"] for check in checks)
    output_path = output_path or default_proving_output_path(
        output_dir, "authority_relationship_eval_report.json"
    )
    payload = {
        "schema_version": AUTHORITY_RELATIONSHIP_EVAL_SCHEMA_VERSION,
        "source_set_id": report["source_set_id"],
        "report_path": str(
            report_path if report_path is not None else report["summary"]["report_path"]
        ),
        "checks": checks,
        "relationship_type_counts": report["semantic_relationships"]["relationship_type_counts"],
        "path_pattern_counts": report["semantic_relationships"]["path_pattern_counts"],
        "summary": {
            "passed": passed,
            "relationship_count": len(relationships),
            "relationship_type_count": len(relationship_types_present),
            "output_path": str(output_path),
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return AuthorityRelationshipEvalResult(output_path=output_path, summary=payload["summary"])


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }


def _class_matches_allowed(
    class_id: str,
    allowed_class_ids: set[str],
    parent_class_by_id: dict[str, str | None],
) -> bool:
    current = class_id
    while current:
        if current in allowed_class_ids:
            return True
        current = parent_class_by_id.get(current)
    return False
