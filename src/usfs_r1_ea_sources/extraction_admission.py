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
        if not required_source_record_ids:
            raise ValueError(
                "Verified extraction admission contract entries must define at least one "
                "required_source_record_id."
            )
        normalized_contracts.append(
            {
                "contract_id": contract_id,
                "description": str(raw_contract.get("description") or "").strip() or None,
                "required_source_record_ids": required_source_record_ids,
                "require_direct_extraction": bool(raw_contract.get("require_direct_extraction")),
            }
        )
    return {
        "schema_version": VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION,
        "contracts": normalized_contracts,
    }


def matched_verified_extraction_contracts(
    source_record_ids: list[str] | set[str] | tuple[str, ...],
    *,
    contract_path: Path | None = None,
) -> dict[str, object]:
    source_record_id_set = {str(value).strip() for value in source_record_ids if str(value).strip()}
    payload = load_verified_extraction_admission_contract(contract_path)
    matched_contracts = []
    required_source_record_ids: set[str] = set()
    require_direct_extraction = False
    for contract in payload.get("contracts", []):
        contract_required_ids = set(contract.get("required_source_record_ids", []))
        present_ids = sorted(source_record_id_set & contract_required_ids)
        if not present_ids:
            continue
        matched_contracts.append(
            {
                "contract_id": contract.get("contract_id"),
                "description": contract.get("description"),
                "required_source_record_ids": present_ids,
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
