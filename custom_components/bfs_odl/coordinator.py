"""Coordinator for the Strahlenschutz integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Station, StrahlenschutzApiClient, StrahlenschutzApiError, distance_km
from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_SELECTED_STATIONS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)


_LOGGER = logging.getLogger(__name__)


class StrahlenschutzDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch and cache data from the BfS API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: StrahlenschutzApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        self.api = api
        self.config_entry = config_entry
        update_minutes = self.config.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES)
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=int(update_minutes)),
        )

    @property
    def config(self) -> dict[str, Any]:
        """Return merged entry data and options."""
        return {**self.config_entry.data, **self.config_entry.options}

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the upstream API."""
        try:
            stations = await self.api.async_get_latest_stations()
        except StrahlenschutzApiError as err:
            raise UpdateFailed(str(err)) from err

        selected = {str(kenn) for kenn in self.config.get(CONF_SELECTED_STATIONS, [])}
        latitude = float(self.config[CONF_LATITUDE])
        longitude = float(self.config[CONF_LONGITUDE])

        data: dict[str, dict[str, Any]] = {}
        for station in stations:
            if station.kenn not in selected:
                continue
            data[station.kenn] = _station_to_dict(station, latitude, longitude)

        return data


def _station_to_dict(station: Station, latitude: float, longitude: float) -> dict[str, Any]:
    """Convert a station dataclass into serializable runtime data."""
    distance = distance_km(latitude, longitude, station.latitude, station.longitude)
    return {
        "feature_id": station.feature_id,
        "station_id": station.station_id,
        "kenn": station.kenn,
        "name": station.name,
        "plz": station.plz,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "value": station.value,
        "unit": station.unit or "µSv/h",
        "start_measure": station.start_measure,
        "end_measure": station.end_measure,
        "validated": station.validated,
        "validated_text": station.validated_text,
        "nuclide": station.nuclide,
        "duration": station.duration,
        "site_status": station.site_status,
        "site_status_text": station.site_status_text,
        "kid": station.kid,
        "kid_text": station.kid_text,
        "height_above_sea": station.height_above_sea,
        "value_cosmic": station.value_cosmic,
        "value_terrestrial": station.value_terrestrial,
        "api_timestamp": station.api_timestamp,
        "layer": station.layer,
        "distance_km": None if distance == float("inf") else round(distance, 2),
    }
