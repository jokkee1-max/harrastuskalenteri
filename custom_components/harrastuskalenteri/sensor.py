"""Sensors for Harrastuskalenteri."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import CHILDREN, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Harrastuskalenteri sensors."""
    coordinator = HarrastuskalenteriCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        HarrastusChildSensor(coordinator, entry, child_key, child_name)
        for child_key, child_name in CHILDREN.items()
    )


class HarrastuskalenteriCoordinator(
    DataUpdateCoordinator[dict[str, list[dict[str, Any]]]]
):
    """Fetch calendar events for all configured children."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    def _configured_calendars(self) -> dict[str, list[str]]:
        """Return configured calendars per child."""
        return {
            child: list(
                self.entry.options.get(
                    child,
                    self.entry.data.get(child, []),
                )
            )
            for child in CHILDREN
        }

    async def _async_update_data(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch today's events."""
        child_calendars = self._configured_calendars()

        all_calendars = sorted(
            {
                entity_id
                for calendars in child_calendars.values()
                for entity_id in calendars
            }
        )

        result: dict[str, list[dict[str, Any]]] = {
            child: [] for child in CHILDREN
        }

        if not all_calendars:
            return result

        now = dt_util.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        try:
            response = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "entity_id": all_calendars,
                    "start_date_time": start.isoformat(),
                    "end_date_time": end.isoformat(),
                },
                blocking=True,
                return_response=True,
            )
        except Exception as err:
            raise UpdateFailed(
                f"Kalenteritapahtumien haku epäonnistui: {err}"
            ) from err

        response = response or {}

        for child, calendars in child_calendars.items():
            events: list[dict[str, Any]] = []

            for calendar_entity in calendars:
                calendar_data = response.get(calendar_entity, {})
                for event in calendar_data.get("events", []):
                    events.append(
                        {
                            "summary": event.get("summary") or "Harrastus",
                            "start": event.get("start"),
                            "end": event.get("end"),
                            "location": event.get("location") or "",
                            "description": event.get("description") or "",
                            "calendar": calendar_entity,
                        }
                    )

            events.sort(key=lambda item: item.get("start") or "")
            result[child] = events

        return result


class HarrastusChildSensor(
    CoordinatorEntity[HarrastuskalenteriCoordinator],
    SensorEntity,
):
    """Sensor representing one child's activities today."""

    _attr_icon = "mdi:calendar-account"

    def __init__(
        self,
        coordinator: HarrastuskalenteriCoordinator,
        entry: ConfigEntry,
        child_key: str,
        child_name: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._child_key = child_key
        self._attr_name = f"{child_name} harrastukset"
        self._attr_unique_id = f"{entry.entry_id}_{child_key}_harrastukset"

    @property
    def native_value(self) -> str:
        """Return the first event name."""
        events = self.coordinator.data.get(self._child_key, [])
        if not events:
            return "Ei harrastuksia"
        return events[0]["summary"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return event details."""
        events = self.coordinator.data.get(self._child_key, [])
        return {
            "count": len(events),
            "events": events,
        }
