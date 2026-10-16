# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the data update coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.config_entries import ConfigEntryState
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.netzooe_eservice.const import SCAN_INTERVAL
from custom_components.netzooe_eservice.const import SCAN_INTERVAL_FULL
from tests import setup_integration
from tests.api_data import CONSENTS_DATA

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
    from yarl import URL

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
PROFILE_URL: str = "https://eservice.netzooe.at/service/v1.0/consumptions/profile/active"
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


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_totals_only_include_active_energy_communities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that an energy community that is not active is not included in the totals."""
    await _setup(hass, config_entry, fake_api)

    total_before: float = float(_state(hass, TOTAL_EXPORT_ENTITY_ID))
    energy_community_export: float = float(_state(hass, ENERGY_COMMUNITY_EXPORT_ENTITY_ID))
    assert energy_community_export > 0

    consents: list[dict[str, Any]] = [
        consent | {"status": "ACTIVE_UNCHANGEABLE"} if consent["contributionPercentage"] == "93" else consent
        for consent in CONSENTS_DATA
    ]

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(consents=consents)

    await _refresh(hass, config_entry)

    assert _state(hass, STATUS_ENTITY_ID) == "active_unchangeable"
    assert float(_state(hass, TOTAL_EXPORT_ENTITY_ID)) == pytest.approx(total_before - energy_community_export)


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_frequent_updates_keep_data_of_energy_community_without_consent(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that a frequent update keeps the previous data if the consent of an energy community is missing."""
    await _setup(hass, config_entry, fake_api)

    total_before: str = _state(hass, TOTAL_EXPORT_ENTITY_ID)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(consents=[])

    await _refresh(hass, config_entry)

    assert _contribution_factor(hass) == "93"
    assert _state(hass, STATUS_ENTITY_ID) == "active"
    assert _state(hass, TOTAL_EXPORT_ENTITY_ID) == total_before


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_DISABLED], indirect=["config_entry"])
async def test_api_error_logged_once_until_available_again(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that API errors are logged once and the recovery is logged."""
    await _setup(hass, config_entry, fake_api)

    for _ in range(2):
        aioclient_mock.clear_requests()
        fake_api.register_auth_request()
        fake_api.register_session_request()
        fake_api.register_consents_request(status=500)

        await _refresh(hass, config_entry)

    assert caplog.text.count("Update failed, using cached data") == 1

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()

    with caplog.at_level(logging.INFO, logger="custom_components.netzooe_eservice.coordinator"):
        await _refresh(hass, config_entry)

    assert "The eService portal is available again" in caplog.text


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_DISABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_new_energy_community_sensors_added_without_reload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the sensors of a new energy community are added after an update."""
    fake_api.register_auth_request()
    fake_api.register_requests(consents=[])

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=NOW,
    ):
        await setup_integration(hass, config_entry)

    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()

    await _refresh(hass, config_entry)

    assert _contribution_factor(hass) == "93"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_unknown_status(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that an unknown consent status is shown as unknown."""
    consents: list[dict[str, Any]] = [
        consent | {"status": "NEW_STATUS"} if consent["contributionPercentage"] == "93" else consent
        for consent in CONSENTS_DATA
    ]

    fake_api.register_auth_request()
    fake_api.register_requests(consents=consents)

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=NOW,
    ):
        await setup_integration(hass, config_entry)

    assert _state(hass, STATUS_ENTITY_ID) == "unknown"


async def test_failed_request_cancels_remaining_requests(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that a failed consumption profile request cancels the remaining requests."""
    await _setup(hass, config_entry, fake_api)

    failed: bool = False
    waiting: int = 0
    cancelled: int = 0

    async def profile_side_effect(method: str, url: URL, *args: object) -> AiohttpClientMockResponse:  # noqa: ARG001
        nonlocal failed, waiting, cancelled

        # The first request fails, the others wait until they are cancelled.
        if not failed:
            failed = True
            return AiohttpClientMockResponse(method, url=url, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        waiting += 1
        never_done: asyncio.Future[AiohttpClientMockResponse] = asyncio.get_running_loop().create_future()

        try:
            return await never_done
        finally:
            cancelled += 1

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    # Registered first, so it takes precedence over the profile response of register_requests().
    aioclient_mock.post(PROFILE_URL, side_effect=profile_side_effect)
    fake_api.register_requests()

    await _refresh(hass, config_entry)

    assert config_entry.runtime_data.last_update_success
    assert waiting > 0
    assert cancelled == waiting


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
async def test_frequent_updates_full_update_across_dst_change(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the full scan interval is measured in real time when DST ends."""
    await _setup(hass, config_entry, fake_api)

    vienna: ZoneInfo = ZoneInfo("Europe/Vienna")
    # 3.5 hours apart, but only 2.5 hours on the wall clock, because DST ends at 03:00.
    last_full_update: datetime = datetime(2026, 10, 25, 1, 0, tzinfo=vienna)
    now: datetime = datetime(2026, 10, 25, 3, 30, tzinfo=vienna)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()
    await _refresh(hass, config_entry, last_full_update)
    assert _contract_account_requested(aioclient_mock)

    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests()
    await _refresh(hass, config_entry, now)

    assert _contract_account_requested(aioclient_mock)


async def test_missing_consent_logged_once(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a missing consent is logged only once until the consent is returned again."""

    def warnings() -> int:
        return sum("No consent found for energy community" in record.getMessage() for record in caplog.records)

    async def refresh(consents: list[dict[str, Any]] | None) -> None:
        aioclient_mock.clear_requests()
        fake_api.register_auth_request()
        fake_api.register_requests(consents=consents)
        await _refresh(hass, config_entry)

    await _setup(hass, config_entry, fake_api)

    with caplog.at_level(logging.WARNING, logger="custom_components.netzooe_eservice.coordinator"):
        await refresh([])
        logged: int = warnings()
        assert logged > 0

        await refresh([])
        assert warnings() == logged

        await refresh(None)
        await refresh([])
        assert warnings() == 2 * logged


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_consent_matched_by_service_provider_position(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that a service provider code elsewhere in the energy community ID does not match the consent."""
    # "9999DYNA" is part of the ID "ATCC9999DYNAMCC100087000000000002", but not at the service provider position.
    other_consent: dict[str, Any] = next(
        consent | {"serviceProvider": "9999DYNA", "contributionPercentage": "1"}
        for consent in CONSENTS_DATA
        if consent["contributionPercentage"] == "93"
    )

    fake_api.register_auth_request()
    fake_api.register_requests(consents=[other_consent, *CONSENTS_DATA])

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=NOW,
    ):
        await setup_integration(hass, config_entry)

    assert _contribution_factor(hass) == "93"
