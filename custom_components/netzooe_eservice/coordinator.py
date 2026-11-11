# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""DataUpdateCoordinator for the Netz OÖ eService integration."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import timedelta
from functools import partial
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
from netzooe_eservice_api.constants import Granularity
from netzooe_eservice_api.constants import ProfileType
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
from .const import ELECTRICITY_SYNTH_PROFILES
from .const import ENERGY_COMMUNITY_DEVICE_TYPES
from .const import ENERGY_COMMUNITY_ID_SERVICE_PROVIDER
from .const import MAX_PARALLEL_REQUESTS
from .const import METER_POINT_DEVICE_TYPES
from .const import METER_READING_REFERENCE_NUMBERS
from .const import PEAK_POWER_REFERENCE_NUMBERS
from .const import PROFILE_DATA_DELAY
from .const import SCAN_INTERVAL
from .const import SCAN_INTERVAL_FULL

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from collections.abc import Iterable

    from aiohttp import ClientSession
    from homeassistant.core import HomeAssistant

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)

type NetzOOEeServiceConfigEntry = ConfigEntry[NetzOOEeServiceDataUpdateCoordinator]
type ConsentsMap = dict[str, list[dict[str, Any]]]


@dataclass(frozen=True, kw_only=True)
class ActiveContractData:
    """Active contract and the contracts to use for a meter point."""

    active_contract: dict[str, Any]
    contracts_to_use: list[dict[str, Any]]


class DateRange(NamedTuple):
    """First and last day of a time range."""

    date_from: date
    date_to: date

    def intersection(self, other: DateRange) -> DateRange | None:
        """Return the days of both time ranges, or `None` if they have no day in common."""
        date_from: date = max(self.date_from, other.date_from)
        date_to: date = min(self.date_to, other.date_to)
        return DateRange(date_from, date_to) if date_from <= date_to else None


@dataclass(frozen=True, kw_only=True)
class ProfilePeriods:
    """Date ranges of the consumption profiles that are requested in a full update."""

    # Last day with L1/L2 profile data of the energy communities.
    cutoff: date
    # All days of the previous month.
    last_month: DateRange

    @classmethod
    def from_today(cls, today: date, /) -> ProfilePeriods:
        """Return the date ranges for the given day."""
        last_day_of_last_month: date = today.replace(day=1) - timedelta(days=1)

        return cls(
            cutoff=today - PROFILE_DATA_DELAY,
            last_month=DateRange(last_day_of_last_month.replace(day=1), last_day_of_last_month),
        )


@dataclass(frozen=True, kw_only=True)
class Timeslice:
    """Energy community timeslice of a contract account at a meter point."""

    contract_account_number: str
    meter_point_administration_number: str
    data: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class ProfileRequest:
    """Consumption profile request of a time range."""

    # Lists of the device data the profile is appended to.
    targets: tuple[list[dict[str, Any]], ...]
    date_range: DateRange


@dataclass(frozen=True, kw_only=True)
class EnergyCommunityProfileRequest(ProfileRequest):
    """Consumption profile request of an energy community timeslice."""

    timeslice: Timeslice


@dataclass(frozen=True, kw_only=True)
class MeterPointProfileRequest(ProfileRequest):
    """L1 consumption profile request of a contract account at a meter point."""

    contract_account_number: str
    meter_point_administration_number: str


class NetzOOEeServiceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch the data of all meter points and energy communities from the eService portal."""

    config_entry: NetzOOEeServiceConfigEntry

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
        self.api: NetzOOEeServiceAPI = NetzOOEeServiceAPI(
            username=username,
            password=password,
            session=session,
        )

        self._last_full_update: datetime | None = None
        self._logged_warnings: set[str] = set()

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
            config_entry=entry,
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

            self._warn_once("api_error", "Update failed, using cached data: %s", error)
            return self.data

        if self._warning_resolved("api_error"):
            _LOGGER.info("The eService portal is available again")

        return data

    async def _async_fetch_all_data(self, periods: ProfilePeriods, /) -> dict[str, Any]:
        """Fetch the data of all meter points and their energy communities."""
        consents_map: ConsentsMap
        contracts_by_mpan: dict[str, list[dict[str, Any]]]
        consents_map, contracts_by_mpan = await self._async_gather(
            [self._async_fetch_consents_map, self._async_fetch_contracts_by_mpan],
        )

        data: dict[str, Any] = {}
        energy_community_requests: list[EnergyCommunityProfileRequest] = []
        meter_point_requests: list[MeterPointProfileRequest] = []

        for mpan, contracts in contracts_by_mpan.items():
            active_contract_data: ActiveContractData | None = self._get_active_contract_data(mpan, contracts)

            if active_contract_data is None:
                continue

            meter_point: dict[str, Any] = self._append_meter_point_data(
                data,
                contract=active_contract_data.active_contract["contract"],
            )
            meter_point_requests += self._get_meter_point_profile_requests(
                meter_point,
                active_contract_data,
                periods=periods,
            )
            energy_community_requests += self._append_energy_communities(
                data,
                active_contract_data,
                consents_map=consents_map,
                periods=periods,
            )

        # Request the profiles of the energy communities and meter points together, within the same limit.
        profiles: list[list[dict[str, Any]]] = await self._async_gather(
            [
                *(
                    partial(self._async_fetch_energy_community_profile, request)
                    for request in energy_community_requests
                ),
                *(partial(self._async_fetch_meter_point_profile, request) for request in meter_point_requests),
            ],
        )
        requests: list[ProfileRequest] = [*energy_community_requests, *meter_point_requests]

        for request, profile in zip(requests, profiles, strict=True):
            for target in request.targets:
                target.extend(profile)

        return data

    async def _async_gather[T](self, requests: Iterable[Callable[[], Awaitable[T]]], /) -> list[T]:
        """Run the requests concurrently, but at most MAX_PARALLEL_REQUESTS at the same time."""
        semaphore: asyncio.Semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)

        # Create the coroutine only when the request starts, a task cancelled before it started
        # would otherwise leave the coroutine unawaited.
        async def limited(request: Callable[[], Awaitable[T]]) -> T:
            """Run a request as soon as the semaphore allows it."""
            async with semaphore:
                return await request()

        tasks: list[asyncio.Task[T]] = [asyncio.create_task(limited(request)) for request in requests]

        try:
            return await asyncio.gather(*tasks)
        finally:
            # If a request fails, cancel the remaining ones (e.g. no further logins with rejected credentials).
            for task in tasks:
                task.cancel()

    async def _async_fetch_consents_map(self) -> ConsentsMap:
        """Fetch the most recent consent per energy community, grouped by meter point."""
        latest_consents: dict[tuple[str, str], dict[str, Any]] = {}

        # The API returns the consent history, keep only the most recent consent.
        for consent in sorted(await self.api.consents(), key=self._valid_through, reverse=True):
            latest_consents.setdefault((consent["pod"], consent["serviceProvider"]), consent)

        consents_map: ConsentsMap = defaultdict(list)

        for consent in latest_consents.values():
            consents_map[consent["pod"]].append(consent)

        return consents_map

    @staticmethod
    def _valid_through(consent: dict[str, Any], /) -> tuple[date, date]:
        """Return the validity period of a consent."""
        return (
            date.fromisoformat(consent["validThrough"]["from"]),
            date.fromisoformat(consent["validThrough"]["to"]),
        )

    async def _async_fetch_contracts_by_mpan(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch all contract accounts and group their electricity contracts by meter point."""
        dashboard: dict[str, Any] = await self.api.dashboard()

        all_contract_accounts: list[dict[str, Any]] = await self._async_gather(
            partial(
                self.api.contract_accounts,
                business_partner_number=account["businessPartnerNumber"],
                contract_account_number=account["contractAccountNumber"],
            )
            for account in dashboard["contractAccounts"]
        )

        contracts_by_mpan: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for contract_accounts in all_contract_accounts:
            for contract in contract_accounts["contracts"]:
                if (
                    contract["branch"] == ConsumptionsProfilesBranch.ELECTRICITY.value
                    and contract["synthProfile"] in ELECTRICITY_SYNTH_PROFILES
                ):
                    contracts_by_mpan[contract["pointOfDelivery"]["meterPointAdministrationNumber"]].append(
                        {"contract": contract, "contractAccounts": contract_accounts},
                    )

        return contracts_by_mpan

    def _get_active_contract_data(self, mpan: str, contracts: list[dict[str, Any]], /) -> ActiveContractData | None:
        """Return the active contract and the contracts to use for the given meter point.

        Without an active contract, the most recently ended contract is used if inactive meter points are shown.
        As with an active contract, the other contracts of the meter point are only used if the data of inactive
        contract accounts is included.
        """
        active_contract: dict[str, Any] | None = next(
            (item for item in contracts if item["contract"].get("active")),
            None,
        )

        if active_contract is None:
            if not self.show_inactive_meter_points:
                self._warn_once(
                    f"inactive_meter_point_{mpan}",
                    "Skipping %d contract(s) because no active contract for meter point %s was returned by the API",
                    len(contracts),
                    mpan,
                )
                return None

            active_contract = max(contracts, key=self._contract_end)

            _LOGGER.debug(
                "No active contract for meter point %s, "
                "using most recently ended contract (moveOutDate=%s) as fallback",
                mpan,
                active_contract["contract"].get("moveOutDate"),
            )
        else:
            self._warning_resolved(f"inactive_meter_point_{mpan}")

        return ActiveContractData(
            active_contract=active_contract,
            contracts_to_use=contracts if self.include_inactive_contract_account_data else [active_contract],
        )

    def _warn_once(self, key: str, msg: str, /, *args: object) -> None:
        """Log a warning only once until its cause is gone (see `_warning_resolved`)."""
        if key not in self._logged_warnings:
            _LOGGER.warning(msg, *args)
            self._logged_warnings.add(key)

    @classmethod
    def _contract_end(cls, item: dict[str, Any], /) -> tuple[date, date, str]:
        """Return the sort key of a contract by its end, independent of the order returned by the API.

        Contracts that end on the same day are sorted by their start, then by their contract account number.
        """
        return (
            cls._contract_date(item, "moveOutDate"),
            cls._contract_date(item, "moveInDate"),
            item["contractAccounts"]["contractAccountNumber"],
        )

    @staticmethod
    def _contract_date(item: dict[str, Any], key: str, /) -> date:
        """Return a date of a contract, the earliest date if the API returns none."""
        value: str | None = item["contract"].get(key)
        return date.fromisoformat(value) if value else date.min

    def _warning_resolved(self, key: str, /) -> bool:
        """Mark the cause of a warning as gone and return whether the warning was logged."""
        if key not in self._logged_warnings:
            return False

        self._logged_warnings.discard(key)
        return True

    @staticmethod
    def _append_meter_point_data(data: dict[str, Any], /, *, contract: dict[str, Any]) -> dict[str, Any]:
        """Add the device data of the meter point of a contract and return it."""
        point_of_delivery: dict[str, Any] = contract["pointOfDelivery"]
        meter_number: str = point_of_delivery["meter"]["meterNumber"]
        last_readings: list[dict[str, Any]] = point_of_delivery["lastReadings"].get("values", [])

        def last_reading(reference_numbers: set[str]) -> dict[str, Any]:
            """Return the last reading of the meter for one of the reference numbers, or an empty dict."""
            return next(
                (
                    item
                    for item in last_readings
                    if item["meternumber"] == meter_number and item["referenceNumber"] in reference_numbers
                ),
                {},
            )

        meter_point: dict[str, Any] = {
            "deviceName": contract["synthProfile"],
            "deviceType": METER_POINT_DEVICE_TYPES[contract["synthProfile"]],
            "scaleType": contract["scaleType"],
            "monthlyTrend": point_of_delivery["monthlyTrend"],
            "yearlyTrend": point_of_delivery["yearlyTrend"],
            "supplier": contract["supplier"],
            "contractStart": contract.get("moveInDate"),
            "meterNumber": meter_number,
            "profileDataAvailableTo": point_of_delivery.get("availableTimeRange", {}).get("to"),
            "meterReading": last_reading(METER_READING_REFERENCE_NUMBERS),
            "lastMonthPeakPower": last_reading(PEAK_POWER_REFERENCE_NUMBERS),
            "totalL1": [],
            "monthlyL1": [],
            "dailyL1": [],
        }
        data[point_of_delivery["meterPointAdministrationNumber"]] = meter_point
        return meter_point

    @classmethod
    def _get_meter_point_profile_requests(
        cls,
        meter_point: dict[str, Any],
        active_contract_data: ActiveContractData,
        /,
        *,
        periods: ProfilePeriods,
    ) -> list[MeterPointProfileRequest]:
        """Return the L1 profile requests of all used contracts of a meter point.

        - ``totalL1``: all profile data
        - ``monthlyL1``: profile data of the previous month
        - ``dailyL1``: profile data of the last day with data of the meter point

        Each contract only requests its own time range, so data of the meter point is not counted twice.
        """
        mpan: str = active_contract_data.active_contract["contract"]["pointOfDelivery"][
            "meterPointAdministrationNumber"
        ]
        contract_ranges: list[tuple[str, DateRange]] = [
            (item["contractAccounts"]["contractAccountNumber"], date_range)
            for item in active_contract_data.contracts_to_use
            if (date_range := cls._available_range(item)) is not None
        ]

        last_day: date = max((date_range.date_to for _number, date_range in contract_ranges), default=date.min)
        profile_requests: list[MeterPointProfileRequest] = []

        for contract_account_number, date_range in contract_ranges:
            for target, period in (
                (meter_point["totalL1"], date_range),
                (meter_point["monthlyL1"], periods.last_month),
                (meter_point["dailyL1"], DateRange(last_day, last_day)),
            ):
                request_range: DateRange | None = date_range.intersection(period)

                if request_range is not None:
                    profile_requests.append(
                        MeterPointProfileRequest(
                            targets=(target,),
                            date_range=request_range,
                            contract_account_number=contract_account_number,
                            meter_point_administration_number=mpan,
                        ),
                    )

        return profile_requests

    @staticmethod
    def _available_range(item: dict[str, Any], /) -> DateRange | None:
        """Return the time range with profile data of a contract, or `None` if there is none.

        The time range of the portal is the one of the meter point, so it is limited to the contract.
        """
        available: dict[str, Any] | None = item["contract"]["pointOfDelivery"].get("availableTimeRange")

        if not available:
            return None

        move_in: str | None = item["contract"].get("moveInDate")
        move_out: str | None = item["contract"].get("moveOutDate")

        return DateRange(date.fromisoformat(available["from"]), date.fromisoformat(available["to"])).intersection(
            DateRange(
                date.fromisoformat(move_in) if move_in else date.min,
                date.fromisoformat(move_out) if move_out else date.max,
            ),
        )

    def _append_energy_communities(
        self,
        data: dict[str, Any],
        active_contract_data: ActiveContractData,
        /,
        *,
        consents_map: ConsentsMap,
        periods: ProfilePeriods,
    ) -> list[EnergyCommunityProfileRequest]:
        """Add the energy communities of a meter point and return the requests for their consumption profiles."""
        active_contract: dict[str, Any] = active_contract_data.active_contract["contract"]
        mpan: str = active_contract["pointOfDelivery"]["meterPointAdministrationNumber"]
        profile_requests: list[EnergyCommunityProfileRequest] = []

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
                    profile_requests += self._get_energy_community_profile_requests(
                        energy_community,
                        Timeslice(
                            contract_account_number=contract_account_number,
                            meter_point_administration_number=mpan,
                            data=timeslice,
                        ),
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
            self._warn_once(
                f"missing_consent_{timeslice['energyCommunityId']}",
                "No consent found for energy community %s",
                timeslice["energyCommunityId"],
            )
            return None

        self._warning_resolved(f"missing_consent_{timeslice['energyCommunityId']}")

        if consent["status"] == ConsentsStatus.REVOKED.value and not self.show_revoked_energy_communities:
            _LOGGER.debug("  Skipping revoked energy community %s", timeslice["energyCommunityName"])
            return None

        energy_community: dict[str, Any] = data.setdefault(
            f"{mpan}_{consent['serviceProvider']}",
            {
                "synthProfile": contract["synthProfile"],
                "meterPointAdministrationNumber": mpan,
                "deviceId": timeslice["energyCommunityId"],
                "deviceName": timeslice["energyCommunityName"],
                "deviceType": ENERGY_COMMUNITY_DEVICE_TYPES[contract["synthProfile"]],
                "totalL2": [],
                "monthlyL2": [],
                "totalL3": [],
                "monthlyL3": [],
                "contributionPercentage": consent.get("contributionPercentage"),
                "status": consent.get("status"),
                "validFrom": consent["validThrough"]["from"],
            },
        )
        return energy_community

    @staticmethod
    def _get_consent(consents_map: ConsentsMap, mpan: str, energy_community_id: str, /) -> dict[str, Any]:
        """Return the consent of an energy community at a meter point, or an empty dict if there is none."""
        # The energy community ID contains the service provider code of the consent at a fixed position.
        # Only match there, so a code that also appears elsewhere in the ID does not match.
        return next(
            (
                consent
                for consent in consents_map.get(mpan, [])
                if energy_community_id[ENERGY_COMMUNITY_ID_SERVICE_PROVIDER] == consent["serviceProvider"]
            ),
            {},
        )

    @staticmethod
    def _get_energy_community_profile_requests(
        energy_community: dict[str, Any],
        timeslice: Timeslice,
        /,
        *,
        periods: ProfilePeriods,
    ) -> list[EnergyCommunityProfileRequest]:
        """Return the profile requests of a timeslice.

        - ``totalL2``: L1/L2 profile up to the cutoff
        - ``monthlyL2``: L1/L2 profile of the previous month
        - ``totalL3``: complete L1/L2/L3 profile
        - ``monthlyL3``: complete L1/L2/L3 profile of the previous month
        """
        available: DateRange = DateRange(
            date.fromisoformat(timeslice.data["profileDataAvailableFrom"]),
            date.fromisoformat(timeslice.data["profileDataAvailableTo"]),
        )
        up_to_cutoff: DateRange | None = available.intersection(DateRange(date.min, periods.cutoff))
        whole_last_month: DateRange | None = available.intersection(periods.last_month)
        # The L1/L2 profile of the previous month also ends at the cutoff, the L1/L2 data after it is not available yet.
        last_month: DateRange | None = (
            up_to_cutoff.intersection(whole_last_month) if up_to_cutoff and whole_last_month else None
        )
        profile_requests: list[EnergyCommunityProfileRequest] = []

        if up_to_cutoff is not None:
            # If all data is older than the cutoff, the L1/L2 profile is also the complete profile.
            profile_requests.append(
                EnergyCommunityProfileRequest(
                    timeslice=timeslice,
                    targets=(
                        (energy_community["totalL2"], energy_community["totalL3"])
                        if up_to_cutoff == available
                        else (energy_community["totalL2"],)
                    ),
                    date_range=up_to_cutoff,
                ),
            )

        if last_month is not None:
            # If the whole previous month is older than the cutoff, the L1/L2 profile is also the complete profile.
            profile_requests.append(
                EnergyCommunityProfileRequest(
                    timeslice=timeslice,
                    targets=(
                        (energy_community["monthlyL2"], energy_community["monthlyL3"])
                        if last_month == whole_last_month
                        else (energy_community["monthlyL2"],)
                    ),
                    date_range=last_month,
                ),
            )

        if whole_last_month is not None and whole_last_month != last_month:
            profile_requests.append(
                EnergyCommunityProfileRequest(
                    timeslice=timeslice,
                    targets=(energy_community["monthlyL3"],),
                    date_range=whole_last_month,
                ),
            )

        if available.date_to > periods.cutoff:
            profile_requests.append(
                EnergyCommunityProfileRequest(
                    timeslice=timeslice,
                    targets=(energy_community["totalL3"],),
                    date_range=available,
                ),
            )

        return profile_requests

    async def _async_fetch_energy_community_profile(
        self,
        request: EnergyCommunityProfileRequest,
        /,
    ) -> list[dict[str, Any]]:
        """Fetch the consumption profile of an energy community timeslice."""
        timeslice: Timeslice = request.timeslice
        date_from: str = request.date_range.date_from.isoformat()
        date_to: str = request.date_range.date_to.isoformat()

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

    async def _async_fetch_meter_point_profile(self, request: MeterPointProfileRequest, /) -> list[dict[str, Any]]:
        """Fetch the L1 consumption profile of a contract account at a meter point."""
        consumptions_profile: list[dict[str, Any]] = await self.api.consumptions_profile(
            pods=[
                Pod(
                    contract_account_number=request.contract_account_number,
                    profile_type=ProfileType.ACTIVE_CURRENT,
                    # The portal chooses the resolution from the length of the time range.
                    best_available_granularity=Granularity.QUARTER_OF_AN_HOUR,
                    meter_point_administration_number=request.meter_point_administration_number,
                    date_from=request.date_range.date_from.isoformat(),
                    date_to=request.date_range.date_to.isoformat(),
                ),
            ],
        )

        # The single values of the profile are not used and would make the data large.
        return [{key: value for key, value in item.items() if key != "profileValues"} for item in consumptions_profile]

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
                "validFrom": consent["validThrough"]["from"],
            }

        _LOGGER.debug("Updated energy community data")
        return data
