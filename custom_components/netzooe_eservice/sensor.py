# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Support for the Netz OÖ eService sensors."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from datetime import date
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import Literal

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.const import EntityCategory
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.core import callback
from homeassistant.util import dt as dt_util
from netzooe_eservice_api.constants import ConsentsStatus
from netzooe_eservice_api.constants import Granularity

from .const import DOMAIN
from .const import ENERGY_COMMUNITY_CONSUMPTION
from .const import ENERGY_COMMUNITY_GENERATION
from .const import ENERGY_COMMUNITY_OVER_COVERAGE
from .const import ENERGY_COMMUNITY_OWN_COVERAGE
from .const import STATUS_OPTIONS
from .const import DeviceType
from .entity import NetzOOEeServiceEntity

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import EnergyCommunityData
    from .coordinator import MeterPointData
    from .coordinator import NetzOOEeServiceConfigEntry
    from .coordinator import NetzOOEeServiceDataUpdateCoordinator

PARALLEL_UPDATES: Final[int] = 0


type Direction = Literal["import", "export"]
# The profile lists of the device data of a meter point and of an energy community.
type MeterPointProfile = Literal["totalL1", "monthlyL1", "dailyL1"]
type EnergyCommunityProfile = Literal["totalL2", "totalL3", "monthlyL2", "monthlyL3"]


class NetzOOEeServiceSensorEntity(NetzOOEeServiceEntity, SensorEntity):
    """Netz OÖ eService sensor entity."""

    # The timeline grows with every timeslice, so it is not stored in the database.
    _unrecorded_attributes: frozenset[str] = frozenset({"timeline"})

    def __init__(
        self,
        coordinator: NetzOOEeServiceDataUpdateCoordinator,
        description: SensorEntityDescription,
        device_identifier: str,
    ) -> None:
        """Initialize the entity."""
        self.entity_description = description

        super().__init__(
            coordinator,
            device_identifier=device_identifier,
        )

        self._attr_unique_id = f"{self.device_identifier}_{self.entity_description.key}".lower()
        self.entity_id: str = f"{SENSOR_DOMAIN}.{DOMAIN}_{self._attr_unique_id}"


class NetzOOEeServiceMeterPointSensorEntity(NetzOOEeServiceSensorEntity):
    """Netz OÖ eService sensor entity of a meter point."""

    entity_description: NetzOOEeServiceMeterPointSensorEntityDescription

    @property
    def native_value(self) -> StateType | date:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._data)

    @property
    def _data(self) -> MeterPointData:
        """Return the device data of the meter point."""
        return self.coordinator.meter_points[self.device_identifier]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return self.entity_description.extra_state_attributes_fn(self._data)


class NetzOOEeServiceMeterPointProfileSensorEntity(NetzOOEeServiceMeterPointSensorEntity):
    """Meter point sensor entity with the L1 profile of a time range."""

    # The timeline has one entry per section of the profile, so it stays small and is recorded.
    _unrecorded_attributes: frozenset[str] = frozenset()

    @property
    def available(self) -> bool:
        """Return whether the sensor is available, it is not without profile data."""
        return super().available and self.native_value is not None


class NetzOOEeServiceEnergyCommunitySensorEntity(NetzOOEeServiceSensorEntity):
    """Netz OÖ eService sensor entity of an energy community."""

    entity_description: NetzOOEeServiceEnergyCommunitySensorEntityDescription

    @property
    def native_value(self) -> StateType | date:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._data)

    @property
    def _data(self) -> EnergyCommunityData:
        """Return the device data of the energy community."""
        return self.coordinator.energy_communities[self.device_identifier]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return self.entity_description.extra_state_attributes_fn(self._data)


class NetzOOEeServiceAggregatedSensorEntity(NetzOOEeServiceSensorEntity):
    """Meter point sensor entity with the total of all energy communities of the meter point."""

    entity_description: NetzOOEeServiceEnergyCommunitySensorEntityDescription

    @property
    def native_value(self) -> float:
        """Return the sum of the values of all active (or, if shown, all) energy communities of the meter point."""
        prefix: str = f"{self.device_identifier}_"

        return sum(
            (
                value
                for device_identifier, data in self.coordinator.energy_communities.items()
                if device_identifier.startswith(prefix)
                and (data["status"] == ConsentsStatus.ACTIVE.value or self.coordinator.show_revoked_energy_communities)
                and isinstance(value := self.entity_description.value_fn(data), float)
            ),
            start=0.0,
        )


def _no_attributes(_data: object) -> Mapping[str, Any] | None:
    """Return no extra state attributes."""
    return None


@dataclass(frozen=True, kw_only=True)
class NetzOOEeServiceMeterPointSensorEntityDescription(SensorEntityDescription):
    """Class describing Netz OÖ eService sensor entities of a meter point."""

    entity_class: type[NetzOOEeServiceMeterPointSensorEntity] = NetzOOEeServiceMeterPointSensorEntity
    # Returns the state from the device data.
    value_fn: Callable[[MeterPointData], StateType | date]
    # Returns the extra state attributes from the device data.
    extra_state_attributes_fn: Callable[[MeterPointData], Mapping[str, Any] | None] = _no_attributes


@dataclass(frozen=True, kw_only=True)
class NetzOOEeServiceEnergyCommunitySensorEntityDescription(SensorEntityDescription):
    """Class describing Netz OÖ eService sensor entities of an energy community, or their totals at a meter point."""

    entity_class: type[NetzOOEeServiceAggregatedSensorEntity | NetzOOEeServiceEnergyCommunitySensorEntity] = (
        NetzOOEeServiceEnergyCommunitySensorEntity
    )
    # Returns the state from the device data.
    value_fn: Callable[[EnergyCommunityData], StateType | date]
    # Returns the extra state attributes from the device data.
    extra_state_attributes_fn: Callable[[EnergyCommunityData], Mapping[str, Any] | None] = _no_attributes


# The description of a sensor of a meter point or of an energy community.
type NetzOOEeServiceSensorEntityDescription = (
    NetzOOEeServiceEnergyCommunitySensorEntityDescription | NetzOOEeServiceMeterPointSensorEntityDescription
)


def _status(data: EnergyCommunityData) -> str | None:
    """Return the status of the consent, or `None` if it is missing or unknown."""
    status: str = (data["status"] or "").lower()
    return status if status in STATUS_OPTIONS else None


def _date(value: str | None) -> date | None:
    """Return the date of an ISO date string, or `None` if it is missing."""
    return date.fromisoformat(value) if value else None


def _sum_by_type(items: list[dict[str, Any]], target_type: str) -> float:
    """Return the sum of all profile values of the given type."""
    # Start with a float, the portal may return whole numbers as integers.
    total: float = sum((item["sum"]["value"] for item in items if item["type"] == target_type), start=0.0)
    return total


def _timeline_by_type(
    items: list[dict[str, Any]],
    target_type: str,
    /,
    *,
    with_statistics: bool,
) -> list[dict[str, Any]]:
    """Return the time ranges of all profile values of the given type, optionally with the values of the portal."""
    return [
        {"from": item["from"], "to": item["to"]} | (_profile_statistics(item) if with_statistics else {})
        for item in items
        if item["type"] == target_type
    ]


def _local_date(value: str) -> str:
    """Return the local date of an ISO timestamp of the portal, without a time zone it is already local time."""
    return dt_util.as_local(dt_util.parse_datetime(value, raise_on_error=True)).date().isoformat()


def _local_timestamp(value: str | None) -> str | None:
    """Return the local ISO timestamp of a timestamp of the portal (UTC), or `None` if it is missing."""
    return dt_util.as_local(dt_util.parse_datetime(value, raise_on_error=True)).isoformat() if value else None


def _resolution(value: str | None) -> str | None:
    """Return the resolution of a profile section, or `None` if it is missing or unknown."""
    try:
        return Granularity(value).value.lower()
    except ValueError:
        return None


def _timeline_entry(item: Mapping[str, Any]) -> dict[str, Any]:
    """Return the timeline entry of a section of an L1 profile."""
    return {"from": _local_date(item["from"]), "to": _local_date(item["to"])} | _profile_statistics(item)


def _profile_statistics(item: Mapping[str, Any]) -> dict[str, Any]:
    """Return the sum, average, maximum and minimum of a profile as returned by the portal."""
    maximum: Mapping[str, Any] = item.get("maximum") or {}
    minimum: Mapping[str, Any] = item.get("minimum") or {}

    return {
        "resolution": _resolution(item.get("granularity")),
        "sum": item["sum"]["value"],
        "average": (item.get("average") or {}).get("value"),
        "maximum": maximum.get("value"),
        "maximum_timestamp": _local_timestamp(maximum.get("dateTime")),
        "minimum": minimum.get("value"),
        "minimum_timestamp": _local_timestamp(minimum.get("dateTime")),
    }


def _meter_point_profile_descriptions(
    direction: Direction, /
) -> list[NetzOOEeServiceMeterPointSensorEntityDescription]:
    """Return the sensors with the L1 profile of all data, the previous month and the last day of a meter point."""

    def description(key: str, profile: MeterPointProfile, /) -> NetzOOEeServiceMeterPointSensorEntityDescription:
        """Return the sensor with the sum of all sections of a profile."""

        def value(data: MeterPointData) -> float | None:
            """Return the sum of all sections, or `None` without profile data."""
            items: list[dict[str, Any]] = data[profile]

            if not items:
                return None

            # Start with a float, the portal may return whole numbers as integers.
            total: float = sum((item["sum"]["value"] for item in items), start=0.0)
            return total

        def attributes(data: MeterPointData) -> Mapping[str, Any]:
            """Return the timeline with one entry per section of the profile."""
            timeline: list[dict[str, Any]] = sorted(
                (_timeline_entry(item) for item in data[profile]),
                key=lambda entry: entry["from"],
            )
            return {"timeline": timeline}

        return NetzOOEeServiceMeterPointSensorEntityDescription(
            entity_class=NetzOOEeServiceMeterPointProfileSensorEntity,
            device_class=SensorDeviceClass.ENERGY,
            key=key,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL,
            translation_key=key,
            value_fn=value,
            extra_state_attributes_fn=attributes,
        )

    return [
        description(f"{direction}_l1", "totalL1"),
        description(f"last_month_{direction}_l1", "monthlyL1"),
        description(f"last_day_{direction}_l1", "dailyL1"),
    ]


def _trend_descriptions(key: Literal["monthly", "yearly"], /) -> list[NetzOOEeServiceMeterPointSensorEntityDescription]:
    """Return the sensors of the monthly or yearly consumption trend of a meter point."""
    trend: Literal["monthlyTrend", "yearlyTrend"] = "monthlyTrend" if key == "monthly" else "yearlyTrend"

    def period(name: str, consumption: str, timerange: str) -> NetzOOEeServiceMeterPointSensorEntityDescription:
        """Return the consumption sensor of one period of the trend."""
        return NetzOOEeServiceMeterPointSensorEntityDescription(
            device_class=SensorDeviceClass.ENERGY,
            key=f"{key}_trend_{name}",
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL,
            translation_key=f"{key}_trend_{name}",
            value_fn=lambda data: data[trend][consumption]["sum"],
            extra_state_attributes_fn=lambda data: {
                "per_day": data[trend][consumption]["perDay"],
                "days": data[trend][consumption]["days"],
                "from": data[trend][timerange]["from"],
                "to": data[trend][timerange]["to"],
            },
        )

    def change(data: MeterPointData) -> float:
        """Return the change of the new period compared to the old one in percent."""
        new: float = data[trend]["consumptionNew"]["sum"]
        old: float = data[trend]["consumptionOld"]["sum"]
        return (new - old) / old * 100 if old > 0 else 0

    return [
        period("new", "consumptionNew", "timerangeNew"),
        period("old", "consumptionOld", "timerangeOld"),
        NetzOOEeServiceMeterPointSensorEntityDescription(
            key=f"{key}_trend",
            native_unit_of_measurement=PERCENTAGE,
            suggested_display_precision=2,
            translation_key=f"{key}_trend",
            value_fn=change,
        ),
    ]


def _energy_community_descriptions(
    direction: Direction,
    /,
    *,
    energy_community: tuple[str, str | None],
    supplier: tuple[str, str | None],
) -> list[NetzOOEeServiceEnergyCommunitySensorEntityDescription]:
    """Return the energy community and supplier sensors of an energy community.

    ``energy_community`` and ``supplier`` are the profile types whose values are added and subtracted.
    Only the energy community sensors have the name and ID of the energy community as attributes.
    """

    def description(
        key: str,
        profile: EnergyCommunityProfile,
        types: tuple[str, str | None],
        /,
        *,
        with_name: bool,
    ) -> NetzOOEeServiceEnergyCommunitySensorEntityDescription:
        """Return the sensor with the sum of the given profile types of a profile."""
        positive_type, negative_type = types

        def value(data: EnergyCommunityData) -> float:
            """Return the sum of the positive profile type minus the negative one."""
            total: float = _sum_by_type(data[profile], positive_type)
            return total - _sum_by_type(data[profile], negative_type) if negative_type else total

        def attributes(data: EnergyCommunityData) -> Mapping[str, Any]:
            """Return the timeline and, for energy community sensors, the name and ID of the energy community."""
            items: list[dict[str, Any]] = data[profile]

            if not items:
                return {}

            name: dict[str, Any] = (
                {"name": items[0]["energyCommunityName"], "id": items[0]["energyCommunityId"]} if with_name else {}
            )
            # The portal only returns the average, maximum and minimum of a single profile type, not of a difference.
            return name | {
                "timeline": _timeline_by_type(items, positive_type, with_statistics=negative_type is None),
            }

        return NetzOOEeServiceEnergyCommunitySensorEntityDescription(
            device_class=SensorDeviceClass.ENERGY,
            key=key,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL,
            translation_key=key,
            value_fn=value,
            extra_state_attributes_fn=attributes,
        )

    # Prefix of the key, profile and level of the sensors.
    profiles: tuple[tuple[str, EnergyCommunityProfile, str], ...] = (
        ("", "totalL2", "l2"),
        ("", "totalL3", "l3"),
        ("last_month_", "monthlyL2", "l2"),
        ("last_month_", "monthlyL3", "l3"),
    )

    return [
        description(f"{prefix}{kind}_{direction}_{level}", profile, types, with_name=kind == "energy_community")
        for prefix, profile, level in profiles
        for kind, types in (("energy_community", energy_community), ("supplier", supplier))
    ]


def _aggregated_descriptions(
    descriptions: list[NetzOOEeServiceEnergyCommunitySensorEntityDescription],
    /,
) -> list[NetzOOEeServiceEnergyCommunitySensorEntityDescription]:
    """Return the meter point sensors with the totals of the given energy community sensors."""
    return [
        replace(
            description,
            entity_class=NetzOOEeServiceAggregatedSensorEntity,
            entity_registry_enabled_default=False,
            extra_state_attributes_fn=_no_attributes,
        )
        for description in descriptions
    ]


def _peak_power_description(direction: Direction, /) -> NetzOOEeServiceMeterPointSensorEntityDescription:
    """Return the sensor with the maximum power of the previous month of a meter point."""
    return NetzOOEeServiceMeterPointSensorEntityDescription(
        device_class=SensorDeviceClass.POWER,
        key=f"last_month_peak_{direction}_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key=f"last_month_peak_{direction}_power",
        value_fn=lambda data: data["lastMonthPeakPower"].get("newResult", {}).get("readingValue"),
        extra_state_attributes_fn=lambda data: {
            "timestamp": data["lastMonthPeakPower"].get("newResult", {}).get("timestamp"),
            "meter_number": data["meterNumber"],
        },
    )


SENSOR_DEFAULT_TYPES: Final[list[NetzOOEeServiceMeterPointSensorEntityDescription]] = [
    NetzOOEeServiceMeterPointSensorEntityDescription(
        key="scale_type",
        translation_key="scale_type",
        value_fn=lambda data: data["scaleType"],
    ),
    NetzOOEeServiceMeterPointSensorEntityDescription(
        device_class=SensorDeviceClass.ENERGY,
        key="meter_reading",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="meter_reading",
        value_fn=lambda data: data["meterReading"].get("newResult", {}).get("readingValue"),
        extra_state_attributes_fn=lambda data: {
            "timestamp": data["meterReading"].get("newResult", {}).get("timestamp"),
            "meter_number": data["meterNumber"],
        },
    ),
    NetzOOEeServiceMeterPointSensorEntityDescription(
        key="supplier",
        translation_key="supplier",
        value_fn=lambda data: data["supplier"]["name"],
        extra_state_attributes_fn=lambda data: {
            "id": data["supplier"].get("id"),
            "contract_start": data["contractStart"],
        },
    ),
    NetzOOEeServiceMeterPointSensorEntityDescription(
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        key="profile_data_available_to",
        translation_key="profile_data_available_to",
        value_fn=lambda data: _date(data["profileDataAvailableTo"]),
    ),
    *_trend_descriptions("monthly"),
    *_trend_descriptions("yearly"),
]

SENSOR_ENERGY_COMMUNITY_DEFAULT_TYPES: Final[list[NetzOOEeServiceEnergyCommunitySensorEntityDescription]] = [
    NetzOOEeServiceEnergyCommunitySensorEntityDescription(
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key="status",
        options=STATUS_OPTIONS,
        translation_key="status",
        value_fn=_status,
        extra_state_attributes_fn=lambda data: {"valid_from": data["validFrom"]},
    ),
    NetzOOEeServiceEnergyCommunitySensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        key="contribution_factor",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="contribution_factor",
        value_fn=lambda data: data["contributionPercentage"],
    ),
]

SENSOR_ENERGY_COMMUNITY_IMPORT_TYPES: Final[list[NetzOOEeServiceEnergyCommunitySensorEntityDescription]] = (
    _energy_community_descriptions(
        "import",
        energy_community=(ENERGY_COMMUNITY_OWN_COVERAGE, None),
        supplier=(ENERGY_COMMUNITY_CONSUMPTION, ENERGY_COMMUNITY_OWN_COVERAGE),
    )
)

SENSOR_ENERGY_COMMUNITY_EXPORT_TYPES: Final[list[NetzOOEeServiceEnergyCommunitySensorEntityDescription]] = (
    _energy_community_descriptions(
        "export",
        energy_community=(ENERGY_COMMUNITY_GENERATION, ENERGY_COMMUNITY_OVER_COVERAGE),
        supplier=(ENERGY_COMMUNITY_OVER_COVERAGE, None),
    )
)

SENSOR_HOUSEHOLD_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = [
    *_meter_point_profile_descriptions("import"),
    *_aggregated_descriptions(SENSOR_ENERGY_COMMUNITY_IMPORT_TYPES),
    _peak_power_description("import"),
]

SENSOR_PHOTOVOLTAICS_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = [
    *_meter_point_profile_descriptions("export"),
    *_aggregated_descriptions(SENSOR_ENERGY_COMMUNITY_EXPORT_TYPES),
    _peak_power_description("export"),
]

SENSOR_TYPES: Final[dict[str, list[NetzOOEeServiceSensorEntityDescription]]] = {
    DeviceType.HOUSEHOLD.value: [*SENSOR_DEFAULT_TYPES, *SENSOR_HOUSEHOLD_TYPES],
    DeviceType.PHOTOVOLTAICS.value: [*SENSOR_DEFAULT_TYPES, *SENSOR_PHOTOVOLTAICS_TYPES],
    DeviceType.ENERGY_COMMUNITY_IMPORT.value: [
        *SENSOR_ENERGY_COMMUNITY_DEFAULT_TYPES,
        *SENSOR_ENERGY_COMMUNITY_IMPORT_TYPES,
    ],
    DeviceType.ENERGY_COMMUNITY_EXPORT.value: [
        *SENSOR_ENERGY_COMMUNITY_DEFAULT_TYPES,
        *SENSOR_ENERGY_COMMUNITY_EXPORT_TYPES,
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: NetzOOEeServiceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors of all devices from a config entry and add the sensors of new devices after updates."""
    coordinator: NetzOOEeServiceDataUpdateCoordinator = entry.runtime_data
    known_device_identifiers: set[str] = set()

    @callback
    def async_add_new_devices() -> None:
        """Add the sensors of the devices that are not known yet."""
        device_identifiers: set[str] = set(coordinator.data)
        new_device_identifiers: set[str] = device_identifiers - known_device_identifiers

        # Removed devices are forgotten, so their sensors are added again if they come back.
        known_device_identifiers.intersection_update(device_identifiers)
        known_device_identifiers.update(new_device_identifiers)

        if not new_device_identifiers:
            return

        async_add_entities(
            description.entity_class(
                coordinator,
                description=description,
                device_identifier=device_identifier,
            )
            for device_identifier, data in coordinator.data.items()
            if device_identifier in new_device_identifiers
            for description in SENSOR_TYPES[data["deviceType"]]
        )

    async_add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(async_add_new_devices))
