# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry
from syrupy.filters import props

from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.util.json import JsonObjectType
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.typing import ClientSessionGenerator
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that the diagnostics contain the data without credentials and customer numbers."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry)

    diagnostics: JsonObjectType = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)

    assert diagnostics == snapshot(exclude=props("created_at", "modified_at", "entry_id"))
