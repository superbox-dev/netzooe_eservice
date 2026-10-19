# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the data update coordinator."""

from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from zoneinfo import ZoneInfo

import pytest
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.netzooe_eservice.const import SCAN_INTERVAL
from custom_components.netzooe_eservice.const import SCAN_INTERVAL_FULL
from tests import NOW
from tests import options
from tests import refresh
from tests import setup_integration
from tests.api_data import CONSENTS_DATA
from tests.api_data import CONTRACT_ACCOUNT_DATA_2
from tests.api_data import CONTRACT_ACCOUNT_DATA_4
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_001_2
from tests.conftest import PROFILE_RESPONSES
from tests.conftest import PROFILE_URL
from tests.conftest import SEVEN_ENERGY
from tests.conftest import WSEG
from tests.conftest import profile_request_keys

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
    from yarl import URL

    from tests.conftest import FakeNetzOOEeServiceAPI
    from tests.conftest import ProfileRequestKey

VIENNA: Final[ZoneInfo] = ZoneInfo("Europe/Vienna")

CONTRIBUTION_FACTOR_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_contribution_factor"
)
STATUS_ENTITY_ID: Final[str] = "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_status"
ENERGY_COMMUNITY_EXPORT_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_energy_community_export_l3"
)
OTHER_ENERGY_COMMUNITY_EXPORT_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_rc103550_energy_community_export_l3"
)
TOTAL_EXPORT_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_energy_community_export_l3"
)
SUPPLIER_ENTITY_ID: Final[str] = "sensor.netzooe_eservice_at0000000000000000000000011111112_supplier"
INACTIVE_METER_POINT: Final[str] = "AT0000000000000000000000011111113"

FREQUENT_UPDATES_ENABLED: Final[dict[str, Any]] = options(frequent_updates=True)
FREQUENT_UPDATES_DISABLED: Final[dict[str, Any]] = options(frequent_updates=False)


def _contract_account_requested(aioclient_mock: AiohttpClientMocker) -> bool:
    """Return whether a contract account was requested."""
    return any("/contract-accounts/" in str(url) for _method, url, _data, _headers in aioclient_mock.mock_calls)


def _state(hass: HomeAssistant, entity_id: str) -> str:
    """Return the state of an entity."""
    state: State | None = hass.states.get(entity_id)
    assert state is not None
    return state.state


def _contribution_factor(hass: HomeAssistant) -> str:
    """Return the state of the contribution factor sensor."""
    return _state(hass, CONTRIBUTION_FACTOR_ENTITY_ID)


def _status_valid_from(hass: HomeAssistant) -> str:
    """Return the `valid_from` attribute of the status sensor."""
    state: State | None = hass.states.get(STATUS_ENTITY_ID)
    assert state is not None
    return state.attributes["valid_from"]


def _consents_with(changes: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the consents with the given changes to the consent of the energy community CC100087."""
    return [consent | changes if consent["contributionPercentage"] == "93" else consent for consent in CONSENTS_DATA]


def _contract_account_with(
    contract_account: dict[str, Any],
    meter_point: str,
    changes: dict[str, Any],
) -> dict[str, Any]:
    """Return a copy of the contract account with the given changes to the contract of the meter point."""
    changed: dict[str, Any] = deepcopy(contract_account)

    for contract in changed["contracts"]:
        if contract.get("pointOfDelivery", {}).get("meterPointAdministrationNumber") == meter_point:
            contract.update(changes)

    return changed


async def _setup(hass: HomeAssistant, config_entry: MockConfigEntry, fake_api: FakeNetzOOEeServiceAPI) -> None:
    """Set up the integration with the default API responses."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED


def _register_consents_update(
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    /,
    *,
    consents: list[dict[str, Any]] | None = None,
    status: int = 200,
) -> None:
    """Replace the registered requests with the ones of an update that only fetches the consents."""
    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_session_request()
    fake_api.register_consents_request(consents=consents, status=status)


def _register_full_update(
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    /,
    *,
    consents: list[dict[str, Any]] | None = None,
    contract_accounts: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Replace the registered requests with the ones of a full update."""
    aioclient_mock.clear_requests()
    fake_api.register_auth_request()
    fake_api.register_requests(consents=consents, contract_accounts=contract_accounts)


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


async def test_first_update_authentication_error_starts_reauth(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that rejected credentials on the first update fail the setup and start the reauth flow."""
    fake_api.register_auth_request(status=HTTPStatus.UNAUTHORIZED)
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert [flow["context"]["source"] for flow in config_entry.async_get_active_flows(hass, {SOURCE_REAUTH})] == [
        SOURCE_REAUTH,
    ]


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

    _register_consents_update(fake_api, aioclient_mock, status=500)
    await refresh(hass, config_entry)

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
    assert _status_valid_from(hass) == "2026-01-26"

    _register_consents_update(
        fake_api,
        aioclient_mock,
        consents=_consents_with(
            {"contributionPercentage": "50", "validThrough": {"from": "2026-06-01", "to": "9999-12-31"}},
        ),
    )
    await refresh(hass, config_entry)

    assert _contribution_factor(hass) == "50"
    assert _status_valid_from(hass) == "2026-06-01"
    assert not _contract_account_requested(aioclient_mock)


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_ENABLED], indirect=["config_entry"])
async def test_frequent_updates_full_update_after_full_scan_interval(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that frequent updates do a full update after the full scan interval, but not before."""
    await _setup(hass, config_entry, fake_api)

    _register_full_update(fake_api, aioclient_mock)
    await refresh(hass, config_entry, now=NOW + SCAN_INTERVAL_FULL - timedelta(seconds=1))

    assert not _contract_account_requested(aioclient_mock)

    _register_full_update(fake_api, aioclient_mock)
    await refresh(hass, config_entry, now=NOW + SCAN_INTERVAL_FULL)

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

    # Last full update was just now: with frequent updates this would only refresh the consents.
    _register_full_update(fake_api, aioclient_mock)
    await refresh(hass, config_entry)

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

    _register_consents_update(fake_api, aioclient_mock, status=500)
    await refresh(hass, config_entry)

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


@pytest.mark.parametrize(
    "config_entry",
    [
        options(
            show_revoked_energy_communities=True,
            include_inactive_contract_account_data=True,
            show_inactive_meter_points=True,
        ),
    ],
    indirect=["config_entry"],
)
async def test_profile_requests(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that every consumption profile is requested once for the right contract account and time range."""
    await _setup(hass, config_entry, fake_api)

    assert sorted(profile_request_keys(aioclient_mock)) == sorted(PROFILE_RESPONSES)


@pytest.mark.parametrize(
    "config_entry",
    [options(show_revoked_energy_communities=True, include_inactive_contract_account_data=True)],
    indirect=["config_entry"],
)
@pytest.mark.parametrize(
    ("now", "expected"),
    [
        # Timeslice 2026-01-26 to 2026-06-28: L1/L2 up to the cutoff, complete profile and previous month.
        (
            NOW,
            [
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-12"),
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"),
                ("001", SEVEN_ENERGY, "2026-05-01", "2026-05-31"),
            ],
        ),
        # Cutoff in the previous month: the previous month ends at the cutoff.
        (
            datetime(2026, 7, 5, 12, 0, tzinfo=VIENNA),
            [
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-19"),
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"),
                ("001", SEVEN_ENERGY, "2026-06-01", "2026-06-19"),
            ],
        ),
        # Cutoff one day before the end of the timeslice.
        (
            datetime(2026, 7, 13, 12, 0, tzinfo=VIENNA),
            [
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-27"),
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"),
                ("001", SEVEN_ENERGY, "2026-06-01", "2026-06-27"),
            ],
        ),
        # Cutoff on the last day of the timeslice: the L1/L2 profile is also the complete profile.
        (
            datetime(2026, 7, 14, 12, 0, tzinfo=VIENNA),
            [
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"),
                ("001", SEVEN_ENERGY, "2026-06-01", "2026-06-28"),
            ],
        ),
        # Cutoff on the first day of the timeslice.
        (
            datetime(2026, 2, 11, 12, 0, tzinfo=VIENNA),
            [
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-01-26"),
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-01-26"),
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"),
            ],
        ),
        # Cutoff one day before the timeslice: only the complete profile.
        (
            datetime(2026, 2, 10, 12, 0, tzinfo=VIENNA),
            [
                ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"),
            ],
        ),
        # Previous month in the previous year (both WSEG timeslices of the contract account).
        (
            datetime(2025, 1, 10, 12, 0, tzinfo=VIENNA),
            [
                ("003", WSEG, "2024-05-06", "2024-05-07"),
                ("003", WSEG, "2024-09-10", "2024-12-25"),
                ("003", WSEG, "2024-09-10", "2025-09-30"),
                ("003", WSEG, "2024-12-01", "2024-12-25"),
            ],
        ),
    ],
)
async def test_profile_request_time_ranges(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    now: datetime,
    expected: list[ProfileRequestKey],
) -> None:
    """Test the time ranges of the consumption profile requests of an energy community."""
    # Other dates request other time ranges than the consumption profiles in the responses.
    fake_api.allow_unknown_profile_requests = True
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry, now=now)

    energy_communities: set[tuple[str, str]] = {
        (number, energy_community_id) for number, energy_community_id, *_ in expected
    }
    assert (
        sorted(key for key in profile_request_keys(fake_api.aioclient_mock) if key[:2] in energy_communities)
        == expected
    )


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_integer_profile_values(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that profile values returned as integers are summed as floats and included in the totals."""
    fake_api.profile_responses[("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28")] = [
        item | {"sum": item["sum"] | {"value": int(item["sum"]["value"])}}
        for item in SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_001_2
    ]

    await _setup(hass, config_entry, fake_api)

    assert _state(hass, ENERGY_COMMUNITY_EXPORT_ENTITY_ID) == "600.0"
    assert float(_state(hass, TOTAL_EXPORT_ENTITY_ID)) == pytest.approx(
        float(_state(hass, ENERGY_COMMUNITY_EXPORT_ENTITY_ID))
        + float(_state(hass, OTHER_ENERGY_COMMUNITY_EXPORT_ENTITY_ID)),
    )


async def test_energy_community_without_consent(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that energy communities without consent are skipped."""
    fake_api.register_auth_request()
    fake_api.register_requests(consents=[])

    with caplog.at_level(logging.WARNING, logger="custom_components.netzooe_eservice.coordinator"):
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

    _register_full_update(fake_api, aioclient_mock, consents=[])
    await refresh(hass, config_entry)

    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.parametrize("config_entry", [FREQUENT_UPDATES_DISABLED], indirect=["config_entry"])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_full_update_removes_revoked_energy_community(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that a full update removes an energy community that was revoked, if revoked ones are not shown."""
    await _setup(hass, config_entry, fake_api)

    assert _state(hass, STATUS_ENTITY_ID) == "active"

    _register_full_update(fake_api, aioclient_mock, consents=_consents_with({"status": "REVOKED"}))
    await refresh(hass, config_entry)

    assert hass.states.get(STATUS_ENTITY_ID) is None


async def test_authentication_error_starts_reauth(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that an authentication error starts the reauth flow."""
    await _setup(hass, config_entry, fake_api)

    aioclient_mock.clear_requests()
    fake_api.register_dashboard_request(status=HTTPStatus.UNAUTHORIZED)
    fake_api.register_consents_request(status=HTTPStatus.UNAUTHORIZED)
    fake_api.register_auth_request(status=HTTPStatus.UNAUTHORIZED)

    await refresh(hass, config_entry)

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

    await setup_integration(hass, config_entry)

    assert _contribution_factor(hass) == "93"


@pytest.mark.parametrize(
    ("config_entry", "status"),
    [
        (FREQUENT_UPDATES_ENABLED, "revoked"),
        # Only active energy communities count, even if the status is similar.
        (FREQUENT_UPDATES_ENABLED, "active_unchangeable"),
    ],
    indirect=["config_entry"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_totals_only_include_active_energy_communities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    status: str,
) -> None:
    """Test that an energy community that is no longer active is removed from the totals by a frequent update."""
    await _setup(hass, config_entry, fake_api)

    total_before: float = float(_state(hass, TOTAL_EXPORT_ENTITY_ID))
    energy_community_export: float = float(_state(hass, ENERGY_COMMUNITY_EXPORT_ENTITY_ID))
    assert energy_community_export > 0

    _register_consents_update(fake_api, aioclient_mock, consents=_consents_with({"status": status.upper()}))
    await refresh(hass, config_entry)

    assert _state(hass, STATUS_ENTITY_ID) == status
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

    _register_consents_update(fake_api, aioclient_mock, consents=[])
    await refresh(hass, config_entry)

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
        _register_consents_update(fake_api, aioclient_mock, status=500)
        await refresh(hass, config_entry)

    assert caplog.text.count("Update failed, using cached data") == 1

    _register_full_update(fake_api, aioclient_mock)

    with caplog.at_level(logging.INFO, logger="custom_components.netzooe_eservice.coordinator"):
        await refresh(hass, config_entry)

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

    await setup_integration(hass, config_entry)

    assert hass.states.get(CONTRIBUTION_FACTOR_ENTITY_ID) is None

    _register_full_update(fake_api, aioclient_mock)
    await refresh(hass, config_entry)

    assert _contribution_factor(hass) == "93"


@pytest.mark.parametrize(("status", "expected"), [("NEW_STATUS", "unknown"), (None, "unknown")])
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_unknown_status(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    status: str | None,
    expected: str,
) -> None:
    """Test that an unknown or missing consent status is shown as unknown."""
    fake_api.register_auth_request()
    fake_api.register_requests(consents=_consents_with({"status": status}))

    await setup_integration(hass, config_entry)

    assert _state(hass, STATUS_ENTITY_ID) == expected


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
        """Fail the first profile request and keep the others waiting until they are cancelled."""
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

    await refresh(hass, config_entry)

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

    # 3.5 hours apart, but only 2.5 hours on the wall clock, because DST ends at 03:00.
    last_full_update: datetime = datetime(2026, 10, 25, 1, 0, tzinfo=VIENNA)
    now: datetime = datetime(2026, 10, 25, 3, 30, tzinfo=VIENNA)

    _register_full_update(fake_api, aioclient_mock)
    await refresh(hass, config_entry, now=last_full_update)
    assert _contract_account_requested(aioclient_mock)

    _register_full_update(fake_api, aioclient_mock)
    await refresh(hass, config_entry, now=now)

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
        """Return the number of logged warnings."""
        return sum("No consent found for energy community" in record.getMessage() for record in caplog.records)

    async def refresh_with(consents: list[dict[str, Any]] | None) -> None:
        """Refresh the coordinator with the given consents."""
        _register_full_update(fake_api, aioclient_mock, consents=consents)
        await refresh(hass, config_entry)

    await _setup(hass, config_entry, fake_api)

    with caplog.at_level(logging.WARNING, logger="custom_components.netzooe_eservice.coordinator"):
        await refresh_with([])
        logged: int = warnings()
        assert logged > 0

        await refresh_with([])
        assert warnings() == logged

        await refresh_with(None)
        await refresh_with([])
        assert warnings() == 2 * logged


async def test_meter_point_without_active_contract_logged_once(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a meter point without an active contract is logged once, and again after it was active again."""

    def warnings() -> int:
        """Return the number of logged warnings for the meter point."""
        return sum(
            f"no active contract for meter point {INACTIVE_METER_POINT}" in record.getMessage()
            for record in caplog.records
        )

    with caplog.at_level(logging.WARNING, logger="custom_components.netzooe_eservice.coordinator"):
        await _setup(hass, config_entry, fake_api)
        assert warnings() == 1

        _register_full_update(fake_api, aioclient_mock)
        await refresh(hass, config_entry)

        assert _contract_account_requested(aioclient_mock)
        assert warnings() == 1

        _register_full_update(
            fake_api,
            aioclient_mock,
            contract_accounts={
                "004": _contract_account_with(CONTRACT_ACCOUNT_DATA_4, INACTIVE_METER_POINT, {"active": True}),
            },
        )
        await refresh(hass, config_entry)
        logged: int = warnings()
        assert logged == 1

        _register_full_update(fake_api, aioclient_mock)
        await refresh(hass, config_entry)
        assert warnings() == logged + 1


@pytest.mark.parametrize("config_entry", [options(show_inactive_meter_points=True)], indirect=["config_entry"])
@pytest.mark.parametrize(
    ("changes", "supplier"),
    [
        ({"moveOutDate": "2026-06-20"}, "EP Energie Plus GmbH"),
        ({"moveOutDate": "2026-06-10"}, "easy green energy GmbH & Co KG"),
        # No move-out date: the other contract.
        ({"moveOutDate": None}, "easy green energy GmbH & Co KG"),
        # Same day: the contract that started last, not the one that the portal returns first.
        ({"moveOutDate": "2026-06-16"}, "EP Energie Plus GmbH"),
        ({"moveOutDate": "2026-06-16", "moveInDate": "2019-01-01"}, "easy green energy GmbH & Co KG"),
        # Same start: the contract with the higher contract account number.
        ({"moveOutDate": "2026-06-16", "moveInDate": "2020-06-08"}, "easy green energy GmbH & Co KG"),
    ],
)
async def test_inactive_meter_point_uses_most_recently_ended_contract(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    changes: dict[str, Any],
    supplier: str,
) -> None:
    """Test that a meter point without an active contract uses the contract that ended last."""
    # Both contracts of the meter point have ended, the one of contract account 003 on 2026-06-16.
    # The portal returns contract account 002 before 003.
    contract_account: dict[str, Any] = _contract_account_with(
        CONTRACT_ACCOUNT_DATA_2,
        "AT0000000000000000000000011111112",
        {"active": False} | changes,
    )

    fake_api.register_auth_request()
    fake_api.register_requests(contract_accounts={"002": contract_account})

    await setup_integration(hass, config_entry)

    assert _state(hass, SUPPLIER_ENTITY_ID) == supplier


@pytest.mark.parametrize(
    ("config_entry", "expected"),
    [
        (
            options(show_inactive_meter_points=True, include_inactive_contract_account_data=False),
            {
                # Active contract: only its own energy communities.
                "11111112_cc100087_energy_community_import_l3": "10.0",
                # No active contract: only the most recently ended contract (005), so the energy community of the
                # older contract (004) is not shown.
                "11111113_cc100087_energy_community_import_l3": "20.0",
                "11111113_rc103550_energy_community_import_l3": None,
                "11111113_energy_community_import_l3": "20.0",
            },
        ),
        (
            options(show_inactive_meter_points=True, include_inactive_contract_account_data=True),
            {
                # Active contract: also the energy communities of the ended contract (003).
                "11111112_cc100087_energy_community_import_l3": "610.0",
                # No active contract: all ended contracts.
                "11111113_cc100087_energy_community_import_l3": "20.0",
                "11111113_rc103550_energy_community_import_l3": "10.0",
                "11111113_energy_community_import_l3": "30.0",
            },
        ),
    ],
    indirect=["config_entry"],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_energy_community_data_of_inactive_contract_accounts(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    expected: dict[str, str | None],
) -> None:
    """Test that ended contracts are only included if the data of inactive contract accounts is included.

    This also applies to a meter point without an active contract, which uses the most recently ended contract.
    """
    await _setup(hass, config_entry, fake_api)

    states: dict[str, str | None] = {}

    for key in expected:
        state: State | None = hass.states.get(f"sensor.netzooe_eservice_at00000000000000000000000{key}")
        states[key] = state.state if state else None

    assert states == expected


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

    await setup_integration(hass, config_entry)

    assert _contribution_factor(hass) == "93"
