# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the sensors."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest
from pytest_homeassistant.common import snapshot_platform

from custom_components.netzooe_eservice.const import CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from custom_components.netzooe_eservice.const import CONF_SHOW_INACTIVE_METER_POINTS
from custom_components.netzooe_eservice.const import CONF_SHOW_REVOKED_ENERGY_COMMUNITIES
from tests import setup_integration
from tests.const import NOW

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion


pytestmark: Final = pytest.mark.freeze_time(NOW)


@pytest.mark.parametrize("language", ["de", "en"], ids=["de", "en"])
@pytest.mark.parametrize(
    "entry_options",
    [
        {
            CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: show_revoked,
            CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: include_inactive,
            CONF_SHOW_INACTIVE_METER_POINTS: show_inactive,
        }
        for show_inactive in (False, True)
        for show_revoked, include_inactive in ((True, True), (True, False), (False, False), (False, True))
    ],
    ids=[
        f"{meter_points}-{options}"
        for meter_points in ("active_meter_points", "inactive_meter_points")
        for options in ("revoked_inactive_contracts", "revoked", "default", "inactive_contracts")
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_portal")
async def test_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    language: str,
) -> None:
    """Test the entity registry entries and states of all sensors."""
    hass.config.language = language
    # The portal returns the maximum and minimum in UTC, the timelines show them in the local time of Austria.
    await hass.config.async_set_time_zone("Europe/Vienna")

    await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.parametrize(
    ("entity_id", "unrecorded"),
    [
        ("sensor.netzooe_eservice_at0000000000000000000000011111111_export_l1", False),
        ("sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_energy_community_export_l3", True),
    ],
    ids=["meter_point_l1", "energy_community"],
)
@pytest.mark.usefixtures("init_integration")
async def test_sensor_timeline_recorded(
    hass: HomeAssistant,
    entity_id: str,
    *,
    unrecorded: bool,
) -> None:
    """Test that only the small timeline of the L1 sensors is recorded, not the growing one of energy communities."""
    state: State | None = hass.states.get(entity_id)

    assert state is not None
    assert state.state_info is not None
    assert ("timeline" in state.state_info["unrecorded_attributes"]) is unrecorded
