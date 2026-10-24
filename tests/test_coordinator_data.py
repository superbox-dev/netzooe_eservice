# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0

"""Test data for `test_coordinator.py`."""

from typing import Any
from typing import Final
from zoneinfo import ZoneInfo

from tests import options

VIENNA: Final[ZoneInfo] = ZoneInfo("Europe/Vienna")

STATUS_ENTITY_ID: Final[str] = "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_status"
ENERGY_COMMUNITY_EXPORT_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_energy_community_export_l3"
)
OTHER_ENERGY_COMMUNITY_EXPORT_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_rc103550_energy_community_export_l3"
)
TOTAL_EXPORT_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_energy_community_export_l3"
)
SUPPLIER_ENTITY_ID: Final[str] = "sensor.netzooe_eservice_at0000000000000000000000011111112_supplier"
INACTIVE_METER_POINT: Final[str] = "AT0000000000000000000000011111113"

FREQUENT_UPDATES_ENABLED: Final[dict[str, Any]] = options(frequent_updates=True)
FREQUENT_UPDATES_DISABLED: Final[dict[str, Any]] = options(frequent_updates=False)
