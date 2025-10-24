# Musik-Snip - System Audio Recorder

Eine Python-basierte GUI-Anwendung zum Aufnehmen von System-Audio mit Timer-Funktion und automatischer MP3-Konvertierung.

## Features

- **Modernes GUI-Design**: Basiert auf ttkbootstrap mit professionellem "darkly" Theme
- **System-Audio-Aufnahme**: Nimm Audioausgaben deines Systems auf (z.B. Musik, Streams, etc.)
- **Präziser Timer**: Stelle Timer in Minuten UND Sekunden ein
- **Timer-Countdown**: Sieh in Echtzeit, wie viel Zeit noch verbleibt
- **Timer-Endzeit**: Zeigt die Uhrzeit an, wann die Aufnahme endet
- **Pause/Resume**: Aufnahmen können pausiert und fortgesetzt werden
- **Audio-Device-Auswahl**: Wähle das gewünschte Aufnahmegerät aus
- **MP3-Konvertierung**: Automatische Konvertierung zu MP3 mit wählbarer Qualität (128-320 kbps mit Bitrate-Anzeige)
- **Audio-Pegel-Anzeige**: Echtzeit-Visualisierung des Aufnahmepegels mit Progressbar
- **Speicherort-Auswahl**: Wähle, wo deine Aufnahmen gespeichert werden sollen
- **Error Handling**: Robuste Fehlerbehandlung mit aussagekräftigen Meldungen
- **Logging**: Detailliertes Logging für Debugging

## Voraussetzungen

- Python 3.7 oder höher
- Tkinter (normalerweise in Python enthalten)
- Windows, macOS oder Linux

## Installation

### 1. Repository klonen oder herunterladen

```bash
git clone https://github.com/huibuh123123/Musik-Snip.git
cd Musik-Snip
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

**Benötigte Pakete:**
- `sounddevice` - Audio-Aufnahme
- `soundfile` - WAV-Datei-Handling
- `numpy` - Audio-Datenverarbeitung
- `lameenc` - MP3-Encoding
- `ttkbootstrap` - Modernes GUI-Framework

### 3. Anwendung starten

```bash
python main.py
```

## Verwendung

### Grundlegende Bedienung

1. **Audio-Gerät wählen**: Wähle das Aufnahmegerät aus der Dropdown-Liste
   - "Standard (System Default)" verwendet das System-Standardgerät
   - Andere Geräte werden mit Name und ID angezeigt

2. **Einstellungen konfigurieren**:
   - **Timer**: Stelle Minuten UND Sekunden genau ein
   - **Timer aktivieren**: Toggle-Button aktivieren, damit Timer verwendet wird
   - **Timer-Endzeit**: Nach Aktivierung siehst du die Uhrzeit, wann die Aufnahme endet (z.B. "Timer endet um: 14:35:30")
   - **MP3-Qualität**: Wähle zwischen Low (128 kbps), Medium (192 kbps), High (256 kbps), Very High (320 kbps) - Bitrate wird direkt angezeigt
   - **Speicherort**: Klicke auf "Ändern" um einen anderen Ordner zu wählen

3. **Aufnahme starten**: Klicke auf "Start"
   - Der Status wechselt zu "🔴 Nehme auf..."
   - Die Laufzeit wird angezeigt (z.B. "Laufzeit: 02:35")
   - Bei aktivem Timer siehst du einen Countdown (z.B. "⏱️ Verbleibend: 02:25")
   - Der Audio-Pegel wird in Echtzeit mit einer Progressbar visualisiert

4. **Aufnahme pausieren** (optional): Klicke auf "Pause"
   - Die Aufnahme wird pausiert
   - Klicke auf "Fortsetzen" um weiterzumachen

5. **Aufnahme stoppen**: Klicke auf "Stop"
   - Die Aufnahme wird gestoppt
   - WAV wird automatisch zu MP3 konvertiert
   - Erfolgreiche Speicherung wird angezeigt

### Ausgabedateien

- Dateien werden im gewählten Speicherort gespeichert
- Standard-Ordner: `aufnahmen/`
- Dateiname-Format: `aufnahme_YYYY-MM-DD_HH-MM-SS.mp3`
- Temporäre WAV-Dateien werden automatisch gelöscht

## Projektstruktur

```
Musik-Snip/
├── main.py           # Hauptprogramm und Entry Point
├── gui.py            # GUI-Implementation
├── recorder.py       # Audio-Aufnahme-Logik
├── encoder.py        # MP3-Encoding-Logik
├── config.py         # Konfiguration und Konstanten
├── requirements.txt  # Python-Dependencies
├── README.md         # Diese Datei
├── .gitignore        # Git-Ignore-Regeln
└── aufnahmen/        # Standard-Ausgabeordner (wird automatisch erstellt)
```

## Konfiguration

Die Datei `config.py` enthält alle Konfigurationsparameter:

### Audio-Einstellungen
- `SAMPLE_RATE`: 44100 Hz (CD-Qualität)
- `CHANNELS`: 2 (Stereo)
- `BUFFER_SIZE`: 1024 Samples

### MP3-Einstellungen
- `DEFAULT_MP3_BITRATE`: 192 kbps
- `MP3_QUALITY`: 2 (LAME-Qualität, 0=best, 9=worst)

### GUI-Einstellungen
- Theme: darkly (ttkbootstrap)
- Fenstergröße: 600x550 Pixel
- Modernes Design mit Bootstrap-Farben
- Timer-Intervalle

## Troubleshooting

### Problem: Keine Audio-Geräte gefunden
**Lösung**: Stelle sicher, dass dein System ein Aufnahmegerät hat. Bei System-Audio unter Windows benötigst du möglicherweise "Stereo Mix" oder eine virtuelle Audio-Cable.

### Problem: "Module not found" Fehler
**Lösung**: Installiere alle Dependencies mit `pip install -r requirements.txt`

### Problem: Aufnahme ist leer oder hat keinen Ton
**Lösung**:
- Prüfe, ob das richtige Audio-Gerät ausgewählt ist
- Stelle sicher, dass Audio abgespielt wird während der Aufnahme
- Prüfe die System-Audio-Einstellungen

### Problem: MP3-Encoding schlägt fehl
**Lösung**:
- Stelle sicher, dass `lameenc` korrekt installiert ist
- Bei Windows: Möglicherweise werden zusätzliche DLLs benötigt
- Prüfe die Log-Datei `audio_recorder.log` für Details

### Problem: Hohe CPU-Auslastung
**Lösung**: Reduziere die MP3-Qualität oder verwende einen größeren BUFFER_SIZE in config.py

## Logging

Die Anwendung erstellt automatisch eine Log-Datei `audio_recorder.log` mit detaillierten Informationen über:
- Programmstart und -ende
- Audio-Device-Erkennung
- Aufnahme-Start/-Stop
- Fehler und Warnungen
- Datei-Operationen

## Bekannte Einschränkungen

- Unter macOS und Linux kann die Audio-Device-Auswahl eingeschränkt sein
- System-Audio-Aufnahme erfordert spezielle Konfiguration je nach Betriebssystem
- Sehr lange Aufnahmen (>1 Stunde) können viel RAM verbrauchen

## Lizenz

MIT License - Frei verwendbar für private und kommerzielle Zwecke

## Credits

Entwickelt mit [Claude Code](https://claude.com/claude-code)

## Support

Bei Problemen oder Fragen:
1. Prüfe die Log-Datei `audio_recorder.log`
2. Erstelle ein Issue auf GitHub
3. Stelle sicher, dass alle Dependencies installiert sind

## Changelog

### Version 2.5 (Aktuell) - Modern UI Update
- **NEU**: Modernes GUI-Design mit ttkbootstrap (darkly Theme)
- **NEU**: Timer mit Minuten UND Sekunden Eingabe
- **NEU**: Live-Countdown während Aufnahme (zeigt verbleibende Zeit)
- **NEU**: Timer-Endzeit-Anzeige (zeigt Uhrzeit wann Timer endet)
- **NEU**: MP3-Qualität mit Bitrate-Anzeige (z.B. "Medium (192 kbps)")
- **Verbessert**: Audio-Pegel mit moderner Progressbar
- **Verbessert**: Status-Anzeige mit Emojis und Farben
- **Verbessert**: Toggle-Button für Timer-Aktivierung
- **Verbessert**: Responsive UI mit besseren Abständen

### Version 2.0
- Komplette Refaktorierung in modulare Struktur
- Hinzugefügt: Audio-Device-Auswahl
- Hinzugefügt: Pause/Resume-Funktion
- Hinzugefügt: Audio-Pegel-Anzeige
- Hinzugefügt: Speicherort-Auswahl
- Hinzugefügt: MP3-Qualitäts-Auswahl
- Hinzugefügt: Robustes Error Handling
- Hinzugefügt: Umfassendes Logging
- Hinzugefügt: Dependency-Check beim Start
- Verbessert: Thread-safe UI-Updates
- Verbessert: Memory Management
- Verbessert: Code-Dokumentation

### Version 1.0
- Grundlegende Audio-Aufnahme
- Timer-Funktion
- MP3-Konvertierung
