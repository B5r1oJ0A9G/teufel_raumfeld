"""Constants for the Teufel Raumfeld integration."""
CHANGE_STEP_VOLUME_DOWN = -2
CHANGE_STEP_VOLUME_UP = 5
DEVICE_CLASS_SPEAKER = "speaker"
DEVICE_MANUFACTURER = "Teufel Audio GmbH"
DOMAIN = "teufel_raumfeld"
DEFAULT_HOST_WEBSERVICE = "raumfeld-host.example.com"
DEFAULT_PORT_WEBSERVICE = "47365"
GROUP_PREFIX = "Group: "
PLATFORMS = ["media_player"]
ROOM_PREFIX = "Room: "
SERVICE_SNAPSHOT = "snapshot"
SERVICE_RESTORE = "restore"
UPNP_CLASS_ALBUM = "object.container.album.musicAlbum"
UPNP_CLASS_TRACK = "object.item.audioItem.musicTrack"
URN_CONTENT_DIRECTORY = "urn:upnp-org:serviceId:ContentDirectory"
MEDIA_CONTENT_ID_SEP = "[:sep:]"
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
