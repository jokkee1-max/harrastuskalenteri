import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN, CHILDREN, DEFAULT_CALENDARS

class HarrastuskalenteriConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Harrastuskalenteri", data=user_input)

        schema = {}
        for key, name in CHILDREN.items():
            schema[vol.Optional(key, default=DEFAULT_CALENDARS.get(key, []))] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar", multiple=True)
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            description_placeholders={"info": "Valitse jokaiselle lapselle harrastuskalenterit."},
        )
