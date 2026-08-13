from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util

from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.parametrize(
    "language",
    [
        "de",
        "en",
    ],
)
@pytest.mark.parametrize(
    "config_entry",
    [
        {
            "options": {
                "show_revoked_energy_communities": True,
                "include_inactive_contract_account_data": True,
            },
        },
        {
            "options": {
                "show_revoked_energy_communities": True,
                "include_inactive_contract_account_data": False,
            },
        },
        {
            "options": {
                "show_revoked_energy_communities": False,
                "include_inactive_contract_account_data": False,
            },
        },
        {
            "options": {
                "show_revoked_energy_communities": False,
                "include_inactive_contract_account_data": True,
            },
        },
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
    fake_api.register_auth_request()
    fake_api.register_requests()

    hass.config.language = language

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=dt_util.parse_datetime("2026-06-28T12:00:00+02:00"),
    ):
        await setup_integration(hass, config_entry)

    states: dict[str, State | None] = {
        entity_id: hass.states.get(entity_id) for entity_id in sorted(hass.states.async_entity_ids("sensor"))
    }

    assert states == snapshot
