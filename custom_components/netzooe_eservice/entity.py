# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Base entity for the Netz OÖ eService integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME
from .const import SHORT_DEVICE_ID_PATTERN
from .coordinator import NetzOOEeServiceConfigEntry
from .coordinator import NetzOOEeServiceDataUpdateCoordinator

if TYPE_CHECKING:
    import re
    from collections.abc import Mapping


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
    def data(self) -> Mapping[str, Any]:
        """Return the device data from the coordinator."""
        data: Mapping[str, Any] = self.coordinator.data[self.device_identifier]
        return data

    @property
    def device_name(self) -> str:
        """Return the name of the device."""
        return f"{self.data['deviceName']} ({self._short_device_id(self.device_identifier)})"

    @staticmethod
    def _short_device_id(device_id: str) -> str:
        """Return the short form of a meter point or energy community ID, e.g. for device names."""
        match: re.Match[str] | None = SHORT_DEVICE_ID_PATTERN.search(device_id)
        return match.group(1) if match else device_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_identifier)},
            name=self.device_name,
            model=NAME,
            manufacturer=MANUFACTURER,
        )
