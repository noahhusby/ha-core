"""Support for media browsing."""
from typing_extensions import Optional

from homeassistant.components.media_player import BrowseMedia, MediaClass
from homeassistant.core import HomeAssistant


async def async_browse_media(
        hass: HomeAssistant,
        media_content_id: Optional[str],
        media_content_type: Optional[str],
) -> BrowseMedia:
    """Browse media."""
    if media_content_id is None:
        return await root_payload(
            hass,
        )

async def root_payload(
        hass: HomeAssistant,
) -> BrowseMedia:
    return BrowseMedia(
        title="Cambridge Audio",
        media_class=MediaClass.DIRECTORY,
        media_content_id="",
        media_content_type="root",
        can_play=False,
        can_expand=True,
    )