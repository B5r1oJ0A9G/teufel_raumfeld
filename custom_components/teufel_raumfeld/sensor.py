"""Platform for sensor integration."""

from homeassistant.components.media_player import MediaPlayerDeviceClass
from homeassistant.helpers.entity import Entity

from . import log_debug
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    device_udns = raumfeld.get_raumfeld_device_udns()
    log_debug("device_udns=%s" % device_udns)
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

    async_add_devices(devices)

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
        return MediaPlayerDeviceClass.SPEAKER

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
