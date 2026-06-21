# Teufel Raumfeld

{% if prerelease %}
> **⚠️ Beta-Version** — diese Integration befindet sich in der Alpha-/Beta-Phase. Funktionalität kann sich ändern.
{% endif %}

Home Assistant Integration für **Teufel Smart Speaker** (Raumfeld Multiroom-System). Steuere deine Teufel-Lautsprecher direkt aus Home Assistant — Lautstärke, Wiedergabe, Gruppen und mehr.

Die API-Logik steckt in der Begleit-Bibliothek [hassfeld](https://github.com/B5r1oJ0A9G/hassfeld).

---

## Features

- **Mediensteuerung** — Play, Pause, Stop, Next, Previous, Shuffle, Repeat, Seek
- **Lautstärke** — pro Raum und global, mit konfigurierbaren Schrittweiten
- **Quellenwahl** — Line-In, Spotify, Tidal, Internetradio, Podcasts, lokale Musik
- **Raumgruppen** — Räume zu Gruppen zusammenfassen, per Service steuern
- **Snapshots** — Wiedergabezustand speichern und wiederherstellen
- **Ansagen** — System-Sounds und TTS-Ansagen über den `play_sound`-Service
- **Auto-Discovery** — Räume und Gruppen automatisch erkennen
- **Config-Flow** — Einrichtung direkt über die Home Assistant UI

Unterstützte Plattformen: `media_player`, `sensor`, `select`, `number`

---

## Installation

### HACS (empfohlen)

1. Stelle sicher, dass [HACS](https://hacs.xyz/) installiert ist
2. HACS → Integrationen → Drei-Punkte-Menü → **Benutzerdefinierte Repositories**
3. Füge `https://github.com/B5r1oJ0A9G/teufel_raumfeld` hinzu, Kategorie: **Integration**
4. Suche nach **Teufel Raumfeld** und installiere
5. Starte Home Assistant neu

### Manuell

```bash
cd /config/custom_components
git clone https://github.com/B5r1oJ0A9G/teufel_raumfeld.git teufel_raumfeld
```

Danach Home Assistant neu starten.

---

## Konfiguration

Nach der Installation:

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. **Teufel Raumfeld** auswählen
3. Hostnamen/IP des Raumfeld-Hosts eingeben (Standard-Port: 47365)
4. Die Integration erkennt Räume und Gruppen automatisch

---

## Links

| | |
|---|---|
| Dokumentation | [Wiki](https://github.com/B5r1oJ0A9G/teufel_raumfeld/wiki) |
| Issue-Tracker | [GitHub Issues](https://github.com/B5r1oJ0A9G/teufel_raumfeld/issues) |
| Diskussionen | [GitHub Discussions](https://github.com/B5r1oJ0A9G/teufel_raumfeld/discussions) |
| Quellcode | [GitHub](https://github.com/B5r1oJ0A9G/teufel_raumfeld) |
| hassfeld (API) | [GitHub](https://github.com/B5r1oJ0A9G/hassfeld) |

---

## Lizenz

GNU General Public License v3 (GPLv3)
