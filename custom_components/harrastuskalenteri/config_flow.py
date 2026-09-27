import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN, CHILDREN, DEFAULT_CALENDARS


def _schema_from_values(values):
    schema = {}
    for key, name in CHILDREN.items():
        current = values.get(key, DEFAULT_CALENDARS.get(key, [])) or []
        if isinstance(current, str):
            current = [current]
        schema[vol.Optional(key, default=current)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="calendar", multiple=True)
        )
    return vol.Schema(schema)


class HarrastuskalenteriConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Harrastuskalenteri", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema_from_values(DEFAULT_CALENDARS),
            description_placeholders={
                "info": "Valitse jokaiselle lapselle harrastuskalenterit."
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return HarrastuskalenteriOptionsFlow(config_entry)


class HarrastuskalenteriOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        current = dict(DEFAULT_CALENDARS)
        current.update(self.config_entry.data or {})
        current.update(self.config_entry.options or {})

        if user_input is not None:
            return self.async_create_entry(
                title="Kalenterit",
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_schema_from_values(current),
            description_placeholders={
                "info": "Muokkaa lasten harrastuskalentereita."
            },
        )
