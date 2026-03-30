"""Constants for the BfS ODL integration."""

from __future__ import annotations

DOMAIN = "bfs_odl"

ATTR_DISTANCE_KM = "distance_km"
ATTR_KID_TEXT = "network_node"
ATTR_SITE_STATUS_TEXT = "site_status"
ATTR_VALIDATED_TEXT = "validation_status"

CONF_LATITUDE = "latitude"
CONF_LOCATION_SOURCE = "location_source"
CONF_LONGITUDE = "longitude"
CONF_MAX_CANDIDATES = "max_candidates"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
CONF_SEARCH_RADIUS_KM = "search_radius_km"
CONF_SELECTED_STATIONS = "selected_stations"
CONF_STATION_DETAILS = "station_details"
CONF_THRESHOLD_LOW = "threshold_low"
CONF_THRESHOLD_HIGH = "threshold_high"

DEFAULT_MAX_CANDIDATES = 20
DEFAULT_SCAN_INTERVAL_MINUTES = 30
DEFAULT_SEARCH_RADIUS_KM = 75
DEFAULT_STATION_COUNT = 3
DEFAULT_THRESHOLD_LOW_USV_H = 0.05
DEFAULT_THRESHOLD_HIGH_USV_H = 0.18

LOCATION_SOURCE_HOME = "home"
LOCATION_SOURCE_MANUAL = "manual"

LATEST_LAYER = "opendata:odlinfo_odl_1h_latest"
HISTORY_LAYER_1H = "opendata:odlinfo_timeseries_odl_1h"
HISTORY_LAYER_24H = "opendata:odlinfo_timeseries_odl_24h"

API_BASE_URLS = [
    "https://www.imis.bfs.de/ogc/opendata/ows",
    "https://www.imis.bfs.de/geoserver-public/opendata/wfs",
]
API_TIMEOUT_SECONDS = 30
API_VERSION = "1.1.0"

KID_LABELS: dict[int, str] = {
    1: "Freiburg",
    2: "Berlin",
    3: "München",
    4: "Bonn",
    5: "Salzgitter",
    6: "Rendsburg",
}

SITE_STATUS_LABELS: dict[int, str] = {
    1: "in Betrieb",
    2: "defekt",
    3: "Testbetrieb",
}

VALIDATED_LABELS: dict[int, str] = {
    1: "geprüft",
    2: "ungeprüft",
}

VALIDATED_STATES: dict[int, str] = {
    1: "validated",
    2: "unvalidated",
}

SITE_STATUS_STATES: dict[int, str] = {
    1: "in_operation",
    2: "defective",
    3: "test_operation",
}

KID_STATES: dict[int, str] = {
    1: "freiburg",
    2: "berlin",
    3: "munich",
    4: "bonn",
    5: "salzgitter",
    6: "rendsburg",
}

MEASUREMENT_ASSESSMENT_NO_DATA = "no_data"
MEASUREMENT_ASSESSMENT_BELOW_NATURAL = "below_natural_range"
MEASUREMENT_ASSESSMENT_WITHIN_NATURAL = "within_natural_range"
MEASUREMENT_ASSESSMENT_ABOVE_NATURAL = "above_natural_range"
MEASUREMENT_ASSESSMENT_BELOW_CONFIGURED = "below_configured_range"
MEASUREMENT_ASSESSMENT_WITHIN_CONFIGURED = "within_configured_range"
MEASUREMENT_ASSESSMENT_ABOVE_CONFIGURED = "above_configured_range"

MANUFACTURER = "Bundesamt für Strahlenschutz"
MODEL = "ODL-Messstelle"
INTEGRATION_NAME = "BfS ODL"
