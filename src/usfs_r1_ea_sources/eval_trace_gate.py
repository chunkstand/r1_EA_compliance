from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import sqlite3

from .eval_trace_contract import DEFAULT_EVAL_TRACE_CONTRACT_PATH
from .eval_trace_contract import load_eval_trace_contract
from .eval_trace_inventory import INVENTORY_RESULT_SCHEMA_VERSION
from .eval_trace_inventory import REPO_ROOT
from .eval_trace_store import STORE_SCHEMA_VERSION
from .records import sha256_file


EVAL_TRACE_GATE_SCHEMA_VERSION = "eval-trace-gate-status-v1"
DEFAULT_EVAL_TRACE_INVENTORY_PATH = Path(
    "source_library/evaluations/eval_trace_inventory/eval_trace_inventory_results.json"
)
DEFAULT_EVAL_TRACE_STORE_PATH = Path(
    "source_library/evaluations/eval_trace/system_eval_trace.sqlite"
)
REQUIRED_STORE_TABLES = (
    "system_eval_runs",
    "system_eval_cases",
    "system_eval_case_results",
    "system_eval_scores",
    "trace_runs",
    "trace_spans",
)
EVAL_ROW_TABLES = (
    "system_eval_runs",
    "system_eval_cases",
    "system_eval_case_results",
    "system_eval_scores",
)
TRACE_ROW_TABLES = ("trace_runs", "trace_spans")


@dataclass(frozen=True)
class EvalTraceGateResult:
    status: dict[str, Any]
    phase: dict[str, Any] | None


def build_eval_trace_gate_phase(
    *,
    output_dir: Path,
    source_set_id: str | None,
    review_id: str | None = None,
    inventory_path: Path | None = None,
    sqlite_path: Path | None = None,
    contract_path: Path = DEFAULT_EVAL_TRACE_CONTRACT_PATH,
    repo_root: Path = REPO_ROOT,
) -> EvalTraceGateResult:
    status = evaluate_eval_trace_gate(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=review_id,
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        contract_path=contract_path,
        repo_root=repo_root,
    )
    if not status["phase_included"]:
        return EvalTraceGateResult(status=status, phase=None)

    blocking = bool(status["ratchet_scope_enabled"])
    phase_passed = bool(status["passed"]) if blocking else True
    phase = {
        "name": "first_class_eval_trace",
        "passed": phase_passed,
        "reviewer_ready": phase_passed,
        "failure_reasons": [] if phase_passed else list(status["failure_reasons"]),
        "details": status,
    }
    return EvalTraceGateResult(status=status, phase=phase)


def evaluate_eval_trace_gate(
    *,
    output_dir: Path,
    source_set_id: str | None,
    review_id: str | None = None,
    inventory_path: Path | None = None,
    sqlite_path: Path | None = None,
    contract_path: Path = DEFAULT_EVAL_TRACE_CONTRACT_PATH,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = _resolve_path(output_dir, repo_root)
    inventory_path = _resolve_path(
        inventory_path or _default_inventory_path(output_dir), repo_root
    )
    sqlite_path = _resolve_path(sqlite_path or _default_store_path(output_dir), repo_root)
    contract = load_eval_trace_contract(_resolve_path(contract_path, repo_root))
    self_reference_paths = _self_reference_paths(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=review_id,
    )
    ratchet = _ratchet_status(
        contract,
        source_set_id=source_set_id,
        review_id=review_id,
    )
    inventory = _inventory_status(
        inventory_path,
        source_set_id=source_set_id,
        review_id=review_id,
        repo_root=repo_root,
        self_reference_paths=self_reference_paths,
    )
    store = _store_status(
        sqlite_path,
        source_set_id=source_set_id,
        review_id=review_id,
        repo_root=repo_root,
        self_reference_paths=self_reference_paths,
    )

    target_evidence_present = inventory["target_matches"] or store["target_matches"]
    ratcheted = bool(ratchet["enabled"])
    phase_included = ratcheted or target_evidence_present
    failure_reasons: list[str] = []
    if ratcheted:
        if not inventory["exists"]:
            failure_reasons.append("eval_trace_inventory_missing")
        if not store["exists"]:
            failure_reasons.append("eval_trace_store_missing")
    if inventory["exists"] and (ratcheted or inventory["target_matches"]):
        failure_reasons.extend(inventory["failure_reasons"])
    if store["exists"] and (ratcheted or store["target_matches"]):
        failure_reasons.extend(store["failure_reasons"])
    failure_reasons = sorted(set(failure_reasons))
    passed = not failure_reasons

    return {
        "schema_version": EVAL_TRACE_GATE_SCHEMA_VERSION,
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "source_set_id": source_set_id,
        "review_id": review_id,
        "mode": "ratcheted" if ratcheted else "optional",
        "ratchet_scope_enabled": ratcheted,
        "ratchet_scope_reasons": ratchet["reasons"],
        "phase_included": phase_included,
        "evidence_status": _evidence_status(
            phase_included=phase_included,
            ratcheted=ratcheted,
            passed=passed,
            target_evidence_present=target_evidence_present,
        ),
        "passed": passed,
        "failure_reasons": failure_reasons,
        "inventory": inventory,
        "store": store,
    }


def _default_inventory_path(output_dir: Path) -> Path:
    return output_dir / "evaluations" / "eval_trace_inventory" / "eval_trace_inventory_results.json"


def _default_store_path(output_dir: Path) -> Path:
    return output_dir / "evaluations" / "eval_trace" / "system_eval_trace.sqlite"


def _ratchet_status(
    contract: dict[str, Any],
    *,
    source_set_id: str | None,
    review_id: str | None,
) -> dict[str, Any]:
    scopes = contract.get("ratchet_scopes")
    if not isinstance(scopes, dict):
        scopes = {}
    enabled_source_set_ids = set(_strings(scopes.get("enabled_source_set_ids")))
    enabled_review_ids = set(_strings(scopes.get("enabled_review_ids")))
    reasons = []
    if source_set_id and source_set_id in enabled_source_set_ids:
        reasons.append("source_set_id")
    if review_id and review_id in enabled_review_ids:
        reasons.append("review_id")
    return {"enabled": bool(reasons), "reasons": reasons}


def _inventory_status(
    path: Path,
    *,
    source_set_id: str | None,
    review_id: str | None,
    repo_root: Path,
    self_reference_paths: set[Path],
) -> dict[str, Any]:
    base = {
        "path": _display_path(path, repo_root),
        "exists": path.exists(),
        "target_matches": False,
        "passed": False,
        "schema_version": None,
        "source_set_id": None,
        "review_id": None,
        "missing_required_artifact_count": None,
        "missing_required_link_count": None,
        "stale_artifact_count": None,
        "current_hash_mismatch_count": None,
        "failure_reasons": [],
    }
    if not path.exists():
        return base

    failure_reasons: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            **base,
            "exists": True,
            "failure_reasons": ["eval_trace_inventory_malformed"],
            "error": str(exc),
        }
    if not isinstance(payload, dict):
        return {
            **base,
            "exists": True,
            "failure_reasons": ["eval_trace_inventory_malformed"],
        }

    scope = payload.get("scope") if isinstance(payload.get("scope"), dict) else {}
    actual_source_set_id = _string(scope.get("source_set_id"))
    actual_review_id = _string(scope.get("review_id"))
    if payload.get("schema_version") != INVENTORY_RESULT_SCHEMA_VERSION:
        failure_reasons.append("eval_trace_inventory_schema_mismatch")
    if not payload.get("passed"):
        failure_reasons.append("eval_trace_inventory_failed")
    if source_set_id and actual_source_set_id and actual_source_set_id != source_set_id:
        failure_reasons.append("eval_trace_inventory_source_set_mismatch")
    if review_id and actual_review_id and actual_review_id != review_id:
        failure_reasons.append("eval_trace_inventory_review_id_mismatch")
    missing_required_link_count = _missing_required_link_count(payload)
    if missing_required_link_count:
        failure_reasons.append("eval_trace_inventory_missing_required_links")
    stale_artifact_count = len(_dict_list(payload.get("stale_artifacts")))
    current_hash_mismatch_count = _inventory_current_hash_mismatch_count(
        payload,
        repo_root=repo_root,
        self_reference_paths=self_reference_paths,
    )
    if stale_artifact_count or current_hash_mismatch_count:
        failure_reasons.append("eval_trace_inventory_stale")

    target_matches = bool(actual_source_set_id == source_set_id) and (
        not review_id or actual_review_id == review_id
    )
    return {
        **base,
        "target_matches": target_matches,
        "passed": not failure_reasons,
        "schema_version": _string(payload.get("schema_version")),
        "source_set_id": actual_source_set_id,
        "review_id": actual_review_id,
        "missing_required_artifact_count": payload.get("missing_required_artifact_count"),
        "missing_required_link_count": missing_required_link_count,
        "stale_artifact_count": stale_artifact_count,
        "current_hash_mismatch_count": current_hash_mismatch_count,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _store_status(
    path: Path,
    *,
    source_set_id: str | None,
    review_id: str | None,
    repo_root: Path,
    self_reference_paths: set[Path],
) -> dict[str, Any]:
    base = {
        "path": _display_path(path, repo_root),
        "exists": path.exists(),
        "target_matches": False,
        "passed": False,
        "store_schema_version": STORE_SCHEMA_VERSION,
        "row_counts": {table: 0 for table in REQUIRED_STORE_TABLES},
        "missing_tables": [],
        "missing_eval_row_count": 0,
        "missing_trace_row_count": 0,
        "blocked_eval_run_count": 0,
        "stale_artifact_count": 0,
        "source_set_ids": [],
        "review_ids": [],
        "source_set_mismatch_count": 0,
        "review_id_mismatch_count": 0,
        "failure_reasons": [],
    }
    if not path.exists():
        return base

    try:
        with sqlite3.connect(path) as connection:
            connection.row_factory = sqlite3.Row
            existing_tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            missing_tables = [
                table for table in REQUIRED_STORE_TABLES if table not in existing_tables
            ]
            row_counts = {
                table: _table_count(connection, table) if table in existing_tables else 0
                for table in REQUIRED_STORE_TABLES
            }
            blocked_eval_runs = (
                _blocked_eval_runs(connection)
                if "system_eval_runs" in existing_tables
                else []
            )
            source_set_ids = _distinct_scope_values(
                connection,
                existing_tables=existing_tables,
                column="source_set_id",
            )
            review_ids = _distinct_scope_values(
                connection,
                existing_tables=existing_tables,
                column="review_id",
            )
            stale_artifact_count = (
                _store_stale_artifact_count(
                    connection,
                    repo_root=repo_root,
                    self_reference_paths=self_reference_paths,
                )
                if "system_eval_runs" in existing_tables
                else 0
            )
    except sqlite3.Error as exc:
        return {
            **base,
            "failure_reasons": ["eval_trace_store_unreadable"],
            "error": str(exc),
        }

    missing_eval_row_count = sum(1 for table in EVAL_ROW_TABLES if row_counts[table] == 0)
    missing_trace_row_count = sum(1 for table in TRACE_ROW_TABLES if row_counts[table] == 0)
    source_set_mismatch_count = (
        sum(1 for value in source_set_ids if value != source_set_id) if source_set_id else 0
    )
    review_id_mismatch_count = (
        sum(1 for value in review_ids if value != review_id) if review_id else 0
    )
    failure_reasons = []
    if missing_tables:
        failure_reasons.append("eval_trace_store_missing_tables")
    if missing_eval_row_count:
        failure_reasons.append("eval_trace_store_missing_eval_rows")
    if missing_trace_row_count:
        failure_reasons.append("eval_trace_store_missing_trace_rows")
    if blocked_eval_runs:
        failure_reasons.append("eval_trace_store_blocked_eval_runs")
    if stale_artifact_count:
        failure_reasons.append("eval_trace_store_stale")
    if source_set_mismatch_count:
        failure_reasons.append("eval_trace_store_source_set_mismatch")
    if review_id_mismatch_count:
        failure_reasons.append("eval_trace_store_review_id_mismatch")

    target_matches = bool(source_set_id and source_set_id in source_set_ids) and (
        not review_id or review_id in review_ids
    )
    return {
        **base,
        "target_matches": target_matches,
        "passed": not failure_reasons,
        "row_counts": row_counts,
        "missing_tables": missing_tables,
        "missing_eval_row_count": missing_eval_row_count,
        "missing_trace_row_count": missing_trace_row_count,
        "blocked_eval_run_count": len(blocked_eval_runs),
        "blocked_eval_runs": blocked_eval_runs,
        "stale_artifact_count": stale_artifact_count,
        "source_set_ids": source_set_ids,
        "review_ids": review_ids,
        "source_set_mismatch_count": source_set_mismatch_count,
        "review_id_mismatch_count": review_id_mismatch_count,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _missing_required_link_count(inventory: dict[str, Any]) -> int:
    status = inventory.get("required_link_status")
    if not isinstance(status, dict):
        return 1
    checks = status.get("checks")
    if not isinstance(checks, list):
        return 1
    return sum(1 for check in checks if isinstance(check, dict) and not check.get("passed"))


def _inventory_current_hash_mismatch_count(
    inventory: dict[str, Any],
    *,
    repo_root: Path,
    self_reference_paths: set[Path],
) -> int:
    mismatches = 0
    for record in _dict_list(inventory.get("artifact_families")):
        expected_hash = _string(record.get("artifact_sha256"))
        if not expected_hash:
            continue
        path = _resolve_artifact_path(record.get("path"), repo_root)
        if path.resolve() in self_reference_paths:
            continue
        if path.exists() and sha256_file(path) != expected_hash:
            mismatches += 1
    return mismatches


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


def _blocked_eval_runs(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT eval_run_id, eval_name, origin_artifact_ref, failure_reason, status, passed
        FROM system_eval_runs
        WHERE status != 'passed' OR passed != 1
        ORDER BY eval_run_id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _distinct_scope_values(
    connection: sqlite3.Connection,
    *,
    existing_tables: set[str],
    column: str,
) -> list[str]:
    values: set[str] = set()
    for table in ("system_eval_runs", "trace_runs"):
        if table not in existing_tables:
            continue
        rows = connection.execute(
            f"SELECT DISTINCT {column} AS value FROM {table} "
            f"WHERE {column} IS NOT NULL AND {column} != ''"
        ).fetchall()
        values.update(str(row["value"]) for row in rows if row["value"])
    return sorted(values)


def _store_stale_artifact_count(
    connection: sqlite3.Connection,
    *,
    repo_root: Path,
    self_reference_paths: set[Path],
) -> int:
    count = 0
    rows = connection.execute(
        """
        SELECT origin_artifact_ref, current_artifact_sha256
        FROM system_eval_runs
        WHERE origin_artifact_ref IS NOT NULL AND origin_artifact_ref != ''
        """
    ).fetchall()
    for row in rows:
        expected_hash = _string(row["current_artifact_sha256"])
        path = _resolve_artifact_path(row["origin_artifact_ref"], repo_root)
        if path.resolve() in self_reference_paths:
            continue
        if expected_hash and path.exists() and sha256_file(path) != expected_hash:
            count += 1
    return count


def _self_reference_paths(
    *,
    output_dir: Path,
    source_set_id: str | None,
    review_id: str | None,
) -> set[Path]:
    paths = set()
    if source_set_id:
        paths.add(
            (
                output_dir
                / "derived"
                / source_set_id
                / "evidence_graph"
                / "phase_eval_results.json"
            ).resolve()
        )
    if review_id:
        paths.add((output_dir / "reviews" / review_id / "phase_eval_results.json").resolve())
    return paths


def _evidence_status(
    *,
    phase_included: bool,
    ratcheted: bool,
    passed: bool,
    target_evidence_present: bool,
) -> str:
    if passed and phase_included:
        return "passed"
    if ratcheted:
        return "blocked"
    if target_evidence_present:
        return "optional_blocked"
    return "not_configured"


def _resolve_artifact_path(value: object, repo_root: Path) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else repo_root / path


def _resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item or "").strip()]


def _string(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
