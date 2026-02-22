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
        return f"{self.coordinator.data[self.device_identifier]["synth_profile"]} - {self.device_identifier.upper()}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.data)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return self.entity_description.extra_state_attributes_fn(self.data)


class NetzOOEeMultipleSensorEntity(NetzOOEeServiceSensorEntity, SensorEntity):
    """Netz OÖ eService sensor entity."""

    def __init__(
        self,
        coordinator: NetzOOEeServiceDataUpdateCoordinator,
        description: NetzOOEeServiceSensorEntityDescription[StateType],
        entry: NetzOOEeServiceConfigEntry,
        device_identifier: str,
        index: int,
    ) -> None:
        """Initialize the entity."""
        self.index: int = index

        self.entity_description: NetzOOEeServiceSensorEntityDescription[StateType] = description

        super().__init__(
            coordinator,
            description=description,
            entry=entry,
            device_identifier=device_identifier,
        )

        self._attr_translation_placeholders = {
            "position": str(index + 1),
        }

        self._attr_unique_id = f"{self._attr_unique_id}_{index + 1}"
        self.entity_id: str = f"{SENSOR_DOMAIN}.{DOMAIN}_{self._attr_unique_id}"

    @property
    def data(self) -> Mapping[str, Any]:
        """Return sensor data from the coordinator."""
        data: Mapping[str, Any] = self.coordinator.data[self.device_identifier][self.entity_description.key][self.index]
        return data


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
    NetzOOEeServiceSensorEntityDescription[str](
        alt_key="total_eeg_export_l2",
        entity_class=NetzOOEeMultipleSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="consumptions_profile_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_eeg_export_l2",
        icon="mdi:transmission-tower-import",
        value_fn=lambda data: data["sum"]["value"],
        extra_state_attributes_fn=lambda data: {
            "name": data["energy_community_name"],
            "id": data["energy_community_id"],
            "average": data["average"]["value"],
            "from": data["from"],
            "to": data["to"],
            "type": data["type"],
            "granularity": data["granularity"],
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
    NetzOOEeServiceSensorEntityDescription[str](
        alt_key="total_eeg_import_l2",
        entity_class=NetzOOEeMultipleSensorEntity,
        device_class=SensorDeviceClass.ENERGY,
        key="consumptions_profile_l2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_eeg_import_l2",
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data["sum"]["value"],
        extra_state_attributes_fn=lambda data: {
            "name": data["energy_community_name"],
            "id": data["energy_community_id"],
            "average": data["average"]["value"],
            "from": data["from"],
            "to": data["to"],
            "type": data["type"],
            "granularity": data["granularity"],
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
            raw_data = data[description.key]
            data_list: list[Mapping[str, Any]] = raw_data if isinstance(raw_data, list) else [raw_data]

            for index, _ in enumerate(data_list):
                sensors.append(
                    description.entity_class(
                        coordinator,
                        description=description,
                        entry=entry,
                        device_identifier=meter_point_administration_number,
                        **({"index": index} if len(data_list) > 1 else {}),
                    ),
                )

    async_add_entities(sensors)
