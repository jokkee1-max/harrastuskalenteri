"""Config flow for Harrastuskalenteri."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CHILDREN, DOMAIN


def _calendar_selector():
    """Return a Google Calendar entity selector."""
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            multiple=True,
            filter=selector.EntityFilterSelectorConfig(
                integration="google",
                domain="calendar",
            ),
        )
    )


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build configuration schema."""
    defaults = defaults or {}
    fields: dict[Any, Any] = {}

    for key in CHILDREN:
        fields[vol.Optional(key, default=defaults.get(key, []))] = _calendar_selector()

    return vol.Schema(fields)


class HarrastuskalenteriConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Harrastuskalenteri."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Harrastuskalenteri",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return HarrastuskalenteriOptionsFlow(config_entry)


class HarrastuskalenteriOptionsFlow(config_entries.OptionsFlow):
    """Handle Harrastuskalenteri options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        current = {
            key: self._config_entry.options.get(
                key,
                self._config_entry.data.get(key, []),
            )
            for key in CHILDREN
        }

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(current),
        )
