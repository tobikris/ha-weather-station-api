"""Config flow: enter the /data.json URL, then pick stations from a live list."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import CannotConnect, async_fetch_data
from .const import CONF_STATIONS, DEFAULT_SCAN_INTERVAL, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


def _station_options(stations: list[dict[str, Any]]) -> list[SelectOptionDict]:
    """Selector options for a station list, sorted by display name."""
    return [
        SelectOptionDict(value=s["station_id"], label=s["station_name"])
        for s in sorted(stations, key=lambda s: s["station_name"].casefold())
    ]


class WeatherStationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handles a config flow for Weather Station API."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> WeatherStationOptionsFlow:
        """Add/remove stations after initial setup, without re-entering the URL."""
        return WeatherStationOptionsFlow()

    def __init__(self) -> None:
        self._url: str | None = None
        self._scan_interval: int = DEFAULT_SCAN_INTERVAL
        self._available_stations: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step: where is the station-data API endpoint."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._url = user_input[CONF_URL]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL]

            self._async_abort_entries_match({CONF_URL: self._url})

            session = async_get_clientsession(self.hass)
            try:
                payload = await async_fetch_data(session, self._url)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                self._available_stations = payload.get("stations", [])
                if not self._available_stations:
                    errors["base"] = "no_stations"
                else:
                    return await self.async_step_stations()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, user_input or {}
            ),
            errors=errors,
            description_placeholders={"example_url": "http://192.0.2.1:8080/data.json"},
        )

    async def async_step_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Second step: which of the live stations to create entities for."""
        if user_input is not None:
            await self.async_set_unique_id(self._url)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Weather Station API ({self._url})",
                data={
                    CONF_URL: self._url,
                    CONF_SCAN_INTERVAL: self._scan_interval,
                    CONF_STATIONS: user_input[CONF_STATIONS],
                },
            )

        options = _station_options(self._available_stations)
        all_ids = [o["value"] for o in options]

        schema = vol.Schema(
            {
                vol.Required(CONF_STATIONS, default=all_ids): SelectSelector(
                    SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.LIST)
                ),
            }
        )
        return self.async_show_form(step_id="stations", data_schema=schema)


class WeatherStationOptionsFlow(OptionsFlow):
    """Re-fetches the live station list and lets you change the selection —
    the integration's "Configure" button. Writes back into the config
    entry's `data` (station selection isn't part of its identity/unique_id,
    just current entities to create) and reloads the entry to apply it."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_STATIONS: user_input[CONF_STATIONS]},
            )
            return self.async_create_entry(data={})

        session = async_get_clientsession(self.hass)
        try:
            payload = await async_fetch_data(session, self.config_entry.data[CONF_URL])
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        available = payload.get("stations", [])
        if not available:
            return self.async_abort(reason="no_stations")

        options = _station_options(available)
        current = self.config_entry.data.get(CONF_STATIONS, [])

        schema = vol.Schema(
            {
                vol.Required(CONF_STATIONS, default=current): SelectSelector(
                    SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.LIST)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
