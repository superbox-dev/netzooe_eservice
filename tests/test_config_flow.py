from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from homeassistant import setup
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from netzooe_eservice_api.error import APIError

from custom_components.netzooe_eservice.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from tests.conftest import FakeNetzOOEeServiceAPI


async def test_user_flow(
    hass: HomeAssistant,
    fake_api: FakeNetzOOEeServiceAPI,
) -> None:
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
    fake_api.register_auth_request()
    fake_api.register_requests()

    config_entry.add_to_hass(hass)

    result: ConfigFlowResult = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

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
