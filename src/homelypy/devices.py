import dataclasses
import datetime
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
from dateutil.parser import parse


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
class State:
    feature_name: str

    @classmethod
    def create_from_rest_response(cls, data: dict) -> "State":
        raise NotImplementedError


def extract_value_and_last_updated(data: dict) -> tuple[Any, datetime.datetime]:
    timestamp = parse(data["lastUpdated"]) if data["lastUpdated"] is not None else None
    return data["value"], timestamp


@dataclass
class BasicAlarmState(State):
    @classmethod
    def create_from_rest_response(cls, data: dict) -> "BasicAlarmState":
        my_data = data["features"]["alarm"]["states"]
        return BasicAlarmState(
            "alarm",
            *extract_value_and_last_updated(my_data["alarm"]),
            *extract_value_and_last_updated(my_data["tamper"]),
        )

    alarm: bool
    alarm_last_updated: datetime.datetime
    tamper: bool
    tamper_last_updated: datetime.datetime


@dataclass
class SmokeAlarmState(State):
    @classmethod
    def create_from_rest_response(cls, data: dict) -> "SmokeAlarmState":
        my_data = data["features"]["alarm"]["states"]
        return SmokeAlarmState(
            "alarm",
            *extract_value_and_last_updated(my_data["fire"]),
        )

    fire: bool
    fire_last_updated: datetime.datetime


@dataclass
class MotionSensorState(BasicAlarmState):
    sensitivity_level: Optional[float]
    sensitivity_level_last_updated: Optional[datetime.datetime]

    @classmethod
    def create_from_rest_response(cls, data: dict) -> "MotionSensorState":
        my_data = data["features"]["alarm"]["states"]
        return MotionSensorState(
            "alarm",
            *extract_value_and_last_updated(my_data["alarm"]),
            *extract_value_and_last_updated(my_data["tamper"]),
            *extract_value_and_last_updated(my_data["sensitivitylevel"]),
        )


@dataclass
class BatteryState(State):
    @classmethod
    def create_from_rest_response(cls, data: dict) -> "BatteryState":
        my_data = data["features"]["battery"]["states"]
        return BatteryState(
            "battery",
            *extract_value_and_last_updated(my_data["defect"]) if "defect" in my_data else (None, None),
            *extract_value_and_last_updated(my_data["low"]),
            *extract_value_and_last_updated(my_data["voltage"]),
        )

    low: bool
    low_last_updated: datetime.datetime
    voltage: float
    voltage_last_updated: datetime.datetime
    defect: Optional[Any]
    defect_last_updated: datetime.datetime


@dataclass
class TemperatureState(State):
    @classmethod
    def create_from_rest_response(cls, data: dict) -> "TemperatureState":
        my_data = data["features"]["temperature"]["states"]
        return TemperatureState(
            "temperature",
            *extract_value_and_last_updated(my_data["temperature"]),
        )

    temperature: float
    temperature_last_updated: datetime.datetime


@dataclass
class DiagnosticState(State):
    @classmethod
    def create_from_rest_response(cls, data: dict) -> "DiagnosticState":
        my_data = data["features"]["diagnostic"]["states"]
        return DiagnosticState(
            "diagnostic",
            *extract_value_and_last_updated(my_data["networklinkaddress"]),
            *extract_value_and_last_updated(my_data["networklinkstrength"]),
        )

    network_link_address: str
    network_link_address_last_updated: datetime.datetime
    network_link_strength: float
    network_link_strength_last_updated: datetime.datetime


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


DEVICE_MAP = {"Motion Sensor Mini": MotionSensorMini, "Smoke Alarm": SmokeAlarm, "Window Sensor": WindowSensor}


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
