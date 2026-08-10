"""The FurryTail Home Assistant integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FurryTailApi
from .const import CONF_ACCOUNT, CONF_TOKEN, PLATFORMS
from .coordinator import FurryTailCoordinator

type FurryTailConfigEntry = ConfigEntry[FurryTailCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FurryTailConfigEntry) -> bool:
    """Set up FurryTail from a config entry."""
    session = async_get_clientsession(hass)
    api = FurryTailApi(
        session,
        account=entry.data[CONF_ACCOUNT],
        password=entry.data[CONF_PASSWORD],
        token=entry.data.get(CONF_TOKEN),
    )

    coordinator = FurryTailCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    if api.token and api.token != entry.data.get(CONF_TOKEN):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_TOKEN: api.token}
        )

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FurryTailConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
