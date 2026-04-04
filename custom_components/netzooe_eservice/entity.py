"""Entity classes for the KEBA KeEnergy integration."""

from __future__ import annotations

import logging
from typing import TypeVar

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME
from .coordinator import NetzOOEeServiceConfigEntry
from .coordinator import NetzOOEeServiceDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T", str, int, float)


class NetzOOEeServiceEntity(CoordinatorEntity[NetzOOEeServiceDataUpdateCoordinator]):
    """Netz OÖ eService base entity."""

    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: NetzOOEeServiceDataUpdateCoordinator,
        entry: NetzOOEeServiceConfigEntry,
        device_identifier: str,
    ) -> None:
        """Initialize the Netz OÖ eService entity."""
        super().__init__(coordinator)
        self.entry: NetzOOEeServiceConfigEntry = entry
        self.device_identifier: str = device_identifier

    @property
    def device_name(self) -> str | None:
        """Return the name of the current device."""
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return updated device specific attributes."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_identifier)},
            name=self.device_name,
            model=NAME,
            manufacturer=MANUFACTURER,
        )
