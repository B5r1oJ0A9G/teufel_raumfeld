"""Platform for select integration."""

import asyncio
import inspect

from hassfeld.constants import (
    POWER_ACTIVE,
    POWER_STANDBY_AUTOMATIC,
    POWER_STANDBY_MANUAL,
)
from homeassistant.components.select import SelectEntity
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity

from . import log_debug, log_fatal
from .const import (
    DELAY_POWER_STATE_UPDATE,
    DOMAIN,
    POWER_ECO,
    POWER_ON,
    POWER_STANDBY,
    ROOM_PREFIX,
)

STATE_TO_ICON = {
    POWER_ACTIVE: "mdi:power-on",
    POWER_STANDBY_AUTOMATIC: "mdi:power-standby",
    POWER_STANDBY_MANUAL: "mdi:power-off",
}

STATE_TO_STATE = {
    POWER_ACTIVE: POWER_ON,
    POWER_STANDBY_AUTOMATIC: POWER_ECO,
    POWER_STANDBY_MANUAL: POWER_STANDBY,
}


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    device_udns = raumfeld.get_raumfeld_device_udns()
    log_debug("device_udns=%s" % device_udns)
    room_names = raumfeld.get_rooms()
    platform = entity_platform.current_platform.get()
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


class RaumfeldRoom(Entity):
    """Representation of a Raumfeld speaker."""

    def __init__(self, sensor_config):
        """Initialize the Raumfeld speaker sensor."""
        self._config = sensor_config
        self._room_name = self._config["room_name"]
        self._sensor_name = self._config["sensor_name"]
        self._name = f"{ROOM_PREFIX}{self._room_name} - {self._sensor_name}"
        self._unique_id = f"{DOMAIN}.{ROOM_PREFIX}{self._room_name}.{self._sensor_name}"
        self._get_state = self._config["get_state"]
        self._room_name = self._config["room_name"]
        self._state = None
        self._icon = None

    @property
    def should_poll(self):
        """Return True as entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """State of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    async def async_update(self):
        """Update sensor."""
        if inspect.iscoroutinefunction(self._get_state):
            state = await self._get_state(self._room_name)
            log_debug("state: %s" % state)
        else:
            state = self._get_state(self._room_name)

        if state in STATE_TO_STATE:
            self._state = STATE_TO_STATE[state]
        else:
            self._state = state
        if state in STATE_TO_ICON:
            self._icon = STATE_TO_ICON[state]


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
