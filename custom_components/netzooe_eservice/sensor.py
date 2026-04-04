"""Support for the Netz OÖ eService sensors."""

import logging
from collections.abc import Callable
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from typing import Final

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from netzooe_eservice_api.constants import SynthProfile

from .const import DOMAIN
from .coordinator import NetzOOEeServiceConfigEntry
from .coordinator import NetzOOEeServiceDataUpdateCoordinator
from .entity import NetzOOEeServiceEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES: Final[int] = 0


@dataclass(frozen=True, kw_only=True)
class NetzOOEeServiceSensorEntityDescription[T](
    SensorEntityDescription,
):
    """Class describing NetzOOEeService sensor entities."""

    entity_class: type["NetzOOEeServiceSensorEntity"]
    value_fn: Callable[[Mapping[str, Any]], StateType]
    extra_state_attributes_fn: Callable[[Mapping[str, Any]], Mapping[str, Any] | None]
    alt_key: str | None = None


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

        self._attr_unique_id = (
            f"{self.device_identifier}_{self.entity_description.alt_key or self.entity_description.key}"
        )

        self.entity_id: str = f"{SENSOR_DOMAIN}.{DOMAIN}_{self._attr_unique_id}"

    @property
    def data(self) -> Mapping[str, Any]:
        """Return sensor data from the coordinator."""
        data: Mapping[str, Any] = self.coordinator.data[self.device_identifier]
        return data

    @property
    def device_name(self) -> str | None:
        """Return the name of the current device."""
        return f"{self.coordinator.data[self.device_identifier]['synth_profile']} - {self.device_identifier.upper()}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return self.entity_description.extra_state_attributes_fn(self.data)


SENSOR_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        key="scale_type",
        translation_key="scale_type",
        value_fn=lambda data: data["scale_type"],
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="meter_reading",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="meter_reading",
        value_fn=(
            lambda data: data["meter_reading"]["values"]["new_result"]["integer_places"]
            + data["meter_reading"]["values"]["new_result"]["decimal_places"]
        ),
        extra_state_attributes_fn=lambda data: {
            "timestamp": data["meter_reading"]["values"]["new_result"]["timestamp"],
            "meter_number": data["meter_reading"]["meter_number"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        key="supplier",
        translation_key="supplier",
        value_fn=lambda data: data["supplier"]["name"],
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        key="synth_profile",
        translation_key="synth_profile",
        value_fn=lambda data: data["synth_profile"],
        extra_state_attributes_fn=lambda data: {},  # noqa: ARG005
    ),
    NetzOOEeServiceSensorEntityDescription[str](
        entity_class=NetzOOEeServiceSensorEntity,
        key="energy_community",
        translation_key="energy_community",
        value_fn=lambda data: data["energy_community"][-1]["energy_community_name"],
        extra_state_attributes_fn=lambda data: {
            "history": [
                {
                    "name": item["energy_community_name"],
                    "id": item["energy_community_id"],
                    "from": item["from"],
                    "to": item["to"],
                }
                for item in data["energy_community"]
            ],
        },
    ),
]


SENSOR_EXPORT_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_trend_export_new",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_export_new",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["monthly_trend"]["consumption_new"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthly_trend"]["consumption_new"]["per_day"],
            "days": data["monthly_trend"]["consumption_new"]["days"],
            "from": data["monthly_trend"]["timerange_new"]["from"],
            "to": data["monthly_trend"]["timerange_new"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_trend_export_old",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_export_old",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["monthly_trend"]["consumption_old"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthly_trend"]["consumption_old"]["per_day"],
            "days": data["monthly_trend"]["consumption_old"]["days"],
            "from": data["monthly_trend"]["timerange_old"]["from"],
            "to": data["monthly_trend"]["timerange_old"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="yearly_trend_export_new",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_export_new",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["yearly_trend"]["consumption_new"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearly_trend"]["consumption_new"]["per_day"],
            "days": data["yearly_trend"]["consumption_new"]["days"],
            "from": data["yearly_trend"]["timerange_new"]["from"],
            "to": data["yearly_trend"]["timerange_new"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="yearly_trend_export_old",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_export_old",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["yearly_trend"]["consumption_old"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearly_trend"]["consumption_old"]["per_day"],
            "days": data["yearly_trend"]["consumption_old"]["days"],
            "from": data["yearly_trend"]["timerange_old"]["from"],
            "to": data["yearly_trend"]["timerange_old"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_export_eeg_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_export_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l2"][0]["sum"]["value"]
            - data["total_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "from": data["total_consumptions_profile_eeg_l2"][0]["from"],
            "to": data["total_consumptions_profile_eeg_l2"][0]["to"],
            "granularity": data["total_consumptions_profile_eeg_l2"][0]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_export_supplier_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_export_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "name": data["total_consumptions_profile_eeg_l2"][1]["energy_community_name"],
            "id": data["total_consumptions_profile_eeg_l2"][1]["energy_community_id"],
            "from": data["total_consumptions_profile_eeg_l2"][1]["from"],
            "to": data["total_consumptions_profile_eeg_l2"][1]["to"],
            "granularity": data["total_consumptions_profile_eeg_l2"][1]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_export_eeg_l3",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_eeg_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l3"][0]["sum"]["value"]
            - data["total_consumptions_profile_eeg_l3"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l3", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "from": data["total_consumptions_profile_eeg_l3"][0]["from"],
            "to": data["total_consumptions_profile_eeg_l3"][0]["to"],
            "granularity": data["total_consumptions_profile_eeg_l3"][0]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_export_supplier_l3",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_export_supplier_l3",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l3"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l3", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "name": data["total_consumptions_profile_eeg_l3"][1]["energy_community_name"],
            "id": data["total_consumptions_profile_eeg_l3"][1]["energy_community_id"],
            "from": data["total_consumptions_profile_eeg_l3"][1]["from"],
            "to": data["total_consumptions_profile_eeg_l3"][1]["to"],
            "granularity": data["total_consumptions_profile_eeg_l3"][1]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_export_eeg_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="monthly_export_eeg_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: (
            data["monthly_consumptions_profile_eeg_l2"][0]["sum"]["value"]
            - data["monthly_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "from": data["monthly_consumptions_profile_eeg_l2"][0]["from"],
            "to": data["monthly_consumptions_profile_eeg_l2"][0]["to"],
            "granularity": data["monthly_consumptions_profile_eeg_l2"][0]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_export_supplier_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="monthly_export_supplier_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: (
            data["monthly_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "name": data["monthly_consumptions_profile_eeg_l2"][1]["energy_community_name"],
            "id": data["monthly_consumptions_profile_eeg_l2"][1]["energy_community_id"],
            "from": data["monthly_consumptions_profile_eeg_l2"][1]["from"],
            "to": data["monthly_consumptions_profile_eeg_l2"][1]["to"],
            "granularity": data["monthly_consumptions_profile_eeg_l2"][1]["granularity"],
        },
    ),
]

SENSOR_IMPORT_TYPES: list[NetzOOEeServiceSensorEntityDescription[Any]] = [
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_trend_import_new",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_import_new",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["monthly_trend"]["consumption_new"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthly_trend"]["consumption_new"]["per_day"],
            "days": data["monthly_trend"]["consumption_new"]["days"],
            "from": data["monthly_trend"]["timerange_new"]["from"],
            "to": data["monthly_trend"]["timerange_new"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_trend_import_old",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_trend_import_old",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["monthly_trend"]["consumption_old"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["monthly_trend"]["consumption_old"]["per_day"],
            "days": data["monthly_trend"]["consumption_old"]["days"],
            "from": data["monthly_trend"]["timerange_old"]["from"],
            "to": data["monthly_trend"]["timerange_old"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="yearly_trend_import_new",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_import_new",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["yearly_trend"]["consumption_new"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearly_trend"]["consumption_new"]["per_day"],
            "days": data["yearly_trend"]["consumption_new"]["days"],
            "from": data["yearly_trend"]["timerange_new"]["from"],
            "to": data["yearly_trend"]["timerange_new"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="yearly_trend_import_old",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="yearly_trend",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="yearly_trend_import_old",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["yearly_trend"]["consumption_old"]["sum"],
        extra_state_attributes_fn=lambda data: {
            "per_day": data["yearly_trend"]["consumption_old"]["per_day"],
            "days": data["yearly_trend"]["consumption_old"]["days"],
            "from": data["yearly_trend"]["timerange_old"]["from"],
            "to": data["yearly_trend"]["timerange_old"]["to"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_import_eeg_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_import_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "name": data["total_consumptions_profile_eeg_l2"][1]["energy_community_name"],
            "id": data["total_consumptions_profile_eeg_l2"][1]["energy_community_id"],
            "from": data["total_consumptions_profile_eeg_l2"][1]["from"],
            "to": data["total_consumptions_profile_eeg_l2"][1]["to"],
            "granularity": data["total_consumptions_profile_eeg_l2"][1]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_import_supplier_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_import_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l2"][0]["sum"]["value"]
            - data["total_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "from": data["total_consumptions_profile_eeg_l2"][0]["from"],
            "to": data["total_consumptions_profile_eeg_l2"][0]["to"],
            "granularity": data["total_consumptions_profile_eeg_l2"][0]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_import_eeg_l3",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_eeg_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l3"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l3", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "name": data["total_consumptions_profile_eeg_l3"][1]["energy_community_name"],
            "id": data["total_consumptions_profile_eeg_l3"][1]["energy_community_id"],
            "from": data["total_consumptions_profile_eeg_l3"][1]["from"],
            "to": data["total_consumptions_profile_eeg_l3"][1]["to"],
            "granularity": data["total_consumptions_profile_eeg_l3"][1]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="total_import_supplier_l3",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="total_consumptions_profile_eeg_l3",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        translation_key="total_import_supplier_l3",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: (
            data["total_consumptions_profile_eeg_l3"][0]["sum"]["value"]
            - data["total_consumptions_profile_eeg_l3"][1]["sum"]["value"]
            if len(data.get("total_consumptions_profile_eeg_l3", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "from": data["total_consumptions_profile_eeg_l3"][0]["from"],
            "to": data["total_consumptions_profile_eeg_l3"][0]["to"],
            "granularity": data["total_consumptions_profile_eeg_l3"][0]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_import_eeg_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="monthly_import_eeg_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: (
            data["monthly_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("monthly_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "name": data["monthly_consumptions_profile_eeg_l2"][1]["energy_community_name"],
            "id": data["monthly_consumptions_profile_eeg_l2"][1]["energy_community_id"],
            "from": data["monthly_consumptions_profile_eeg_l2"][1]["from"],
            "to": data["monthly_consumptions_profile_eeg_l2"][1]["to"],
            "granularity": data["monthly_consumptions_profile_eeg_l2"][1]["granularity"],
        },
    ),
    NetzOOEeServiceSensorEntityDescription[float](
        alt_key="monthly_import_supplier_l2",
        entity_class=NetzOOEeServiceSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="monthly_consumptions_profile_eeg_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="monthly_import_supplier_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: (
            data["monthly_consumptions_profile_eeg_l2"][0]["sum"]["value"]
            - data["monthly_consumptions_profile_eeg_l2"][1]["sum"]["value"]
            if len(data.get("monthly_consumptions_profile_eeg_l2", [])) == 2  # noqa: PLR2004
            else None
        ),
        extra_state_attributes_fn=lambda data: {
            "from": data["monthly_consumptions_profile_eeg_l2"][0]["from"],
            "to": data["monthly_consumptions_profile_eeg_l2"][0]["to"],
            "granularity": data["monthly_consumptions_profile_eeg_l2"][0]["granularity"],
        },
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

    for meter_point_administration_number, data in coordinator.data.items():
        for description in SENSOR_TYPES:
            sensors += [
                description.entity_class(
                    coordinator,
                    description=description,
                    entry=entry,
                    device_identifier=meter_point_administration_number,
                ),
            ]

        profile_sensor_types: list[NetzOOEeServiceSensorEntityDescription[Any]]

        if data["synth_profile"] == SynthProfile.PHOTOVOLTAICS.value:
            profile_sensor_types = SENSOR_EXPORT_TYPES
        elif data["synth_profile"] == SynthProfile.HOUSEHOLD.value:
            profile_sensor_types = SENSOR_IMPORT_TYPES
        else:
            continue

        for description in profile_sensor_types:
            value: StateType = description.value_fn(data)

            if value is not None:
                sensors += [
                    description.entity_class(
                        coordinator,
                        description=description,
                        entry=entry,
                        device_identifier=meter_point_administration_number,
                    ),
                ]

    async_add_entities(sensors)
