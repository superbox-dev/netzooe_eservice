from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.core import State
from homeassistant.util import dt as dt_util

from tests import setup_integration

if TYPE_CHECKING:
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion
    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.parametrize(
    "entity",
    [
        "sensor.netzooe_eservice_at0000000000000000000000011111111_meter_reading",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_monthly_trend_export_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_monthly_trend_export_old",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_contribution_factor",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_energy_community_export_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_energy_community_export_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_last_month_energy_community_export_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_last_month_supplier_export_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_status",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_supplier_export_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_rc100930_supplier_export_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_scale_type",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_supplier",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_yearly_trend_export_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_yearly_trend_export_old",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_contribution_factor",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_energy_community_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_energy_community_import_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_last_month_energy_community_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_last_month_supplier_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_status",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_supplier_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_cc100087_supplier_import_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_meter_reading",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_monthly_trend_import_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_monthly_trend_import_old",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_contribution_factor",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_energy_community_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_energy_community_import_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_last_month_energy_community_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_last_month_supplier_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_status",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_supplier_import_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_rc100930_supplier_import_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_scale_type",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_supplier",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_yearly_trend_import_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_yearly_trend_import_old",
    ],
)
@pytest.mark.parametrize(
    "language",
    [
        "de",
        "en",
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    fake_api: FakeNetzOOEeServiceAPI,
    snapshot: SnapshotAssertion,
    entity: str,
    language: str,
) -> None:
    fake_api.register_auth_request()
    fake_api.register_requests()

    hass.config.language = language

    with patch(
        "custom_components.netzooe_eservice.coordinator.dt_util.now",
        return_value=dt_util.parse_datetime("2026-04-19T12:00:00+02:00"),
    ):
        await setup_integration(hass, config_entry)

    sensor: State | None = hass.states.get(entity)
    assert isinstance(sensor, State)
    assert sensor == snapshot
