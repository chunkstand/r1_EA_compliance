from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
import socket
import ssl
import subprocess
import tempfile

from .adapters import adapt_download_url
from .config import NetworkConfig, ValidationConfig


BROWSER_COMPATIBLE_USER_AGENT = "Mozilla/5.0"


@dataclass(frozen=True)
class PreflightFetchResult:
    status: str
    http_status: int | None
    final_url: str | None
    redirect_chain: list[str]
    content_type: str | None
    content_length: int | None
    method: str | None
    failure: dict | None
    validation: dict
    attempt_count: int = 1


@dataclass(frozen=True)
class CurlTransportResult:
    http_status: int | None
    final_url: str | None
    redirect_chain: list[str]
    content_type: str | None
    content_length: int | None
    body: bytes


class RecordingRedirectHandler(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redirect_chain: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        self.redirect_chain.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_metadata(
    url: str,
    network: NetworkConfig,
    validation: ValidationConfig,
) -> PreflightFetchResult:
    adapted = adapt_download_url(url, network)
    fetch_url = adapted.url if adapted else url
    last_result: PreflightFetchResult | None = None
    max_attempts = max(1, network.max_attempts)
    for attempt in range(1, max_attempts + 1):
        for method in ("HEAD", "GET"):
            result = _fetch_once(fetch_url, method, network, validation, attempt, original_url=url)
            if adapted and result.status == "preflight_ok":
                result = _with_adapter_metadata(result, adapted.adapter, adapted.expected_content_type)
            last_result = result
            if method == "HEAD" and result.status in {
                "blocked",
                "failed",
                "rate_limited",
                "unsupported_content_type",
            }:
                continue
            if method == "HEAD" and result.http_status in {403, 405, 406}:
                continue
            break
        if last_result and not _is_transient_status(last_result.status):
            return last_result
    if last_result is None:
        return _error_result("failed", "NoAttempt", "No preflight attempt completed", None, 0)
    return last_result


def _fetch_once(
    url: str,
    method: str,
    network: NetworkConfig,
    validation: ValidationConfig,
    attempt_count: int,
    *,
    original_url: str | None = None,
) -> PreflightFetchResult:
    if _uses_verified_curl_transport(url, network):
        return _fetch_once_with_curl(url, method, network, validation, attempt_count, original_url=original_url)
    redirect_handler = RecordingRedirectHandler()
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), redirect_handler)
    headers = _request_headers(url, network)
    if method == "GET":
        headers["Range"] = "bytes=0-0"

    request = Request(url, headers=headers, method=method)
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    try:
        with opener.open(request, timeout=timeout) as response:
            body_sample = response.read(4096) if method == "GET" else b""
            http_status = response.status
            final_url = response.geturl()
            content_type = _base_content_type(response.headers.get("content-type"))
            content_length = _int_or_none(response.headers.get("content-length"))
            result = _classify_response(
                http_status=http_status,
                final_url=final_url,
                redirect_chain=redirect_handler.redirect_chain,
                content_type=content_type,
                content_length=content_length,
                method=method,
                attempt_count=attempt_count,
                body_sample=body_sample,
                validation=validation,
                original_url=original_url,
            )
            if _uses_browser_compatible_user_agent(url, network):
                return _with_browser_compatible_metadata(result)
            return result
    except HTTPError as error:
        return _http_error_result(error, redirect_handler.redirect_chain, method, validation, attempt_count)
    except TimeoutError as error:
        return _error_result("timeout", "TimeoutError", str(error), method, attempt_count)
    except socket.timeout as error:
        return _error_result("timeout", "TimeoutError", str(error), method, attempt_count)
    except ssl.SSLError as error:
        return _error_result("ssl_error", "SSLError", str(error), method, attempt_count)
    except URLError as error:
        reason = getattr(error, "reason", None)
        if isinstance(reason, ssl.SSLError):
            return _error_result("ssl_error", "SSLError", str(reason), method, attempt_count)
        if isinstance(reason, TimeoutError):
            return _error_result("timeout", "TimeoutError", str(reason), method, attempt_count)
        return _error_result("failed", "URLError", str(error), method, attempt_count)
    except Exception as error:
        return _error_result("failed", type(error).__name__, str(error), method, attempt_count)


def _fetch_once_with_curl(
    url: str,
    method: str,
    network: NetworkConfig,
    validation: ValidationConfig,
    attempt_count: int,
    *,
    original_url: str | None = None,
) -> PreflightFetchResult:
    headers = _request_headers(url, network)
    range_bytes = "0-4095" if method == "GET" else None
    curl_result, error = _run_curl_request(
        url=url,
        method=method,
        headers=headers,
        network=network,
        range_bytes=range_bytes,
    )
    if error is not None:
        return _error_result(error["status"], error["error_class"], error["message"], method, attempt_count)

    result = _classify_response(
        http_status=curl_result.http_status or 0,
        final_url=curl_result.final_url or url,
        redirect_chain=curl_result.redirect_chain,
        content_type=curl_result.content_type,
        content_length=curl_result.content_length,
        method=method,
        attempt_count=attempt_count,
        body_sample=curl_result.body[:4096],
        validation=validation,
        original_url=original_url,
    )
    result = _with_verified_transport_metadata(result, "curl")
    if _uses_browser_compatible_user_agent(url, network):
        return _with_browser_compatible_metadata(result)
    return result


def _classify_response(
    *,
    http_status: int,
    final_url: str,
    redirect_chain: list[str],
    content_type: str | None,
    content_length: int | None,
    method: str,
    attempt_count: int,
    body_sample: bytes,
    validation: ValidationConfig,
    original_url: str | None = None,
) -> PreflightFetchResult:
    final_url_lower = final_url.lower()
    body_text = body_sample[:4096].decode("utf-8", errors="ignore").lower()
    chain_lower = " ".join([final_url_lower, *(url.lower() for url in redirect_chain)])

    status = "preflight_ok"
    reason = None
    if http_status == 429:
        status = "rate_limited"
        reason = "HTTP 429"
    elif http_status == 404:
        status = "not_found"
        reason = "HTTP 404"
    elif http_status >= 500:
        status = "failed"
        reason = f"HTTP {http_status}"
    elif any(pattern.lower() in chain_lower for pattern in validation.challenge_url_patterns):
        status = "challenge_page"
        reason = "Challenge URL pattern matched"
    elif any(pattern.lower() in final_url_lower for pattern in validation.not_found_url_patterns):
        status = "not_found"
        reason = "Not-found URL pattern matched"
    elif body_text and _body_looks_not_found(body_text):
        status = "not_found"
        reason = "Not-found body pattern matched"
    elif body_text and _body_looks_blocked(body_text):
        status = "challenge_page"
        reason = "Challenge body pattern matched"
    elif body_sample[:1024].lstrip().startswith((b"<?xml", b"<RULE", b"<ECFR")):
        content_type = content_type if content_type in {"application/xml", "text/xml"} else "application/xml"
    elif content_type and content_type not in validation.allowed_content_types:
        status = "unsupported_content_type"
        reason = f"Unsupported content type: {content_type}"

    validation_result = {
        "mode": "preflight",
        "passed": status == "preflight_ok",
        "reason": reason,
    }
    return PreflightFetchResult(
        status=status,
        http_status=http_status,
        final_url=original_url or final_url,
        redirect_chain=redirect_chain + ([final_url] if original_url and final_url != original_url else []),
        content_type=content_type,
        content_length=content_length,
        method=method,
        attempt_count=attempt_count,
        failure=None if status == "preflight_ok" else _failure(status, reason or status, attempt_count),
        validation=validation_result,
    )


def _http_error_result(
    error: HTTPError,
    redirect_chain: list[str],
    method: str,
    validation: ValidationConfig,
    attempt_count: int,
) -> PreflightFetchResult:
    content_type = _base_content_type(error.headers.get("content-type")) if error.headers else None
    content_length = _int_or_none(error.headers.get("content-length")) if error.headers else None
    status = "failed"
    if error.code == 404:
        status = "not_found"
    elif error.code == 429:
        status = "rate_limited"
    elif error.code in {401, 403}:
        status = "blocked"
    return PreflightFetchResult(
        status=status,
        http_status=error.code,
        final_url=error.url,
        redirect_chain=redirect_chain,
        content_type=content_type,
        content_length=content_length,
        method=method,
        attempt_count=attempt_count,
        failure=_failure(status, str(error), attempt_count),
        validation={"mode": "preflight", "passed": False, "reason": str(error)},
    )


def _error_result(
    status: str,
    error_class: str,
    message: str,
    method: str | None,
    attempt_count: int,
) -> PreflightFetchResult:
    return PreflightFetchResult(
        status=status,
        http_status=None,
        final_url=None,
        redirect_chain=[],
        content_type=None,
        content_length=None,
        method=method,
        attempt_count=attempt_count,
        failure={"error_class": error_class, "error_message": message, "attempt_count": attempt_count},
        validation={"mode": "preflight", "passed": False, "reason": message},
    )


def _failure(error_class: str, message: str, attempt_count: int) -> dict:
    return {"error_class": error_class, "error_message": message, "attempt_count": attempt_count}


def _base_content_type(value: str | None) -> str | None:
    if not value:
        return None
    return value.split(";", 1)[0].strip().lower()


def _int_or_none(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _body_looks_blocked(body_text: str) -> bool:
    patterns = [
        "unblock.federalregister.gov",
        "access denied",
        "enable javascript",
        "verify you are human",
    ]
    return any(pattern in body_text for pattern in patterns)


def _body_looks_not_found(body_text: str) -> bool:
    patterns = [
        "docnotfound",
        "document not found",
        "page not found",
        "404 not found",
    ]
    return any(pattern in body_text for pattern in patterns)


def _with_adapter_metadata(
    result: PreflightFetchResult,
    adapter: str,
    expected_content_type: str | None,
) -> PreflightFetchResult:
    validation = dict(result.validation)
    validation["adapter"] = adapter
    return PreflightFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=expected_content_type or result.content_type,
        content_length=result.content_length,
        method=result.method,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _with_browser_compatible_metadata(result: PreflightFetchResult) -> PreflightFetchResult:
    validation = dict(result.validation)
    validation["browser_compatible_user_agent"] = True
    return PreflightFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=result.content_type,
        content_length=result.content_length,
        method=result.method,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _with_verified_transport_metadata(result: PreflightFetchResult, transport: str) -> PreflightFetchResult:
    validation = dict(result.validation)
    validation["verified_transport"] = transport
    return PreflightFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=result.content_type,
        content_length=result.content_length,
        method=result.method,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _request_headers(url: str, network: NetworkConfig) -> dict[str, str]:
    if _uses_browser_compatible_user_agent(url, network):
        return {
            "User-Agent": BROWSER_COMPATIBLE_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    return {
        "User-Agent": network.user_agent,
        "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.8",
    }


def _uses_browser_compatible_user_agent(url: str, network: NetworkConfig) -> bool:
    host_config = network.hosts.get(urlsplit(url).netloc.lower())
    return bool(host_config and host_config.browser_compatible_user_agent)


def _uses_verified_curl_transport(url: str, network: NetworkConfig) -> bool:
    host_config = network.hosts.get(urlsplit(url).netloc.lower())
    return bool(host_config and host_config.verified_transport == "curl")


def _respect_host_delay(
    host: str,
    host_last_fetch: dict[str, float],
    network: NetworkConfig,
    sleep_fn,
) -> None:
    last_fetch = host_last_fetch.get(host)
    if last_fetch is None:
        return
    host_config = network.hosts.get(host)
    delay = host_config.delay_seconds if host_config else network.default_host_delay_seconds
    remaining = delay - (monotonic() - last_fetch)
    if remaining > 0:
        sleep_fn(remaining)


def _run_curl_request(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    network: NetworkConfig,
    range_bytes: str | None = None,
) -> tuple[CurlTransportResult | None, dict | None]:
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    with tempfile.TemporaryDirectory(prefix="usfs-r1-curl-") as tmpdir:
        header_path = Path(tmpdir) / "headers.txt"
        body_path = Path(tmpdir) / "body.bin"
        command = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--connect-timeout",
            str(network.connect_timeout_seconds),
            "--max-time",
            str(timeout),
            "--dump-header",
            str(header_path),
            "--output",
            str(body_path),
            "--write-out",
            "CURLMETA:%{http_code}\t%{content_type}\t%{url_effective}\t%{size_download}\n",
        ]
        if method == "HEAD":
            command.append("--head")
        if range_bytes:
            command.extend(["--range", range_bytes])
        for name, value in headers.items():
            command.extend(["--header", f"{name}: {value}"])
        command.append(url)
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as error:
            return None, {
                "status": "failed",
                "error_class": type(error).__name__,
                "message": str(error),
            }
        if completed.returncode != 0:
            return None, _classify_curl_error(completed.returncode, completed.stderr)

        meta = _parse_curl_meta(completed.stdout)
        header_text = header_path.read_text(encoding="utf-8", errors="replace")
        header_sections = _parse_curl_header_sections(header_text)
        final_headers = header_sections[-1] if header_sections else {}
        redirect_chain = [
            section["location"]
            for section in header_sections[:-1]
            if section.get("location")
        ]
        body = body_path.read_bytes() if body_path.exists() else b""
        return (
            CurlTransportResult(
                http_status=meta["http_status"],
                final_url=meta["final_url"],
                redirect_chain=redirect_chain,
                content_type=_base_content_type(final_headers.get("content-type") or meta["content_type"]),
                content_length=_int_or_none(final_headers.get("content-length")),
                body=body,
            ),
            None,
        )


def _parse_curl_meta(stdout: str) -> dict[str, int | str | None]:
    line = next((entry for entry in stdout.splitlines() if entry.startswith("CURLMETA:")), "")
    _, _, payload = line.partition(":")
    http_code, content_type, final_url, _size_download = (payload.split("\t") + ["", "", "", ""])[:4]
    try:
        http_status = int(http_code)
    except ValueError:
        http_status = None
    return {
        "http_status": http_status,
        "content_type": content_type or None,
        "final_url": final_url or None,
    }


def _parse_curl_header_sections(header_text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in header_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("HTTP/"):
            current = {}
            sections.append(current)
            continue
        if current is None or ":" not in line:
            continue
        name, value = line.split(":", 1)
        current[name.strip().lower()] = value.strip()
    return sections


def _classify_curl_error(returncode: int, stderr: str) -> dict[str, str]:
    message = stderr.strip() or f"curl exited with status {returncode}"
    lowered = message.lower()
    if returncode == 28 or "timed out" in lowered:
        return {"status": "timeout", "error_class": "TimeoutError", "message": message}
    if returncode in {35, 51, 58, 59, 60, 64, 66} or "ssl" in lowered or "certificate" in lowered:
        return {"status": "ssl_error", "error_class": "SSLError", "message": message}
    return {"status": "failed", "error_class": "CurlError", "message": message}


def _is_transient_status(status: str) -> bool:
    return status in {"failed", "rate_limited", "timeout"}
