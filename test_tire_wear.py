"""Synthetic tests for normalized per-wheel tyre-wear telemetry."""
import ast
import struct
import unittest
from pathlib import Path

from ams2_telemetry import (
    MINIMUM_PAGE_SIZE, OFF_VERSION, OFF_GAME_STATE, OFF_SPEED_MS, OFF_BRAKE,
    OFF_THROTTLE, OFF_ABS_ACTIVE, OFF_TYRE_RPS, OFF_TYRE_WEAR,
    OFF_SEQUENCE_NUMBER, decode_ams2_page,
)
from iracing_telemetry import WEAR_VARIABLES, decode_iracing_values
from f1_26_telemetry import (
    HEADER_SIZE, CAR_DAMAGE_SIZE, CAR_DAMAGE_PACKET_SIZE,
    decode_car_damage,
)


def load_warning_function():
    source = Path(__file__).with_name("PHF_controller.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "compute_progressive_warning")
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 "PHF_controller.py", "exec"), namespace)
    return namespace["compute_progressive_warning"]


class WearTelemetryTests(unittest.TestCase):
    def test_ams2_wear_is_fraction_worn(self):
        raw = bytearray(MINIMUM_PAGE_SIZE)
        struct.pack_into("<I", raw, OFF_VERSION, 14)
        struct.pack_into("<I", raw, OFF_GAME_STATE, 2)
        struct.pack_into("<f", raw, OFF_SPEED_MS, 30.0)
        struct.pack_into("<f", raw, OFF_BRAKE, 0.5)
        struct.pack_into("<f", raw, OFF_THROTTLE, 0.0)
        struct.pack_into("<?", raw, OFF_ABS_ACTIVE, False)
        struct.pack_into("<4f", raw, OFF_TYRE_RPS, 30, 30, 30, 30)
        struct.pack_into("<4f", raw, OFF_TYRE_WEAR, 0.0, 0.1, 0.5, 1.0)
        struct.pack_into("<I", raw, OFF_SEQUENCE_NUMBER, 2)
        data = decode_ams2_page(bytes(raw))
        for actual, expected in zip(data["wheel_wear"], (0.0, 0.1, 0.5, 1.0)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_iracing_percent_remaining_is_inverted(self):
        values = {"Speed": 30.0, "Brake": 0.5, "Throttle": 0.0,
                  "LFspeed": 30.0, "RFspeed": 30.0, "LRspeed": 30.0, "RRspeed": 30.0}
        for i, name in enumerate(WEAR_VARIABLES):
            # Three zones per wheel; each corner receives 100, 90, 80, or 70% remaining.
            corner_index = ("LF", "RF", "LR", "RR").index(name[:2])
            values[name] = (100, 90, 80, 70)[corner_index]
        data = decode_iracing_values(values)
        for actual, expected in zip(data["wheel_wear"], (0.0, 0.1, 0.2, 0.3)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_wear_coefficient_increases_warning_when_wear_increases(self):
        compute = load_warning_function()
        advanced = {
            "warning_min_speed_kmh": 0.0,
            "warning_grip_coefficient": 0.0,
            "warning_wear_coefficient": 1.0,
            "warning_onset_intercept": 45.0,
            "warning_max_speed_kmh": 250.0,
            "warning_max_intercept": 60.0,
            "warning_max_slope": 0.2,
        }
        args = dict(brake_demand=0.75, speed_kmh=100.0, wheel_slips=(0, 0, 0, 0),
                    advanced=advanced, max_intensity=100.0)
        fresh = compute(**args, wheel_wear=(0, 0, 0, 0))
        worn = compute(**args, wheel_wear=(0, 0, 0, 1))
        self.assertGreater(worn, fresh)

    def test_zero_wear_coefficient_is_neutral(self):
        compute = load_warning_function()
        advanced = {
            "warning_min_speed_kmh": 0.0,
            "warning_grip_coefficient": 0.0,
            "warning_wear_coefficient": 0.0,
            "warning_onset_intercept": 45.0,
            "warning_max_speed_kmh": 250.0,
            "warning_max_intercept": 60.0,
            "warning_max_slope": 0.2,
        }
        args = dict(brake_demand=0.75, speed_kmh=100.0, wheel_slips=(0, 0, 0, 0),
                    advanced=advanced, max_intensity=100.0)
        no_data = compute(**args, wheel_wear=())
        worn = compute(**args, wheel_wear=(0, 0, 0, 1))
        self.assertAlmostEqual(no_data, worn)

    def test_f1_26_car_damage_packet(self):
        packet = bytearray(CAR_DAMAGE_PACKET_SIZE)
        struct.pack_into("<H", packet, 0, 2026)
        packet[5] = 1  # packet version
        packet[6] = 10 # Car Damage
        struct.pack_into("<I", packet, 19, 1234)  # frame identifier
        packet[27] = 2  # player car index
        base = HEADER_SIZE + 2 * CAR_DAMAGE_SIZE
        struct.pack_into("<4f", packet, base, 0.0, 25.0, 50.0, 100.0)
        data = decode_car_damage(bytes(packet))
        self.assertEqual(data["frame_id"], 1234)
        self.assertEqual(data["wheel_wear"], (0.0, 0.25, 0.5, 1.0))


if __name__ == "__main__":
    unittest.main()
