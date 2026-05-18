from __future__ import annotations

import gzip
import json
import random
import time
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import (
    BaseHandler,
    HTTPCookieProcessor,
    HTTPDefaultErrorHandler,
    HTTPErrorProcessor,
    HTTPHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)

DEFAULT_USER_AGENT = "AetherScraper/0.1"
USER_AGENTS = [
    DEFAULT_USER_AGENT,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]


@dataclass(frozen=True)
class NetworkOptions:
    timeout: int = 10
    retries: int = 1
    backoff_factor: float = 1.0
    allow_redirects: bool = True
    proxy: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    user_agent: str = DEFAULT_USER_AGENT
    random_user_agent: bool = False
    referer: str | None = None
    xhr: bool = False
    accept_gzip: bool = True


@dataclass(frozen=True)
class HttpResponse:
    url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    reason: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def text(self) -> str:
        return self.body.decode(self.encoding or "utf-8", "replace")

    @property
    def encoding(self) -> str | None:
        content_type = self.headers.get("content-type", "")
        for part in content_type.split(";"):
            part = part.strip()
            if part.lower().startswith("charset="):
                return part.split("=", 1)[1].strip() or None
        return None

    def json(self):
        return json.loads(self.text)


class NoRedirectHandler(HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response


class RedirectBlocker(BaseHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        return fp

    http_error_302 = http_error_301
    http_error_303 = http_error_301
    http_error_307 = http_error_301
    http_error_308 = http_error_301


def build_url(base_url, params=None):
    if not params:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return base_url + separator + urlencode(params)


def browser_headers(
    *,
    user_agent: str | None = None,
    referer: str | None = None,
    xhr: bool = False,
    accept_gzip: bool = True,
):
    headers = {
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if accept_gzip:
        headers["Accept-Encoding"] = "gzip"
    if referer:
        headers["Referer"] = referer
    if xhr:
        headers.update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            }
        )
    return headers


def choose_user_agent(randomize: bool = False, user_agent: str | None = None) -> str:
    if user_agent:
        return user_agent
    if randomize:
        return random.choice(USER_AGENTS)  # noqa: S311 - cosmetic header rotation only
    return DEFAULT_USER_AGENT


class HttpClient:
    def __init__(self, options: NetworkOptions | None = None, cookie_jar=None) -> None:
        self.options = options or NetworkOptions()
        self.cookie_jar = cookie_jar or CookieJar()
        self._opener = self._build_opener()

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        params: dict[str, str] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        retries: int | None = None,
        allow_redirects: bool | None = None,
    ) -> HttpResponse:
        target = build_url(url, params)
        request_headers = self._headers(headers)
        request = Request(target, data=data, headers=request_headers, method=method)
        return self._with_retries(
            request,
            timeout=timeout if timeout is not None else self.options.timeout,
            retries=retries if retries is not None else self.options.retries,
            allow_redirects=allow_redirects,
        )

    def get_text(self, url: str, **kwargs) -> str:
        return self.request(url, **kwargs).text

    def get_json(self, url: str, **kwargs):
        return self.request(url, **kwargs).json()

    def partial_content(
        self,
        url: str,
        start: int = 0,
        end: int | None = None,
        **kwargs,
    ) -> HttpResponse:
        range_value = f"bytes={start}-{'' if end is None else end}"
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["Range"] = range_value
        return self.request(url, headers=headers, **kwargs)

    def file_size(self, url: str, **kwargs) -> int | None:
        try:
            response = self.request(url, method="HEAD", **kwargs)
            length = response.headers.get("content-length")
            if length and length.isdigit():
                return int(length)
        except (HTTPError, URLError, TimeoutError):
            pass
        response = self.partial_content(url, 0, 0, **kwargs)
        content_range = response.headers.get("content-range", "")
        if "/" in content_range:
            size = content_range.rsplit("/", 1)[1]
            if size.isdigit():
                return int(size)
        length = response.headers.get("content-length")
        return int(length) if length and length.isdigit() else None

    def _build_opener(self):
        handlers = [HTTPHandler(), HTTPSHandler(), HTTPCookieProcessor(self.cookie_jar)]
        if self.options.proxy:
            handlers.append(
                ProxyHandler({"http": self.options.proxy, "https": self.options.proxy})
            )
        if not self.options.allow_redirects:
            handlers.extend(
                [RedirectBlocker(), NoRedirectHandler(), HTTPDefaultErrorHandler()]
            )
        return build_opener(*handlers)

    def _headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        user_agent = choose_user_agent(
            self.options.random_user_agent,
            self.options.user_agent
            if self.options.user_agent != DEFAULT_USER_AGENT
            else None,
        )
        merged = browser_headers(
            user_agent=user_agent,
            referer=self.options.referer,
            xhr=self.options.xhr,
            accept_gzip=self.options.accept_gzip,
        )
        merged.update(self.options.headers)
        merged.update(headers or {})
        return merged

    def _with_retries(
        self,
        request: Request,
        *,
        timeout: int,
        retries: int,
        allow_redirects: bool | None,
    ) -> HttpResponse:
        last_error = None
        opener = self._opener
        if (
            allow_redirects is not None
            and allow_redirects != self.options.allow_redirects
        ):
            override = NetworkOptions(
                **{**self.options.__dict__, "allow_redirects": allow_redirects}
            )
            opener = HttpClient(override, self.cookie_jar)._opener
        for attempt in range(retries + 1):
            try:
                with opener.open(request, timeout=timeout) as response:  # noqa: S310 - provider URL is user-configured
                    body = response.read()
                    headers = {
                        key.lower(): value for key, value in response.headers.items()
                    }
                    if headers.get("content-encoding", "").lower() == "gzip":
                        body = gzip.decompress(body)
                    return HttpResponse(
                        url=response.geturl(),
                        status_code=getattr(response, "status", response.getcode()),
                        headers=headers,
                        body=body,
                        reason=getattr(response, "reason", ""),
                    )
            except (HTTPError, URLError, TimeoutError) as exc:
                last_error = exc
                if isinstance(exc, HTTPError):
                    exc.close()
                if attempt < retries:
                    time.sleep(min(self.options.backoff_factor * (2**attempt), 5))
        if last_error is not None:
            raise last_error
        raise RuntimeError("request failed without exception")


def options_from_provider(provider_config, search_options=None) -> NetworkOptions:
    extra = getattr(search_options, "extra", {}) or {}
    network_extra = extra.get("network", {}) or {}
    timeout = getattr(search_options, "timeout", None) or getattr(
        provider_config, "timeout", 10
    )
    return NetworkOptions(
        timeout=network_extra.get("timeout", timeout),
        retries=network_extra.get("retries", getattr(provider_config, "retries", 1)),
        backoff_factor=network_extra.get("backoff_factor", 1.0),
        allow_redirects=network_extra.get("allow_redirects", True),
        proxy=network_extra.get("proxy"),
        headers={
            **getattr(provider_config, "headers", {}),
            **network_extra.get("headers", {}),
        },
        user_agent=network_extra.get(
            "user_agent", getattr(provider_config, "user_agent", DEFAULT_USER_AGENT)
        ),
        random_user_agent=network_extra.get("random_user_agent", False),
        referer=network_extra.get("referer"),
        xhr=network_extra.get("xhr", False),
        accept_gzip=network_extra.get("accept_gzip", True),
    )


def get_text(url, headers=None, params=None, timeout=10, retries=1):
    client = HttpClient(
        NetworkOptions(timeout=timeout, retries=retries, headers=headers or {})
    )
    return client.get_text(url, params=params)


def get_json(url, headers=None, params=None, timeout=10, retries=1):
    client = HttpClient(
        NetworkOptions(timeout=timeout, retries=retries, headers=headers or {})
    )
    return client.get_json(url, params=params)
