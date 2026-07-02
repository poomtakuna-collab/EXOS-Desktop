from __future__ import annotations

import unittest

from src.analysis.poom_combo import (
    POOMComboParameters,
    analyze_poom_combo,
    calculate_poom_combo_snapshot,
)


class POOMComboTest(unittest.TestCase):
    def test_default_parameters_match_pine_inputs(self) -> None:
        params = POOMComboParameters()

        self.assertEqual(params.ewFast, 5)
        self.assertEqual(params.ewSlow, 35)
        self.assertEqual(params.scaleFactor, 200)
        self.assertEqual(params.vpLen, 20)
        self.assertEqual(params.vpSmooth1, 5)
        self.assertEqual(params.vpSmooth2, 8)
        self.assertEqual(params.tsLen, 20)
        self.assertEqual(params.tsLookback, 10)
        self.assertEqual(params.tsSmooth, 5)
        self.assertEqual(params.tsScale, 1.5)
        self.assertEqual(params.bbLen, 20)
        self.assertEqual(params.bbMult, 2.0)
        self.assertEqual(params.kcMult, 1.5)
        self.assertEqual(params.msbLeft, 2)
        self.assertEqual(params.msbRight, 2)

    def test_positive_trend_window_calculates_core_poom_values(self) -> None:
        rows = [
            {
                "open": 100.0 + index,
                "high": 102.0 + index,
                "low": 99.0 + index,
                "close": 101.0 + index,
                "volume": 1000.0 + index * 10,
            }
            for index in range(40)
        ]

        snapshot = calculate_poom_combo_snapshot(rows)

        self.assertEqual(snapshot["ew_norm"], 21.4286)
        self.assertEqual(snapshot["volume_pressure"], 100.0)
        self.assertEqual(snapshot["trend_slope"], 11.1653)
        self.assertFalse(snapshot["in_squeeze"])
        self.assertFalse(snapshot["squeeze_up"])
        self.assertFalse(snapshot["squeeze_down"])
        self.assertEqual(snapshot["signal_summary"]["ew_state"], "positive")
        self.assertEqual(snapshot["signal_summary"]["trend_slope_state"], "positive")

    def test_constant_window_detects_squeeze(self) -> None:
        rows = [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0}
            for _ in range(21)
        ]

        result = analyze_poom_combo(rows)

        self.assertTrue(result.in_squeeze)
        self.assertFalse(result.squeeze_up)
        self.assertFalse(result.squeeze_down)
        self.assertEqual(result.signal_summary["squeeze"], "in_squeeze")

    def test_market_structure_breakout_sets_bos_flags(self) -> None:
        values = [
            10,
            15,
            12,
            18,
            13,
            20,
            14,
            19,
            15,
            21,
            16,
            22,
            17,
            24,
            18,
            26,
            19,
            28,
            20,
            35,
        ]
        rows = [
            {
                "open": value - 0.2,
                "high": value + 0.5,
                "low": value - 0.5,
                "close": value,
                "volume": 1000.0,
            }
            for value in values
        ]

        snapshot = calculate_poom_combo_snapshot(rows)

        self.assertTrue(snapshot["bos_up"])
        self.assertFalse(snapshot["bos_down"])
        self.assertEqual(snapshot["msb_last_high"], 20.5)
        self.assertEqual(snapshot["msb_dir"], 1)
        self.assertEqual(snapshot["signal_summary"]["structure"], "bos_up")


if __name__ == "__main__":
    unittest.main()
