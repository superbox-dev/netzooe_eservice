from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from netzooe_eservice_api.error import APIError

from custom_components.netzooe_eservice.const import DOMAIN
from custom_components.netzooe_eservice.coordinator import NetzOOEeServiceDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from aiohttp import ClientSession


async def test_async_update_data_api_error_raises_update_failed(hass: HomeAssistant) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    with (
        patch.object(
            coordinator.api,
            "dashboard",
            new=AsyncMock(side_effect=APIError("boom")),
        ),
        pytest.raises(UpdateFailed) as error,
    ):
        await coordinator._async_update_data()

    assert error.value.translation_domain == DOMAIN
    assert error.value.translation_key == "communication_error"
    assert error.value.translation_placeholders == {"error": "boom"}
