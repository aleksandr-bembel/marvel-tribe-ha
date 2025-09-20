"""Switch platform for Marvel Tribe."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, DEVICE_MODEL, DEVICE_SW_VERSION
from .coordinator import MarvelTribeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marvel Tribe switch based on a config entry."""
    coordinator: MarvelTribeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    switches = [
        # Переключатели на основе реальных данных
        MarvelTribeAmbientLightSwitch(coordinator, entry, "rgb_light"),
        MarvelTribeAudioSwitch(coordinator, entry, "audio"),
        MarvelTribeAutoSleepSwitch(coordinator, entry, "auto_sleep"),
    ]

    async_add_entities(switches)


class MarvelTribeSwitch(SwitchEntity):
    """Base class for Marvel Tribe switches."""
    
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MarvelTribeDataUpdateCoordinator,
        entry: ConfigEntry,
        switch_type: str,
    ) -> None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self.entry = entry
        self.switch_type = switch_type
        self._attr_unique_id = f"{entry.data['host']}:{entry.data['port']}_{switch_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.data['host']}:{entry.data['port']}")},
            name=entry.data["name"],
            manufacturer=MANUFACTURER,
            model=DEVICE_MODEL,
            sw_version=DEVICE_SW_VERSION,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class MarvelTribeAmbientLightSwitch(MarvelTribeSwitch):
    """Ambient light switch."""

    _attr_name = "Ambient Light"
    _attr_icon = "mdi:led-on"

    @property
    def is_on(self) -> bool:
        """Return if ambient light light is on."""
        data = self.coordinator.data
        if data:
            return data.get("rgb_enabled", False)
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on ambient light light."""
        try:
            # Get current ambient light config and update enable field
            current_data = self.coordinator.data or {}
            rgb_config = {
                "enable": True,
                "brightness": current_data.get("rgb_brightness", 20),
                "speed": current_data.get("rgb_speed", 20),
                "effect": current_data.get("rgb_effect", 1),
                "easy_effect": ["#ff0000"] * 6,  # Default colors
                "breath_effect": ["#ff0000"] * 6,
                "unify_effect": "#000000"
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "rgb_light", rgb_config
            )
            if success:
                _LOGGER.info("ambient light light turned on")
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["rgb_enabled"] = True
                    self.coordinator.protect_state_key("rgb_enabled", 3.0)  # Protect for 3 seconds
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners (including binary sensors)
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to turn on ambient light light")
        except Exception as err:
            _LOGGER.error("Error turning on ambient light light: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off ambient light light."""
        try:
            # Get current ambient light config and update enable field
            current_data = self.coordinator.data or {}
            rgb_config = {
                "enable": False,
                "brightness": current_data.get("rgb_brightness", 20),
                "speed": current_data.get("rgb_speed", 20),
                "effect": current_data.get("rgb_effect", 1),
                "easy_effect": ["#ff0000"] * 6,
                "breath_effect": ["#ff0000"] * 6,
                "unify_effect": "#000000"
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "rgb_light", rgb_config
            )
            if success:
                _LOGGER.info("ambient light light turned off")
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["rgb_enabled"] = False
                    self.coordinator.protect_state_key("rgb_enabled", 3.0)  # Protect for 3 seconds
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners (including binary sensors)
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to turn off ambient light light")
        except Exception as err:
            _LOGGER.error("Error turning off ambient light light: %s", err)


class MarvelTribeAudioSwitch(MarvelTribeSwitch):
    """Audio switch."""

    _attr_name = "Audio"
    _attr_icon = "mdi:volume-high"

    @property
    def is_on(self) -> bool:
        """Return if audio is on."""
        data = self.coordinator.data
        if data:
            return data.get("audio_enabled", False)
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on audio."""
        try:
            # Send command to enable audio
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "audio", {"enable": True}
            )
            if success:
                _LOGGER.info("Audio turned on")
                # Request updated data
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn on audio")
        except Exception as err:
            _LOGGER.error("Error turning on audio: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off audio."""
        try:
            # Send command to disable audio
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "audio", {"enable": False}
            )
            if success:
                _LOGGER.info("Audio turned off")
                # Request updated data
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn off audio")
        except Exception as err:
            _LOGGER.error("Error turning off audio: %s", err)


class MarvelTribeAutoSleepSwitch(MarvelTribeSwitch):
    """Auto sleep switch."""

    _attr_name = "Auto Sleep"
    _attr_icon = "mdi:sleep"

    @property
    def is_on(self) -> bool:
        """Return if auto sleep is on."""
        data = self.coordinator.data
        if data:
            return data.get("auto_sleep_enabled", False)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "start_time": data.get("auto_sleep_start", "00:00"),
            "end_time": data.get("auto_sleep_end", "00:00"),
            "period": f"{data.get('auto_sleep_start', '00:00')} - {data.get('auto_sleep_end', '00:00')}",
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on auto sleep."""
        try:
            # Get current auto-sleep config and enable it
            current_data = self.coordinator.data or {}
            autosleep_config = {
                "enable": True,
                "start": current_data.get("auto_sleep_start", "22:00"),
                "end": current_data.get("auto_sleep_end", "07:00")
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "auto_sleep", autosleep_config
            )
            if success:
                _LOGGER.info("Auto sleep turned on")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn on auto sleep")
        except Exception as err:
            _LOGGER.error("Error turning on auto sleep: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off auto sleep."""
        try:
            # Get current auto-sleep config and disable it
            current_data = self.coordinator.data or {}
            autosleep_config = {
                "enable": False,
                "start": current_data.get("auto_sleep_start", "22:00"),
                "end": current_data.get("auto_sleep_end", "07:00")
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "auto_sleep", autosleep_config
            )
            if success:
                _LOGGER.info("Auto sleep turned off")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn off auto sleep")
        except Exception as err:
            _LOGGER.error("Error turning off auto sleep: %s", err)
