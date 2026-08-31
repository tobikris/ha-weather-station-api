"""Minimal HTTP client for a station-data API endpoint (any server producing
the documented JSON schema — see README.md)."""

from __future__ import annotations

from typing import Any

import aiohttp


class CannotConnect(Exception):
    """Raised when the service can't be reached or returns unexpected data."""


async def async_fetch_data(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    """Fetch and return the raw JSON payload from `url` (the exact endpoint,
    e.g. `http://192.0.2.1:8080/data.json` — nothing is appended)."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            return await resp.json()
    except (aiohttp.ClientError, TimeoutError) as err:
        raise CannotConnect(str(err)) from err
