"""Harrastuskalenteri integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Harrastuskalenteri frontend resources."""
    hass.data.setdefault(DOMAIN, {})

    if not hass.data[DOMAIN].get("frontend_registered"):
        frontend_path = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/harrastuskalenteri",
                    str(frontend_path),
                    False,
                )
            ]
        )
        hass.data[DOMAIN]["frontend_registered"] = True

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Harrastuskalenteri from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if not hass.data[DOMAIN].get("frontend_registered"):
        frontend_path = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/harrastuskalenteri",
                    str(frontend_path),
                    False,
                )
            ]
        )
        hass.data[DOMAIN]["frontend_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)
