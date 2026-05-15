"""Config flow for Watering.IO Hub."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_PREFIX, DOMAIN


class WateringIoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Watering.IO Hub."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            prefix = (user_input.get("topic_prefix") or DEFAULT_PREFIX).strip()
            await self.async_set_unique_id(prefix.lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Watering.IO Hub",
                data={"topic_prefix": prefix},
            )

        schema = vol.Schema(
            {
                vol.Required("topic_prefix", default=DEFAULT_PREFIX): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
