"""DataUpdateCoordinator polling a station-data API endpoint (any server
producing the documented JSON schema — see README.md)."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, async_fetch_data
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WeatherStationCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetches the station-data endpoint and indexes it by station_id for entity lookup."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        url: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._url = url
        # Shown as the device manufacturer — the actual source host, since the
        # integration itself has no fixed brand behind it.
        self.source_host = urlparse(url).netloc or url

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        session = async_get_clientsession(self.hass)
        try:
            payload = await async_fetch_data(session, self._url)
        except CannotConnect as err:
            raise UpdateFailed(str(err)) from err

        stations = payload.get("stations", [])
        return {s["station_id"]: s for s in stations if "station_id" in s}
