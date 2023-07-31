"""Platform for select integration."""

import asyncio

from homeassistant.components.select import SelectEntity

from . import log_debug, log_fatal
from .common import RaumfeldRoom
from .const import DELAY_POWER_STATE_UPDATE, DOMAIN, POWER_ECO, POWER_ON, POWER_STANDBY


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    device_udns = raumfeld.get_raumfeld_device_udns()
    log_debug("device_udns=%s" % device_udns)
    room_names = raumfeld.get_rooms()
    devices = []

    for room in room_names:
        sensor_config = {
            "room_name": room,
            "get_state": raumfeld.get_room_power_state,
            "identifier": room,
            "sensor_name": "PowerState",
        }
        log_debug("sensor_config=%s" % sensor_config)
        devices.append(RaumfeldPowerState(raumfeld, sensor_config))

    async_add_devices(devices)

    return True


class RaumfeldPowerState(RaumfeldRoom, SelectEntity):
    """Power state selector of a room."""

    def __init__(self, raumfeld, sensor_config):
        """Initialize the Raumfeld speaker sensor."""
        super().__init__(sensor_config)
        self._raumfeld = raumfeld
        self._attr_options = [POWER_ON, POWER_ECO, POWER_STANDBY]

    async def async_select_option(self, option):
        """Put a speaker in standby or wake it up."""
        log_debug("%s -> option: %s" % (self._room_name, option))
        if option == POWER_ON:
            await self._raumfeld.async_leave_standby(self._room_name)
        elif option == POWER_ECO:
            await self._raumfeld.async_enter_automatic_standby(self._room_name)
        elif option == POWER_STANDBY:
            await self._raumfeld.async_enter_manual_standby(self._room_name)
        else:
            log_fatal("Unexpected power state: {option}")
        await self.async_update()
        await asyncio.sleep(DELAY_POWER_STATE_UPDATE)
        self.async_schedule_update_ha_state()
