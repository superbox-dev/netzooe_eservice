# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the data update coordinator."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.config_entries import ConfigEntryState
from homeassistant.util import dt as dt_util

from custom_components.netzooe_eservice.const import SCAN_INTERVAL
from custom_components.netzooe_eservice.const import SCAN_INTERVAL_FULL
from tests import setup_integration
from tests.api_data import CONSENTS_DATA

if TYPE_CHECKING:
    from datetime import datetime
    from datetime import timedelta

    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

    from custom_components.netzooe_eservice.coordinator import NetzOOEeServiceDataUpdateCoordinator
    from tests.conftest import FakeNetzOOEeServiceAPI

NOW: datetime | None = dt_util.parse_datetime("2026-06-28T12:00:00+02:00")

CONTRIBUTION_FACTOR_ENTITY_ID: str = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_contribution_factor"
)
STATUS_ENTITY_ID: str = "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_status"
ENERGY_COMMUNITY_EXPORT_ENTITY_ID: str = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_energy_community_export_l3"
)
TOTAL_EXPORT_ENTITY_ID: str = "sensor.netzooe_eservice_at0000000000000000000000011111111_energy_community_export_l3"

FREQUENT_UPDATES_ENABLED: dict[str, Any] = {
    "options": {
        "include_inactive_contract_account_data": True,
        "show_revoked_energy_communities": False,
        "frequent_updates": True,
    },
}

FREQUENT_UPDATES_DISABLED: dict[str, Any] = {
    "options": {
        "include_inactive_contract_account_data": True,
        "show_revoked_energy_communities": False,
        "frequent_updates": False,
    },
}


def _contract_account_requested(aioclient_mock: AiohttpClientMocker) -> bool:
    return any("/contract-accounts/" in str(url) for _method, url, _data, _headers in aioclient_mock.mock_calls)


def _state(hass: HomeAssistant, entity_id: str) -> str:
    state: State | None = hass.states.get(entity_id)
    assert state is not None
    return state.state


def _contribution_factor(hass: HomeAssistant) -> str:
    return _state(hass, CONTRIBUTION_FACTOR_ENTITY_ID)


async def _refresh(hass: HomeAssistant, config_entry: MockConfigEntry, now: datetime | None = NOW) -> None:
    coordinator: NetzOOEeServiceDataUpdateCoordinator = config_entry.runtime_data

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=now,
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, config_entry: MockConfigEntry, fake_api: FakeNetzOOEeServiceAPI) -> None:
    fake_api.register_auth_request()
    fake_api.register_requests()

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=NOW,
    ):
        await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED


async def test_setup_api_error_retries_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that an API error on the dashboard request retries the setup."""
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_dashboard_request(status=500)

    config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_first_update_api_error_retries_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that an API error on the first update retries the setup."""
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_dashboard_request()
    fake_api.register_consents_request(status=500)

    config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_DISABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_full_update_api_error_keeps_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an API error on a full update keeps the previous data."""
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(status=500)

    await _refresh(hass, config_entry)

    assert config_entry.runtime_data.last_update_success is True
    assert _contribution_factor(hass) == "93"
    assert "Update failed, using cached data" in caplog.text


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_frequent_updates_only_refresh_energy_community_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that frequent updates only refresh the consents."""
    await _setup(hass, config_entry, fake_api)

    assert _contribution_factor(hass) == "93"

    consents: list[dict[str, Any]] = [
        consent | {"contributionPercentage": "50"} if consent["contributionPercentage"] == "93" else consent
        for consent in CONSENTS_DATA
    ]

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(consents=consents)

    await _refresh(hass, config_entry)

    assert _contribution_factor(hass) == "50"
    assert not _contract_account_requested(aioclient_mock)


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
async def test_frequent_updates_full_update_after_full_scan_interval(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that frequent updates do a full update after the full scan interval."""
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()

    assert NOW is not None
    await _refresh(hass, config_entry, NOW + SCAN_INTERVAL_FULL)

    assert _contract_account_requested(aioclient_mock)


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_DISABLED], indirect=["config_entry"])
async def test_without_frequent_updates_always_full_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that without frequent updates every update is a full update."""
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()

    # Last full update was just now: with frequent updates this would only refresh the consents.
    await _refresh(hass, config_entry)

    assert _contract_account_requested(aioclient_mock)


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_energy_community_update_api_error_keeps_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an API error on a frequent update keeps the previous data."""
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(status=500)

    await _refresh(hass, config_entry)

    assert config_entry.runtime_data.last_update_success is True
    assert _contribution_factor(hass) == "93"
    assert "Update failed, using cached data" in caplog.text


@pytest.mark.parametrize(
    ("config_entry", "update_interval"),
    [
        (FREQUENT_UPDATES_ENABLED, SCAN_INTERVAL),
        (FREQUENT_UPDATES_DISABLED, SCAN_INTERVAL_FULL),
    ],
    indirect=["config_entry"],
)
async def test_update_interval(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    update_interval: timedelta,
) -> None:
    """Test the update interval with and without frequent updates."""
    await _setup(hass, config_entry, fake_api)

    assert config_entry.runtime_data.update_interval == update_interval


async def test_energy_community_without_consent(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that energy communities without consent are skipped."""
    fake_api.register_auth_request()
    fake_api.register_requests(consents=[])

    with (
        patch(
            "custom_components.netzooe_eservice.coordinator.dt_util.now",
            return_value=NOW,
        ),
        caplog.at_level(
            logging.WARNING,
            logger="custom_components.netzooe_eservice.coordinator",
        ),
    ):
        await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None
    assert "No consent found for energy community" in caplog.text


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_DISABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_removed_energy_community_sensors_update_without_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that removed energy communities are removed without errors."""
    await _setup(hass, config_entry, fake_api)

    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is not None

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests(consents=[])

    await _refresh(hass, config_entry)

    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


async def test_authentication_error_starts_reauth(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that an authentication error starts the reauth flow."""
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request(status=HTTPStatus.UNAUTHORIZED)

    await _refresh(hass, config_entry)

    assert config_entry.runtime_data.last_update_success is False
    assert [flow["context"]["source"] for flow in config_entry.async_get_active_flows(hass, {SOURCE_REAUTH})] == [
        SOURCE_REAUTH,
    ]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_only_most_recent_consent_is_used(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that only the most recent consent of the consent history is used."""
    older_consent: dict[str, Any] = next(
        consent | {"validThrough": {"from": "2020-01-01", "to": "2020-12-31"}, "contributionPercentage": "10"}
        for consent in CONSENTS_DATA
        if consent["contributionPercentage"] == "93"
    )

    fake_api.register_auth_request()
    fake_api.register_requests(consents=[*CONSENTS_DATA, older_consent])

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=NOW,
    ):
        await setup_integration(hass, config_entry)

    assert _contribution_factor(hass) == "93"


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_frequent_updates_exclude_revoked_energy_community_from_totals(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that a revoked energy community is removed from the totals."""
    await _setup(hass, config_entry, fake_api)

    total_before: float = float(_state(hass, TOTAL_EXPORT_ENTITY_ID))
    energy_community_export: float = float(_state(hass, ENERGY_COMMUNITY_EXPORT_ENTITY_ID))
    assert energy_community_export > 0

    consents: list[dict[str, Any]] = [
        consent | {"status": "REVOKED"} if consent["contributionPercentage"] == "93" else consent
        for consent in CONSENTS_DATA
    ]

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(consents=consents)

    await _refresh(hass, config_entry)

    assert _state(hass, STATUS_ENTITY_ID) == "revoked"
    assert float(_state(hass, TOTAL_EXPORT_ENTITY_ID)) == pytest.approx(total_before - energy_community_export)
