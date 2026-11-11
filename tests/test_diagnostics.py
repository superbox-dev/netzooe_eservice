# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Tests for the diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest
from pytest_homeassistant.components.diagnostics import get_diagnostics_for_config_entry
from syrupy.filters import props

from tests.const import NOW

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.util.json import JsonObjectType
    from pytest_homeassistant.common import MockConfigEntry
    from pytest_homeassistant.typing import ClientSessionGenerator
    from syrupy.assertion import SnapshotAssertion


pytestmark: Final = pytest.mark.freeze_time(NOW)


@pytest.mark.usefixtures("init_integration")
async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that the diagnostics contain the data without credentials and customer numbers."""
    diagnostics: JsonObjectType = await get_diagnostics_for_config_entry(hass, hass_client, mock_config_entry)

    assert diagnostics == snapshot(exclude=props("created_at", "modified_at", "entry_id"))
