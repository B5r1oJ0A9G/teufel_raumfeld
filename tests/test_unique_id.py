"""Tests for unique_id generation and backward compatibility."""

import base64
import json
import pickle

from custom_components.teufel_raumfeld.media_player import (
    UID_PREFIX,
    obj_to_uid,
    uid_to_obj,
)


class TestObjToUid:
    """Tests for the new obj_to_uid function."""

    def test_order_independent(self):
        """Same rooms in different order produce the same unique_id."""
        uid1 = obj_to_uid(["Wohnzimmer", "Küche", "Bad"])
        uid2 = obj_to_uid(["Bad", "Wohnzimmer", "Küche"])
        uid3 = obj_to_uid(["Küche", "Bad", "Wohnzimmer"])
        assert uid1 == uid2 == uid3

    def test_different_rooms_different_id(self):
        """Different room sets produce different unique_ids."""
        uid1 = obj_to_uid(["Wohnzimmer", "Küche"])
        uid2 = obj_to_uid(["Wohnzimmer", "Bad"])
        assert uid1 != uid2

    def test_has_v2_prefix(self):
        """New format IDs start with the v2: prefix."""
        uid = obj_to_uid(["Wohnzimmer"])
        assert uid.startswith(UID_PREFIX)

    def test_no_trailing_newline(self):
        """Unique IDs must not contain newlines (unlike the old pickle+encodebytes format)."""
        uid = obj_to_uid(["Wohnzimmer", "Küche"])
        assert "\n" not in uid

    def test_single_room(self):
        """Single-room group works correctly."""
        uid = obj_to_uid(["Wohnzimmer"])
        assert uid == UID_PREFIX + base64.b64encode(
            json.dumps(["Wohnzimmer"], sort_keys=True).encode()
        ).decode().strip()

    def test_empty_list(self):
        """Empty room list works correctly."""
        uid = obj_to_uid([])
        assert uid == UID_PREFIX + base64.b64encode(
            json.dumps([], sort_keys=True).encode()
        ).decode().strip()


class TestUidToObj:
    """Tests for uid_to_obj with both new and legacy formats."""

    def test_round_trip_new_format(self):
        """New format IDs round-trip correctly (sorted rooms returned)."""
        rooms = ["Wohnzimmer", "Küche", "Bad"]
        uid = obj_to_uid(rooms)
        result = uid_to_obj(uid)
        assert sorted(result) == sorted(rooms)

    def test_round_trip_single_room(self):
        """Single room round-trips correctly."""
        uid = obj_to_uid(["Wohnzimmer"])
        result = uid_to_obj(uid)
        assert result == ["Wohnzimmer"]

    def test_round_trip_empty(self):
        """Empty list round-trips correctly."""
        uid = obj_to_uid([])
        result = uid_to_obj(uid)
        assert result == []

    def test_legacy_pickle_format(self):
        """Legacy pickle-encoded unique_ids still decode correctly."""
        old_rooms = ["Wohnzimmer", "Küche"]
        old_pickle = pickle.dumps(old_rooms)
        old_uid = base64.encodebytes(old_pickle).decode()
        result = uid_to_obj(old_uid)
        assert result == old_rooms

    def test_legacy_pickle_single_room(self):
        """Legacy pickle-encoded single room still decodes."""
        old_uid = base64.encodebytes(pickle.dumps(["Wohnzimmer"])).decode()
        result = uid_to_obj(old_uid)
        assert result == ["Wohnzimmer"]

    def test_invalid_uid_returns_empty_list(self):
        """Completely invalid unique_id returns an empty list."""
        result = uid_to_obj("not_a_valid_uid_at_all_!@#$")
        assert result == []

    def test_new_format_preserves_sort_order(self):
        """New format always returns rooms in sorted order, regardless of input order."""
        uid = obj_to_uid(["Wohnzimmer", "Bad", "Küche"])
        result = uid_to_obj(uid)
        assert result == sorted(["Wohnzimmer", "Bad", "Küche"])


class TestBackwardCompatibility:
    """Integration tests for old-to-new migration scenarios."""

    def test_old_format_creates_different_ids_for_same_rooms_different_order(self):
        """Demonstrate the bug: old pickle format produces different IDs for same rooms in different order."""
        rooms_ab = ["A", "B"]
        rooms_ba = ["B", "A"]
        old_uid_ab = base64.encodebytes(pickle.dumps(rooms_ab)).decode()
        old_uid_ba = base64.encodebytes(pickle.dumps(rooms_ba)).decode()
        assert old_uid_ab != old_uid_ba  # This is the bug the new format fixes

    def test_new_format_fixes_ordering_bug(self):
        """New format: same rooms always produce same ID regardless of order."""
        uid_ab = obj_to_uid(["A", "B"])
        uid_ba = obj_to_uid(["B", "A"])
        assert uid_ab == uid_ba

    def test_old_entities_migrate_correctly(self):
        """Existing old-format entities in the registry still resolve correctly."""
        # Simulate an old-format entity in the registry
        old_rooms = ["Wohnzimmer", "Küche", "Bad"]
        old_uid = base64.encodebytes(pickle.dumps(old_rooms)).decode()

        # The new uid_to_obj should decode it
        result = uid_to_obj(old_uid)
        assert sorted(result) == sorted(old_rooms)

    def test_new_entity_can_replace_old(self):
        """A new-format entity for the same rooms coexists with old format."""
        old_rooms = ["Wohnzimmer", "Küche"]
        old_uid = base64.encodebytes(pickle.dumps(old_rooms)).decode()
        new_uid = obj_to_uid(old_rooms)

        # Both decode to the same rooms
        assert sorted(uid_to_obj(old_uid)) == sorted(uid_to_obj(new_uid))
