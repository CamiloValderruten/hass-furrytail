"""Async API client for FurryTail Home (Granwin / wuwei cloud)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE,
    DEFAULT_LANG,
    EVENT_IDS,
    MERCHANT_ID,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class FurryTailAuthError(Exception):
    """Raised when authentication fails."""


class FurryTailApiError(Exception):
    """Raised when the API returns an error envelope or transport fails."""


def _as_ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


class FurryTailApi:
    """Minimal cloud client for read-only litter box data."""

    def __init__(
        self,
        session: ClientSession,
        account: str,
        password: str,
        token: str | None = None,
        lang: str = DEFAULT_LANG,
    ) -> None:
        self._session = session
        self._account = account
        self._password = password
        self._token = token
        self._refresh_token: str | None = None
        self._lang = lang

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    async def async_login(self) -> str:
        """Authenticate and store the user JWT."""
        payload = {
            "merchantId": MERCHANT_ID,
            "account": self._account,
            "password": self._password,
            "phoneCode": "1",
            "lang": self._lang,
        }
        data = await self._request(
            "POST",
            "/app/user/login",
            json_body=payload,
            auth=False,
        )
        token = self._extract_token(data)
        if not token:
            raise FurryTailAuthError("Login succeeded but no token was returned")
        self._token = token
        info = data.get("info") if isinstance(data.get("info"), dict) else {}
        self._refresh_token = info.get("refreshToken")
        return token

    async def async_ensure_token(self) -> str:
        if self._token:
            return self._token
        return await self.async_login()

    async def async_get_user(self) -> dict[str, Any]:
        data = await self._request("POST", "/app/user/get")
        return data.get("info") or {}

    async def async_list_places(self) -> list[dict[str, Any]]:
        data = await self._request("POST", "/home/place/list")
        return data.get("list") or []

    async def async_place_index(self, place_id: str) -> dict[str, Any]:
        payload = {
            "placeId": place_id,
            "markNameList": ["1", "4", "5", "6"],
            "lang": self._lang,
            "type": 1,
        }
        data = await self._request("POST", "/home/place/index", json_body=payload)
        return data.get("info") or {}

    async def async_device_property(self, mac: str) -> dict[str, Any]:
        payload = {"mac": mac, "lang": self._lang}
        data = await self._request(
            "POST", "/device/query/device/property", json_body=payload
        )
        return data.get("info") or {}

    async def async_control_device(
        self, mac: str, property_map: dict[str, Any]
    ) -> None:
        """Set one or more device properties."""
        await self._request(
            "POST",
            "/device/control/device",
            json_body={"mac": mac, "propertyMap": property_map},
        )

    async def async_event_log(
        self,
        mac: str,
        start: datetime,
        end: datetime,
        eids: str = EVENT_IDS,
    ) -> list[dict[str, Any]]:
        payload = {
            "eids": eids,
            "startTime": _as_ms(start),
            "endTime": _as_ms(end),
            "mac": mac,
        }
        data = await self._request(
            "POST", "/device/v1/event/log/between/time", json_body=payload
        )
        return data.get("list") or []

    async def async_pet_list(self, place_id: str) -> list[dict[str, Any]]:
        payload = {
            "placeId": place_id,
            "pageNum": "1",
            "pageSize": "100",
            "blurry": "false",
        }
        data = await self._request("POST", "/pet/pet/info/list", json_body=payload)
        return data.get("list") or []

    async def async_upgrade_list(self, mac: str) -> list[dict[str, Any]]:
        payload = {
            "mac": mac,
            "lang": self._lang,
            "upgradeIdList": ["1"],
        }
        data = await self._request("POST", "/device/upgrade/list", json_body=payload)
        return data.get("list") or []

    @staticmethod
    def _extract_token(data: dict[str, Any]) -> str | None:
        info = data.get("info")
        if isinstance(info, dict):
            for key in ("token", "accessToken", "userToken", "authorization"):
                value = info.get(key)
                if isinstance(value, str) and value:
                    return value
        for key in ("token", "accessToken", "userToken"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        headers = {
            "Accept": "*/*",
            "User-Agent": USER_AGENT,
            "lang": self._lang,
        }
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        if auth:
            token = await self.async_ensure_token()
            headers["Authorization"] = token

        url = f"{API_BASE}{path}"
        try:
            async with self._session.request(
                method, url, headers=headers, json=json_body
            ) as resp:
                # Some endpoints return 401 with JSON envelope.
                try:
                    data = await resp.json(content_type=None)
                except Exception as err:  # noqa: BLE001
                    text = await resp.text()
                    raise FurryTailApiError(
                        f"Non-JSON response from {path}: HTTP {resp.status} {text[:200]}"
                    ) from err
        except ClientError as err:
            raise FurryTailApiError(f"Request to {path} failed: {err}") from err

        if not isinstance(data, dict):
            raise FurryTailApiError(f"Unexpected response from {path}")

        code = data.get("code")
        tip = data.get("tip") or data.get("message") or ""

        # Auth failures — clear token so caller can re-login.
        if code in (20013, 401, "20013", "401") or resp.status == 401:
            self._token = None
            raise FurryTailAuthError(tip or "Unauthorized")

        if code not in (0, "0", None) and resp.status >= 400:
            raise FurryTailApiError(f"{path} failed: code={code} tip={tip}")

        if code not in (0, "0"):
            # Business error with HTTP 200.
            if path.endswith("/login"):
                raise FurryTailAuthError(tip or f"Login failed ({code})")
            raise FurryTailApiError(tip or f"API error ({code}) on {path}")

        return data
