"""Platform for sensor integration."""

import asyncio
import inspect

from hassfeld.constants import (
    POWER_ACTIVE,
    POWER_STANDBY_AUTOMATIC,
    POWER_STANDBY_MANUAL,
)
import voluptuous as vol

from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import Entity

from . import log_debug, log_fatal
from .const import (
    ATTR_POWER_STATE,
    DEVICE_CLASS_SPEAKER,
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

    for udn in device_udns:
        renderer_udn = await raumfeld.async_get_device_renderer(udn)
        device_name = raumfeld.device_udn_to_name(renderer_udn)
        sw_version = await raumfeld.async_get_device_info(udn)
        manufacturer = await raumfeld.async_get_device_manufacturer(udn)
        model = await raumfeld.async_get_device_model_name(udn)

        sensor_config = {
            "device_udn": udn,
            "device_name": device_name,
            "get_state": raumfeld.async_get_device_info,
            "identifier": device_name,
            "manufacturer": manufacturer,
            "model": model,
            "sensor_name": "SoftwareVersion",
            "sw_version": sw_version,
        }
        log_debug("sensor_config=%s" % sensor_config)
        devices.append(RaumfeldSpeaker(raumfeld, sensor_config))

        sensor_config["sensor_name"] = "UpdateInfoVersion"
        sensor_config["get_state"] = raumfeld.async_get_device_update_info_version
        log_debug("sensor_config=%s" % sensor_config)
        devices.append(RaumfeldSpeaker(raumfeld, sensor_config))

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

    platform.async_register_entity_service(
        "set_power_state",
        vol.All(
            cv.make_entity_service_schema({vol.Required(ATTR_POWER_STATE): cv.string})
        ),
        "set_room_power_state",
    )

    return True


class RaumfeldSpeaker(Entity):
    """Representation of a Raumfeld speaker."""

    def __init__(self, raumfeld, sensor_config):
        """Initialize the Raumfeld speaker sensor."""
        self._raumfeld = raumfeld
        self._config = sensor_config
        self._device_udn = self._config["device_udn"]
        self._device_name = self._config["device_name"]
        self._sensor_name = self._config["sensor_name"]
        self._name = f"{self._device_name} - {self._sensor_name}"
        self._unique_id = f"{DOMAIN}.{self._device_name}.{self._sensor_name}"
        self._get_state = self._config["get_state"]
        self._sw_version = self._config["sw_version"]
        self._identifier = self._config["identifier"]
        self._manufacturer = self._config["manufacturer"]
        self._model = self._config["model"]
        self._state = None

        self._device_info = {
            "identifiers": {(DOMAIN, self._identifier)},
            "manufacturer": self._manufacturer,
            "model": self._model,
            "name": self._device_name,
            "sw_version": self._sw_version,
        }

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_SPEAKER

    @property
    def device_info(self):
        """Return information about the device."""
        return self._device_info

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
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    async def async_update(self):
        """Update sensor."""
        self._state = await self._get_state(self._device_udn)


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
        else:
            state = self._get_state(self._room_name)

        if state in STATE_TO_STATE:
            self._state = STATE_TO_STATE[state]
        else:
            self._state = state
        if state in STATE_TO_ICON:
            self._icon = STATE_TO_ICON[state]


class RaumfeldPowerState(RaumfeldRoom):
    """Power state sensor of a room."""

    def __init__(self, raumfeld, sensor_config):
        """Initialize the Raumfeld speaker sensor."""
        super().__init__(sensor_config)
        self._raumfeld = raumfeld

    def set_room_power_state(self, power_state):
        """Put a speaker in standby or wake it up."""
        if power_state == POWER_ON:
            self._raumfeld.leave_standby(self._room_name)
        elif power_state == POWER_ECO:
            self._raumfeld.enter_automatic_standby(self._room_name)
        elif power_state == POWER_STANDBY:
            self._raumfeld.enter_manual_standby(self._room_name)
        else:
            log_fatal("Unexpected power state: {power_state}")
