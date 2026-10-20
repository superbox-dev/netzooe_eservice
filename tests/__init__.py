# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Netz OÖ eService integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

from homeassistant.helpers.translation import async_get_translations

from tests.api_data import NOW

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.netzooe_eservice.coordinator import NetzOOEeServiceDataUpdateCoordinator

"""Time of the updates, the consumption profiles in `tests.api_data.PROFILE_RESPONSES` are requested for it."""


def options(**overrides: bool) -> dict[str, Any]:
    """Return the indirect `config_entry` parameter with the given options, the others keep their defaults."""
    return {"options": overrides}


async def setup_integration(hass: HomeAssistant, config_entry: MockConfigEntry, /, *, now: datetime = NOW) -> None:
    """Set up the Netz OÖ eService integration in Home Assistant at the given time."""
    config_entry.add_to_hass(hass)

    with patch("custom_components.netzooe_eservice.coordinator.dt_util.now", return_value=now):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()


async def refresh(hass: HomeAssistant, config_entry: MockConfigEntry, /, *, now: datetime = NOW) -> None:
    """Refresh the coordinator at the given time."""
    coordinator: NetzOOEeServiceDataUpdateCoordinator = config_entry.runtime_data

    with patch("custom_components.netzooe_eservice.coordinator.dt_util.now", return_value=now):
        await coordinator.async_refresh()
        await hass.async_block_till_done()


async def init_translations(hass: HomeAssistant, config_entry: MockConfigEntry, /, *, category: str) -> dict[str, str]:
    """Return the translations of the integration for the given category."""
    translations: dict[str, str] = await async_get_translations(
        hass,
        hass.config.language,
        category,
        [config_entry.domain],
    )

    return translations
