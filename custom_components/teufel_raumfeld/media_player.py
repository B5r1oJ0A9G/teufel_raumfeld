import base64
import datetime
import logging
import pickle

import hassfeld
import voluptuous as vol
from hassfeld.constants import (BROWSE_CHILDREN, BROWSE_METADATA,
                                PLAY_MODE_NORMAL, PLAY_MODE_RANDOM,
                                PLAY_MODE_REPEAT_ALL, PLAY_MODE_REPEAT_ONE,
                                PLAY_MODE_SHUFFLE, TRANSPORT_STATE_NO_MEDIA,
                                TRANSPORT_STATE_PAUSED,
                                TRANSPORT_STATE_PLAYING,
                                TRANSPORT_STATE_STOPPED,
                                TRANSPORT_STATE_TRANSITIONING,
                                TRIGGER_UPDATE_DEVICES,
                                TRIGGER_UPDATE_HOST_INFO,
                                TRIGGER_UPDATE_SYSTEM_STATE,
                                TRIGGER_UPDATE_ZONE_CONFIG)
from homeassistant.components.media_player import (BrowseMedia,
                                                   MediaPlayerEntity)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC, REPEAT_MODE_ALL, REPEAT_MODE_OFF, REPEAT_MODE_ONE,
    SUPPORT_BROWSE_MEDIA, SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA, SUPPORT_PREVIOUS_TRACK, SUPPORT_REPEAT_SET,
    SUPPORT_SEEK, SUPPORT_SHUFFLE_SET, SUPPORT_STOP, SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, SUPPORT_VOLUME_STEP)
from homeassistant.const import (STATE_IDLE, STATE_OFF, STATE_PAUSED,
                                 STATE_PLAYING)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry, async_get_registry)
from homeassistant.util.dt import utcnow

SUPPORT_RAUMFELD = SUPPORT_PAUSE | SUPPORT_STOP | SUPPORT_PLAY

SUPPORT_RAUMFELD_GROUP = (
    SUPPORT_PAUSE
    | SUPPORT_SEEK
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_VOLUME_STEP
    | SUPPORT_STOP
    | SUPPORT_TURN_ON
    | SUPPORT_PLAY
    | SUPPORT_SHUFFLE_SET
    | SUPPORT_BROWSE_MEDIA
    | SUPPORT_REPEAT_SET
)

from .const import (CHANGE_STEP_VOLUME_DOWN, CHANGE_STEP_VOLUME_UP,
                    DEVICE_CLASS_SPEAKER, DEVICE_MANUFACTURER, DOMAIN,
                    GROUP_PREFIX, MEDIA_CONTENT_ID_SEP, ROOM_PREFIX,
                    SERVICE_RESTORE, SERVICE_SNAPSHOT, UPNP_CLASS_ALBUM,
                    UPNP_CLASS_TRACK)

SUPPORTED_MEDIA_TYPES = [MEDIA_TYPE_MUSIC, UPNP_CLASS_ALBUM, UPNP_CLASS_TRACK]

_LOGGER = logging.getLogger(__name__)


def obj_to_uid(object):
    object_ser = pickle.dumps(object)
    serialised_b64 = base64.encodebytes(object_ser)
    unique_id = serialised_b64.decode()
    return unique_id


def uid_to_obj(uid):
    serialized_b64 = uid.encode()
    object_ser = base64.decodebytes(serialized_b64)
    object = pickle.loads(object_ser)
    return object


async def async_setup_entry(hass, config_entry, async_add_devices):
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    room_names = raumfeld.get_rooms()
    room_groups = raumfeld.get_groups()
    entity_registry = await hass.helpers.entity_registry.async_get_registry()
    entity_entries = hass.helpers.entity_registry.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    platform = entity_platform.current_platform.get()
    devices = []

    for room_name in room_names:
        devices.append(RaumfeldRoom(room_name, raumfeld))

    for group in room_groups:
        if len(group) > 1:
            devices.append(RaumfeldGroup(group, raumfeld))

    for entity in entity_entries:
        rooms = uid_to_obj(entity.unique_id)
        if len(rooms) > 1:
            group = rooms
            if group not in room_groups:
                devices.append(RaumfeldGroup(group, raumfeld))

    async_add_devices(devices)
    platform.async_register_entity_service(SERVICE_RESTORE, {}, "restore")
    platform.async_register_entity_service(SERVICE_SNAPSHOT, {}, "snapshot")
    return True


class RaumfeldGroup(MediaPlayerEntity):
    def __init__(self, rooms, raumfeld):
        self._rooms = rooms
        self._raumfeld = raumfeld
        self._mute = None
        self._media_position = None
        self._media_position_updated_at = None
        self._name = GROUP_PREFIX + repr(self._rooms)
        self._state = None
        self._volume_level = None
        self._unique_id = obj_to_uid(rooms)
        self._icon = "mdi:speaker-multiple"
        self._media_duration = None
        self._media_image_url = None
        self._media_title = None
        self._media_artist = None
        self._media_album_name = None
        self._media_album_artist = None
        self._media_track = None
        self._shuffle = None
        self._repeat = None
        self._play_mode = None

    # Entity Properties

    @property
    def should_poll(self):
        return True

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        """State of the player."""
        return self._state

    @property
    def device_class(self):
        return DEVICE_CLASS_SPEAKER

    @property
    def icon(self):
        return self._icon

    # MediaPlayer properties

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume_level

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._mute

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self._media_duration

    @property
    def media_position(self):
        """Position of current playing media in seconds."""
        return self._media_position

    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid."""
        return self._media_position_updated_at

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._media_image_url

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._media_title

    @property
    def media_artist(self):
        """Artist of current playing media, music track only."""
        return self._media_artist

    @property
    def media_album_name(self):
        """Album name of current playing media, music track only."""
        return self._media_album_name

    @property
    def media_album_artist(self):
        """Album artist of current playing media, music track only."""
        return self._media_album_artist

    @property
    def media_track(self):
        """Track number of current playing media, music track only."""
        return self._media_track

    @property
    def shuffle(self):
        """Boolean if shuffle is enabled."""
        return self._shuffle

    @property
    def repeat(self):
        """Return current repeat mode."""
        return self._repeat

    @property
    def supported_features(self):
        return SUPPORT_RAUMFELD_GROUP

    # MediaPlayer Methods

    def turn_on(self):
        """Turn the media player on."""
        self._raumfeld.create_group(self._rooms)
        self.update_transport_state()

    def mute_volume(self, mute):
        self._raumfeld.set_group_mute(self._rooms, mute)
        self.update_mute()

    def set_volume_level(self, volume):
        raumfeld_vol = volume * 100
        self._raumfeld.set_group_volume(self._rooms, raumfeld_vol)
        self.update_volume_level()

    def media_play(self):
        self._raumfeld.group_play(self._rooms)
        self.update_transport_state()

    def media_pause(self):
        self._raumfeld.group_pause(self._rooms)
        self.update_transport_state()

    def media_stop(self):
        self._raumfeld.group_stop(self._rooms)
        self.update_transport_state()

    def media_previous_track(self):
        self._raumfeld.group_previous_track(self._rooms)
        self.update_track_info()

    def media_next_track(self):
        self._raumfeld.group_next_track(self._rooms)
        self.update_track_info()

    def media_seek(self, position):
        raumfeld_pos = str(datetime.timedelta(seconds=int(position)))
        self._raumfeld.group_seek(self._rooms, raumfeld_pos)
        self.update_track_info()

    def play_media(self, media_type, media_id, **kwargs):
        """Play a piece of media."""
        if media_type == MEDIA_TYPE_MUSIC:
            if media_id.startswith("http"):
                play_uri = media_id
        if media_type == UPNP_CLASS_ALBUM or media_type == UPNP_CLASS_TRACK:
            play_uri = media_id.split(MEDIA_CONTENT_ID_SEP)[1]
        if media_type in SUPPORTED_MEDIA_TYPES:
            if self.state == STATE_OFF:
                self.turn_on()
            self._raumfeld.set_av_transport_uri(self._rooms, play_uri)

    def set_shuffle(self, shuffle):
        """Enable/disable shuffle mode."""
        if shuffle:
            if self._repeat != REPEAT_MODE_OFF:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_RANDOM)
            else:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_SHUFFLE)
        elif self._play_mode == PLAY_MODE_SHUFFLE:
            self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_NORMAL)
        elif self._play_mode == PLAY_MODE_RANDOM:
            self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_REPEAT_ALL)
        self.update_play_mode()

    def set_repeat(self, repeat):
        """Set repeat mode."""
        if repeat == REPEAT_MODE_ALL:
            if self._shuffle:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_RANDOM)
            else:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_REPEAT_ALL)
        elif repeat == REPEAT_MODE_ONE:
            self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_REPEAT_ONE)
        elif repeat == REPEAT_MODE_OFF:
            if self._shuffle:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_SHUFFLE)
            else:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_NORMAL)
        self.update_play_mode()

    def volume_up(self):
        self._raumfeld.change_group_volume(self._rooms, CHANGE_STEP_VOLUME_UP)
        self.update_volume_level()

    def volume_down(self):
        self._raumfeld.change_group_volume(self._rooms, CHANGE_STEP_VOLUME_DOWN)
        self.update_volume_level()

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Implement the websocket media browsing helper."""
        if media_content_type in [None, "library"]:
            pass

        if media_content_id is None:
            object_id = "0"
        else:
            object_id = media_content_id

        metadata = await self.hass.async_add_executor_job(
            self._raumfeld.browse_media, object_id, BROWSE_METADATA
        )
        metadata = metadata[0]

        children = await self.hass.async_add_executor_job(
            self._raumfeld.browse_media, object_id, BROWSE_CHILDREN
        )

        if children is None:
            raise BrowseError(
                f"Media not found: {media_content_type} / {media_content_id}"
            )

        metadata.children = children
        return metadata

    # MediaPlayer update methods

    def update_transport_state(self):
        info = self._raumfeld.get_transport_info(self._rooms)
        transport_state = info["CurrentTransportState"]
        if transport_state == TRANSPORT_STATE_STOPPED:
            self._state = STATE_IDLE
        elif transport_state == TRANSPORT_STATE_NO_MEDIA:
            self._state = STATE_IDLE
        elif transport_state == TRANSPORT_STATE_PLAYING:
            self._state = STATE_PLAYING
        elif transport_state == TRANSPORT_STATE_PAUSED:
            self._state = STATE_PAUSED
        elif transport_state == TRANSPORT_STATE_TRANSITIONING:
            pass
        else:
            self._state = STATE_OFF

    def update_volume_level(self):
        self._volume_level = self._raumfeld.get_group_volume(self._rooms) / 100

    def update_mute(self):
        self._mute = self._raumfeld.get_group_mute(self._rooms)

    def update_track_info(self):
        track_info = self._raumfeld.get_track_info(self._rooms)
        self._media_duration = track_info["duration"]
        self._media_image_url = track_info["image_uri"]
        self._media_title = track_info["title"]
        self._media_artist = track_info["artist"]
        self._media_album_name = track_info["album"]
        self._media_album_artist = track_info["artist"]
        self._media_track = track_info["number"]
        self._media_position = track_info["position"]
        self._media_position_updated_at = utcnow()

    def update_play_mode(self):
        play_mode = self._raumfeld.get_play_mode(self._rooms)
        self._play_mode = play_mode
        if play_mode == PLAY_MODE_NORMAL:
            self._shuffle = False
            self._repeat = REPEAT_MODE_OFF
        elif play_mode == PLAY_MODE_SHUFFLE:
            self._shuffle = True
            self._repeat = REPEAT_MODE_OFF
        elif play_mode == PLAY_MODE_REPEAT_ONE:
            self._shuffle = False
            self._repeat = REPEAT_MODE_ONE
        elif play_mode == PLAY_MODE_REPEAT_ALL:
            self._shuffle = False
            self._repeat = REPEAT_MODE_ALL
        elif play_mode == PLAY_MODE_RANDOM:
            self._shuffle = True
            self._repeat = REPEAT_MODE_ALL

    def update_all(self):
        self.update_transport_state()
        self.update_volume_level()
        self.update_mute()
        self.update_track_info()
        self.update_play_mode()

    def update(self):
        if self._raumfeld.group_is_valid(self._rooms):
            self.update_all()
        else:
            self._state = STATE_OFF

    # MediaPlayer service methods

    def snapshot(self):
        self._raumfeld.save_group(self._rooms)

    def restore(self):
        self._raumfeld.restore_group(self._rooms)


class RaumfeldRoom(RaumfeldGroup):
    def __init__(self, room, raumfeld):
        self._rooms = [room]
        self._raumfeld = raumfeld
        self._mute = None
        self._media_position = None
        self._media_position_updated_at = None
        self._name = ROOM_PREFIX + repr(self._rooms)
        self._state = None
        self._volume_level = None
        self._unique_id = obj_to_uid([room])
        self._icon = "mdi:speaker"
        self._media_duration = None
        self._media_image_url = None
        self._media_title = None
        self._media_artist = None
        self._media_album_name = None
        self._media_album_artist = None
        self._media_track = None
        self._shuffle = None
        self._repeat = None
        self._play_mode = None


class RaumfeldDevice(MediaPlayerEntity):
    def __init__(self, room, raumfeld):
        self._room = room
        self._raumfeld = raumfeld
        self._icon = "mdi:speaker"
        self._name = ROOM_PREFIX + self._room
        self._unique_id = self._name
        self._state = STATE_IDLE
        self._host_entry_id = ROOM_PREFIX + repr(self._raumfeld.get_host_room())

        self._device_info = {
            "identifiers": {(DOMAIN, self._name)},
            "name": self.name,
            "manufacturer": DEVICE_MANUFACTURER,
            "via_device": (DOMAIN, self._host_entry_id),
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_SPEAKER

    @property
    def device_info(self):
        return self._device_info

    @property
    def icon(self):
        return self._icon

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        return self._state

    @property
    def supported_features(self):
        return SUPPORT_RAUMFELD

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def media_content_type(self):
        pass

    def media_stop(self):
        pass

    def media_play(self):
        pass

    def media_pause(self):
        pass

    def media_seek(self, target):
        pass
