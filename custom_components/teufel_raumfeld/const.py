"""Constants for the Teufel Raumfeld integration."""
from enum import IntFlag

ATTR_EVENT_WSUPD_TYPE = "type"
DEFAULT_ANNOUNCEMENT_VOLUME = 40
DEFAULT_CHANGE_STEP_VOLUME_DOWN = 2
DEFAULT_CHANGE_STEP_VOLUME_UP = 5
DEFAULT_HOST_WEBSERVICE = "raumfeld-host.example.com"
DEFAULT_PORT_WEBSERVICE = "47365"
DEFAULT_VOLUME = 25
DELAY_FAST_UPDATE_CHECKS = 0.3
DELAY_MODERATE_UPDATE_CHECKS = 1
DELAY_POWER_STATE_UPDATE = 2
DEVICE_MANUFACTURER = "Teufel Audio GmbH"
DIDL_ATTR_ID = "@id"
DIDL_ATTR_CHILD_CNT = "@childCount"
DIDL_ELEM_ARTIST = "upnp:artist"
DIDL_ELEM_ART_URI = "upnp:albumArtURI"
DIDL_ELEM_CLASS = "upnp:class"
DIDL_ELEM_CONTAINER = "container"
DIDL_ELEM_ITEM = "item"
DIDL_ELEM_TITLE = "dc:title"
DIDL_ELEM_ALBUM = "upnp:album"
DIDL_ELEMENT = "DIDL-Lite"
DIDL_VALUE = "#text"
DOMAIN = "teufel_raumfeld"
EVENT_WEBSERVICE_UPDATE = "teufel_raumfeld.webservice_update"
GROUP_PREFIX = "Group: "
MEDIA_CONTENT_ID_SEP = "[:sep:]"
MESSAGE_PHASE_ALPHA = (
    "You are using teufel_raumfeld, which is still in alpha phase and therefore subject to change."
    " This includes, among other things, the addition, redesign or removal of functionality."
)
NUMBER_ROOM_VOLUME_ICON = "mdi:volume-high"
NUMBER_ROOM_VOLUME_NAME = "Volume"
OBJECT_ID_LINE_IN = "0/Line In"
OPTION_ANNOUNCEMENT_VOLUME = "announcement_volume"
OPTION_CHANGE_STEP_VOLUME_DOWN = "change_step_volume_down"
OPTION_CHANGE_STEP_VOLUME_UP = "change_step_volume_up"
OPTION_DEFAULT_VOLUME = "default_volume"
OPTION_FIXED_ANNOUNCEMENT_VOLUME = "fixed_announcement_volume"
OPTION_USE_DEFAULT_VOLUME = "use_default_volume"
PLATFORMS = ["media_player", "sensor", "select", "number"]
PORT_LINE_IN = 8888
POSINF_ELEM_ABS_TIME = "AbsTime"
POSINF_ELEM_DURATION = "TrackDuration"
POSINF_ELEM_TRACK = "Track"
POSINF_ELEM_TRACK_DATA = "TrackMetaData"
POSINF_ELEM_URI = "TrackURI"
POWER_ECO = "eco"
POWER_ON = "on"
POWER_STANDBY = "off"
ROOM_PREFIX = "Room: "
SERVICE_GROUP = "group"
SERVICE_ABS_VOLUME_SET = "abs_volume_set"
SERVICE_ADD_ROOM = "add_room"
SERVICE_SET_ROOM_VOLUME = "set_room_volume"
SERVICE_PAR_ROOM = "room"
SERVICE_PAR_VOLUME = "volume"
SERVICE_PAR_MEMBER = "room_of_group"
SERVICE_DROP_ROOM = "drop_room"
SERVICE_PLAY_SYSTEM_SOUND = "play_sound"
SERVICE_RESTORE = "restore"
SERVICE_SNAPSHOT = "snapshot"
TIMEOUT_TRANSITION_PERIOD = 5
TIMEOUT_HOST_VALIDATION = 30
TITLE_UNKNOWN = "Unkown title (Teufel Raumfeld)"
TRACKINF_ALBUM = "album"
TRACKINF_ARTIST = "artist"
TRACKINF_IMGURI = "image_uri"
TRACKINF_TITLE = "title"
UNSUPPORTED_OBJECT_IDS = [
    "0/My Music/Search",
    "0/Playlists/Shuffles",
    "0/Renderers",
    "0/Spotify",
    "0/Tidal/Search",
    "0/RadioTime/Search",
    "0/Zones",
]
UPNP_CLASS_ALBUM = "object.container.album.musicAlbum"
UPNP_CLASS_TRACK = "object.item.audioItem.musicTrack"
UPNP_CLASS_RADIO = "object.item.audioItem.audioBroadcast.radio"
UPNP_CLASS_PLAYLIST_CONTAINER = "object.container.playlistContainer"
UPNP_CLASS_PODCAST_EPISODE = "object.item.audioItem.podcastEpisode"
UPNP_CLASS_LINE_IN = "object.item.audioItem.audioBroadcast.lineIn"
UPNP_CLASS_AUDIO_ITEM = "object.item.audioItem"
URN_CONTENT_DIRECTORY = "urn:upnp-org:serviceId:ContentDirectory"
