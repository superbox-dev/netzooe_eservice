"""Constants for the Netz OÖ eService integration."""

from __future__ import annotations

from datetime import timedelta
from enum import Enum
from typing import Final

CONFIG_ENTRY_VERSION: Final[int] = 1
CONF_SHOW_REVOKED_ENERGY_COMMUNITIES: Final[str] = "show_revoked_energy_communities"
DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES: Final[bool] = False
DOMAIN: Final[str] = "netzooe_eservice"
MANUFACTURER: Final[str] = "Netz OÖ"
NAME: Final[str] = "eService"
SCAN_INTERVAL: Final[timedelta] = timedelta(hours=3)


class DeviceType(Enum):
    """All device types."""

    ENERGY_COMMUNITY_IMPORT = "ENERGY_COMMUNITY_IMPORT"
    ENERGY_COMMUNITY_EXPORT = "ENERGY_COMMUNITY_EXPORT"
    HOUSEHOLD = "HOUSEHOLD"
    PHOTOVOLTAICS = "PHOTOVOLTAICS"
