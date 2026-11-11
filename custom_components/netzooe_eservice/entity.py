# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Base entity for the Netz OÖ eService integration."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import NetzOOEeServiceDataUpdateCoordinator


class NetzOOEeServiceEntity(CoordinatorEntity[NetzOOEeServiceDataUpdateCoordinator]):
    """Netz OÖ eService base entity."""

    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: NetzOOEeServiceDataUpdateCoordinator,
        device_identifier: str,
    ) -> None:
        """Initialize the Netz OÖ eService entity."""
        super().__init__(coordinator)
        self.device_identifier: str = device_identifier
        self._attr_device_info = coordinator.device_info(device_identifier)
