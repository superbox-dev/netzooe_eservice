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


@pytest.mark.parametrize("language", ["de", "en"], ids=["de", "en"])
@pytest.mark.parametrize(
    "config_entry",
    [
        options(
            show_revoked_energy_communities=show_revoked,
            include_inactive_contract_account_data=include_inactive,
            show_inactive_meter_points=show_inactive,
        )
        for show_inactive in (False, True)
        for show_revoked, include_inactive in ((True, True), (True, False), (False, False), (False, True))
    ],
    indirect=["config_entry"],
    ids=[
        f"{meter_points}-{options}"
        for meter_points in ("active_meter_points", "inactive_meter_points")
        for options in ("revoked_inactive_contracts", "revoked", "default", "inactive_contracts")
    ],
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
