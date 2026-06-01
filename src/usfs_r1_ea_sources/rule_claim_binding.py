from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import sqlite3

from .claim_extraction import _load_validated_claims_for_eval
from .claim_extraction import _source_set_id_from_catalog
from .claim_extraction import default_claims_path
from .rule_claim_binding_runtime import RULE_CLAIM_LINK_SCHEMA_VERSION
from .rule_claim_binding_runtime import _build_links
from .rule_claim_binding_runtime import _safe_segment
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack
from .source_set_support import source_derived_dir


RULE_CLAIM_LINK_VALIDATION_SCHEMA_VERSION = "rule-claim-link-validation-v0"
RULE_CLAIM_LINK_EVAL_SCHEMA_VERSION = "rule-claim-link-eval-v1"
RULE_CLAIM_LINK_EVAL_RESULTS_SCHEMA_VERSION = "rule-claim-link-eval-results-v1"
DEFAULT_RULE_CLAIM_EVAL_PATH = Path("config/rule_claim_link_eval_seed.json")
DEFAULT_TOP_K = 5
SUPPORTED_RULE_CLAIM_EVAL_FILTERS = {"rule_id", "claim_type", "source_record_id"}
REQUIRED_LINK_FIELDS = {
    "artifact_path",
    "artifact_sha256",
    "authority_level",
    "chunk_char_end",
    "chunk_char_start",
    "chunk_id",
    "citation_label",
    "claim_id",
    "claim_text",
    "claim_type",
    "content_sha256",
    "document_role",
    "link_id",
    "matched_terms",
    "parser_name",
    "parser_version",
    "rank",
    "rule_id",
    "rule_pack_id",
    "rule_pack_version",
    "rule_query",
    "rule_source_filters",
    "schema_version",
    "score",
    "source_char_end",
    "source_char_start",
    "source_record_id",
    "source_set_id",
    "validation_status",
}
REQUIRED_GAP_FIELDS = {
    "gap_id",
    "reason",
    "rule_id",
    "rule_pack_id",
    "rule_pack_version",
    "rule_query",
    "rule_source_filters",
    "schema_version",
    "source_set_id",
    "validation_status",
}


@dataclass(frozen=True)
class RuleClaimLinkResult:
    source_set_id: str
    links_dir: Path
    links_path: Path
    gaps_path: Path
    sqlite_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class RuleClaimLinkEvalResult:
    links_path: Path
    eval_file: Path
    output_path: Path
    summary: dict


def build_rule_claim_links(
    *,
    output_dir: Path,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    claims_path: Path | None = None,
    links_dir: Path | None = None,
    top_k: int = DEFAULT_TOP_K,
    allow_partial_claims: bool = False,
) -> RuleClaimLinkResult:
    """Build deterministic links from compliance rules to validated source claims."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    rule_pack_path = Path(rule_pack_path)
    if not rule_pack_path.exists():
        raise FileNotFoundError(f"Missing compliance rule pack: {rule_pack_path}")
    rule_pack = load_rule_pack(rule_pack_path)
    rule_pack_validation = validate_rule_pack(rule_pack)
    if not rule_pack_validation["passed"]:
        failed = ", ".join(_failed_check_names(rule_pack_validation))
        raise ValueError(f"Compliance rule pack is invalid. Failed checks: {failed}")

    claims_path = claims_path or default_claims_path(output_dir, source_set_id)
    claims_summary, claims_validation = _claim_artifact_readiness(claims_path)
    claims_reviewer_ready = bool(claims_summary and claims_summary.get("reviewer_ready"))
    claims_validation_passed = bool(claims_validation and claims_validation.get("passed"))
    claims = _load_validated_claims_for_eval(
        claims_path,
        require_reviewer_ready=not allow_partial_claims,
    )
    canonical_links_dir = default_rule_claim_links_dir(
        output_dir,
        source_set_id=source_set_id,
        rule_pack=rule_pack,
    )
    custom_links_dir = links_dir is not None
    links_dir = Path(links_dir) if links_dir is not None else canonical_links_dir
    if custom_links_dir:
        _ensure_custom_links_dir_noncanonical(
            requested_dir=links_dir,
            canonical_dir=canonical_links_dir,
            label="links_dir",
        )
    links_dir.mkdir(parents=True, exist_ok=True)
    links_path = links_dir / "rule_claim_links.jsonl"
    gaps_path = links_dir / "rule_claim_link_gaps.jsonl"
    sqlite_path = links_dir / "rule_claim_links.sqlite"
    validation_path = links_dir / "rule_claim_link_validation.json"
    summary_path = links_dir / "summary.json"

    created_at = _utc_now()
    links, gaps = _build_links(
        source_set_id=source_set_id,
        rule_pack=rule_pack,
        claims=claims,
        top_k=top_k,
        created_at=created_at,
    )
    _write_jsonl(links_path, links)
    _write_jsonl(gaps_path, gaps)
    validation = validate_rule_claim_links(
        output_dir=output_dir,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
        claims_path=claims_path,
        links_path=links_path,
        gaps_path=gaps_path,
        allow_partial_claims=allow_partial_claims,
    )
    if validation["passed"]:
        _write_sqlite_links(
            sqlite_path,
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            links=links,
            gaps=gaps,
        )
        validation = _with_additional_checks(
            validation,
            _sqlite_link_checks(
                sqlite_path,
                expected_link_count=len(links),
                expected_gap_count=len(gaps),
            ),
            allow_partial_claims=allow_partial_claims,
        )
        if not validation["passed"]:
            sqlite_path.unlink(missing_ok=True)
    else:
        sqlite_path.unlink(missing_ok=True)

    rule_ids = [str(rule["id"]) for rule in rule_pack["rules"]]
    linked_rule_ids = sorted({str(link["rule_id"]) for link in links})
    gap_rule_ids = sorted({str(gap["rule_id"]) for gap in gaps})
    link_counts_by_rule = Counter(str(link["rule_id"]) for link in links)
    summary = {
        "schema_version": RULE_CLAIM_LINK_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "output_dir": str(output_dir),
        "links_dir": str(links_dir),
        "canonical_links_dir": str(canonical_links_dir),
        "links_dir_is_canonical": links_dir.resolve() == canonical_links_dir.resolve(),
        "links_path": str(links_path),
        "gaps_path": str(gaps_path),
        "sqlite_path": str(sqlite_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "claims_path": str(claims_path),
        "rule_pack_path": str(rule_pack_path),
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "top_k": top_k,
        "allow_partial_claims": allow_partial_claims,
        "claims_validation_passed": claims_validation_passed,
        "claims_reviewer_ready": claims_reviewer_ready,
        "rule_count": len(rule_ids),
        "claim_count": len(claims),
        "link_count": len(links),
        "gap_count": len(gaps),
        "linked_rule_count": len(linked_rule_ids),
        "gap_rule_count": len(gap_rule_ids),
        "rules_without_links": gap_rule_ids,
        "links_per_rule": {rule_id: link_counts_by_rule.get(rule_id, 0) for rule_id in rule_ids},
        "claim_type_counts": dict(Counter(link["claim_type"] for link in links)),
        "source_record_count": len({link["source_record_id"] for link in links}),
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"] and claims_reviewer_ready,
    }
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
    return RuleClaimLinkResult(
        source_set_id=source_set_id,
        links_dir=links_dir,
        links_path=links_path,
        gaps_path=gaps_path,
        sqlite_path=sqlite_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
    )


def validate_rule_claim_links(
    *,
    output_dir: Path,
    source_set_id: str,
    rule_pack_path: Path,
    claims_path: Path,
    links_path: Path,
    gaps_path: Path,
    allow_partial_claims: bool = False,
) -> dict:
    from .rule_claim_binding_validation import validate_rule_claim_links as _validate

    return _validate(
        output_dir=output_dir,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
        claims_path=claims_path,
        links_path=links_path,
        gaps_path=gaps_path,
        allow_partial_claims=allow_partial_claims,
    )


def run_rule_claim_link_eval(
    *,
    links_path: Path,
    eval_file: Path,
    top_k: int = DEFAULT_TOP_K,
    output_dir: Path | None = None,
) -> RuleClaimLinkEvalResult:
    from .rule_claim_binding_eval import run_rule_claim_link_eval as _run_eval

    return _run_eval(
        links_path=links_path,
        eval_file=eval_file,
        top_k=top_k,
        output_dir=output_dir,
    )


def default_rule_claim_links_dir(
    output_dir: Path,
    *,
    source_set_id: str | None = None,
    rule_pack: dict | None = None,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    if rule_pack is None:
        rule_pack = load_rule_pack(rule_pack_path)
    return (
        source_derived_dir(output_dir / "derived", source_set_id)
        / "rule_claim_links"
        / _safe_segment(str(rule_pack["rule_pack_id"]))
        / _safe_segment(str(rule_pack["version"]))
    )


def default_rule_claim_links_path(
    output_dir: Path,
    *,
    source_set_id: str | None = None,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
) -> Path:
    return default_rule_claim_links_dir(
        output_dir,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
    ) / "rule_claim_links.jsonl"


def links_by_rule(links: list[dict], *, limit: int | None = None) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for link in sorted(
        links,
        key=lambda item: (
            str(item.get("rule_id") or ""),
            int(item.get("rank") or 0),
            -float(item.get("score") or 0),
        ),
    ):
        rule_id = str(link.get("rule_id") or "")
        if limit is None or len(grouped[rule_id]) < limit:
            grouped[rule_id].append(link)
    return dict(grouped)


def _load_validated_links_for_eval(links_path: Path) -> list[dict]:
    from .rule_claim_binding_eval import _load_validated_links_for_eval as _load

    return _load(links_path)

def _claim_artifact_readiness(claims_path: Path) -> tuple[dict | None, dict | None]:
    claims_dir = Path(claims_path).parent
    summary_path = claims_dir / "summary.json"
    validation_path = claims_dir / "claim_validation.json"
    summary = _read_json(summary_path) if summary_path.exists() else None
    validation = _read_json(validation_path) if validation_path.exists() else None
    return summary, validation


def _write_sqlite_links(
    path: Path,
    *,
    source_set_id: str,
    rule_pack: dict,
    links: list[dict],
    gaps: list[dict],
) -> None:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL
            );

            CREATE TABLE rule_claim_links (
              link_id TEXT PRIMARY KEY,
              rule_id TEXT NOT NULL,
              claim_id TEXT NOT NULL,
              source_record_id TEXT NOT NULL,
              claim_type TEXT NOT NULL,
              rank INTEGER NOT NULL,
              score REAL NOT NULL,
              citation_label TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE rule_claim_gaps (
              gap_id TEXT PRIMARY KEY,
              rule_id TEXT NOT NULL,
              reason TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE INDEX idx_rule_claim_links_rule_id ON rule_claim_links(rule_id);
            CREATE INDEX idx_rule_claim_links_claim_id ON rule_claim_links(claim_id);
            CREATE INDEX idx_rule_claim_links_source_record_id ON rule_claim_links(source_record_id);
            CREATE INDEX idx_rule_claim_links_claim_type ON rule_claim_links(claim_type);
            CREATE INDEX idx_rule_claim_gaps_rule_id ON rule_claim_gaps(rule_id);
            """
        )
        metadata = {
            "schema_version": RULE_CLAIM_LINK_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "rule_pack_id": rule_pack["rule_pack_id"],
            "rule_pack_version": rule_pack["version"],
            "created_at": _utc_now(),
            "link_count": len(links),
            "gap_count": len(gaps),
        }
        for key, value in metadata.items():
            connection.execute(
                "INSERT INTO metadata VALUES (?, ?)",
                (key, json.dumps(value, sort_keys=True)),
            )
        for link in links:
            connection.execute(
                """
                INSERT INTO rule_claim_links VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link["link_id"],
                    link["rule_id"],
                    link["claim_id"],
                    link["source_record_id"],
                    link["claim_type"],
                    int(link["rank"]),
                    float(link["score"]),
                    link["citation_label"],
                    json.dumps(link, sort_keys=True),
                ),
            )
        for gap in gaps:
            connection.execute(
                "INSERT INTO rule_claim_gaps VALUES (?, ?, ?, ?)",
                (
                    gap["gap_id"],
                    gap["rule_id"],
                    gap["reason"],
                    json.dumps(gap, sort_keys=True),
                ),
            )
        connection.commit()


def _sqlite_link_checks(
    path: Path,
    *,
    expected_link_count: int,
    expected_gap_count: int,
) -> list[dict]:
    from .rule_claim_binding_validation import _sqlite_link_checks as _checks

    return _checks(
        path,
        expected_link_count=expected_link_count,
        expected_gap_count=expected_gap_count,
    )


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_claims: bool,
) -> dict:
    from .rule_claim_binding_validation import _with_additional_checks as _merge

    return _merge(
        validation,
        checks,
        allow_partial_claims=allow_partial_claims,
    )


def _output_dir_from_links_path(links_path: Path, *, source_set_id: str) -> Path:
    if not source_set_id:
        raise ValueError("Rule-claim link summary has no source_set_id.")
    if links_path.name != "rule_claim_links.jsonl":
        raise ValueError(f"Expected rule_claim_links.jsonl path, got: {links_path}")
    version_dir = links_path.parent
    pack_dir = version_dir.parent
    links_root = pack_dir.parent
    source_dir = links_root.parent
    derived_dir = source_dir.parent
    if links_root.name != "rule_claim_links" or source_dir.name != source_set_id or derived_dir.name != "derived":
        raise ValueError(
            "Rule-claim links path must be under "
            "source_library/derived/<source_set_id>/rule_claim_links/<rule_pack>/<version>/."
        )
    return derived_dir.parent


def _output_dir_from_link_summary(links_path: Path, summary: dict) -> Path:
    output_dir = summary.get("output_dir")
    if output_dir:
        return Path(str(output_dir))
    return _output_dir_from_links_path(
        links_path,
        source_set_id=str(summary.get("source_set_id") or ""),
    )


def _ensure_custom_links_dir_noncanonical(
    *,
    requested_dir: Path,
    canonical_dir: Path,
    label: str,
) -> None:
    requested = Path(requested_dir).resolve()
    canonical = Path(canonical_dir).resolve()
    if requested == canonical or canonical in requested.parents:
        raise ValueError(
            f"{label} must not point at or inside canonical rule-claim output directory: "
            f"{canonical_dir}"
        )


def _failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
