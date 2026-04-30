from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


DEFAULT_CONFIG_PATH = Path("config/downloader.toml")


@dataclass(frozen=True)
class WorkbookConfig:
    canonical_sheets: tuple[str, ...]
    exclusion_sheet: str
    header_row: int
    overrides_path: Path | None


@dataclass(frozen=True)
class OutputConfig:
    root: Path
    raw_artifact_dir: Path
    manifest_dir: Path
    run_dir: Path


@dataclass(frozen=True)
class HostConfig:
    delay_seconds: float
    concurrency: int
    browser_compatible_user_agent: bool = False


@dataclass(frozen=True)
class NetworkConfig:
    user_agent: str
    connect_timeout_seconds: float
    read_timeout_seconds: float
    max_attempts: int
    global_concurrency: int
    default_host_concurrency: int
    default_host_delay_seconds: float
    hosts: dict[str, HostConfig]


@dataclass(frozen=True)
class ValidationConfig:
    minimum_body_bytes: int
    allowed_content_types: tuple[str, ...]
    challenge_url_patterns: tuple[str, ...]
    not_found_url_patterns: tuple[str, ...]


@dataclass(frozen=True)
class DownloaderConfig:
    workbook: WorkbookConfig
    outputs: OutputConfig
    network: NetworkConfig
    validation: ValidationConfig


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> DownloaderConfig:
    config_path = Path(path)
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    workbook = data["workbook"]
    outputs = data["outputs"]
    network = data["network"]
    validation = data["validation"]
    host_data = data.get("hosts", {})

    return DownloaderConfig(
        workbook=WorkbookConfig(
            canonical_sheets=tuple(workbook["canonical_sheets"]),
            exclusion_sheet=workbook["exclusion_sheet"],
            header_row=int(workbook["header_row"]),
            overrides_path=Path(workbook["overrides_path"]) if workbook.get("overrides_path") else None,
        ),
        outputs=OutputConfig(
            root=Path(outputs["root"]),
            raw_artifact_dir=Path(outputs["raw_artifact_dir"]),
            manifest_dir=Path(outputs["manifest_dir"]),
            run_dir=Path(outputs["run_dir"]),
        ),
        network=NetworkConfig(
            user_agent=network["user_agent"],
            connect_timeout_seconds=float(network["connect_timeout_seconds"]),
            read_timeout_seconds=float(network["read_timeout_seconds"]),
            max_attempts=int(network["max_attempts"]),
            global_concurrency=int(network["global_concurrency"]),
            default_host_concurrency=int(network["default_host_concurrency"]),
            default_host_delay_seconds=float(network["default_host_delay_seconds"]),
            hosts={
                host: HostConfig(
                    delay_seconds=float(values["delay_seconds"]),
                    concurrency=int(values["concurrency"]),
                    browser_compatible_user_agent=bool(
                        values.get("browser_compatible_user_agent", False)
                    ),
                )
                for host, values in host_data.items()
            },
        ),
        validation=ValidationConfig(
            minimum_body_bytes=int(validation["minimum_body_bytes"]),
            allowed_content_types=tuple(validation["allowed_content_types"]),
            challenge_url_patterns=tuple(validation["challenge_url_patterns"]),
            not_found_url_patterns=tuple(validation["not_found_url_patterns"]),
        ),
    )
