"""Defines the type of states that can be found in the  features provided by a Homely device."""
import datetime
from dataclasses import dataclass
from typing import Any, Optional

from dateutil.parser import parse


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
            *extract_value_and_last_updated(my_data["low"]),
            *extract_value_and_last_updated(my_data["voltage"]),
            *extract_value_and_last_updated(my_data["defect"]) if "defect" in my_data else (None, None),
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
class MeteringState(State):
    @classmethod
    def create_from_rest_response(cls, data: dict) -> "MeteringState":
        my_data = data["features"]["metering"]["states"]
        return MeteringState(
            "metering",
            *extract_value_and_last_updated(my_data["summationdelivered"]),
            *extract_value_and_last_updated(my_data["summationreceived"]),
            *extract_value_and_last_updated(my_data["demand"]),
            *extract_value_and_last_updated(my_data["check"]),
        )

    summation_delivered: float
    summation_delivered_last_updated: datetime.datetime
    summation_received: float
    summation_received_last_update: datetime.datetime
    demand: float
    demand_last_updated: datetime.datetime
    check: bool
    check_last_updated: datetime.datetime


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
