"""Sensors for FurryTail."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfMass, UnitOfTime
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
    entities: list[SensorEntity] = []

    for device in coordinator.data.get("devices") or []:
        mac = device["mac"]
        entities.extend(
            [
                FurryTailLastVisitTimeSensor(coordinator, mac),
                FurryTailLastVisitDurationSensor(coordinator, mac),
                FurryTailLastVisitWeightSensor(coordinator, mac),
                FurryTailLastVisitPetSensor(coordinator, mac),
                FurryTailCleanDelaySensor(coordinator, mac),
                FurryTailWifiFirmwareSensor(coordinator, mac),
                FurryTailMcuFirmwareSensor(coordinator, mac),
            ]
        )
        for pet in device.get("pets") or []:
            pet_id = str(pet.get("id") or "")
            if pet_id:
                entities.append(
                    FurryTailPetWeightSensor(coordinator, mac, pet_id)
                )

    async_add_entities(entities)


class FurryTailDeviceEntity(CoordinatorEntity[FurryTailCoordinator]):
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


class FurryTailLastVisitTimeSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="last_visit_time",
        name="Last visit",
        device_class=SensorDeviceClass.TIMESTAMP,
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_last_visit_time"

    @property
    def native_value(self):
        visit = self._device().get("last_visit") or {}
        ts = visit.get("trigger_time")
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None


class FurryTailLastVisitDurationSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="last_visit_duration",
        name="Last visit duration",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_last_visit_duration"

    @property
    def native_value(self):
        visit = self._device().get("last_visit") or {}
        return visit.get("duration_s")


class FurryTailLastVisitWeightSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="last_visit_weight",
        name="Last visit weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_last_visit_weight"

    @property
    def native_value(self):
        visit = self._device().get("last_visit") or {}
        return visit.get("weight_g")


class FurryTailLastVisitPetSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="last_visit_pet",
        name="Last visit pet",
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_last_visit_pet"

    @property
    def native_value(self):
        visit = self._device().get("last_visit") or {}
        return visit.get("pet_name") or visit.get("pet_id")


class FurryTailCleanDelaySensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="clean_delay",
        name="Clean delay",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_clean_delay"

    @property
    def native_value(self):
        return self._device().get("clean_delay_min")


class FurryTailWifiFirmwareSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="wifi_firmware",
        name="WiFi firmware",
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_wifi_firmware"

    @property
    def native_value(self):
        for item in self._device().get("upgrades") or []:
            if item.get("thoroughfareNumber") == 1:
                return item.get("currentVersion")
        return None


class FurryTailMcuFirmwareSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="mcu_firmware",
        name="MCU firmware",
    )

    def __init__(self, coordinator: FurryTailCoordinator, mac: str) -> None:
        super().__init__(coordinator, mac)
        self._attr_unique_id = f"{mac}_mcu_firmware"

    @property
    def native_value(self):
        for item in self._device().get("upgrades") or []:
            if item.get("thoroughfareNumber") == 2:
                return item.get("currentVersion")
        return None


class FurryTailPetWeightSensor(FurryTailDeviceEntity, SensorEntity):
    entity_description = SensorEntityDescription(
        key="pet_weight",
        name="Pet weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
    )

    def __init__(
        self, coordinator: FurryTailCoordinator, mac: str, pet_id: str
    ) -> None:
        super().__init__(coordinator, mac)
        self._pet_id = pet_id
        self._attr_unique_id = f"{mac}_pet_{pet_id}_weight"

    def _pet(self) -> dict:
        for pet in self._device().get("pets") or []:
            if str(pet.get("id")) == self._pet_id:
                return pet
        return {}

    @property
    def name(self) -> str:
        pet = self._pet()
        name = pet.get("name") or "Pet"
        return f"{name} weight"

    @property
    def native_value(self):
        pet = self._pet()
        weight = pet.get("weight")
        try:
            return float(weight) if weight is not None else None
        except (TypeError, ValueError):
            return None
