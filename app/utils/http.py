import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import httpx

from config import settings


logger = logging.getLogger(__name__)


class AsyncHttpClient:
    def __init__(
        self,
        timeout: float | None = None,
        retry_attempts: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        self.timeout = timeout or settings.http_timeout
        self.retry_attempts = retry_attempts or settings.http_retry_attempts
        self.retry_delay = retry_delay or settings.http_retry_delay

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.retry_attempts + 1):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json,
                    )
                    response.raise_for_status()
                    return response
                except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
                    last_error = error
                    logger.warning(
                        "http_request_failed method=%s url=%s attempt=%s error=%s",
                        method,
                        url,
                        attempt,
                        error,
                    )
                    if attempt < self.retry_attempts:
                        await asyncio.sleep(self.retry_delay * attempt)

        if last_error is None:
            raise RuntimeError("HTTP request failed without captured exception")

        raise last_error

    async def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        return await self.request("GET", url, headers=headers, params=params)

    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        return await self.request("POST", url, headers=headers, json=json)
