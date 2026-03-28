"""Config flow for Strahlenschutz."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Station, StrahlenschutzApiClient, StrahlenschutzApiError, select_nearby_stations
from .const import (
    CONF_LATITUDE,
    CONF_LOCATION_SOURCE,
    CONF_LONGITUDE,
    CONF_MAX_CANDIDATES,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_SEARCH_RADIUS_KM,
    CONF_SELECTED_STATIONS,
    CONF_STATION_DETAILS,
    DEFAULT_MAX_CANDIDATES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_SEARCH_RADIUS_KM,
    DEFAULT_STATION_COUNT,
    DOMAIN,
    INTEGRATION_NAME,
    LOCATION_SOURCE_HOME,
    LOCATION_SOURCE_MANUAL,
)

DEFAULT_MANUAL_LATITUDE = 51.1657
DEFAULT_MANUAL_LONGITUDE = 10.4515


def _location_source_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=LOCATION_SOURCE_HOME, label="Home Assistant"),
                selector.SelectOptionDict(value=LOCATION_SOURCE_MANUAL, label="Manuell"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="location_source",
        )
    )


def _radius_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=300,
            step=5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="km",
        )
    )


def _candidate_count_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=50,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _scan_interval_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=10,
            max=240,
            step=5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="min",
        )
    )


def _manual_coordinate_schema(config: Mapping[str, Any], hass) -> vol.Schema:
    """Return a robust schema for manual coordinates.

    Plain float validation is used here instead of NumberSelector because the
    selector-based variant can trigger a generic frontend error on some HA
    installations during flow navigation.
    """
    default_latitude = config.get(CONF_LATITUDE)
    if default_latitude is None:
        default_latitude = hass.config.latitude if hass.config.latitude is not None else DEFAULT_MANUAL_LATITUDE

    default_longitude = config.get(CONF_LONGITUDE)
    if default_longitude is None:
        default_longitude = hass.config.longitude if hass.config.longitude is not None else DEFAULT_MANUAL_LONGITUDE

    return vol.Schema(
        {
            vol.Required(CONF_LATITUDE, default=float(default_latitude)): vol.All(
                vol.Coerce(float),
                vol.Range(min=-90, max=90),
            ),
            vol.Required(CONF_LONGITUDE, default=float(default_longitude)): vol.All(
                vol.Coerce(float),
                vol.Range(min=-180, max=180),
            ),
        }
    )


def _base_user_schema(config: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_LOCATION_SOURCE, default=config.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_HOME)): _location_source_selector(),
            vol.Required(CONF_SEARCH_RADIUS_KM, default=config.get(CONF_SEARCH_RADIUS_KM, DEFAULT_SEARCH_RADIUS_KM)): _radius_selector(),
            vol.Required(CONF_MAX_CANDIDATES, default=config.get(CONF_MAX_CANDIDATES, DEFAULT_MAX_CANDIDATES)): _candidate_count_selector(),
            vol.Required(CONF_SCAN_INTERVAL_MINUTES, default=config.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES)): _scan_interval_selector(),
        }
    )


class StrahlenschutzConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Strahlenschutz."""

    VERSION = 1
    MINOR_VERSION = 0

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._candidates: list[tuple[Station, float]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._config = {
                CONF_LOCATION_SOURCE: user_input[CONF_LOCATION_SOURCE],
                CONF_SEARCH_RADIUS_KM: int(user_input[CONF_SEARCH_RADIUS_KM]),
                CONF_MAX_CANDIDATES: int(user_input[CONF_MAX_CANDIDATES]),
                CONF_SCAN_INTERVAL_MINUTES: int(user_input[CONF_SCAN_INTERVAL_MINUTES]),
            }
            if user_input[CONF_LOCATION_SOURCE] == LOCATION_SOURCE_HOME:
                if self.hass.config.latitude is None or self.hass.config.longitude is None:
                    errors["base"] = "home_location_missing"
                else:
                    self._config[CONF_LATITUDE] = float(self.hass.config.latitude)
                    self._config[CONF_LONGITUDE] = float(self.hass.config.longitude)
                    return await self._async_prepare_station_selection(return_step_id="user")
            else:
                return await self.async_step_manual_location()

        return self.async_show_form(step_id="user", data_schema=_base_user_schema(self._config), errors=errors)

    async def async_step_manual_location(self, user_input: dict[str, Any] | None = None):
        """Handle manual coordinate entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._config[CONF_LATITUDE] = float(user_input[CONF_LATITUDE])
                self._config[CONF_LONGITUDE] = float(user_input[CONF_LONGITUDE])
            except (TypeError, ValueError):
                errors["base"] = "invalid_coordinates"
            else:
                return await self._async_prepare_station_selection(return_step_id="manual_location")

        return self.async_show_form(
            step_id="manual_location",
            data_schema=_manual_coordinate_schema(self._config, self.hass),
            errors=errors,
        )

    async def async_step_select_stations(self, user_input: dict[str, Any] | None = None):
        """Handle station selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected = [str(kenn) for kenn in user_input[CONF_SELECTED_STATIONS]]
            if not selected:
                errors[CONF_SELECTED_STATIONS] = "no_station_selected"
            else:
                station_details = {
                    station.kenn: {
                        "station_id": station.station_id,
                        "name": station.name,
                        "plz": station.plz,
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                    }
                    for station, _ in self._candidates
                    if station.kenn in selected
                }

                title = f"{INTEGRATION_NAME} ({len(selected)} Messpunkte)"
                return self.async_create_entry(
                    title=title,
                    data={
                        **self._config,
                        CONF_SELECTED_STATIONS: selected,
                        CONF_STATION_DETAILS: station_details,
                    },
                )

        options = [
            selector.SelectOptionDict(value=station.kenn, label=_station_label(station, distance))
            for station, distance in self._candidates
        ]
        default_selection = [station.kenn for station, _ in self._candidates[:DEFAULT_STATION_COUNT]]

        schema = vol.Schema(
            {
                vol.Required(CONF_SELECTED_STATIONS, default=default_selection): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="select_stations",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "latitude": f"{self._config[CONF_LATITUDE]:.5f}",
                "longitude": f"{self._config[CONF_LONGITUDE]:.5f}",
                "radius": str(self._config[CONF_SEARCH_RADIUS_KM]),
                "candidate_count": str(len(self._candidates)),
            },
        )

    async def _async_prepare_station_selection(self, return_step_id: str):
        """Fetch stations and calculate nearby candidates."""
        session = async_get_clientsession(self.hass)
        api = StrahlenschutzApiClient(session)

        try:
            stations = await api.async_get_latest_stations()
        except StrahlenschutzApiError:
            if return_step_id == "manual_location":
                return self.async_show_form(
                    step_id="manual_location",
                    data_schema=_manual_coordinate_schema(self._config, self.hass),
                    errors={"base": "cannot_connect"},
                )
            return self.async_show_form(
                step_id="user",
                data_schema=_base_user_schema(self._config),
                errors={"base": "cannot_connect"},
            )

        self._candidates = select_nearby_stations(
            stations=stations,
            latitude=float(self._config[CONF_LATITUDE]),
            longitude=float(self._config[CONF_LONGITUDE]),
            radius_km=float(self._config[CONF_SEARCH_RADIUS_KM]),
            max_candidates=int(self._config[CONF_MAX_CANDIDATES]),
        )

        return await self.async_step_select_stations()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return StrahlenschutzOptionsFlow(config_entry)


class StrahlenschutzOptionsFlow(OptionsFlow):
    """Handle options for Strahlenschutz."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry
        self._config: dict[str, Any] = {**config_entry.data, **config_entry.options}
        self._candidates: list[tuple[Station, float]] = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage basic options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._config.update(
                {
                    CONF_LOCATION_SOURCE: user_input[CONF_LOCATION_SOURCE],
                    CONF_SEARCH_RADIUS_KM: int(user_input[CONF_SEARCH_RADIUS_KM]),
                    CONF_MAX_CANDIDATES: int(user_input[CONF_MAX_CANDIDATES]),
                    CONF_SCAN_INTERVAL_MINUTES: int(user_input[CONF_SCAN_INTERVAL_MINUTES]),
                }
            )
            if user_input[CONF_LOCATION_SOURCE] == LOCATION_SOURCE_HOME:
                if self.hass.config.latitude is None or self.hass.config.longitude is None:
                    errors["base"] = "home_location_missing"
                else:
                    self._config[CONF_LATITUDE] = float(self.hass.config.latitude)
                    self._config[CONF_LONGITUDE] = float(self.hass.config.longitude)
                    return await self._async_prepare_station_selection(return_step_id="init")
            else:
                return await self.async_step_manual_location()

        return self.async_show_form(step_id="init", data_schema=_base_user_schema(self._config), errors=errors)

    async def async_step_manual_location(self, user_input: dict[str, Any] | None = None):
        """Handle manual coordinates for options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._config[CONF_LATITUDE] = float(user_input[CONF_LATITUDE])
                self._config[CONF_LONGITUDE] = float(user_input[CONF_LONGITUDE])
            except (TypeError, ValueError):
                errors["base"] = "invalid_coordinates"
            else:
                return await self._async_prepare_station_selection(return_step_id="manual_location")

        return self.async_show_form(
            step_id="manual_location",
            data_schema=_manual_coordinate_schema(self._config, self.hass),
            errors=errors,
        )

    async def async_step_select_stations(self, user_input: dict[str, Any] | None = None):
        """Select stations for the options flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected = [str(kenn) for kenn in user_input[CONF_SELECTED_STATIONS]]
            if not selected:
                errors[CONF_SELECTED_STATIONS] = "no_station_selected"
            else:
                station_details = {
                    station.kenn: {
                        "station_id": station.station_id,
                        "name": station.name,
                        "plz": station.plz,
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                    }
                    for station, _ in self._candidates
                    if station.kenn in selected
                }
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_LOCATION_SOURCE: self._config[CONF_LOCATION_SOURCE],
                        CONF_LATITUDE: self._config[CONF_LATITUDE],
                        CONF_LONGITUDE: self._config[CONF_LONGITUDE],
                        CONF_SEARCH_RADIUS_KM: self._config[CONF_SEARCH_RADIUS_KM],
                        CONF_MAX_CANDIDATES: self._config[CONF_MAX_CANDIDATES],
                        CONF_SCAN_INTERVAL_MINUTES: self._config[CONF_SCAN_INTERVAL_MINUTES],
                        CONF_SELECTED_STATIONS: selected,
                        CONF_STATION_DETAILS: station_details,
                    },
                )

        options = [
            selector.SelectOptionDict(value=station.kenn, label=_station_label(station, distance))
            for station, distance in self._candidates
        ]
        current_selection = [
            station.kenn
            for station, _ in self._candidates
            if station.kenn in set(self._config.get(CONF_SELECTED_STATIONS, []))
        ]
        if not current_selection:
            current_selection = [station.kenn for station, _ in self._candidates[:DEFAULT_STATION_COUNT]]

        schema = vol.Schema(
            {
                vol.Required(CONF_SELECTED_STATIONS, default=current_selection): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="select_stations",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "latitude": f"{self._config[CONF_LATITUDE]:.5f}",
                "longitude": f"{self._config[CONF_LONGITUDE]:.5f}",
                "radius": str(self._config[CONF_SEARCH_RADIUS_KM]),
                "candidate_count": str(len(self._candidates)),
            },
        )

    async def _async_prepare_station_selection(self, return_step_id: str):
        """Fetch stations and calculate nearby candidates for options."""
        session = async_get_clientsession(self.hass)
        api = StrahlenschutzApiClient(session)

        try:
            stations = await api.async_get_latest_stations()
        except StrahlenschutzApiError:
            if return_step_id == "manual_location":
                return self.async_show_form(
                    step_id="manual_location",
                    data_schema=_manual_coordinate_schema(self._config, self.hass),
                    errors={"base": "cannot_connect"},
                )
            return self.async_show_form(
                step_id="init",
                data_schema=_base_user_schema(self._config),
                errors={"base": "cannot_connect"},
            )

        self._candidates = select_nearby_stations(
            stations=stations,
            latitude=float(self._config[CONF_LATITUDE]),
            longitude=float(self._config[CONF_LONGITUDE]),
            radius_km=float(self._config[CONF_SEARCH_RADIUS_KM]),
            max_candidates=int(self._config[CONF_MAX_CANDIDATES]),
        )

        return await self.async_step_select_stations()


def _station_label(station: Station, distance: float) -> str:
    """Return a user friendly option label."""
    status = station.site_status_text or "unbekannt"
    value = "n. v."
    if station.value is not None:
        value = f"{station.value:.3f} {station.unit or 'µSv/h'}"
    return f"{station.name} ({station.plz or 'ohne PLZ'}) · {distance:.1f} km · {value} · {status} · {station.kenn}"
