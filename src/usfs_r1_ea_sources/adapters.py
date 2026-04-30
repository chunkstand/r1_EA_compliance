from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
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


def adapt_download_url(url: str, network: NetworkConfig) -> AdaptedURL | None:
    parsed = urlsplit(url)
    host = parsed.netloc.lower()
    if host == "www.ecfr.gov":
        return _adapt_ecfr_url(url, network)
    if host == "www.federalregister.gov":
        return _adapt_federal_register_url(url)
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
