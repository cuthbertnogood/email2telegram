"""Telegram Bot API relay: probe vps2/vps3 and failover on network errors."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from telegram.request import HTTPXRequest

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT = 4.0
_CACHE_TTL_SEC = 120.0

_cached_order: list[str] | None = None
_cache_ts: float = 0.0


def parse_relay_roots(raw: str) -> list[str]:
    roots: list[str] = []
    for part in raw.replace(";", ",").split(","):
        root = part.strip().rstrip("/")
        if root:
            roots.append(root)
    return roots


def bot_api_base(root: str) -> str:
    root = root.rstrip("/")
    return root if root.endswith("/bot") else f"{root}/bot"


def probe_relay_root(root: str, *, timeout: float = _PROBE_TIMEOUT) -> bool:
    root = root.rstrip("/")
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(f"{root}/")
            return resp.status_code < 500
    except Exception:
        return False


def order_relay_roots(roots: list[str], *, refresh: bool = False) -> list[str]:
    global _cached_order, _cache_ts

    if not roots:
        return []
    if len(roots) == 1:
        return roots

    now = time.monotonic()
    if not refresh and _cached_order and (now - _cache_ts) < _CACHE_TTL_SEC:
        return _cached_order

    working: list[str] = []
    dead: list[str] = []
    for root in roots:
        (working if probe_relay_root(root) else dead).append(root)

    if not working:
        logger.error("telegram relay: all probes failed, keeping %s", roots[0])
        ordered = list(roots)
    else:
        if working[0] != roots[0]:
            logger.warning("telegram relay failover: primary down, using %s", working[0])
        ordered = working + dead

    _cached_order = ordered
    _cache_ts = now
    return ordered


def invalidate_relay_cache() -> None:
    global _cache_ts
    _cache_ts = 0.0


def resolve_bot_api_base(raw: str, *, refresh: bool = False) -> str:
    roots = order_relay_roots(parse_relay_roots(raw), refresh=refresh)
    if not roots:
        return ""
    return bot_api_base(roots[0])


def _rewrite_relay_url(url: str, from_root: str, to_root: str) -> str:
    old = bot_api_base(from_root)
    new = bot_api_base(to_root)
    if old in url:
        return url.replace(old, new, 1)
    from_u = urlparse(from_root)
    to_u = urlparse(to_root)
    return url.replace(
        f"{from_u.scheme}://{from_u.netloc}",
        f"{to_u.scheme}://{to_u.netloc}",
        1,
    )


class RelayFailoverHTTPXRequest(HTTPXRequest):
    """Retry Telegram HTTP on the next relay host after connect/timeout errors."""

    def __init__(self, relay_raw: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._relay_raw = relay_raw

    def _ordered_roots(self) -> list[str]:
        return order_relay_roots(parse_relay_roots(self._relay_raw))

    async def do_request(
        self,
        url: str,
        method: str,
        request_data: Any = None,
        **kwargs: Any,
    ) -> tuple[int, bytes]:
        roots = self._ordered_roots()
        if len(roots) <= 1:
            return await super().do_request(url, method, request_data, **kwargs)

        last_exc: Exception | None = None
        for i, root in enumerate(roots):
            try_url = _rewrite_relay_url(url, roots[0], root) if i else url
            try:
                return await super().do_request(try_url, method, request_data, **kwargs)
            except Exception as exc:
                last_exc = exc
                if i < len(roots) - 1:
                    logger.warning(
                        "telegram relay %s failed (%s), trying %s",
                        roots[0],
                        exc,
                        roots[i + 1],
                    )
                    invalidate_relay_cache()
                continue
        assert last_exc is not None
        raise last_exc
