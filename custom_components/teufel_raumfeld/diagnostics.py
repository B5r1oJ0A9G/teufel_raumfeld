"""Diagnostics support for Teufel Raumfeld integration."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT = {"host", "port"}


def _redact_dict(data: dict, keys: set) -> dict:
    """Return a copy of data with the given keys replaced by '**REDACTED**'."""
    return {k: "**REDACTED**" if k in keys else v for k, v in data.items()}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    raumfeld = entry.runtime_data

    # Safely collect host validity — may fail if host is unreachable
    host_valid: bool | str = "unknown"
    try:
        host_valid = await raumfeld.async_host_is_valid()
    except Exception:
        pass

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "data": _redact_dict(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
            "domain": entry.domain,
            "title": entry.title,
        },
        "host": {"valid": host_valid},
        "zones": raumfeld.get_zones(),
        "rooms": raumfeld.get_rooms(),
        "devices": raumfeld.get_raumfeld_device_udns(),
        "options": getattr(raumfeld, "options", None),
    }
