"""Constants for the Teufel Raumfeld integration."""
CHANGE_STEP_VOLUME_DOWN = -2
CHANGE_STEP_VOLUME_UP = 5
DEFAULT_HOST_WEBSERVICE = "raumfeld-host.example.com"
DEFAULT_PORT_WEBSERVICE = "47365"
DEVICE_CLASS_SPEAKER = "speaker"
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
GROUP_PREFIX = "Group: "
MEDIA_CONTENT_ID_SEP = "[:sep:]"
PLATFORMS = ["media_player"]
POSINF_ELEM_ABS_TIME = "AbsTime"
POSINF_ELEM_DURATION = "TrackDuration"
POSINF_ELEM_TRACK = "Track"
POSINF_ELEM_TRACK_DATA = "TrackMetaData"
POSINF_ELEM_URI = "TrackURI"
ROOM_PREFIX = "Room: "
SERVICE_GROUP = "group"
SERVICE_RESTORE = "restore"
SERVICE_SNAPSHOT = "snapshot"
SUPPORTED_OBJECT_IDS = ["0", "0/DemoTracks", "0/My Music"]
SUPPORTED_OBJECT_PREFIXES = [
    "0/My Music/Artists",
    "0/My Music/Albums",
    "0/My Music/Genres",
    "0/My Music/Composers",
    "0/My Music/ByFolder",
    "0/My Music/RecentlyAdded",
    "0/My Music/AllTracks",
    "0/DemoTracks",
]
TRACKINF_ALBUM = "album"
TRACKINF_ARTIST = "artist"
TRACKINF_IMGURI = "image_uri"
TRACKINF_TITLE = "title"
UPNP_CLASS_ALBUM = "object.container.album.musicAlbum"
UPNP_CLASS_TRACK = "object.item.audioItem.musicTrack"
URN_CONTENT_DIRECTORY = "urn:upnp-org:serviceId:ContentDirectory"
