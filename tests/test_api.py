"""Tests for the FurryTail API client."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock


aiohttp = types.ModuleType("aiohttp")
aiohttp.ClientError = Exception
aiohttp.ClientSession = object
sys.modules.setdefault("aiohttp", aiohttp)

package = types.ModuleType("furrytail")
package.__path__ = []
sys.modules.setdefault("furrytail", package)

root = Path(__file__).parents[1] / "custom_components" / "furrytail"
for module_name in ("const", "api"):
    spec = importlib.util.spec_from_file_location(
        f"furrytail.{module_name}", root / f"{module_name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

FurryTailApi = sys.modules["furrytail.api"].FurryTailApi


class FurryTailApiTest(unittest.IsolatedAsyncioTestCase):
    async def test_control_device_sends_property_map(self) -> None:
        api = FurryTailApi(object(), "account", "password", token="token")
        api._request = AsyncMock(return_value={"code": 0})

        await api.async_control_device("9C139E69AE40", {"22": 42})

        api._request.assert_awaited_once_with(
            "POST",
            "/device/control/device",
            json_body={"mac": "9C139E69AE40", "propertyMap": {"22": 42}},
        )


if __name__ == "__main__":
    unittest.main()
