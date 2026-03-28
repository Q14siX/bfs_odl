"""Sensor platform for Strahlenschutz."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DISTANCE_KM,
    ATTR_KID_TEXT,
    ATTR_SITE_STATUS_TEXT,
    ATTR_VALIDATED_TEXT,
    CONF_SELECTED_STATIONS,
    CONF_STATION_DETAILS,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import StrahlenschutzDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class StrahlenschutzSensorDescription(SensorEntityDescription):
    """Describe a Strahlenschutz sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    extra_attributes_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None
    enum_options: list[str] | None = None
    display_precision: int | None = None


SENSOR_DESCRIPTIONS: tuple[StrahlenschutzSensorDescription, ...] = (
    StrahlenschutzSensorDescription(
        key="gamma_odl_1h",
        name="Gamma-ODL (1h)",
        icon="mdi:radioactive",
        native_unit_of_measurement="µSv/h",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station.get("value"),
        extra_attributes_fn=lambda station, station_info: _primary_attributes(station, station_info),
        display_precision=3,
    ),
    StrahlenschutzSensorDescription(
        key="gamma_odl_1h_cosmic",
        name="Gamma-ODL kosmisch (1h)",
        icon="mdi:weather-night",
        native_unit_of_measurement="µSv/h",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("value_cosmic"),
        display_precision=3,
    ),
    StrahlenschutzSensorDescription(
        key="gamma_odl_1h_terrestrial",
        name="Gamma-ODL terrestrisch (1h)",
        icon="mdi:pine-tree",
        native_unit_of_measurement="µSv/h",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("value_terrestrial"),
        display_precision=3,
    ),
    StrahlenschutzSensorDescription(
        key="distance",
        name="Entfernung",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement="km",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("distance_km"),
        display_precision=2,
    ),
    StrahlenschutzSensorDescription(
        key="height_above_sea",
        name="Höhe über NN",
        icon="mdi:image-filter-hdr",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement="m",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("height_above_sea"),
        display_precision=0,
    ),
    StrahlenschutzSensorDescription(
        key="validation_status",
        name="Prüfstatus",
        icon="mdi:check-decagram",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("validated_text") or "unbekannt",
        enum_options=["geprüft", "ungeprüft", "unbekannt"],
    ),
    StrahlenschutzSensorDescription(
        key="site_status",
        name="Messstellenstatus",
        icon="mdi:radio-tower",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("site_status_text") or "unbekannt",
        enum_options=["in Betrieb", "defekt", "Testbetrieb", "unbekannt"],
    ),
    StrahlenschutzSensorDescription(
        key="kid",
        name="Messnetzknoten",
        icon="mdi:domain",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("kid_text") or "unbekannt",
        enum_options=["Freiburg", "Berlin", "München", "Bonn", "Salzgitter", "Rendsburg", "unbekannt"],
    ),
    StrahlenschutzSensorDescription(
        key="measurement_start",
        name="Messbeginn",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: _parse_datetime(station.get("start_measure")),
    ),
    StrahlenschutzSensorDescription(
        key="measurement_end",
        name="Messende",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: _parse_datetime(station.get("end_measure")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Strahlenschutz sensors from a config entry."""
    coordinator: StrahlenschutzDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    merged = {**entry.data, **entry.options}
    station_details: dict[str, dict[str, Any]] = merged.get(CONF_STATION_DETAILS, {})

    entities = [
        StrahlenschutzStationSensor(
            coordinator=coordinator,
            description=description,
            kenn=str(kenn),
            station_info=station_details.get(str(kenn), {}),
        )
        for kenn in merged.get(CONF_SELECTED_STATIONS, [])
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class StrahlenschutzStationSensor(
    CoordinatorEntity[StrahlenschutzDataUpdateCoordinator], SensorEntity
):
    """Represent one sensor for one selected station."""

    entity_description: StrahlenschutzSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StrahlenschutzDataUpdateCoordinator,
        description: StrahlenschutzSensorDescription,
        kenn: str,
        station_info: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._kenn = kenn
        self._station_info = station_info
        self._attr_unique_id = f"{kenn}_{description.key}"
        if description.display_precision is not None:
            self._attr_suggested_display_precision = description.display_precision
        if description.enum_options is not None:
            self._attr_options = description.enum_options

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._kenn in self.coordinator.data

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        station = self.coordinator.data.get(self._kenn)
        if station is None:
            return None
        return self.entity_description.value_fn(station)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for the station."""
        station = self.coordinator.data.get(self._kenn, {})
        name = station.get("name") or self._station_info.get("name") or self._kenn
        plz = station.get("plz") or self._station_info.get("plz")
        display_name = f"{name} ({self._kenn})"
        if plz:
            display_name = f"{name} {plz} ({self._kenn})"

        return DeviceInfo(
            identifiers={(DOMAIN, self._kenn)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=display_name,
            configuration_url="https://strahlenschutz.api.bund.dev",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.extra_attributes_fn is None:
            return None
        station = self.coordinator.data.get(self._kenn, {})
        return self.entity_description.extra_attributes_fn(station, self._station_info)


def _primary_attributes(station: dict[str, Any], station_info: dict[str, Any]) -> dict[str, Any]:
    """Return richer attributes for the primary dose-rate sensor."""
    value = station.get("value")
    cosmic = station.get("value_cosmic")
    terrestrial = station.get("value_terrestrial")

    cosmic_share = None
    terrestrial_share = None
    if value not in (None, 0) and cosmic is not None:
        cosmic_share = round((cosmic / value) * 100, 1)
    if value not in (None, 0) and terrestrial is not None:
        terrestrial_share = round((terrestrial / value) * 100, 1)

    latitude = station.get("latitude") or station_info.get("latitude")
    longitude = station.get("longitude") or station_info.get("longitude")
    coordinate_text = None
    if latitude is not None and longitude is not None:
        coordinate_text = f"{latitude:.5f}, {longitude:.5f}"

    return {
        "interne_kennung": station.get("kenn"),
        "messstellen_id": station.get("station_id") or station_info.get("station_id"),
        "feature_id": station.get("feature_id"),
        "plz": station.get("plz") or station_info.get("plz"),
        "name": station.get("name") or station_info.get("name"),
        "koordinaten": coordinate_text,
        "latitude": latitude,
        "longitude": longitude,
        ATTR_DISTANCE_KM: station.get("distance_km"),
        "messbeginn": station.get("start_measure"),
        "messende": station.get("end_measure"),
        "messdauer": station.get("duration"),
        "messgroesse": station.get("nuclide"),
        "pruefstatus_code": station.get("validated"),
        ATTR_VALIDATED_TEXT: station.get("validated_text"),
        "messstellenstatus_code": station.get("site_status"),
        ATTR_SITE_STATUS_TEXT: station.get("site_status_text"),
        "messnetzknoten_id": station.get("kid"),
        ATTR_KID_TEXT: station.get("kid_text"),
        "hoehe_ueber_nn_m": station.get("height_above_sea"),
        "wert_kosmisch_µSv_h": cosmic,
        "wert_terrestrisch_µSv_h": terrestrial,
        "anteil_kosmisch_prozent": cosmic_share,
        "anteil_terrestrisch_prozent": terrestrial_share,
        "api_zeitstempel": station.get("api_timestamp"),
        "datenlayer": station.get("layer"),
    }


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO datetime string into a timezone-aware datetime."""
    if not value:
        return None
    dt_value = dt_util.parse_datetime(value)
    if dt_value is None:
        return None
    if dt_value.tzinfo is None:
        return dt_util.as_utc(dt_value)
    return dt_value
