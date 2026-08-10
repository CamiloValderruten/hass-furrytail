"""Light entities for FurryTail."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FurryTailConfigEntry
from .const import DP_LIGHT_BRIGHTNESS
from .coordinator import FurryTailCoordinator
from .sensor import FurryTailDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurryTailConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FurryTail lights."""
    coordinator = entry.runtime_data
    async_add_entities(
        FurryTailLight(coordinator, device["mac"])
        for device in coordinator.data.get("devices") or []
    )


class FurryTailLight(FurryTailDeviceEntity, LightEntity):
    """FurryTail litter box night light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_has_entity_name = True
    _attr_name = "Night light"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_night_light"

    @property
    def _brightness_percent(self) -> float:
        try:
            value = float(
                (self._device().get("properties") or {}).get(DP_LIGHT_BRIGHTNESS, 0)
            )
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, value))

    @property
    def is_on(self) -> bool:
        """Return whether the night light is on."""
        return self._brightness_percent > 0

    @property
    def brightness(self) -> int:
        """Return the night-light brightness."""
        return round(self._brightness_percent * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the night light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        percent = round(max(0, min(255, brightness)) * 100 / 255)
        await self.coordinator.api.async_control_device(
            self._mac, {DP_LIGHT_BRIGHTNESS: percent}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the night light."""
        await self.coordinator.api.async_control_device(
            self._mac, {DP_LIGHT_BRIGHTNESS: 0}
        )
        await self.coordinator.async_request_refresh()
