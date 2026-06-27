"""Tests for teufel_raumfeld __init__ module — utility functions and HassRaumfeldHost."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.teufel_raumfeld.__init__ import (
    HassRaumfeldHost,
    is_supported_oid,
    timespan_secs,
)
from custom_components.teufel_raumfeld.const import (
    MEDIA_CONTENT_ID_SEP,
    OBJECT_ID_LINE_IN,
    PORT_LINE_IN,
    TITLE_UNKNOWN,
    UPNP_CLASS_ALBUM,
    UPNP_CLASS_AUDIO_ITEM,
    UPNP_CLASS_LINE_IN,
    UPNP_CLASS_PLAYLIST_CONTAINER,
    UPNP_CLASS_PODCAST_EPISODE,
    UPNP_CLASS_RADIO,
    UPNP_CLASS_TRACK,
)


class TestTimespanSecs:
    """Tests for timespan_secs — parsing H:MM:SS / MM:SS / SS strings."""

    def test_full_hms(self):
        assert timespan_secs("1:02:03") == 3723

    def test_minutes_seconds(self):
        assert timespan_secs("05:30") == 330

    def test_seconds_only(self):
        assert timespan_secs("42") == 42

    def test_zero(self):
        assert timespan_secs("0:00:00") == 0

    def test_leading_zeroes(self):
        assert timespan_secs("00:01:05") == 65


class TestIsSupportedOid:
    """Tests for is_supported_oid."""

    def test_normal_oid(self):
        assert is_supported_oid("0/My Music/Albums") is True

    def test_unsupported_search_oid(self):
        assert is_supported_oid("0/My Music/Search") is False

    def test_unsupported_spotify_oid(self):
        assert is_supported_oid("0/Spotify") is False

    def test_unsupported_zones_oid(self):
        assert is_supported_oid("0/Zones") is False

    def test_unsupported_renderers_oid(self):
        assert is_supported_oid("0/Renderers") is False

    def test_unsupported_shuffles_oid(self):
        assert is_supported_oid("0/Playlists/Shuffles") is False

    def test_unsupported_tidal_search(self):
        assert is_supported_oid("0/Tidal/Search") is False

    def test_unsupported_radiotime_search(self):
        assert is_supported_oid("0/RadioTime/Search") is False


class TestMkPlayUri:
    """Tests for HassRaumfeldHost.mk_play_uri — synchronous, needs mock session."""

    def setup_method(self):
        mock_session = MagicMock()
        self.host = HassRaumfeldHost(host="127.0.0.1", session=mock_session)
        self.host.media_server_udn = "uuid:test-ms-udn"

    def test_album_uri(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn, UPNP_CLASS_ALBUM, "0/My Music/Albums/Test"
        )
        assert uri is not None
        assert uri.startswith("dlna-playcontainer://")

    def test_playlist_container_uri(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn,
            UPNP_CLASS_PLAYLIST_CONTAINER,
            "0/Playlists/MyList",
        )
        assert uri is not None
        assert uri.startswith("dlna-playcontainer://")

    def test_track_uri_has_fid(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn, UPNP_CLASS_TRACK, "0/My Music/Albums/Test/1.mp3"
        )
        assert "&fid=" in uri

    def test_podcast_episode_has_fid(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn,
            UPNP_CLASS_PODCAST_EPISODE,
            "0/Podcasts/Show/Episode1",
        )
        assert "&fid=" in uri

    def test_radio_uri(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn, UPNP_CLASS_RADIO, "0/RadioTime/Stations/WDR2"
        )
        assert uri.startswith("dlna-playsingle://")
        assert "&iid=" in uri

    def test_line_in_uri(self):
        encoded_udn = "uuid%3Atest-device-udn"
        oid = f"{OBJECT_ID_LINE_IN}/{encoded_udn}"
        self.host.device_udn_to_location = MagicMock(return_value="http://10.0.0.5:47365")
        uri = self.host.mk_play_uri(self.host.media_server_udn, UPNP_CLASS_LINE_IN, oid)
        assert uri is not None
        assert f":{PORT_LINE_IN}/stream.flac" in uri

    def test_line_in_non_matching_oid_returns_none(self):
        self.host.device_udn_to_location = MagicMock()
        uri = self.host.mk_play_uri(
            self.host.media_server_udn, UPNP_CLASS_LINE_IN, "0/SomeOther"
        )
        assert uri is None

    def test_audio_item_fallback(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn, UPNP_CLASS_AUDIO_ITEM, "some_id"
        )
        assert uri == "some_id"

    def test_album_uri_correct_params(self):
        uri = self.host.mk_play_uri(
            self.host.media_server_udn, UPNP_CLASS_ALBUM, "0/Albums/5"
        )
        assert "?sid=" in uri
        assert "&cid=" in uri
        assert "&md=0" in uri


class TestAsyncBrowseMedia:
    """Tests for HassRaumfeldHost.async_browse_media."""

    def setup_method(self):
        mock_session = MagicMock()
        self.host = HassRaumfeldHost(host="127.0.0.1", session=mock_session)

    @pytest.mark.asyncio
    async def test_empty_when_none(self):
        self.host.async_browse_media_server = AsyncMock(return_value=None)
        result = await self.host.async_browse_media(object_id="0")
        assert result == []

    @pytest.mark.asyncio
    async def test_separator_stripped(self):
        self.host.async_browse_media_server = AsyncMock(return_value=None)
        await self.host.async_browse_media(
            object_id=f"0/My Music{MEDIA_CONTENT_ID_SEP}dlna-playsingle://..."
        )
        called_oid = self.host.async_browse_media_server.call_args[0][0]
        assert called_oid == "0/My Music"

    @pytest.mark.asyncio
    async def test_containers_and_items(self):
        didl_xml = (
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/"'
            ' xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">'
            '<container id="0/My Music" childCount="5" restricted="1">'
            "<dc:title>My Music</dc:title>"
            '<upnp:class>object.container.storageFolder</upnp:class>'
            "</container>"
            '<item id="0/My Music/Track1.mp3" restricted="1">'
            "<dc:title>Test Track</dc:title>"
            '<upnp:class>object.item.audioItem.musicTrack</upnp:class>'
            "</item>"
            "</DIDL-Lite>"
        )
        self.host.async_browse_media_server = AsyncMock(return_value=didl_xml)
        self.host.media_server_udn = "uuid:test"
        self.host.mk_play_uri = MagicMock(return_value="dlna-playcontainer://test")

        result = await self.host.async_browse_media(object_id="0")

        assert len(result) == 2
        assert result[0].title == "My Music"
        assert result[0].can_expand is True
        assert result[1].title == "Test Track"
        assert result[1].can_expand is False

    @pytest.mark.asyncio
    async def test_skips_unsupported_oids(self):
        didl_xml = (
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/"'
            ' xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">'
            '<container id="0/My Music/Search" childCount="0" restricted="1">'
            "<dc:title>Search</dc:title>"
            '<upnp:class>object.container</upnp:class>'
            "</container>"
            '<item id="0/My Music/Track1.mp3" restricted="1">'
            "<dc:title>Valid Track</dc:title>"
            '<upnp:class>object.item.audioItem.musicTrack</upnp:class>'
            "</item>"
            "</DIDL-Lite>"
        )
        self.host.async_browse_media_server = AsyncMock(return_value=didl_xml)
        self.host.media_server_udn = "uuid:test"
        self.host.mk_play_uri = MagicMock(return_value="dlna-playsingle://test")

        result = await self.host.async_browse_media(object_id="0")
        assert len(result) == 1
        assert result[0].title == "Valid Track"

    @pytest.mark.asyncio
    async def test_entry_without_title(self):
        didl_xml = (
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/"'
            ' xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">'
            '<container id="0/My Music" childCount="5" restricted="1">'
            '<upnp:class>object.container.storageFolder</upnp:class>'
            "</container>"
            "</DIDL-Lite>"
        )
        self.host.async_browse_media_server = AsyncMock(return_value=didl_xml)
        self.host.media_server_udn = "uuid:test"
        self.host.mk_play_uri = MagicMock(return_value="dlna-playsingle://test")

        result = await self.host.async_browse_media(object_id="0")
        assert len(result) == 1
        assert result[0].title == TITLE_UNKNOWN
