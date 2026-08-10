"""Tests for verified FurryTail datapoint mappings."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


root = Path(__file__).parents[1] / "custom_components" / "furrytail"
spec = importlib.util.spec_from_file_location("furrytail_const", root / "const.py")
const = importlib.util.module_from_spec(spec)
spec.loader.exec_module(const)


class FurryTailDatapointTest(unittest.TestCase):
    def test_verified_command_and_state_datapoints(self) -> None:
        self.assertEqual("2", const.DP_CLEAN_STATE)
        self.assertEqual(
            ("3", "4", "5"),
            (
                const.DP_CLEAN,
                const.DP_FLATTEN,
                const.DP_EMPTY,
            ),
        )


if __name__ == "__main__":
    unittest.main()
