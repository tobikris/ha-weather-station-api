"""Shared constants for the Weather Station API integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "weather_station_api"

DEFAULT_SCAN_INTERVAL = 1800  # seconds; matches the source's own update cadence

CONF_STATIONS = "stations"


@dataclass(frozen=True)
class MetricInfo:
    """Static metadata for one of the six scraped metrics."""

    key: str
    device_class: str
    unit: str


# The six metric keys the API schema's `metrics` object may carry per station,
# plus the HA device_class/unit each maps to.
METRICS: tuple[MetricInfo, ...] = (
    MetricInfo("temperature", "temperature", "°C"),
    MetricInfo("humidity", "humidity", "%"),
    MetricInfo("pressure", "pressure", "hPa"),
    MetricInfo("wind", "wind_speed", "m/s"),
    MetricInfo("solar", "irradiance", "W/m²"),
    MetricInfo("rain", "precipitation", "mm"),
)

# Weather-domain condition, derived from rain + solar (the API reports no
# condition of its own): rain > 0 -> rainy; else solar above this threshold ->
# sunny; solar > 0 but below it -> cloudy; solar ~0 -> clear-night.
SUNNY_SOLAR_THRESHOLD = 100
