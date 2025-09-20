"""Config flow for Marvel Tribe integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN
from .websocket_client import MarvelTribeWebSocketClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


class MarvelTribeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marvel Tribe."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = {}
            
            # Check if already configured first
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            
            # Test connection
            try:
                client = MarvelTribeWebSocketClient(
                    user_input[CONF_HOST], user_input[CONF_PORT]
                )
                await client.test_connection()
                await client.disconnect()
                
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            except ConnectionError:
                _LOGGER.error("Cannot connect to Marvel Tribe at %s:%s", user_input[CONF_HOST], user_input[CONF_PORT])
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Unexpected error connecting to Marvel Tribe: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
