"""Unit tests for IQS properties and diagnostics."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import EntityCategory

from custom_components.teufel_raumfeld.common import RaumfeldRoom as BaseRaumfeldRoom
from custom_components.teufel_raumfeld.const import DEVICE_MANUFACTURER, DOMAIN
from custom_components.teufel_raumfeld.media_player import RaumfeldGroup, RaumfeldRoom
from custom_components.teufel_raumfeld.number import RaumfeldRoomVolume
from custom_components.teufel_raumfeld.select import RaumfeldPowerState
from custom_components.teufel_raumfeld.sensor import RaumfeldSpeaker

# — helpers —


def _make_speaker():
    raumfeld = MagicMock()
    config = {
        "device_udn": "uuid:test",
        "device_name": "Test",
        "get_state": MagicMock(),
        "identifier": "test",
        "manufacturer": "Test",
        "model": "Test",
        "sensor_name": "SoftwareVersion",
        "sw_version": "1.0",
    }
    return RaumfeldSpeaker(raumfeld, config)


def _make_power_state():
    raumfeld = MagicMock()
    raumfeld.options = {}
    config = {"room_name": "Test", "sensor_name": "PowerState", "get_state": lambda r: "on"}
    return RaumfeldPowerState(raumfeld, config)


def _make_volume():
    raumfeld = MagicMock()
    raumfeld.options = {}
    config = {"room_name": "Test", "sensor_name": "Volume", "get_state": lambda r: 50}
    return RaumfeldRoomVolume(raumfeld, config)


def _make_media_group():
    raumfeld = MagicMock()
    raumfeld.options = {}
    return RaumfeldGroup(["Wohnzimmer", "Küche"], raumfeld)


def _make_media_room():
    raumfeld = MagicMock()
    raumfeld.options = {}
    return RaumfeldRoom("Wohnzimmer", raumfeld)


# — PARALLEL_UPDATES —

PARALLEL_CLASSES = [
    BaseRaumfeldRoom,
    RaumfeldGroup,
    RaumfeldRoom,
    RaumfeldSpeaker,
    RaumfeldPowerState,
    RaumfeldRoomVolume,
]


def test_all_entity_classes_have_parallel_updates():
    for cls in PARALLEL_CLASSES:
        assert cls.PARALLEL_UPDATES == 1, f"{cls.__name__} missing PARALLEL_UPDATES"


# — ENTITY CATEGORY —


def test_sensor_category_is_diagnostic():
    assert _make_speaker().entity_category == EntityCategory.DIAGNOSTIC


def test_select_category_is_config():
    assert _make_power_state().entity_category == EntityCategory.CONFIG


def test_number_category_is_config():
    assert _make_volume().entity_category == EntityCategory.CONFIG


def test_media_player_has_no_category():
    for entity in (_make_media_group(), _make_media_room()):
        assert entity.entity_category is None


# — DISABLED BY DEFAULT —


def test_sensor_disabled_by_default():
    assert _make_speaker().entity_registry_enabled_default is False


# — DEVICE INFO —


def test_device_info_on_media_player_group():
    group = _make_media_group()
    info = group.device_info
    assert info["identifiers"] == {(DOMAIN, group.unique_id)}
    assert info["manufacturer"] == DEVICE_MANUFACTURER
    assert info["model"] == "Raumfeld Zone"


def test_device_info_on_base_room():
    config = {"room_name": "Test Room", "sensor_name": "Volume", "get_state": lambda r: 50}
    entity = BaseRaumfeldRoom(config)
    info = entity.device_info
    assert info["identifiers"] == {(DOMAIN, "Test Room")}
    assert info["manufacturer"] == DEVICE_MANUFACTURER
    assert info["model"] == "Raumfeld Speaker"


# — DEVICE CLASS REMOVED —


def test_speaker_sensor_has_no_device_class():
    assert _make_speaker().device_class is None


# — DIAGNOSTICS —


class TestDiagnostics:
    """Tests for async_get_config_entry_diagnostics."""

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self):
        from custom_components.teufel_raumfeld.diagnostics import async_get_config_entry_diagnostics

        raumfeld = MagicMock()
        raumfeld.async_host_is_valid = AsyncMock(return_value=True)
        raumfeld.get_zones.return_value = [["Kitchen"]]
        raumfeld.get_rooms.return_value = ["Kitchen"]
        raumfeld.get_raumfeld_device_udns.return_value = ["uuid:1"]
        raumfeld.options = {"volume": 50}

        entry = MagicMock()
        entry.runtime_data = raumfeld
        entry.entry_id = "test-id"
        entry.data = {"host": "1.2.3.4", "port": "47365"}
        entry.options = {}
        entry.domain = "teufel_raumfeld"
        entry.title = "Test"

        result = await async_get_config_entry_diagnostics(MagicMock(), entry)

        assert result["host"]["valid"] is True
        assert result["zones"] == [["Kitchen"]]
        assert result["rooms"] == ["Kitchen"]
        assert result["devices"] == ["uuid:1"]
        assert result["entry"]["data"]["host"] == "**REDACTED**"
        assert result["entry"]["data"]["port"] == "**REDACTED**"

    @pytest.mark.asyncio
    async def test_host_unreachable_does_not_crash(self):
        from custom_components.teufel_raumfeld.diagnostics import async_get_config_entry_diagnostics

        raumfeld = MagicMock()
        raumfeld.async_host_is_valid = AsyncMock(side_effect=RuntimeError("boom"))
        raumfeld.get_zones.return_value = []
        raumfeld.get_rooms.return_value = []
        raumfeld.get_raumfeld_device_udns.return_value = []
        raumfeld.options = {}

        entry = MagicMock()
        entry.runtime_data = raumfeld
        entry.entry_id = "test-id"
        entry.data = {}
        entry.options = {}
        entry.domain = "teufel_raumfeld"
        entry.title = "Test"

        result = await async_get_config_entry_diagnostics(MagicMock(), entry)

        assert result["host"]["valid"] == "unknown"
