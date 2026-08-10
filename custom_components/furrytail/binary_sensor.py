"""Binary sensors for FurryTail."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FurryTailConfigEntry
from .coordinator import FurryTailCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurryTailConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for device in coordinator.data.get("devices") or []:
        entities.append(FurryTailOnlineBinarySensor(coordinator, device["mac"]))
        entities.append(FurryTailCleaningBinarySensor(coordinator, device["mac"]))
    async_add_entities(entities)


class FurryTailDeviceEntity(CoordinatorEntity[FurryTailCoordinator]):
    """Shared device helpers."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac

    def _device(self) -> dict:
        for device in self.coordinator.data.get("devices") or []:
            if device.get("mac") == self._mac:
                return device
        return {}

    @property
    def device_info(self):
        device = self._device()
        return {
            "identifiers": {("furrytail", self._mac)},
            "name": device.get("name") or "FurryTail Litter Box",
            "manufacturer": "FurryTail",
            "model": device.get("product_model") or "PF001",
            "connections": {("mac", self._mac)},
        }


class FurryTailOnlineBinarySensor(FurryTailDeviceEntity, BinarySensorEntity):
    """Device cloud online status."""

    entity_description = BinarySensorEntityDescription(
        key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_online"

    @property
    def is_on(self) -> bool:
        return bool(self._device().get("online"))


class FurryTailCleaningBinarySensor(FurryTailDeviceEntity, BinarySensorEntity):
    """Whether a litter-box cycle is active (DP 2)."""

    entity_description = BinarySensorEntityDescription(
        key="cleaning",
        name="Cleaning",
        device_class=BinarySensorDeviceClass.RUNNING,
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_cleaning"

    @property
    def is_on(self) -> bool:
        return str(self._device().get("clean_state") or "0") not in {"0", ""}
