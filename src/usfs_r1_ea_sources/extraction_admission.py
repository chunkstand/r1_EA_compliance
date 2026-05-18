from __future__ import annotations

from pathlib import Path
import json


VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION = (
    "verified-extraction-admission-contract-v0"
)
DEFAULT_VERIFIED_EXTRACTION_ADMISSION_CONTRACT_PATH = Path(
    "config/verified_extraction_admission_contract.json"
)


def load_verified_extraction_admission_contract(
    path: Path | None = None,
) -> dict[str, object]:
    contract_path = Path(path) if path is not None else DEFAULT_VERIFIED_EXTRACTION_ADMISSION_CONTRACT_PATH
    if not contract_path.exists():
        return {
            "schema_version": VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION,
            "contracts": [],
        }
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Verified extraction admission contract must be a JSON object.")
    schema_version = str(payload.get("schema_version") or "")
    if schema_version != VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported verified extraction admission contract schema_version: "
            f"{schema_version!r}."
        )
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise ValueError("Verified extraction admission contract must define a contracts list.")
    normalized_contracts = []
    for index, raw_contract in enumerate(contracts):
        if not isinstance(raw_contract, dict):
            raise ValueError(
                "Verified extraction admission contract entries must be JSON objects: "
                f"index={index}."
            )
        contract_id = str(raw_contract.get("contract_id") or "").strip()
        if not contract_id:
            raise ValueError(
                "Verified extraction admission contract entries must define contract_id."
            )
        required_source_record_ids = sorted(
            {
                str(value).strip()
                for value in raw_contract.get("required_source_record_ids", [])
                if str(value).strip()
            }
        )
        required_record_selectors = [
            _normalize_selector(selector, contract_id=contract_id, index=selector_index)
            for selector_index, selector in enumerate(
                raw_contract.get("required_record_selectors", []),
                start=1,
            )
        ]
        if not required_source_record_ids and not required_record_selectors:
            raise ValueError(
                "Verified extraction admission contract entries must define at least one "
                "required_source_record_id or required_record_selector."
            )
        normalized_contracts.append(
            {
                "contract_id": contract_id,
                "description": str(raw_contract.get("description") or "").strip() or None,
                "required_source_record_ids": required_source_record_ids,
                "required_record_selectors": required_record_selectors,
                "require_direct_extraction": bool(raw_contract.get("require_direct_extraction")),
            }
        )
    return {
        "schema_version": VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION,
        "contracts": normalized_contracts,
    }


def matched_verified_extraction_contracts(
    source_record_ids: list[str] | set[str] | tuple[str, ...] | None = None,
    *,
    records: list[dict] | None = None,
    contract_path: Path | None = None,
) -> dict[str, object]:
    record_map = {
        str(record.get("source_record_id") or "").strip(): record
        for record in (records or [])
        if str(record.get("source_record_id") or "").strip()
    }
    source_record_id_set = {
        str(value).strip()
        for value in (source_record_ids or [])
        if str(value).strip()
    }
    source_record_id_set.update(record_map)
    payload = load_verified_extraction_admission_contract(contract_path)
    matched_contracts = []
    required_source_record_ids: set[str] = set()
    require_direct_extraction = False
    for contract in payload.get("contracts", []):
        contract_required_ids = set(contract.get("required_source_record_ids", []))
        if contract_required_ids and not contract_required_ids.issubset(source_record_id_set):
            continue
        selector_source_record_ids: set[str] = set()
        for selector in contract.get("required_record_selectors", []):
            selector_source_record_ids.update(
                _selector_source_record_ids(
                    record_map=record_map,
                    selector=selector,
                )
            )
        if not contract_required_ids and not selector_source_record_ids:
            continue
        present_ids = sorted(contract_required_ids | selector_source_record_ids)
        matched_contracts.append(
            {
                "contract_id": contract.get("contract_id"),
                "description": contract.get("description"),
                "required_source_record_ids": present_ids,
                "required_record_selectors": contract.get("required_record_selectors", []),
                "matched_source_record_ids": present_ids,
                "require_direct_extraction": bool(contract.get("require_direct_extraction")),
            }
        )
        required_source_record_ids.update(present_ids)
        require_direct_extraction = require_direct_extraction or bool(
            contract.get("require_direct_extraction")
        )
    return {
        "contract_path": str(
            Path(contract_path)
            if contract_path is not None
            else DEFAULT_VERIFIED_EXTRACTION_ADMISSION_CONTRACT_PATH
        ),
        "contracts": matched_contracts,
        "required_source_record_ids": sorted(required_source_record_ids),
        "require_direct_extraction": require_direct_extraction,
    }


def _normalize_selector(raw_selector: object, *, contract_id: str, index: int) -> dict[str, object]:
    if not isinstance(raw_selector, dict):
        raise ValueError(
            "Verified extraction admission required_record_selectors must be JSON objects: "
            f"contract_id={contract_id!r}, index={index}."
        )
    return {
        "source_record_ids": _normalized_string_list(raw_selector.get("source_record_ids", [])),
        "exclude_source_record_ids": _normalized_string_list(
            raw_selector.get("exclude_source_record_ids", [])
        ),
        "loader_contracts": _normalized_string_list(raw_selector.get("loader_contracts", [])),
        "source_partitions": _normalized_string_list(raw_selector.get("source_partitions", [])),
        "parser_admission_classes": _normalized_string_list(
            raw_selector.get("parser_admission_classes", [])
        ),
        "expected_parsers": _normalized_string_list(raw_selector.get("expected_parsers", [])),
        "source_statuses": _normalized_string_list(raw_selector.get("source_statuses", [])),
        "document_types": _normalized_string_list(raw_selector.get("document_types", [])),
        "url_classes": _normalized_string_list(raw_selector.get("url_classes", [])),
        "currentness_status_contains": _normalized_string_list(
            raw_selector.get("currentness_status_contains", [])
        ),
        "currentness_status_not_contains": _normalized_string_list(
            raw_selector.get("currentness_status_not_contains", [])
        ),
        "docling_instructions_contains": _normalized_string_list(
            raw_selector.get("docling_instructions_contains", [])
        ),
        "docling_instructions_not_contains": _normalized_string_list(
            raw_selector.get("docling_instructions_not_contains", [])
        ),
        "artifact_is_proving_placeholder": raw_selector.get("artifact_is_proving_placeholder"),
    }


def _normalized_string_list(values: object) -> list[str]:
    return sorted({str(value).strip() for value in values or [] if str(value).strip()})


def _selector_source_record_ids(*, record_map: dict[str, dict], selector: dict[str, object]) -> set[str]:
    return {
        source_record_id
        for source_record_id, record in record_map.items()
        if _record_matches_selector(source_record_id=source_record_id, record=record, selector=selector)
    }


def _record_matches_selector(*, source_record_id: str, record: dict, selector: dict[str, object]) -> bool:
    only_ids = set(selector.get("source_record_ids", []))
    if only_ids and source_record_id not in only_ids:
        return False
    if source_record_id in set(selector.get("exclude_source_record_ids", [])):
        return False

    if not _matches_allowed(
        str(record.get("loader_contract") or ""),
        selector.get("loader_contracts", []),
    ):
        return False
    if not _matches_allowed(
        str(record.get("source_partition") or ""),
        selector.get("source_partitions", []),
    ):
        return False
    if not _matches_allowed(
        str(record.get("parser_admission_class") or ""),
        selector.get("parser_admission_classes", []),
    ):
        return False
    if not _matches_allowed(
        str(record.get("expected_parser") or ""),
        selector.get("expected_parsers", []),
    ):
        return False
    if not _matches_allowed(
        str(record.get("source_status") or ""),
        selector.get("source_statuses", []),
    ):
        return False
    if not _matches_allowed(
        str(record.get("document_type") or ""),
        selector.get("document_types", []),
    ):
        return False
    if not _matches_allowed(
        str(record.get("url_class") or ""),
        selector.get("url_classes", []),
    ):
        return False
    artifact_is_proving_placeholder = selector.get("artifact_is_proving_placeholder")
    if artifact_is_proving_placeholder is not None and bool(
        record.get("artifact_is_proving_placeholder")
    ) is not bool(artifact_is_proving_placeholder):
        return False

    currentness_status = str(record.get("currentness_status") or "")
    docling_instructions = str(record.get("docling_instructions") or "")
    if selector.get("currentness_status_contains") and not _matches_contains(
        currentness_status,
        selector.get("currentness_status_contains", []),
    ):
        return False
    if _matches_contains(
        currentness_status,
        selector.get("currentness_status_not_contains", []),
    ):
        return False
    if selector.get("docling_instructions_contains") and not _matches_contains(
        docling_instructions,
        selector.get("docling_instructions_contains", []),
    ):
        return False
    if _matches_contains(
        docling_instructions,
        selector.get("docling_instructions_not_contains", []),
    ):
        return False
    return True


def _matches_allowed(value: str, allowed_values: object) -> bool:
    allowed = [str(item).strip() for item in (allowed_values or []) if str(item).strip()]
    return not allowed or value in allowed


def _matches_contains(value: str, expected_substrings: object) -> bool:
    substrings = [str(item).strip().lower() for item in (expected_substrings or []) if str(item).strip()]
    if not substrings:
        return False
    lowered = value.lower()
    return any(substring in lowered for substring in substrings)
