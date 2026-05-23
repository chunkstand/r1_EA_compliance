from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
import json
import re
import subprocess

from .config import NetworkConfig


@dataclass(frozen=True)
class AdaptedURL:
    url: str
    adapter: str
    expected_content_type: str | None = None


_ECFR_DATE_CACHE: dict[int, str | None] = {}
_BOX_PUBLIC_HOSTS = {"usfs-public.app.box.com", "usfs-public.box.com"}
_BOX_PUBLIC_FILE_RE = re.compile(r"/(?:s|v)/[^/]+/file/(?P<file_id>\d+)(?:/|$)")
_USFS_LEGACY_DIRECTIVES_HOSTS = {"www.fs.usda.gov", "fs.usda.gov"}
_USFS_NATIONAL_DIRECTIVES_URL = "https://www.fs.usda.gov/about-agency/regulations-policies/national-directives"
_DIRECT_DOCUMENT_EXTENSIONS = ("pdf", "doc", "docx")


def adapt_download_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    parsed = urlsplit(url)
    host = parsed.netloc.lower()
    if host == "www.ecfr.gov":
        return _adapt_ecfr_url(url, network)
    if host in {"www.federalregister.gov", "federalregister.gov"}:
        return _adapt_federal_register_url(url, network)
    if host in _BOX_PUBLIC_HOSTS:
        return _adapt_box_public_file_url(url, network)
    if host in _USFS_LEGACY_DIRECTIVES_HOSTS:
        return _adapt_usfs_legacy_directive_url(url, network)
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


def _adapt_federal_register_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    parsed = urlsplit(url)
    match = re.search(
        r"/documents/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<docnum>[^/]+)",
        parsed.path,
    )
    if match:
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
    short_match = re.search(r"/d/(?P<docnum>\d{4}-\d+)", parsed.path)
    if not short_match:
        return None
    api_url = _federal_register_document_xml_url(short_match.group("docnum"), network)
    if not api_url:
        return None
    return AdaptedURL(
        url=api_url,
        adapter="federal_register_full_text_xml",
        expected_content_type="text/xml",
    )


def _federal_register_document_xml_url(docnum: str, network: NetworkConfig) -> str | None:
    request = Request(
        f"https://www.federalregister.gov/api/v1/documents/{docnum}",
        headers={"User-Agent": network.user_agent, "Accept": "application/json"},
    )
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except Exception:
        return None
    xml_url = data.get("full_text_xml_url")
    return xml_url if isinstance(xml_url, str) else None


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


def _adapt_usfs_legacy_directive_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    parsed = urlsplit(url)
    legacy_match = re.fullmatch(r"/cgi-bin/Directives/get_dirs/(?P<kind>fsh|fsm)", parsed.path)
    if not legacy_match:
        return None
    if legacy_match.group("kind") != "fsh":
        return None
    code = _legacy_directive_code(parsed.query)
    if not code:
        return None
    national_directives_page = _read_text_url_with_curl(_USFS_NATIONAL_DIRECTIVES_URL, network)
    if not national_directives_page:
        return None
    directive_page_url = _usfs_handbook_contents_page_url(code, national_directives_page)
    if not directive_page_url:
        return None
    directive_page = _read_text_url_with_curl(directive_page_url, network)
    if not directive_page:
        return None
    direct_document_url = _extract_direct_document_url(directive_page_url, directive_page)
    if not direct_document_url:
        return None
    return AdaptedURL(
        url=direct_document_url,
        adapter="usfs_national_directives_handbook_direct_document",
        expected_content_type=_direct_document_content_type(direct_document_url),
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


def _read_text_url_with_curl(url: str, network: NetworkConfig) -> str | None:
    max_time = max(1, int(network.connect_timeout_seconds + network.read_timeout_seconds))
    command = [
        "curl",
        "-L",
        "--silent",
        "--show-error",
        "--fail",
        "--connect-timeout",
        str(max(1, int(network.connect_timeout_seconds))),
        "--max-time",
        str(max_time),
        "-H",
        f"User-Agent: {network.user_agent}",
        "-H",
        "Accept: text/html,application/xhtml+xml",
        url,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return _read_text_url(url, network)
    if result.returncode == 0 and result.stdout:
        return result.stdout
    return _read_text_url(url, network)


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


def _legacy_directive_code(query: str) -> str | None:
    candidate = query.strip().rstrip("=").strip()
    if not candidate:
        return None
    return candidate if re.fullmatch(r"[0-9]+(?:\.[0-9A-Za-z]+)?", candidate) else None


def _usfs_handbook_contents_page_url(code: str, page_text: str) -> str | None:
    expected_label = f"{code} - Contents".lower()
    for href, text in _anchor_pairs(page_text):
        if text.lower() != expected_label:
            continue
        if "/about-agency/regulations-policies/handbook/" not in href:
            continue
        return urljoin(_USFS_NATIONAL_DIRECTIVES_URL, href)
    return None


def _anchor_pairs(page_text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for match in re.finditer(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page_text, re.IGNORECASE | re.DOTALL):
        href = unescape(match.group(1)).strip()
        inner_html = match.group(2)
        text = unescape(re.sub(r"<[^>]+>", " ", inner_html))
        normalized_text = " ".join(text.split())
        if href and normalized_text:
            pairs.append((href, normalized_text))
    return pairs


def _extract_direct_document_url(page_url: str, page_text: str) -> str | None:
    for pattern in (
        rf'data-src="([^"]+\.(?:{"|".join(_DIRECT_DOCUMENT_EXTENSIONS)})[^"]*)"',
        rf'href="([^"]+\.(?:{"|".join(_DIRECT_DOCUMENT_EXTENSIONS)})[^"]*)"',
    ):
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            return urljoin(page_url, unescape(match.group(1)))
    viewer_match = re.search(r'viewer\.html\?file=([^"&]+)', page_text, re.IGNORECASE)
    if not viewer_match:
        return None
    return urljoin(page_url, unquote(unescape(viewer_match.group(1))))


def _direct_document_content_type(url: str) -> str | None:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".doc":
        return "application/msword"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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
