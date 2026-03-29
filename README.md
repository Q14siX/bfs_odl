# BfS ODL für Home Assistant

HACS-fähige Custom Integration für die ODL-Info-Daten (Ortsdosisleistung) des Bundesamts für Strahlenschutz.

## Funktionen

- Auswahl nahegelegener Messpunkte direkt während der Einrichtung
- Standort über Home-Assistant-Position oder manuelle Koordinaten
- Hauptsensor pro Messstelle für den aktuellen 1h-Gamma-ODL-Wert
- zusätzliche Diagnose-Sensoren pro Messstelle
- erweiterte Attribute am Hauptsensor, unter anderem:
  - Messstellen-ID
  - Feature-ID
  - Koordinaten
  - Messbeginn / Messende
  - Messdauer
  - Prüfstatus
  - Messstellenstatus
  - Messnetzknoten
  - Höhe über NN
  - kosmischer und terrestrischer Anteil
  - API-Zeitstempel

## Installation

### Installation über HACS

Diese Integration kann über **HACS** installiert werden.

#### Variante 1: Über HACS als benutzerdefiniertes Repository

Sobald sich dieses Projekt in einem **öffentlichen GitHub-Repository** befindet, kann es direkt in HACS eingebunden werden:

1. **HACS** öffnen
2. oben rechts auf die **drei Punkte** klicken
3. **Benutzerdefinierte Repositories** wählen
4. die URL des GitHub-Repositories eintragen
5. als Kategorie **Integration** auswählen
6. Repository hinzufügen
7. nach **BfS ODL** suchen und installieren
8. Home Assistant neu starten

#### Variante 2: Direkt über den HACS-Store

Wenn das Repository später offiziell im HACS-Standardkatalog gelistet ist, reicht:

1. **HACS → Integrationen** öffnen
2. nach **BfS ODL** suchen
3. Integration installieren
4. Home Assistant neu starten

> Hinweis: Die direkte Suche im normalen HACS-Store funktioniert erst dann, wenn das Repository offiziell im HACS-Katalog aufgenommen wurde. Ohne diese Aufnahme funktioniert die Installation weiterhin über **Benutzerdefinierte Repositories**.

### Manuelle Installation

1. den Ordner `custom_components/bfs_odl` in deine Home-Assistant-Installation kopieren
2. Home Assistant neu starten
3. unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **BfS ODL** suchen

## Einrichtung

1. Integration hinzufügen
2. Standortquelle wählen:
   - **Home-Assistant-Standort verwenden** oder
   - **manuelle Koordinaten** eingeben
3. Suchradius festlegen
4. gewünschte Messpunkte auswählen
5. Einrichtung abschließen

## Diagnose-Sensoren

Je Messstelle werden zusätzliche Diagnose-Entitäten angelegt, zum Beispiel:

- kosmischer Anteil
- terrestrischer Anteil
- Entfernung
- Höhe über NN
- Prüfstatus
- Messstellenstatus
- Messnetzknoten
- Messbeginn
- Messende

Ob diese standardmäßig aktiviert sind, hängt von der Implementierung in `sensor.py` ab.

## Datenquelle

- BfS ODL-Info / Datenschnittstelle
- WFS Layer: `opendata:odlinfo_odl_1h_latest`
