import logging
import time
from dataclasses import dataclass
from typing import Callable

import rel as rel
import requests as requests
import websocket

WEB_SOCKET_URL = "ws://sdk.iotiliti.cloud"

SDK_URL = "https://sdk.iotiliti.cloud"
AUTHENTICATION_ENDPOINT = "/homely/oauth/token"
LOCATIONS_ENDPOINT = "/homely/locations"
SINGLE_LOCATION_ENDPOINT = "/homely/home"
REFRESH_TOKEN_ENDPOINT = "/homely/oauth/refresh-token"

logger = logging.getLogger(__name__)


class ConnectionFailedException(Exception):
    pass


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
    features: list[dict]

    def __str__(self):
        return self.name


@dataclass
class SingleLocation:
    location_id: str
    gateway_serial: str
    name: str
    alarm_state: str
    user_role_at_location: str
    devices: list[Device]

    def __str__(self):
        return f"{self.name} with {len(self.devices)} devices"


class Homely:
    def __init__(self, username: str, password: str):
        self.refresh_expires_in = 0
        self.expires_in = 0
        self.authentication_time = 0
        self.access_token = None
        self.refresh_token = None
        self.username = username
        self.password = password

    @staticmethod
    def url(endpoint: str) -> str:
        return SDK_URL + endpoint

    def authenticate(self):
        response = requests.post(
            self.url(AUTHENTICATION_ENDPOINT),
            data={"username": self.username, "password": self.password},
        )
        if response.status_code != 201:
            raise ConnectionFailedException(response.text)
        data = response.json()
        self.store_authentication_information(data)

    def store_authentication_information(self, data: dict):
        self.access_token = data["access_token"]
        self.authentication_time = time.time()
        self.expires_in = data["expires_in"]
        self.refresh_token = data["refresh_token"]
        self.refresh_expires_in = data["refresh_expires_in"]

    def reauthenticate(self):
        response = requests.post(
            self.url(AUTHENTICATION_ENDPOINT),
            data={"refresh_token": self.refresh_token},
        )
        if response.status_code != 200:
            raise ConnectionFailedException(response.text)
        data = response.json()
        self.store_authentication_information(data)

    def authenticate_if_required(self):
        if time.time() - self.authentication_time > self.refresh_expires_in - 2:
            self.authenticate()
        elif time.time() - self.authentication_time > self.expires_in - 2:
            self.reauthenticate()

    @property
    def authorisation_header(self) -> dict:
        self.authenticate_if_required()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_locations(self) -> list[Location]:
        response = requests.get(self.url(LOCATIONS_ENDPOINT), headers=self.authorisation_header)
        if response.status_code != 200:
            raise ConnectionFailedException(response.text)
        return [
            Location(
                location_data["name"],
                location_data["role"],
                location_data["userId"],
                location_data["locationId"],
                location_data["gatewayserial"],
            )
            for location_data in response.json()
        ]

    def get_location(self, location_id) -> SingleLocation:
        response = requests.get(
            self.url(SINGLE_LOCATION_ENDPOINT) + f"/{location_id}",
            headers=self.authorisation_header,
        )
        if response.status_code != 200:
            raise ConnectionFailedException(response.text)
        data = response.json()
        devices = []
        for device in data["devices"]:
            devices.append(
                Device(
                    device["id"],
                    device["name"],
                    device["serialNumber"],
                    device["location"],
                    device["online"],
                    device["modelId"],
                    device["modelName"],
                    device["features"],
                )
            )
        return SingleLocation(
            data["locationId"],
            data["gatewayserial"],
            data["name"],
            data["alarmState"],
            data["userRoleAtLocation"],
            devices,
        )

    def get_web_socket(self, location_id: str, on_message: Callable) -> websocket.WebSocketApp:
        self.authenticate_if_required()
        websocket.enableTrace(True)
        url = f"{WEB_SOCKET_URL}?locationId={location_id}"
        logger.debug(f"Connecting to web socket {url}")
        ws = websocket.WebSocketApp(
            url,
            header={**self.authorisation_header, "locationId": location_id},
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        return ws


def on_error(ws, error):
    logger.debug(f"Websocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    logger.debug(f"Websocket closed")


def on_open(ws):
    logger.debug(f"Websocket connected")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    homely = Homely("***", "***")
    locations = homely.get_locations()
    for location in locations:
        logger.debug(f"Received location '{location}'")
    location = homely.get_location(locations[0].location_id)
    logger.debug(f"Received single location '{location}'")
    for device in location.devices:
        logger.debug(f"Device: {device} has features {device.features}")
    ws = homely.get_web_socket(location.location_id, lambda data: logger.debug(f"Received data: {data}"))
    ws.run_forever(
        dispatcher=rel, reconnect=5
    )  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
