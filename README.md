# Teufel Raumfeld

[![GitHub Downloads](https://img.shields.io/github/downloads/B5r1oJ0A9G/teufel_raumfeld/latest/total)](https://github.com/B5r1oJ0A9G/teufel_raumfeld/releases/)
[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![hassfest](https://github.com/B5r1oJ0A9G/teufel_raumfeld/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/B5r1oJ0A9G/teufel_raumfeld/actions/workflows/hassfest.yaml)
[![CodeQL](https://github.com/B5r1oJ0A9G/teufel_raumfeld/actions/workflows/github-code-scanning/codeql/badge.svg?branch=master)](https://github.com/B5r1oJ0A9G/teufel_raumfeld/actions/workflows/github-code-scanning/codeql)

Home Assistant integration for **Teufel Smart Speakers** (Raumfeld multiroom system). Control your Teufel speakers directly from Home Assistant — volume, playback, groups, and more.

The API logic lives in the companion library [hassfeld](https://github.com/B5r1oJ0A9G/hassfeld).

---

## Features

- **Media control** — Play, Pause, Stop, Next, Previous, Shuffle, Repeat, Seek
- **Volume** — per-room and global, with configurable step sizes
- **Source selection** — Line-In, Spotify, Tidal, Internet radio, Podcasts, local music
- **Room groups** — Combine rooms into groups, control via services
- **Snapshots** — Save and restore playback state
- **Announcements** — System sounds and TTS announcements via the `play_sound` service
- **Auto-discovery** — Rooms and groups detected automatically
- **Config-Flow** — Set up directly through the Home Assistant UI

Supported platforms: `media_player`, `sensor`, `select`, `number`

---

## Installation

### HACS (recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed
2. HACS → Integrations → Three-dot menu → **Custom repositories**
3. Add `https://github.com/B5r1oJ0A9G/teufel_raumfeld`, category: **Integration**
4. Search for **Teufel Raumfeld** and install
5. Restart Home Assistant

### Manual

```bash
cd /config/custom_components
git clone https://github.com/B5r1oJ0A9G/teufel_raumfeld.git teufel_raumfeld
```

Then restart Home Assistant.

---

## Configuration

After installation:

1. **Settings → Devices & Services → Add Integration**
2. Select **Teufel Raumfeld**
3. Enter the hostname/IP of your Raumfeld host (default port: 47365)
4. The integration auto-discovers rooms and groups

---

## Links

| | |
|---|---|
| Documentation | [Wiki](https://github.com/B5r1oJ0A9G/teufel_raumfeld/wiki) |
| Issue tracker | [GitHub Issues](https://github.com/B5r1oJ0A9G/teufel_raumfeld/issues) |
| Discussions | [GitHub Discussions](https://github.com/B5r1oJ0A9G/teufel_raumfeld/discussions) |
| Source code | [GitHub](https://github.com/B5r1oJ0A9G/teufel_raumfeld) |
| hassfeld (API) | [GitHub](https://github.com/B5r1oJ0A9G/hassfeld) |

---

## License

GNU General Public License v3 (GPLv3)
