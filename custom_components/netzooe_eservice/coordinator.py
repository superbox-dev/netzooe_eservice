"""DataUpdateCoordinator for the Netz OÖ eService integration."""

from __future__ import annotations

import calendar
import logging
import re
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import DEFAULT_TIME_ZONE
from netzooe_eservice_api.api import NetzOOEeServiceAPI
from netzooe_eservice_api.api import Pod
from netzooe_eservice_api.constants import ConsumptionsProfilesBranch
from netzooe_eservice_api.constants import SynthProfile
from netzooe_eservice_api.error import APIError

from .const import DOMAIN
from .const import SCAN_INTERVAL

if TYPE_CHECKING:
    from collections.abc import Mapping
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant

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
                first_day, last_day = self._get_last_l2_month()

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
                            "totalConsumptionsProfileEegL2": await self._get_consumptions_profile(
                                contract_account_number=dashboard_contract_accounts["contractAccountNumber"],
                                energy_community=contract["energyCommunityData"]["timeslices"][-1],
                                meter_point_administration_number=point_of_delivery["meterPointAdministrationNumber"],
                                date_from=None,
                                date_to=dt_util.now() - timedelta(days=16),
                            ),
                            "totalConsumptionsProfileEegL3": await self._get_consumptions_profile(
                                contract_account_number=dashboard_contract_accounts["contractAccountNumber"],
                                energy_community=contract["energyCommunityData"]["timeslices"][-1],
                                meter_point_administration_number=point_of_delivery["meterPointAdministrationNumber"],
                                date_from=None,
                                date_to=dt_util.now(),
                            ),
                            "monthlyConsumptionsProfileEegL2": await self._get_consumptions_profile(
                                contract_account_number=dashboard_contract_accounts["contractAccountNumber"],
                                energy_community=contract["energyCommunityData"]["timeslices"][-1],
                                meter_point_administration_number=point_of_delivery["meterPointAdministrationNumber"],
                                date_from=first_day,
                                date_to=last_day,
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
        date_from: datetime | None,
        date_to: datetime,
    ) -> list[dict[str, Any]]:
        consumptions_profile: list[dict[str, Any]] = await self.api.consumptions_profile(
            pods=[
                Pod(
                    contract_account_number=contract_account_number,
                    profile_type=profile["profileType"],
                    best_available_granularity=profile["granularity"],
                    energy_community_id=energy_community["energyCommunityId"],
                    meter_point_administration_number=meter_point_administration_number,
                    date_from=(
                        max(
                            date_from,
                            dt_util.as_local(
                                datetime.strptime(profile["from"], "%Y-%m-%d").replace(
                                    tzinfo=dt_util.DEFAULT_TIME_ZONE,
                                ),
                            ),
                        ).strftime(
                            "%Y-%m-%d",
                        )
                        if date_from
                        else profile["from"]
                    ),
                    date_to=date_to.strftime("%Y-%m-%d"),
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

    @staticmethod
    def _get_last_l2_month() -> tuple[datetime, datetime]:
        today: datetime = dt_util.now()
        year: int = today.year - 1 if today.month == 1 else today.year
        month: int = 12 if today.month == 1 else today.month - 1

        first_day: datetime = dt_util.as_local(datetime(year, month, 1, tzinfo=DEFAULT_TIME_ZONE))
        last_day_of_month: datetime = dt_util.as_local(
            datetime(year, month, calendar.monthrange(year, month)[1], tzinfo=DEFAULT_TIME_ZONE),
        )

        cutoff: datetime = today - timedelta(days=16)
        last_day: datetime = min(last_day_of_month, cutoff)

        return first_day, last_day
