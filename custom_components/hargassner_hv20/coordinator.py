from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HargassnerClient, HargassnerError, HargassnerFrame
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HargassnerCoordinator(DataUpdateCoordinator[HargassnerFrame]):
    def __init__(self, hass: HomeAssistant, client: HargassnerClient, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> HargassnerFrame:
        try:
            return await self.hass.async_add_executor_job(self.client.read_frame)
        except HargassnerError as err:
            raise UpdateFailed(str(err)) from err
