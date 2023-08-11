"""Commonly used classes."""
import inspect

from hassfeld.constants import (
    POWER_ACTIVE,
    POWER_STANDBY_AUTOMATIC,
    POWER_STANDBY_MANUAL,
)
from homeassistant.helpers.entity import Entity

from . import log_debug
from .const import DOMAIN, POWER_ECO, POWER_ON, POWER_STANDBY, ROOM_PREFIX

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
