"""Select platform for Marvel Tribe."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
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
    """Set up Marvel Tribe select based on a config entry."""
    coordinator: MarvelTribeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    selects = [
        MarvelTribeRGBEffectSelect(coordinator, entry, "rgb_effect"),
    ]

    async_add_entities(selects)


class MarvelTribeSelect(SelectEntity):
    """Base class for Marvel Tribe selects."""
    
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MarvelTribeDataUpdateCoordinator,
        entry: ConfigEntry,
        select_type: str,
    ) -> None:
        """Initialize the select."""
        self.coordinator = coordinator
        self.entry = entry
        self.select_type = select_type
        self._attr_unique_id = f"{entry.data['host']}:{entry.data['port']}_{select_type}"
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


class MarvelTribeRGBEffectSelect(MarvelTribeSelect):
    """RGB effect select."""

    _attr_name = "RGB Effect"
    _attr_icon = "mdi:palette"
    _attr_options = ["Rainbow", "Flow", "Breath", "Mono"]

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        data = self.coordinator.data
        if data:
            effect = data.get("rgb_effect", 0)
            effect_map = {0: "Rainbow", 1: "Flow", 2: "Breath", 3: "Mono"}
            return effect_map.get(effect, "Rainbow")

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        try:
            effect_map = {"Rainbow": 0, "Flow": 1, "Breath": 2, "Mono": 3}
            effect_value = effect_map.get(option, 0)
            
            # Get current RGB config and update effect
            current_data = self.coordinator.data or {}
            rgb_config = {
                "enable": current_data.get("rgb_enabled", True),
                "brightness": current_data.get("rgb_brightness", 20),
                "speed": current_data.get("rgb_speed", 20),
                "effect": effect_value,
                "easy_effect": ["#ff0000"] * 6,  # Default colors for Mono
                "breath_effect": ["#ff0000"] * 6,  # Default colors for Breath
                "unify_effect": "#000000"
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "rgb_light", rgb_config
            )
            if success:
                _LOGGER.info("RGB effect set to %s", option)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to set RGB effect")
        except Exception as err:
            _LOGGER.error("Error setting RGB effect: %s", err)
