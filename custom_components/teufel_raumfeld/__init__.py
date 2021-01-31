"""The Teufel Raumfeld integration."""
import asyncio
import urllib.parse

import hassfeld
import voluptuous as vol
import xmltodict
from homeassistant.components.media_player import BrowseMedia
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (DOMAIN, MEDIA_CONTENT_ID_SEP, PLATFORMS,
                    SUPPORTED_OBJECT_IDS, SUPPORTED_OBJECT_PREFIXES,
                    UPNP_CLASS_ALBUM, UPNP_CLASS_TRACK, URN_CONTENT_DIRECTORY)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Teufel Raumfeld component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Teufel Raumfeld from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]
    raumfeld = HassRaumfeldHost(host, port)
    raumfeld.start_update_thread()
    hass.data[DOMAIN][entry.entry_id] = raumfeld

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    def handle_group(call):
        room_lst = call.data.get("room_names")
        raumfeld.create_group(room_lst)

    hass.services.async_register(DOMAIN, "group", handle_group)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class HassRaumfeldHost(hassfeld.RaumfeldHost):
    def get_groups(self):
        return self.get_zones()

    def group_is_valid(self, room_lst):
        return self.zone_is_valid(room_lst)

    def create_group(self, room_lst):
        self.create_zone(room_lst)

    def set_group_mute(self, room_lst, mute):
        self.set_zone_mute(room_lst, mute)

    def set_group_volume(self, room_lst, raumfeld_vol):
        self.set_zone_volume(room_lst, raumfeld_vol)

    def group_play(self, room_lst):
        self.zone_play(room_lst)

    def group_pause(self, room_lst):
        self.zone_pause(room_lst)

    def group_stop(self, room_lst):
        self.zone_stop(room_lst)

    def group_previous_track(self, room_lst):
        self.zone_previous_track(room_lst)

    def group_next_track(self, room_lst):
        self.zone_next_track(room_lst)

    def group_seek(self, room_lst, position):
        self.zone_seek(room_lst, position)

    def change_group_volume(self, room_lst, volume):
        self.change_zone_volume(room_lst, volume)

    def get_group_volume(self, room_lst):
        return self.get_zone_volume(room_lst)

    def get_group_mute(self, room_lst):
        return self.get_zone_mute(room_lst)

    def save_group(self, room_lst):
        self.save_zone(room_lst)

    def restore_group(self, room_lst):
        self.restore_zone(room_lst)

    def search_and_group_play(self, zone_room_lst, search_criteria):
        self.search_and_zone_play(zone_room_lst, search_criteria)

    def _timespan_secs(self, timespan):
        """Parse a time-span into number of seconds."""
        return sum(
            60 ** x[0] * int(x[1]) for x in enumerate(reversed(timespan.split(":")))
        )

    def browse_media(self, object_id=0, browse_flag=None):
        browse_lst = []
        can_expand = False
        can_play = False
        thumbnail = None
        track_number = -1
        browsable_oid = object_id.split(MEDIA_CONTENT_ID_SEP)[0]
        media_xml = self.browse_media_server(browsable_oid, browse_flag)
        media = xmltodict.parse(media_xml, force_list=("container", "item"))

        if "container" in media["DIDL-Lite"]:
            entry_type = "container"
        elif "item" in media["DIDL-Lite"]:
            entry_type = "item"

        media_entries = media["DIDL-Lite"][entry_type]

        for entry in media_entries:
            supported_oid = False
            media_content_id = entry["@id"]

            if media_content_id in SUPPORTED_OBJECT_IDS:
                supported_oid = True
            else:
                for oid_prefix in SUPPORTED_OBJECT_PREFIXES:
                    if media_content_id.startswith(oid_prefix):
                        supported_oid = True
                        break

            if not supported_oid:
                continue

            media_content_type = entry["upnp:class"]

            if "@childCount" in entry:
                if entry["@childCount"] != "0":
                    can_expand = True
                if "upnp:albumArtURI" in entry:
                    thumbnail = entry["upnp:albumArtURI"]["#text"]
            if entry_type == "item":
                track_number += 1

            play_uri = self.mk_play_uri(
                media_content_type, media_content_id, track_number
            )
            media_content_id += MEDIA_CONTENT_ID_SEP + play_uri

            browse_lst.append(
                BrowseMedia(
                    title=entry["dc:title"],
                    media_class="music",
                    media_content_id=media_content_id,
                    media_content_type=media_content_type,
                    can_play=can_play,
                    can_expand=can_expand,
                    thumbnail=thumbnail,
                )
            )
        return browse_lst

    def get_track_info(self, zone_room_lst):
        position_info = self.get_position_info(zone_room_lst)
        metadata_xml = position_info["TrackMetaData"]

        track_info = {
            "title": None,
            "artist": None,
            "image_uri": None,
            "album": None,
        }

        track_info["number"] = position_info["Track"]
        track_info["duration"] = self._timespan_secs(position_info["TrackDuration"])
        track_info["uri"] = position_info["TrackURI"]
        track_info["position"] = self._timespan_secs(position_info["AbsTime"])

        if metadata_xml is not None:
            metadata = xmltodict.parse(metadata_xml)
            if "dc:title" in metadata["DIDL-Lite"]["item"]:
                track_info["title"] = metadata["DIDL-Lite"]["item"]["dc:title"]
            if "upnp:artist" in metadata["DIDL-Lite"]["item"]:
                track_info["artist"] = metadata["DIDL-Lite"]["item"]["upnp:artist"]
            if "upnp:albumArtURI" in metadata["DIDL-Lite"]["item"]:
                if "#text" in metadata["DIDL-Lite"]["item"]["upnp:albumArtURI"]:
                    track_info["image_uri"] = metadata["DIDL-Lite"]["item"][
                        "upnp:albumArtURI"
                    ]["#text"]
            if "upnp:album" in metadata["DIDL-Lite"]["item"]:
                track_info["album"] = metadata["DIDL-Lite"]["item"]["upnp:album"]

        return track_info

    def mk_play_uri(self, media_type, media_id, track_number=0):
        if media_type == UPNP_CLASS_ALBUM or media_type == UPNP_CLASS_TRACK:
            media_server_udn = self.media_server_udn

            play_uri = (
                "dlna-playcontainer://"
                + urllib.parse.quote(media_server_udn)
                + "?sid="
                + urllib.parse.quote(URN_CONTENT_DIRECTORY)
                + "&cid="
            )

            if media_type == UPNP_CLASS_ALBUM:
                play_uri += urllib.parse.quote(media_id)
            elif media_type == UPNP_CLASS_TRACK:
                container_id = media_id.rsplit("/", 1)[0]
                play_uri += urllib.parse.quote(container_id)

            play_uri += "&md=0"

            if media_type == UPNP_CLASS_TRACK:
                track_number = str(track_number)
                play_uri += (
                    "&fid=" + urllib.parse.quote(media_id) + "&fii=" + track_number
                )

            return play_uri
        else:
            return media_id
