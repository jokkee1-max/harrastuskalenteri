from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import re
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CHILDREN, DEFAULT_CALENDARS

_LOGGER = logging.getLogger(__name__)


def _parse_dt(value):
    if not value:
        return None
    try:
        return dt_util.parse_datetime(value) or dt_util.parse_date(value)
    except Exception:
        return None


def _event_dict(raw: dict[str, Any], calendar_entity: str, child_key: str, child_name: str):
    start = raw.get("start") or raw.get("start_time")
    end = raw.get("end") or raw.get("end_time")
    desc = raw.get("description") or ""
    location = raw.get("location") or ""
    summary = raw.get("summary") or raw.get("message") or "Harrastus"

    ride = ""
    urls = []
    for line in str(desc).splitlines():
        clean = line.strip()
        low = clean.lower()
        if low.startswith(("kyyti:", "kuljetus:")):
            ride = clean.split(":", 1)[1].strip()
        for url in re.findall(r"https?://[^\s<>()]+", clean):
            urls.append(url.rstrip(".,)"))

    details = ""
    for line in str(desc).splitlines():
        clean = line.strip()
        if not clean:
            continue
        low = clean.lower()
        if low.startswith(("pelaajat:", "kyyti:", "kuljetus:")):
            continue
        if re.fullmatch(r"https?://\S+", clean):
            continue
        if "merkitse in/out" in low:
            continue
        details = clean
        break

    return {
        "child": child_name,
        "child_key": child_key,
        "summary": summary,
        "start": start,
        "end": end,
        "location": location,
        "description": desc,
        "details": details,
        "ride": ride,
        "url": urls[0] if urls else "",
        "urls": urls,
        "calendar": calendar_entity,
        "calendar_name": calendar_entity.removeprefix("calendar.").replace("_", " "),
    }


class HarrastusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, calendars_by_child):
        super().__init__(
            hass,
            _LOGGER,
            name="Harrastuskalenteri",
            update_interval=timedelta(minutes=1),
        )
        self.calendars_by_child = calendars_by_child

    async def _async_update_data(self):
        now = dt_util.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)

        all_entities = sorted({
            ent
            for ents in self.calendars_by_child.values()
            for ent in (ents or [])
            if ent
        })

        response = {}
        if all_entities:
            try:
                response = await self.hass.services.async_call(
                    "calendar",
                    "get_events",
                    {
                        "entity_id": all_entities,
                        "start_date_time": start.isoformat(),
                        "end_date_time": end.isoformat(),
                    },
                    blocking=True,
                    return_response=True,
                ) or {}
            except Exception:
                response = {}

        result = {key: [] for key in CHILDREN}

        for child_key, child_name in CHILDREN.items():
            for cal in self.calendars_by_child.get(child_key, []):
                block = response.get(cal, {}) if isinstance(response, dict) else {}
                events = block.get("events", []) if isinstance(block, dict) else []
                for raw in events:
                    result[child_key].append(_event_dict(raw, cal, child_key, child_name))

            result[child_key].sort(key=lambda e: e.get("start") or "")

        return result


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    src = dict(DEFAULT_CALENDARS)
    for key in CHILDREN:
        if key in entry.data:
            value = entry.data.get(key) or []
            if isinstance(value, str):
                value = [value]
            src[key] = value

    coordinator = HarrastusCoordinator(hass, src)
    await coordinator.async_config_entry_first_refresh()

    entities = [ChildActivitiesSensor(coordinator, key, name) for key, name in CHILDREN.items()]
    entities.append(ConflictSensor(coordinator))
    async_add_entities(entities)


class ChildActivitiesSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, child_key, child_name):
        super().__init__(coordinator)
        self.child_key = child_key
        self.child_name = child_name
        self._attr_unique_id = f"harrastuskalenteri_{child_key}"
        self._attr_name = f"{child_name} harrastukset"
        self._attr_icon = "mdi:calendar-star"

    @property
    def native_value(self):
        return len(self._today())

    def _events(self):
        return list((self.coordinator.data or {}).get(self.child_key, []))

    def _day_events(self, offset):
        target = dt_util.now().date() + timedelta(days=offset)
        out = []
        for event in self._events():
            dt = _parse_dt(event.get("start"))
            if isinstance(dt, datetime):
                dt = dt_util.as_local(dt)
                d = dt.date()
            else:
                d = dt
            if d == target:
                out.append(event)
        return out

    def _today(self):
        return self._day_events(0)

    @property
    def extra_state_attributes(self):
        events = self._events()
        today = self._day_events(0)
        tomorrow = self._day_events(1)
        after_tomorrow = []
        for day in range(2, 7):
            after_tomorrow.extend(self._day_events(day))
        return {
            "events": today,               # yhteensopivuus vanhan dashboardin kanssa
            "today": today,
            "tomorrow": tomorrow,
            "upcoming": after_tomorrow,
            "all_events": events,
            "next_event": next((e for e in events if (_parse_dt(e.get("end")) or _parse_dt(e.get("start"))) and
                                (_parse_dt(e.get("end")) or _parse_dt(e.get("start"))) >= dt_util.now()), None),
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "harrastuskalenteri")},
            name="Harrastuskalenteri",
            manufacturer="Custom",
        )


class ConflictSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "harrastuskalenteri_ristiriidat"
        self._attr_name = "Harrastuskalenteri ristiriidat"
        self._attr_icon = "mdi:calendar-alert"

    def _conflicts(self):
        flat = []
        for child_key, events in (self.coordinator.data or {}).items():
            for e in events:
                s = _parse_dt(e.get("start"))
                en = _parse_dt(e.get("end")) or s
                if isinstance(s, datetime):
                    s = dt_util.as_local(s)
                if isinstance(en, datetime):
                    en = dt_util.as_local(en)
                if not isinstance(s, datetime) or not isinstance(en, datetime):
                    continue
                flat.append((s, en, e))

        flat.sort(key=lambda x: x[0])
        conflicts = []
        buffer = timedelta(minutes=30)

        for i, (s1, e1, a) in enumerate(flat):
            for s2, e2, b in flat[i+1:]:
                if s2 > e1 + buffer:
                    break
                if a.get("child_key") == b.get("child_key"):
                    continue
                if s2 <= e1 + buffer:
                    conflicts.append({
                        "first": a,
                        "second": b,
                        "gap_minutes": round((s2 - e1).total_seconds() / 60),
                    })
        return conflicts

    @property
    def native_value(self):
        return len(self._conflicts())

    @property
    def extra_state_attributes(self):
        return {"conflicts": self._conflicts(), "buffer_minutes": 30}
