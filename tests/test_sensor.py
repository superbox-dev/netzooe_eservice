# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import snapshot_platform

from tests import options
from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from pytest_homeassistant.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.parametrize("language", ["de", "en"], ids=["de", "en"])
@pytest.mark.parametrize(
    "mock_config_entry",
    [
        options(
            show_revoked_energy_communities=show_revoked,
            include_inactive_contract_account_data=include_inactive,
            show_inactive_meter_points=show_inactive,
        )
        for show_inactive in (False, True)
        for show_revoked, include_inactive in ((True, True), (True, False), (False, False), (False, True))
    ],
    indirect=["mock_config_entry"],
    ids=[
        f"{meter_points}-{options}"
        for meter_points in ("active_meter_points", "inactive_meter_points")
        for options in ("revoked_inactive_contracts", "revoked", "default", "inactive_contracts")
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
    language: str,
) -> None:
    """Test the entity registry entries and states of all sensors."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    hass.config.language = language
    # The portal returns the maximum and minimum in UTC, the timelines show them in the local time of Austria.
    await hass.config.async_set_time_zone("Europe/Vienna")

    await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, er.async_get(hass), snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("entity_id", "unrecorded"),
    [
        ("sensor.netzooe_eservice_at0000000000000000000000011111111_export_l1", False),
        ("sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_energy_community_export_l3", True),
    ],
    ids=["meter_point_l1", "energy_community"],
)
async def test_sensor_timeline_recorded(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    entity_id: str,
    *,
    unrecorded: bool,
) -> None:
    """Test that only the small timeline of the L1 sensors is recorded, not the growing one of energy communities."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, mock_config_entry)

    state: State | None = hass.states.get(entity_id)

    assert state is not None
    assert state.state_info is not None
    assert ("timeline" in state.state_info["unrecorded_attributes"]) is unrecorded
