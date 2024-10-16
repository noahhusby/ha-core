"""Constants for the Cambridge Audio integration."""

import asyncio
import logging

from aiostreammagic import StreamMagicConnectionError, StreamMagicError

DOMAIN = "cambridge_audio"

SERVICE_PLAY_AIRABLE = "play_airable"
ATTR_AIRABLE_ID = "airable_radio_id"

SERVICE_PLAY_RADIO = "play_radio"
ATTR_STATION_NAME = "station_name"
ATTR_RADIO_URL = "radio_url"
LOGGER = logging.getLogger(__package__)

STREAM_MAGIC_EXCEPTIONS = (
    StreamMagicConnectionError,
    StreamMagicError,
    asyncio.CancelledError,
    TimeoutError,
)

CONNECT_TIMEOUT = 5
