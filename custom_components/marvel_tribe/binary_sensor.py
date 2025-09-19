"""Binary sensor platform for Marvel Tribe."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
    """Set up Marvel Tribe binary sensor based on a config entry."""
    coordinator: MarvelTribeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    binary_sensors = [
        MarvelTribeConnectionBinarySensor(coordinator, entry, "connected"),
        MarvelTribeChargingBinarySensor(coordinator, entry, "charging"),
        # Новые binary sensors на основе реальных данных
        MarvelTribeWiFiConnectedBinarySensor(coordinator, entry, "wifi_connected"),
        MarvelTribeRGBEnabledBinarySensor(coordinator, entry, "rgb_enabled"),
        MarvelTribeAudioEnabledBinarySensor(coordinator, entry, "audio_enabled"),
        MarvelTribeAlarmSystemBinarySensor(coordinator, entry, "alarm_system"),
        MarvelTribeAutoSleepBinarySensor(coordinator, entry, "auto_sleep"),
    ]

    async_add_entities(binary_sensors)


class MarvelTribeBinarySensor(BinarySensorEntity):
    """Base class for Marvel Tribe binary sensors."""
    
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MarvelTribeDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
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


class MarvelTribeConnectionBinarySensor(MarvelTribeBinarySensor):
    """Connection status binary sensor."""

    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:wifi"

    @property
    def is_on(self) -> bool | None:
        """Return if the device is connected."""
        data = self.coordinator.data
        if data:
            return data.get("connected", False)


class MarvelTribeChargingBinarySensor(MarvelTribeBinarySensor):
    """Charging status binary sensor."""

    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_icon = "mdi:battery-charging"

    @property
    def is_on(self) -> bool | None:
        """Return if the device is charging."""
        data = self.coordinator.data
        if data:
            return data.get("battery_charging", False)


class MarvelTribeWiFiConnectedBinarySensor(MarvelTribeBinarySensor):
    """WiFi connected binary sensor."""

    _attr_name = "WiFi Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:wifi"

    @property
    def is_on(self) -> bool | None:
        """Return if WiFi is connected."""
        data = self.coordinator.data
        if data:
            return data.get("wifi_connected", False)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "ssid": data.get("wifi_ssid", ""),
            "ip_address": data.get("ip_address", ""),
        }


class MarvelTribeRGBEnabledBinarySensor(MarvelTribeBinarySensor):
    """RGB enabled binary sensor."""

    _attr_name = "RGB Enabled"
    _attr_icon = "mdi:led-on"

    @property
    def is_on(self) -> bool | None:
        """Return if RGB is enabled."""
        data = self.coordinator.data
        if data:
            return data.get("rgb_enabled", False)

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "brightness": data.get("rgb_brightness", 0),
            "speed": data.get("rgb_speed", 0),
            "effect": data.get("rgb_effect", 0),
        }


class MarvelTribeAudioEnabledBinarySensor(MarvelTribeBinarySensor):
    """Audio enabled binary sensor."""

    _attr_name = "Audio Enabled"
    _attr_icon = "mdi:volume-high"

    @property
    def is_on(self) -> bool | None:
        """Return if audio is enabled."""
        data = self.coordinator.data
        if data:
            return data.get("audio_enabled", False)

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "volume_key": data.get("volume_key", 0),
            "volume_startup": data.get("volume_startup", 0),
            "volume_alarm": data.get("volume_alarm", 0),
        }


class MarvelTribeAlarmSystemBinarySensor(MarvelTribeBinarySensor):
    """Alarm system binary sensor."""

    _attr_name = "Alarm System"
    _attr_icon = "mdi:alarm"

    @property
    def is_on(self) -> bool | None:
        """Return if alarm system is enabled."""
        data = self.coordinator.data
        if data:
            return data.get("alarm_system_enabled", False)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        active_alarms = 0
        alarm_times = []
        
        for i in range(6):
            if data.get(f"alarm_{i}_enabled", False):
                active_alarms += 1
                alarm_times.append(data.get(f"alarm_{i}_time", "00:00"))
        
        return {
            "active_alarms_count": active_alarms,
            "alarm_times": alarm_times,
            "total_slots": 6,
        }


class MarvelTribeAutoSleepBinarySensor(MarvelTribeBinarySensor):
    """Auto sleep binary sensor."""

    _attr_name = "Auto Sleep Active"
    _attr_icon = "mdi:sleep"

    @property
    def is_on(self) -> bool | None:
        """Return if auto sleep is active."""
        data = self.coordinator.data
        if data:
            return data.get("auto_sleep_enabled", False)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return extra state attributes."""
        data = self.coordinator.data or {}
        return {
            "start_time": data.get("auto_sleep_start", "00:00"),
            "end_time": data.get("auto_sleep_end", "00:00"),
            "schedule": f"{data.get('auto_sleep_start', '00:00')} - {data.get('auto_sleep_end', '00:00')}",
        }
