"""Config flow for F1 25 Telemetry integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN, 
    DEFAULT_PORT, 
    CONF_PORT,
    CONF_FORWARD_ENABLED,
    CONF_FORWARD_IP,
    CONF_FORWARD_PORT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_FORWARD_ENABLED, default=False): bool,
        vol.Optional(CONF_FORWARD_IP, default=""): str,
        vol.Optional(CONF_FORWARD_PORT, default=DEFAULT_PORT): int,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for F1 25 Telemetry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="F1 25 Telemetry", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("port", default=DEFAULT_PORT): int,
                    vol.Optional("forward_enabled", default=False): bool,
                    vol.Optional("forward_ip", default=""): str,
                    vol.Optional("forward_port", default=DEFAULT_PORT): int,
                }
            ),
            errors=errors
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for F1 25 Telemetry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from options or initial data
        current_port = self.config_entry.options.get(
            "port", self.config_entry.data.get("port", DEFAULT_PORT)
        )
        current_forward_enabled = self.config_entry.options.get(
            "forward_enabled", self.config_entry.data.get("forward_enabled", False)
        )
        current_forward_ip = self.config_entry.options.get(
            "forward_ip", self.config_entry.data.get("forward_ip", "")
        )
        current_forward_port = self.config_entry.options.get(
            "forward_port", self.config_entry.data.get("forward_port", DEFAULT_PORT)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("port", default=current_port): int,
                    vol.Optional("forward_enabled", default=current_forward_enabled): bool,
                    vol.Optional("forward_ip", default=current_forward_ip): str,
                    vol.Optional("forward_port", default=current_forward_port): int,
                }
            ),
        )
