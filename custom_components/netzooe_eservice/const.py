# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Constants for the Netz OÖ eService integration."""

from __future__ import annotations

import re
from datetime import timedelta
from enum import Enum
from typing import Final

from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.const import Platform
from netzooe_eservice_api.constants import ConsentsStatus
from netzooe_eservice_api.constants import SynthProfile

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


PLATFORMS: Final[list[Platform]] = [
    Platform.SENSOR,
]

# Options with their defaults, in the order of the options form.
OPTIONS: Final[dict[str, bool]] = {
    CONF_FREQUENT_UPDATES: DEFAULT_FREQUENT_UPDATES,
    CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES,
    CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA: DEFAULT_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA,
    CONF_SHOW_INACTIVE_METER_POINTS: DEFAULT_SHOW_INACTIVE_METER_POINTS,
}
DESCRIPTION_PLACEHOLDERS: Final[dict[str, str]] = {
    "name": f"{MANUFACTURER} {NAME}",
}

ELECTRICITY_SYNTH_PROFILES: Final[set[str]] = {
    SynthProfile.HOUSEHOLD.value,
    SynthProfile.PHOTOVOLTAICS.value,
}
METER_POINT_DEVICE_TYPES: Final[dict[str, str]] = {
    SynthProfile.HOUSEHOLD.value: DeviceType.HOUSEHOLD.value,
    SynthProfile.PHOTOVOLTAICS.value: DeviceType.PHOTOVOLTAICS.value,
}
ENERGY_COMMUNITY_DEVICE_TYPES: Final[dict[str, str]] = {
    SynthProfile.HOUSEHOLD.value: DeviceType.ENERGY_COMMUNITY_IMPORT.value,
    SynthProfile.PHOTOVOLTAICS.value: DeviceType.ENERGY_COMMUNITY_EXPORT.value,
}
METER_READING_REFERENCE_NUMBERS: Final[set[str]] = {"1.8.1", "2.8.1"}
PEAK_POWER_REFERENCE_NUMBERS: Final[set[str]] = {"1.6.0", "2.6.0"}
ENERGY_COMMUNITY_ID_SERVICE_PROVIDER: Final[slice] = slice(13, 21)

TO_REDACT: Final[set[str]] = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "businessPartnerNumber",
    "contractAccountNumber",
    "meterNumber",
    "meternumber",
    "meterPointAdministrationNumber",
    "title",
    "unique_id",
}

# Matches IDs like "AT0031000000000000000000000012345" and captures the number without leading zeros, e.g. "12345".
SHORT_DEVICE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z]{2}\d{4}0*([1-9][0-9]*)$")

ENERGY_COMMUNITY_OWN_COVERAGE: Final[str] = "ENERGY_COMMUNITY_OWN_COVERAGE"
ENERGY_COMMUNITY_CONSUMPTION: Final[str] = "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR"
ENERGY_COMMUNITY_GENERATION: Final[str] = "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR"
ENERGY_COMMUNITY_OVER_COVERAGE: Final[str] = "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR"
STATUS_OPTIONS: Final[list[str]] = [status.value.lower() for status in ConsentsStatus]
