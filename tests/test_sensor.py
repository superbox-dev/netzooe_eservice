# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import options
from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.parametrize("language", ["de", "en"])
@pytest.mark.parametrize(
    "config_entry",
    [
        options(show_revoked_energy_communities=True, include_inactive_contract_account_data=True),
        options(show_revoked_energy_communities=True, include_inactive_contract_account_data=False),
        options(show_revoked_energy_communities=False, include_inactive_contract_account_data=False),
        options(show_revoked_energy_communities=False, include_inactive_contract_account_data=True),
    ],
    indirect=["config_entry"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
    language: str,
) -> None:
    """Test the states of all sensors."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    hass.config.language = language

    await setup_integration(hass, config_entry)

    states: dict[str, State | None] = {
        entity_id: hass.states.get(entity_id) for entity_id in sorted(hass.states.async_entity_ids("sensor"))
    }

    assert states == snapshot
