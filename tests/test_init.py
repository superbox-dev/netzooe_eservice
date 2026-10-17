# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the setup of the integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.util import dt as dt_util

from custom_components.netzooe_eservice.const import DOMAIN
from tests import setup_integration

if TYPE_CHECKING:
    from aiohttp import ClientSession
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
                "show_inactive_meter_points": False,
            },
        },
        {
            "options": {
                "show_revoked_energy_communities": True,
                "include_inactive_contract_account_data": False,
                "show_inactive_meter_points": False,
            },
        },
        {
            "options": {
                "show_revoked_energy_communities": False,
                "include_inactive_contract_account_data": False,
                "show_inactive_meter_points": False,
            },
        },
        {
            "options": {
                "show_revoked_energy_communities": False,
                "include_inactive_contract_account_data": True,
                "show_inactive_meter_points": False,
            },
        },
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

    with (
        patch(
            "custom_components.netzooe_eservice.coordinator.dt_util.now",
            return_value=dt_util.parse_datetime("2026-06-28T12:00:00+02:00"),
        ),
        caplog.at_level(
            logging.WARNING,
            logger="custom_components.netzooe_eservice.coordinator",
        ),
    ):
        await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == snapshot

    assert set(hass.states.async_entity_ids()) == snapshot

    assert (
        "Skipping 1 contract(s) because no active contract for meter point "
        "AT0000000000000000000000011111113 was returned by the API." in caplog.text
    )


@pytest.mark.parametrize(
    "config_entry",
    [
        {
            "options": {
                "show_revoked_energy_communities": False,
                "include_inactive_contract_account_data": True,
                "show_inactive_meter_points": True,
            },
        },
    ],
    indirect=["config_entry"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_load_entry_with_enabled_inactive_meter_points(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the entities with inactive meter points."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    with (
        patch(
            "custom_components.netzooe_eservice.coordinator.dt_util.now",
            return_value=dt_util.parse_datetime("2026-06-28T12:00:00+02:00"),
        ),
        caplog.at_level(
            logging.WARNING,
            logger="custom_components.netzooe_eservice.coordinator",
        ),
    ):
        await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == snapshot

    assert set(hass.states.async_entity_ids()) == snapshot


async def test_stale_device_removed_on_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that devices that are no longer returned by the API are removed."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    device_registry: dr.DeviceRegistry = dr.async_get(hass)
    stale_device: dr.DeviceEntry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "stale_identifier_not_in_api_data")},
        name="Stale device",
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert device_registry.async_get(stale_device.id) is None


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
