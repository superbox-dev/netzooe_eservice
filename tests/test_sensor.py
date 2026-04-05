from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.core import State

from tests import setup_integration

if TYPE_CHECKING:
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from syrupy.assertion import SnapshotAssertion
    from tests.conftest import FakeNetzOOEeServiceAPI


@pytest.mark.parametrize(
    "entity",
    [
        "sensor.netzooe_eservice_at0000000000000000000000011111111_energy_community",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_meter_reading",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_monthly_export_eeg_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_monthly_export_supplier_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_monthly_trend_export_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_monthly_trend_export_old",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_scale_type",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_supplier",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_synth_profile",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_total_export_eeg_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_total_export_eeg_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_total_export_supplier_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_total_export_supplier_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_yearly_trend_export_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111111_yearly_trend_export_old",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_energy_community",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_meter_reading",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_monthly_import_eeg_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_monthly_import_supplier_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_monthly_trend_import_new",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_monthly_trend_import_old",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_scale_type",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_supplier",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_synth_profile",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_total_import_eeg_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_total_import_eeg_l3",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_total_import_supplier_l2",
        "sensor.netzooe_eservice_at0000000000000000000000011111112_total_import_supplier_l3",
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
    await setup_integration(hass, config_entry)

    sensor: State | None = hass.states.get(entity)
    assert isinstance(sensor, State)
    assert sensor == snapshot
