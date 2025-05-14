
# Firm Finder

Ein automatisiertes Tool zum Finden von Firmen ohne Website auf Firmenabc.at, mit Fokus auf Coaches, Therapeuten und ähnliche Branchen.

## Beschreibung

Dieses Python-Skript durchsucht die Website Firmenabc.at nach Unternehmen in bestimmten Branchen (Coaching, Therapie, etc.), die keine eigene Website haben. Es identifiziert diese Unternehmen durch das Fehlen eines "W:"-Eintrags in den Kontaktinformationen und speichert relevante Informationen wie Name, Adresse, Telefonnummer und E-Mail-Adresse.

## Funktionen

- Automatische Suche nach vordefinierten Schlüsselwörtern (Coach, Therapeut, etc.)
- Identifizierung von Firmen ohne Website
- Extraktion von Firmeninformationen (Name, Adresse, Telefon, E-Mail, Beschreibung)
- Speicherung der Daten in JSON-Format
- Verfolgung bereits kontaktierter Firmen zur Vermeidung von Duplikaten
- Tägliche automatische Ausführung oder einmalige Ausführung

## Installation

1. Stellen Sie sicher, dass Python 3.6 oder höher installiert ist.

2. Klonen Sie dieses Repository oder laden Sie die Dateien herunter.

3. Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install requests beautifulsoup4 schedule
```

Alternativ können Sie die Abhängigkeiten mit der requirements.txt-Datei installieren:

```bash
pip install -r requirements.txt
```

## Verwendung

### Einmalige Ausführung

Um das Skript einmalig auszuführen und 12 Firmen ohne Website zu finden:

```bash
python firm_finder.py --once
```

### Tägliche automatische Ausführung

Um das Skript im Dauerbetrieb zu starten, der täglich um 8:00 Uhr ausgeführt wird:

```bash
python firm_finder.py
```

Sie können das Skript in einem Terminal-Fenster laufen lassen oder es als Hintergrundprozess starten:

```bash
nohup python firm_finder.py > firm_finder_output.log 2>&1 &
```

### Einrichtung als Cron-Job

Alternativ können Sie einen Cron-Job einrichten, um das Skript täglich auszuführen:

1. Öffnen Sie die Crontab-Datei:

```bash
crontab -e
```

2. Fügen Sie folgende Zeile hinzu, um das Skript täglich um 8:00 Uhr auszuführen (passen Sie den Pfad entsprechend an):

```
0 8 * * * cd /pfad/zum/skript && /usr/bin/python3 firm_finder.py --once >> firm_finder_cron.log 2>&1
```

## Ausgabedateien

Das Skript erstellt folgende Dateien:

- `data/YYYY-MM-DD_firms.json`: Tägliche Ergebnisdatei mit gefundenen Firmen
- `data/contacted.json`: Liste bereits kontaktierter Firmen (zur Vermeidung von Duplikaten)
- `firm_finder.log`: Protokolldatei mit Informationen zur Skriptausführung

### Beispiel für die JSON-Ausgabe

```json
[
  {
    "id": "ABC123",
    "url": "https://www.firmenabc.at/example-company_ABC123",
    "name": "Example Coaching",
    "address": "Musterstraße 123, 1010 Wien",
    "phone": "+43 1 234567890",
    "email": "info@example.com",
    "description": "Coaching für Führungskräfte und Teams",
    "category": "Coaching & Beratung",
    "found_date": "2023-05-14"
  },
  ...
]
```

## Anpassung

Sie können die folgenden Parameter im Skript anpassen:

- `KEYWORDS`: Liste der Suchbegriffe
- `RESULTS_PER_RUN`: Anzahl der zu findenden Firmen pro Durchlauf (Standard: 12)
- Zeitplan für die tägliche Ausführung (in der `main()`-Funktion)

## Fehlerbehebung

- Wenn das Skript keine Ergebnisse liefert, überprüfen Sie die Logdatei `firm_finder.log`.
- Bei Verbindungsproblemen kann es hilfreich sein, die Wartezeiten zwischen den Anfragen zu erhöhen.
- Wenn die Website ihre Struktur ändert, muss möglicherweise die HTML-Parsing-Logik angepasst werden.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.
