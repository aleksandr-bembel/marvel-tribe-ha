"""Data update coordinator for Marvel Tribe."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import SCAN_INTERVAL
from .websocket_client import MarvelTribeWebSocketClient

_LOGGER = logging.getLogger(__name__)


class MarvelTribeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Marvel Tribe."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.client = MarvelTribeWebSocketClient(
            entry.data["host"], entry.data["port"]
        )
        
        # Register message handlers
        self.client.register_message_handler("status", self._handle_status)
        self.client.register_message_handler("time", self._handle_time)
        self.client.register_message_handler("pong", self._handle_pong)
        self.client.register_message_handler("marvel_tribe_data", self._handle_marvel_tribe_response)
        
        # Cache for avoiding too frequent requests
        self._last_request_time = 0
        self._request_cache_timeout = 2  # seconds
        
        # Protection for local state changes
        self._protected_keys = {}  # key -> expiry_time

        super().__init__(
            hass,
            _LOGGER,
            name="Marvel Tribe",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via WebSocket."""
        if not self.client.connected:
            _LOGGER.info("Client not connected, attempting to connect...")
            try:
                if not await self.client.connect():
                    raise UpdateFailed("Failed to connect to Marvel Tribe")
            except Exception as err:
                _LOGGER.error("Connection failed: %s", err)
                raise UpdateFailed(f"Connection failed: {err}")

        try:
            # Avoid too frequent requests using cache
            current_time = time.time()
            if current_time - self._last_request_time < self._request_cache_timeout:
                _LOGGER.debug("Using cached data to avoid frequent requests")
                return self.data or {}
            
            self._last_request_time = current_time
            
            # Request status updates
            await self.client.get_status()
            await self.client.get_time()
            
            # Return current data (will be updated by message handlers)
            current_data = self.data or {}
            if not current_data:
                _LOGGER.info("First connection to Marvel Tribe - initializing with default values")
                # Initialize with default values
                current_data = {
                    "connected": self.client.connected,
                    "status": "unknown", 
                    "last_update": datetime.now().isoformat(),
                }
            
            return current_data
            
        except Exception as err:
            # If connection is lost, mark client as disconnected
            if "connection" in str(err).lower() or "websocket" in str(err).lower():
                self.client.connected = False
                _LOGGER.warning("Connection lost during update: %s", err)
            else:
                _LOGGER.error("Error updating data: %s", err)
            
            # Return cached data if available, otherwise raise error
            if self.data:
                _LOGGER.debug("Returning cached data due to connection error")
                return self.data
            else:
                raise UpdateFailed(f"Error communicating with Marvel Tribe: {err}")

    async def _handle_status(self, message: dict):
        """Handle status message."""
        data = message.get("data", {})
        current_data = self.data or {}
        current_data.update({
            "status": data.get("status", "connected"),
            "connected": True,  # If we receive data, we're connected
            "last_update": datetime.now().isoformat(),
        })
        self.data = current_data
        _LOGGER.debug("Updated status: %s", current_data)

    async def _handle_time(self, message: dict):
        """Handle time message."""
        data = message.get("data", {})
        current_data = self.data or {}
        current_data.update({
            "device_time": data.get("time", ""),
            "timezone": data.get("timezone", ""),
            "last_update": datetime.now().isoformat(),
        })
        self.data = current_data
        _LOGGER.debug("Updated time: %s", current_data)

    async def _handle_pong(self, message: dict):
        """Handle pong message."""
        current_data = self.data or {}
        current_data.update({
            "last_ping": datetime.now().isoformat(),
            "ping_successful": True,
            "last_update": datetime.now().isoformat(),
        })
        self.data = current_data
        _LOGGER.debug("Received pong: %s", current_data)

    async def _handle_marvel_tribe_response(self, message: dict):
        """Handle Marvel Tribe protocol response."""
        _LOGGER.debug("Received Marvel Tribe response: %s", message)
        
        # Extract data based on command type
        command = message.get("command")
        current_data = self.data or {}
        
        if command == 2:  # get_user_property response
            # Device info (property 2)
            if "2" in message:
                device_info = message["2"]
                current_data.update({
                    "firmware_version": device_info.get("firmware", "Unknown"),
                    "hardware_version": device_info.get("hardware", "Unknown"),
                    "serial_number": device_info.get("sn", "Unknown"),
                    "wifi_mac": device_info.get("wifi_mac", "Unknown"),
                })
            
            # Time info (property 3)
            if "3" in message:
                time_info = message["3"]
                current_data.update({
                    "device_time": datetime.fromtimestamp(time_info.get("timestamp", 0)).isoformat(),
                    "timezone": time_info.get("timezone", ""),
                    "timezone_info": time_info.get("timezone_city_info", ""),
                })
            
            # Ambient light info (property 7)
            if "7" in message:
                rgb_info = message["7"]
                rgb_updates = {}
                
                # Only update rgb_enabled if it's not protected
                if not self.is_key_protected("rgb_enabled"):
                    rgb_updates["rgb_enabled"] = rgb_info.get("enable", False)
                else:
                    _LOGGER.debug("Skipping rgb_enabled update - key is protected")
                
                # Other RGB properties - check protection for each
                if not self.is_key_protected("rgb_brightness"):
                    rgb_updates["rgb_brightness"] = rgb_info.get("brightness", 0)
                if not self.is_key_protected("rgb_speed"):
                    rgb_updates["rgb_speed"] = rgb_info.get("speed", 0)
                if not self.is_key_protected("rgb_effect"):
                    rgb_updates["rgb_effect"] = rgb_info.get("effect", 0)
                
                current_data.update(rgb_updates)
            
            # WiFi info (property 8)
            if "8" in message:
                wifi_info = message["8"]
                current_data.update({
                    "wifi_connected": wifi_info.get("sta_enable", False),
                    "ip_address": wifi_info.get("ipv4", ""),
                    "wifi_ssid": wifi_info.get("ssid", ""),
                })
            
            # Audio info (property 9)
            if "9" in message:
                audio_info = message["9"]
                audio_updates = {}
                
                # Only update audio_enabled if it's not protected
                if not self.is_key_protected("audio_enabled"):
                    audio_updates["audio_enabled"] = audio_info.get("enable", False)
                else:
                    _LOGGER.debug("Skipping audio_enabled update - key is protected")
                
                # Other audio properties - check protection for each
                if not self.is_key_protected("volume_key"):
                    audio_updates["volume_key"] = audio_info.get("volume_key", 0)
                if not self.is_key_protected("volume_startup"):
                    audio_updates["volume_startup"] = audio_info.get("volume_startup", 0)
                if not self.is_key_protected("volume_alarm"):
                    audio_updates["volume_alarm"] = audio_info.get("volume_alarm", 0)
                
                current_data.update(audio_updates)
            
            # LCD info (property 12)
            if "12" in message:
                lcd_info = message["12"]
                lcd_updates = {}
                
                # Check protection for LCD brightness
                if not self.is_key_protected("lcd_brightness"):
                    lcd_updates["lcd_brightness"] = lcd_info.get("lcd_brightness", 0)
                else:
                    _LOGGER.debug("Skipping lcd_brightness update - key is protected")
                
                # Other LCD properties can be updated normally
                lcd_updates.update({
                    "language": lcd_info.get("language", "en"),
                    "display_mode": lcd_info.get("display_mode", 0),
                    "style": lcd_info.get("style", 0),
                    "style_auto_switch": lcd_info.get("style_auto_switch", 0),
                    "time_album_auto_switch": lcd_info.get("time_album_auto_switch", 0),
                    "matrix_rain_color": lcd_info.get("matrix_rain_color", "#00ff00"),
                    "date_mode_date_duration": lcd_info.get("date_mode_date_duration", 60),
                    "date_mode_time_duration": lcd_info.get("date_mode_time_duration", 60),
                })
                
                current_data.update(lcd_updates)
            
            # Alarm info (property 4)
            if "4" in message:
                alarm_info = message["4"]
                current_data.update({
                    "alarm_system_enabled": alarm_info.get("enable", False),
                    "alarms": alarm_info.get("alarm", []),
                })
                
                # Process individual alarms for easy access
                alarms = alarm_info.get("alarm", [])
                for i, alarm in enumerate(alarms):
                    current_data[f"alarm_{i}_enabled"] = alarm.get("enable", False)
                    current_data[f"alarm_{i}_time"] = alarm.get("moment", "00:00")
                    current_data[f"alarm_{i}_repeat"] = alarm.get("repeat", False)
                    current_data[f"alarm_{i}_rgb_flash"] = alarm.get("rgb_flash", False)
                    
                    # Days of week
                    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    current_data[f"alarm_{i}_days"] = [day for day in days if alarm.get(day, False)]
            
            # Auto-sleep info (property 6)
            if "6" in message:
                autosleep_info = message["6"]
                autosleep_updates = {}
                
                # Only update auto_sleep_enabled if it's not protected
                if not self.is_key_protected("auto_sleep_enabled"):
                    autosleep_updates["auto_sleep_enabled"] = autosleep_info.get("enable", False)
                else:
                    _LOGGER.debug("Skipping auto_sleep_enabled update - key is protected")
                
                # Other auto-sleep properties can be updated normally
                autosleep_updates.update({
                    "auto_sleep_start": autosleep_info.get("start", "00:00"),
                    "auto_sleep_end": autosleep_info.get("end", "00:00"),
                })
                
                current_data.update(autosleep_updates)
        
        elif command == 8:  # characteristic response
            char_data = message.get("data", {})
            current_data.update({
                "screen_width": char_data.get("screen_width", 0),
                "screen_height": char_data.get("screen_height", 0),
                "style_count": char_data.get("style_count", 0),
            })
        
        # Update connection status
        current_data.update({
            "connected": True,
            "status": "connected",
            "last_update": datetime.now().isoformat(),
        })
        
        self.data = current_data
        _LOGGER.debug("Updated Marvel Tribe data: %s", current_data)

    def protect_state_key(self, key: str, duration: float = 2.0):
        """Protect a state key from being overwritten for a duration."""
        import time
        self._protected_keys[key] = time.time() + duration
        _LOGGER.debug("Protected key %s for %.1f seconds", key, duration)
    
    def is_key_protected(self, key: str) -> bool:
        """Check if a key is currently protected."""
        import time
        if key not in self._protected_keys:
            return False
        
        if time.time() > self._protected_keys[key]:
            # Protection expired
            del self._protected_keys[key]
            return False
        
        return True

    async def async_shutdown(self):
        """Shutdown the coordinator."""
        await self.client.disconnect()
        await super().async_shutdown()
