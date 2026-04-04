"""Constants for the Netz OÖ eService integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

CONFIG_ENTRY_VERSION: Final[int] = 1
DOMAIN: Final[str] = "netzooe_eservice"
MANUFACTURER: Final = "Netz OÖ"
NAME: Final = "eService"
SCAN_INTERVAL: Final[timedelta] = timedelta(hours=3)
