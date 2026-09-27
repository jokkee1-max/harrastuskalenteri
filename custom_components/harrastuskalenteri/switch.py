from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN


def _friendly_name(service: str) -> str:
    raw = service.removeprefix("mobile_app_")
    return raw.replace("_", " ").strip().title() or service


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    notify_services = hass.services.async_services().get("notify", {})

    mobile_services = sorted(
        service
        for service in notify_services
        if service.startswith("mobile_app_")
    )

    async_add_entities(
        [NotificationRecipientSwitch(service) for service in mobile_services]
    )


class NotificationRecipientSwitch(RestoreEntity, SwitchEntity):
    _attr_icon = "mdi:cellphone-message"
    _attr_should_poll = False

    def __init__(self, service: str) -> None:
        self._service = service
        self._attr_unique_id = f"harrastuskalenteri_notify_{service}"
        self._attr_name = f"Ilmoitukset – {_friendly_name(service)}"
        self._is_on = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        previous = await self.async_get_last_state()
        if previous is not None:
            self._is_on = previous.state == "on"

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._is_on = False
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {
            "notify_service": f"notify.{self._service}",
            "mobile_app_service": self._service,
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "harrastuskalenteri")},
            name="Harrastuskalenteri",
            manufacturer="Custom",
        )
