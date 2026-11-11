# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the setup of the integration."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

import pytest
from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr

from custom_components.netzooe_eservice.const import DOMAIN
from tests import next_update
from tests import options
from tests import setup_integration
from tests.const import CONTRIBUTION_FACTOR_ENTITY_ID
from tests.test_init_data import ENERGY_COMMUNITY_DEVICE_IDENTIFIER

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion

    from tests.conftest import FakeNetzOOEeServiceAPI


def _device(hass: HomeAssistant, mock_config_entry: MockConfigEntry, identifier: str) -> dr.DeviceEntry | None:
    """Return the device of the config entry with the given identifier."""
    return next(
        (
            device
            for device in dr.async_entries_for_config_entry(dr.async_get(hass), mock_config_entry.entry_id)
            if (DOMAIN, identifier) in device.identifiers
        ),
        None,
    )


@pytest.mark.parametrize(
    "mock_config_entry",
    [
        options(show_revoked_energy_communities=True, include_inactive_contract_account_data=True),
        options(show_revoked_energy_communities=True, include_inactive_contract_account_data=False),
        options(show_revoked_energy_communities=False, include_inactive_contract_account_data=False),
        options(show_revoked_energy_communities=False, include_inactive_contract_account_data=True),
    ],
    indirect=["mock_config_entry"],
    ids=["revoked_inactive_contracts", "revoked", "default", "inactive_contracts"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_load_entry_with_disabled_inactive_meter_points(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the entities without inactive meter points."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    with caplog.at_level(logging.WARNING, logger="custom_components.netzooe_eservice.coordinator"):
        await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == snapshot

    assert set(hass.states.async_entity_ids()) == snapshot

    assert (
        "Skipping 2 contract(s) because no active contract for meter point "
        "AT0000000000000000000000011111113 was returned by the API" in caplog.text
    )
    assert (
        "Skipping 1 contract(s) because no active contract for meter point "
        "AT0000000000000000000000011111114 was returned by the API" in caplog.text
    )


@pytest.mark.parametrize(
    "mock_config_entry",
    [
        options(
            show_revoked_energy_communities=show_revoked,
            include_inactive_contract_account_data=include_inactive,
            show_inactive_meter_points=True,
        )
        for show_revoked, include_inactive in ((True, True), (True, False), (False, False), (False, True))
    ],
    indirect=["mock_config_entry"],
    ids=["revoked_inactive_contracts", "revoked", "default", "inactive_contracts"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_load_entry_with_enabled_inactive_meter_points(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the entities with inactive meter points."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == snapshot

    assert set(hass.states.async_entity_ids()) == snapshot


async def test_stale_device_removed_on_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that devices that are no longer returned by the API are removed, devices of other domains are kept."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    mock_config_entry.add_to_hass(hass)

    device_registry: dr.DeviceRegistry = dr.async_get(hass)
    stale_device: dr.DeviceEntry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "stale_identifier_not_in_api_data")},
        name="Stale device",
    )
    other_device: dr.DeviceEntry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={("other_domain", "stale_identifier_not_in_api_data")},
        name="Device of another domain",
    )

    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert device_registry.async_get(stale_device.id) is None
    assert device_registry.async_get(other_device.id) is not None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_removed_energy_community_device_comes_back(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that the device of a removed energy community is removed and added again with its sensors."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, mock_config_entry)

    assert _device(hass, mock_config_entry, ENERGY_COMMUNITY_DEVICE_IDENTIFIER) is not None
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is not None

    fake_api.aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests(consents=[])
    await next_update(hass, freezer)

    assert _device(hass, mock_config_entry, ENERGY_COMMUNITY_DEVICE_IDENTIFIER) is None
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None

    fake_api.aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()
    await next_update(hass, freezer)

    assert _device(hass, mock_config_entry, ENERGY_COMMUNITY_DEVICE_IDENTIFIER) is not None
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is not None


@pytest.mark.parametrize(
    "mock_config_entry",
    [options(show_inactive_meter_points=True)],
    indirect=["mock_config_entry"],
    ids=["inactive_meter_points"],
)
async def test_device_name_with_unknown_meter_point_format(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the device name contains the whole meter point number if it cannot be shortened."""
    contract_account: dict[str, Any] = deepcopy(fake_api.account.contract_accounts["004"])

    for contract in contract_account["contracts"]:
        if (
            contract.get("pointOfDelivery", {}).get("meterPointAdministrationNumber")
            == "AT0000000000000000000000011111113"
        ):
            contract["pointOfDelivery"]["meterPointAdministrationNumber"] = "XX-11111113"

    fake_api.register_auth_request()
    fake_api.register_requests(contract_accounts={"004": contract_account})

    await setup_integration(hass, mock_config_entry)

    device: dr.DeviceEntry | None = _device(hass, mock_config_entry, "XX-11111113")
    assert device is not None
    assert device.name == "Haushalt (XX-11111113)"


async def test_session_not_closed_on_unload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the session of the config entry is not closed on unload.

    Home Assistant detaches the session itself and raises an error if an integration closes it.
    """
    fake_api.register_auth_request()
    fake_api.register_requests()

    with patch.object(ClientSession, "close", autospec=True) as close:
        await setup_integration(hass, mock_config_entry)

        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    close.assert_not_called()
