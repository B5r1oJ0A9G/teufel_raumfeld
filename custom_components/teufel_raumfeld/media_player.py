"""The Teufel Raumfeld media_player component."""
import base64
import datetime
import logging
import pickle

import hassfeld
from hassfeld.constants import (
    BROWSE_CHILDREN,
    BROWSE_METADATA,
    PLAY_MODE_NORMAL,
    PLAY_MODE_RANDOM,
    PLAY_MODE_REPEAT_ALL,
    PLAY_MODE_REPEAT_ONE,
    PLAY_MODE_SHUFFLE,
    TRANSPORT_STATE_NO_MEDIA,
    TRANSPORT_STATE_PAUSED,
    TRANSPORT_STATE_PLAYING,
    TRANSPORT_STATE_STOPPED,
    TRANSPORT_STATE_TRANSITIONING,
    TRIGGER_UPDATE_DEVICES,
    TRIGGER_UPDATE_HOST_INFO,
    TRIGGER_UPDATE_SYSTEM_STATE,
    TRIGGER_UPDATE_ZONE_CONFIG,
)
import voluptuous as vol

from homeassistant.components.media_player import BrowseMedia, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_VOLUME_LEVEL,
    MEDIA_TYPE_MUSIC,
    REPEAT_MODE_ALL,
    REPEAT_MODE_OFF,
    REPEAT_MODE_ONE,
    SUPPORT_BROWSE_MEDIA,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_REPEAT_SET,
    SUPPORT_SEEK,
    SUPPORT_SHUFFLE_SET,
    SUPPORT_STOP,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
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

from . import log_debug, log_error, log_fatal, log_info
from .const import (
    CHANGE_STEP_VOLUME_DOWN,
    CHANGE_STEP_VOLUME_UP,
    DEVICE_CLASS_SPEAKER,
    DOMAIN,
    GROUP_PREFIX,
    MEDIA_CONTENT_ID_SEP,
    ROOM_PREFIX,
    SERVICE_RESTORE,
    SERVICE_SNAPSHOT,
    UPNP_CLASS_ALBUM,
    UPNP_CLASS_LINE_IN,
    UPNP_CLASS_PLAYLIST_CONTAINER,
    UPNP_CLASS_PODCAST_EPISODE,
    UPNP_CLASS_RADIO,
    UPNP_CLASS_TRACK,
)

SUPPORTED_MEDIA_TYPES = [
    MEDIA_TYPE_MUSIC,
    UPNP_CLASS_ALBUM,
    UPNP_CLASS_TRACK,
    UPNP_CLASS_RADIO,
    UPNP_CLASS_PLAYLIST_CONTAINER,
    UPNP_CLASS_PODCAST_EPISODE,
    UPNP_CLASS_LINE_IN,
]

_LOGGER = logging.getLogger(__name__)


def obj_to_uid(object):
    """Bulid unique id based on object (room list)."""
    object_ser = pickle.dumps(object)
    serialised_b64 = base64.encodebytes(object_ser)
    unique_id = serialised_b64.decode()
    return unique_id


def uid_to_obj(uid):
    """Bulid object (room list) from unique id."""
    serialized_b64 = uid.encode()
    object_ser = base64.decodebytes(serialized_b64)
    object = pickle.loads(object_ser)
    return object


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
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
        if not entity.entity_id.startswith(platform.domain):
            log_info(
                "Entity '%s' is not recognized as media player and will not be restored as such"
                % entity.entity_id
            )
            continue

        rooms = uid_to_obj(entity.unique_id)
        if len(rooms) > 1:
            group = rooms
            if group not in room_groups:
                if entity.disabled:
                    continue
                devices.append(RaumfeldGroup(group, raumfeld))
        else:
            log_info(
                "Media player entity '%s' is not recognized as speaker group"
                % entity.entity_id
            )

    async_add_devices(devices)
    platform.async_register_entity_service(SERVICE_RESTORE, {}, "restore")
    platform.async_register_entity_service(SERVICE_SNAPSHOT, {}, "snapshot")
    platform.async_register_entity_service(
        "abs_volume_set",
        vol.All(
            cv.make_entity_service_schema(
                {
                    vol.Required(ATTR_MEDIA_VOLUME_LEVEL): cv.small_float,
                    vol.Optional("rooms"): vol.All(
                        cv.ensure_list, [vol.In(room_names)]
                    ),
                }
            )
        ),
        "set_rooms_volume_level",
    )
    return True


class RaumfeldGroup(MediaPlayerEntity):
    """Class representing a virtual media renderer for a speaker group."""

    def __init__(self, rooms, raumfeld):
        """Initialize media player for speaker group."""
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
        """Return True as entity has to be polled for state."""
        return True

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def state(self):
        """State of the player."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_SPEAKER

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
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
        """Flag media player features that are supported."""
        return SUPPORT_RAUMFELD_GROUP

    # MediaPlayer Methods

    def turn_on(self):
        """Turn the media player on."""
        if not self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.create_group(self._rooms)
            self.update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def mute_volume(self, mute):
        """Mute the volume."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.set_group_mute(self._rooms, mute)
            self.update_mute()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        if self._raumfeld.group_is_valid(self._rooms):
            raumfeld_vol = volume * 100
            self._raumfeld.set_group_volume(self._rooms, raumfeld_vol)
            self.update_volume_level()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def media_play(self):
        """Send play command."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.group_play(self._rooms)
            self.update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def media_pause(self):
        """Send pause command."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.group_pause(self._rooms)
            self.update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def media_stop(self):
        """Send stop command."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.group_stop(self._rooms)
            self.update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def media_previous_track(self):
        """Send previous track command."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.group_previous_track(self._rooms)
            self.update_track_info()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def media_next_track(self):
        """Send next track command."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.group_next_track(self._rooms)
            self.update_track_info()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def media_seek(self, position):
        """Send seek command."""
        if self._raumfeld.group_is_valid(self._rooms):
            raumfeld_pos = str(datetime.timedelta(seconds=int(position)))
            self._raumfeld.group_seek(self._rooms, raumfeld_pos)
            self.update_track_info()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def play_media(self, media_type, media_id, **kwargs):
        """Play a piece of media."""
        if self._raumfeld.group_is_valid(self._rooms):
            if media_type in SUPPORTED_MEDIA_TYPES:
                if media_type == MEDIA_TYPE_MUSIC:
                    if media_id.startswith("http"):
                        play_uri = media_id
                    else:
                        log_error("Unexpected URI for media type: %s" % media_type)
                elif media_type in [
                    UPNP_CLASS_ALBUM,
                    UPNP_CLASS_LINE_IN,
                    UPNP_CLASS_PLAYLIST_CONTAINER,
                    UPNP_CLASS_PODCAST_EPISODE,
                    UPNP_CLASS_RADIO,
                    UPNP_CLASS_TRACK,
                ]:
                    play_uri = media_id.split(MEDIA_CONTENT_ID_SEP)[1]
                else:
                    log_error("Unhandled media type: %s" % media_type)
                if self.state == STATE_OFF:
                    self.turn_on()
                log_debug("self._rooms=%s, play_uri=%s" % (self._rooms, play_uri))
                self._raumfeld.set_av_transport_uri(self._rooms, play_uri)
            else:
                log_error("Playing of media type '%s' not supported" % media_type)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def set_shuffle(self, shuffle):
        """Enable/disable shuffle mode."""
        if self._raumfeld.group_is_valid(self._rooms):
            if shuffle:
                if self._repeat != REPEAT_MODE_OFF:
                    self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_RANDOM)
                else:
                    self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_SHUFFLE)
            elif self._play_mode == PLAY_MODE_SHUFFLE:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_NORMAL)
            elif self._play_mode == PLAY_MODE_RANDOM:
                self._raumfeld.set_play_mode(self._rooms, PLAY_MODE_REPEAT_ALL)
            else:
                log_fatal("Invalid shuffle mode: %s" % shuffle)
            self.update_play_mode()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def set_repeat(self, repeat):
        """Set repeat mode."""
        if self._raumfeld.group_is_valid(self._rooms):
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
            else:
                log_fatal("Invalid repeate mode: %s" % repeat)
            self.update_play_mode()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def volume_up(self):
        """Turn volume up for media player."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.change_group_volume(self._rooms, CHANGE_STEP_VOLUME_UP)
            self.update_volume_level()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def volume_down(self):
        """Turn volume down for media player."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.change_group_volume(self._rooms, CHANGE_STEP_VOLUME_DOWN)
            self.update_volume_level()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

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
        """Update state of the player."""
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
            log_fatal("Unrecognized transport state: %s" % transport_state)
            self._state = STATE_OFF

    def update_volume_level(self):
        """Update volume level of the player."""
        self._volume_level = self._raumfeld.get_group_volume(self._rooms) / 100

    def update_mute(self):
        """Update mute status of the player."""
        self._mute = self._raumfeld.get_group_mute(self._rooms)

    def update_track_info(self):
        """Update media information of the player."""
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
        """Update play mode of the player."""
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
        else:
            log_fatal("Unrecognized play mode: %s" % play_mode)

    def update_all(self):
        """Run all state update methods of the player."""
        self.update_transport_state()
        self.update_volume_level()
        self.update_mute()
        self.update_track_info()
        self.update_play_mode()

    def update(self):
        """Update entity"""
        if self._raumfeld.group_is_valid(self._rooms):
            self.update_all()
        else:
            self._state = STATE_OFF

    # MediaPlayer service methods

    def snapshot(self):
        """Save the current media and position of the player."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.save_group(self._rooms)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def restore(self):
        """Restore previously saved media and position of the player."""
        if self._raumfeld.group_is_valid(self._rooms):
            self._raumfeld.restore_group(self._rooms)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    def set_rooms_volume_level(self, volume_level, rooms=None):
        """Set volume level, range 0..1."""
        if self._raumfeld.group_is_valid(self._rooms):
            raumfeld_vol = volume_level * 100
            self._raumfeld.set_group_room_volume(self._rooms, raumfeld_vol, rooms)
            self.update_volume_level()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )


class RaumfeldRoom(RaumfeldGroup):
    """Class representing a virtual media renderer for a room."""

    def __init__(self, room, raumfeld):
        """Initialize media player for room."""
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
