"""Support for the Netz OÖ eService sensors."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from typing import Final
from typing import TYPE_CHECKING

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.const import PERCENTAGE
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .const import DeviceType
from .const import MANUFACTURER
from .const import NAME
from .entity import NetzOOEeServiceEntity

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType
    from .coordinator import NetzOOEeServiceConfigEntry
    from .coordinator import NetzOOEeServiceDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES: Final[int] = 0


@dataclass(frozen=True, kw_only=True)
class NetzOOEeServiceSensorEntityDescription[T](
    SensorEntityDescription,
):
    """Class describing NetzOOEeService sensor entities."""

    entity_class: type[NetzOOEeServiceSensorEntity]
    value_fn: Callable[..., StateType]
    extra_state_attributes_fn: Callable[[Mapping[str, Any]], Mapping[str, Any] | None]


class NetzOOEeServiceSensorEntity(NetzOOEeServiceEntity, SensorEntity):
    """Netz OÖ eService sensor entity."""

    def __init__(
        self,
        coordinator: NetzOOEeServiceDataUpdateCoordinator,
        description: NetzOOEeServiceSensorEntityDescription[StateType],
        entry: NetzOOEeServiceConfigEntry,
        device_identifier: str,
    ) -> None:
        """Initialize the entity."""
        self.entity_description: NetzOOEeServiceSensorEntityDescription[StateType] = description

        super().__init__(
            coordinator,
            entry=entry,
            device_identifier=device_identifier,
        )

        self._attr_unique_id = f"{self.device_identifier}_{self.entity_description.key}".lower()

        self.entity_id: str = f"{SENSOR_DOMAIN}.{DOMAIN}_{self._attr_unique_id}"

    @property
    def data(self) -> Mapping[str, Any]:
        """Return sensor data from the coordinator."""
        data: Mapping[str, Any] = self.coordinator.data[self.device_identifier]
        return data

    @property
    def device_name(self) -> str | None:
        """Return the name of the current device."""
        return f"{self.data['deviceName']} ({self._short_device_id(self.device_identifier)})"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return self.entity_description.extra_state_attributes_fn(self.data)


class NetzOOEeServiceEEGSensorEntity(NetzOOEeServiceSensorEntity):
    """Netz OÖ eService EEG sensor entity."""

    @property
    def device_name(self) -> str | None:
        """Return the name of the current device."""
        return (
            f"{self.data['synthProfile']}: {self.data['deviceName']} "
            f"({self._short_device_id(self.data['meterPointAdministrationNumber'])})"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return updated device specific attributes."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_identifier)},
            name=self.device_name,
            model=NAME,
            manufacturer=MANUFACTURER,
            via_device=(DOMAIN, self.data["meterPointAdministrationNumber"]),
        )


class NetzOOEeServiceAggregatedSensorEntity(NetzOOEeServiceSensorEntity):
    """Aggregated sensor entity."""

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator, self.device_identifier)


def _sum_by_type(
    items: list[dict[str, Any]],
    target_type: str,
) -> float:
    total: float = sum(item["sum"]["value"] for item in items if item["type"] == target_type)
    return total


def _sum_difference_by_type(
    items: list[dict[str, Any]],
    positive_type: str,
    negative_type: str,
) -> float:
    positive: float = sum(item["sum"]["value"] for item in items if item["type"] == positive_type)
    negative: float = sum(item["sum"]["value"] for item in items if item["type"] == negative_type)

    return positive - negative


def _sum_values_for_mpan(
    coordinator: NetzOOEeServiceDataUpdateCoordinator,
    device_identifier: str,
    key: str,
    positive_type: str,
    negative_type: str | None = None,
    status: str | None = None,
) -> float:
    total: float = 0.0

    for current_device_identifier, data in coordinator.data.items():
        if not current_device_identifier.startswith(f"{device_identifier}_"):
            continue

        if status is not None and data["status"].lower() != status.lower():
            continue

        items: list[dict[str, Any]] = data.get(key, [])

        if negative_type:
            total += _sum_difference_by_type(
                items,
                positive_type,
                negative_type,
            )
        else:
            total += _sum_by_type(
                items,
                positive_type,
            )

    return total


def _timeline_by_type(
    items: list[dict[str, Any]],
    target_type: str,
) -> list[dict[str, str]]:
    return [
        {
            "from": item["from"],
            "to": item["to"],
        }
        for item in items
        if item["type"] == target_type
    ]


SENSOR_DEFAULT_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        key="scale_type",
        translation_key="scale_type",
        value_fn=lambda data: data["scaleType"],
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="meter_reading",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="meter_reading",
        value_fn=(lambda data: data["meterReading"]["values"]["newResult"]["readingValue"]),
        extra_state_attributes_fn=lambda data: {
            "timestamp": data["meterReading"]["values"]["newResult"]["timestamp"],
            "meter_number": data["meterReading"]["meterNumber"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        key="supplier",
        translation_key="supplier",
        value_fn=lambda data: data["supplier"]["name"],
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
]

SENSOR_HOUSEHOLD_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend_import_new",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_import_new",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["monthlyTrend"]["consumptionNew"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthlyTrend"]["consumptionNew"]["perDay"],
            "days": data["monthlyTrend"]["consumptionNew"]["days"],
            "from": data["monthlyTrend"]["timerangeNew"]["from"],
            "to": data["monthlyTrend"]["timerangeNew"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend_import_old",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_import_old",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["monthlyTrend"]["consumptionOld"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthlyTrend"]["consumptionOld"]["perDay"],
            "days": data["monthlyTrend"]["consumptionOld"]["days"],
            "from": data["monthlyTrend"]["timerangeOld"]["from"],
            "to": data["monthlyTrend"]["timerangeOld"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend_import_new",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_import_new",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["yearlyTrend"]["consumptionNew"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearlyTrend"]["consumptionNew"]["perDay"],
            "days": data["yearlyTrend"]["consumptionNew"]["days"],
            "from": data["yearlyTrend"]["timerangeNew"]["from"],
            "to": data["yearlyTrend"]["timerangeNew"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend_import_old",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_import_old",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["yearlyTrend"]["consumptionOld"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearlyTrend"]["consumptionOld"]["perDay"],
            "days": data["yearlyTrend"]["consumptionOld"]["days"],
            "from": data["yearlyTrend"]["timerangeOld"]["from"],
            "to": data["yearlyTrend"]["timerangeOld"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_eeg_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_supplier_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_supplier_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_import_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_import_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_import_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_import_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_active_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_active_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_active_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_active_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_active_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_active_eeg_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_active_supplier_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_active_supplier_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_import_active_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_import_active_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_import_active_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_import_active_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
]

SENSOR_PHOTOVOLTAICS_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend_export_new",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_export_new",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["monthlyTrend"]["consumptionNew"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthlyTrend"]["consumptionNew"]["perDay"],
            "days": data["monthlyTrend"]["consumptionNew"]["days"],
            "from": data["monthlyTrend"]["timerangeNew"]["from"],
            "to": data["monthlyTrend"]["timerangeNew"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend_export_old",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_export_old",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["monthlyTrend"]["consumptionOld"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthlyTrend"]["consumptionOld"]["perDay"],
            "days": data["monthlyTrend"]["consumptionOld"]["days"],
            "from": data["monthlyTrend"]["timerangeOld"]["from"],
            "to": data["monthlyTrend"]["timerangeOld"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend_export_new",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_export_new",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["yearlyTrend"]["consumptionNew"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearlyTrend"]["consumptionNew"]["perDay"],
            "days": data["yearlyTrend"]["consumptionNew"]["days"],
            "from": data["yearlyTrend"]["timerangeNew"]["from"],
            "to": data["yearlyTrend"]["timerangeNew"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend_export_old",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_export_old",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["yearlyTrend"]["consumptionOld"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearlyTrend"]["consumptionOld"]["perDay"],
            "days": data["yearlyTrend"]["consumptionOld"]["days"],
            "from": data["yearlyTrend"]["timerangeOld"]["from"],
            "to": data["yearlyTrend"]["timerangeOld"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_eeg_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_supplier_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_supplier_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_export_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_export_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_export_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_export_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_active_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_active_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_active_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_active_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL2",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_active_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_active_eeg_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_active_supplier_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_active_supplier_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "totalEegL3",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_export_active_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_export_active_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceAggregatedSensorEntity,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_export_active_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_export_active_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda coordinator, device_identifier: _sum_values_for_mpan(
            coordinator,
            device_identifier,
            "monthlyEegL2",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
            status="active",
        ),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
]

SENSOR_EEG_DEFAULT_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        entity_category=EntityCategory.DIAGNOSTIC,
        key="status",
        translation_key="status",
        value_fn=lambda data: data["status"].lower(),
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[int](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        entity_category=EntityCategory.DIAGNOSTIC,
        key="contribution_factor",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="contribution_factor",
        value_fn=lambda data: data["contributionPercentage"],
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
]

SENSOR_EEG_IMPORT_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _sum_by_type(
            data["totalEegL2"],
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "name": data["totalEegL2"][0]["energyCommunityName"],
                "id": data["totalEegL2"][0]["energyCommunityId"],
                "timeline": _timeline_by_type(
                    data["totalEegL2"],
                    "ENERGY_COMMUNITY_OWN_COVERAGE",
                ),
            }
            if data["totalEegL2"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _sum_difference_by_type(
            data["totalEegL2"],
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "timeline": _timeline_by_type(
                    data["totalEegL2"],
                    "ENERGY_COMMUNITY_OWN_COVERAGE",
                ),
            }
            if data["totalEegL2"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_eeg_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _sum_by_type(
            data["totalEegL3"],
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "name": data["totalEegL3"][0]["energyCommunityName"],
                "id": data["totalEegL3"][0]["energyCommunityId"],
                "timeline": _timeline_by_type(
                    data["totalEegL3"],
                    "ENERGY_COMMUNITY_OWN_COVERAGE",
                ),
            }
            if data["totalEegL3"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_import_supplier_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_supplier_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _sum_difference_by_type(
            data["totalEegL3"],
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "timeline": _timeline_by_type(
                    data["totalEegL3"],
                    "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["totalEegL3"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_import_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_import_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _sum_by_type(
            data["monthlyEegL2"],
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "name": data["monthlyEegL2"][0]["energyCommunityName"],
                "id": data["monthlyEegL2"][0]["energyCommunityId"],
                "timeline": _timeline_by_type(
                    data["monthlyEegL2"],
                    "ENERGY_COMMUNITY_OWN_COVERAGE",
                ),
            }
            if data["monthlyEegL2"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_import_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_import_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: _sum_difference_by_type(
            data["monthlyEegL2"],
            "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OWN_COVERAGE",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "timeline": _timeline_by_type(
                    data["monthlyEegL2"],
                    "ENERGY_COMMUNITY_CONSUMPTION_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["monthlyEegL2"]
            else {}
        ),
    ),
]

SENSOR_EEG_EXPORT_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _sum_difference_by_type(
            data["totalEegL2"],
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "name": data["totalEegL2"][0]["energyCommunityName"],
                "id": data["totalEegL2"][0]["energyCommunityId"],
                "timeline": _timeline_by_type(
                    data["totalEegL2"],
                    "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["totalEegL2"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _sum_by_type(
            data["totalEegL2"],
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "timeline": _timeline_by_type(
                    data["totalEegL2"],
                    "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["totalEegL2"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_eeg_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _sum_difference_by_type(
            data["totalEegL3"],
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "name": data["totalEegL3"][0]["energyCommunityName"],
                "id": data["totalEegL3"][0]["energyCommunityId"],
                "timeline": _timeline_by_type(
                    data["totalEegL3"],
                    "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["totalEegL3"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_export_supplier_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_supplier_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _sum_by_type(
            data["totalEegL3"],
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "timeline": _timeline_by_type(
                    data["totalEegL3"],
                    "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["totalEegL3"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_export_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_export_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _sum_difference_by_type(
            data["monthlyEegL2"],
            "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "name": data["monthlyEegL2"][0]["energyCommunityName"],
                "id": data["monthlyEegL2"][0]["energyCommunityId"],
                "timeline": _timeline_by_type(
                    data["monthlyEegL2"],
                    "ENERGY_COMMUNITY_GENERATION_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["monthlyEegL2"]
            else {}
        ),
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        entity_class=NetzOOEeServiceEEGSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_export_supplier_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_export_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: _sum_by_type(
            data["monthlyEegL2"],
            "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
        ),
        extra_state_attributes_fn=lambda data: (
            {
                "timeline": _timeline_by_type(
                    data["monthlyEegL2"],
                    "ENERGY_COMMUNITY_OVER_COVERAGE_PER_CONTRIBUTION_FACTOR",
                ),
            }
            if data["monthlyEegL2"]
            else {}
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: NetzOOEeServiceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Netz OÖ eService from a config entry."""
    coordinator: NetzOOEeServiceDataUpdateCoordinator = entry.runtime_data
    sensors: list[NetzOOEeServiceSensorEntity] = []

    for device_identifier, data in coordinator.data.items():
        sensor_types: list[NetzOOEeServiceSensorEntityDescription[Any]] = []

        if data.get("deviceType") == DeviceType.HOUSEHOLD.value:
            sensor_types = SENSOR_DEFAULT_TYPES + SENSOR_HOUSEHOLD_TYPES
        elif data.get("deviceType") == DeviceType.PHOTOVOLTAICS.value:
            sensor_types = SENSOR_DEFAULT_TYPES + SENSOR_PHOTOVOLTAICS_TYPES
        elif data.get("deviceType") == DeviceType.EEG_IMPORT.value:
            sensor_types = SENSOR_EEG_DEFAULT_TYPES + SENSOR_EEG_IMPORT_TYPES
        elif data.get("deviceType") == DeviceType.EEG_EXPORT.value:
            sensor_types = SENSOR_EEG_DEFAULT_TYPES + SENSOR_EEG_EXPORT_TYPES

        for description in sensor_types:
            sensors += [
                description.entity_class(
                    coordinator,
                    description=description,
                    entry=entry,
                    device_identifier=device_identifier,
                ),
            ]

    async_add_entities(sensors)
