# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Fixtures and the fake eService portal API for the tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.netzooe_eservice.const import DOMAIN
from tests.api_data import CONSENTS_DATA
from tests.api_data import CONTRACT_ACCOUNT_DATA_1
from tests.api_data import CONTRACT_ACCOUNT_DATA_2
from tests.api_data import CONTRACT_ACCOUNT_DATA_3
from tests.api_data import CONTRACT_ACCOUNT_DATA_4
from tests.api_data import DASHBOARD_DATA
from tests.api_data import EEG_OOE_PROFILE_DATA_MONTHLY_L2_001_3
from tests.api_data import EEG_OOE_PROFILE_DATA_MONTHLY_L2_003_4
from tests.api_data import EEG_OOE_PROFILE_DATA_TOTAL_L2_001_3
from tests.api_data import EEG_OOE_PROFILE_DATA_TOTAL_L2_003_4
from tests.api_data import EEG_OOE_PROFILE_DATA_TOTAL_L3_001_3
from tests.api_data import EEG_OOE_PROFILE_DATA_TOTAL_L3_002_2
from tests.api_data import EEG_OOE_PROFILE_DATA_TOTAL_L3_003_4
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_MONTHLY_L2_001_2
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_MONTHLY_L2_003_3
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_TOTAL_L2_001_2
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_TOTAL_L2_003_3
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_001_2
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_002_1
from tests.api_data import SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_003_3
from tests.api_data import WSEG_PROFILE_DATA_TOTAL_L2_L3_001_1
from tests.api_data import WSEG_PROFILE_DATA_TOTAL_L2_L3_003_1
from tests.api_data import WSEG_PROFILE_DATA_TOTAL_L2_L3_003_2

if TYPE_CHECKING:
    from collections.abc import Generator

    from _pytest.fixtures import SubRequest
    from syrupy.assertion import SnapshotAssertion
    from yarl import URL

type ProfileRequestKey = tuple[str, str, str, str]
"""Contract account number, energy community ID, first and last day of a consumption profile request."""

API_URL: Final[str] = "https://eservice.netzooe.at/service"
PROFILE_URL: Final[str] = f"{API_URL}/v1.0/consumptions/profile/active"

WSEG: Final[str] = "AT00300000000RC100930000000965743"
SEVEN_ENERGY: Final[str] = "ATCC9999DYNAMCC100087000000000002"
EEG_OOE: Final[str] = "AT00300000000RC103550000000985681"

CONTRACT_ACCOUNTS: Final[dict[str, dict[str, Any]]] = {
    "001": CONTRACT_ACCOUNT_DATA_1,
    "002": CONTRACT_ACCOUNT_DATA_2,
    "003": CONTRACT_ACCOUNT_DATA_3,
    "004": CONTRACT_ACCOUNT_DATA_4,
}

# Consumption profiles by request, for the full update at tests.NOW (cutoff 2026-06-12, previous month May 2026).
PROFILE_RESPONSES: Final[dict[ProfileRequestKey, list[dict[str, Any]]]] = {
    ("001", WSEG, "2024-05-06", "2025-09-30"): WSEG_PROFILE_DATA_TOTAL_L2_L3_001_1,
    ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-12"): SEVEN_ENERGY_PROFILE_DATA_TOTAL_L2_001_2,
    ("001", SEVEN_ENERGY, "2026-05-01", "2026-05-31"): SEVEN_ENERGY_PROFILE_DATA_MONTHLY_L2_001_2,
    ("001", SEVEN_ENERGY, "2026-01-26", "2026-06-28"): SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_001_2,
    ("001", EEG_OOE, "2026-05-21", "2026-06-12"): EEG_OOE_PROFILE_DATA_TOTAL_L2_001_3,
    ("001", EEG_OOE, "2026-05-21", "2026-05-31"): EEG_OOE_PROFILE_DATA_MONTHLY_L2_001_3,
    ("001", EEG_OOE, "2026-05-21", "2026-06-28"): EEG_OOE_PROFILE_DATA_TOTAL_L3_001_3,
    ("002", SEVEN_ENERGY, "2026-06-17", "2026-06-28"): SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_002_1,
    ("002", EEG_OOE, "2026-06-17", "2026-06-28"): EEG_OOE_PROFILE_DATA_TOTAL_L3_002_2,
    ("003", WSEG, "2024-05-06", "2024-05-07"): WSEG_PROFILE_DATA_TOTAL_L2_L3_003_1,
    ("003", WSEG, "2024-09-10", "2025-09-30"): WSEG_PROFILE_DATA_TOTAL_L2_L3_003_2,
    ("003", SEVEN_ENERGY, "2026-01-26", "2026-06-12"): SEVEN_ENERGY_PROFILE_DATA_TOTAL_L2_003_3,
    ("003", SEVEN_ENERGY, "2026-05-01", "2026-05-31"): SEVEN_ENERGY_PROFILE_DATA_MONTHLY_L2_003_3,
    ("003", SEVEN_ENERGY, "2026-01-26", "2026-06-16"): SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_003_3,
    ("003", EEG_OOE, "2026-05-21", "2026-06-12"): EEG_OOE_PROFILE_DATA_TOTAL_L2_003_4,
    ("003", EEG_OOE, "2026-05-21", "2026-05-31"): EEG_OOE_PROFILE_DATA_MONTHLY_L2_003_4,
    ("003", EEG_OOE, "2026-05-21", "2026-06-16"): EEG_OOE_PROFILE_DATA_TOTAL_L3_003_4,
}


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:  # noqa: ARG001
    """Enable custom integrations in all tests."""
    return


def profile_request_key(data: dict[str, Any]) -> ProfileRequestKey:
    """Return the key of a consumption profile request body."""
    pod: dict[str, Any] = data["pods"][0]
    return (
        pod["contractAccountNumber"],
        pod["energyCommunityId"],
        pod["timerange"]["from"],
        pod["timerange"]["to"],
    )


def profile_request_keys(aioclient_mock: AiohttpClientMocker) -> list[ProfileRequestKey]:
    """Return the keys of all requested consumption profiles."""
    return [
        profile_request_key(data)
        for _method, url, data, _headers in aioclient_mock.mock_calls
        if str(url) == PROFILE_URL
    ]


class FakeNetzOOEeServiceAPI:
    """Fake eService portal API that registers the mocked HTTP responses."""

    def __init__(self, aioclient_mock: AiohttpClientMocker) -> None:
        """Initialize the fake API with the consumption profiles of the requests."""
        self.aioclient_mock: AiohttpClientMocker = aioclient_mock
        self.profile_responses: dict[ProfileRequestKey, list[dict[str, Any]]] = dict(PROFILE_RESPONSES)

    def register_auth_request(self, /, *, status: int = 200, exc: Exception | None = None) -> None:
        """Register the login request."""
        self.aioclient_mock.post(f"{API_URL}/j_security_check", status=status, exc=exc)

    def register_session_request(self) -> None:
        """Register the session request."""
        self.aioclient_mock.get(f"{API_URL}/v1.0/session", cookies={"XSRF-TOKEN": "mocked-token"})

    def register_consents_request(
        self,
        /,
        *,
        consents: list[dict[str, Any]] | None = None,
        status: int = 200,
    ) -> None:
        """Register the consents request."""
        self.aioclient_mock.get(
            f"{API_URL}/v1.0/consents",
            status=status,
            json=CONSENTS_DATA if consents is None else consents,
        )

    def register_dashboard_request(self, /, *, status: int = 200) -> None:
        """Register the dashboard request."""
        self.aioclient_mock.get(f"{API_URL}/v1.0/dashboard", status=status, json=DASHBOARD_DATA)

    def register_requests(
        self,
        /,
        *,
        consents: list[dict[str, Any]] | None = None,
        contract_accounts: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Register all requests of a full update except the login.

        ``contract_accounts`` replaces the data of the given contract account numbers.
        """
        self.register_session_request()
        self.register_consents_request(consents=consents)
        self.register_dashboard_request()

        for number, data in (CONTRACT_ACCOUNTS | (contract_accounts or {})).items():
            self.aioclient_mock.get(f"{API_URL}/v1.0/contract-accounts/100/{number}", json=data)

        self.aioclient_mock.post(PROFILE_URL, side_effect=self.profile_data_side_effect)

    async def profile_data_side_effect(
        self,
        method: str,
        url: URL,
        data: dict[str, Any],
    ) -> AiohttpClientMockResponse:
        """Return the consumption profile of the request, or no values for an unknown request."""
        return AiohttpClientMockResponse(
            method,
            url=url,
            json=self.profile_responses.get(profile_request_key(data), []),
        )


@pytest.fixture(autouse=True)
async def fake_api(
    aioclient_mock: AiohttpClientMocker,
) -> FakeNetzOOEeServiceAPI:
    """Return the fake eService portal API."""
    return FakeNetzOOEeServiceAPI(aioclient_mock)


@pytest.fixture
def config_entry(request: SubRequest) -> MockConfigEntry:
    """Return a config entry, optionally updated with the indirect parameter."""
    mock_config_entry_data: dict[str, Any] = {
        "title": "Netz OÖ eService (test)",
        "data": {
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
        "unique_id": "test",
        "options": {
            "include_inactive_contract_account_data": True,
            "show_revoked_energy_communities": False,
        },
    }

    if hasattr(request, "param"):
        mock_config_entry_data.update(request.param)

    return MockConfigEntry(
        domain=DOMAIN,
        **mock_config_entry_data,
    )


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Test fixture that ensures all entities are enabled in the registry."""
    with (
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            return_value=True,
        ),
    ):
        yield
