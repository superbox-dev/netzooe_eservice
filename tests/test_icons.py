# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the icon translations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Final

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.icon import async_get_icons

from custom_components.netzooe_eservice.const import CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from custom_components.netzooe_eservice.const import CONF_SHOW_REVOKED_ENERGY_COMMUNITIES
from custom_components.netzooe_eservice.const import DOMAIN
from tests.const import NOW

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion


pytestmark: Final = pytest.mark.freeze_time(NOW)


@pytest.mark.parametrize(
    "entry_options",
    [
        {CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: True, CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: True},
    ],
    ids=["revoked_inactive_contracts"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_icons(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that every icon in icons.json is used and the icons that the entities get."""
    icons: dict[str, dict[str, Any]] = (await async_get_icons(hass, "entity", [DOMAIN]))[DOMAIN]
    entries: list[er.RegistryEntry] = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    used: set[tuple[str, str | None]] = {(entry.domain, entry.translation_key) for entry in entries}
    defined: set[tuple[str, str | None]] = {(platform, key) for platform, keys in icons.items() for key in keys}

    assert defined - used == set()
    assert {
        entry.entity_id: icons.get(entry.domain, {}).get(entry.translation_key or "") or entry.original_icon
        for entry in sorted(entries, key=lambda entry: entry.entity_id)
    } == snapshot
