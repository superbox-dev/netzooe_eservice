from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch

import pytest
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


def _contribution_factor(hass: HomeAssistant) -> str:
    state: State | None = hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID)
    assert state is not None
    return state.state


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
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(status=500)

    await _refresh(hass, config_entry)

    assert config_entry.runtime_data.last_update_success is True
    assert _contribution_factor(hass) == "93"
    assert "Energy community data update failed, using cached data" in caplog.text


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
    await _setup(hass, config_entry, fake_api)

    assert config_entry.runtime_data.update_interval == update_interval


async def test_energy_community_without_consent(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
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
