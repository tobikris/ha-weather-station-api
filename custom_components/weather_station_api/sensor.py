"""Sensor platform: one entity per station per metric."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WeatherStationConfigEntry
from .const import CONF_STATIONS, DOMAIN, METRICS, MetricInfo
from .coordinator import WeatherStationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeatherStationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one sensor per selected station per metric."""
    coordinator = entry.runtime_data
    station_ids: list[str] = entry.data[CONF_STATIONS]

    entities = [
        WeatherStationSensor(coordinator, entry.entry_id, station_id, metric)
        for station_id in station_ids
        for metric in METRICS
    ]
    async_add_entities(entities)


class WeatherStationSensor(CoordinatorEntity[WeatherStationCoordinator], SensorEntity):
    """A single metric (temperature, humidity, ...) for one station."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    # `rain` may actually be a running daily total rather than a per-reading
    # instantaneous value (unverified against real rainy-day data); switch to
    # SensorStateClass.TOTAL_INCREASING for that metric if so.

    def __init__(
        self,
        coordinator: WeatherStationCoordinator,
        entry_id: str,
        station_id: str,
        metric: MetricInfo,
    ) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._metric = metric
        self._attr_unique_id = f"{entry_id}_{station_id}_{metric.key}"
        self._attr_translation_key = metric.key
        self._attr_device_class = metric.device_class
        self._attr_native_unit_of_measurement = metric.unit
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

    @property
    def native_value(self) -> float | None:
        station = self.coordinator.data.get(self._station_id, {})
        metric = station.get("metrics", {}).get(self._metric.key, {})
        latest = metric.get("latest")
        return latest.get("v") if latest else None
