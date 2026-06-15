from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .channels import DIGITAL_CHANNELS
from .const import DOMAIN, MODEL, SOFTWARE_VERSION, HARDWARE_VERSION
from .coordinator import HargassnerCoordinator
from .friendly_names import friendly_digital_name

# Enable normal HV20 pumps/valves/statuses by default. Pelletkessel-specific PK_*
# expansion bits stay available but disabled unless explicitly needed.
DEFAULT_ENABLED_DIGITAL_KEYS = {
    "d00_01_hkp1", "d00_02_hkp2",
    "d00_03_m1a", "d00_04_m1z", "d00_05_m2a", "d00_06_m2z",
    "d00_07_boilanf_1", "d00_08_lamdaheiz", "d00_10_z_ndheiz",
    "d00_11_slk_auf", "d00_12_slk_zu", "d00_13_plk_auf", "d00_14_plk_zu",
    "d01_00_stb", "d01_01_tks", "d01_02_st_rung", "d01_03_ext_anf",
    "d02_00_bp1", "d02_01_bp2", "d02_02_bp3",
    "d02_03_rlm_auf", "d02_04_rlm_zu", "d02_05_schnellladev",
    "d03_00_hkp3", "d03_01_hkp4",
    "d03_03_m3a", "d03_04_m3z", "d03_05_m4a", "d03_06_m4z",
    "d03_07_boilanf_2", "d03_08_zp_boi_1", "d03_09_zp_boi_2", "d03_10_zp_boi_3",
    "d04_00_hkp5", "d04_01_hkp6",
    "d04_03_m5a", "d04_04_m5z", "d04_05_m6a", "d04_06_m6z",
    "d04_07_boilanf_3", "d04_11_fw_freig", "d04_12_fw_pumpe", "d04_13_flp",
    "d05_00_hkpa", "d05_01_maa", "d05_02_maz", "d05_03_bpa",
    "d05_04_zp_boi_a", "d05_05_boilanf_a",
    "d05_07_hkpb", "d05_08_mba", "d05_09_mbz", "d05_10_bpb",
    "d05_11_zp_boi_b", "d05_12_boilanf_b",
    "d07_00_gflp", "d07_01_gflm_auf", "d07_02_gflm_zu",
    "d07_03_dreg_p1", "d07_04_dreg_p2", "d07_05_dreg_mi_auf", "d07_06_dreg_mi_zu",
    "d07_07_sp_lung_aktiv", "d07_08_dreg2_p1", "d07_09_dreg2_p2",
    "d07_10_dreg2_mi_auf", "d07_11_dreg2_mi_zu",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: HargassnerCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        HargassnerConnectionSensor(coordinator, entry),
        HargassnerDoorSensor(coordinator, entry),
    ]
    entities.extend(HargassnerDigitalSensor(coordinator, entry, ch) for ch in DIGITAL_CHANNELS if ch["key"] != "d01_01_tks")
    async_add_entities(entities)


class HargassnerConnectionSensor(CoordinatorEntity[HargassnerCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Verbindung"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: HargassnerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_connection"

    @property
    def available(self) -> bool:
        # Keep the connection entity available so it can explicitly show on/off
        # even when the coordinator's latest poll failed.
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            "last_successful_update": data.received_at.isoformat() if data else None,
            "host": self.coordinator.client.host,
            "port": self.coordinator.client.port,
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


class HargassnerDoorSensor(CoordinatorEntity[HargassnerCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Kesseltür"
    _attr_device_class = BinarySensorDeviceClass.DOOR
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: HargassnerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        # Reuse the original DAQ unique id so existing installs migrate cleanly
        # from the raw TKS bit to the proper door entity.
        self._attr_unique_id = f"{entry.entry_id}_d01_01_tks"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        raw_contact_closed = self.coordinator.data.digital.get("d01_01_tks")
        if raw_contact_closed is None:
            return None
        # TKS is true when the boiler door contact is closed. Home Assistant door
        # sensors use on=True for open, so expose the inverted value.
        return not raw_contact_closed

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        raw_contact_closed = None
        if self.coordinator.data:
            raw_contact_closed = self.coordinator.data.digital.get("d01_01_tks")
        return {
            "daq_word": 1,
            "daq_bit": 1,
            "daq_name": "TKS",
            "raw_contact_closed": raw_contact_closed,
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


class HargassnerDigitalSensor(CoordinatorEntity[HargassnerCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HargassnerCoordinator, entry: ConfigEntry, channel: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_{channel['key']}"
        self._attr_name = friendly_digital_name(channel)
        self._attr_entity_registry_enabled_default = channel["key"] in DEFAULT_ENABLED_DIGITAL_KEYS

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.digital.get(self._channel["key"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "daq_word": self._channel["word"],
            "daq_bit": self._channel["bit"],
            "daq_name": self._channel["name"],
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
