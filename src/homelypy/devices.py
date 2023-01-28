import dataclasses
import datetime
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple

from dateutil.parser import parse

logger = logging.getLogger(__name__)

from homelypy.states import (
    State,
    BatteryState,
    DiagnosticState,
    TemperatureState,
    BasicAlarmState,
    SmokeAlarmState,
    MotionSensorState,
    MeteringState,
)


class AlarmStates(Enum):
    DISARMED = "DISARMED"
    ARMED_AWAY = "ARMED_AWAY"
    ARMED_NIGHT = "ARMED_NIGHT"
    ARMED_STAY = "ARMED_STAY"
    BREACHED = "BREACHED"
    ALARM_PENDING = "ALARM_PENDING"
    ARM_STAY_PENDING = "ARM_STAY_PENDING"
    ARM_NIGHT_PENDING = "ARM_NIGHT_PENDING"
    ARM_PENDING = "ARM_PENDING"


@dataclass
class Location:
    name: str
    role: str
    user_id: str
    location_id: str
    gateway_serial: str

    def __str__(self):
        return self.name


@dataclass
class Device:
    id: str
    name: str
    serial_number: str
    location: str
    online: bool
    model_id: str
    model_name: str

    def __str__(self):
        return f"{self.name} in {self.location}"

    def update_state(self, changes: List[dict]):
        """Updates the various features of the device based on the list of changes"""
        # Expects the contents of the ["data"]["changes"] key.
        # {
        #     "type": "device-state-changed",
        #     "data": {
        #         "deviceId": "ad5d19b5-3988-4ad2-96c0-08f6283e073a",
        #         "gatewayId": "3b0187f4-878e-4b51-af2b-fc563b81f137",
        #         "locationId": "48617520-863c-4e27-9a05-4ce3cce50f8e",
        #         "modelId": "87fa1ae0-824f-4d42-be7a-cc5b6c7b1e35",
        #         "rootLocationId": "d14a27d8-311c-41d8-b8c1-08b757c2253f",
        #         "changes": [
        #             {
        #                 "feature": "temperature",
        #                 "stateName": "temperature",
        #                 "value": 4.8,
        #                 "lastUpdated": "2023-01-25T10:27:07.786Z",
        #             }
        #         ],
        #     },
        # }
        updated_states = []
        for change in changes:
            try:
                state = getattr(self, change["feature"])
                setattr(state, change["stateName"], change["value"])
                setattr(state, f"{change['stateName']}_last_updated", parse(change["lastUpdated"]))
                updated_states.append(state)
            except AttributeError:
                logger.exception(f"Device '{self}' does not have the feature {change['feature']}")
        return updated_states

    @classmethod
    def create_from_rest_response(cls, device: dict) -> "Device":
        state_fields = {}
        for field in dataclasses.fields(cls):
            if issubclass(field.type, State):
                state_fields[field.name] = field.type.create_from_rest_response(device)
        return cls(
            device["id"],
            device["name"],
            device["serialNumber"],
            device["location"],
            device["online"],
            device["modelId"],
            device["modelName"],
            **state_fields,
        )

    def get_entities(self) -> list[State]:
        return [getattr(self, field.name) for field in dataclasses.fields(self) if issubclass(field.type, State)]


@dataclass
class WindowSensor(Device):
    battery: BatteryState
    diagnostic: DiagnosticState
    temperature: TemperatureState
    alarm: BasicAlarmState


@dataclass
class SmokeAlarm(Device):
    battery: BatteryState
    diagnostic: DiagnosticState
    temperature: TemperatureState
    alarm: SmokeAlarmState


@dataclass
class HeatAlarm(Device):
    battery: BatteryState
    diagnostic: DiagnosticState
    temperature: TemperatureState
    alarm: SmokeAlarmState


@dataclass
class MotionSensorMini(Device):
    battery: BatteryState
    diagnostic: DiagnosticState
    temperature: TemperatureState
    alarm: MotionSensorState


@dataclass
class EMIHANPowersSensor(Device):
    diagnostic: DiagnosticState
    metering: MeteringState


DEVICE_MAP = {
    "Motion Sensor Mini": MotionSensorMini,
    "Motion Sensor 2 Alarm": MotionSensorMini,
    "Smoke Alarm": SmokeAlarm,
    "Intelligent Smoke Alarm": SmokeAlarm,
    "Heat Alarm": HeatAlarm,
    "Window Sensor": WindowSensor,
    "Window Alarm Sensor": WindowSensor,
    "EMI Norwegian HAN": EMIHANPowersSensor,
}


class UnknownDeviceException(Exception):
    pass


def create_device_from_rest_response(data: dict) -> Optional[Device]:
    device_class = DEVICE_MAP.get(data.get("modelName"))
    if device_class is None:
        raise UnknownDeviceException(f"Unknown device: '{data.get('modelName')}'")
    return device_class.create_from_rest_response(data)


@dataclass
class SingleLocation:
    location_id: str
    gateway_serial: str
    name: str
    alarm_state: AlarmStates
    alarm_state_last_updated: datetime.datetime
    user_role_at_location: str
    devices: list[Device]

    def __str__(self):
        return f"{self.name} with {len(self.devices)} devices"

    def find_device(self, device_id) -> Optional[Device]:
        return next(filter(lambda d: d.id == device_id, self.devices), None)

    def update_device_state_from_stream(self, data: dict) -> Optional[Tuple[Device, List[State]]]:
        """
        Updates the device state based on the data package received from the Homely websocket stream. Returns the
        updated device.
        """
        # Expects the contents of the "data" key.
        # {
        #     "type": "device-state-changed",
        #     "data": {
        #         "deviceId": "ad5d19b5-3988-4ad2-96c0-08f6283e073a",
        #         "gatewayId": "3b0187f4-878e-4b51-af2b-fc563b81f137",
        #         "locationId": "48617520-863c-4e27-9a05-4ce3cce50f8e",
        #         "modelId": "87fa1ae0-824f-4d42-be7a-cc5b6c7b1e35",
        #         "rootLocationId": "d14a27d8-311c-41d8-b8c1-08b757c2253f",
        #         "changes": [
        #             {
        #                 "feature": "temperature",
        #                 "stateName": "temperature",
        #                 "value": 4.8,
        #                 "lastUpdated": "2023-01-25T10:27:07.786Z",
        #             }
        #         ],
        #     },
        # }
        device = self.find_device(data["deviceId"])
        if device:
            states = device.update_state(data["changes"])
            return device, states
        else:
            logger.warning(f"Did not find a device matching data update: {data}")
            return None
