from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import hashlib
import json
import re

from .artifact_utils import _utc_now as utc_now
from .artifact_utils import _write_json as write_json
from .config import DEFAULT_CONFIG_PATH
from .config import NetworkConfig
from .config import load_config
from .records import sha256_file


BOX_FOLDER_INVENTORY_SCHEMA_VERSION = "box-folder-inventory-v1"
BOX_IMPORT_MANIFEST_SCHEMA_VERSION = "box-import-manifest-v1"
BOX_DOWNLOAD_URL_TEMPLATE = (
    "https://usfs-public.app.box.com/index.php?rm=box_download_shared_file"
    "&shared_name=<shared_name>&file_id=f_<box_file_id>"
)
BOX_FOLDER_URL_RE = re.compile(r"/folder/(?P<folder_id>\d+)(?:/|$)")
UNSAFE_PATH_CHARS_RE = re.compile(r"[/:\\\x00]")


@dataclass(frozen=True)
class BoxFolderIntakeResult:
    summary: dict
    inventory_path: Path
    import_manifest_path: Path | None


@dataclass(frozen=True)
class _BoxFolderTarget:
    folder_id: int
    folder_name: str
    parent_folder_id: int | None
    relative_path: str


@dataclass(frozen=True)
class _FetchedBoxFolderPage:
    shared_name: str
    folder_id: int
    folder_name: str
    folder_url: str
    page_count: int
    page_number: int
    items: list[dict]


def run_box_folder_intake(
    *,
    review_id: str,
    root_folder_url: str,
    output_dir: Path = Path("source_library"),
    intake_dir: Path | None = None,
    download: bool = False,
    include_relative_path_prefixes: list[str] | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> BoxFolderIntakeResult:
    network = load_config(config_path).network
    intake_dir = intake_dir or output_dir / "reviews" / "_intake" / review_id
    intake_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_box_folder_inventory(
        review_id=review_id,
        root_folder_url=root_folder_url,
        network=network,
    )
    inventory_path = intake_dir / "box_inventory.json"
    write_json(inventory_path, inventory)

    import_manifest_path: Path | None = None
    summary = {
        "review_id": review_id,
        "root_folder_url": inventory["root_folder_url"],
        "root_box_folder_id": inventory["root_box_folder_id"],
        "shared_name": inventory["shared_name"],
        "inventory_path": str(inventory_path),
        "folder_count": inventory["folder_count"],
        "file_count": inventory["file_count"],
        "expected_total_byte_size": inventory["expected_total_byte_size"],
        "download_requested": download,
        "include_relative_path_prefixes": _normalized_prefixes(include_relative_path_prefixes),
    }

    if download:
        manifest = download_box_folder_inventory(
            inventory=inventory,
            destination_dir=intake_dir,
            network=network,
            include_relative_path_prefixes=include_relative_path_prefixes,
        )
        import_manifest_path = intake_dir / "box_import_manifest.json"
        write_json(import_manifest_path, manifest)
        summary.update(
            {
                "import_manifest_path": str(import_manifest_path),
                "selected_document_count": manifest["document_count"],
                "downloaded_count": manifest["downloaded_count"],
                "existing_count": manifest["existing_count"],
                "failure_count": manifest["failure_count"],
                "actual_total_byte_size": manifest["actual_total_byte_size"],
            }
        )

    return BoxFolderIntakeResult(
        summary=summary,
        inventory_path=inventory_path,
        import_manifest_path=import_manifest_path,
    )


def build_box_folder_inventory(
    *,
    review_id: str,
    root_folder_url: str,
    network: NetworkConfig,
    fetch_folder_page: Callable[[int, int, NetworkConfig], _FetchedBoxFolderPage] | None = None,
) -> dict:
    folder_id = _folder_id_from_url(root_folder_url)
    fetch_folder_page = fetch_folder_page or _fetch_box_folder_page
    folder_targets = deque(
        [_BoxFolderTarget(folder_id=folder_id, folder_name="", parent_folder_id=None, relative_path="")]
    )
    folder_records: list[dict] = []
    file_records: list[dict] = []
    seen_folder_ids: set[int] = {folder_id}
    seen_file_ids: set[int] = set()
    shared_name: str | None = None

    while folder_targets:
        target = folder_targets.popleft()
        first_page = fetch_folder_page(target.folder_id, 1, network)
        shared_name = _shared_name_or_fail(shared_name, first_page.shared_name)
        page_count = max(1, first_page.page_count)
        root_name = target.folder_name or first_page.folder_name
        pages = [first_page]
        for page_number in range(2, page_count + 1):
            next_page = fetch_folder_page(target.folder_id, page_number, network)
            shared_name = _shared_name_or_fail(shared_name, next_page.shared_name)
            pages.append(next_page)

        for page in pages:
            folder_records.append(
                {
                    "box_folder_id": target.folder_id,
                    "box_folder_name": root_name,
                    "page_count": page_count,
                    "page_number": page.page_number,
                    "page_size_observed": len(page.items),
                    "parent_folder_id": target.parent_folder_id,
                    "relative_path": target.relative_path,
                    "source_folder_url": page.folder_url,
                }
            )
            for item in page.items:
                item_type = str(item.get("type") or "").lower()
                if item_type == "folder":
                    child_folder_id = _int_value(item.get("id"))
                    if child_folder_id is None or child_folder_id in seen_folder_ids:
                        continue
                    child_name = str(item.get("name") or f"folder-{child_folder_id}")
                    seen_folder_ids.add(child_folder_id)
                    folder_targets.append(
                        _BoxFolderTarget(
                            folder_id=child_folder_id,
                            folder_name=child_name,
                            parent_folder_id=target.folder_id,
                            relative_path=_join_relative_path(target.relative_path, child_name),
                        )
                    )
                    continue
                if item_type != "file":
                    continue
                box_file_id = _int_value(item.get("id"))
                if box_file_id is None or box_file_id in seen_file_ids:
                    continue
                seen_file_ids.add(box_file_id)
                name = str(item.get("name") or f"file-{box_file_id}")
                file_records.append(
                    {
                        "box_file_id": box_file_id,
                        "box_folder_id": target.folder_id,
                        "box_folder_name": root_name,
                        "box_typed_id": str(item.get("typedID") or f"f_{box_file_id}"),
                        "content_updated": _int_value(item.get("contentUpdated")),
                        "created": _int_value(item.get("created")),
                        "download_url_template": BOX_DOWNLOAD_URL_TEMPLATE,
                        "expected_byte_size": _int_value(item.get("itemSize")) or 0,
                        "extension": _file_extension(item, name),
                        "folder_page": page.page_number,
                        "folder_relative_path": target.relative_path,
                        "name": name,
                        "relative_path": _join_relative_path(target.relative_path, name),
                        "source_folder_url": page.folder_url,
                    }
                )

    return {
        "schema_version": BOX_FOLDER_INVENTORY_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "review_id": review_id,
        "root_folder_url": _normalized_box_folder_url(folder_id),
        "root_box_folder_id": folder_id,
        "shared_name": shared_name,
        "folder_count": len(folder_records),
        "file_count": len(file_records),
        "expected_total_byte_size": sum(
            int(record.get("expected_byte_size") or 0) for record in file_records
        ),
        "folders": folder_records,
        "files": sorted(file_records, key=lambda record: record["relative_path"].lower()),
    }


def download_box_folder_inventory(
    *,
    inventory: dict,
    destination_dir: Path,
    network: NetworkConfig,
    include_relative_path_prefixes: list[str] | None = None,
    download_bytes: Callable[[str, NetworkConfig], bytes] | None = None,
) -> dict:
    destination_dir.mkdir(parents=True, exist_ok=True)
    download_bytes = download_bytes or _download_bytes
    prefixes = _normalized_prefixes(include_relative_path_prefixes)
    documents = _selected_documents(inventory["files"], prefixes)
    failures: list[dict] = []
    document_records: list[dict] = []
    downloaded_count = 0
    existing_count = 0
    actual_total_byte_size = 0
    started_at = utc_now()

    for document in documents:
        relative_path = document["relative_path"]
        path = destination_dir / _local_relative_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        status = "downloaded"
        actual_byte_size = None
        sha256 = None

        if path.exists() and path.stat().st_size == int(document.get("expected_byte_size") or 0):
            status = "existing"
            actual_byte_size = path.stat().st_size
            sha256 = sha256_file(path)
            existing_count += 1
        else:
            try:
                content = download_bytes(
                    _download_url(document["download_url_template"], inventory["shared_name"], document["box_file_id"]),
                    network,
                )
            except Exception as error:  # pragma: no cover - exercised via tests with injected fetcher
                failures.append(
                    {
                        "box_file_id": document["box_file_id"],
                        "relative_path": relative_path,
                        "error_class": error.__class__.__name__,
                        "error_message": str(error),
                    }
                )
                document_records.append(
                    {
                        **document,
                        "path": str(path),
                        "actual_byte_size": None,
                        "sha256": None,
                        "status": "failed",
                    }
                )
                continue
            actual_byte_size, sha256 = _write_download(path, content)
            downloaded_count += 1

        actual_total_byte_size += actual_byte_size or 0
        document_records.append(
            {
                **document,
                "path": str(path),
                "actual_byte_size": actual_byte_size,
                "sha256": sha256,
                "status": status,
            }
        )

    return {
        "schema_version": BOX_IMPORT_MANIFEST_SCHEMA_VERSION,
        "started_at": started_at,
        "completed_at": utc_now(),
        "review_id": inventory["review_id"],
        "root_folder_url": inventory["root_folder_url"],
        "root_box_folder_id": inventory["root_box_folder_id"],
        "shared_name": inventory["shared_name"],
        "inventory_path": str(destination_dir / "box_inventory.json"),
        "selection_relative_path_prefixes": prefixes,
        "folder_count": inventory["folder_count"],
        "document_count": len(documents),
        "downloaded_count": downloaded_count,
        "existing_count": existing_count,
        "failure_count": len(failures),
        "expected_total_byte_size": sum(
            int(document.get("expected_byte_size") or 0) for document in documents
        ),
        "actual_total_byte_size": actual_total_byte_size,
        "failures": failures,
        "documents": document_records,
    }


def _fetch_box_folder_page(
    folder_id: int,
    page_number: int,
    network: NetworkConfig,
) -> _FetchedBoxFolderPage:
    folder_url = _normalized_box_folder_url(folder_id)
    page_url = folder_url if page_number == 1 else f"{folder_url}?page={page_number}"
    page_text = _read_text(page_url, network)
    stream_data = _extract_box_shared_folder_stream_data(page_text)
    if not isinstance(stream_data, dict):
        raise ValueError(f"Could not parse Box stream data from {page_url}")
    shared_item = stream_data.get("/app-api/enduserapp/shared-item")
    shared_folder = stream_data.get("/app-api/enduserapp/shared-folder")
    if not isinstance(shared_item, dict) or not isinstance(shared_folder, dict):
        raise ValueError(f"Missing shared Box folder payload in {page_url}")
    shared_name = shared_item.get("sharedName")
    if not isinstance(shared_name, str) or not shared_name:
        raise ValueError(f"Missing shared Box name in {page_url}")
    items = shared_folder.get("items")
    if not isinstance(items, list):
        raise ValueError(f"Missing Box folder items in {page_url}")
    current_folder_id = _int_value(shared_folder.get("currentFolderID"))
    if current_folder_id is None:
        raise ValueError(f"Missing Box currentFolderID in {page_url}")
    folder_name = str(
        shared_folder.get("currentFolderName")
        or (shared_folder.get("folder") or {}).get("name")
        or current_folder_id
    )
    page_count = _int_value(shared_folder.get("pageCount")) or 1
    observed_page_number = _int_value(shared_folder.get("pageNumber")) or page_number
    return _FetchedBoxFolderPage(
        shared_name=shared_name,
        folder_id=current_folder_id,
        folder_name=folder_name,
        folder_url=folder_url,
        page_count=page_count,
        page_number=observed_page_number,
        items=items,
    )


def _extract_box_shared_folder_stream_data(page_text: str) -> dict | None:
    for marker in ("Box.postStreamData", "Box.prefetchedData"):
        object_text = _extract_json_object_after(page_text, marker)
        if not object_text:
            continue
        try:
            data = json.loads(object_text)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if "/app-api/enduserapp/shared-folder" in data:
            return data
    return None


def _extract_json_object_after(text: str, marker: str) -> str | None:
    marker_index = text.find(marker)
    if marker_index < 0:
        return None
    start = text.find("{", marker_index)
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _read_text(url: str, network: NetworkConfig) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": network.user_agent,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _download_bytes(url: str, network: NetworkConfig) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": network.user_agent, "Accept": "*/*"},
    )
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _download_url(template: str, shared_name: str, box_file_id: int) -> str:
    return template.replace("<shared_name>", shared_name).replace(
        "<box_file_id>", str(box_file_id)
    )


def _write_download(path: Path, content: bytes) -> tuple[int, str]:
    path.write_bytes(content)
    return len(content), hashlib.sha256(content).hexdigest()


def _selected_documents(files: list[dict], prefixes: list[str]) -> list[dict]:
    if not prefixes:
        return list(files)
    selected = []
    for document in files:
        relative_path = str(document.get("relative_path") or "")
        if any(
            relative_path == prefix or relative_path.startswith(f"{prefix}/") for prefix in prefixes
        ):
            selected.append(document)
    return selected


def _normalized_prefixes(prefixes: list[str] | None) -> list[str]:
    normalized = []
    for prefix in prefixes or []:
        cleaned = prefix.strip().strip("/")
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def _join_relative_path(parent_relative_path: str, name: str) -> str:
    segment = _safe_path_segment(name)
    if not parent_relative_path:
        return segment
    return f"{parent_relative_path}/{segment}"


def _safe_path_segment(value: str) -> str:
    cleaned = UNSAFE_PATH_CHARS_RE.sub("_", value).strip()
    return cleaned or "unnamed"


def _local_relative_path(relative_path: str) -> Path:
    return Path(*(segment for segment in relative_path.split("/") if segment))


def _normalized_box_folder_url(folder_id: int) -> str:
    return f"https://usfs-public.app.box.com/v/PinyonPublic/folder/{folder_id}"


def _folder_id_from_url(url: str) -> int:
    match = BOX_FOLDER_URL_RE.search(urlsplit(url).path)
    if not match:
        raise ValueError(f"Could not parse Box folder id from {url}")
    return int(match.group("folder_id"))


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _file_extension(item: dict, name: str) -> str | None:
    extension = item.get("extension")
    if isinstance(extension, str) and extension:
        return extension.lower()
    suffix = Path(name).suffix.lower().lstrip(".")
    return suffix or None


def _shared_name_or_fail(existing: str | None, observed: str) -> str:
    if existing is None:
        return observed
    if existing != observed:
        raise ValueError(
            f"Observed inconsistent Box shared names while inventorying public folder: {existing} vs {observed}"
        )
    return existing
