"""Tests for media browser TypeError fix (Issue #67)."""

from unittest.mock import AsyncMock

import pytest

from custom_components.teufel_raumfeld.__init__ import HassRaumfeldHost
from custom_components.teufel_raumfeld.const import MEDIA_CONTENT_ID_SEP


class TestAsyncBrowseMedia:
    """Test that async_browse_media handles None media_xml gracefully."""

    @pytest.mark.asyncio
    async def test_browse_media_returns_empty_list_when_server_returns_none(self):
        """When UPnP browse returns None, the method should return an empty list instead of crashing."""
        host = HassRaumfeldHost(host="127.0.0.1")
        host.async_browse_media_server = AsyncMock(return_value=None)

        result = await host.async_browse_media(object_id="0")

        assert result == []
        host.async_browse_media_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_browse_media_with_object_id_containing_separator(self):
        """Object ID with separator should be split correctly before browse."""
        host = HassRaumfeldHost(host="127.0.0.1")
        host.async_browse_media_server = AsyncMock(return_value=None)

        result = await host.async_browse_media(
            object_id=f"0/My Music{MEDIA_CONTENT_ID_SEP}some_uri"
        )

        assert result == []
        # Should have called browse with the part before the separator
        called_oid = host.async_browse_media_server.call_args[0][0]
        assert called_oid == "0/My Music"
