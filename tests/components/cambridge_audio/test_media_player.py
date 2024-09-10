"""Tests for the Cambridge Audio media player."""
from unittest.mock import AsyncMock, patch

import pytest
from syrupy import SnapshotAssertion
from syrupy.filters import props

from homeassistant.components.cambridge_audio.media_player import CambridgeAudioDevice
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.util.decorator import Registry
from tests.common import MockConfigEntry, snapshot_platform
from tests.components.cambridge_audio import setup_integration
from homeassistant.helpers import entity_registry as er

async def setup(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_stream_magic_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> RegistryEntry:
    """Test all entities."""
    with patch("homeassistant.components.cambridge_audio.PLATFORMS", [Platform.MEDIA_PLAYER]):
        await setup_integration(hass, mock_config_entry)

    entity_entries = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)
    return entity_entries[0]


