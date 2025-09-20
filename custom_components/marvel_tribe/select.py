"""Select platform for Marvel Tribe."""

from __future__ import annotations

import asyncio
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
        MarvelTribeAmbientLightEffectSelect(coordinator, entry, "rgb_effect"),
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


class MarvelTribeAmbientLightEffectSelect(MarvelTribeSelect):
    """Ambient light effect select."""

    _attr_name = "Ambient Light Effect"
    _attr_icon = "mdi:palette"
    _attr_options = ["Flow", "Breath", "Mono", "Rainbow"]

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        data = self.coordinator.data
        if data:
            effect = data.get("rgb_effect", 1)
            effect_map = {1: "Flow", 2: "Breath", 3: "Mono", 0: "Rainbow"}
            return effect_map.get(effect, "Flow")

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        try:
            effect_map = {"Flow": 1, "Breath": 2, "Mono": 3, "Rainbow": 0}
            effect_value = effect_map.get(option, 1)
            
            # Get current ambient light config and update effect
            current_data = self.coordinator.data or {}
            
            # Special colors for different effects
            if option == "Rainbow":
                easy_colors = ["#ff0000", "#ff8000", "#ffff00", "#00ff00", "#0000ff", "#8000ff"]
                breath_colors = ["#ff0000", "#ff8000", "#ffff00", "#00ff00", "#0000ff", "#8000ff"]
                unify_color = "#ff0000"
            elif option == "Flow":
                easy_colors = ["#0080ff", "#00ff80", "#80ff00", "#ff8000", "#ff0080", "#8000ff"]
                breath_colors = ["#0080ff", "#00ff80", "#80ff00", "#ff8000", "#ff0080", "#8000ff"]
                unify_color = "#0080ff"
            elif option == "Breath":
                easy_colors = ["#ff6060", "#60ff60", "#6060ff", "#ffff60", "#ff60ff", "#60ffff"]
                breath_colors = ["#ff6060", "#60ff60", "#6060ff", "#ffff60", "#ff60ff", "#60ffff"]
                unify_color = "#ff6060"
            else:  # Mono
                easy_colors = ["#ffffff"] * 6
                breath_colors = ["#ffffff"] * 6
                unify_color = "#ffffff"
            
            rgb_config = {
                "enable": current_data.get("rgb_enabled", True),
                "brightness": current_data.get("rgb_brightness", 20),
                "speed": current_data.get("rgb_speed", 20),
                "effect": effect_value,
                "easy_effect": easy_colors,
                "breath_effect": breath_colors,
                "unify_effect": unify_color
            }
            
            success = await self.coordinator.client.send_property_command(
                "set_user_property", "rgb_light", rgb_config
            )
            if success:
                _LOGGER.info("ambient light effect set to %s", option)
                # Update local state immediately and protect it
                if self.coordinator.data:
                    self.coordinator.data["rgb_effect"] = effect_value
                    self.coordinator.protect_state_key("rgb_effect", 3.0)
                # Update entity state immediately
                self.async_write_ha_state()
                # Wait a bit for device to process the command
                await asyncio.sleep(0.5)
                # Request updated data from device
                await self.coordinator.async_request_refresh()
                # Force update all listeners
                self.coordinator.async_update_listeners()
            else:
                _LOGGER.error("Failed to set ambient light effect")
        except Exception as err:
            _LOGGER.error("Error setting ambient light effect: %s", err)
