# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Constants of the fake eService portal API, its responses are in `tests/fixtures/account/`.

Special cases of the consumption profiles in `tests/fixtures/account/consumptions/profile/active/`:

- `001_AT00300000000RC100930000000965743_2024-05-06_2025-09-30.json`: the portal returns the average, maximum and
  minimum of each profile type, the energy community sensors only show them for a single profile type, not for a
  difference of two types.
- `001_2023-10-18_2026-06-27.json`: two sections, e.g. after a change from daily to quarter-hourly values, minimum and
  maximum across DST changes, maximum and minimum are at the start of their interval, e.g. of a year.
- `003_2026-05-01_2026-05-31.json`: section change within the month.
- `005_2026-06-10_2026-06-10.json`: not returned by the portal so far, a section without average, maximum, minimum and
  a known resolution.
- `006_2025-01-01_2026-06-01.json`: monthly values, the portal uses them for a total that is too short for yearly
  values.
- `006_2026-06-01_2026-06-01.json`: no data for the last day.
- Contract account 004 has no L1 profile data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final
from zoneinfo import ZoneInfo

# Contract account number, energy community ID, first and last day of a consumption profile request.
type ProfileRequestKey = tuple[str, str, str, str]

API_URL: Final[str] = "https://eservice.netzooe.at/service"
PROFILE_URL: Final[str] = f"{API_URL}/v1.0/consumptions/profile/active"

WSEG: Final[str] = "AT00300000000RC100930000000965743"
SEVEN_ENERGY: Final[str] = "ATCC9999DYNAMCC100087000000000002"

MPAN_1: Final[str] = "AT0000000000000000000000011111111"

# Time of the full update the consumption profiles are requested for (cutoff 2026-06-12, previous month May 2026).
NOW: Final[datetime] = datetime(2026, 6, 28, 12, 0, tzinfo=ZoneInfo("Europe/Vienna"))

CONTRIBUTION_FACTOR_ENTITY_ID: Final[str] = (
    "sensor.netzooe_eservice_at0000000000000000000000011111111_cc100087_contribution_factor"
)
