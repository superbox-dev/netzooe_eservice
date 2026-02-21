"""The Netz OÖ eService integration."""

import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .coordinator import NetzOOEeServiceConfigEntry
from .coordinator import NetzOOEeServiceDataUpdateCoordinator

if TYPE_CHECKING:
    from aiohttp import ClientSession

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: NetzOOEeServiceConfigEntry) -> bool:
    """Set up Netz OÖ eService platform."""
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    session: ClientSession = async_create_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        username=username,
        password=password,
        session=session,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NetzOOEeServiceConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
