# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Netz OÖ eService integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant.common import async_fire_time_changed

from custom_components.netzooe_eservice.const import SCAN_INTERVAL_FULL

if TYPE_CHECKING:
    from datetime import timedelta

    from freezegun.api import FrozenDateTimeFactory
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant.common import MockConfigEntry


def options(**overrides: bool) -> dict[str, Any]:
    """Return the indirect `mock_config_entry` parameter with the given options, the others keep their defaults."""
    return {"options": overrides}


async def setup_integration(hass: HomeAssistant, mock_config_entry: MockConfigEntry, /) -> None:
    """Set up the Netz OÖ eService integration in Home Assistant."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def next_update(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    /,
    *,
    interval: timedelta = SCAN_INTERVAL_FULL,
) -> None:
    """Advance the time by the update interval and run the scheduled update, without frequent updates by default."""
    freezer.tick(interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


async def init_translations(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, /, *, category: str
) -> dict[str, str]:
    """Return the translations of the integration for the given category."""
    translations: dict[str, str] = await async_get_translations(
        hass,
        hass.config.language,
        category,
        [mock_config_entry.domain],
    )

    return translations
