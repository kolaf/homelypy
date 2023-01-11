import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from states import (
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
    ARMED_PARTLY = "ARMED_PARTLY"
    BREACHED = "BREACHED"
    ALARM_PENDING = "ALARM_PENDING"
    ALARM_STAY_PENDING = "ALARM_STAY_PENDING"
    ARMED_NIGHT_PENDING = "ARMED_NIGHT_PENDING"
    ARMED_AWAY_PENDING = "ARMED_AWAY_PENDING"


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
        return self.name

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
    "Smoke Alarm": SmokeAlarm,
    "Window Sensor": WindowSensor,
    "EMI Norwegian HAN": EMIHANPowersSensor,
}


def create_device_from_rest_response(data: dict) -> Optional[Device]:
    device_class = DEVICE_MAP.get(data.get("modelName"))
    if device_class is None:
        return
    return device_class.create_from_rest_response(data)


@dataclass
class SingleLocation:
    location_id: str
    gateway_serial: str
    name: str
    alarm_state: AlarmStates
    user_role_at_location: str
    devices: list[Device]

    def __str__(self):
        return f"{self.name} with {len(self.devices)} devices"
