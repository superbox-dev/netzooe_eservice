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
from .const import DeviceType
from .const import SCAN_INTERVAL

if TYPE_CHECKING:
    from collections.abc import Mapping
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

type NetzOOEeServiceConfigEntry = ConfigEntry[NetzOOEeServiceDataUpdateCoordinator]


class NetzOOEeServiceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Netz OÖ eService data API."""

    _attr_has_entity_name: bool = True

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
        data: dict[str, Any] = {}

        try:
            dashboard: dict[str, Any] = await self.api.dashboard()

            for dashboard_contract_account in dashboard["contractAccounts"]:
                contract_accounts: dict[str, Any] = await self.api.contract_accounts(
                    business_partner_number=dashboard_contract_account["businessPartnerNumber"],
                    contract_account_number=dashboard_contract_account["contractAccountNumber"],
                )

                for contract in contract_accounts["contracts"]:
                    _LOGGER.debug("contract: %s", contract)

                    if contract["branch"] == ConsumptionsProfilesBranch.ELECTRICITY.value and contract[
                        "synthProfile"
                    ] in [
                        SynthProfile.HOUSEHOLD.value,
                        SynthProfile.PHOTOVOLTAICS.value,
                    ]:
                        await self._append_mpan_data(data, contract=contract)
                        await self._append_energy_community_data(
                            data,
                            contract=contract,
                            contract_accounts=contract_accounts,
                        )

        except APIError as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={
                    "error": str(error),
                },
            ) from error

        _LOGGER.debug("data: %s", data)

        return data

    async def _append_mpan_data(self, data: dict[str, Any], /, *, contract: dict[str, Any]) -> None:
        point_of_delivery: dict[str, Any] = contract["pointOfDelivery"]

        device_type: str = ""

        if contract["synthProfile"] == SynthProfile.HOUSEHOLD.value:
            device_type = DeviceType.HOUSEHOLD.value
        elif contract["synthProfile"] == SynthProfile.PHOTOVOLTAICS.value:
            device_type = DeviceType.PHOTOVOLTAICS.value

        data[point_of_delivery["meterPointAdministrationNumber"]] = self._convert_recursive(
            {
                "profile": contract["synthProfile"],
                "deviceName": contract["synthProfile"],
                "deviceType": device_type,
                "scaleType": contract["scaleType"],
                "monthlyTrend": point_of_delivery["monthlyTrend"],
                "yearlyTrend": point_of_delivery["yearlyTrend"],
                "supplier": contract["supplier"],
                "meterReading": {
                    "meterNumber": point_of_delivery["meter"]["meterNumber"],
                    "values": self._get_meter_readings_data(
                        point_of_delivery["lastReadings"]["values"],
                        point_of_delivery["meter"]["meterNumber"],
                    ),
                },
            },
        )

    async def _append_energy_community_data(
        self,
        data: dict[str, Any],
        /,
        *,
        contract: dict[str, Any],
        contract_accounts: dict[str, Any],
    ) -> None:
        mpan: str = contract["pointOfDelivery"]["meterPointAdministrationNumber"]
        cutoff: datetime = dt_util.now() - timedelta(days=16)

        if contract["synthProfile"] == SynthProfile.HOUSEHOLD.value:
            device_type = DeviceType.EEG_IMPORT.value
        elif contract["synthProfile"] == SynthProfile.PHOTOVOLTAICS.value:
            device_type = DeviceType.EEG_EXPORT.value
        else:
            return

        grouped_energy_communities: dict[str, dict[str, Any]] = {}

        for energy_community in contract.get("energyCommunityData", {}).get("timeslices", []):
            energy_community_key: str = f"{mpan}_{energy_community['energyCommunityId']}"

            profile_available_from: datetime = dt_util.as_local(
                datetime.strptime(
                    energy_community["profileDataAvailableFrom"],
                    "%Y-%m-%d",
                ).replace(tzinfo=DEFAULT_TIME_ZONE),
            )

            profile_available_to: datetime = dt_util.as_local(
                datetime.strptime(
                    energy_community["profileDataAvailableTo"],
                    "%Y-%m-%d",
                ).replace(tzinfo=DEFAULT_TIME_ZONE),
            )

            if energy_community_key in grouped_energy_communities:
                grouped: dict[str, Any] = grouped_energy_communities[energy_community_key]
                grouped["profile_available_from"] = min(grouped["profile_available_from"], profile_available_from)
                grouped["profile_available_to"] = max(grouped["profile_available_to"], profile_available_to)
            else:
                grouped_energy_communities[energy_community_key] = {
                    "energy_community": energy_community,
                    "profile_available_from": profile_available_from,
                    "profile_available_to": profile_available_to,
                }

        for energy_community_key, grouped in grouped_energy_communities.items():
            total_eeg_l2: list[dict[str, Any]] = []

            if grouped["profile_available_from"] <= cutoff:
                total_eeg_l2 = await self._get_consumptions_profile(
                    contract_account_number=contract_accounts["contractAccountNumber"],
                    energy_community=grouped["energy_community"],
                    meter_point_administration_number=mpan,
                    date_from=grouped["profile_available_from"],
                    date_to=min(grouped["profile_available_to"], cutoff),
                )

            first_day, last_day = self._get_last_l2_month()
            monthly_eeg_l2: list[dict[str, Any]] = []

            if grouped["profile_available_from"] <= last_day and grouped["profile_available_to"] >= first_day:
                monthly_eeg_l2 = await self._get_consumptions_profile(
                    contract_account_number=contract_accounts["contractAccountNumber"],
                    energy_community=grouped["energy_community"],
                    meter_point_administration_number=mpan,
                    date_from=max(first_day, grouped["profile_available_from"]),
                    date_to=last_day,
                )

            total_eeg_l3 = await self._get_consumptions_profile(
                contract_account_number=contract_accounts["contractAccountNumber"],
                energy_community=grouped["energy_community"],
                meter_point_administration_number=mpan,
                date_from=grouped["profile_available_from"],
                date_to=grouped["profile_available_to"],
            )

            data[energy_community_key] = self._convert_recursive(
                {
                    "profile": contract["synthProfile"],
                    "mpan": mpan,
                    "deviceId": grouped["energy_community"]["energyCommunityId"],
                    "deviceName": grouped["energy_community"]["energyCommunityName"],
                    "deviceType": device_type,
                    "totalEegL2": [total_eeg_l2] if total_eeg_l2 else [],
                    "monthlyEegL2": [monthly_eeg_l2] if monthly_eeg_l2 else [],
                    "totalEegL3": [total_eeg_l3] if total_eeg_l3 else [],
                },
            )

    async def _get_consumptions_profile(
        self,
        contract_account_number: str,
        energy_community: Mapping[str, Any],
        meter_point_administration_number: str,
        date_from: datetime,
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
                    date_from=date_from.strftime("%Y-%m-%d"),
                    date_to=date_to.strftime("%Y-%m-%d"),
                )
                for profile in energy_community["profiles"]
            ],
        )

        for item in consumptions_profile:
            # When no profile exists (e.g. date range with no data) than the EEG information are missing!
            item["energyCommunityName"] = energy_community["energyCommunityName"]
            item["energyCommunityId"] = energy_community["energyCommunityId"]

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
