from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
import json
import re

from .config import NetworkConfig


@dataclass(frozen=True)
class AdaptedURL:
    url: str
    adapter: str
    expected_content_type: str | None = None


_ECFR_DATE_CACHE: dict[int, str | None] = {}
_BOX_PUBLIC_HOSTS = {"usfs-public.app.box.com", "usfs-public.box.com"}
_BOX_PUBLIC_FILE_RE = re.compile(r"/(?:s|v)/[^/]+/file/(?P<file_id>\d+)(?:/|$)")


def adapt_download_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    parsed = urlsplit(url)
    host = parsed.netloc.lower()
    if host == "www.ecfr.gov":
        return _adapt_ecfr_url(url, network)
    if host == "www.federalregister.gov":
        return _adapt_federal_register_url(url)
    if host in _BOX_PUBLIC_HOSTS:
        return _adapt_box_public_file_url(url, network)
    return None


def _adapt_ecfr_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    parsed = urlsplit(url)
    match = re.search(r"/current/title-(?P<title>\d+)(?P<rest>/.*)?$", parsed.path)
    if not match:
        return None
    title = int(match.group("title"))
    rest = match.group("rest") or ""
    part = _extract_path_component(rest, "part")
    section = _extract_path_component(rest, "section")
    date = latest_ecfr_date(title, network)
    if not date:
        return None
    api_url = f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml"
    if part:
        api_url += f"?part={part}"
    elif section:
        # eCFR full endpoint filters by part. For section-only URLs, use the section prefix as a
        # best-effort part filter when possible, for example 219.15 -> part 219.
        api_url += f"?part={section.split('.', 1)[0]}"
    return AdaptedURL(url=api_url, adapter="ecfr_full_xml", expected_content_type="application/xml")


def _adapt_federal_register_url(url: str) -> AdaptedURL | None:
    parsed = urlsplit(url)
    match = re.search(
        r"/documents/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<docnum>[^/]+)",
        parsed.path,
    )
    if not match:
        return None
    api_url = (
        "https://www.federalregister.gov/documents/full_text/xml/"
        f"{match.group('year')}/{match.group('month')}/{match.group('day')}/"
        f"{match.group('docnum')}.xml"
    )
    return AdaptedURL(
        url=api_url,
        adapter="federal_register_full_text_xml",
        expected_content_type="text/xml",
    )


def _adapt_box_public_file_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    match = _BOX_PUBLIC_FILE_RE.search(urlsplit(url).path)
    if not match:
        return None
    file_id = match.group("file_id")
    page_text = _read_text_url(url, network)
    if not page_text:
        return None
    stream_data = _extract_box_stream_data(page_text)
    if not isinstance(stream_data, dict):
        return None
    download_url = _find_key_value(stream_data, "authenticated_download_url")
    token_map = _find_key_value(stream_data, "preview_prefetch_token_map")
    read_token = _box_read_token(token_map, file_id)
    if not isinstance(download_url, str) or not read_token:
        return None
    separator = "&" if "?" in download_url else "?"
    return AdaptedURL(
        url=f"{download_url}{separator}access_token={quote(read_token, safe='')}",
        adapter="box_public_file_download",
    )


def _read_text_url(url: str, network: NetworkConfig) -> str | None:
    request = Request(
        url,
        headers={
            "User-Agent": network.user_agent,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _extract_box_stream_data(page_text: str) -> dict | None:
    for marker in ("Box.prefetchedData", "Box.postStreamData"):
        object_text = _extract_json_object_after(page_text, marker)
        if not object_text:
            continue
        try:
            data = json.loads(object_text)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
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


def _find_key_value(data: object, key: str) -> object | None:
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = _find_key_value(value, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_key_value(item, key)
            if found is not None:
                return found
    return None


def _box_read_token(token_map: object, file_id: str) -> str | None:
    if not isinstance(token_map, dict):
        return None
    token_entry = token_map.get(file_id)
    if isinstance(token_entry, dict):
        token = token_entry.get("read")
        return token if isinstance(token, str) else None
    return token_entry if isinstance(token_entry, str) else None


def _extract_path_component(path: str, name: str) -> str | None:
    match = re.search(rf"/{re.escape(name)}-([^/]+)", path)
    return match.group(1) if match else None


def latest_ecfr_date(title: int, network: NetworkConfig) -> str | None:
    if title in _ECFR_DATE_CACHE:
        return _ECFR_DATE_CACHE[title]
    request = Request(
        "https://www.ecfr.gov/api/versioner/v1/titles.json",
        headers={"User-Agent": network.user_agent, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=max(network.connect_timeout_seconds, network.read_timeout_seconds)) as response:
            data = json.load(response)
    except Exception:
        _ECFR_DATE_CACHE[title] = None
        return None
    for item in data.get("titles", []):
        if item.get("number") == title:
            _ECFR_DATE_CACHE[title] = item.get("up_to_date_as_of") or item.get("latest_issue_date")
            return _ECFR_DATE_CACHE[title]
    _ECFR_DATE_CACHE[title] = None
    return None
