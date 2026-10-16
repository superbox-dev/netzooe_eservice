# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Fixtures and the fake eService portal API for the tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
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


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:  # noqa: ARG001
    """Enable custom integrations in all tests."""
    return


class FakeNetzOOEeServiceAPI:
    """Fake eService portal API that registers the mocked HTTP responses."""

    def __init__(self, aioclient_mock: AiohttpClientMocker) -> None:
        """Initialize the fake API with the consumption profiles in the order of the requests."""
        self.aioclient_mock: AiohttpClientMocker = aioclient_mock

        self.profile_data_queue: list[list[dict[str, Any]]] = []
        self.profile_data: list[list[dict[str, Any]]] = [
            WSEG_PROFILE_DATA_TOTAL_L2_L3_001_1,
            SEVEN_ENERGY_PROFILE_DATA_TOTAL_L2_001_2,
            SEVEN_ENERGY_PROFILE_DATA_MONTHLY_L2_001_2,
            SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_001_2,
            EEG_OOE_PROFILE_DATA_TOTAL_L2_001_3,
            EEG_OOE_PROFILE_DATA_MONTHLY_L2_001_3,
            EEG_OOE_PROFILE_DATA_TOTAL_L3_001_3,
            SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_002_1,
            EEG_OOE_PROFILE_DATA_TOTAL_L3_002_2,
            WSEG_PROFILE_DATA_TOTAL_L2_L3_003_1,
            WSEG_PROFILE_DATA_TOTAL_L2_L3_003_2,
            SEVEN_ENERGY_PROFILE_DATA_TOTAL_L2_003_3,
            SEVEN_ENERGY_PROFILE_DATA_MONTHLY_L2_003_3,
            SEVEN_ENERGY_PROFILE_DATA_TOTAL_L3_003_3,
            EEG_OOE_PROFILE_DATA_TOTAL_L2_003_4,
            EEG_OOE_PROFILE_DATA_MONTHLY_L2_003_4,
            EEG_OOE_PROFILE_DATA_TOTAL_L3_003_4,
        ]

    def register_auth_request(self, /, *, status: int = 200, exc: Exception | None = None) -> None:
        """Register the login request."""
        self.aioclient_mock.post(
            "https://eservice.netzooe.at/service/j_security_check",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
            },
            status=status,
            exc=exc,
        )

    def register_session_request(self) -> None:
        """Register the session request."""
        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/session",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Set-Cookie": "XSRF-TOKEN=mocked-token; Path=/",
            },
            status=200,
        )

    def register_consents_request(
        self,
        /,
        *,
        consents: list[dict[str, Any]] | None = None,
        status: int = 200,
    ) -> None:
        """Register the consents request."""
        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/consents",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
                "x-xsrf-token": "mocked-token",
            },
            status=status,
            json=CONSENTS_DATA if consents is None else consents,
        )

    def register_dashboard_request(self, /, *, status: int = 200) -> None:
        """Register the dashboard request."""
        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/dashboard",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
                "x-xsrf-token": "mocked-token",
            },
            status=status,
            json=DASHBOARD_DATA,
        )

    def register_requests(self, /, *, consents: list[dict[str, Any]] | None = None) -> None:
        """Register all requests of a full update except the login."""
        self.register_session_request()
        self.register_consents_request(consents=consents)
        self.register_dashboard_request()
        self.register_contract_account_requests()

    def register_contract_account_requests(self) -> None:
        """Register the contract account and consumption profile requests."""
        self.profile_data_queue = list(self.profile_data)

        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/contract-accounts/100/001",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
                "x-xsrf-token": "mocked-token",
            },
            status=200,
            json=CONTRACT_ACCOUNT_DATA_1,
        )

        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/contract-accounts/100/002",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
                "x-xsrf-token": "mocked-token",
            },
            status=200,
            json=CONTRACT_ACCOUNT_DATA_2,
        )

        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/contract-accounts/100/003",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
                "x-xsrf-token": "mocked-token",
            },
            status=200,
            json=CONTRACT_ACCOUNT_DATA_3,
        )

        self.aioclient_mock.get(
            "https://eservice.netzooe.at/service/v1.0/contract-accounts/100/004",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
                "x-xsrf-token": "mocked-token",
            },
            status=200,
            json=CONTRACT_ACCOUNT_DATA_4,
        )

        self.aioclient_mock.post(
            "https://eservice.netzooe.at/service/v1.0/consumptions/profile/active",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "client-id": "netzonline",
                "Content-Type": "application/json",
            },
            status=200,
            side_effect=self.profile_data_side_effect,
        )

    async def profile_data_side_effect(
        self,
        method: str,
        url: URL,
        *args: object,  # noqa: ARG002
    ) -> AiohttpClientMockResponse:
        """Return the next consumption profile in the order of the requests."""
        response = self.profile_data_queue.pop(0)

        return AiohttpClientMockResponse(
            method,
            url=url,
            json=response,
            headers={"Content-Type": "application/json"},
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
