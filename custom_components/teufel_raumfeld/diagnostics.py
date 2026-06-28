"""Diagnostics support for Teufel Raumfeld integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import HassRaumfeldHost

TO_REDACT = {"host", "port"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    raumfeld: HassRaumfeldHost = entry.runtime_data

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "host": {
            "valid": await raumfeld.async_host_is_valid(),
        },
        "zones": raumfeld.get_zones() if hasattr(raumfeld, "get_zones") else None,
        "rooms": raumfeld.get_rooms() if hasattr(raumfeld, "get_rooms") else None,
        "devices": raumfeld.get_raumfeld_device_udns() if hasattr(raumfeld, "get_raumfeld_device_udns") else None,
        "options": raumfeld.options if hasattr(raumfeld, "options") else None,
    }
