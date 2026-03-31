[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?style=flat&logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat&logo=hacs&logoColor=white)](https://hacs.xyz/)
[![Version](https://img.shields.io/github/v/release/Q14siX/bfs_odl?style=flat&color=41BDF5&label=Version)](https://github.com/Q14siX/bfs_odl/releases/latest)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-41BDF5?style=flat)](#)
[![Stars](https://img.shields.io/github/stars/Q14siX/bfs_odl?style=flat&logo=github&color=41BDF5&label=Stars)](https://github.com/Q14siX/bfs_odl/stargazers)
[![Languages](https://img.shields.io/badge/Languages-DE%20%7C%20EN-41BDF5?style=flat&logo=translate&logoColor=white)](#)
[![License](https://img.shields.io/github/license/Q14siX/bfs_odl?style=flat&color=41BDF5&label=License)](https://github.com/Q14siX/bfs_odl/blob/main/LICENSE)
[![Downloads](https://img.shields.io/github/downloads/Q14siX/bfs_odl/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/Q14siX/bfs_odl/releases/latest)
[![Issues](https://img.shields.io/github/issues/Q14siX/bfs_odl?style=flat&color=41BDF5&label=Issues)](https://github.com/Q14siX/bfs_odl/issues)

# BfS ODL

[Jump to English section](#english)

## Deutsch

Diese Home-Assistant-Custom-Integration liest aktuelle Gamma-Ortsdosisleistungswerte (ODL) aus der öffentlichen BfS-ODL-Info-API und lässt den Nutzer während der Einrichtung nahegelegene Messpunkte auswählen.

### Funktionen

- HACS-kompatible Custom Integration
- Einrichtungsassistent mit Messpunkt-Auswahl auf Basis des Home-Assistant-Standorts oder manueller Koordinaten
- Benutzerdefinierbare Schwellen für den Sensor **Messwertbewertung**
- Standardschwellen `0,05 µSv/h` und `0,18 µSv/h`
- Hauptsensor für den aktuellen 1-Stunden-Gamma-ODL-Wert
- Zusätzliche Diagnose-Sensoren für kosmischen und terrestrischen Anteil, Entfernung, Höhe über NN, Prüfstatus, Messstellenstatus, Messnetzknoten, Messstations-ID, Stationscode sowie Messbeginn und Messende
- Deutsche und englische Sprachdateien enthalten
- Zeitstempel aus der API werden als UTC/Zulu behandelt; Home Assistant rechnet die Timestamp-Sensoren für die Anzeige in die Nutzerzeitzone um

### Installation

#### HACS (benutzerdefiniertes Repository)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Q14siX&repository=bfs_odl)

1. Dieses Projekt in ein öffentliches GitHub-Repository legen.
2. In HACS als **Benutzerdefiniertes Repository** vom Typ **Integration** hinzufügen.
3. Repository über HACS installieren.
4. Home Assistant neu starten.
5. **BfS ODL** über **Einstellungen → Geräte & Dienste → Integration hinzufügen** einrichten.

#### Manuelle Installation
1. `custom_components/bfs_odl` in dein Home-Assistant-Konfigurationsverzeichnis kopieren.
2. Optional zusätzlich den gewünschten Blueprint-Unterordner kopieren:
   - `blueprints/automation/bfs_odl/de`
   - `blueprints/automation/bfs_odl/en`
3. Home Assistant neu starten.
4. **BfS ODL** über **Einstellungen → Geräte & Dienste → Integration hinzufügen** einrichten.

### Einrichtungsassistent
Der Einrichtungsassistent hat vier Schritte:
1. Standortquelle, Suchradius, Anzahl vorgeschlagener Messpunkte und Aktualisierungsintervall festlegen.
2. Falls manuelle Position gewählt wurde: manuelle Koordinaten eingeben.
3. Einen oder mehrere nahegelegene Messpunkte auswählen.
4. Die untere und obere Schwelle für den Sensor **Messwertbewertung** festlegen.

#### Standardschwellen
- Untere Schwelle: **0,05 µSv/h**
- Obere Schwelle: **0,18 µSv/h**

Wenn diese Standardwerte verwendet werden, nutzt der Bewertungssensor die Formulierung **natürlicher Bereich**:
- `below_natural_range` → **Unter natürlichem Bereich**
- `within_natural_range` → **Im natürlichen Bereich**
- `above_natural_range` → **Über natürlichem Bereich**

Wenn mindestens eine Schwelle geändert wird, nutzt der Bewertungssensor die Formulierung **konfigurierter Bereich**:
- `below_configured_range` → **Unter konfiguriertem Bereich**
- `within_configured_range` → **Im konfigurierten Bereich**
- `above_configured_range` → **Über konfiguriertem Bereich**

Zusätzlicher Zustand:
- `no_data` → **Keine Daten**

### Sensoren

#### Hauptsensor
- **Gamma-ODL (1h)**

#### Bewertungssensor
- **Messwertbewertung**

Die Messwertbewertung ist eine Einordnungshilfe und kein rechtlicher Strahlenschutz-Grenzwertalarm.

Wenn die Standardschwellen verwendet werden:
- **Unter natürlichem Bereich**: Wert `< 0,05 µSv/h`
- **Im natürlichen Bereich**: Wert `0,05 µSv/h` bis `0,18 µSv/h`
- **Über natürlichem Bereich**: Wert `> 0,18 µSv/h`

Wenn benutzerdefinierte Schwellen verwendet werden:
- **Unter konfiguriertem Bereich**: Wert `< untere Schwelle`
- **Im konfigurierten Bereich**: `untere Schwelle <= Wert <= obere Schwelle`
- **Über konfiguriertem Bereich**: Wert `> obere Schwelle`

Wenn kein gültiger aktueller Wert vorhanden ist:
- **Keine Daten**

#### Diagnose-Sensoren
- **Gamma-ODL kosmisch (1h)**
- **Gamma-ODL terrestrisch (1h)**
- **Entfernung**
- **Höhe über NN**
- **Messstations-ID**
- **Stationscode**
- **Prüfstatus**
- **Messstellenstatus**
- **Messnetzknoten**
- **Messbeginn**
- **Messende**

### Attribute des Hauptsensors
Der Hauptsensor `Gamma-ODL (1h)` stellt eine bereinigte Attributliste ohne Dubletten bereit:
- `station_code`
- `station_id`
- `feature_id`
- `postal_code`
- `station_name`
- `coordinates`
- `distance_km`
- `measurement_start`
- `measurement_end`
- `measurement_start_utc`
- `measurement_end_utc`
- `api_timestamp`
- `api_timestamp_utc`
- `duration`
- `quantity`
- `validation_code`
- `validation_status`
- `site_status_code`
- `site_status`
- `network_node_id`
- `network_node`
- `height_above_sea_m`
- `cosmic_value_uSv_h`
- `terrestrial_value_uSv_h`
- `cosmic_share_percent`
- `terrestrial_share_percent`
- `assessment_state`
- `assessment_threshold_low_uSv_h`
- `assessment_threshold_high_uSv_h`
- `assessment_uses_default_thresholds`
- `assessment_model`
- `api_timezone`
- `local_timezone`

### Zeitbehandlung
Die API dokumentiert `start_measure`, `end_measure` und `timeStamp` als ISO-Datetimes mit `Z`. Diese Integration behandelt die Zeitangaben der API deshalb als UTC.

Die Integration:
- hält die Timestamp-Sensoren timezone-aware in UTC
- stellt `Messbeginn` und `Messende` als Timestamp-Sensoren bereit, die Home Assistant in der Oberfläche in die Nutzerzeitzone umrechnet
- ergänzt am Hauptsensor sowohl lokale Zeit (`measurement_start`, `measurement_end`, `api_timestamp`) als auch die ursprünglichen UTC-Zeitpunkte (`*_utc`)

### Blueprints

Die Blueprints liegen in zwei getrennten Sprachversionen vor:

#### Deutsche Blueprints
- `blueprints/automation/bfs_odl/de/reference_range_notification.yaml`
- `blueprints/automation/bfs_odl/de/sudden_change_notification.yaml`
- `blueprints/automation/bfs_odl/de/data_unavailable_notification.yaml`

#### Englische Blueprints
- `blueprints/automation/bfs_odl/en/reference_range_notification.yaml`
- `blueprints/automation/bfs_odl/en/sudden_change_notification.yaml`
- `blueprints/automation/bfs_odl/en/data_unavailable_notification.yaml`

Die Blueprints werden von Home Assistant nicht automatisch beim Installieren der Integration importiert.

#### Deutsche Blueprints über die RAW-Datei von GitHub importieren
Für weniger versierte Nutzer ist das der einfachste Weg:

1. In Home Assistant zu **Einstellungen → Automatisierungen & Szenen → Blueprints** gehen.
2. Unten rechts auf **Blueprint importieren** klicken.
3. Den passenden **RAW-Link** des gewünschten deutschen Blueprints in das Eingabefeld einfügen.
4. Den Import bestätigen.
5. Danach den Blueprint öffnen und daraus eine Automation erstellen.

Direkte RAW-Links der deutschen Blueprints:

- Referenzbereich-Benachrichtigung:  
  `https://raw.githubusercontent.com/Q14siX/bfs_odl/main/blueprints/automation/bfs_odl/de/reference_range_notification.yaml`  
  [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fbfs_odl%2Fmain%2Fblueprints%2Fautomation%2Fbfs_odl%2Fde%2Freference_range_notification.yaml)

- Sprunghafte Änderung:  
  `https://raw.githubusercontent.com/Q14siX/bfs_odl/main/blueprints/automation/bfs_odl/de/sudden_change_notification.yaml`  
  [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fbfs_odl%2Fmain%2Fblueprints%2Fautomation%2Fbfs_odl%2Fde%2Fsudden_change_notification.yaml)

- Daten nicht verfügbar:  
  `https://raw.githubusercontent.com/Q14siX/bfs_odl/main/blueprints/automation/bfs_odl/de/data_unavailable_notification.yaml`  
  [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fbfs_odl%2Fmain%2Fblueprints%2Fautomation%2Fbfs_odl%2Fde%2Fdata_unavailable_notification.yaml)

#### Deutsche Blueprints manuell kopieren
Alternativ können die deutschen YAML-Dateien direkt nach folgendem Ordner kopiert werden:

`<config>/blueprints/automation/bfs_odl/de/`

Danach Home Assistant neu laden oder neu starten.

#### Hinweis zur Zustandsauswahl im Referenzbereich-Blueprint
Der deutsche Referenzbereich-Blueprint zeigt lesbare deutsche Auswahltexte an. Intern arbeitet er weiterhin mit den Rohzuständen des Bewertungssensors.

- Solange die Standardschwellen aktiv sind, werden intern die Zustände `*_natural_range` verwendet.
- Bei benutzerdefinierten Schwellen werden intern die Zustände `*_configured_range` verwendet.

### Bestehende Installation aktualisieren
1. Den Ordner `custom_components/bfs_odl` ersetzen.
2. Falls du auch die neuesten Blueprint-Versionen möchtest, zusätzlich `blueprints/automation/bfs_odl/de` und/oder `blueprints/automation/bfs_odl/en` ersetzen.
3. Home Assistant vollständig neu starten.
4. Falls gewünscht, anschließend in den Integrationsoptionen die Schwellen anpassen.
5. Falls Home Assistant noch eine verwaiste Alt-Entität aus einem früheren fehlerhaften Build anzeigt, diesen veralteten Eintrag einmalig löschen und die Integration neu laden.

### Fehlerbehebung

**API konnte nicht erreicht werden**
- Prüfe, ob Home Assistant ausgehenden HTTPS-Zugriff hat.
- Starte Home Assistant nach dem Dateiaustausch neu.
- Öffne den Einrichtungsassistenten erneut, wenn du den Integrationsordner manuell ersetzt hast.

**Unbekannter Fehler bei manuellen Koordinaten**
- Verwende numerische Werte für Breiten- und Längengrad.
- Breitengrad muss zwischen `-90` und `90` liegen.
- Längengrad muss zwischen `-180` und `180` liegen.

**Bewertungssensor nicht sichtbar**
- Starte Home Assistant nach dem Update neu.
- Suche nach der Entität `measurement_assessment` oder `Messwertbewertung`.
- Lösche alte verwaiste Entitäten nur dann, wenn Home Assistant sie ausdrücklich als nicht mehr bereitgestellt kennzeichnet.

**Zustände wirken nach Änderung der Schwellen falsch**
- Öffne die Integrationsoptionen und prüfe die konfigurierte untere und obere Schwelle.
- Wenn die Schwellen exakt den Standardwerten entsprechen, verwendet der Sensor die Formulierungen zum natürlichen Bereich.
- Wenn die Schwellen von den Standardwerten abweichen, verwendet der Sensor die Formulierungen zum konfigurierten Bereich.

<a id="english"></a>

## English

This Home Assistant custom integration reads current gamma ambient dose rate (ODL) values from the public BfS ODL-Info API and lets the user select nearby measurement points during setup.

### Features

- HACS-compatible custom integration
- Setup flow with station selection based on the Home Assistant location or manual coordinates
- User-configurable thresholds for the **Measurement assessment** sensor
- Default thresholds `0.05 µSv/h` and `0.18 µSv/h`
- Main sensor for the current 1-hour gamma ODL value
- Additional diagnostic sensors for cosmic and terrestrial share, distance, elevation, validation status, station status, network node, measurement station ID, station code, measurement start, and measurement end
- German and English translation files included
- API timestamps are treated as UTC/Zulu; Home Assistant renders timestamp sensors in the user timezone

### Installation

#### HACS (custom repository)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Q14siX&repository=bfs_odl)

1. Put this project into a public GitHub repository.
2. In HACS, add it as a **Custom repository** of type **Integration**.
3. Install the repository via HACS.
4. Restart Home Assistant.
5. Add **BfS ODL** via **Settings → Devices & services → Add integration**.

#### Manual installation
1. Copy `custom_components/bfs_odl` into your Home Assistant configuration directory.
2. Optionally also copy the blueprint language folder you want:
   - `blueprints/automation/bfs_odl/de`
   - `blueprints/automation/bfs_odl/en`
3. Restart Home Assistant.
4. Add **BfS ODL** via **Settings → Devices & services → Add integration**.

### Setup wizard
The setup wizard has four steps:
1. Choose the location source, search radius, number of suggested stations, and update interval.
2. Enter manual coordinates if manual position was selected.
3. Select one or more nearby measurement points.
4. Set the lower and upper thresholds for the **Measurement assessment** sensor.

#### Default thresholds
- Lower threshold: **0.05 µSv/h**
- Upper threshold: **0.18 µSv/h**

If these default values are used, the assessment sensor uses **natural range** wording:
- `below_natural_range` → **Below natural range**
- `within_natural_range` → **Within natural range**
- `above_natural_range` → **Above natural range**

If at least one threshold is changed, the assessment sensor uses **configured range** wording:
- `below_configured_range` → **Below configured range**
- `within_configured_range` → **Within configured range**
- `above_configured_range` → **Above configured range**

Additional state:
- `no_data` → **No data**

### Sensors

#### Main sensor
- **Gamma ODL (1h)**

#### Assessment sensor
- **Measurement assessment**

The measurement assessment is a classification helper and not a legal radiation alarm.

If the default thresholds are used:
- **Below natural range**: value `< 0.05 µSv/h`
- **Within natural range**: value `0.05 µSv/h` to `0.18 µSv/h`
- **Above natural range**: value `> 0.18 µSv/h`

If custom thresholds are used:
- **Below configured range**: value `< lower threshold`
- **Within configured range**: `lower threshold <= value <= upper threshold`
- **Above configured range**: value `> upper threshold`

If no valid current value is available:
- **No data**

#### Diagnostic sensors
- **Gamma ODL cosmic (1h)**
- **Gamma ODL terrestrial (1h)**
- **Distance**
- **Height above sea level**
- **Measurement station ID**
- **Station code**
- **Validation status**
- **Measurement point status**
- **Network node**
- **Measurement start**
- **Measurement end**

### Main sensor attributes
The main `Gamma ODL (1h)` sensor exposes a cleaned-up attribute set without duplicates:
- `station_code`
- `station_id`
- `feature_id`
- `postal_code`
- `station_name`
- `coordinates`
- `distance_km`
- `measurement_start`
- `measurement_end`
- `measurement_start_utc`
- `measurement_end_utc`
- `api_timestamp`
- `api_timestamp_utc`
- `duration`
- `quantity`
- `validation_code`
- `validation_status`
- `site_status_code`
- `site_status`
- `network_node_id`
- `network_node`
- `height_above_sea_m`
- `cosmic_value_uSv_h`
- `terrestrial_value_uSv_h`
- `cosmic_share_percent`
- `terrestrial_share_percent`
- `assessment_state`
- `assessment_threshold_low_uSv_h`
- `assessment_threshold_high_uSv_h`
- `assessment_uses_default_thresholds`
- `assessment_model`
- `api_timezone`
- `local_timezone`

### Time handling
The API documents `start_measure`, `end_measure`, and `timeStamp` as ISO datetimes with `Z`. This integration therefore treats upstream timestamps as UTC.

The integration:
- keeps timestamp sensors timezone-aware in UTC
- exposes `Measurement start` and `Measurement end` as timestamp sensors that Home Assistant renders in the user timezone
- adds both local time (`measurement_start`, `measurement_end`, `api_timestamp`) and the original UTC instants (`*_utc`) to the main sensor

### Blueprints

Blueprints are available in two separate language sets:

#### German blueprints
- `blueprints/automation/bfs_odl/de/reference_range_notification.yaml`
- `blueprints/automation/bfs_odl/de/sudden_change_notification.yaml`
- `blueprints/automation/bfs_odl/de/data_unavailable_notification.yaml`

#### English blueprints
- `blueprints/automation/bfs_odl/en/reference_range_notification.yaml`
- `blueprints/automation/bfs_odl/en/sudden_change_notification.yaml`
- `blueprints/automation/bfs_odl/en/data_unavailable_notification.yaml`

Blueprints are not imported automatically when the integration is installed.

#### Import English blueprints using the GitHub RAW file
For less technical users this is usually the easiest method:

1. In Home Assistant open **Settings → Automations & Scenes → Blueprints**.
2. Click **Import Blueprint** in the lower right corner.
3. Paste the matching **RAW link** of the English blueprint you want to import.
4. Confirm the import.
5. Open the imported blueprint and create an automation from it.

Direct RAW links for the English blueprints:

- Reference range notification:  
  `https://raw.githubusercontent.com/Q14siX/bfs_odl/main/blueprints/automation/bfs_odl/en/reference_range_notification.yaml`  
  [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fbfs_odl%2Fmain%2Fblueprints%2Fautomation%2Fbfs_odl%2Fen%2Freference_range_notification.yaml)

- Sudden change:  
  `https://raw.githubusercontent.com/Q14siX/bfs_odl/main/blueprints/automation/bfs_odl/en/sudden_change_notification.yaml`  
  [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fbfs_odl%2Fmain%2Fblueprints%2Fautomation%2Fbfs_odl%2Fen%2Fsudden_change_notification.yaml)

- Data unavailable:  
  `https://raw.githubusercontent.com/Q14siX/bfs_odl/main/blueprints/automation/bfs_odl/en/data_unavailable_notification.yaml`  
  [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FQ14siX%2Fbfs_odl%2Fmain%2Fblueprints%2Fautomation%2Fbfs_odl%2Fen%2Fdata_unavailable_notification.yaml)

#### Copy English blueprints manually
Alternatively, copy the English YAML files directly into:

`<config>/blueprints/automation/bfs_odl/en/`

Then reload Home Assistant or restart it.

#### Note about state selection in the reference-range blueprint
The English reference-range blueprint shows readable English labels in the selection field. Internally it still works with the raw states of the assessment sensor.

- While the default thresholds are active it internally uses the `*_natural_range` states.
- With custom thresholds it internally uses the `*_configured_range` states.

### Updating an existing installation
1. Replace the `custom_components/bfs_odl` folder.
2. If you also want the latest blueprint versions, also replace `blueprints/automation/bfs_odl/de` and/or `blueprints/automation/bfs_odl/en`.
3. Restart Home Assistant completely.
4. Open the integration options if you want to change thresholds later.
5. If Home Assistant still shows an old orphaned entity from an earlier broken build, remove that stale entity once and reload the integration.

### Troubleshooting

**API could not be reached**
- Verify outbound HTTPS access from Home Assistant.
- Restart Home Assistant after replacing files.
- Re-open the setup flow if you changed the integration folder manually.

**Unknown error during manual coordinates**
- Use numeric latitude/longitude values.
- Latitude must be between `-90` and `90`.
- Longitude must be between `-180` and `180`.

**Assessment sensor not visible**
- Restart Home Assistant after updating the integration.
- Search for the entity by `measurement_assessment` or “Measurement assessment”.
- Remove stale old entities only if they are explicitly shown as no longer provided.

**States look wrong after changing thresholds**
- Open the integration options and verify the configured lower and upper thresholds.
- If thresholds match the defaults exactly, the sensor uses the natural-range wording.
- If thresholds differ from the defaults, it uses the configured-range wording.
