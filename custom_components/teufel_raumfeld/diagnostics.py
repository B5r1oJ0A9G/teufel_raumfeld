"""Diagnostics support for Teufel Raumfeld integration."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT = {"host", "port"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    raumfeld = entry.runtime_data

    # Redact sensitive fields using the official HA utility
    entry_data = dict(entry.data)
    try:
        from homeassistant.components.diagnostics import async_redact_data

        entry_data = async_redact_data(entry_data, TO_REDACT)
    except ImportError:
        entry_data = {k: "**REDACTED**" if k in TO_REDACT else v for k, v in entry_data.items()}

    # Safely collect host validity — may fail if host is unreachable
    host_valid: bool | str = "unknown"
    try:
        host_valid = await raumfeld.async_host_is_valid()
    except Exception:
        pass

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "data": entry_data,
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
