# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the setup of the integration."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from custom_components.netzooe_eservice.const import DOMAIN
from tests import options
from tests import refresh
from tests import setup_integration
from tests.api_data import CONTRACT_ACCOUNT_DATA_4

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI

ENERGY_COMMUNITY_DEVICE_IDENTIFIER: Final[str] = "AT0000000000000000000000011111111_CC100087"
CONTRIBUTION_FACTOR_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_contribution_factor"
)


def _device(hass: HomeAssistant, config_entry: MockConfigEntry, identifier: str) -> dr.DeviceEntry | None:
    """Return the device of the config entry with the given identifier."""
    return next(
        (
            device
            for device in dr.async_entries_for_config_entry(dr.async_get(hass), config_entry.entry_id)
            if (DOMAIN, identifier) in device.identifiers
        ),
        None,
    )


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
async def test_load_entry_with_disabled_inactive_meter_points(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the entities without inactive meter points."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    with caplog.at_level(logging.WARNING, logger="custom_components.netzooe_eservice.coordinator"):
        await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == snapshot

    assert set(hass.states.async_entity_ids()) == snapshot

    assert (
        "Skipping 1 contract(s) because no active contract for meter point "
        "AT0000000000000000000000011111113 was returned by the API." in caplog.text
    )


@pytest.mark.parametrize("config_entry", [options(show_inactive_meter_points=True)], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_load_entry_with_enabled_inactive_meter_points(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the entities with inactive meter points."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == snapshot

    assert set(hass.states.async_entity_ids()) == snapshot


async def test_stale_device_removed_on_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that devices that are no longer returned by the API are removed, devices of other domains are kept."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    device_registry: dr.DeviceRegistry = dr.async_get(hass)
    stale_device: dr.DeviceEntry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "stale_identifier_not_in_api_data")},
        name="Stale device",
    )
    other_device: dr.DeviceEntry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("other_domain", "stale_identifier_not_in_api_data")},
        name="Device of another domain",
    )

    await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert device_registry.async_get(stale_device.id) is None
    assert device_registry.async_get(other_device.id) is not None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_removed_energy_community_device_comes_back(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the device of a removed energy community is removed and added again with its sensors."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry)

    assert _device(hass, config_entry, ENERGY_COMMUNITY_DEVICE_IDENTIFIER) is not None
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is not None

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests(consents=[])
    await refresh(hass, config_entry)

    assert _device(hass, config_entry, ENERGY_COMMUNITY_DEVICE_IDENTIFIER) is None
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()
    await refresh(hass, config_entry)

    assert _device(hass, config_entry, ENERGY_COMMUNITY_DEVICE_IDENTIFIER) is not None
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is not None


@pytest.mark.parametrize("config_entry", [options(show_inactive_meter_points=True)], indirect=["config_entry"])
async def test_device_name_with_unknown_meter_point_format(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the device name contains the whole meter point number if it cannot be shortened."""
    contract_account: dict[str, Any] = deepcopy(CONTRACT_ACCOUNT_DATA_4)

    for contract in contract_account["contracts"]:
        if (
            contract.get("pointOfDelivery", {}).get("meterPointAdministrationNumber")
            == "AT0000000000000000000000011111113"
        ):
            contract["pointOfDelivery"]["meterPointAdministrationNumber"] = "XX-11111113"

    fake_api.register_auth_request()
    fake_api.register_requests(contract_accounts={"004": contract_account})

    await setup_integration(hass, config_entry)

    device: dr.DeviceEntry | None = _device(hass, config_entry, "XX-11111113")
    assert device is not None
    assert device.name == "Haushalt (XX-11111113)"


async def test_session_closed_on_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the session of the config entry is closed when the entry is unloaded."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    sessions: list[ClientSession] = []

    def create_session(hass: HomeAssistant) -> ClientSession:
        """Create the session and remember it."""
        session: ClientSession = async_create_clientsession(hass)
        sessions.append(session)
        return session

    with patch(
        "custom_components.netzooe_eservice.async_create_clientsession",
        side_effect=create_session,
    ):
        await setup_integration(hass, config_entry)

    assert len(sessions) == 1
    session: ClientSession = sessions[0]
    assert not session.closed

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert session.closed
