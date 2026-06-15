from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .channels import ANALOG_CHANNELS
from .const import DOMAIN, MODEL, SOFTWARE_VERSION, HARDWARE_VERSION
from .coordinator import HargassnerCoordinator
from .friendly_names import friendly_analog_name

# Keep noisy/unused expansion channels disabled by default, but expose the core HV20
# values and common heating/boiler/buffer values immediately.
DEFAULT_ENABLED_ANALOG_IDS = {
    0, 1, 2, 3, 4, 5, 6,
    7, 8, 9, 10, 11, 12, 13, 14, 15,
    16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
    46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
    56, 57, 58, 59, 60,
    61, 62, 63,
    115, 116,
    117, 118, 119,
    124, 125, 126, 127,
    128,
    140, 141, 142, 143, 144, 145, 146, 147, 148,
    151, 152, 153, 154, 155, 156, 157, 158, 159, 160,
}


def _unit(unit: str | None) -> str | None:
    if unit == "°C":
        return UnitOfTemperature.CELSIUS
    if unit == "%":
        return PERCENTAGE
    return unit


def _device_class(unit: str | None) -> SensorDeviceClass | None:
    if unit == "°C":
        return SensorDeviceClass.TEMPERATURE
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: HargassnerCoordinator = entry.runtime_data
    async_add_entities(HargassnerAnalogSensor(coordinator, entry, ch) for ch in ANALOG_CHANNELS)


class HargassnerAnalogSensor(CoordinatorEntity[HargassnerCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HargassnerCoordinator, entry: ConfigEntry, channel: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_{channel['key']}"
        self._attr_name = friendly_analog_name(channel)
        self._attr_native_unit_of_measurement = _unit(channel.get("unit"))
        self._attr_device_class = _device_class(channel.get("unit"))
        if channel.get("unit") or channel["id"] in DEFAULT_ENABLED_ANALOG_IDS:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_registry_enabled_default = channel["id"] in DEFAULT_ENABLED_ANALOG_IDS

    @property
    def native_value(self) -> int | float | str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.analog.get(self._channel["id"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "daq_id": self._channel["id"],
            "daq_name": self._channel["name"],
            "raw_unit": self._channel.get("unit"),
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Hargassner",
            "model": MODEL,
            "sw_version": SOFTWARE_VERSION,
            "hw_version": HARDWARE_VERSION,
        }
