"""Russound RIO integration services."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import re
from typing import Any, Final

from aiorussound.rio import RussoundClient, ZoneControlSurface
import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import (
    EntityServiceResponse,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.service import async_extract_referenced_entity_ids
from homeassistant.helpers.typing import VolSchemaType

from .const import ATTR_ENABLED, DOMAIN

SERVICE_SET_LOUDNESS = "set_loudness"

SET_LOUDNESS_SCHEMA = vol.All(
    vol.Schema(
        {
            **cv.ENTITY_SERVICE_FIELDS,
            vol.Required(ATTR_ENABLED): cv.boolean,
        }
    ),
    cv.has_at_least_one_key(ATTR_ENTITY_ID),
)


@dataclass(frozen=True)
class EntityServiceDescription:
    """Describe an entity service."""

    name: str
    method: Callable[
        [ServiceCall],
        Coroutine[Any, Any, ServiceResponse | EntityServiceResponse]
        | ServiceResponse
        | EntityServiceResponse
        | None,
    ]
    schema: VolSchemaType | None = None
    supports_response: SupportsResponse = SupportsResponse.NONE

    def async_register(self, hass: HomeAssistant) -> None:
        """Register the service with the platform."""
        hass.services.async_register(
            DOMAIN,
            self.name,
            self.method,
            self.schema,
            supports_response=self.supports_response,
        )


@callback
def _async_get_zones_from_call(call: ServiceCall) -> list[ZoneControlSurface]:
    """Extract zones from call."""
    zones = []
    for entity_id in async_extract_referenced_entity_ids(call.hass, call).referenced:
        entity_registry = er.async_get(call.hass)
        entry = entity_registry.async_get(entity_id)
        if not entry:
            continue

        config_entry_id = entry.config_entry_id
        if not config_entry_id:
            continue

        pattern = r"-C\[(.*?)\]\.Z\[(.*?)\]"
        match = re.search(pattern, entry.unique_id)
        if not match:
            continue
        controller_id = int(match.group(1))
        zone_id = int(match.group(2))
        config_entry = call.hass.config_entries.async_get_entry(config_entry_id)
        if not config_entry:
            continue
        client: RussoundClient = config_entry.runtime_data
        zones.append(client.controllers[controller_id].zones[zone_id])
    return zones


async def set_loudness(call: ServiceCall) -> None:
    """Set zone loudness."""
    enabled: bool = call.data[ATTR_ENABLED]
    zones = _async_get_zones_from_call(call)
    for zone in zones:
        await zone.set_loudness(enabled)


SERVICES: Final = (
    EntityServiceDescription(SERVICE_SET_LOUDNESS, set_loudness, SET_LOUDNESS_SCHEMA),
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the Russound RIO services."""

    for service in SERVICES:
        service.async_register(hass)
