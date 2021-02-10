"""Platform for sensor integration."""
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import entity_platform

from . import DOMAIN

import hassfeld.aioupnp
import hassfeld.upnp

from .const import (DEVICE_CLASS_SPEAKER, DOMAIN)

def get_update_info_version(location):
    """Wrapper function to return the version of a device"""
    response = hassfeld.upnp.get_update_info(location)
    return response["Version"]

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    device_udns = raumfeld.get_raumfeld_device_udns()
    entity_registry = await hass.helpers.entity_registry.async_get_registry()
    entity_entries = hass.helpers.entity_registry.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    platform = entity_platform.current_platform.get()
    devices = []

    for udn in device_udns:
        device_location = raumfeld.device_udn_to_location(udn)
        renderer_udn = await hass.async_add_executor_job(hassfeld.upnp.get_device, device_location, "renderer")
        device_name = raumfeld.device_udn_to_name(renderer_udn)
        sw_version = await hass.async_add_executor_job(hassfeld.upnp.get_info, device_location)
        manufacturer = await hass.async_add_executor_job(hassfeld.upnp.get_manufacturer, device_location)
        model = await hass.async_add_executor_job(hassfeld.upnp.get_model_name, device_location)

        sensor_config = {
            "device_name": device_name,
            "get_state": hassfeld.upnp.get_info,
            "identifier": device_name,
            "location": device_location,
            "manufacturer": manufacturer,
            "model": model,
            "sensor_name": "SoftwareVersion",
            "sw_version": sw_version,
        }
        devices.append(RaumfeldSensor(sensor_config))

        sensor_config["sensor_name"] = "UpdateInfoVersion"
        sensor_config["get_state"] = get_update_info_version
        devices.append(RaumfeldSensor(sensor_config))

    async_add_devices(devices)
    return True

class RaumfeldSensor(Entity):
    """Representation of a Raumfeld speaker."""

    def __init__(self, sensor_config):
        """Initialize the Raumfeld speaker sensor."""
        self._config = sensor_config
        self._name = self._config["device_name"] + " - " + self._config["sensor_name"]
        self._device_name = self._config["device_name"]
        self._unique_id = DOMAIN + "." + self._config["device_name"] + "." + self._config["sensor_name"]
        self._location = self._config["location"]
        self._get_state = self._config["get_state"]
        self._sw_version = self._config["sw_version"]
        self._identifier = self._config["identifier"]
        self._manufacturer= self._config["manufacturer"]
        self._model= self._config["model"]
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

    def update(self):
        """Update sensor."""
        self._state = self._get_state(self._location)
