"""Tests for the FurryTail light entity."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock


class CoordinatorEntity:
    def __init__(self, coordinator) -> None:
        self.coordinator = coordinator


class FurryTailDeviceEntity(CoordinatorEntity):
    def __init__(self, coordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac

    def _device(self) -> dict:
        return self.coordinator.data["devices"][0]


light_module = types.ModuleType("homeassistant.components.light")
light_module.ATTR_BRIGHTNESS = "brightness"
light_module.ColorMode = types.SimpleNamespace(BRIGHTNESS="brightness")
light_module.LightEntity = object
sys.modules["homeassistant"] = types.ModuleType("homeassistant")
sys.modules["homeassistant.components"] = types.ModuleType("homeassistant.components")
sys.modules["homeassistant.components.light"] = light_module

core_module = types.ModuleType("homeassistant.core")
core_module.HomeAssistant = object
sys.modules["homeassistant.core"] = core_module

platform_module = types.ModuleType("homeassistant.helpers.entity_platform")
platform_module.AddEntitiesCallback = object
sys.modules["homeassistant.helpers"] = types.ModuleType("homeassistant.helpers")
sys.modules["homeassistant.helpers.entity_platform"] = platform_module

package = types.ModuleType("furrytail")
package.__path__ = []
package.FurryTailConfigEntry = object
sys.modules["furrytail"] = package

const_module = types.ModuleType("furrytail.const")
const_module.DP_LIGHT_BRIGHTNESS = "22"
sys.modules["furrytail.const"] = const_module

coordinator_module = types.ModuleType("furrytail.coordinator")
coordinator_module.FurryTailCoordinator = object
sys.modules["furrytail.coordinator"] = coordinator_module

sensor_module = types.ModuleType("furrytail.sensor")
sensor_module.FurryTailDeviceEntity = FurryTailDeviceEntity
sys.modules["furrytail.sensor"] = sensor_module

root = Path(__file__).parents[1] / "custom_components" / "furrytail"
spec = importlib.util.spec_from_file_location("furrytail.light", root / "light.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

FurryTailLight = module.FurryTailLight


class FurryTailLightTest(unittest.IsolatedAsyncioTestCase):
    def _coordinator(self):
        return types.SimpleNamespace(
            data={"devices": [{"mac": "9C139E69AE40", "properties": {"22": 0}}]},
            api=types.SimpleNamespace(async_control_device=AsyncMock()),
            async_request_refresh=AsyncMock(),
        )

    async def test_turn_on_maps_ha_brightness_to_device_percent(self) -> None:
        coordinator = self._coordinator()
        light = FurryTailLight(coordinator, "9C139E69AE40")

        await light.async_turn_on(brightness=128)

        coordinator.api.async_control_device.assert_awaited_once_with(
            "9C139E69AE40", {"22": 50}
        )
        coordinator.async_request_refresh.assert_awaited_once()

    async def test_turn_off_sets_device_brightness_to_zero(self) -> None:
        coordinator = self._coordinator()
        light = FurryTailLight(coordinator, "9C139E69AE40")

        await light.async_turn_off()

        coordinator.api.async_control_device.assert_awaited_once_with(
            "9C139E69AE40", {"22": 0}
        )
        coordinator.async_request_refresh.assert_awaited_once()

    def test_state_uses_reported_device_brightness(self) -> None:
        coordinator = self._coordinator()
        coordinator.data["devices"][0]["properties"]["22"] = 42
        light = FurryTailLight(coordinator, "9C139E69AE40")

        self.assertTrue(light.is_on)
        self.assertEqual(107, light.brightness)


if __name__ == "__main__":
    unittest.main()
