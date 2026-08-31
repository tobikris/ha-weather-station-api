"""Weather platform: one entity per station (temperature/humidity/pressure/wind).

No forecast data and no reported `condition` — solar irradiance and rain stay
sensor-only (the weather domain has no field for either), and `condition` is
derived from those two readings rather than left blank. See
SUNNY_SOLAR_THRESHOLD in const.py for the exact heuristic.
"""

from __future__ import annotations

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WeatherStationConfigEntry
from .const import CONF_STATIONS, DOMAIN, SUNNY_SOLAR_THRESHOLD
from .coordinator import WeatherStationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeatherStationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one weather entity per selected station."""
    coordinator = entry.runtime_data
    station_ids: list[str] = entry.data[CONF_STATIONS]
    async_add_entities(
        WeatherStationWeather(coordinator, entry.entry_id, station_id)
        for station_id in station_ids
    )


class WeatherStationWeather(CoordinatorEntity[WeatherStationCoordinator], WeatherEntity):
    """Current conditions for one station."""

    _attr_has_entity_name = True
    _attr_name = None  # use the device name as-is
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = WeatherEntityFeature(0)

    def __init__(
        self, coordinator: WeatherStationCoordinator, entry_id: str, station_id: str
    ) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_unique_id = f"{entry_id}_{station_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=self._station_name,
            manufacturer=coordinator.source_host,
            model="Weather Station",
        )

    @property
    def _station_name(self) -> str:
        station = self.coordinator.data.get(self._station_id, {})
        return station.get("station_name", self._station_id)

    @property
    def available(self) -> bool:
        return super().available and self._station_id in self.coordinator.data

    def _metric(self, key: str) -> float | None:
        station = self.coordinator.data.get(self._station_id, {})
        latest = station.get("metrics", {}).get(key, {}).get("latest")
        return latest.get("v") if latest else None

    @property
    def native_temperature(self) -> float | None:
        return self._metric("temperature")

    @property
    def humidity(self) -> float | None:
        return self._metric("humidity")

    @property
    def native_pressure(self) -> float | None:
        return self._metric("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        return self._metric("wind")

    @property
    def condition(self) -> str | None:
        rain = self._metric("rain")
        solar = self._metric("solar")
        if rain is None or solar is None:
            return None
        if rain > 0:
            return ATTR_CONDITION_RAINY
        if solar > SUNNY_SOLAR_THRESHOLD:
            return ATTR_CONDITION_SUNNY
        if solar > 0:
            return ATTR_CONDITION_CLOUDY
        return ATTR_CONDITION_CLEAR_NIGHT
