# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Fixtures and the fake eService portal API for the tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.common import get_fixture_path
from pytest_homeassistant.common import load_fixture
from pytest_homeassistant.common import load_json_object_fixture
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.netzooe_eservice.const import CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from custom_components.netzooe_eservice.const import CONF_SHOW_REVOKED_ENERGY_COMMUNITIES
from custom_components.netzooe_eservice.const import DOMAIN
from tests import setup_integration
from tests.const import API_URL
from tests.const import PROFILE_URL
from tests.const import ProfileRequestKey

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from collections.abc import Generator
    from pathlib import Path

    from homeassistant.core import HomeAssistant
    from yarl import URL


def profile_request_key(data: dict[str, Any]) -> ProfileRequestKey:
    """Return the key of a consumption profile request body, an L1 profile has an empty energy community ID."""
    pod: dict[str, Any] = data["pods"][0]
    return (
        pod["contractAccountNumber"],
        pod.get("energyCommunityId", ""),
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


@dataclass(frozen=True, kw_only=True)
class PortalAccount:
    """Responses of the eService portal for an account.

    Each response is a JSON file in `tests/fixtures/<account>/` at the path of its request URL. The name of a
    consumption profile is the contract account number, the energy community ID (missing for an L1 profile) and the
    first and last day of the request.
    """

    consents: list[dict[str, Any]]
    dashboard: dict[str, Any]
    contract_accounts: dict[str, dict[str, Any]]
    profile_responses: dict[ProfileRequestKey, list[dict[str, Any]]]

    @classmethod
    def load(cls, name: str, /) -> PortalAccount:
        """Load the responses of the account in `tests/fixtures/<name>/`."""
        dashboard: dict[str, Any] = load_json_object_fixture(f"{name}/dashboard.json")
        profiles: str = f"{name}/consumptions/profile/active"

        return cls(
            consents=cls._load_json_list_fixture(f"{name}/consents.json"),
            dashboard=dashboard,
            contract_accounts={
                account["contractAccountNumber"]: load_json_object_fixture(
                    f"{name}/contract-accounts/{account['businessPartnerNumber']}/{account['contractAccountNumber']}.json",
                )
                for account in dashboard["contractAccounts"]
            },
            profile_responses={
                cls._profile_request_key(path): cls._load_json_list_fixture(f"{profiles}/{path.name}")
                for path in sorted(get_fixture_path(profiles).glob("*.json"))
            },
        )

    @staticmethod
    def _load_json_list_fixture(filename: str, /) -> list[dict[str, Any]]:
        """Return a JSON array of objects from a fixture, `load_json_array_fixture()` does not type its items."""
        data: list[dict[str, Any]] = json.loads(load_fixture(filename))

        return data

    @staticmethod
    def _profile_request_key(path: Path, /) -> ProfileRequestKey:
        """Return the key of the consumption profile request from the name of its file."""
        number, *energy_community_id, date_from, date_to = path.stem.split("_")

        return number, "".join(energy_community_id), date_from, date_to


class FakeNetzOOEeServiceAPI:
    """Fake eService portal API that registers the mocked HTTP responses."""

    def __init__(self, aioclient_mock: AiohttpClientMocker, account: PortalAccount) -> None:
        """Initialize the fake API with the responses of the account."""
        self.aioclient_mock: AiohttpClientMocker = aioclient_mock
        self.account: PortalAccount = account
        self.profile_responses: dict[ProfileRequestKey, list[dict[str, Any]]] = dict(account.profile_responses)
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
            json=self.account.consents if consents is None else consents,
        )

    def register_dashboard_request(self, /, *, status: int = 200) -> None:
        """Register the dashboard request."""
        self.aioclient_mock.get(f"{API_URL}/v1.0/dashboard", status=status, json=self.account.dashboard)

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

        for number, data in (self.account.contract_accounts | (contract_accounts or {})).items():
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
async def fake_api(aioclient_mock: AiohttpClientMocker) -> AsyncGenerator[FakeNetzOOEeServiceAPI]:
    """Return the fake eService portal API with the account in `tests/fixtures/account/`.

    Checks that no unknown consumption profile was requested.

    A test that checks the requests itself sets `allow_unknown_profile_requests`.
    """
    api: FakeNetzOOEeServiceAPI = FakeNetzOOEeServiceAPI(aioclient_mock, PortalAccount.load("account"))

    yield api

    if not api.allow_unknown_profile_requests:
        assert api.unknown_profile_requests == []


@pytest.fixture
def mock_portal(fake_api: FakeNetzOOEeServiceAPI) -> FakeNetzOOEeServiceAPI:
    """Register the responses of the account for the login and a full update."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    return fake_api


@pytest.fixture
def entry_options() -> dict[str, Any]:
    """Return the options of the config entry, overridden by `parametrize`, missing ones keep their defaults."""
    return {
        CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: True,
        CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: False,
    }


@pytest.fixture
def mock_config_entry(entry_options: dict[str, Any]) -> MockConfigEntry:
    """Return the config entry with the options."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Netz OÖ eService (test)",
        data={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
        unique_id="test",
        options=entry_options,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> MockConfigEntry:
    """Set up the integration with the responses of the account and return its config entry."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, mock_config_entry)

    return mock_config_entry


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Replace the setup of the config entry, the config flow tests only test the flow."""
    with patch("custom_components.netzooe_eservice.async_setup_entry", return_value=True) as setup_entry:
        yield setup_entry
