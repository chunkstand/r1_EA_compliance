from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .review_packet_index_common import _Artifact
from .review_packet_index_common import _OutputPaths
from .review_packet_index_common import PACKET_INDEX_FILENAME
from .review_packet_index_common import PACKET_INDEX_MARKDOWN_FILENAME
from .review_packet_index_common import PACKET_INDEX_PDF_FILENAME
from .review_packet_index_common import RENDER_MANIFEST_FILENAME
from .review_packet_index_common import ROW_INVENTORY_FILENAME
from .review_packet_index_common import ROW_INVENTORY_MARKDOWN_FILENAME
from .review_packet_index_common import VALIDATION_FILENAME


def _output_paths(index_dir: Path) -> _OutputPaths:
    return _OutputPaths(
        row_inventory_path=index_dir / ROW_INVENTORY_FILENAME,
        row_inventory_markdown_path=index_dir / ROW_INVENTORY_MARKDOWN_FILENAME,
        render_manifest_path=index_dir / RENDER_MANIFEST_FILENAME,
        packet_index_path=index_dir / PACKET_INDEX_FILENAME,
        packet_index_markdown_path=index_dir / PACKET_INDEX_MARKDOWN_FILENAME,
        packet_index_pdf_path=index_dir / PACKET_INDEX_PDF_FILENAME,
        validation_path=index_dir / VALIDATION_FILENAME,
    )


def _load_artifacts(*, review_dir: Path) -> dict[str, _Artifact]:
    specs = {
        "compliance_matrix": (review_dir / "compliance_matrix.json", "json", True),
        "compliance_matrix_markdown": (review_dir / "compliance_matrix.md", "text", True),
        "compliance_matrix_pdf": (review_dir / "compliance_matrix.pdf", "pdf", True),
        "compliance_review": (review_dir / "compliance_review.json", "json", True),
        "applicable_authorities": (
            review_dir / "applicability" / "applicable_authorities.json",
            "json",
            True,
        ),
        "generated_rule_pack": (
            review_dir / "applicability" / "generated_rule_pack.json",
            "json",
            True,
        ),
        "non_applicable_authorities": (
            review_dir / "applicability" / "non_applicable_authorities.json",
            "json",
            True,
        ),
        "search_coverage_certificates": (
            review_dir / "applicability" / "search_coverage_certificates.json",
            "json",
            True,
        ),
        "non_applicable_authority_appendix": (
            review_dir / "non_applicable_authority_appendix.json",
            "json",
            True,
        ),
        "forest_plan_component_findings": (
            review_dir / "forest_plan_component_findings.json",
            "json",
            True,
        ),
        "forest_plan_applicable_standard_coverage": (
            review_dir / "forest_plan_applicable_standard_coverage.json",
            "json",
            True,
        ),
        "decision_support_report": (
            review_dir / "decision_support" / "ea_consistency_decision_support.json",
            "json",
            True,
        ),
        "final_qa_report": (
            review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
            "json",
            True,
        ),
    }
    return {
        key: _load_artifact(key=key, path=path, artifact_type=artifact_type, required=required)
        for key, (path, artifact_type, required) in specs.items()
    }


def _load_artifact(
    *,
    key: str,
    path: Path,
    artifact_type: str,
    required: bool,
) -> _Artifact:
    if not path.exists():
        return _Artifact(
            key=key,
            path=path,
            required=required,
            artifact_type=artifact_type,
            payload=None,
            text="",
            exists=False,
            parse_ok=False,
            sha256=None,
            error=f"Missing artifact: {path}",
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8") if artifact_type != "pdf" else ""
        if artifact_type == "json":
            payload = json.loads(text)
            parse_ok = isinstance(payload, dict)
        elif artifact_type == "text":
            payload = text
            parse_ok = True
        elif artifact_type == "pdf":
            payload = {"pdf_header_valid": raw.startswith(b"%PDF-")}
            parse_ok = bool(payload["pdf_header_valid"])
        else:
            payload = text
            parse_ok = True
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _Artifact(
            key=key,
            path=path,
            required=required,
            artifact_type=artifact_type,
            payload=None,
            text="",
            exists=True,
            parse_ok=False,
            sha256=digest,
            error=str(exc),
        )
    return _Artifact(
        key=key,
        path=path,
        required=required,
        artifact_type=artifact_type,
        payload=payload,
        text=text,
        exists=True,
        parse_ok=parse_ok,
        sha256=digest,
        error=None if parse_ok else f"Artifact did not parse as {artifact_type}: {path}",
    )
