"""Platform for number integration."""

from homeassistant.components.number import NumberEntity

from . import log_debug, log_fatal
from .common import RaumfeldRoom
from .const import (
    DELAY_POWER_STATE_UPDATE,
    DOMAIN,
    NUMBER_ROOM_VOLUME_ICON,
    NUMBER_ROOM_VOLUME_NAME,
)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    device_udns = raumfeld.get_raumfeld_device_udns()
    log_debug("device_udns=%s" % device_udns)
    room_names = raumfeld.get_rooms()
    devices = []

    for room in room_names:
        number_config = {
            "room_name": room,
            "get_state": raumfeld.async_get_room_volume,
            "identifier": room,
            "sensor_name": NUMBER_ROOM_VOLUME_NAME,
            "native_unit_of_measurement": "%",
        }
        log_debug("number_config=%s" % number_config)
        devices.append(RaumfeldRoomVolume(raumfeld, number_config))

    async_add_devices(devices)

    return True


class RaumfeldRoomVolume(RaumfeldRoom, NumberEntity):
    """Volume selector of a room."""

    def __init__(self, raumfeld, number_config):
        """Initialize the Raumfeld speaker number."""
        super().__init__(number_config)
        self._raumfeld = raumfeld
        self._icon = NUMBER_ROOM_VOLUME_ICON

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    async def async_set_native_value(self, value):
        """Set new speaker volume."""
        volume = int(value)
        log_debug("%s -> volume: %s" % (self._room_name, volume))
        await self._raumfeld.async_set_room_volume(self._room_name, volume)
        await self.async_update()
        self.async_schedule_update_ha_state()
