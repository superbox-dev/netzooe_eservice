"""DataUpdateCoordinator for the Netz OÖ eService integration."""

from __future__ import annotations

import asyncio
import calendar
import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import ClassVar
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
    from collections.abc import Awaitable
    from collections.abc import Mapping
    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

type NetzOOEeServiceConfigEntry = ConfigEntry[NetzOOEeServiceDataUpdateCoordinator]


class NetzOOEeServiceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Netz OÖ eService data API."""

    PROFILE_DEVICE_TYPES: ClassVar[dict[str, str]] = {
        SynthProfile.HOUSEHOLD.value: DeviceType.HOUSEHOLD.value,
        SynthProfile.PHOTOVOLTAICS.value: DeviceType.PHOTOVOLTAICS.value,
    }
    EEG_DEVICE_TYPES: ClassVar[dict[str, str]] = {
        SynthProfile.HOUSEHOLD.value: DeviceType.EEG_IMPORT.value,
        SynthProfile.PHOTOVOLTAICS.value: DeviceType.EEG_EXPORT.value,
    }

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

        self._semaphore = asyncio.Semaphore(10)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> dict[str, Any]:
        """Read all values from API to update coordinator data."""
        data: dict[str, Any] = {}
        tasks: list[Awaitable[None]] = []

        try:
            dashboard: dict[str, Any] = await self.api.dashboard()

            contract_accounts_results: list[dict[str, Any]] = await asyncio.gather(
                *[
                    self.api.contract_accounts(
                        business_partner_number=account["businessPartnerNumber"],
                        contract_account_number=account["contractAccountNumber"],
                    )
                    for account in dashboard["contractAccounts"]
                ],
            )

            for contract_accounts in contract_accounts_results:
                for contract in contract_accounts["contracts"]:
                    if contract["branch"] == ConsumptionsProfilesBranch.ELECTRICITY.value and contract[
                        "synthProfile"
                    ] in {
                        SynthProfile.HOUSEHOLD.value,
                        SynthProfile.PHOTOVOLTAICS.value,
                    }:
                        self._append_mpan_data(data, contract=contract)

                        tasks.append(
                            self._append_energy_community_data(
                                data,
                                contract=contract,
                                contract_accounts=contract_accounts,
                            ),
                        )

            await asyncio.gather(*tasks)

        except APIError as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={
                    "error": str(error),
                },
            ) from error

        return data

    def _append_mpan_data(self, data: dict[str, Any], /, *, contract: dict[str, Any]) -> None:
        point_of_delivery: dict[str, Any] = contract["pointOfDelivery"]
        device_type: str = self.PROFILE_DEVICE_TYPES[contract["synthProfile"]]

        data[point_of_delivery["meterPointAdministrationNumber"]] = {
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
        }

    async def _append_energy_community_data(
        self,
        data: dict[str, Any],
        /,
        *,
        contract: dict[str, Any],
        contract_accounts: dict[str, Any],
    ) -> None:
        meter_point_administration_number: str = contract["pointOfDelivery"]["meterPointAdministrationNumber"]
        grouped_energy_communities: dict[str, dict[str, Any]] = {}

        for energy_community in contract.get("energyCommunityData", {}).get("timeslices", []):
            energy_community_key: str = f"{meter_point_administration_number}_{energy_community['energyCommunityId']}"

            profile_available_from: datetime = self._parse_local_date(energy_community["profileDataAvailableFrom"])
            profile_available_to: datetime = self._parse_local_date(energy_community["profileDataAvailableTo"])

            if energy_community_key in grouped_energy_communities:
                grouped: dict[str, Any] = grouped_energy_communities[energy_community_key]
                grouped["profileAvailableFrom"] = min(grouped["profileAvailableFrom"], profile_available_from)
                grouped["profileAvailableTo"] = max(grouped["profileAvailableTo"], profile_available_to)
            else:
                grouped_energy_communities[energy_community_key] = {
                    "energyCommunity": energy_community,
                    "profileAvailableFrom": profile_available_from,
                    "profileAvailableTo": profile_available_to,
                }

        results: list[tuple[str, dict[str, Any] | list[Any] | str]] = await asyncio.gather(
            *[
                self._process_energy_community(
                    contract=contract,
                    contract_accounts=contract_accounts,
                    meter_point_administration_number=meter_point_administration_number,
                    energy_community_key=energy_community_key,
                    grouped=grouped,
                )
                for energy_community_key, grouped in grouped_energy_communities.items()
            ],
        )

        data.update(dict(results))

    async def _process_energy_community(
        self,
        *,
        contract: dict[str, Any],
        contract_accounts: dict[str, Any],
        meter_point_administration_number: str,
        energy_community_key: str,
        grouped: dict[str, Any],
    ) -> tuple[str, dict[str, Any] | list[Any] | str]:
        cutoff: datetime = dt_util.now() - timedelta(days=16)
        first_day, last_day = self._get_last_l2_month()
        device_type: str = self.EEG_DEVICE_TYPES[contract["synthProfile"]]

        tasks: dict[str, Awaitable[list[dict[str, Any]]]] = {}

        if grouped["profileAvailableFrom"] <= cutoff:
            tasks["totalEegL2"] = self._api_call(
                self._get_consumptions_profile(
                    contract_account_number=contract_accounts["contractAccountNumber"],
                    energy_community=grouped["energyCommunity"],
                    meter_point_administration_number=meter_point_administration_number,
                    date_from=grouped["profileAvailableFrom"],
                    date_to=min(grouped["profileAvailableTo"], cutoff),
                ),
            )

        if grouped["profileAvailableFrom"] <= last_day and grouped["profileAvailableTo"] >= first_day:
            tasks["monthlyEegL2"] = self._api_call(
                self._get_consumptions_profile(
                    contract_account_number=contract_accounts["contractAccountNumber"],
                    energy_community=grouped["energyCommunity"],
                    meter_point_administration_number=meter_point_administration_number,
                    date_from=max(first_day, grouped["profileAvailableFrom"]),
                    date_to=last_day,
                ),
            )

        tasks["totalEegL3"] = self._api_call(
            self._get_consumptions_profile(
                contract_account_number=contract_accounts["contractAccountNumber"],
                energy_community=grouped["energyCommunity"],
                meter_point_administration_number=meter_point_administration_number,
                date_from=grouped["profileAvailableFrom"],
                date_to=grouped["profileAvailableTo"],
            ),
        )

        task_names: list[str] = list(tasks.keys())
        results: list[list[dict[str, Any]]] = await asyncio.gather(*tasks.values())
        task_results: dict[str, list[dict[str, Any]]] = dict(zip(task_names, results, strict=True))

        return energy_community_key, {
            "synthProfile": contract["synthProfile"],
            "meterPointAdministrationNumber": meter_point_administration_number,
            "deviceId": grouped["energyCommunity"]["energyCommunityId"],
            "deviceName": grouped["energyCommunity"]["energyCommunityName"],
            "deviceType": device_type,
            "totalEegL2": task_results.get("totalEegL2", []),
            "monthlyEegL2": task_results.get("monthlyEegL2", []),
            "totalEegL3": task_results["totalEegL3"],
        }

    async def _get_consumptions_profile(
        self,
        contract_account_number: str,
        energy_community: Mapping[str, Any],
        meter_point_administration_number: str,
        date_from: datetime,
        date_to: datetime,
    ) -> list[dict[str, Any]]:
        _date_from: str = date_from.strftime("%Y-%m-%d")
        _date_to: str = date_to.strftime("%Y-%m-%d")

        consumptions_profile: list[dict[str, Any]] = await self.api.consumptions_profile(
            pods=[
                Pod(
                    contract_account_number=contract_account_number,
                    profile_type=profile["profileType"],
                    best_available_granularity=profile["granularity"],
                    energy_community_id=energy_community["energyCommunityId"],
                    meter_point_administration_number=meter_point_administration_number,
                    date_from=_date_from,
                    date_to=_date_to,
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

        for item in last_readings_values:
            if item["meternumber"] == meter_number:
                meter_readings_data = item
                break

        return meter_readings_data

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

    @staticmethod
    def _parse_local_date(date_str: str) -> datetime:
        return dt_util.as_local(datetime.fromisoformat(date_str).replace(tzinfo=DEFAULT_TIME_ZONE))

    async def _api_call[T](self, coro: Awaitable[T]) -> T:
        async with self._semaphore:
            async with asyncio.timeout(120):
                return await coro
