import unittest

from acc_telemetry import calculate_braking_slip


class TestACCSlipCalculation(unittest.TestCase):
    def test_braking_slip_is_positive_magnitude(self):
        values = calculate_braking_slip((-0.05, -0.10, -1.0, 0.0))
        self.assertEqual(values, (0.05, 0.10, 1.0, 0.0))

    def test_acceleration_slip_is_ignored(self):
        self.assertEqual(
            calculate_braking_slip((0.2, 0.5, 0.0, -0.1)),
            (0.0, 0.0, 0.0, 0.1),
        )

    def test_values_are_bounded(self):
        self.assertEqual(
            calculate_braking_slip((-2.0, 2.0, -0.4, float("nan"))),
            (1.0, 0.0, 0.4, 0.0),
        )

    def test_requires_four_wheels(self):
        with self.assertRaises(ValueError):
            calculate_braking_slip((-0.1, -0.2, -0.3))


if __name__ == "__main__":
    unittest.main()
