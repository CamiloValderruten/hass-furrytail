"""Tests for FurryTail command buttons."""

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


class ButtonEntityDescription:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)


button_module = types.ModuleType("homeassistant.components.button")
button_module.ButtonEntity = object
button_module.ButtonEntityDescription = ButtonEntityDescription
sys.modules["homeassistant"] = types.ModuleType("homeassistant")
sys.modules["homeassistant.components"] = types.ModuleType("homeassistant.components")
sys.modules["homeassistant.components.button"] = button_module

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
const_module.DP_CLEAN = "3"
const_module.DP_EMPTY = "5"
const_module.DP_FLATTEN = "4"
sys.modules["furrytail.const"] = const_module

coordinator_module = types.ModuleType("furrytail.coordinator")
coordinator_module.FurryTailCoordinator = object
sys.modules["furrytail.coordinator"] = coordinator_module

sensor_module = types.ModuleType("furrytail.sensor")
sensor_module.FurryTailDeviceEntity = FurryTailDeviceEntity
sys.modules["furrytail.sensor"] = sensor_module

root = Path(__file__).parents[1] / "custom_components" / "furrytail"
spec = importlib.util.spec_from_file_location("furrytail.button", root / "button.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

FurryTailCommandButton = module.FurryTailCommandButton


class FurryTailCommandButtonTest(unittest.IsolatedAsyncioTestCase):
    async def test_setup_adds_three_buttons_per_device(self) -> None:
        coordinator = types.SimpleNamespace(data={"devices": [{"mac": "9C139E69AE40"}]})
        entry = types.SimpleNamespace(runtime_data=coordinator)
        entities = []

        self.assertTrue(hasattr(module, "async_setup_entry"))
        await module.async_setup_entry(
            object(), entry, lambda added: entities.extend(added)
        )

        self.assertEqual(
            ["clean", "flatten", "empty"],
            [entity.entity_description.key for entity in entities],
        )

    async def test_press_sends_command_datapoint(self) -> None:
        coordinator = types.SimpleNamespace(
            api=types.SimpleNamespace(async_control_device=AsyncMock()),
            async_request_refresh=AsyncMock(),
        )

        for description, datapoint in module.BUTTONS:
            with self.subTest(command=description.key):
                button = FurryTailCommandButton(
                    coordinator, "9C139E69AE40", description, datapoint
                )

                await button.async_press()

                coordinator.api.async_control_device.assert_awaited_once_with(
                    "9C139E69AE40", {datapoint: 1}
                )
                coordinator.api.async_control_device.reset_mock()

        self.assertEqual(3, len(module.BUTTONS))


if __name__ == "__main__":
    unittest.main()
