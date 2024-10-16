"""Support for Cambridge Audio AV Receiver."""

from __future__ import annotations

from datetime import datetime

from aiostreammagic import (
    RepeatMode as CambridgeRepeatMode,
    ShuffleMode,
    StreamMagicClient,
    TransportControl,
)
import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AIRABLE_ID,
    ATTR_AIRABLE_NAME,
    ATTR_RADIO_NAME,
    ATTR_RADIO_URL,
    SERVICE_PLAY_AIRABLE,
    SERVICE_PLAY_RADIO,
)
from .entity import CambridgeAudioEntity, command

BASE_FEATURES = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
)

PREAMP_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
)

TRANSPORT_FEATURES: dict[TransportControl, MediaPlayerEntityFeature] = {
    TransportControl.PLAY: MediaPlayerEntityFeature.PLAY,
    TransportControl.PAUSE: MediaPlayerEntityFeature.PAUSE,
    TransportControl.TRACK_NEXT: MediaPlayerEntityFeature.NEXT_TRACK,
    TransportControl.TRACK_PREVIOUS: MediaPlayerEntityFeature.PREVIOUS_TRACK,
    TransportControl.TOGGLE_REPEAT: MediaPlayerEntityFeature.REPEAT_SET,
    TransportControl.TOGGLE_SHUFFLE: MediaPlayerEntityFeature.SHUFFLE_SET,
    TransportControl.SEEK: MediaPlayerEntityFeature.SEEK,
    TransportControl.STOP: MediaPlayerEntityFeature.STOP,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cambridge Audio device based on a config entry."""
    client: StreamMagicClient = entry.runtime_data
    async_add_entities([CambridgeAudioDevice(client)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_PLAY_AIRABLE,
        {
            vol.Required(ATTR_AIRABLE_NAME): str,
            vol.Required(ATTR_AIRABLE_ID): cv.positive_int,
        },
        "play_airable",
    )
    platform.async_register_entity_service(
        SERVICE_PLAY_RADIO,
        {
            vol.Required(ATTR_RADIO_NAME): str,
            vol.Required(ATTR_RADIO_URL): str,
        },
        "play_radio",
    )


class CambridgeAudioDevice(CambridgeAudioEntity, MediaPlayerEntity):
    """Representation of a Cambridge Audio Media Player Device."""

    _attr_name = None
    _attr_media_content_type = MediaType.MUSIC
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(self, client: StreamMagicClient) -> None:
        """Initialize an Cambridge Audio entity."""
        super().__init__(client)
        self._attr_unique_id = client.info.unit_id

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Supported features for the media player."""
        controls = self.client.now_playing.controls
        features = BASE_FEATURES
        if self.client.state.pre_amp_mode:
            features |= PREAMP_FEATURES
        if TransportControl.PLAY_PAUSE in controls:
            features |= MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.PAUSE
        for control in controls:
            feature = TRANSPORT_FEATURES.get(control)
            if feature:
                features |= feature
        return features

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        media_state = self.client.play_state.state
        if media_state == "NETWORK":
            return MediaPlayerState.STANDBY
        if self.client.state.power:
            if media_state == "play":
                return MediaPlayerState.PLAYING
            if media_state == "pause":
                return MediaPlayerState.PAUSED
            if media_state == "connecting":
                return MediaPlayerState.BUFFERING
            if media_state in ("stop", "ready"):
                return MediaPlayerState.IDLE
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def source_list(self) -> list[str]:
        """Return a list of available input sources."""
        return [item.name for item in self.client.sources]

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return next(
            (
                item.name
                for item in self.client.sources
                if item.id == self.client.state.source
            ),
            None,
        )

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        return self.client.play_state.metadata.title

    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media, music track only."""
        return self.client.play_state.metadata.artist

    @property
    def media_album_name(self) -> str | None:
        """Album name of current playing media, music track only."""
        return self.client.play_state.metadata.album

    @property
    def media_image_url(self) -> str | None:
        """Image url of current playing media."""
        return self.client.play_state.metadata.art_url

    @property
    def media_duration(self) -> int | None:
        """Duration of the current media."""
        return self.client.play_state.metadata.duration

    @property
    def media_position(self) -> int | None:
        """Position of the current media."""
        return self.client.play_state.position

    @property
    def media_position_updated_at(self) -> datetime:
        """Last time the media position was updated."""
        return self.client.position_last_updated

    @property
    def is_volume_muted(self) -> bool | None:
        """Volume mute status."""
        return self.client.state.mute

    @property
    def volume_level(self) -> float | None:
        """Current pre-amp volume level."""
        volume = self.client.state.volume_percent or 0
        return volume / 100

    @property
    def shuffle(self) -> bool | None:
        """Current shuffle configuration."""
        mode_shuffle = self.client.play_state.mode_shuffle
        if not mode_shuffle:
            return False
        return mode_shuffle != ShuffleMode.OFF

    @property
    def repeat(self) -> RepeatMode | None:
        """Current repeat configuration."""
        mode_repeat = RepeatMode.OFF
        if self.client.play_state.mode_repeat == CambridgeRepeatMode.ALL:
            mode_repeat = RepeatMode.ALL
        return mode_repeat

    @command
    async def async_media_play_pause(self) -> None:
        """Toggle play/pause the current media."""
        await self.client.play_pause()

    @command
    async def async_media_pause(self) -> None:
        """Pause the current media."""
        controls = self.client.now_playing.controls
        if (
            TransportControl.PAUSE not in controls
            and TransportControl.PLAY_PAUSE in controls
        ):
            await self.client.play_pause()
        else:
            await self.client.pause()

    @command
    async def async_media_stop(self) -> None:
        """Stop the current media."""
        await self.client.stop()

    @command
    async def async_media_play(self) -> None:
        """Play the current media."""
        controls = self.client.now_playing.controls
        if (
            TransportControl.PLAY not in controls
            and TransportControl.PLAY_PAUSE in controls
        ):
            await self.client.play_pause()
        else:
            await self.client.play()

    @command
    async def async_media_next_track(self) -> None:
        """Skip to the next track."""
        await self.client.next_track()

    @command
    async def async_media_previous_track(self) -> None:
        """Skip to the previous track."""
        await self.client.previous_track()

    @command
    async def async_select_source(self, source: str) -> None:
        """Select the source."""
        for src in self.client.sources:
            if src.name == source:
                await self.client.set_source_by_id(src.id)
                break

    @command
    async def async_turn_on(self) -> None:
        """Power on the device."""
        await self.client.power_on()

    @command
    async def async_turn_off(self) -> None:
        """Power off the device."""
        await self.client.power_off()

    @command
    async def async_volume_up(self) -> None:
        """Step the volume up."""
        await self.client.volume_up()

    @command
    async def async_volume_down(self) -> None:
        """Step the volume down."""
        await self.client.volume_down()

    @command
    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume level."""
        await self.client.set_volume(int(volume * 100))

    @command
    async def async_mute_volume(self, mute: bool) -> None:
        """Set the mute state."""
        await self.client.set_mute(mute)

    @command
    async def async_media_seek(self, position: float) -> None:
        """Seek to a position in the current media."""
        await self.client.media_seek(int(position))

    @command
    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Set the shuffle mode for the current queue."""
        shuffle_mode = ShuffleMode.OFF
        if shuffle:
            shuffle_mode = ShuffleMode.ALL
        await self.client.set_shuffle(shuffle_mode)

    @command
    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Set the repeat mode for the current queue."""
        repeat_mode = CambridgeRepeatMode.OFF
        if repeat in {RepeatMode.ALL, RepeatMode.ONE}:
            repeat_mode = CambridgeRepeatMode.ALL
        await self.client.set_repeat(repeat_mode)

    @command
    async def play_airable(
        self, airable_radio_name: str, airable_radio_id: int
    ) -> None:
        """Play airable radio on Cambridge Audio device."""
        await self.client.play_radio_airable(airable_radio_name, airable_radio_id)

    @command
    async def play_radio(self, radio_name: str, radio_url: str) -> None:
        """Play radio on Cambridge Audio device."""
        await self.client.play_radio_url(radio_name, radio_url)
