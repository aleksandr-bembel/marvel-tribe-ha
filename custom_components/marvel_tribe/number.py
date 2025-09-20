"""Number platform for Marvel Tribe."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.number import NumberEntity
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
    """Set up Marvel Tribe number based on a config entry."""
    coordinator: MarvelTribeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = [
        MarvelTribeAmbientLightBrightnessNumber(coordinator, entry, "rgb_brightness"),
        MarvelTribeAmbientLightSpeedNumber(coordinator, entry, "rgb_speed"),
        MarvelTribeLCDBrightnessNumber(coordinator, entry, "lcd_brightness"),
        MarvelTribeVolumeKeyNumber(coordinator, entry, "volume_key"),
        MarvelTribeVolumeStartupNumber(coordinator, entry, "volume_startup"),
        MarvelTribeVolumeAlarmNumber(coordinator, entry, "volume_alarm"),
    ]

    async_add_entities(numbers)


class MarvelTribeNumber(NumberEntity):
    """Base class for Marvel Tribe numbers."""
    
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MarvelTribeDataUpdateCoordinator,
        entry: ConfigEntry,
        number_type: str,
    ) -> None:
        """Initialize the number."""
        self.coordinator = coordinator
        self.entry = entry
        self.number_type = number_type
        self._attr_unique_id = f"{entry.data['host']}:{entry.data['port']}_{number_type}"
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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class MarvelTribeAmbientLightBrightnessNumber(MarvelTribeNumber):
    """Ambient light brightness number."""

    _attr_name = "Ambient Light Brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 10  # Минимум 10, так как 0 не поддерживается
    _attr_native_max_value = 100
    _attr_native_step = 5  # Шаг 5 для удобства
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data:
            return data.get("rgb_brightness", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        try:
            # Get current ambient light config and update brightness
            current_data = self.coordinator.data or {}
            rgb_config = {
                "enable": current_data.get("rgb_enabled", True),
                "brightness": int(value),
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
                _LOGGER.info("ambient light brightness set to %d", value)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["rgb_brightness"] = int(value)
                    self.coordinator.protect_state_key("rgb_brightness", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set ambient light brightness")
        except Exception as err:
            _LOGGER.error("Error setting ambient light brightness: %s", err)


class MarvelTribeAmbientLightSpeedNumber(MarvelTribeNumber):
    """Ambient light speed number."""

    _attr_name = "Ambient Light Speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 10  # Минимум 10 для стабильности
    _attr_native_max_value = 100
    _attr_native_step = 5  # Шаг 5 для удобства
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data:
            return data.get("rgb_speed", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        try:
            # Get current ambient light config and update speed
            current_data = self.coordinator.data or {}
            rgb_config = {
                "enable": current_data.get("rgb_enabled", True),
                "brightness": current_data.get("rgb_brightness", 20),
                "speed": int(value),
                "effect": current_data.get("rgb_effect", 1),
                "easy_effect": ["#ff0000"] * 6,
                "breath_effect": ["#ff0000"] * 6,
                "unify_effect": "#000000"
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "rgb_light", rgb_config
            )
            if success:
                _LOGGER.info("ambient light speed set to %d", value)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["rgb_speed"] = int(value)
                    self.coordinator.protect_state_key("rgb_speed", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set ambient light speed")
        except Exception as err:
            _LOGGER.error("Error setting ambient light speed: %s", err)


class MarvelTribeLCDBrightnessNumber(MarvelTribeNumber):
    """LCD brightness number."""

    _attr_name = "LCD Brightness"
    _attr_icon = "mdi:brightness-7"
    _attr_native_min_value = 0  # Поддерживается полное выключение!
    _attr_native_max_value = 100
    _attr_native_step = 5  # Шаг 5 для удобства (можно любые значения)
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data:
            return data.get("lcd_brightness", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        try:
            # Get current others config and update LCD brightness
            # First get the full current config from device to preserve all settings
            current_config = await self.coordinator.client.send_property_command(
                "get_user_property", "others"
            )
            
            # Use data from coordinator as fallback
            current_data = self.coordinator.data or {}
            
            # Build complete others config preserving all existing values
            others_config = {
                "language": current_data.get("language", "en"),
                "lcd_brightness": int(value),
                "style": current_data.get("style", 0),
                "style_auto_switch": current_data.get("style_auto_switch", 0),
                "time_album_auto_switch": current_data.get("time_album_auto_switch", 0),
                "date_mode_date_duration": current_data.get("date_mode_date_duration", 60),
                "date_mode_time_duration": current_data.get("date_mode_time_duration", 60),
                "matrix_rain_color": current_data.get("matrix_rain_color", "#00ff00"),
                "display_mode": current_data.get("display_mode", 0)
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "others", others_config
            )
            if success:
                _LOGGER.info("LCD brightness set to %d", value)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["lcd_brightness"] = int(value)
                    self.coordinator.protect_state_key("lcd_brightness", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set LCD brightness")
        except Exception as err:
            _LOGGER.error("Error setting LCD brightness: %s", err)


class MarvelTribeVolumeKeyNumber(MarvelTribeNumber):
    """Volume key number."""

    _attr_name = "Volume Key"
    _attr_icon = "mdi:volume-high"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data:
            return data.get("volume_key", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        try:
            # Get current audio config and update volume_key
            current_data = self.coordinator.data or {}
            audio_config = {
                "enable": current_data.get("audio_enabled", True),
                "volume_key": int(value),
                "volume_startup": current_data.get("volume_startup", 50),
                "volume_alarm": current_data.get("volume_alarm", 50),
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "audio", audio_config
            )
            if success:
                _LOGGER.info("Volume key set to %d", value)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["volume_key"] = int(value)
                    self.coordinator.protect_state_key("volume_key", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set volume key")
        except Exception as err:
            _LOGGER.error("Error setting volume key: %s", err)


class MarvelTribeVolumeStartupNumber(MarvelTribeNumber):
    """Volume startup number."""

    _attr_name = "Volume Startup"
    _attr_icon = "mdi:volume-medium"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data:
            return data.get("volume_startup", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        try:
            # Get current audio config and update volume_startup
            current_data = self.coordinator.data or {}
            audio_config = {
                "enable": current_data.get("audio_enabled", True),
                "volume_key": current_data.get("volume_key", 50),
                "volume_startup": int(value),
                "volume_alarm": current_data.get("volume_alarm", 50),
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "audio", audio_config
            )
            if success:
                _LOGGER.info("Volume startup set to %d", value)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["volume_startup"] = int(value)
                    self.coordinator.protect_state_key("volume_startup", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set volume startup")
        except Exception as err:
            _LOGGER.error("Error setting volume startup: %s", err)


class MarvelTribeVolumeAlarmNumber(MarvelTribeNumber):
    """Volume alarm number."""

    _attr_name = "Volume Alarm"
    _attr_icon = "mdi:alarm"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data:
            return data.get("volume_alarm", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        try:
            # Get current audio config and update volume_alarm
            current_data = self.coordinator.data or {}
            audio_config = {
                "enable": current_data.get("audio_enabled", True),
                "volume_key": current_data.get("volume_key", 50),
                "volume_startup": current_data.get("volume_startup", 50),
                "volume_alarm": int(value),
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "audio", audio_config
            )
            if success:
                _LOGGER.info("Volume alarm set to %d", value)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["volume_alarm"] = int(value)
                    self.coordinator.protect_state_key("volume_alarm", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set volume alarm")
        except Exception as err:
            _LOGGER.error("Error setting volume alarm: %s", err)
