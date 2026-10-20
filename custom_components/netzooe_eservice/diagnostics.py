# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Diagnostics for the Netz OÖ eService integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from homeassistant.components.diagnostics import async_redact_data

from .const import TO_REDACT

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import NetzOOEeServiceConfigEntry
    from .coordinator import NetzOOEeServiceDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: NetzOOEeServiceConfigEntry,
) -> dict[str, Any]:
    """Return the diagnostics of a config entry."""
    coordinator: NetzOOEeServiceDataUpdateCoordinator = entry.runtime_data

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        # The device identifiers contain the meter point number, so the devices are listed without them.
        "devices": async_redact_data(list(coordinator.data.values()), TO_REDACT),
    }
