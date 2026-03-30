"""API client for the BfS ODL-Info API."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from math import asin, cos, radians, sin, sqrt
from typing import Any
import xml.etree.ElementTree as ET

from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE_URLS,
    API_TIMEOUT_SECONDS,
    API_VERSION,
    KID_LABELS,
    LATEST_LAYER,
    SITE_STATUS_LABELS,
    VALIDATED_LABELS,
)

_LOGGER = logging.getLogger(__name__)


class StrahlenschutzApiError(RuntimeError):
    """Raised when the Strahlenschutz API request fails."""


@dataclass(slots=True)
class Station:
    """Representation of one BfS station reading."""

    feature_id: str
    station_id: str
    kenn: str
    name: str
    plz: str | None
    latitude: float | None
    longitude: float | None
    value: float | None
    unit: str | None
    start_measure: str | None
    end_measure: str | None
    validated: int | None
    validated_text: str | None
    nuclide: str | None
    duration: str | None
    site_status: int | None
    site_status_text: str | None
    kid: int | None
    kid_text: str | None
    height_above_sea: float | None
    value_cosmic: float | None
    value_terrestrial: float | None
    api_timestamp: str | None
    layer: str

    @property
    def title(self) -> str:
        """Return a user friendly station title."""
        if self.plz:
            return f"{self.name} ({self.plz})"
        return self.name


class StrahlenschutzApiClient:
    """Async client for the BfS ODL-Info API."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get_json(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform one HTTP GET and return JSON.

        The BfS service is documented as a WFS endpoint. In practice, it may return
        a ServiceException XML document when a parameter combination is rejected.
        Therefore we first read the response as text, then try JSON, and finally
        extract a useful error from XML if needed.
        """
        last_error: str | None = None

        headers = {
            "Accept": "application/json, */*;q=0.8",
            "User-Agent": "HomeAssistant-BfS-ODL/20260331",
        }

        for base_url in API_BASE_URLS:
            try:
                async with self._session.get(
                    base_url,
                    params=params,
                    headers=headers,
                    timeout=API_TIMEOUT_SECONDS,
                ) as response:
                    text = await response.text()
                    response.raise_for_status()
            except (TimeoutError, ClientError) as err:
                last_error = f"{base_url}: {err}"
                _LOGGER.debug("BfS request against %s failed: %s", base_url, err)
                continue

            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                service_error = _extract_service_exception(text)
                if service_error:
                    last_error = f"{base_url}: {service_error}"
                    _LOGGER.debug(
                        "BfS service exception from %s: %s", base_url, service_error
                    )
                    continue

                last_error = f"{base_url}: unexpected non-JSON response"
                _LOGGER.debug(
                    "Unexpected non-JSON response from %s: %.500r", base_url, text
                )
                continue

            if not isinstance(data, dict):
                last_error = f"{base_url}: unexpected payload"
                _LOGGER.debug("Unexpected payload type from %s: %s", base_url, type(data))
                continue

            return data

        raise StrahlenschutzApiError(last_error or "API request failed")

    async def async_get_latest_stations(self) -> list[Station]:
        """Return the latest 1-hour value for all stations.

        Although the OpenAPI description documents ``maxFeatures`` and ``startIndex``,
        the public examples from BfS and working Home Assistant community examples use
        the unpaginated request. The service only exposes about 1.7k stations, so a
        single full download is small enough and avoids compatibility issues.
        """
        candidate_params = [
            {
                "service": "WFS",
                "version": API_VERSION,
                "request": "GetFeature",
                "typeName": LATEST_LAYER,
                "outputFormat": "application/json",
            },
            {
                "service": "WFS",
                "version": API_VERSION,
                "request": "GetFeature",
                "typeName": LATEST_LAYER,
                "outputFormat": "json",
            },
        ]

        last_error: StrahlenschutzApiError | None = None
        for params in candidate_params:
            try:
                payload = await self._get_json(params)
                features = payload.get("features", [])
                if not isinstance(features, list):
                    raise StrahlenschutzApiError(
                        "API response did not contain a features list"
                    )
                api_timestamp = _coerce_str_or_none(payload.get("timeStamp"))
                return [self._parse_station(feature, api_timestamp) for feature in features]
            except StrahlenschutzApiError as err:
                last_error = err
                _LOGGER.debug(
                    "BfS request variant failed for %s: %s",
                    params.get("outputFormat"),
                    err,
                )

        raise last_error or StrahlenschutzApiError("API request failed")

    @staticmethod
    def _parse_station(feature: dict[str, Any], api_timestamp: str | None) -> Station:
        """Convert one GeoJSON feature into a Station dataclass."""
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or [None, None]

        longitude = _coerce_float(coordinates[0]) if len(coordinates) > 0 else None
        latitude = _coerce_float(coordinates[1]) if len(coordinates) > 1 else None

        validated = _coerce_int(props.get("validated"))
        site_status = _coerce_int(props.get("site_status"))
        kid = _coerce_int(props.get("kid"))

        site_status_text = props.get("site_status_text")
        if not site_status_text and site_status is not None:
            site_status_text = SITE_STATUS_LABELS.get(site_status)

        return Station(
            feature_id=str(feature.get("id", "")),
            station_id=str(props.get("id", "")),
            kenn=str(props.get("kenn", "")),
            name=str(props.get("name", "Unbekannt")),
            plz=_coerce_str_or_none(props.get("plz")),
            latitude=latitude,
            longitude=longitude,
            value=_coerce_float(props.get("value")),
            unit=_coerce_str_or_none(props.get("unit")),
            start_measure=_coerce_str_or_none(props.get("start_measure")),
            end_measure=_coerce_str_or_none(props.get("end_measure")),
            validated=validated,
            validated_text=VALIDATED_LABELS.get(validated),
            nuclide=_coerce_str_or_none(props.get("nuclide")),
            duration=_coerce_str_or_none(props.get("duration")),
            site_status=site_status,
            site_status_text=_coerce_str_or_none(site_status_text),
            kid=kid,
            kid_text=KID_LABELS.get(kid),
            height_above_sea=_coerce_float(props.get("height_above_sea")),
            value_cosmic=_coerce_float(props.get("value_cosmic")),
            value_terrestrial=_coerce_float(props.get("value_terrestrial")),
            api_timestamp=api_timestamp,
            layer=LATEST_LAYER,
        )


def distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float | None,
    longitude_2: float | None,
) -> float:
    """Calculate great-circle distance in kilometers."""
    if latitude_2 is None or longitude_2 is None:
        return float("inf")

    earth_radius_km = 6371.0088

    lat1 = radians(latitude_1)
    lon1 = radians(longitude_1)
    lat2 = radians(latitude_2)
    lon2 = radians(longitude_2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(haversine))


def select_nearby_stations(
    stations: list[Station],
    latitude: float,
    longitude: float,
    radius_km: float,
    max_candidates: int,
) -> list[tuple[Station, float]]:
    """Return nearby stations sorted by distance.

    If no stations are within the configured radius, the nearest stations are returned.
    """
    ranked: list[tuple[Station, float]] = []

    for station in stations:
        if station.latitude is None or station.longitude is None:
            continue
        ranked.append((station, distance_km(latitude, longitude, station.latitude, station.longitude)))

    ranked.sort(key=lambda item: (item[1], item[0].name.casefold(), item[0].kenn))

    within_radius = [item for item in ranked if item[1] <= radius_km]
    if within_radius:
        return within_radius[:max_candidates]

    return ranked[:max_candidates]


def _coerce_float(value: Any) -> float | None:
    """Coerce a value to float if possible."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        _LOGGER.debug("Could not coerce %r to float", value)
        return None


def _coerce_int(value: Any) -> int | None:
    """Coerce a value to int if possible."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        _LOGGER.debug("Could not coerce %r to int", value)
        return None


def _coerce_str_or_none(value: Any) -> str | None:
    """Return a stripped string or None."""
    if value in (None, ""):
        return None
    return str(value)


def _extract_service_exception(text: str) -> str | None:
    """Try to extract a readable WFS/OWS service exception."""
    if not text:
        return None

    snippet = text.strip()
    if not snippet.startswith("<"):
        return None

    try:
        root = ET.fromstring(snippet)
    except ET.ParseError:
        return None

    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in {"ServiceException", "ExceptionText", "message"}:
            content = (elem.text or "").strip()
            if content:
                return content

    return None
