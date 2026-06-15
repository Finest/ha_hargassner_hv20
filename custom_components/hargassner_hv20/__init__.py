from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import HargassnerClient
from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import HargassnerCoordinator

type HargassnerConfigEntry = ConfigEntry[HargassnerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: HargassnerConfigEntry) -> bool:
    host = entry.data["host"]
    port = int(entry.data.get("port", DEFAULT_PORT))
    scan_interval = int(entry.options.get("scan_interval", entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)))

    client = HargassnerClient(host=host, port=port)
    coordinator = HargassnerCoordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HargassnerConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
