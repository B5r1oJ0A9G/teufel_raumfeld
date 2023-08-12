"""Config flow for Teufel Raumfeld integration."""
import logging
from typing import Any

import hassfeld
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN  # pylint:disable=unused-import
from .const import (
    DEFAULT_ANNOUNCEMENT_VOLUME,
    DEFAULT_CHANGE_STEP_VOLUME_DOWN,
    DEFAULT_CHANGE_STEP_VOLUME_UP,
    DEFAULT_HOST_WEBSERVICE,
    DEFAULT_PORT_WEBSERVICE,
    DEFAULT_VOLUME,
    OPTION_ANNOUNCEMENT_VOLUME,
    OPTION_CHANGE_STEP_VOLUME_DOWN,
    OPTION_CHANGE_STEP_VOLUME_UP,
    OPTION_DEFAULT_VOLUME,
    OPTION_FIXED_ANNOUNCEMENT_VOLUME,
    OPTION_USE_DEFAULT_VOLUME,
)

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default=DEFAULT_HOST_WEBSERVICE): str,
        vol.Required("port", default=DEFAULT_PORT_WEBSERVICE): str,
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Connects to raumfehld host and tested the interface."""
    raumfeld = hassfeld.RaumfeldHost(data["host"], data["port"])

    if not await raumfeld.async_host_is_valid():
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": f"Raumfeld host: {data['host']}"}


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPTION_FIXED_ANNOUNCEMENT_VOLUME,
                        default=self.config_entry.options.get(
                            OPTION_FIXED_ANNOUNCEMENT_VOLUME, False
                        ),
                    ): bool,
                    vol.Required(
                        OPTION_ANNOUNCEMENT_VOLUME,
                        default=self.config_entry.options.get(
                            OPTION_ANNOUNCEMENT_VOLUME, DEFAULT_ANNOUNCEMENT_VOLUME
                        ),
                    ): vol.All(int, vol.Range(min=0, max=100)),
                    vol.Required(
                        OPTION_USE_DEFAULT_VOLUME,
                        default=self.config_entry.options.get(
                            OPTION_USE_DEFAULT_VOLUME, False
                        ),
                    ): bool,
                    vol.Required(
                        OPTION_DEFAULT_VOLUME,
                        default=self.config_entry.options.get(
                            OPTION_DEFAULT_VOLUME, DEFAULT_VOLUME
                        ),
                    ): vol.All(int, vol.Range(min=0, max=100)),
                    vol.Required(
                        OPTION_CHANGE_STEP_VOLUME_UP,
                        default=self.config_entry.options.get(
                            OPTION_CHANGE_STEP_VOLUME_UP,
                            DEFAULT_CHANGE_STEP_VOLUME_UP,
                        ),
                    ): vol.All(int, vol.Range(min=1, max=20)),
                    vol.Required(
                        OPTION_CHANGE_STEP_VOLUME_DOWN,
                        default=self.config_entry.options.get(
                            OPTION_CHANGE_STEP_VOLUME_DOWN,
                            DEFAULT_CHANGE_STEP_VOLUME_DOWN,
                        ),
                    ): vol.All(int, vol.Range(min=1, max=20)),
                }
            ),
        )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow to add Raumfeld media players and sensors."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
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
