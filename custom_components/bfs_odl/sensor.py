"""Sensor platform for BfS ODL."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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
    DEFAULT_THRESHOLD_HIGH_USV_H,
    DEFAULT_THRESHOLD_LOW_USV_H,
    DOMAIN,
    KID_STATES,
    MANUFACTURER,
    MEASUREMENT_ASSESSMENT_ABOVE_CONFIGURED,
    MEASUREMENT_ASSESSMENT_ABOVE_NATURAL,
    MEASUREMENT_ASSESSMENT_BELOW_CONFIGURED,
    MEASUREMENT_ASSESSMENT_BELOW_NATURAL,
    MEASUREMENT_ASSESSMENT_NO_DATA,
    MEASUREMENT_ASSESSMENT_WITHIN_CONFIGURED,
    MEASUREMENT_ASSESSMENT_WITHIN_NATURAL,
    MODEL,
    SITE_STATUS_STATES,
    VALIDATED_STATES,
)
from .coordinator import StrahlenschutzDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class BfsOdlSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    enum_options: list[str] | None = None
    display_precision: int | None = None


def _validation_state(station: dict[str, Any]) -> str:
    code = station.get("validated")
    if code is None:
        return "unknown"
    return VALIDATED_STATES.get(code, "unknown")


def _site_status_state(station: dict[str, Any]) -> str:
    code = station.get("site_status")
    if code is None:
        return "unknown"
    return SITE_STATUS_STATES.get(code, "unknown")


def _kid_state(station: dict[str, Any]) -> str:
    code = station.get("kid")
    if code is None:
        return "unknown"
    return KID_STATES.get(code, "unknown")


def _uses_default_assessment_thresholds(low: float, high: float) -> bool:
    return abs(low - DEFAULT_THRESHOLD_LOW_USV_H) < 1e-9 and abs(high - DEFAULT_THRESHOLD_HIGH_USV_H) < 1e-9


def _measurement_assessment_state(station: dict[str, Any], low: float, high: float) -> str:
    value = station.get("value")
    if value is None:
        return MEASUREMENT_ASSESSMENT_NO_DATA
    if _uses_default_assessment_thresholds(low, high):
        if value < low:
            return MEASUREMENT_ASSESSMENT_BELOW_NATURAL
        if value > high:
            return MEASUREMENT_ASSESSMENT_ABOVE_NATURAL
        return MEASUREMENT_ASSESSMENT_WITHIN_NATURAL
    if value < low:
        return MEASUREMENT_ASSESSMENT_BELOW_CONFIGURED
    if value > high:
        return MEASUREMENT_ASSESSMENT_ABOVE_CONFIGURED
    return MEASUREMENT_ASSESSMENT_WITHIN_CONFIGURED


def _parse_datetime_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    dt_value = dt_util.parse_datetime(value)
    if dt_value is None:
        return None
    if dt_value.tzinfo is None:
        return dt_util.as_utc(dt_value)
    return dt_util.as_utc(dt_value)


def _format_local_iso(value: str | None) -> str | None:
    dt_value = _parse_datetime_utc(value)
    if dt_value is None:
        return None
    return dt_util.as_local(dt_value).isoformat()


def _format_utc_iso(value: str | None) -> str | None:
    dt_value = _parse_datetime_utc(value)
    if dt_value is None:
        return None
    return dt_util.as_utc(dt_value).isoformat()


def _assessment_attributes(station: dict[str, Any], low: float, high: float) -> dict[str, Any]:
    uses_defaults = _uses_default_assessment_thresholds(low, high)
    return {
        "current_value_uSv_h": station.get("value"),
        "threshold_low_uSv_h": low,
        "threshold_high_uSv_h": high,
        "assessment_model": "natural_reference_range" if uses_defaults else "user_configured_range",
        "uses_default_thresholds": uses_defaults,
        "uses_legal_limit": False,
        "api_timezone": "UTC",
        "local_timezone": str(dt_util.DEFAULT_TIME_ZONE),
    }


def _primary_attributes(station: dict[str, Any], station_info: dict[str, Any], low: float, high: float) -> dict[str, Any]:
    value = station.get("value")
    cosmic = station.get("value_cosmic")
    terrestrial = station.get("value_terrestrial")
    cosmic_share = round((cosmic / value) * 100, 1) if value not in (None, 0) and cosmic is not None else None
    terrestrial_share = round((terrestrial / value) * 100, 1) if value not in (None, 0) and terrestrial is not None else None
    latitude = station.get("latitude") or station_info.get("latitude")
    longitude = station.get("longitude") or station_info.get("longitude")
    coordinate_text = f"{latitude:.5f}, {longitude:.5f}" if latitude is not None and longitude is not None else None
    start_local = _format_local_iso(station.get("start_measure"))
    end_local = _format_local_iso(station.get("end_measure"))
    api_local = _format_local_iso(station.get("api_timestamp"))
    start_utc = _format_utc_iso(station.get("start_measure"))
    end_utc = _format_utc_iso(station.get("end_measure"))
    api_utc = _format_utc_iso(station.get("api_timestamp"))
    uses_defaults = _uses_default_assessment_thresholds(low, high)
    return {
        "station_code": station.get("kenn"),
        "station_id": station.get("station_id") or station_info.get("station_id"),
        "feature_id": station.get("feature_id"),
        "postal_code": station.get("plz") or station_info.get("plz"),
        "station_name": station.get("name") or station_info.get("name"),
        "coordinates": coordinate_text,
        "latitude": latitude,
        "longitude": longitude,
        ATTR_DISTANCE_KM: station.get("distance_km"),
        "measurement_start": start_local,
        "measurement_end": end_local,
        "measurement_start_utc": start_utc,
        "measurement_end_utc": end_utc,
        "api_timestamp": api_local,
        "api_timestamp_utc": api_utc,
        "duration": station.get("duration"),
        "quantity": station.get("nuclide"),
        "validation_code": station.get("validated"),
        ATTR_VALIDATED_TEXT: station.get("validated_text"),
        "site_status_code": station.get("site_status"),
        ATTR_SITE_STATUS_TEXT: station.get("site_status_text"),
        "network_node_id": station.get("kid"),
        ATTR_KID_TEXT: station.get("kid_text"),
        "height_above_sea_m": station.get("height_above_sea"),
        "cosmic_value_uSv_h": cosmic,
        "terrestrial_value_uSv_h": terrestrial,
        "cosmic_share_percent": cosmic_share,
        "terrestrial_share_percent": terrestrial_share,
        "data_layer": station.get("layer"),
        "assessment_state": _measurement_assessment_state(station, low, high),
        "assessment_threshold_low_uSv_h": low,
        "assessment_threshold_high_uSv_h": high,
        "assessment_uses_default_thresholds": uses_defaults,
        "assessment_model": "natural_reference_range" if uses_defaults else "user_configured_range",
        "api_timezone": "UTC",
        "local_timezone": str(dt_util.DEFAULT_TIME_ZONE),
    }


SENSOR_DESCRIPTIONS: tuple[BfsOdlSensorDescription, ...] = (
    BfsOdlSensorDescription(
        key="gamma_odl_1h",
        translation_key="gamma_odl_1h",
        icon="mdi:radioactive",
        native_unit_of_measurement="µSv/h",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda station: station.get("value"),
        display_precision=3,
    ),
    BfsOdlSensorDescription(
        key="measurement_assessment",
        translation_key="measurement_assessment",
        icon="mdi:chart-bell-curve-cumulative",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda station: station,
        enum_options=[
            MEASUREMENT_ASSESSMENT_NO_DATA,
            MEASUREMENT_ASSESSMENT_BELOW_NATURAL,
            MEASUREMENT_ASSESSMENT_WITHIN_NATURAL,
            MEASUREMENT_ASSESSMENT_ABOVE_NATURAL,
            MEASUREMENT_ASSESSMENT_BELOW_CONFIGURED,
            MEASUREMENT_ASSESSMENT_WITHIN_CONFIGURED,
            MEASUREMENT_ASSESSMENT_ABOVE_CONFIGURED,
        ],
    ),
    BfsOdlSensorDescription(
        key="gamma_odl_1h_cosmic",
        translation_key="gamma_odl_1h_cosmic",
        icon="mdi:weather-night",
        native_unit_of_measurement="µSv/h",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("value_cosmic"),
        display_precision=3,
    ),
    BfsOdlSensorDescription(
        key="gamma_odl_1h_terrestrial",
        translation_key="gamma_odl_1h_terrestrial",
        icon="mdi:pine-tree",
        native_unit_of_measurement="µSv/h",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("value_terrestrial"),
        display_precision=3,
    ),
    BfsOdlSensorDescription(
        key="distance",
        translation_key="distance",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement="km",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("distance_km"),
        display_precision=2,
    ),
    BfsOdlSensorDescription(
        key="height_above_sea",
        translation_key="height_above_sea",
        icon="mdi:image-filter-hdr",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement="m",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("height_above_sea"),
        display_precision=0,
    ),
    BfsOdlSensorDescription(
        key="station_id",
        translation_key="station_id",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("station_id"),
    ),
    BfsOdlSensorDescription(
        key="station_code",
        translation_key="station_code",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: station.get("kenn"),
    ),
    BfsOdlSensorDescription(
        key="validation_status",
        translation_key="validation_status",
        icon="mdi:check-decagram",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=_validation_state,
        enum_options=["validated", "unvalidated", "unknown"],
    ),
    BfsOdlSensorDescription(
        key="site_status",
        translation_key="site_status",
        icon="mdi:radio-tower",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=_site_status_state,
        enum_options=["in_operation", "defective", "test_operation", "unknown"],
    ),
    BfsOdlSensorDescription(
        key="kid",
        translation_key="kid",
        icon="mdi:domain",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=_kid_state,
        enum_options=["freiburg", "berlin", "munich", "bonn", "salzgitter", "rendsburg", "unknown"],
    ),
    BfsOdlSensorDescription(
        key="measurement_start",
        translation_key="measurement_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: _parse_datetime_utc(station.get("start_measure")),
    ),
    BfsOdlSensorDescription(
        key="measurement_end",
        translation_key="measurement_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda station: _parse_datetime_utc(station.get("end_measure")),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: StrahlenschutzDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    merged = {**entry.data, **entry.options}
    station_details: dict[str, dict[str, Any]] = merged.get(CONF_STATION_DETAILS, {})
    entities = [
        BfsOdlStationSensor(coordinator=coordinator, description=description, kenn=str(kenn), station_info=station_details.get(str(kenn), {}))
        for kenn in merged.get(CONF_SELECTED_STATIONS, [])
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class BfsOdlStationSensor(CoordinatorEntity[StrahlenschutzDataUpdateCoordinator], SensorEntity):
    entity_description: BfsOdlSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: StrahlenschutzDataUpdateCoordinator, description: BfsOdlSensorDescription, kenn: str, station_info: dict[str, Any]) -> None:
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
        return self._kenn in self.coordinator.data

    @property
    def native_value(self) -> Any:
        station = self.coordinator.data.get(self._kenn)
        if station is None:
            return None
        if self.entity_description.key == "measurement_assessment":
            low, high = self.coordinator.assessment_thresholds
            return _measurement_assessment_state(station, low, high)
        return self.entity_description.value_fn(station)

    @property
    def device_info(self) -> DeviceInfo:
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
            configuration_url="https://odlinfo.bfs.de/ODL/DE/service/datenschnittstelle/datenschnittstelle_node.html",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        station = self.coordinator.data.get(self._kenn)
        if station is None:
            return None
        low, high = self.coordinator.assessment_thresholds
        if self.entity_description.key == "gamma_odl_1h":
            return _primary_attributes(station, self._station_info, low, high)
        if self.entity_description.key == "measurement_assessment":
            return _assessment_attributes(station, low, high)
        return None
