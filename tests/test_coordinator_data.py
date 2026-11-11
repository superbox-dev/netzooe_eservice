# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0

"""Test data for `test_coordinator.py`."""

from datetime import datetime
from typing import Any
from typing import Final
from zoneinfo import ZoneInfo

from tests import options
from tests.const import SEVEN_ENERGY
from tests.const import ProfileRequestKey

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

LAST_MONTH_ENTITY_ID: Final[str] = "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_last_month_{}"


def _profile(date_from: str, date_to: str, generation: float, over_coverage: float) -> list[dict[str, Any]]:
    """Return the export profile of 7Energy at the first meter point for a time range."""
    return [
        {
            "meterPointAdministrationNumber": "AT0000000000000000000000011111111",
            "from": f"{date_from}T00:00:00",
            "to": f"{date_to}T23:59:59",
            "type": profile_type,
            "energyDirection": "GENERATION",
            "sum": {"value": value, "unit": "KWH"},
        }
        for profile_type, value in (
            ("ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR", generation),
            ("ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR", over_coverage),
        )
    ]


# On 2026-07-05 the cutoff is 2026-06-19, so the L1/L2 profile of June ends there and the complete one does not.
LAST_MONTH_CUTOFF_NOW: Final[datetime] = datetime(2026, 7, 5, 12, 0, tzinfo=VIENNA)
LAST_MONTH_PROFILE_RESPONSES: Final[dict[ProfileRequestKey, list[dict[str, Any]]]] = {
    ("001", SEVEN_ENERGY, "2026-06-01", "2026-06-19"): _profile("2026-06-01", "2026-06-19", 300.0, 200.0),
    ("001", SEVEN_ENERGY, "2026-06-01", "2026-06-28"): _profile("2026-06-01", "2026-06-28", 450.0, 280.0),
}
