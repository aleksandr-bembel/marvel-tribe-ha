"""Button platform for Marvel Tribe."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up Marvel Tribe button based on a config entry."""
    coordinator: MarvelTribeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    buttons = [
        MarvelTribeSyncTimeButton(coordinator, entry, "sync_time"),
        MarvelTribePingButton(coordinator, entry, "ping_device"),
        MarvelTribeRefreshButton(coordinator, entry, "refresh_data"),
        # Новые кнопки на основе реальных функций
        MarvelTribeScanWiFiButton(coordinator, entry, "scan_wifi"),
        MarvelTribeGetDeviceInfoButton(coordinator, entry, "get_device_info"),
    ]

    async_add_entities(buttons)


class MarvelTribeButton(ButtonEntity):
    """Base class for Marvel Tribe buttons."""
    
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MarvelTribeDataUpdateCoordinator,
        entry: ConfigEntry,
        button_type: str,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self.entry = entry
        self.button_type = button_type
        self._attr_unique_id = f"{entry.data['host']}:{entry.data['port']}_{button_type}"
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


class MarvelTribeSyncTimeButton(MarvelTribeButton):
    """Sync time button."""

    _attr_name = "Sync Time"
    _attr_icon = "mdi:clock-sync"

    async def async_press(self) -> None:
        """Handle the button press."""
        from datetime import datetime
        
        # Send current time to device
        current_time = datetime.now().timestamp()
        await self.coordinator.client.set_time(current_time)
        _LOGGER.info("Time sync requested")


class MarvelTribePingButton(MarvelTribeButton):
    """Ping button."""

    _attr_name = "Ping Device"
    _attr_icon = "mdi:network"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.client.ping()
        _LOGGER.info("Ping sent to device")


class MarvelTribeRefreshButton(MarvelTribeButton):
    """Refresh data button."""

    _attr_name = "Refresh Data"
    _attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Data refresh requested")


class MarvelTribeScanWiFiButton(MarvelTribeButton):
    """Scan WiFi button."""

    _attr_name = "Scan WiFi"
    _attr_icon = "mdi:wifi-refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self.coordinator.client.scan_wifi()
            if success:
                _LOGGER.info("WiFi scan initiated")
                # Wait a moment then refresh data
                await asyncio.sleep(2)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to initiate WiFi scan")
        except Exception as err:
            _LOGGER.error("Error scanning WiFi: %s", err)


class MarvelTribeGetDeviceInfoButton(MarvelTribeButton):
    """Get device info button."""

    _attr_name = "Get Device Info"
    _attr_icon = "mdi:information"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self.coordinator.client.get_device_info()
            if success:
                _LOGGER.info("Device info requested")
                # Wait a moment then refresh data
                await asyncio.sleep(1)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to get device info")
        except Exception as err:
            _LOGGER.error("Error getting device info: %s", err)
