"""The Teufel Raumfeld media_player component."""
import asyncio
import base64
import datetime
import logging
import pickle
from typing import Any

import voluptuous as vol
from hassfeld.constants import (
    BROWSE_CHILDREN,
    BROWSE_METADATA,
    PLAY_MODE_NORMAL,
    PLAY_MODE_RANDOM,
    PLAY_MODE_REPEAT_ALL,
    PLAY_MODE_REPEAT_ONE,
    PLAY_MODE_SHUFFLE,
    SOUND_FAILURE,
    SOUND_SUCCESS,
    TRANSPORT_STATE_NO_MEDIA,
    TRANSPORT_STATE_PAUSED,
    TRANSPORT_STATE_PLAYING,
    TRANSPORT_STATE_STOPPED,
    TRANSPORT_STATE_TRANSITIONING,
)
from homeassistant.components import media_source
from homeassistant.components.media_player import (
    ATTR_MEDIA_ANNOUNCE,
    ATTR_MEDIA_VOLUME_LEVEL,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaType,
    RepeatMode,
    async_process_play_media_url,
)
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry
from homeassistant.util.dt import utcnow

from . import log_debug, log_error, log_fatal, log_info
from .const import (
    DELAY_FAST_UPDATE_CHECKS,
    DOMAIN,
    GROUP_PREFIX,
    MEDIA_CONTENT_ID_SEP,
    OPTION_ANNOUNCEMENT_VOLUME,
    OPTION_CHANGE_STEP_VOLUME_DOWN,
    OPTION_CHANGE_STEP_VOLUME_UP,
    OPTION_DEFAULT_VOLUME,
    OPTION_FIXED_ANNOUNCEMENT_VOLUME,
    OPTION_USE_DEFAULT_VOLUME,
    ROOM_PREFIX,
    SERVICE_ABS_VOLUME_SET,
    SERVICE_PLAY_SYSTEM_SOUND,
    SERVICE_RESTORE,
    SERVICE_SNAPSHOT,
    TIMEOUT_TRANSITION_PERIOD,
    UPNP_CLASS_ALBUM,
    UPNP_CLASS_LINE_IN,
    UPNP_CLASS_PLAYLIST_CONTAINER,
    UPNP_CLASS_PODCAST_EPISODE,
    UPNP_CLASS_RADIO,
    UPNP_CLASS_TRACK,
)

SUPPORT_RAUMFELD_SPOTIFY = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
)

SUPPORT_RAUMFELD_GROUP = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.REPEAT_SET
)

SUPPORT_RAUMFELD_ROOM = SUPPORT_RAUMFELD_GROUP | MediaPlayerEntityFeature.GROUPING

SUPPORTED_MEDIA_TYPES = [
    MediaType.MUSIC,
    UPNP_CLASS_ALBUM,
    UPNP_CLASS_TRACK,
    UPNP_CLASS_RADIO,
    UPNP_CLASS_PLAYLIST_CONTAINER,
    UPNP_CLASS_PODCAST_EPISODE,
    UPNP_CLASS_LINE_IN,
]

_LOGGER = logging.getLogger(__name__)


def obj_to_uid(obj):
    """Bulid unique id based on object (room list)."""
    object_ser = pickle.dumps(obj)
    serialised_b64 = base64.encodebytes(object_ser)
    unique_id = serialised_b64.decode()
    return unique_id


def uid_to_obj(uid):
    """Bulid object (room list) from unique id."""
    serialized_b64 = uid.encode()
    object_ser = base64.decodebytes(serialized_b64)
    obj = pickle.loads(object_ser)
    return obj


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up entry."""
    raumfeld = hass.data[DOMAIN][config_entry.entry_id]
    room_names = raumfeld.get_rooms()
    room_groups = raumfeld.get_groups()
    registry = entity_registry.async_get(hass)
    entity_entries = entity_registry.async_entries_for_config_entry(
        registry, config_entry.entry_id
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
                raumfeld.eid_to_obj[entity.entity_id] = uid_to_obj(entity.unique_id)
        else:
            log_info(
                "Media player entity '%s' is not recognized as speaker group"
                % entity.entity_id
            )
            raumfeld.eid_to_obj[entity.entity_id] = uid_to_obj(entity.unique_id)

    async_add_devices(devices)
    platform.async_register_entity_service(SERVICE_RESTORE, {}, "async_restore")
    platform.async_register_entity_service(SERVICE_SNAPSHOT, {}, "async_snapshot")
    platform.async_register_entity_service(
        SERVICE_ABS_VOLUME_SET,
        vol.All(
            cv.make_entity_service_schema(
                {
                    vol.Required(ATTR_MEDIA_VOLUME_LEVEL): cv.positive_int,
                    vol.Optional("rooms"): vol.All(
                        cv.ensure_list, [vol.In(room_names)]
                    ),
                }
            )
        ),
        "async_set_rooms_volume_level",
    )
    platform.async_register_entity_service(
        SERVICE_PLAY_SYSTEM_SOUND,
        vol.All(
            cv.make_entity_service_schema(
                {
                    vol.Optional("sound"): vol.All(
                        cv.string, vol.In([SOUND_SUCCESS, SOUND_FAILURE])
                    ),
                }
            )
        ),
        "async_play_system_sound",
    )
    return True


class RaumfeldGroup(MediaPlayerEntity):
    """Class representing a virtual media renderer for a speaker group."""

    def __init__(self, rooms, raumfeld):
        """Initialize media player for speaker group."""
        self._room = None
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
        self._is_spotify_sroom = None
        self._attributes: dict[str, Any] = {}

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
        return MediaPlayerDeviceClass.SPEAKER

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
        return self._media_duration if self._media_duration else None

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
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def shuffle(self):
        """Boolean if shuffle is enabled."""
        return self._shuffle

    @property
    def repeat(self):
        """Return current repeat mode."""
        return self._repeat

    @property
    def group_members(self):
        """Return group memebers."""
        return self._rooms

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_RAUMFELD_GROUP

    # MediaPlayer Methods

    async def async_turn_on(self):
        """Turn the media player on."""
        if not self._raumfeld.group_is_valid(self._rooms):
            use_default_volume = self._raumfeld.options[OPTION_USE_DEFAULT_VOLUME]
            await self._raumfeld.async_create_group(self._rooms)
            if use_default_volume:
                default_volume = self._raumfeld.options[OPTION_DEFAULT_VOLUME] / 100
                await self.async_set_rooms_volume_level(default_volume)
            await self._raumfeld.async_restore_group(self._rooms)
            await self.async_update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_turn_off(self):
        """Turn the media player off."""
        if self._raumfeld.group_is_valid(self._rooms):
            if self._state == STATE_PLAYING:
                await self._raumfeld.async_save_group(self._rooms)
            await self.async_media_pause()
            rooms_to_drop = self._rooms[1:]
            while rooms_to_drop:
                room_to_drop = rooms_to_drop.pop()
                await self._raumfeld.async_drop_room_from_group(room_to_drop)
                await asyncio.sleep(DELAY_FAST_UPDATE_CHECKS)
            await self.async_update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_mute_volume(self, mute):
        """Mute the volume."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_set_group_mute(self._rooms, mute)
            await self.async_update_mute()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        raumfeld_vol = int(volume * 100)
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_set_group_volume(self._rooms, raumfeld_vol)
        elif self._is_spotify_sroom:
            await self._raumfeld.async_set_room_volume(self._room, raumfeld_vol)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )
        await self.async_update_volume_level()

    async def async_media_play(self):
        """Send play command."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_group_play(self._rooms)
        elif self._is_spotify_sroom:
            await self._raumfeld.async_room_play(self._room)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )
        await self.async_update_transport_state()

    async def async_media_pause(self):
        """Send pause command."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_group_pause(self._rooms)
        elif self._is_spotify_sroom:
            await self._raumfeld.async_room_pause(self._room)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )
        await self.async_update_transport_state()

    async def async_media_stop(self):
        """Send stop command."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_group_stop(self._rooms)
            await self.async_update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_media_previous_track(self):
        """Send previous track command."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_group_previous_track(self._rooms)
        elif self._is_spotify_sroom:
            await self._raumfeld.async_room_previous_track(self._room)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )
        await self.async_update_track_info()

    async def async_media_next_track(self):
        """Send next track command."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_group_next_track(self._rooms)
        elif self._is_spotify_sroom:
            await self._raumfeld.async_room_next_track(self._room)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )
        await self.async_update_track_info()

    async def async_media_seek(self, position):
        """Send seek command."""
        if self._raumfeld.group_is_valid(self._rooms):
            raumfeld_pos = str(datetime.timedelta(seconds=int(position)))
            await self._raumfeld.async_group_seek(self._rooms, raumfeld_pos)
            await self.async_update_track_info()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Play a piece of media."""
        play_uri = None
        if self._raumfeld.rooms_are_valid(self._rooms):
            if media_type in SUPPORTED_MEDIA_TYPES:
                log_debug("media_id=%s" % (media_id))
                if media_type == MediaType.MUSIC:
                    if media_id.startswith("http"):
                        play_uri = media_id
                    if media_id.startswith("media-source"):
                        play_item = await media_source.async_resolve_media(
                            self.hass, media_id, self.entity_id
                        )
                        play_uri = async_process_play_media_url(
                            self.hass, play_item.url
                        )
                    else:
                        log_error("Unexpected media ID for media type: %s" % media_type)
                elif media_type in [
                    UPNP_CLASS_ALBUM,
                    UPNP_CLASS_LINE_IN,
                    UPNP_CLASS_PLAYLIST_CONTAINER,
                    UPNP_CLASS_PODCAST_EPISODE,
                    UPNP_CLASS_RADIO,
                    UPNP_CLASS_TRACK,
                ]:
                    if MEDIA_CONTENT_ID_SEP in media_id:
                        play_uri = media_id.split(MEDIA_CONTENT_ID_SEP)[1]
                    else:
                        play_uri = media_id
                else:
                    log_error("Unhandled media type: %s" % media_type)
                log_debug("self._rooms=%s, play_uri=%s" % (self._rooms, play_uri))
                if play_uri is None:
                    log_error("URI to play could not be composed.")
                else:
                    announce = kwargs.get(ATTR_MEDIA_ANNOUNCE)
                    state_was_off = self.state == STATE_OFF
                    if state_was_off and not announce:
                        await self.async_turn_on()
                    was_playing = self._state == STATE_PLAYING
                    if announce and was_playing:
                        log_debug(
                            "Trigger snapshot for '%s' due to announcement"
                            % self._rooms
                        )
                        await self.async_snapshot()
                    if state_was_off and announce:
                        log_debug(
                            "Skip playing media for announcement because triggered on room "
                            + "or group that is in off state"
                        )
                    else:
                        fixed_announcement_volume = self._raumfeld.options[
                            OPTION_FIXED_ANNOUNCEMENT_VOLUME
                        ]
                        if announce and fixed_announcement_volume:
                            announcement_volume = (
                                self._raumfeld.options[OPTION_ANNOUNCEMENT_VOLUME] / 100
                            )
                            await self.async_set_volume_level(announcement_volume)
                        await self._raumfeld.async_set_av_transport_uri(
                            self._rooms, play_uri
                        )
                        self._attributes["last_content_id"] = play_uri
                        self._attributes["last_content_type"] = media_type
                    if announce and was_playing:
                        while self._state == STATE_PLAYING:
                            await asyncio.sleep(DELAY_FAST_UPDATE_CHECKS)
                        log_debug(
                            "Trigger restore of snapshot for '%s' due to announcement"
                            % self._rooms
                        )
                        await self.async_restore()
            else:
                log_error("Playing of media type '%s' not supported" % media_type)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_set_shuffle(self, shuffle):
        """Enable/disable shuffle mode."""
        if self._raumfeld.group_is_valid(self._rooms):
            if shuffle:
                if self._repeat != RepeatMode.OFF:
                    await self._raumfeld.async_set_play_mode(
                        self._rooms, PLAY_MODE_RANDOM
                    )
                else:
                    await self._raumfeld.async_set_play_mode(
                        self._rooms, PLAY_MODE_SHUFFLE
                    )
            elif self._play_mode == PLAY_MODE_SHUFFLE:
                await self._raumfeld.async_set_play_mode(self._rooms, PLAY_MODE_NORMAL)
            elif self._play_mode == PLAY_MODE_RANDOM:
                await self._raumfeld.async_set_play_mode(
                    self._rooms, PLAY_MODE_REPEAT_ALL
                )
            else:
                log_fatal("Invalid shuffle mode: %s" % shuffle)
            await self.async_update_play_mode()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_set_repeat(self, repeat):
        """Set repeat mode."""
        if self._raumfeld.group_is_valid(self._rooms):
            if repeat == RepeatMode.ALL:
                if self._shuffle:
                    await self._raumfeld.async_set_play_mode(
                        self._rooms, PLAY_MODE_RANDOM
                    )
                else:
                    await self._raumfeld.async_set_play_mode(
                        self._rooms, PLAY_MODE_REPEAT_ALL
                    )
            elif repeat == RepeatMode.ONE:
                await self._raumfeld.async_set_play_mode(
                    self._rooms, PLAY_MODE_REPEAT_ONE
                )
            elif repeat == RepeatMode.OFF:
                if self._shuffle:
                    await self._raumfeld.async_set_play_mode(
                        self._rooms, PLAY_MODE_SHUFFLE
                    )
                else:
                    await self._raumfeld.async_set_play_mode(
                        self._rooms, PLAY_MODE_NORMAL
                    )
            else:
                log_fatal("Invalid repeate mode: %s" % repeat)
            await self.async_update_play_mode()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_volume_up(self):
        """Turn volume up for media player."""
        if self._raumfeld.group_is_valid(self._rooms):
            change_step_volume = self._raumfeld.options[OPTION_CHANGE_STEP_VOLUME_UP]
            await self._raumfeld.async_change_group_volume(
                self._rooms, change_step_volume
            )
            await self.async_update_volume_level()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_volume_down(self):
        """Turn volume down for media player."""
        if self._raumfeld.group_is_valid(self._rooms):
            change_step_volume = (
                -1 * self._raumfeld.options[OPTION_CHANGE_STEP_VOLUME_DOWN]
            )
            await self._raumfeld.async_change_group_volume(
                self._rooms, change_step_volume
            )
            await self.async_update_volume_level()
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

        metadata = await self._raumfeld.async_browse_media(object_id, BROWSE_METADATA)
        metadata = metadata[0]

        children = await self._raumfeld.async_browse_media(object_id, BROWSE_CHILDREN)

        if children is None:
            log_fatal("No media identified")

        metadata.children = children
        return metadata

    # MediaPlayer update methods

    async def async_update_transport_state(self):
        """Update state of the player."""
        info = None
        max_attempts = int(TIMEOUT_TRANSITION_PERIOD / DELAY_FAST_UPDATE_CHECKS)

        for attempt in range(1, max_attempts):
            if self._raumfeld.group_is_valid(self._rooms):
                info = await self._raumfeld.async_get_transport_info(self._rooms)
            elif self._is_spotify_sroom:
                info = await self._raumfeld.async_get_room_transport_info(self._room)

            if info:
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
                    if attempt < max_attempts:
                        await asyncio.sleep(DELAY_FAST_UPDATE_CHECKS)
                        log_info(
                            "Starting attempt '%s' out of '%s' attempts for transport state update"
                            % (attempt + 1, max_attempts)
                        )
                        continue
                else:
                    log_fatal("Unrecognized transport state: %s" % transport_state)
                    self._state = STATE_OFF
            else:
                log_debug(
                    "Method was called although speaker group '%s' is invalid"
                    % self._rooms
                )
            break

    async def async_update_volume_level(self):
        """Update volume level of the player."""
        if self._raumfeld.group_is_valid(self._rooms):
            group_volume = await self._raumfeld.async_get_group_volume(self._rooms)
        elif self._is_spotify_sroom:
            group_volume = await self._raumfeld.async_get_room_volume(self._room)
        if group_volume:
            self._volume_level = group_volume / 100

    async def async_update_mute(self):
        """Update mute status of the player."""
        self._mute = await self._raumfeld.async_get_group_mute(self._rooms)

    async def async_update_track_info(self):
        """Update media information of the player."""
        track_info = await self._raumfeld.async_get_track_info(self._rooms)
        if track_info:
            self._media_duration = track_info["duration"]
            self._media_image_url = track_info["image_uri"]
            self._media_title = track_info["title"]
            self._media_artist = track_info["artist"]
            self._media_album_name = track_info["album"]
            self._media_album_artist = track_info["artist"]
            self._media_track = track_info["number"]
            self._media_position = track_info["position"]
            self._media_position_updated_at = utcnow()

    async def async_update_play_mode(self):
        """Update play mode of the player."""
        play_mode = await self._raumfeld.async_get_play_mode(self._rooms)
        if play_mode:
            self._play_mode = play_mode
            if play_mode == PLAY_MODE_NORMAL:
                self._shuffle = False
                self._repeat = RepeatMode.OFF
            elif play_mode == PLAY_MODE_SHUFFLE:
                self._shuffle = True
                self._repeat = RepeatMode.OFF
            elif play_mode == PLAY_MODE_REPEAT_ONE:
                self._shuffle = False
                self._repeat = RepeatMode.ONE
            elif play_mode == PLAY_MODE_REPEAT_ALL:
                self._shuffle = False
                self._repeat = RepeatMode.ALL
            elif play_mode == PLAY_MODE_RANDOM:
                self._shuffle = True
                self._repeat = RepeatMode.ALL
            else:
                log_fatal("Unrecognized play mode: %s" % play_mode)

    async def async_update_all(self):
        """Run all state update methods of the player."""
        await self.async_update_transport_state()
        if self._state != STATE_OFF:
            await self.async_update_volume_level()
            await self.async_update_mute()
            await self.async_update_track_info()
            await self.async_update_play_mode()

    async def async_update(self):
        """Update entity"""
        if self._raumfeld.group_is_valid(self._rooms):
            await self.async_update_all()
        else:
            self._state = STATE_OFF

    # MediaPlayer service methods

    async def async_snapshot(self):
        """Save the current media and position of the player."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_save_group(self._rooms)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_play_system_sound(self, sound=SOUND_SUCCESS):
        """Play system sound 'Success' or 'Failure'."""
        if self._raumfeld.group_is_valid(self._rooms):
            for room in self._rooms:
                await self._raumfeld.async_room_play_system_sound(room, sound)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_restore(self):
        """Restore previously saved media and position of the player."""
        if self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_restore_group(self._rooms)
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_set_rooms_volume_level(self, volume_level, rooms=None):
        """Set volume level, range 0..100."""
        if self._raumfeld.group_is_valid(self._rooms):
            raumfeld_vol = volume_level
            await self._raumfeld.async_set_group_room_volume(
                self._rooms, raumfeld_vol, rooms
            )
            await self.async_update_volume_level()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )


class RaumfeldRoom(RaumfeldGroup):
    """Class representing a virtual media renderer for a room."""

    def __init__(self, room, raumfeld):
        """Initialize media player for room."""
        super().__init__(room, raumfeld)
        self._room = room
        self._rooms = [room]
        self._raumfeld = raumfeld
        self._name = ROOM_PREFIX + repr(self._rooms)
        self._unique_id = obj_to_uid([room])
        self._icon = "mdi:speaker"

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        if self._is_spotify_sroom:
            return SUPPORT_RAUMFELD_SPOTIFY
        return super().supported_features

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_RAUMFELD_ROOM

    async def async_join_players(self, group_members):
        """Join `group_members` as a player group with the current player."""
        if self._raumfeld.group_is_valid(self._rooms):
            room_lst = []
            for member in group_members:
                obj = self._raumfeld.eid_to_obj[member]
                room_lst += obj
            await self._raumfeld.async_add_rooms_to_group(room_lst, self._rooms)
            await self.async_update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is invalid" % self._rooms
            )

    async def async_unjoin_player(self):
        """Remove this player from any group."""
        if not self._raumfeld.group_is_valid(self._rooms):
            await self._raumfeld.async_drop_room_from_group(self._room)
            await self.async_update_transport_state()
        else:
            log_debug(
                "Method was called although speaker group '%s' is valid" % self._rooms
            )

    async def async_update(self):
        """Update entity"""
        if self._raumfeld.group_is_valid(self._rooms):
            await super().async_update_all()
        elif self._raumfeld.room_is_spotify_single_room(self._room):
            self._is_spotify_sroom = True
            await super().async_update_transport_state()
        else:
            self._is_spotify_sroom = False
            self._state = STATE_OFF
