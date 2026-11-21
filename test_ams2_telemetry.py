"""Synthetic unit tests for the AMS2 shared-memory decoder."""
import struct
import unittest

from ams2_telemetry import (
    MINIMUM_PAGE_SIZE,
    OFF_ABS_ACTIVE,
    OFF_BRAKE,
    OFF_CAR_CLASS_NAME,
    OFF_CAR_NAME,
    OFF_GAME_STATE,
    OFF_SPEED_MS,
    OFF_SEQUENCE_NUMBER,
    OFF_THROTTLE,
    OFF_TYRE_RPS,
    OFF_VERSION,
    decode_ams2_page,
)


def make_page(version=14, game_state=2, sequence=2):
    raw = bytearray(MINIMUM_PAGE_SIZE)
    struct.pack_into("<I", raw, OFF_VERSION, version)
    struct.pack_into("<I", raw, OFF_GAME_STATE, game_state)
    struct.pack_into("<f", raw, OFF_SPEED_MS, 30.0)
    struct.pack_into("<f", raw, OFF_BRAKE, 0.8)
    struct.pack_into("<f", raw, OFF_THROTTLE, 0.1)
    struct.pack_into("<?", raw, OFF_ABS_ACTIVE, True)
    struct.pack_into("<4f", raw, OFF_TYRE_RPS, 40.0, 20.0, 40.0, 40.0)
    struct.pack_into("<I", raw, OFF_SEQUENCE_NUMBER, sequence)
    raw[OFF_CAR_NAME:OFF_CAR_NAME + 64] = b"Synthetic GT3\0".ljust(64, b"\0")
    raw[OFF_CAR_CLASS_NAME:OFF_CAR_CLASS_NAME + 64] = b"GT3\0".ljust(64, b"\0")
    return bytes(raw)


class AMS2DecoderTests(unittest.TestCase):
    def test_decodes_pedals_speed_and_wheels(self):
        data = decode_ams2_page(make_page())
        self.assertAlmostEqual(data["speed_kmh"], 108.0)
        self.assertAlmostEqual(data["brake"], 0.8)
        self.assertAlmostEqual(data["throttle"], 0.1)
        self.assertEqual(data["wheel_order"], ("FL", "FR", "RL", "RR"))
        self.assertEqual(data["wheel_slips"], (0.0, 0.5, 0.0, 0.0))
        self.assertTrue(data["abs_active"])
        self.assertEqual(data["vehicle_name"], "Synthetic GT3")
        self.assertEqual(data["vehicle_class"], "GT3")

    def test_rejects_unknown_shared_memory_version(self):
        with self.assertRaises(RuntimeError):
            decode_ams2_page(make_page(version=13))

    def test_ignores_non_driving_game_state(self):
        self.assertIsNone(decode_ams2_page(make_page(game_state=1)))

    def test_ignores_duplicate_sequence(self):
        self.assertIsNone(decode_ams2_page(make_page(sequence=2), previous_sequence=2))

    def test_ignores_odd_sequence(self):
        self.assertIsNone(decode_ams2_page(make_page(sequence=3)))


if __name__ == "__main__":
    unittest.main()
