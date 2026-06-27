"""Tests for RaumfeldGroup and RaumfeldRoom media player entities."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.teufel_raumfeld.const import (
    OPTION_CHANGE_STEP_VOLUME_DOWN,
    OPTION_CHANGE_STEP_VOLUME_UP,
)
from custom_components.teufel_raumfeld.media_player import (
    SUPPORT_RAUMFELD_GROUP,
    SUPPORT_RAUMFELD_ROOM,
    RaumfeldGroup,
    RaumfeldRoom,
)


class TestRaumfeldGroupCore:
    """Tests for RaumfeldGroup basic properties and initialization."""

    def setup_method(self):
        self.rooms = ["Wohnzimmer", "Küche"]
        self.raumfeld = MagicMock()
        self.raumfeld.options = {}
        self.group = RaumfeldGroup(self.rooms, self.raumfeld)

    def test_name_prefixed_with_group(self):
        assert self.group.name.startswith("Group: ")

    def test_unique_id_is_stable(self):
        uid = self.group.unique_id
        assert uid.startswith("v2:")

    def test_device_class_is_speaker(self):
        assert self.group.device_class == "speaker"

    def test_icon_is_multiple_speakers(self):
        assert "multiple" in self.group.icon

    def test_supported_features(self):
        assert self.group.supported_features == SUPPORT_RAUMFELD_GROUP

    def test_group_members_returns_rooms(self):
        assert self.group.group_members == self.rooms

    def test_state_defaults_none(self):
        assert self.group.state is None


class TestRaumfeldGroupVolume:
    """Tests for volume-related methods, mocking update chain."""

    def setup_method(self):
        self.rooms = ["Wohnzimmer"]
        self.raumfeld = MagicMock()
        self.raumfeld.options = {
            OPTION_CHANGE_STEP_VOLUME_UP: 5,
            OPTION_CHANGE_STEP_VOLUME_DOWN: 2,
        }
        self.group = RaumfeldGroup(self.rooms, self.raumfeld)

    @pytest.mark.asyncio
    async def test_volume_up_calls_change_group_volume(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_change_group_volume = AsyncMock()
        self.group.async_update_volume_level = AsyncMock()

        await self.group.async_volume_up()

        self.raumfeld.async_change_group_volume.assert_called_once_with(
            self.rooms, 5
        )

    @pytest.mark.asyncio
    async def test_volume_down_calls_change_group_volume(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_change_group_volume = AsyncMock()
        self.group.async_update_volume_level = AsyncMock()

        await self.group.async_volume_down()

        self.raumfeld.async_change_group_volume.assert_called_once_with(
            self.rooms, -2
        )

    @pytest.mark.asyncio
    async def test_volume_up_invalid_group_logs(self):
        self.raumfeld.group_is_valid.return_value = False

        await self.group.async_volume_up()
        # Should not crash, just log debug

    @pytest.mark.asyncio
    async def test_set_volume_level(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_set_group_volume = AsyncMock()
        self.group.async_update_volume_level = AsyncMock()

        await self.group.async_set_volume_level(0.75)

        self.raumfeld.async_set_group_volume.assert_called_once_with(
            self.rooms, 75
        )


class TestRaumfeldGroupMute:
    """Tests for mute-related methods."""

    def setup_method(self):
        self.rooms = ["Wohnzimmer"]
        self.raumfeld = MagicMock()
        self.raumfeld.options = {}
        self.group = RaumfeldGroup(self.rooms, self.raumfeld)

    @pytest.mark.asyncio
    async def test_mute_true(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_set_group_mute = AsyncMock()
        self.group.async_update_mute = AsyncMock()

        await self.group.async_mute_volume(True)

        self.raumfeld.async_set_group_mute.assert_called_once_with(
            self.rooms, True
        )

    @pytest.mark.asyncio
    async def test_mute_false(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_set_group_mute = AsyncMock()
        self.group.async_update_mute = AsyncMock()

        await self.group.async_mute_volume(False)

        self.raumfeld.async_set_group_mute.assert_called_once_with(
            self.rooms, False
        )


class TestRaumfeldGroupTransport:
    """Tests for transport control methods."""

    def setup_method(self):
        self.rooms = ["Wohnzimmer"]
        self.raumfeld = MagicMock()
        self.raumfeld.options = {}
        self.group = RaumfeldGroup(self.rooms, self.raumfeld)

    @pytest.mark.asyncio
    async def test_media_play(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_group_play = AsyncMock()
        self.group.async_update_transport_state = AsyncMock()

        await self.group.async_media_play()
        self.raumfeld.async_group_play.assert_called_once_with(self.rooms)

    @pytest.mark.asyncio
    async def test_media_pause(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_group_pause = AsyncMock()
        self.group.async_update_transport_state = AsyncMock()

        await self.group.async_media_pause()
        self.raumfeld.async_group_pause.assert_called_once_with(self.rooms)

    @pytest.mark.asyncio
    async def test_media_stop(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_group_stop = AsyncMock()
        self.group.async_update_transport_state = AsyncMock()

        await self.group.async_media_stop()
        self.raumfeld.async_group_stop.assert_called_once_with(self.rooms)

    @pytest.mark.asyncio
    async def test_media_previous_track(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_group_previous_track = AsyncMock()
        self.group.async_update_track_info = AsyncMock()

        await self.group.async_media_previous_track()
        self.raumfeld.async_group_previous_track.assert_called_once_with(self.rooms)

    @pytest.mark.asyncio
    async def test_media_next_track(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_group_next_track = AsyncMock()
        self.group.async_update_track_info = AsyncMock()

        await self.group.async_media_next_track()
        self.raumfeld.async_group_next_track.assert_called_once_with(self.rooms)

    @pytest.mark.asyncio
    async def test_media_seek(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_group_seek = AsyncMock()
        self.group.async_update_track_info = AsyncMock()

        await self.group.async_media_seek(120)
        self.raumfeld.async_group_seek.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_group_no_crash(self):
        """Methods called on invalid group should log debug, not crash."""
        self.raumfeld.group_is_valid.return_value = False
        self.group.async_update_transport_state = AsyncMock()
        self.group.async_update_track_info = AsyncMock()

        await self.group.async_media_play()
        await self.group.async_media_pause()
        await self.group.async_media_stop()
        await self.group.async_media_previous_track()
        await self.group.async_media_next_track()
        await self.group.async_media_seek(120)
        # None of these should raise


class TestRaumfeldGroupSnapshot:
    """Tests for snapshot/restore methods."""

    def setup_method(self):
        self.rooms = ["Wohnzimmer"]
        self.raumfeld = MagicMock()
        self.raumfeld.options = {}
        self.group = RaumfeldGroup(self.rooms, self.raumfeld)

    @pytest.mark.asyncio
    async def test_snapshot(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_save_group = AsyncMock()

        await self.group.async_snapshot()

        self.raumfeld.async_save_group.assert_called_once_with(self.rooms)

    @pytest.mark.asyncio
    async def test_restore(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_restore_group = AsyncMock()

        await self.group.async_restore()

        self.raumfeld.async_restore_group.assert_called_once_with(self.rooms)


class TestRaumfeldRoom:
    """Tests for RaumfeldRoom (single-room media player)."""

    def setup_method(self):
        self.room = "Wohnzimmer"
        self.raumfeld = MagicMock()
        self.raumfeld.options = {}
        self.room_entity = RaumfeldRoom(self.room, self.raumfeld)

    def test_name_prefixed_with_room(self):
        assert self.room_entity.name.startswith("Room: ")

    def test_icon_is_single_speaker(self):
        assert self.room_entity.icon == "mdi:speaker"

    def test_supported_features_includes_grouping(self):
        assert self.room_entity.supported_features == SUPPORT_RAUMFELD_ROOM

    def test_group_members_returns_single_room(self):
        assert self.room_entity.group_members == [self.room]

    @pytest.mark.asyncio
    async def test_unjoin_player_valid(self):
        """Unjoining a player when group is invalid (= standalone room)."""
        self.raumfeld.group_is_valid.return_value = False
        self.raumfeld.async_drop_room_from_group = AsyncMock()
        self.room_entity.async_update_transport_state = AsyncMock()

        await self.room_entity.async_unjoin_player()
        self.raumfeld.async_drop_room_from_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_join_players(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.eid_to_obj = {"media_player.kueche": ["Küche"]}
        self.raumfeld.async_add_rooms_to_group = AsyncMock()
        self.room_entity.async_update_transport_state = AsyncMock()

        await self.room_entity.async_join_players(["media_player.kueche"])
        self.raumfeld.async_add_rooms_to_group.assert_called_once()


class TestPlaySystemSound:
    """Tests for the play_system_sound service method."""

    def setup_method(self):
        self.rooms = ["Wohnzimmer", "Küche"]
        self.raumfeld = MagicMock()
        self.raumfeld.options = {}
        self.group = RaumfeldGroup(self.rooms, self.raumfeld)

    @pytest.mark.asyncio
    async def test_play_system_sound_on_all_rooms(self):
        self.raumfeld.group_is_valid.return_value = True
        self.raumfeld.async_room_play_system_sound = AsyncMock()

        await self.group.async_play_system_sound(sound="Success")

        assert self.raumfeld.async_room_play_system_sound.call_count == 2
        calls = self.raumfeld.async_room_play_system_sound.call_args_list
        assert calls[0][0] == ("Wohnzimmer", "Success")
        assert calls[1][0] == ("Küche", "Success")
