"""DataUpdateCoordinator for the Netz OÖ eService integration."""

from __future__ import annotations

import calendar
import logging
from collections import defaultdict
from datetime import date
from datetime import timedelta
from typing import Any
from typing import ClassVar
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from netzooe_eservice_api.api import NetzOOEeServiceAPI
from netzooe_eservice_api.api import Pod
from netzooe_eservice_api.constants import ConsumptionsProfilesBranch
from netzooe_eservice_api.constants import SynthProfile
from netzooe_eservice_api.error import APIError
from netzooe_eservice_api.error import AuthenticationError

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

    PROFILE_DEVICE_TYPES: ClassVar[dict[str, str]] = {
        SynthProfile.HOUSEHOLD.value: DeviceType.HOUSEHOLD.value,
        SynthProfile.PHOTOVOLTAICS.value: DeviceType.PHOTOVOLTAICS.value,
    }
    ENERGY_COMMUNITY_DEVICE_TYPES: ClassVar[dict[str, str]] = {
        SynthProfile.HOUSEHOLD.value: DeviceType.ENERGY_COMMUNITY_IMPORT.value,
        SynthProfile.PHOTOVOLTAICS.value: DeviceType.ENERGY_COMMUNITY_EXPORT.value,
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

        self.dashboard: dict[str, Any] = {}

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            self.dashboard = await self.api.dashboard()
        except AuthenticationError as error:  # pragma: no cover
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="authentication_error",
            ) from error
        except APIError as error:  # pragma: no cover
            raise UpdateFailed(error) from error
        else:
            _LOGGER.debug("dashboard: %s", self.dashboard)

    async def _async_update_data(self) -> dict[str, Any]:
        """Read all values from API to update coordinator data."""
        data: dict[str, Any] = {}

        try:
            await self._append_data(data)
        except AuthenticationError as error:  # pragma: no cover
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="authentication_error",
            ) from error
        except APIError as error:  # pragma: no cover
            _LOGGER.error("An error occurred while communicating with the API: %s", error)  # noqa: TRY400

            if self.data is not None:
                _LOGGER.warning("Update failed, using cached data")
                return self.data

            raise UpdateFailed(error) from error
        else:
            _LOGGER.debug("data: %s", data)
            return data

    async def _append_data(self, data: dict[str, Any]) -> None:
        consents_map: dict[str, list[dict[str, Any]]] = await self._get_consents_map()

        all_contracts_by_mpan: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for account in self.dashboard["contractAccounts"]:
            contract_accounts: dict[str, Any] = await self.api.contract_accounts(
                business_partner_number=account["businessPartnerNumber"],
                contract_account_number=account["contractAccountNumber"],
            )

            for contract in contract_accounts["contracts"]:
                if contract["branch"] == ConsumptionsProfilesBranch.ELECTRICITY.value and contract["synthProfile"] in {
                    SynthProfile.HOUSEHOLD.value,
                    SynthProfile.PHOTOVOLTAICS.value,
                }:
                    all_contracts_by_mpan[contract["pointOfDelivery"]["meterPointAdministrationNumber"]].append(
                        {
                            "contract": contract,
                            "contractAccounts": contract_accounts,
                        },
                    )

                    if contract["active"]:
                        self._append_mpan_data(data, contract=contract)

        for contracts in all_contracts_by_mpan.values():
            active_contract: dict[str, Any] = next(item for item in contracts if item["contract"]["active"])

            await self._append_energy_community_data(
                data,
                contracts=contracts,
                active_contract=active_contract,
                consents_map=consents_map,
            )

    async def _get_consents_map(self) -> dict[str, list[dict[str, Any]]]:
        consents: list[dict[str, Any]] = await self.api.consents()
        latest_consents: dict[tuple[str, str], dict[str, Any]] = {}

        for consent in consents:
            key = (consent["pod"], consent["serviceProvider"])

            existing: dict[str, Any] | None = latest_consents.get(key)

            # The API returns the consent history. Keep only the most recent
            # consent per POD and service provider.
            if existing is None or (
                date.fromisoformat(consent["validThrough"]["from"]),
                date.fromisoformat(consent["validThrough"]["to"]),
            ) > (
                date.fromisoformat(existing["validThrough"]["from"]),
                date.fromisoformat(existing["validThrough"]["to"]),
            ):
                latest_consents[key] = consent

        consents_map: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for consent in latest_consents.values():
            consents_map[consent["pod"]].append(consent)

        return consents_map

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
                    point_of_delivery["lastReadings"].get("values", []),
                    point_of_delivery["meter"]["meterNumber"],
                ),
            },
        }

    async def _append_energy_community_data(
        self,
        data: dict[str, Any],
        /,
        *,
        contracts: list[dict[str, Any]],
        active_contract: dict[str, Any],
        consents_map: dict[str, list[dict[str, Any]]],
    ) -> None:
        cutoff: date = dt_util.now().date() - timedelta(days=16)
        first_day, last_day = self._get_last_l2_month()

        meter_point_administration_number: str = active_contract["contract"]["pointOfDelivery"][
            "meterPointAdministrationNumber"
        ]

        device_type: str = self.ENERGY_COMMUNITY_DEVICE_TYPES[active_contract["contract"]["synthProfile"]]

        energy_communities: dict[str, dict[str, Any]] = {}

        for item in contracts:
            contract: dict[str, Any] = item["contract"]
            contract_accounts: dict[str, Any] = item["contractAccounts"]

            _LOGGER.debug("Contract %s", contract_accounts["contractAccountNumber"])

            for timeslice in contract.get("energyCommunityData", {}).get("timeslices", []):
                _LOGGER.debug("  %s", timeslice["energyCommunityName"])

                energy_community: dict[str, Any] = self._get_or_create_energy_community(
                    energy_communities,
                    consents_map=consents_map,
                    meter_point_administration_number=meter_point_administration_number,
                    active_contract=active_contract,
                    device_type=device_type,
                    timeslice=timeslice,
                )

                profile_available_from: date = date.fromisoformat(timeslice["profileDataAvailableFrom"])
                profile_available_to: date = date.fromisoformat(timeslice["profileDataAvailableTo"])

                total_l2_profile_available_to: date = min(profile_available_to, cutoff)
                total_l2: list[dict[str, Any]] = []

                if profile_available_from <= cutoff:
                    total_l2 = await self._get_consumptions_profile(
                        contract_account_number=contract_accounts["contractAccountNumber"],
                        timeslice=timeslice,
                        meter_point_administration_number=meter_point_administration_number,
                        date_from=profile_available_from,
                        date_to=total_l2_profile_available_to,
                    )
                    energy_community["totalL2"].extend(total_l2)

                if profile_available_from <= last_day and profile_available_to >= first_day:
                    energy_community["monthlyL2"].extend(
                        await self._get_consumptions_profile(
                            contract_account_number=contract_accounts["contractAccountNumber"],
                            timeslice=timeslice,
                            meter_point_administration_number=meter_point_administration_number,
                            date_from=max(first_day, profile_available_from),
                            date_to=min(last_day, profile_available_to),
                        ),
                    )

                if profile_available_to <= cutoff:
                    energy_community["totalL3"].extend(total_l2)
                else:
                    energy_community["totalL3"].extend(
                        await self._get_consumptions_profile(
                            contract_account_number=contract_accounts["contractAccountNumber"],
                            timeslice=timeslice,
                            meter_point_administration_number=meter_point_administration_number,
                            date_from=profile_available_from,
                            date_to=profile_available_to,
                        ),
                    )

        data.update(energy_communities)

    @staticmethod
    def _get_or_create_energy_community(
        energy_communities: dict[str, dict[str, Any]],
        /,
        *,
        consents_map: dict[str, list[dict[str, Any]]],
        meter_point_administration_number: str,
        active_contract: dict[str, Any],
        device_type: str,
        timeslice: dict[str, Any],
    ) -> dict[str, Any]:
        consent: dict[str, Any] = next(
            (
                consent
                for consent in consents_map[meter_point_administration_number]
                if consent["serviceProvider"] in timeslice["energyCommunityId"]
            ),
            {},
        )

        key: str = f"{meter_point_administration_number}_{consent['serviceProvider']}"

        if key in energy_communities:
            return energy_communities[key]

        energy_community: dict[str, Any] = {
            "synthProfile": active_contract["contract"]["synthProfile"],
            "meterPointAdministrationNumber": meter_point_administration_number,
            "deviceId": timeslice["energyCommunityId"],
            "deviceName": timeslice["energyCommunityName"],
            "deviceType": device_type,
            "totalL2": [],
            "monthlyL2": [],
            "totalL3": [],
            "contributionPercentage": consent["contributionPercentage"],
            "status": consent["status"],
        }

        energy_communities[key] = energy_community

        return energy_community

    async def _get_consumptions_profile(
        self,
        contract_account_number: str,
        timeslice: Mapping[str, Any],
        meter_point_administration_number: str,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        _date_from: str = date_from.isoformat()
        _date_to: str = date_to.isoformat()

        consumptions_profile: list[dict[str, Any]] = await self.api.consumptions_profile(
            pods=[
                Pod(
                    contract_account_number=contract_account_number,
                    profile_type=profile["profileType"],
                    best_available_granularity=profile["granularity"],
                    energy_community_id=timeslice["energyCommunityId"],
                    meter_point_administration_number=meter_point_administration_number,
                    date_from=_date_from,
                    date_to=_date_to,
                )
                for profile in timeslice["profiles"]
            ],
        )

        for item in consumptions_profile:
            # When no profile exists (e.g. date range with no data) than the energy community information are missing!
            item["energyCommunityName"] = timeslice["energyCommunityName"]
            item["energyCommunityId"] = timeslice["energyCommunityId"]

            # Overwrite the from/to with the correct time period, the time period from the API is not valid!
            item["from"] = _date_from
            item["to"] = _date_to

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
    def _get_last_l2_month() -> tuple[date, date]:
        today: date = dt_util.now().date()
        year: int = today.year - 1 if today.month == 1 else today.year
        month: int = 12 if today.month == 1 else today.month - 1

        first_day: date = date(year, month, 1)
        last_day_of_month: date = date(year, month, calendar.monthrange(year, month)[1])

        cutoff: date = today - timedelta(days=16)
        last_day: date = min(last_day_of_month, cutoff)

        return first_day, last_day
