from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.util import dt as dt_util

from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion
    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_load_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
) -> None:
    fake_api.register_auth_request()
    fake_api.register_requests()

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=dt_util.parse_datetime("2026-06-28T12:00:00+02:00"),
    ):
        await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == 78

    assert set(hass.states.async_entity_ids()) == snapshot
