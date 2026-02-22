"""DataUpdateCoordinator for the Netz OÖ eService integration."""

import logging
import re
from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from netzooe_eservice_api.api import NetzOOEeServiceAPI
from netzooe_eservice_api.api import Pod
from netzooe_eservice_api.constants import ConsumptionsProfilesBranch
from netzooe_eservice_api.constants import SynthProfile
from netzooe_eservice_api.error import APIError

from .const import DOMAIN
from .const import SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type NetzOOEeServiceConfigEntry = ConfigEntry[NetzOOEeServiceDataUpdateCoordinator]


class NetzOOEeServiceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Netz OÖ eService data API."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        /,
        *,
        username: str,
        password: str,
        session: ClientSession,
    ) -> None:
        """Initialize."""
        self.api: NetzOOEeServiceAPI = NetzOOEeServiceAPI(
            username=username,
            password=password,
            session=session,
        )

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> dict[str, Any]:
        """Read all values from API to update coordinator data."""
        try:
            dashboard: dict[str, Any] = await self.api.dashboard()
        except APIError as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={
                    "error": str(error),
                },
            ) from error

        data: dict[str, Any] = {}

        for dashboard_contract_accounts in dashboard["contractAccounts"]:
            contract_accounts: dict[str, Any] = await self.api.contract_accounts(
                business_partner_number=dashboard_contract_accounts["businessPartnerNumber"],
                contract_account_number=dashboard_contract_accounts["contractAccountNumber"],
            )

            for contract in contract_accounts["contracts"]:
                if contract["branch"] != ConsumptionsProfilesBranch.ELECTRICITY.value:
                    continue

                if contract["synthProfile"] not in [SynthProfile.HOUSEHOLD.value, SynthProfile.PHOTOVOLTAICS.value]:
                    continue

                point_of_delivery: dict[str, Any] = contract["pointOfDelivery"]

                data[self._camel_to_snake(point_of_delivery["meterPointAdministrationNumber"])] = (
                    self._convert_recursive(
                        {
                            "scaleType": contract["scaleType"],
                            "monthlyTrend": point_of_delivery["monthlyTrend"],
                            "yearlyTrend": point_of_delivery["yearlyTrend"],
                            "supplier": contract["supplier"],
                            "synthProfile": contract["synthProfile"],
                            "energyCommunity": contract["energyCommunityData"]["timeslices"],
                            "meterReading": {
                                "meterNumber": point_of_delivery["meter"]["meterNumber"],
                                "values": self._get_meter_readings_data(
                                    point_of_delivery["lastReadings"]["values"],
                                    point_of_delivery["meter"]["meterNumber"],
                                ),
                            },
                            "consumptionsProfileL2": await self._get_consumptions_profile(
                                contract_account_number=dashboard_contract_accounts["contractAccountNumber"],
                                energy_community=contract["energyCommunityData"]["timeslices"][-1],
                                meter_point_administration_number=point_of_delivery["meterPointAdministrationNumber"],
                            ),
                        },
                    )
                )

        return data

    async def _get_consumptions_profile(
        self,
        contract_account_number: str,
        energy_community: Mapping[str, Any],
        meter_point_administration_number: str,
    ) -> list[dict[str, Any]]:
        day = dt_util.now() - timedelta(days=16)

        consumptions_profile: list[dict[str, Any]] = await self.api.consumptions_profile(
            pods=[
                Pod(
                    contract_account_number=contract_account_number,
                    profile_type=profile["profileType"],
                    best_available_granularity=profile["granularity"],
                    energy_community_id=energy_community["energyCommunityId"],
                    meter_point_administration_number=meter_point_administration_number,
                    date_from=profile["from"],
                    date_to=day.strftime("%Y-%m-%d"),
                )
                for profile in energy_community["profiles"]
            ],
        )

        return consumptions_profile

    @staticmethod
    def _get_meter_readings_data(last_readings_values: list[Mapping[str, Any]], meter_number: str) -> Mapping[str, Any]:
        meter_readings_data: Mapping[str, Any] = {}

        for last_readings_value in last_readings_values:
            if last_readings_value["meternumber"] == meter_number:
                meter_readings_data = last_readings_value
                break

        return meter_readings_data

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _convert_dict_keys(self, d: dict[str, Any]) -> dict[str, Any]:
        return {self._camel_to_snake(k): v for k, v in d.items()}

    def _convert_recursive(self, obj: dict[str, Any] | list[Any] | str) -> dict[str, Any] | list[Any] | str:
        if isinstance(obj, dict):
            return {self._camel_to_snake(k): self._convert_recursive(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_recursive(i) for i in obj]
        return obj
