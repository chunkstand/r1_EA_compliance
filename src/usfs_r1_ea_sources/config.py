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


@dataclass(frozen=True)
class OutputConfig:
    root: Path
    raw_artifact_dir: Path
    manifest_dir: Path
    run_dir: Path


@dataclass(frozen=True)
class DownloaderConfig:
    workbook: WorkbookConfig
    outputs: OutputConfig


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> DownloaderConfig:
    config_path = Path(path)
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    workbook = data["workbook"]
    outputs = data["outputs"]

    return DownloaderConfig(
        workbook=WorkbookConfig(
            canonical_sheets=tuple(workbook["canonical_sheets"]),
            exclusion_sheet=workbook["exclusion_sheet"],
            header_row=int(workbook["header_row"]),
        ),
        outputs=OutputConfig(
            root=Path(outputs["root"]),
            raw_artifact_dir=Path(outputs["raw_artifact_dir"]),
            manifest_dir=Path(outputs["manifest_dir"]),
            run_dir=Path(outputs["run_dir"]),
        ),
    )
