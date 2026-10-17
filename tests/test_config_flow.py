# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the config and options flow."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from homeassistant import setup
from homeassistant.config_entries import SOURCE_USER
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from netzooe_eservice_api.error import APIError

from custom_components.netzooe_eservice.const import DOMAIN
from tests import setup_integration

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from tests.conftest import FakeNetzOOEeServiceAPI


async def test_user_flow(
    hass: HomeAssistant,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the user flow creates a config entry."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    assert await setup.async_setup_component(hass, DOMAIN, {})

    result_user_step: ConfigFlowResult = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result_user_step["type"] is FlowResultType.FORM
    assert result_user_step["step_id"] == "user"

    result_create_entry: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result_user_step["flow_id"],
        user_input={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
    )

    assert result_create_entry["type"] == FlowResultType.CREATE_ENTRY
    assert result_create_entry["result"].title == "Netz OÖ eService (test)"
    assert result_create_entry["data"] == {
        "username": "test",
        "password": "test",
    }

    assert hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, "test")


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (APIError("mocked api error"), "cannot_connect"),
        (APIError("mocked api error", status=HTTPStatus.UNAUTHORIZED), "invalid_auth"),
        (Exception("mocked client error"), "unknown"),
    ],
)
async def test_user_flow_failed(
    hass: HomeAssistant,
    fake_api: FakeNetzOOEeServiceAPI,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test that the user flow shows an error if the login fails."""
    fake_api.register_auth_request(exc=side_effect)
    fake_api.register_requests()

    assert await setup.async_setup_component(hass, DOMAIN, {})

    result_user_step: ConfigFlowResult = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result_user_step["type"] is FlowResultType.FORM
    assert result_user_step["step_id"] == "user"

    result_create_entry: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result_user_step["flow_id"],
        user_input={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
        },
    )

    assert result_create_entry["type"] == FlowResultType.FORM
    assert result_create_entry["errors"] == {
        "base": expected_error,
    }


async def test_reconfigure_flow(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the reconfigure flow updates the config entry."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result: ConfigFlowResult = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result_user_step: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test",
            "password": "test",
        },
    )

    await hass.async_block_till_done()

    assert result_user_step["type"] == FlowResultType.ABORT
    assert result_user_step["reason"] == "reconfigure_successful"


async def test_reconfigure_flow_failed(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the reconfigure flow shows an error if the login fails."""
    fake_api.register_auth_request(exc=APIError("mocked api error"))
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result: ConfigFlowResult = await config_entry.start_reconfigure_flow(hass)

    result_reconfigure_step: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test",
            "password": "test",
        },
    )

    assert result_reconfigure_step["type"] == FlowResultType.FORM
    assert result_reconfigure_step["step_id"] == "reconfigure"
    assert result_reconfigure_step["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_flow_wrong_account(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the reconfigure flow aborts for another account."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result: ConfigFlowResult = await config_entry.start_reconfigure_flow(hass)

    result_user_step: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "other",
            "password": "test",
        },
    )

    assert result_user_step["type"] == FlowResultType.ABORT
    assert result_user_step["reason"] == "wrong_account"


async def test_reauth_flow(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the reauth flow only asks for the new password and updates it."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result: ConfigFlowResult = await config_entry.start_reauth_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["data_schema"]
    assert list(result["data_schema"].schema.keys()) == ["password"]
    assert result["description_placeholders"] == {"name": "Netz OÖ eService", "username": "test"}

    result_confirm_step: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "new-password",
        },
    )

    await hass.async_block_till_done()

    assert result_confirm_step["type"] == FlowResultType.ABORT
    assert result_confirm_step["reason"] == "reauth_successful"
    assert config_entry.data == {CONF_USERNAME: "test", CONF_PASSWORD: "new-password"}


async def test_reauth_flow_failed(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the reauth flow shows an error and keeps the password if the login fails."""
    fake_api.register_auth_request(exc=APIError("mocked api error", status=HTTPStatus.UNAUTHORIZED))
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result: ConfigFlowResult = await config_entry.start_reauth_flow(hass)

    result_confirm_step: ConfigFlowResult = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "password": "wrong-password",
        },
    )

    assert result_confirm_step["type"] == FlowResultType.FORM
    assert result_confirm_step["step_id"] == "reauth_confirm"
    assert result_confirm_step["errors"] == {"base": "invalid_auth"}
    assert config_entry.data == {CONF_USERNAME: "test", CONF_PASSWORD: "test"}


async def test_option_flow(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the options flow saves all options."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry)

    result_init: ConfigFlowResult = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        data=None,
    )

    assert result_init["type"] is FlowResultType.FORM
    assert result_init["step_id"] == "init"
    assert result_init["data_schema"]

    # The changed options reload the config entry, which fetches the consumption profiles again.
    fake_api.register_contract_account_requests()

    assert list(result_init["data_schema"].schema.keys()) == [
        "frequent_updates",
        "show_revoked_energy_communities",
        "include_inactive_contract_account_data",
        "show_inactive_meter_points",
    ]

    result_create_entry: ConfigFlowResult = await hass.config_entries.options.async_configure(
        result_init["flow_id"],
        user_input={
            "frequent_updates": False,
            "show_revoked_energy_communities": True,
            "include_inactive_contract_account_data": False,
            "show_inactive_meter_points": True,
        },
    )
    await hass.async_block_till_done()

    assert result_create_entry["type"] is FlowResultType.CREATE_ENTRY
    assert result_create_entry["data"] == {
        "frequent_updates": False,
        "show_revoked_energy_communities": True,
        "include_inactive_contract_account_data": False,
        "show_inactive_meter_points": True,
    }
    assert config_entry.state is ConfigEntryState.LOADED


async def test_option_flow_defaults(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the options flow uses the default values."""
    fake_api.register_auth_request()
    fake_api.register_requests()

    await setup_integration(hass, config_entry)

    result_init: ConfigFlowResult = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        data=None,
    )

    result_create_entry: ConfigFlowResult = await hass.config_entries.options.async_configure(
        result_init["flow_id"],
        user_input={},
    )
    await hass.async_block_till_done()

    assert result_create_entry["type"] is FlowResultType.CREATE_ENTRY
    assert result_create_entry["data"] == {
        "frequent_updates": False,
        "show_revoked_energy_communities": False,
        "include_inactive_contract_account_data": True,
        "show_inactive_meter_points": False,
    }
    assert config_entry.state is ConfigEntryState.LOADED


async def test_option_flow_when_integration_not_loaded(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
    """Test that the options flow also works if the integration is not loaded."""
    # The changed options set up the config entry.
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result_init: ConfigFlowResult = await hass.config_entries.options.async_init(
        config_entry.entry_id,
        data=None,
    )

    assert result_init["type"] is FlowResultType.FORM
    assert result_init["step_id"] == "init"

    result_create_entry: ConfigFlowResult = await hass.config_entries.options.async_configure(
        result_init["flow_id"],
        user_input={"show_inactive_meter_points": True},
    )
    await hass.async_block_till_done()

    assert result_create_entry["type"] is FlowResultType.CREATE_ENTRY
    assert result_create_entry["data"]["show_inactive_meter_points"] is True
    assert config_entry.state is ConfigEntryState.LOADED
