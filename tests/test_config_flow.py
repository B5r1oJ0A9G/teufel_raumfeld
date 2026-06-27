"""Tests for teufel_raumfeld config_flow module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.teufel_raumfeld.const import (
    OPTION_ANNOUNCEMENT_VOLUME,
    OPTION_CHANGE_STEP_VOLUME_DOWN,
    OPTION_CHANGE_STEP_VOLUME_UP,
    OPTION_DEFAULT_VOLUME,
    OPTION_FIXED_ANNOUNCEMENT_VOLUME,
    OPTION_USE_DEFAULT_VOLUME,
)


class TestOptionsFlowHandler:
    """Tests for the OptionsFlowHandler options form."""

    @pytest.mark.asyncio
    async def test_submit_creates_entry(self):
        """Submitting the options form creates an options entry."""
        from custom_components.teufel_raumfeld.config_flow import OptionsFlowHandler

        config_entry = MagicMock()
        config_entry.options.get.side_effect = lambda key, default: default

        handler = OptionsFlowHandler(config_entry)
        # config_entry is a @property that reads from self.handler.config_entry.
        # Mock handler (which would be set by the framework).
        handler.handler = MagicMock()
        handler.handler.config_entry = config_entry
        handler.hass = MagicMock()

        user_input = {
            OPTION_FIXED_ANNOUNCEMENT_VOLUME: True,
            OPTION_ANNOUNCEMENT_VOLUME: 50,
            OPTION_USE_DEFAULT_VOLUME: False,
            OPTION_DEFAULT_VOLUME: 30,
            OPTION_CHANGE_STEP_VOLUME_UP: 3,
            OPTION_CHANGE_STEP_VOLUME_DOWN: 2,
        }

        result = await handler.async_step_init(user_input=user_input)
        assert result["type"] == "create_entry"
        assert result["data"] == user_input


class TestConfigFlowUserStep:
    """Tests for the ConfigFlow async_step_user method."""

    @pytest.mark.asyncio
    async def test_show_form_when_no_input(self):
        from custom_components.teufel_raumfeld.config_flow import ConfigFlow

        flow = ConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user(user_input=None)
        assert result["type"] == "form"

    @pytest.mark.asyncio
    async def test_successful_validation_creates_entry(self):
        from custom_components.teufel_raumfeld.config_flow import ConfigFlow

        flow = ConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.teufel_raumfeld.config_flow.validate_input",
            new_callable=AsyncMock,
        ) as mock_validate:
            mock_validate.return_value = {"title": "Raumfeld host: 192.168.1.100"}

            result = await flow.async_step_user(
                user_input={"host": "192.168.1.100", "port": "47365"}
            )
            assert result["type"] == "create_entry"
            assert result["title"] == "Raumfeld host: 192.168.1.100"
            assert result["data"]["host"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_cannot_connect_shows_error(self):
        from custom_components.teufel_raumfeld.config_flow import (
            CannotConnect,
            ConfigFlow,
        )

        flow = ConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.teufel_raumfeld.config_flow.validate_input",
            new_callable=AsyncMock,
        ) as mock_validate:
            mock_validate.side_effect = CannotConnect

            result = await flow.async_step_user(
                user_input={"host": "bad-host", "port": "47365"}
            )
            assert result["type"] == "form"
            assert result["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_unexpected_error_shows_unknown(self):
        from custom_components.teufel_raumfeld.config_flow import ConfigFlow

        flow = ConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.teufel_raumfeld.config_flow.validate_input",
            new_callable=AsyncMock,
        ) as mock_validate:
            mock_validate.side_effect = RuntimeError("Boom")

            result = await flow.async_step_user(
                user_input={"host": "bad-host", "port": "47365"}
            )
            assert result["type"] == "form"
            assert result["errors"]["base"] == "unknown"

    def test_form_schema_has_host_and_port(self):
        from custom_components.teufel_raumfeld.config_flow import (
            STEP_USER_DATA_SCHEMA,
        )

        schema_str = str(STEP_USER_DATA_SCHEMA.schema)
        assert "host" in schema_str
        assert "port" in schema_str
