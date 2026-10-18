# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the icon translations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.icon import async_get_icons
from homeassistant.util import dt as dt_util

from custom_components.netzooe_eservice.const import DOMAIN
from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.parametrize(
    "config_entry",
    [
        {
            "options": {
                "show_revoked_energy_communities": True,
                "include_inactive_contract_account_data": True,
            },
        },
    ],
    indirect=["config_entry"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_icons(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that every icon in icons.json is used and the icons that the entities get."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=dt_util.parse_datetime("2026-06-28T12:00:00+02:00"),
    ):
        await setup_integration(hass, config_entry)

    icons: dict[str, dict[str, Any]] = (await async_get_icons(hass, "entity", [DOMAIN]))[DOMAIN]
    entries: list[er.RegistryEntry] = er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)

    used: set[tuple[str, str | None]] = {(entry.domain, entry.translation_key) for entry in entries}
    defined: set[tuple[str, str | None]] = {(platform, key) for platform, keys in icons.items() for key in keys}

    assert defined - used == set()
    assert {
        entry.entity_id: icons.get(entry.domain, {}).get(entry.translation_key or "") or entry.original_icon
        for entry in sorted(entries, key=lambda entry: entry.entity_id)
    } == snapshot
