# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Constants for the Netz OÖ eService integration."""

from __future__ import annotations

from datetime import timedelta
from enum import Enum
from typing import Final

CONFIG_ENTRY_VERSION: Final[int] = 1
CONF_FREQUENT_UPDATES: Final[str] = "frequent_updates"
CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: Final[str] = "include_inactive_contract_account_data"
CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: Final[str] = "show_revoked_energy_communities"
CONF_SHOW_INACTIVE_METER_POINTS: Final[str] = "show_inactive_meter_points"
DEFAULT_FREQUENT_UPDATES: Final[bool] = False
DEFAULT_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: Final[bool] = True
DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES: Final[bool] = False
DEFAULT_SHOW_INACTIVE_METER_POINTS: Final[bool] = False
DOMAIN: Final[str] = "netzooe_eservice"
MANUFACTURER: Final[str] = "Netz OÖ"
NAME: Final[str] = "eService"
SCAN_INTERVAL: Final[timedelta] = timedelta(minutes=15)
SCAN_INTERVAL_FULL: Final[timedelta] = timedelta(hours=3)

# The portal provides the L1/L2 profile data of the energy communities with a delay of about 16 days.
PROFILE_DATA_DELAY: Final[timedelta] = timedelta(days=16)
# Maximum number of consumption profile requests that are sent to the portal at the same time.
MAX_PARALLEL_REQUESTS: Final[int] = 4


class DeviceType(Enum):
    """All device types."""

    ENERGY_COMMUNITY_IMPORT = "ENERGY_COMMUNITY_IMPORT"
    ENERGY_COMMUNITY_EXPORT = "ENERGY_COMMUNITY_EXPORT"
    HOUSEHOLD = "HOUSEHOLD"
    PHOTOVOLTAICS = "PHOTOVOLTAICS"
