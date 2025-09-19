"""Sensor platform for Marvel Tribe."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfTime
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
    """Set up Marvel Tribe sensor based on a config entry."""
    coordinator: MarvelTribeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        # Основные сенсоры
        MarvelTribeDeviceTimeSensor(coordinator, entry, "device_time"),
        MarvelTribeFirmwareVersionSensor(coordinator, entry, "firmware_version"),
        # WiFi (только основное)
        MarvelTribeWiFiSSIDSensor(coordinator, entry, "wifi_ssid"),
        MarvelTribeIPAddressSensor(coordinator, entry, "ip_address"),
        # Ambient Light и LCD мониторинг
        MarvelTribeAmbientLightBrightnessSensor(coordinator, entry, "rgb_brightness"),
        MarvelTribeLCDBrightnessSensor(coordinator, entry, "lcd_brightness"),
        # Аудио
        MarvelTribeVolumeKeySensor(coordinator, entry, "volume_key"),
        # Система
        MarvelTribleLanguageSensor(coordinator, entry, "language"),
        # Будильники и auto-sleep
        MarvelTribeAutoSleepPeriodSensor(coordinator, entry, "auto_sleep_period"),
        MarvelTribeActiveAlarmsSensor(coordinator, entry, "active_alarms"),
        # Диагностика
        MarvelTribeLastUpdateSensor(coordinator, entry, "last_update"),
    ]

    async_add_entities(sensors)


class MarvelTribeSensor(SensorEntity):
    """Base class for Marvel Tribe sensors."""
    
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MarvelTribeDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entry = entry
        self.sensor_type = sensor_type
        self._attr_unique_id = f"{entry.data['host']}:{entry.data['port']}_{sensor_type}"
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


class MarvelTribeDeviceTimeSensor(MarvelTribeSensor):
    """Device time sensor."""

    _attr_name = "Device Time"
    _attr_icon = "mdi:clock-digital"

    @property
    def native_value(self) -> str | None:
        """Return the device time."""
        data = self.coordinator.data
        if data:
            return data.get("device_time")

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "timezone": data.get("timezone", ""),
        }


class MarvelTribeFirmwareVersionSensor(MarvelTribeSensor):
    """Firmware version sensor."""

    _attr_name = "Firmware Version"
    _attr_icon = "mdi:memory"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        data = self.coordinator.data
        if data:
            return data.get("firmware_version")


class MarvelTribeWiFiSSIDSensor(MarvelTribeSensor):
    """WiFi SSID sensor."""

    _attr_name = "WiFi SSID"
    _attr_icon = "mdi:wifi-settings"

    @property
    def native_value(self) -> str | None:
        """Return the WiFi SSID."""
        data = self.coordinator.data
        if data:
            return data.get("wifi_ssid")


class MarvelTribeIPAddressSensor(MarvelTribeSensor):
    """IP address sensor."""

    _attr_name = "IP Address"
    _attr_icon = "mdi:ip-network"

    @property
    def native_value(self) -> str | None:
        """Return the IP address."""
        data = self.coordinator.data
        if data:
            return data.get("ip_address")


class MarvelTribeAmbientLightBrightnessSensor(MarvelTribeSensor):
    """Ambient light brightness sensor."""

    _attr_name = "Ambient Light Brightness"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:led-variant-on"

    @property
    def native_value(self) -> int | None:
        """Return the ambient light brightness."""
        data = self.coordinator.data
        if data:
            return data.get("rgb_brightness")

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "rgb_enabled": data.get("rgb_enabled", False),
            "rgb_speed": data.get("rgb_speed", 0),
            "rgb_effect": data.get("rgb_effect", 0),
        }


class MarvelTribeLCDBrightnessSensor(MarvelTribeSensor):
    """LCD brightness sensor."""

    _attr_name = "LCD Brightness"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:monitor-shimmer"

    @property
    def native_value(self) -> int | None:
        """Return the LCD brightness."""
        data = self.coordinator.data
        if data:
            return data.get("lcd_brightness")

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "display_mode": data.get("display_mode", 0),
            "language": data.get("language", "en"),
        }


class MarvelTribeVolumeKeySensor(MarvelTribeSensor):
    """Volume key sensor."""

    _attr_name = "Volume Key"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:keyboard-variant"

    @property
    def native_value(self) -> int | None:
        """Return the volume key level."""
        data = self.coordinator.data
        if data:
            return data.get("volume_key")

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "audio_enabled": data.get("audio_enabled", False),
            "volume_startup": data.get("volume_startup", 0),
            "volume_alarm": data.get("volume_alarm", 0),
        }


class MarvelTribleLanguageSensor(MarvelTribeSensor):
    """Language sensor."""

    _attr_name = "Language"
    _attr_icon = "mdi:web"

    @property
    def native_value(self) -> str | None:
        """Return the language."""
        data = self.coordinator.data
        if data:
            return data.get("language")


class MarvelTribeAutoSleepPeriodSensor(MarvelTribeSensor):
    """Auto-sleep period sensor."""

    _attr_name = "Auto Sleep Period"
    _attr_icon = "mdi:timer-sleep"

    @property
    def native_value(self) -> str | None:
        """Return the auto-sleep period."""
        data = self.coordinator.data
        if data and data.get("auto_sleep_enabled", False):
            start = data.get("auto_sleep_start", "00:00")
            end = data.get("auto_sleep_end", "00:00")
            return f"{start} - {end}"
        return "Disabled"

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "enabled": data.get("auto_sleep_enabled", False),
            "start_time": data.get("auto_sleep_start", "00:00"),
            "end_time": data.get("auto_sleep_end", "00:00"),
        }


class MarvelTribeActiveAlarmsSensor(MarvelTribeSensor):
    """Active alarms sensor."""

    _attr_name = "Active Alarms"
    _attr_icon = "mdi:alarm-multiple"

    @property
    def native_value(self) -> int | None:
        """Return the number of active alarms."""
        data = self.coordinator.data
        if data:
            active_count = 0
            for i in range(6):  # 6 alarm slots
                if data.get(f"alarm_{i}_enabled", False):
                    active_count += 1
            return active_count
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        alarms_info = {}
        
        for i in range(6):
            if data.get(f"alarm_{i}_enabled", False):
                alarms_info[f"alarm_{i}"] = {
                    "time": data.get(f"alarm_{i}_time", "00:00"),
                    "repeat": data.get(f"alarm_{i}_repeat", False),
                    "rgb_flash": data.get(f"alarm_{i}_rgb_flash", False),
                    "days": data.get(f"alarm_{i}_days", []),
                }
        
        return {
            "system_enabled": data.get("alarm_system_enabled", False),
            "active_alarms": alarms_info,
        }


class MarvelTribeLastUpdateSensor(MarvelTribeSensor):
    """Last update sensor."""

    _attr_name = "Last Update"
    _attr_icon = "mdi:update"

    @property
    def native_value(self) -> str | None:
        """Return the last update time."""
        data = self.coordinator.data
        if data:
            return data.get("last_update")

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        last_update_time = getattr(self.coordinator, 'last_update_success', None)
        return {
            "coordinator_last_update": last_update_time.isoformat() if last_update_time else None,
            "data_age_seconds": (datetime.now() - last_update_time).total_seconds() if last_update_time else None,
            "update_count": getattr(self.coordinator, 'update_count', 0),
            "failed_count": getattr(self.coordinator, 'failed_count', 0),
        }
