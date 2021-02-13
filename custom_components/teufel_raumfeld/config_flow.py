"""Config flow for Teufel Raumfeld integration."""
import logging

import hassfeld
import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DEFAULT_HOST_WEBSERVICE, DEFAULT_PORT_WEBSERVICE
from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default=DEFAULT_HOST_WEBSERVICE): str,
        vol.Required("port", default=DEFAULT_PORT_WEBSERVICE): str,
    }
)


async def validate_input(hass: core.HomeAssistant, data):

    raumfeld = hassfeld.RaumfeldHost(data["host"], data["port"])

    if not await raumfeld.async_host_is_valid():
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": f"Raumfeld host: {data['host']}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except (CannotConnect):
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            data = user_input
            data["entry_id"] = "raumfeld_host"
            return self.async_create_entry(title=info["title"], data=data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
