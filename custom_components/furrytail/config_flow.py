"""Config flow for FurryTail."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FurryTailApi, FurryTailApiError, FurryTailAuthError
from .const import CONF_ACCOUNT, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCOUNT): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_login(
    hass: HomeAssistant, account: str, password: str
) -> dict[str, str]:
    session = async_get_clientsession(hass)
    api = FurryTailApi(session, account=account, password=password)
    token = await api.async_login()
    # Prove the token works.
    await api.async_list_places()
    return {CONF_ACCOUNT: account, CONF_PASSWORD: password, CONF_TOKEN: token}


class FurryTailConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FurryTail."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            account = user_input[CONF_ACCOUNT].strip()
            password = user_input[CONF_PASSWORD]
            await self.async_set_unique_id(account.lower())
            self._abort_if_unique_id_configured()
            try:
                data = await _validate_login(self.hass, account, password)
            except FurryTailAuthError:
                errors["base"] = "invalid_auth"
            except FurryTailApiError:
                _LOGGER.exception("FurryTail API error during setup")
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected FurryTail setup error")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="FurryTail", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            account = user_input.get(CONF_ACCOUNT) or entry.data.get(CONF_ACCOUNT)
            password = user_input[CONF_PASSWORD]
            try:
                data = await _validate_login(self.hass, account, password)
            except FurryTailAuthError:
                errors["base"] = "invalid_auth"
            except FurryTailApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(entry, data_updates=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ACCOUNT, default=entry.data.get(CONF_ACCOUNT, "")
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
