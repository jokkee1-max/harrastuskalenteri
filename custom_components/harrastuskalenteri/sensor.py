from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
import logging
import re

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
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    try:
        return dt_util.parse_datetime(value) or dt_util.parse_date(value)
    except Exception:
        return None


def _to_local_date(value):
    dt = _parse_dt(value)
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        dt = dt_util.as_local(dt)
        return dt.date()
    return dt


def _to_local_datetime(value):
    dt = _parse_dt(value)
    if not isinstance(dt, datetime):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return dt_util.as_local(dt)


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
            if ent and self.hass.states.get(ent) is not None
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
            except Exception as err:
                _LOGGER.exception("calendar.get_events failed: %s", err)
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

    def _events(self):
        return list((self.coordinator.data or {}).get(self.child_key, []))

    def _day_events(self, offset):
        target = dt_util.now().date() + timedelta(days=offset)
        return [e for e in self._events() if _to_local_date(e.get("start")) == target]

    def _today(self):
        return self._day_events(0)

    @property
    def native_value(self):
        return len(self._today())

    @property
    def extra_state_attributes(self):
        events = self._events()
        today = self._day_events(0)
        tomorrow = self._day_events(1)
        upcoming = []
        for day in range(2, 7):
            upcoming.extend(self._day_events(day))

        now = dt_util.now()
        next_event = None
        for e in events:
            marker = _to_local_datetime(e.get("end")) or _to_local_datetime(e.get("start"))
            if marker and marker >= now:
                next_event = e
                break

        return {
            "events": today,
            "today": today,
            "tomorrow": tomorrow,
            "upcoming": upcoming,
            "all_events": events,
            "next_event": next_event,
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "harrastuskalenteri")},
            name="Harrastuskalenteri",
            manufacturer="Custom",
        )



def _normalize_location(value: str) -> str:
    """Normalize calendar location text for rough same-place comparison."""
    if not value:
        return ""
    value = value.casefold().strip()
    value = re.sub(r"\b\d{5}\b", " ", value)
    value = re.sub(r"[^\wåäö]+", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _same_location(a: str, b: str) -> bool:
    """Return True when two location strings clearly refer to the same place."""
    na = _normalize_location(a)
    nb = _normalize_location(b)

    if not na or not nb:
        return False

    if na == nb:
        return True

    # Example: "Ollikkalan koulu" vs
    # "Ollikkalan koulu, Hämeenojankatu 9, 24260 Salo".
    if len(na) >= 6 and na in nb:
        return True
    if len(nb) >= 6 and nb in na:
        return True

    pa = _normalize_location((a or "").split(",", 1)[0])
    pb = _normalize_location((b or "").split(",", 1)[0])
    return bool(pa and pb and pa == pb)


class ConflictSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "harrastuskalenteri_ristiriidat"
        self._attr_name = "Harrastuskalenteri ristiriidat"
        self._attr_icon = "mdi:calendar-alert"

    def _conflicts(self):
        today = dt_util.now().date()
        tomorrow = today + timedelta(days=1)

        flat = []
        for child_key, events in (self.coordinator.data or {}).items():
            for e in events:
                s = _to_local_datetime(e.get("start"))
                en = _to_local_datetime(e.get("end")) or s
                if not s or not en:
                    continue
                if s.date() not in (today, tomorrow):
                    continue
                flat.append((s, en, e))

        flat.sort(key=lambda x: x[0])
        conflicts = []
        seen = set()
        buffer = timedelta(minutes=30)

        for i, (s1, e1, a) in enumerate(flat):
            for s2, e2, b in flat[i + 1:]:
                if s2.date() != s1.date():
                    break
                if s2 > e1 + buffer:
                    break
                if a.get("child_key") == b.get("child_key"):
                    continue

                location_a = a.get("location") or ""
                location_b = b.get("location") or ""

                # Same venue is not a transport conflict.
                # If either location is unknown, do not make a definite
                # conflict warning from time alone.
                if not location_a or not location_b:
                    continue
                if _same_location(location_a, location_b):
                    continue

                gap = round((s2 - e1).total_seconds() / 60)
                kind = "overlap" if gap < 0 else "tight"
                key = (
                    s1.isoformat(),
                    e1.isoformat(),
                    a.get("child_key"),
                    a.get("summary"),
                    s2.isoformat(),
                    e2.isoformat(),
                    b.get("child_key"),
                    b.get("summary"),
                )
                if key in seen:
                    continue
                seen.add(key)

                conflicts.append({
                    "date": s1.date().isoformat(),
                    "kind": kind,
                    "gap_minutes": gap,
                    "first": {
                        "child": a.get("child"),
                        "summary": a.get("summary"),
                        "start": s1.isoformat(),
                        "end": e1.isoformat(),
                        "location": a.get("location") or "",
                    },
                    "second": {
                        "child": b.get("child"),
                        "summary": b.get("summary"),
                        "start": s2.isoformat(),
                        "end": e2.isoformat(),
                        "location": b.get("location") or "",
                    },
                })
        return conflicts

    @property
    def native_value(self):
        return len(self._conflicts())

    @property
    def extra_state_attributes(self):
        return {
            "conflicts": self._conflicts(),
            "buffer_minutes": 30,
            "scope": "today_and_tomorrow",
        }
