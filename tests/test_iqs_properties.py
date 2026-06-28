"""Unit tests for IQS properties: PARALLEL_UPDATES, entity_category, device_info, disabled-by-default.

These tests verify the class-level attributes set in PR #94.
No HA lifecycle needed — just instantiate or inspect.
"""

from unittest.mock import MagicMock

from homeassistant.const import EntityCategory

from custom_components.teufel_raumfeld.common import RaumfeldRoom as BaseRaumfeldRoom
from custom_components.teufel_raumfeld.const import DEVICE_MANUFACTURER, DOMAIN
from custom_components.teufel_raumfeld.media_player import RaumfeldGroup, RaumfeldRoom
from custom_components.teufel_raumfeld.number import RaumfeldRoomVolume
from custom_components.teufel_raumfeld.select import RaumfeldPowerState
from custom_components.teufel_raumfeld.sensor import RaumfeldSpeaker

# — helpers —


def _make_speaker():
    """Create a minimal RaumfeldSpeaker instance for property inspection."""
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


# — ENTITY CATEGORY (test instance properties, not _attr_*) —


def test_sensor_category_is_diagnostic():
    entity = _make_speaker()
    assert entity.entity_category == EntityCategory.DIAGNOSTIC


def test_select_category_is_config():
    entity = _make_power_state()
    assert entity.entity_category == EntityCategory.CONFIG


def test_number_category_is_config():
    entity = _make_volume()
    assert entity.entity_category == EntityCategory.CONFIG


def test_media_player_has_no_category():
    for entity in (_make_media_group(), _make_media_room()):
        assert entity.entity_category is None


# — DISABLED BY DEFAULT (test instance property) —


def test_sensor_disabled_by_default():
    entity = _make_speaker()
    assert entity.entity_registry_enabled_default is False


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
    entity = _make_speaker()
    assert entity.device_class is None
