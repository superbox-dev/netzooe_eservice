# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""DataUpdateCoordinator for the Netz OÖ eService integration."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import NamedTuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from netzooe_eservice_api.api import NetzOOEeServiceAPI
from netzooe_eservice_api.api import Pod
from netzooe_eservice_api.constants import ConsentsStatus
from netzooe_eservice_api.constants import ConsumptionsProfilesBranch
from netzooe_eservice_api.constants import SynthProfile
from netzooe_eservice_api.error import APIError
from netzooe_eservice_api.error import AuthenticationError

from .const import CONF_FREQUENT_UPDATES
from .const import CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from .const import CONF_SHOW_INACTIVE_METER_POINTS
from .const import CONF_SHOW_REVOKED_ENERGY_COMMUNITIES
from .const import DEFAULT_FREQUENT_UPDATES
from .const import DEFAULT_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA
from .const import DEFAULT_SHOW_INACTIVE_METER_POINTS
from .const import DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES
from .const import DOMAIN
from .const import MAX_PARALLEL_REQUESTS
from .const import PROFILE_DATA_DELAY
from .const import SCAN_INTERVAL
from .const import SCAN_INTERVAL_FULL
from .const import DeviceType

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from collections.abc import Iterable

    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

type NetzOOEeServiceConfigEntry = ConfigEntry[NetzOOEeServiceDataUpdateCoordinator]
type ConsentsMap = dict[str, list[dict[str, Any]]]

ELECTRICITY_SYNTH_PROFILES: Final[set[str]] = {
    SynthProfile.HOUSEHOLD.value,
    SynthProfile.PHOTOVOLTAICS.value,
}
METER_POINT_DEVICE_TYPES: Final[dict[str, str]] = {
    SynthProfile.HOUSEHOLD.value: DeviceType.HOUSEHOLD.value,
    SynthProfile.PHOTOVOLTAICS.value: DeviceType.PHOTOVOLTAICS.value,
}
ENERGY_COMMUNITY_DEVICE_TYPES: Final[dict[str, str]] = {
    SynthProfile.HOUSEHOLD.value: DeviceType.ENERGY_COMMUNITY_IMPORT.value,
    SynthProfile.PHOTOVOLTAICS.value: DeviceType.ENERGY_COMMUNITY_EXPORT.value,
}
METER_READING_REFERENCE_NUMBERS: Final[set[str]] = {"1.8.1", "2.8.1"}
PEAK_POWER_REFERENCE_NUMBERS: Final[set[str]] = {"1.6.0", "2.6.0"}
ENERGY_COMMUNITY_ID_SERVICE_PROVIDER: Final[slice] = slice(13, 21)
"""Position of the service provider code in the energy community ID, e.g. `AT00300000000RC100930000000965743`."""


class ActiveContractData(NamedTuple):
    """Active contract and the contracts to use for a meter point."""

    active_contract: dict[str, Any]
    contracts_to_use: list[dict[str, Any]]


class ProfilePeriods(NamedTuple):
    """Date ranges of the consumption profiles that are requested in a full update."""

    cutoff: date
    """Last day with L1/L2 profile data."""
    last_month_from: date
    """First day of the previous month."""
    last_month_to: date
    """Last day of the previous month with L1/L2 profile data."""

    @classmethod
    def from_today(cls, today: date, /) -> ProfilePeriods:
        """Return the date ranges for the given day."""
        cutoff: date = today - PROFILE_DATA_DELAY
        last_day_of_last_month: date = today.replace(day=1) - timedelta(days=1)

        return cls(
            cutoff=cutoff,
            last_month_from=last_day_of_last_month.replace(day=1),
            last_month_to=min(last_day_of_last_month, cutoff),
        )


class Timeslice(NamedTuple):
    """Energy community timeslice of a contract account at a meter point."""

    contract_account_number: str
    meter_point_administration_number: str
    data: dict[str, Any]


class ProfileRequest(NamedTuple):
    """Consumption profile request of an energy community timeslice."""

    targets: tuple[list[dict[str, Any]], ...]
    """Lists of the energy community device data the profile is appended to."""
    timeslice: Timeslice
    date_from: date
    date_to: date


def _valid_through(consent: dict[str, Any]) -> tuple[date, date]:
    """Return the validity period of a consent."""
    return (
        date.fromisoformat(consent["validThrough"]["from"]),
        date.fromisoformat(consent["validThrough"]["to"]),
    )


class NetzOOEeServiceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch the data of all meter points and energy communities from the eService portal."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: NetzOOEeServiceConfigEntry,
        /,
        *,
        username: str,
        password: str,
        session: ClientSession,
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry: NetzOOEeServiceConfigEntry = entry

        self.api: NetzOOEeServiceAPI = NetzOOEeServiceAPI(
            username=username,
            password=password,
            session=session,
        )

        self._last_full_update: datetime | None = None
        self._api_error_logged: bool = False
        self._missing_consents_logged: set[str] = set()

        self.frequent_updates: bool = entry.options.get(CONF_FREQUENT_UPDATES, DEFAULT_FREQUENT_UPDATES)
        self.show_revoked_energy_communities: bool = entry.options.get(
            CONF_SHOW_REVOKED_ENERGY_COMMUNITIES,
            DEFAULT_SHOW_REVOKED_ENERGY_COMMUNITIES,
        )
        self.include_inactive_contract_account_data: bool = entry.options.get(
            CONF_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA,
            DEFAULT_INCLUDE_INACTIVE_CONTRACT_ACCOUNT_DATA,
        )
        self.show_inactive_meter_points: bool = entry.options.get(
            CONF_SHOW_INACTIVE_METER_POINTS,
            DEFAULT_SHOW_INACTIVE_METER_POINTS,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL if self.frequent_updates else SCAN_INTERVAL_FULL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all data, or with frequent updates only the energy community data in between full updates."""
        now: datetime = dt_util.now()
        # Compare in UTC, the difference of two local times ignores a DST change in between.
        now_utc: datetime = dt_util.as_utc(now)

        # Without frequent updates the coordinator only runs every SCAN_INTERVAL_FULL,
        # so always do a full update (avoids missing it because of scheduling jitter).
        full_update: bool = (
            not self.frequent_updates
            or self._last_full_update is None
            or now_utc - self._last_full_update >= SCAN_INTERVAL_FULL
        )

        try:
            if full_update:
                data: dict[str, Any] = await self._async_fetch_all_data(ProfilePeriods.from_today(now.date()))
                self._last_full_update = now_utc
            else:
                data = await self._async_fetch_energy_community_data()
        except AuthenticationError as error:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="authentication_error",
            ) from error
        except APIError as error:
            if self.data is None:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="update_failed",
                    translation_placeholders={"error": str(error)},
                ) from error

            # Log only once until the portal is available again.
            if not self._api_error_logged:
                _LOGGER.warning("Update failed, using cached data: %s", error)
                self._api_error_logged = True

            return self.data

        if self._api_error_logged:
            _LOGGER.info("The eService portal is available again")
            self._api_error_logged = False

        _LOGGER.debug("data: %s", data)
        return data

    async def _async_gather[T](self, coroutines: Iterable[Coroutine[Any, Any, T]], /) -> list[T]:
        """Run the requests concurrently, but at most MAX_PARALLEL_REQUESTS at the same time."""
        semaphore: asyncio.Semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)

        async def limited(coroutine: Coroutine[Any, Any, T]) -> T:
            try:
                async with semaphore:
                    return await coroutine
            finally:
                # Close the coroutine if it was cancelled before it started (avoids "never awaited").
                coroutine.close()

        tasks: list[asyncio.Task[T]] = [asyncio.create_task(limited(coroutine)) for coroutine in coroutines]

        try:
            return await asyncio.gather(*tasks)
        finally:
            # If a request fails, cancel the remaining ones (e.g. no further logins with rejected credentials).
            for task in tasks:
                task.cancel()

    async def _async_fetch_all_data(self, periods: ProfilePeriods, /) -> dict[str, Any]:
        """Fetch the data of all meter points and their energy communities."""
        consents_task: asyncio.Task[ConsentsMap] = asyncio.create_task(self._async_fetch_consents_map())
        contracts_task: asyncio.Task[dict[str, list[dict[str, Any]]]] = asyncio.create_task(
            self._async_fetch_contracts_by_mpan(),
        )

        try:
            await asyncio.gather(consents_task, contracts_task)
        finally:
            consents_task.cancel()
            contracts_task.cancel()

        consents_map: ConsentsMap = consents_task.result()
        contracts_by_mpan: dict[str, list[dict[str, Any]]] = contracts_task.result()

        data: dict[str, Any] = {}
        profile_requests: list[ProfileRequest] = []

        for mpan, contracts in contracts_by_mpan.items():
            active_contract_data: ActiveContractData | None = self._get_active_contract_data(mpan, contracts)

            if active_contract_data is None:
                continue

            self._append_meter_point_data(data, contract=active_contract_data.active_contract["contract"])
            profile_requests += self._append_energy_communities(
                data,
                active_contract_data,
                consents_map=consents_map,
                periods=periods,
            )

        profiles: list[list[dict[str, Any]]] = await self._async_gather(
            self._async_fetch_consumptions_profile(request) for request in profile_requests
        )

        for request, profile in zip(profile_requests, profiles, strict=True):
            for target in request.targets:
                target.extend(profile)

        return data

    async def _async_fetch_energy_community_data(self) -> dict[str, Any]:
        """Return the previous data with the current contribution factors and statuses of the energy communities."""
        consents_map: ConsentsMap = await self._async_fetch_consents_map()
        data: dict[str, Any] = dict(self.data)

        for device_identifier, device_data in self.data.items():
            if device_data["deviceType"] not in ENERGY_COMMUNITY_DEVICE_TYPES.values():
                continue

            consent: dict[str, Any] = self._get_consent(
                consents_map,
                device_data["meterPointAdministrationNumber"],
                device_data["deviceId"],
            )

            # Keep the previous values, the next full update removes the energy community if its consent is gone.
            if not consent:
                continue

            data[device_identifier] = device_data | {
                "contributionPercentage": consent.get("contributionPercentage"),
                "status": consent.get("status"),
            }

        _LOGGER.debug("Updated energy community data")
        return data

    async def _async_fetch_contracts_by_mpan(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch all contract accounts and group their electricity contracts by meter point."""
        dashboard: dict[str, Any] = await self.api.dashboard()
        _LOGGER.debug("dashboard: %s", dashboard)

        all_contract_accounts: list[dict[str, Any]] = await self._async_gather(
            self.api.contract_accounts(
                business_partner_number=account["businessPartnerNumber"],
                contract_account_number=account["contractAccountNumber"],
            )
            for account in dashboard["contractAccounts"]
        )

        contracts_by_mpan: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for contract_accounts in all_contract_accounts:
            _LOGGER.debug("contract_accounts: %s", contract_accounts)

            for contract in contract_accounts["contracts"]:
                if (
                    contract["branch"] == ConsumptionsProfilesBranch.ELECTRICITY.value
                    and contract["synthProfile"] in ELECTRICITY_SYNTH_PROFILES
                ):
                    contracts_by_mpan[contract["pointOfDelivery"]["meterPointAdministrationNumber"]].append(
                        {"contract": contract, "contractAccounts": contract_accounts},
                    )

        return contracts_by_mpan

    async def _async_fetch_consents_map(self) -> ConsentsMap:
        """Fetch the most recent consent per energy community, grouped by meter point."""
        latest_consents: dict[tuple[str, str], dict[str, Any]] = {}

        for consent in await self.api.consents():
            key: tuple[str, str] = (consent["pod"], consent["serviceProvider"])

            # The API returns the consent history, keep only the most recent consent.
            if key not in latest_consents or _valid_through(consent) > _valid_through(latest_consents[key]):
                latest_consents[key] = consent

        consents_map: ConsentsMap = defaultdict(list)

        for consent in latest_consents.values():
            consents_map[consent["pod"]].append(consent)

        return consents_map

    def _get_active_contract_data(self, mpan: str, contracts: list[dict[str, Any]], /) -> ActiveContractData | None:
        """Return the active contract and the contracts to use for the given meter point.

        Without an active contract, the most recently ended contract is used if inactive meter points are shown.
        """
        active_contract: dict[str, Any] | None = next(
            (item for item in contracts if item["contract"].get("active")),
            None,
        )

        if active_contract is None:
            if not self.show_inactive_meter_points:
                _LOGGER.warning(
                    "Skipping %d contract(s) because no active contract for meter point %s was returned by the API.",
                    len(contracts),
                    mpan,
                )
                return None

            most_recent_contract: dict[str, Any] = max(
                contracts,
                key=lambda item: date.fromisoformat(item["contract"]["moveOutDate"]),
            )

            _LOGGER.debug(
                "No active contract for meter point %s, "
                "using most recently ended contract (moveOutDate=%s) as fallback.",
                mpan,
                most_recent_contract["contract"]["moveOutDate"],
            )

            return ActiveContractData(active_contract=most_recent_contract, contracts_to_use=contracts)

        return ActiveContractData(
            active_contract=active_contract,
            contracts_to_use=contracts if self.include_inactive_contract_account_data else [active_contract],
        )

    @staticmethod
    def _get_consent(consents_map: ConsentsMap, mpan: str, energy_community_id: str, /) -> dict[str, Any]:
        """Return the consent of an energy community at a meter point, or an empty dict if there is none."""
        # The energy community ID contains the service provider code of the consent, usually at a fixed position.
        # Prefer an exact match there, so a code that also appears elsewhere in the ID does not match.
        consents: list[dict[str, Any]] = [
            consent for consent in consents_map.get(mpan, []) if consent["serviceProvider"] in energy_community_id
        ]
        return next(
            (
                consent
                for consent in consents
                if energy_community_id[ENERGY_COMMUNITY_ID_SERVICE_PROVIDER] == consent["serviceProvider"]
            ),
            consents[0] if consents else {},
        )

    @staticmethod
    def _append_meter_point_data(data: dict[str, Any], /, *, contract: dict[str, Any]) -> None:
        """Add the device data of the meter point of a contract."""
        point_of_delivery: dict[str, Any] = contract["pointOfDelivery"]
        meter_number: str = point_of_delivery["meter"]["meterNumber"]
        last_readings: list[dict[str, Any]] = point_of_delivery["lastReadings"].get("values", [])

        def last_reading(reference_numbers: set[str]) -> dict[str, Any]:
            return next(
                (
                    item
                    for item in last_readings
                    if item["meternumber"] == meter_number and item["referenceNumber"] in reference_numbers
                ),
                {},
            )

        data[point_of_delivery["meterPointAdministrationNumber"]] = {
            "deviceName": contract["synthProfile"],
            "deviceType": METER_POINT_DEVICE_TYPES[contract["synthProfile"]],
            "scaleType": contract["scaleType"],
            "monthlyTrend": point_of_delivery["monthlyTrend"],
            "yearlyTrend": point_of_delivery["yearlyTrend"],
            "supplier": contract["supplier"],
            "meterNumber": meter_number,
            "meterReading": last_reading(METER_READING_REFERENCE_NUMBERS),
            "lastMonthPeakPower": last_reading(PEAK_POWER_REFERENCE_NUMBERS),
        }

    def _append_energy_communities(
        self,
        data: dict[str, Any],
        active_contract_data: ActiveContractData,
        /,
        *,
        consents_map: ConsentsMap,
        periods: ProfilePeriods,
    ) -> list[ProfileRequest]:
        """Add the energy communities of a meter point and return the requests for their consumption profiles."""
        active_contract: dict[str, Any] = active_contract_data.active_contract["contract"]
        mpan: str = active_contract["pointOfDelivery"]["meterPointAdministrationNumber"]
        profile_requests: list[ProfileRequest] = []

        for item in active_contract_data.contracts_to_use:
            contract_account_number: str = item["contractAccounts"]["contractAccountNumber"]
            _LOGGER.debug("Contract %s", contract_account_number)

            for timeslice in item["contract"].get("energyCommunityData", {}).get("timeslices", []):
                _LOGGER.debug("  %s", timeslice["energyCommunityName"])

                energy_community: dict[str, Any] | None = self._get_or_create_energy_community(
                    data,
                    contract=active_contract,
                    consents_map=consents_map,
                    timeslice=timeslice,
                )

                if energy_community is not None:
                    profile_requests += self._get_profile_requests(
                        energy_community,
                        Timeslice(contract_account_number, mpan, timeslice),
                        periods=periods,
                    )

        return profile_requests

    def _get_or_create_energy_community(
        self,
        data: dict[str, Any],
        /,
        *,
        contract: dict[str, Any],
        consents_map: ConsentsMap,
        timeslice: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Return the device data of the energy community of a timeslice, or `None` if it is not shown."""
        mpan: str = contract["pointOfDelivery"]["meterPointAdministrationNumber"]
        consent: dict[str, Any] = self._get_consent(consents_map, mpan, timeslice["energyCommunityId"])

        if not consent:
            # Log only once until the consent is returned again.
            if timeslice["energyCommunityId"] not in self._missing_consents_logged:
                _LOGGER.warning("No consent found for energy community %s", timeslice["energyCommunityId"])
                self._missing_consents_logged.add(timeslice["energyCommunityId"])

            return None

        self._missing_consents_logged.discard(timeslice["energyCommunityId"])

        if consent["status"] == ConsentsStatus.REVOKED.value and not self.show_revoked_energy_communities:
            _LOGGER.debug("  Skipping revoked energy community %s", timeslice["energyCommunityName"])
            return None

        device_identifier: str = f"{mpan}_{consent['serviceProvider']}"

        if device_identifier not in data:
            data[device_identifier] = {
                "synthProfile": contract["synthProfile"],
                "meterPointAdministrationNumber": mpan,
                "deviceId": timeslice["energyCommunityId"],
                "deviceName": timeslice["energyCommunityName"],
                "deviceType": ENERGY_COMMUNITY_DEVICE_TYPES[contract["synthProfile"]],
                "totalL2": [],
                "monthlyL2": [],
                "totalL3": [],
                "contributionPercentage": consent.get("contributionPercentage"),
                "status": consent.get("status"),
            }

        energy_community: dict[str, Any] = data[device_identifier]
        return energy_community

    @staticmethod
    def _get_profile_requests(
        energy_community: dict[str, Any],
        timeslice: Timeslice,
        /,
        *,
        periods: ProfilePeriods,
    ) -> list[ProfileRequest]:
        """Return the profile requests of a timeslice.

        - ``totalL2``: L1/L2 profile up to the cutoff
        - ``monthlyL2``: L1/L2 profile of the previous month
        - ``totalL3``: complete L1/L2/L3 profile
        """
        available_from: date = date.fromisoformat(timeslice.data["profileDataAvailableFrom"])
        available_to: date = date.fromisoformat(timeslice.data["profileDataAvailableTo"])
        profile_requests: list[ProfileRequest] = []

        if available_from <= periods.cutoff:
            # If all data is older than the cutoff, the L1/L2 profile is also the complete profile.
            profile_requests.append(
                ProfileRequest(
                    timeslice=timeslice,
                    targets=(
                        (energy_community["totalL2"], energy_community["totalL3"])
                        if available_to <= periods.cutoff
                        else (energy_community["totalL2"],)
                    ),
                    date_from=available_from,
                    date_to=min(available_to, periods.cutoff),
                ),
            )

        if available_from <= periods.last_month_to and available_to >= periods.last_month_from:
            profile_requests.append(
                ProfileRequest(
                    timeslice=timeslice,
                    targets=(energy_community["monthlyL2"],),
                    date_from=max(periods.last_month_from, available_from),
                    date_to=min(periods.last_month_to, available_to),
                ),
            )

        if available_to > periods.cutoff:
            profile_requests.append(
                ProfileRequest(
                    timeslice=timeslice,
                    targets=(energy_community["totalL3"],),
                    date_from=available_from,
                    date_to=available_to,
                ),
            )

        return profile_requests

    async def _async_fetch_consumptions_profile(self, request: ProfileRequest, /) -> list[dict[str, Any]]:
        """Fetch the consumption profile of an energy community timeslice."""
        timeslice: Timeslice = request.timeslice
        date_from: str = request.date_from.isoformat()
        date_to: str = request.date_to.isoformat()

        consumptions_profile: list[dict[str, Any]] = await self.api.consumptions_profile(
            pods=[
                Pod(
                    contract_account_number=timeslice.contract_account_number,
                    profile_type=profile["profileType"],
                    best_available_granularity=profile["granularity"],
                    energy_community_id=timeslice.data["energyCommunityId"],
                    meter_point_administration_number=timeslice.meter_point_administration_number,
                    date_from=date_from,
                    date_to=date_to,
                )
                for profile in timeslice.data["profiles"]
            ],
        )

        for item in consumptions_profile:
            # Without data for the time range, the API returns no energy community information.
            item["energyCommunityName"] = timeslice.data["energyCommunityName"]
            item["energyCommunityId"] = timeslice.data["energyCommunityId"]

            # The time range returned by the API is not valid, use the requested one.
            item["from"] = date_from
            item["to"] = date_to

        return consumptions_profile
