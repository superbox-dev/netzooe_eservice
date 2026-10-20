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
from tests.api_data import API_URL
from tests.api_data import CONSENTS_DATA
from tests.api_data import CONTRACT_ACCOUNTS
from tests.api_data import DASHBOARD_DATA
from tests.api_data import PROFILE_RESPONSES
from tests.api_data import PROFILE_URL
from tests.api_data import ProfileRequestKey

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from collections.abc import Generator

    from _pytest.fixtures import SubRequest
    from syrupy.assertion import SnapshotAssertion
    from yarl import URL

"""Contract account number, energy community ID, first and last day of a consumption profile request."""


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
        self.allow_unknown_profile_requests: bool = False
        self.unknown_profile_requests: list[ProfileRequestKey] = []

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
        """Return the consumption profile of the request, or no values for an unknown request.

        Unknown requests are recorded, the `fake_api` fixture fails the test if there are any.
        """
        key: ProfileRequestKey = profile_request_key(data)

        if key not in self.profile_responses:
            self.unknown_profile_requests.append(key)

        return AiohttpClientMockResponse(method, url=url, json=self.profile_responses.get(key, []))


@pytest.fixture(autouse=True)
async def fake_api(
    aioclient_mock: AiohttpClientMocker,
) -> AsyncGenerator[FakeNetzOOEeServiceAPI]:
    """Return the fake eService portal API and check that no unknown consumption profile was requested.

    A test that checks the requests itself sets `allow_unknown_profile_requests`.
    """
    api: FakeNetzOOEeServiceAPI = FakeNetzOOEeServiceAPI(aioclient_mock)

    yield api

    if not api.allow_unknown_profile_requests:
        assert api.unknown_profile_requests == []


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
