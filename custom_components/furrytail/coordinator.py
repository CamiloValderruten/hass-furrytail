"""Data update coordinator for FurryTail."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FurryTailApi, FurryTailApiError, FurryTailAuthError
from .const import (
    DP_CLEAN_DELAY,
    DP_CLEAN_STATE,
    DP_VISIT_DURATION,
    DP_VISIT_WEIGHT,
    EVENT_VISIT,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def _parse_event_data(raw: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dp_value(blob: dict[str, Any], key: str) -> Any:
    entry = blob.get(key)
    if isinstance(entry, dict) and "value" in entry:
        return entry.get("value")
    return entry


class FurryTailCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll FurryTail cloud for litter boxes and pets."""

    def __init__(self, hass: HomeAssistant, api: FurryTailApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="FurryTail",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._fetch()
        except FurryTailAuthError:
            try:
                await self.api.async_login()
                return await self._fetch()
            except FurryTailAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except FurryTailApiError as err:
                raise UpdateFailed(str(err)) from err
        except FurryTailApiError as err:
            raise UpdateFailed(str(err)) from err

    async def _fetch(self) -> dict[str, Any]:
        places = await self.api.async_list_places()
        devices: list[dict[str, Any]] = []
        pets_by_place: dict[str, list[dict[str, Any]]] = {}

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=2)

        for place in places:
            place_id = str(place.get("placeId") or "")
            if not place_id:
                continue

            index = await self.api.async_place_index(place_id)
            pets = await self.api.async_pet_list(place_id)
            pets_by_place[place_id] = pets
            pet_lookup = {str(p.get("id")): p for p in pets}

            for device in index.get("allDeviceList") or []:
                mac = str(device.get("mac") or "")
                if not mac:
                    continue

                props = await self.api.async_device_property(mac)
                events = await self.api.async_event_log(mac, start, now)
                upgrades = await self.api.async_upgrade_list(mac)

                last_visit = None
                for event in events:
                    if event.get("eventId") != EVENT_VISIT:
                        continue
                    data = _parse_event_data(event.get("data"))
                    pet_id = str(_dp_value(data, "groupId") or "") or None
                    pet = pet_lookup.get(pet_id or "")
                    last_visit = {
                        "event_id": event.get("id"),
                        "ref_date": event.get("refDate"),
                        "trigger_time": event.get("triggerTime"),
                        "pet_id": pet_id,
                        "pet_name": (pet or {}).get("name"),
                        "duration_s": _coerce_number(
                            _dp_value(data, DP_VISIT_DURATION)
                        ),
                        "weight_g": _coerce_number(_dp_value(data, DP_VISIT_WEIGHT)),
                    }
                    break  # events appear newest-first in captures

                devices.append(
                    {
                        "place_id": place_id,
                        "place_name": index.get("name") or place.get("placeName"),
                        "device_id": str(
                            device.get("deviceId") or device.get("id") or mac
                        ),
                        "name": device.get("name") or "FurryTail Litter Box",
                        "mac": mac,
                        "product_model": device.get("productModel"),
                        "product_key": device.get("productKey"),
                        "online": bool(
                            props.get("onlineStatus", device.get("onlineStatus"))
                        ),
                        "properties": props,
                        "clean_state": str(props.get(DP_CLEAN_STATE) or "0"),
                        "clean_delay_min": _coerce_number(props.get(DP_CLEAN_DELAY)),
                        "auto_clean": str(props.get("6") or ""),
                        "upgrades": upgrades,
                        "last_visit": last_visit,
                        "events": events[:20],
                        "pets": pets,
                    }
                )

        return {
            "places": places,
            "devices": devices,
            "pets_by_place": pets_by_place,
        }


def _coerce_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
