# Copyright 2026 Michael Hacker
# SPDX-License-Identifier: Apache-2.0
"""Support for the Netz OÖ eService sensors."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import Literal
from typing import cast

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
from homeassistant.helpers import device_registry as dr
from netzooe_eservice_api.constants import ConsentsStatus

from .const import DOMAIN
from .const import DeviceType
from .entity import NetzOOEeServiceEntity

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceInfo
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import NetzOOEeServiceConfigEntry
    from .coordinator import NetzOOEeServiceDataUpdateCoordinator

PARALLEL_UPDATES: Final[int] = 0

ENERGY_COMMUNITY_OWN_COVERAGE: Final[str] = "ENERGY_COMMUNITY_OWN_COVERAGE"
ENERGY_COMMUNITY_CONSUMPTION: Final[str] = "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR"
ENERGY_COMMUNITY_GENERATION: Final[str] = "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR"
ENERGY_COMMUNITY_OVER_COVERAGE: Final[str] = "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR"
STATUS_OPTIONS: Final[list[str]] = [status.value.lower() for status in ConsentsStatus]

type Direction = Literal["import", "export"]


class NetzOOEeServiceSensorEntity(NetzOOEeServiceEntity, SensorEntity):
    """Netz OÖ eService sensor entity."""

    entity_description: NetzOOEeServiceSensorEntityDescription

    def __init__(
        self,
        coordinator: NetzOOEeServiceDataUpdateCoordinator,
        description: NetzOOEeServiceSensorEntityDescription,
        entry: NetzOOEeServiceConfigEntry,
        device_identifier: str,
    ) -> None:
        """Initialize the entity."""
        self.entity_description = description

        super().__init__(
            coordinator,
            entry=entry,
            device_identifier=device_identifier,
        )

        self._attr_unique_id = f"{self.device_identifier}_{self.entity_description.key}".lower()
        self.entity_id: str = f"{SENSOR_DOMAIN}.{DOMAIN}_{self._attr_unique_id}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return self.entity_description.extra_state_attributes_fn(self.data)


class NetzOOEeServiceEnergyCommunitySensorEntity(NetzOOEeServiceSensorEntity):
    """Netz OÖ eService energy community sensor entity."""

    @property
    def device_name(self) -> str:
        """Return the name of the device."""
        return (
            f"{self.data['synthProfile']}: {self.data['deviceName']} "
            f"({self._short_device_id(self.data['meterPointAdministrationNumber'])})"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info, linked to the device of the meter point."""
        device_info: DeviceInfo = super().device_info
        device_info["via_device_id"] = dr.async_get_device_id_by_identifier(
            self.hass,
            (DOMAIN, self.data["meterPointAdministrationNumber"]),
            config_entry_id=self.entry.entry_id,
        )
        return device_info


class NetzOOEeServiceAggregatedSensorEntity(NetzOOEeServiceSensorEntity):
    """Meter point sensor entity with the total of all energy communities of the meter point."""

    @property
    def native_value(self) -> float:
        """Return the sum of the values of all active (or, if shown, all) energy communities of the meter point."""
        prefix: str = f"{self.device_identifier}_"

        return sum(
            (
                cast("float", self.entity_description.value_fn(data))
                for device_identifier, data in self.coordinator.data.items()
                if device_identifier.startswith(prefix)
                and (data["status"] == ConsentsStatus.ACTIVE.value or self.coordinator.show_revoked_energy_communities)
            ),
            start=0.0,
        )


def _no_attributes(_data: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return no extra state attributes."""
    return None


@dataclass(frozen=True, kw_only=True)
class NetzOOEeServiceSensorEntityDescription(SensorEntityDescription):
    """Class describing Netz OÖ eService sensor entities."""

    entity_class: type[NetzOOEeServiceSensorEntity] = NetzOOEeServiceSensorEntity
    value_fn: Callable[[Mapping[str, Any]], StateType]
    """Return the state from the device data."""
    extra_state_attributes_fn: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] = _no_attributes
    """Return the extra state attributes from the device data."""


def _status(data: Mapping[str, Any]) -> str | None:
    """Return the status of the consent, or `None` if it is missing or unknown."""
    status: str = (data["status"] or "").lower()
    return status if status in STATUS_OPTIONS else None


def _sum_by_type(items: list[dict[str, Any]], target_type: str) -> float:
    """Return the sum of all profile values of the given type."""
    total: float = sum(item["sum"]["value"] for item in items if item["type"] == target_type)
    return total


def _timeline_by_type(items: list[dict[str, Any]], target_type: str) -> list[dict[str, str]]:
    """Return the time ranges of all profile values of the given type."""
    return [{"from": item["from"], "to": item["to"]} for item in items if item["type"] == target_type]


def _trend_descriptions(key: Literal["monthly", "yearly"], /) -> list[NetzOOEeServiceSensorEntityDescription]:
    """Return the sensors of the monthly or yearly consumption trend of a meter point."""
    trend: str = f"{key}Trend"

    def period(name: str, consumption: str, timerange: str) -> NetzOOEeServiceSensorEntityDescription:
        return NetzOOEeServiceSensorEntityDescription(
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

    def change(data: Mapping[str, Any]) -> float:
        new: float = data[trend]["consumptionNew"]["sum"]
        old: float = data[trend]["consumptionOld"]["sum"]
        return (new - old) / old * 100 if old > 0 else 0

    return [
        period("new", "consumptionNew", "timerangeNew"),
        period("old", "consumptionOld", "timerangeOld"),
        NetzOOEeServiceSensorEntityDescription(
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
) -> list[NetzOOEeServiceSensorEntityDescription]:
    """Return the energy community and supplier sensors of an energy community.

    ``energy_community`` and ``supplier`` are the profile types whose values are added and subtracted.
    Only the energy community sensors have the name and ID of the energy community as attributes.
    """

    def description(
        key: str,
        profile: str,
        types: tuple[str, str | None],
        /,
        *,
        with_name: bool,
    ) -> NetzOOEeServiceSensorEntityDescription:
        positive_type, negative_type = types

        def value(data: Mapping[str, Any]) -> float:
            total: float = _sum_by_type(data[profile], positive_type)
            return total - _sum_by_type(data[profile], negative_type) if negative_type else total

        def attributes(data: Mapping[str, Any]) -> Mapping[str, Any]:
            items: list[dict[str, Any]] = data[profile]

            if not items:
                return {}

            name: dict[str, Any] = (
                {"name": items[0]["energyCommunityName"], "id": items[0]["energyCommunityId"]} if with_name else {}
            )
            return name | {"timeline": _timeline_by_type(items, positive_type)}

        return NetzOOEeServiceSensorEntityDescription(
            entity_class=NetzOOEeServiceEnergyCommunitySensorEntity,
            device_class=SensorDeviceClass.ENERGY,
            key=key,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL,
            translation_key=key,
            value_fn=value,
            extra_state_attributes_fn=attributes,
        )

    return [
        description(f"{prefix}{kind}_{direction}_{level}", profile, types, with_name=kind == "energy_community")
        for prefix, profile, level in (("", "totalL2", "l2"), ("", "totalL3", "l3"), ("last_month_", "monthlyL2", "l2"))
        for kind, types in (("energy_community", energy_community), ("supplier", supplier))
    ]


def _aggregated_descriptions(
    descriptions: list[NetzOOEeServiceSensorEntityDescription],
    /,
) -> list[NetzOOEeServiceSensorEntityDescription]:
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


def _peak_power_description(direction: Direction, /) -> NetzOOEeServiceSensorEntityDescription:
    """Return the sensor with the maximum power of the previous month of a meter point."""
    return NetzOOEeServiceSensorEntityDescription(
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


SENSOR_DEFAULT_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = [
    NetzOOEeServiceSensorEntityDescription(
        key="scale_type",
        translation_key="scale_type",
        value_fn=lambda data: data["scaleType"],
    ),
    NetzOOEeServiceSensorEntityDescription(
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
    NetzOOEeServiceSensorEntityDescription(
        key="supplier",
        translation_key="supplier",
        value_fn=lambda data: data["supplier"]["name"],
    ),
    *_trend_descriptions("monthly"),
    *_trend_descriptions("yearly"),
]

SENSOR_ENERGY_COMMUNITY_DEFAULT_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = [
    NetzOOEeServiceSensorEntityDescription(
        entity_class=NetzOOEeServiceEnergyCommunitySensorEntity,
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key="status",
        options=STATUS_OPTIONS,
        translation_key="status",
        value_fn=_status,
    ),
    NetzOOEeServiceSensorEntityDescription(
        entity_class=NetzOOEeServiceEnergyCommunitySensorEntity,
        entity_category=EntityCategory.DIAGNOSTIC,
        key="contribution_factor",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="contribution_factor",
        value_fn=lambda data: data["contributionPercentage"],
    ),
]

SENSOR_ENERGY_COMMUNITY_IMPORT_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = (
    _energy_community_descriptions(
        "import",
        energy_community=(ENERGY_COMMUNITY_OWN_COVERAGE, None),
        supplier=(ENERGY_COMMUNITY_CONSUMPTION, ENERGY_COMMUNITY_OWN_COVERAGE),
    )
)

SENSOR_ENERGY_COMMUNITY_EXPORT_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = (
    _energy_community_descriptions(
        "export",
        energy_community=(ENERGY_COMMUNITY_GENERATION, ENERGY_COMMUNITY_OVER_COVERAGE),
        supplier=(ENERGY_COMMUNITY_OVER_COVERAGE, None),
    )
)

SENSOR_HOUSEHOLD_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = [
    *_aggregated_descriptions(SENSOR_ENERGY_COMMUNITY_IMPORT_TYPES),
    _peak_power_description("import"),
]

SENSOR_PHOTOVOLTAICS_TYPES: Final[list[NetzOOEeServiceSensorEntityDescription]] = [
    *_aggregated_descriptions(SENSOR_ENERGY_COMMUNITY_EXPORT_TYPES),
    _peak_power_description("export"),
]

SENSOR_TYPES: Final[dict[str, list[NetzOOEeServiceSensorEntityDescription]]] = {
    DeviceType.HOUSEHOLD.value: SENSOR_DEFAULT_TYPES + SENSOR_HOUSEHOLD_TYPES,
    DeviceType.PHOTOVOLTAICS.value: SENSOR_DEFAULT_TYPES + SENSOR_PHOTOVOLTAICS_TYPES,
    DeviceType.ENERGY_COMMUNITY_IMPORT.value: SENSOR_ENERGY_COMMUNITY_DEFAULT_TYPES
    + SENSOR_ENERGY_COMMUNITY_IMPORT_TYPES,
    DeviceType.ENERGY_COMMUNITY_EXPORT.value: SENSOR_ENERGY_COMMUNITY_DEFAULT_TYPES
    + SENSOR_ENERGY_COMMUNITY_EXPORT_TYPES,
}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: NetzOOEeServiceConfigEntry,
    async_add_entities: AddEntitiesCallback,
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
                entry=entry,
                device_identifier=device_identifier,
            )
            for device_identifier, data in coordinator.data.items()
            if device_identifier in new_device_identifiers
            for description in SENSOR_TYPES[data["deviceType"]]
        )

    async_add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(async_add_new_devices))
