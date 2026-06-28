"""Platform for number integration."""

from homeassistant.components.number import NumberEntity
from homeassistant.const import EntityCategory

from . import log_debug
from .common import RaumfeldRoom
from .const import (
    NUMBER_ROOM_VOLUME_ICON,
    NUMBER_ROOM_VOLUME_NAME,
)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = config_entry.runtime_data
    device_udns = raumfeld.get_raumfeld_device_udns()
    log_debug(f"device_udns={device_udns}")
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
        log_debug(f"number_config={number_config}")
        devices.append(RaumfeldRoomVolume(raumfeld, number_config))

    async_add_devices(devices)

    return True


class RaumfeldRoomVolume(RaumfeldRoom, NumberEntity):
    """Volume selector of a room."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    PARALLEL_UPDATES = 1

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
        log_debug(f"{self._room_name} -> volume: {volume}")
        await self._raumfeld.async_set_room_volume(self._room_name, volume)
        await self.async_update()
        self.async_schedule_update_ha_state()
