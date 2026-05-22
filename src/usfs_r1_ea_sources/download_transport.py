from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
import socket
import ssl

from .adapters import adapt_download_url
from .config import NetworkConfig, ValidationConfig
from .preflight_transport import (
    _base_content_type,
    _body_looks_blocked,
    _body_looks_not_found,
    _int_or_none,
    _request_headers,
    _run_curl_request,
    _uses_browser_compatible_user_agent,
    _uses_verified_curl_transport,
)


@dataclass(frozen=True)
class DownloadFetchResult:
    status: str
    http_status: int | None
    final_url: str | None
    redirect_chain: list[str]
    content_type: str | None
    content_length: int | None
    body: bytes
    attempt_count: int
    failure: dict | None
    validation: dict


class RecordingRedirectHandler(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redirect_chain: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        self.redirect_chain.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_url(
    url: str,
    network: NetworkConfig,
    validation: ValidationConfig,
) -> DownloadFetchResult:
    adapted = adapt_download_url(url, network)
    fetch_url = adapted.url if adapted else url
    last_result: DownloadFetchResult | None = None
    max_attempts = max(1, network.max_attempts)
    for attempt in range(1, max_attempts + 1):
        result = _download_once(fetch_url, network, validation, attempt, original_url=url)
        if adapted and result.status == "downloaded":
            result = _with_adapter_metadata(result, adapted.adapter, adapted.expected_content_type)
        last_result = result
        if result.status not in {"failed", "rate_limited", "timeout"}:
            return result
    if last_result is None:
        return _error_result("failed", None, [], None, "NoAttempt", "No download attempt completed", 0)
    return last_result


def _download_once(
    url: str,
    network: NetworkConfig,
    validation: ValidationConfig,
    attempt_count: int,
    *,
    original_url: str | None = None,
) -> DownloadFetchResult:
    if _uses_verified_curl_transport(url, network):
        return _download_once_with_curl(url, network, validation, attempt_count, original_url=original_url)
    redirect_handler = RecordingRedirectHandler()
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), redirect_handler)
    request = Request(
        url,
        headers=_request_headers(url, network),
        method="GET",
    )
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read()
            result = _classify_download_response(
                http_status=response.status,
                final_url=response.geturl(),
                redirect_chain=redirect_handler.redirect_chain,
                content_type=_base_content_type(response.headers.get("content-type")),
                content_length=_int_or_none(response.headers.get("content-length")),
                body=body,
                validation=validation,
                attempt_count=attempt_count,
                original_url=original_url,
            )
            if _uses_browser_compatible_user_agent(url, network):
                return _with_browser_compatible_metadata(result)
            return result
    except HTTPError as error:
        status = "failed"
        if error.code == 404:
            status = "not_found"
        elif error.code == 429:
            status = "rate_limited"
        elif error.code in {401, 403}:
            status = "blocked"
        return _error_result(
            status,
            error.code,
            redirect_handler.redirect_chain,
            error.url,
            status,
            str(error),
            attempt_count,
            content_type=_base_content_type(error.headers.get("content-type")) if error.headers else None,
            content_length=_int_or_none(error.headers.get("content-length")) if error.headers else None,
        )
    except TimeoutError as error:
        return _error_result("timeout", None, [], None, "TimeoutError", str(error), attempt_count)
    except socket.timeout as error:
        return _error_result("timeout", None, [], None, "TimeoutError", str(error), attempt_count)
    except ssl.SSLError as error:
        return _error_result("ssl_error", None, [], None, "SSLError", str(error), attempt_count)
    except URLError as error:
        reason = getattr(error, "reason", None)
        if isinstance(reason, ssl.SSLError):
            return _error_result("ssl_error", None, [], None, "SSLError", str(reason), attempt_count)
        if isinstance(reason, TimeoutError):
            return _error_result("timeout", None, [], None, "TimeoutError", str(reason), attempt_count)
        return _error_result("failed", None, [], None, "URLError", str(error), attempt_count)
    except Exception as error:
        return _error_result("failed", None, [], None, type(error).__name__, str(error), attempt_count)


def _download_once_with_curl(
    url: str,
    network: NetworkConfig,
    validation: ValidationConfig,
    attempt_count: int,
    *,
    original_url: str | None = None,
) -> DownloadFetchResult:
    curl_result, error = _run_curl_request(
        url=url,
        method="GET",
        headers=_request_headers(url, network),
        network=network,
    )
    if error is not None:
        return _error_result(error["status"], None, [], None, error["error_class"], error["message"], attempt_count)

    result = _classify_download_response(
        http_status=curl_result.http_status or 0,
        final_url=curl_result.final_url or url,
        redirect_chain=curl_result.redirect_chain,
        content_type=curl_result.content_type,
        content_length=curl_result.content_length,
        body=curl_result.body,
        validation=validation,
        attempt_count=attempt_count,
        original_url=original_url,
    )
    result = _with_verified_transport_metadata(result, "curl")
    if _uses_browser_compatible_user_agent(url, network):
        return _with_browser_compatible_metadata(result)
    return result


def _classify_download_response(
    *,
    http_status: int,
    final_url: str,
    redirect_chain: list[str],
    content_type: str | None,
    content_length: int | None,
    body: bytes,
    validation: ValidationConfig,
    attempt_count: int,
    original_url: str | None = None,
) -> DownloadFetchResult:
    final_url_lower = final_url.lower()
    chain_lower = " ".join([final_url_lower, *(url.lower() for url in redirect_chain)])
    body_text = body[:8192].decode("utf-8", errors="ignore").lower()
    status = "downloaded"
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
    elif len(body) < validation.minimum_body_bytes:
        status = "invalid_content"
        reason = f"Body smaller than minimum: {len(body)} bytes"
    elif _is_xml_body(body):
        content_type = content_type if content_type in {"application/xml", "text/xml"} else "application/xml"
    elif content_type and content_type not in validation.allowed_content_types:
        status = "unsupported_content_type"
        reason = f"Unsupported content type: {content_type}"
    elif content_type == "application/pdf" and not _looks_like_pdf(body):
        status = "invalid_content"
        reason = "PDF content type did not contain a PDF header"

    return DownloadFetchResult(
        status=status,
        http_status=http_status,
        final_url=original_url or final_url,
        redirect_chain=redirect_chain + ([final_url] if original_url and final_url != original_url else []),
        content_type=content_type,
        content_length=content_length,
        body=body if status == "downloaded" else b"",
        attempt_count=attempt_count,
        failure=None if status == "downloaded" else _failure(status, reason or status, attempt_count),
        validation={"mode": "download", "passed": status == "downloaded", "reason": reason},
    )


def _error_result(
    status: str,
    http_status: int | None,
    redirect_chain: list[str],
    final_url: str | None,
    error_class: str,
    message: str,
    attempt_count: int,
    *,
    content_type: str | None = None,
    content_length: int | None = None,
) -> DownloadFetchResult:
    return DownloadFetchResult(
        status=status,
        http_status=http_status,
        final_url=final_url,
        redirect_chain=redirect_chain,
        content_type=content_type,
        content_length=content_length,
        body=b"",
        attempt_count=attempt_count,
        failure=_failure(error_class, message, attempt_count),
        validation={"mode": "download", "passed": False, "reason": message},
    )


def _failure(error_class: str, message: str, attempt_count: int) -> dict:
    return {"error_class": error_class, "error_message": message, "attempt_count": attempt_count}


def _looks_like_pdf(body: bytes) -> bool:
    return body[:1024].lstrip().startswith(b"%PDF")


def _is_xml_body(body: bytes) -> bool:
    sample = body[:1024].lstrip()
    return sample.startswith(b"<?xml") or sample.startswith(b"<RULE") or sample.startswith(b"<ECFR")


def _with_adapter_metadata(
    result: DownloadFetchResult,
    adapter: str,
    expected_content_type: str | None,
) -> DownloadFetchResult:
    validation = dict(result.validation)
    validation["adapter"] = adapter
    return DownloadFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=expected_content_type or result.content_type,
        content_length=result.content_length,
        body=result.body,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _with_browser_compatible_metadata(result: DownloadFetchResult) -> DownloadFetchResult:
    validation = dict(result.validation)
    validation["browser_compatible_user_agent"] = True
    return DownloadFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=result.content_type,
        content_length=result.content_length,
        body=result.body,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _with_verified_transport_metadata(result: DownloadFetchResult, transport: str) -> DownloadFetchResult:
    validation = dict(result.validation)
    validation["verified_transport"] = transport
    return DownloadFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=result.content_type,
        content_length=result.content_length,
        body=result.body,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )
