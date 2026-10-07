from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from netzooe_eservice_api.error import APIError

from custom_components.netzooe_eservice.const import CONF_FREQUENT_UPDATES
from custom_components.netzooe_eservice.const import SCAN_INTERVAL
from custom_components.netzooe_eservice.const import SCAN_INTERVAL_FULL
from custom_components.netzooe_eservice.coordinator import NetzOOEeServiceDataUpdateCoordinator

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_async_update_data_api_error_raises_update_failed(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    with (
        patch.object(
            coordinator.api,
            "consents",
            new=AsyncMock(side_effect=APIError("boom")),
        ),
        pytest.raises(UpdateFailed) as error,
    ):
        await coordinator._async_update_data()

    assert str(error.value) == "boom"


async def test_async_setup_api_error_raises_update_failed(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
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
        await coordinator._async_setup()

    assert str(error.value) == "boom"


def test_get_or_create_energy_community_without_consent(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    energy_communities: dict[str, dict[str, object]] = {}

    result: dict[str, object] | None = coordinator._get_or_create_energy_community(
        energy_communities,
        consents_map={"AT001": []},
        meter_point_administration_number="AT001",
        active_contract={
            "contract": {
                "synthProfile": "H0",
            },
        },
        device_type="energy_community",
        timeslice={
            "energyCommunityId": "CC100087",
            "energyCommunityName": "Test",
        },
    )

    assert result is None
    assert energy_communities == {}


async def test_async_update_energy_community_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    coordinator.data = {
        "meter": {
            "meterPointAdministrationNumber": "AT001",
        },
        "energy_community": {
            "meterPointAdministrationNumber": "AT001",
            "deviceId": "CC100087",
            "contributionPercentage": 10,
            "status": "OLD",
        },
    }

    consents_map: dict[str, list[dict[str, object]]] = {
        "AT001": [
            {
                "serviceProvider": "CC100087",
                "contributionPercentage": 99,
                "status": "ACTIVE",
            },
        ],
    }

    with patch.object(
        coordinator,
        "_get_consents_map",
        new=AsyncMock(return_value=consents_map),
    ):
        data: dict[str, Any] = await coordinator._async_update_energy_community_data()

    assert data["energy_community"]["contributionPercentage"] == 99
    assert data["energy_community"]["status"] == "ACTIVE"
    assert data["meter"]["meterPointAdministrationNumber"] == "AT001"


async def test_async_update_data_calls_energy_community_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    coordinator._last_full_update = dt_util.now()

    with patch.object(
        coordinator,
        "_async_update_energy_community_data",
        new=AsyncMock(return_value={"test": {}}),
    ) as update:
        data: dict[str, Any] = await coordinator._async_update_data()

    assert data == {"test": {}}
    update.assert_awaited_once()


async def test_update_interval_with_frequent_updates(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    assert coordinator.frequent_updates is True
    assert coordinator.update_interval == SCAN_INTERVAL


async def test_update_interval_without_frequent_updates(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_FREQUENT_UPDATES: False})

    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    assert coordinator.frequent_updates is False
    assert coordinator.update_interval == SCAN_INTERVAL_FULL


async def test_async_update_data_always_full_update_without_frequent_updates(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_FREQUENT_UPDATES: False})

    session: ClientSession = async_get_clientsession(hass)

    coordinator: NetzOOEeServiceDataUpdateCoordinator = NetzOOEeServiceDataUpdateCoordinator(
        hass,
        config_entry,
        username="test",
        password="test",  # noqa: S106
        session=session,
    )

    # Last full update was just now: with frequent updates this would only refresh the consents.
    coordinator._last_full_update = dt_util.now()

    with (
        patch.object(
            coordinator,
            "_async_full_update",
            new=AsyncMock(return_value={"test": {}}),
        ) as full_update,
        patch.object(
            coordinator,
            "_async_update_energy_community_data",
            new=AsyncMock(),
        ) as energy_community_update,
    ):
        data: dict[str, Any] = await coordinator._async_update_data()

    assert data == {"test": {}}
    full_update.assert_awaited_once()
    energy_community_update.assert_not_awaited()
