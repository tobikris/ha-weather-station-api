"""The Weather Station API integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_URL, Platform
from homeassistant.core import HomeAssistant

from .const import DEFAULT_SCAN_INTERVAL
from .coordinator import WeatherStationCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]

type WeatherStationConfigEntry = ConfigEntry[WeatherStationCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: WeatherStationConfigEntry) -> bool:
    """Set up Weather Station API from a config entry."""
    coordinator = WeatherStationCoordinator(
        hass,
        entry,
        url=entry.data[CONF_URL],
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # The options flow (add/remove stations) writes into entry.data and needs
    # a reload to rebuild the sensor/weather entity lists to match.
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: WeatherStationConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: WeatherStationConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
