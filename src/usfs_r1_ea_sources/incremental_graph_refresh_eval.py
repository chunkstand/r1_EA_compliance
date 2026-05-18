from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .artifact_utils import _dict
from .artifact_utils import _source_set_id_from_catalog


INCREMENTAL_GRAPH_REFRESH_EVAL_SCHEMA_VERSION = "incremental-graph-refresh-eval-results-v1"
DEFAULT_INCREMENTAL_GRAPH_REFRESH_EVAL_PATH = Path("config/incremental_graph_refresh_eval_v1.json")
DEFAULT_INCREMENTAL_GRAPH_REFRESH_RESULTS_PATH = Path(
    "evaluations/incremental_graph_refresh/incremental_graph_refresh_eval_results.json"
)


@dataclass(frozen=True)
class IncrementalGraphRefreshEvalResult:
    output_path: Path
    summary: dict


def run_incremental_graph_refresh_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    eval_path: Path = DEFAULT_INCREMENTAL_GRAPH_REFRESH_EVAL_PATH,
    output_path: Path | None = None,
) -> IncrementalGraphRefreshEvalResult:
    output_dir = Path(output_dir)
    eval_path = Path(eval_path)
    contract = json.loads(eval_path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "incremental-graph-refresh-eval-v1":
        raise ValueError(
            "Unsupported incremental graph refresh eval schema_version: "
            f"{contract.get('schema_version')!r}"
        )
    resolved_source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    currentness_path = (
        output_dir
        / "derived"
        / resolved_source_set_id
        / "authority_currentness"
        / "authority_currentness_report.json"
    )
    graph_summary_path = (
        output_dir
        / "derived"
        / resolved_source_set_id
        / "knowledge_graph"
        / "nepa_3d_graph_summary.json"
    )
    graph_health_path = (
        output_dir
        / "derived"
        / resolved_source_set_id
        / "knowledge_graph"
        / "graph_health_eval_report.json"
    )
    graph_accuracy_path = (
        output_dir
        / "derived"
        / resolved_source_set_id
        / "knowledge_graph"
        / "graph_accuracy_eval_report.json"
    )
    results_path = (
        Path(output_path)
        if output_path is not None
        else output_dir / DEFAULT_INCREMENTAL_GRAPH_REFRESH_RESULTS_PATH
    )

    currentness = _read_json_if_exists(currentness_path)
    graph_summary = _read_json_if_exists(graph_summary_path)
    graph_health = _read_json_if_exists(graph_health_path)
    graph_accuracy = _read_json_if_exists(graph_accuracy_path)

    currentness_summary = _dict((currentness or {}).get("summary"))
    currentness_validation = _dict((currentness or {}).get("validation"))
    graph_health_summary = _dict((graph_health or {}).get("summary"))
    graph_accuracy_summary = _dict((graph_accuracy or {}).get("summary"))
    readiness_blocker_counts = _dict((graph_summary or {}).get("readiness_blocker_counts"))
    documented_source_change_count = int(currentness_summary.get("documented_source_gap_count") or 0) + int(
        currentness_summary.get("documented_source_non_addition_count") or 0
    )
    observed_blocker_types = sorted(
        blocker_type
        for blocker_type, count in readiness_blocker_counts.items()
        if int(count or 0) > 0
    )
    required_blocker_types = [
        str(value)
        for value in contract.get("required_blocker_types", [])
        if str(value).strip()
    ]
    allowed_source_set_ids = [
        str(value)
        for value in contract.get("allowed_source_set_ids", [])
        if str(value).strip()
    ]
    checks = [
        _check(
            "incremental_graph_refresh_contract_loaded",
            contract.get("contract_id") == "incremental-graph-refresh-eval-v1",
            "incremental-graph-refresh-eval-v1",
            contract.get("contract_id"),
        ),
        _check(
            "source_set_allowed_by_contract",
            not allowed_source_set_ids or resolved_source_set_id in allowed_source_set_ids,
            allowed_source_set_ids or ["any"],
            resolved_source_set_id,
        ),
        _check(
            "currentness_report_present",
            currentness is not None,
            True,
            currentness is not None,
        ),
        _check(
            "currentness_source_set_matches",
            (currentness or {}).get("source_set_id") == resolved_source_set_id,
            resolved_source_set_id,
            (currentness or {}).get("source_set_id"),
        ),
        _check(
            "currentness_validation_passed",
            currentness_validation.get("passed") is True
            and currentness_summary.get("validation_passed") is True,
            True,
            bool(currentness_validation.get("passed") is True and currentness_summary.get("validation_passed") is True),
        ),
        _check(
            "graph_summary_present",
            graph_summary is not None,
            True,
            graph_summary is not None,
        ),
        _check(
            "graph_summary_source_set_matches",
            (graph_summary or {}).get("source_set_id") == resolved_source_set_id,
            resolved_source_set_id,
            (graph_summary or {}).get("source_set_id"),
        ),
        _check(
            "graph_summary_validation_passed",
            (graph_summary or {}).get("validation_passed") is True
            and int((graph_summary or {}).get("failed_validation_check_count") or 0) == 0,
            True,
            bool(
                (graph_summary or {}).get("validation_passed") is True
                and int((graph_summary or {}).get("failed_validation_check_count") or 0) == 0
            ),
        ),
        _check(
            "graph_health_eval_present",
            graph_health is not None,
            True,
            graph_health is not None,
        ),
        _check(
            "graph_health_eval_passed",
            graph_health_summary.get("passed") is True,
            True,
            graph_health_summary.get("passed"),
        ),
        _check(
            "graph_accuracy_eval_present",
            graph_accuracy is not None,
            True,
            graph_accuracy is not None,
        ),
        _check(
            "graph_accuracy_eval_passed",
            graph_accuracy_summary.get("passed") is True,
            True,
            graph_accuracy_summary.get("passed"),
        ),
        _check(
            "documented_source_change_count_meets_floor",
            documented_source_change_count
            >= int(contract.get("minimum_documented_source_change_count", 1)),
            int(contract.get("minimum_documented_source_change_count", 1)),
            documented_source_change_count,
        ),
        _check(
            "superseded_replacement_confirmed_family_count_meets_floor",
            int(currentness_summary.get("superseded_replacement_confirmed_family_count") or 0)
            >= int(contract.get("minimum_superseded_replacement_confirmed_family_count", 1)),
            int(contract.get("minimum_superseded_replacement_confirmed_family_count", 1)),
            int(currentness_summary.get("superseded_replacement_confirmed_family_count") or 0),
        ),
        _check(
            "temporal_lineage_record_count_meets_floor",
            int(currentness_summary.get("temporal_lineage_record_count") or 0)
            >= int(contract.get("minimum_temporal_lineage_record_count", 1)),
            int(contract.get("minimum_temporal_lineage_record_count", 1)),
            int(currentness_summary.get("temporal_lineage_record_count") or 0),
        ),
        _check(
            "required_refresh_blocker_types_visible",
            set(required_blocker_types).issubset(set(observed_blocker_types)),
            sorted(required_blocker_types),
            observed_blocker_types,
        ),
    ]
    passed = all(check["passed"] for check in checks)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": INCREMENTAL_GRAPH_REFRESH_EVAL_SCHEMA_VERSION,
        "contract_id": contract.get("contract_id"),
        "contract_version": contract.get("version"),
        "source_set_id": resolved_source_set_id,
        "currentness_report_path": str(currentness_path),
        "graph_summary_path": str(graph_summary_path),
        "graph_health_report_path": str(graph_health_path),
        "graph_accuracy_report_path": str(graph_accuracy_path),
        "checks": checks,
        "summary": {
            "passed": passed,
            "source_set_id": resolved_source_set_id,
            "documented_source_change_count": documented_source_change_count,
            "documented_source_gap_count": int(
                currentness_summary.get("documented_source_gap_count") or 0
            ),
            "documented_source_non_addition_count": int(
                currentness_summary.get("documented_source_non_addition_count") or 0
            ),
            "superseded_replacement_confirmed_family_count": int(
                currentness_summary.get("superseded_replacement_confirmed_family_count") or 0
            ),
            "temporal_lineage_record_count": int(
                currentness_summary.get("temporal_lineage_record_count") or 0
            ),
            "observed_blocker_types": observed_blocker_types,
            "readiness_blocker_counts": readiness_blocker_counts,
            "output_path": str(results_path),
        },
    }
    results_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return IncrementalGraphRefreshEvalResult(output_path=results_path, summary=body["summary"])


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, expected: object, actual: object) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
