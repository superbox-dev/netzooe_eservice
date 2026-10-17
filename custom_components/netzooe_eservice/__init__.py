# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""The Netz OÖ eService integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.const import Platform
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN
from .coordinator import NetzOOEeServiceConfigEntry
from .coordinator import NetzOOEeServiceDataUpdateCoordinator

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceRegistry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: NetzOOEeServiceConfigEntry) -> bool:
    """Set up Netz OÖ eService from a config entry."""
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]

    # Each config entry needs its own session (cookie jar), close it when the entry is unloaded or reloaded.
    session: ClientSession = async_create_clientsession(hass)
    entry.async_on_unload(session.close)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        entry,
        username=username,
        password=password,
        session=session,
    )

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    _async_remove_stale_devices(hass, entry, coordinator.data)
    entry.async_on_unload(
        coordinator.async_add_listener(lambda: _async_remove_stale_devices(hass, entry, coordinator.data)),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _async_remove_stale_devices(
    hass: HomeAssistant,
    entry: NetzOOEeServiceConfigEntry,
    data: dict[str, Any],
) -> None:
    """Remove the devices of the config entry that are no longer in the coordinator data."""
    device_registry: DeviceRegistry = dr.async_get(hass)
    valid_identifiers: set[str] = set(data)

    for device_entry in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        our_identifiers: set[str] = {i[1] for i in device_entry.identifiers if i[0] == DOMAIN}

        if our_identifiers and not our_identifiers & valid_identifiers:
            device_registry.async_remove_device(device_entry.id)


async def async_unload_entry(hass: HomeAssistant, entry: NetzOOEeServiceConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
