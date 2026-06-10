"""Proxy rotation for geo-unblocking and rate-limit mitigation."""

from __future__ import annotations

import itertools
import logging
import random
from typing import Any

logger = logging.getLogger("arb_scanner.proxy")


class ProxyRotator:
    def __init__(self, proxies: list[str]) -> None:
        self._proxies = proxies
        self._cycle = itertools.cycle(proxies) if proxies else None

    @property
    def enabled(self) -> bool:
        return bool(self._proxies)

    def next(self) -> str | None:
        if not self._cycle:
            return None
        proxy = next(self._cycle)
        logger.debug("Using proxy: %s", proxy[:20] + "...")
        return proxy

    def random(self) -> str | None:
        if not self._proxies:
            return None
        return random.choice(self._proxies)

    def playwright_proxy(self) -> dict[str, str] | None:
        proxy_url = self.next()
        if not proxy_url:
            return None
        return {"server": proxy_url}

    def httpx_proxy(self) -> dict[str, str] | None:
        proxy_url = self.next()
        if not proxy_url:
            return None
        return {"http://": proxy_url, "https://": proxy_url}

    def selenium_capabilities(self) -> dict[str, Any]:
        proxy_url = self.next()
        if not proxy_url:
            return {}
        return {"proxy": {"proxyType": "MANUAL", "httpProxy": proxy_url, "sslProxy": proxy_url}}