# Weather Station API

A Home Assistant custom integration that turns any HTTP endpoint returning the
JSON schema documented below into `sensor.*` and `weather.*` entities — one
device per station, picked from a live list, no YAML required.

It doesn't talk to any specific weather-station brand, vendor, or region. It
talks to *your* server, as long as that server speaks the schema below — any
backend producing this JSON works.

## API format

`GET <your-url>` must return:

```json
{
  "generated_at": "2026-07-28T13:53:39Z",
  "stations": [
    {
      "station_id": "70B3D58FF102FF4E",
      "station_name": "Rooftop Station",
      "metrics": {
        "temperature": { "unit": "°C",   "latest": { "t": "2026-07-28T13:53:39", "v": 21.7 } },
        "humidity":    { "unit": "%",    "latest": { "t": "2026-07-28T13:53:39", "v": 36.0 } },
        "pressure":    { "unit": "hPa",  "latest": { "t": "2026-07-28T13:53:39", "v": 999.5 } },
        "wind":        { "unit": "m/s",  "latest": { "t": "2026-07-28T13:53:39", "v": 0.4 } },
        "solar":       { "unit": "W/m²", "latest": { "t": "2026-07-28T13:53:39", "v": 58.0 } },
        "rain":        { "unit": "mm",   "latest": { "t": "2026-07-28T13:53:39", "v": 0.0 } }
      }
    }
  ]
}
```

- `stations` may contain any number of entries; the integration's setup step
  lets you pick which ones to create entities for.
- All six `metrics` keys are optional per station — a station missing a metric
  just doesn't get that sensor.
- Only `latest.v` is read; any additional fields (e.g. a full time series) are
  ignored.

## Installation

### HACS (custom repository)

1. HACS → the `⋮` menu → **Custom repositories**.
2. Add `https://github.com/tobikris/ha-weather-station-api`, category
   **Integration**.
3. Install **Weather Station API**, restart Home Assistant.

### Manual

Copy `custom_components/weather_station_api` into your Home Assistant's
`custom_components/` directory, then restart.

## Setup

**Settings → Devices & Services → Add Integration → Weather Station API.**

1. Enter the full URL of your API endpoint (e.g.
   `http://192.0.2.1:8080/data.json`) and a refresh interval in seconds.
2. Pick which stations to create entities for, from the live list your server
   returns.

Each selected station becomes one device with:

- Six `sensor.*` entities (temperature, humidity, pressure, wind, solar
  irradiance, rain) — whichever metrics that station actually reports.
- One `weather.*` entity, covering temperature/humidity/pressure/wind (the
  `weather` domain has no field for solar irradiance or rain, so those stay
  sensor-only). Since the API reports no `condition`, one is derived from real
  rain + solar readings: rain > 0 → rainy; solar above a 100 W/m² threshold →
  sunny; solar > 0 but below that → cloudy; solar ~0 → clear-night.

## Adding or removing stations later

**Settings → Devices & Services → Weather Station API → Configure.**

Re-fetches the live station list from your server and lets you change the
selection — no reinstall, no restart, no YAML. Removed stations' entities go
`unavailable` rather than being deleted (Home Assistant's normal behavior for
an entity a config entry stops creating); re-adding the station brings them
back live.

## License

MIT — see [LICENSE](LICENSE).
