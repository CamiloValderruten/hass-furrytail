"""Button entities for FurryTail."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FurryTailConfigEntry
from .const import DP_CLEAN, DP_EMPTY, DP_FLATTEN
from .coordinator import FurryTailCoordinator
from .sensor import FurryTailDeviceEntity

BUTTONS = (
    (ButtonEntityDescription(key="clean", name="Clean"), DP_CLEAN),
    (ButtonEntityDescription(key="flatten", name="Flatten"), DP_FLATTEN),
    (ButtonEntityDescription(key="empty", name="Empty"), DP_EMPTY),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurryTailConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FurryTail command buttons."""
    coordinator = entry.runtime_data
    async_add_entities(
        FurryTailCommandButton(coordinator, device["mac"], description, datapoint)
        for device in coordinator.data.get("devices") or []
        for description, datapoint in BUTTONS
    )


class FurryTailCommandButton(FurryTailDeviceEntity, ButtonEntity):
    """FurryTail litter-box command."""

    def __init__(
        self,
        coordinator: FurryTailCoordinator,
        mac: str,
        description: ButtonEntityDescription,
        datapoint: str,
    ) -> None:
        super().__init__(coordinator, mac)
        self.entity_description = description
        self._datapoint = datapoint
        self._attr_unique_id = f"{mac}_{description.key}"

    async def async_press(self) -> None:
        """Run the command."""
        await self.coordinator.api.async_control_device(self._mac, {self._datapoint: 1})
        await self.coordinator.async_request_refresh()
