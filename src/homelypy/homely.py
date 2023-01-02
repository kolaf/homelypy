import argparse
import dataclasses
import json
import logging
import time
from getpass import getpass
from pprint import pprint
from typing import Callable, Dict, List

import requests
import websocket

from homelypy.devices import Location, SingleLocation, create_device_from_rest_response

WEB_SOCKET_URL = "ws://sdk.iotiliti.cloud"

SDK_URL = "https://sdk.iotiliti.cloud"
AUTHENTICATION_ENDPOINT = "/homely/oauth/token"
LOCATIONS_ENDPOINT = "/homely/locations"
SINGLE_LOCATION_ENDPOINT = "/homely/home"
REFRESH_TOKEN_ENDPOINT = "/homely/oauth/refresh-token"

logger = logging.getLogger(__name__)


class ConnectionFailedException(Exception):
    pass


class AuthenticationFailedException(Exception):
    pass


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
        if response.status_code == 401:
            raise AuthenticationFailedException(response.text)
        if response.status_code != 201:
            raise ConnectionFailedException(response.text)
        data = response.json()
        self.store_authentication_information(data)

    def store_authentication_information(self, data: Dict):
        self.access_token = data["access_token"]
        self.authentication_time = time.time()
        self.expires_in = data["expires_in"]
        self.refresh_token = data["refresh_token"]
        self.refresh_expires_in = data["refresh_expires_in"]

    def reauthenticate(self):
        response = requests.post(
            self.url(REFRESH_TOKEN_ENDPOINT),
            data={"refresh_token": self.refresh_token},
        )
        if response.status_code != 201:
            self.refresh_expires_in = -1
            self.expires_in = -1
            raise ConnectionFailedException(response.text)
        data = response.json()
        self.store_authentication_information(data)

    def authenticate_if_required(self):
        if time.time() - self.authentication_time > self.refresh_expires_in - 2:
            self.authenticate()
        elif time.time() - self.authentication_time > self.expires_in - 2:
            self.reauthenticate()

    @property
    def authorisation_header(self) -> Dict:
        self.authenticate_if_required()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_locations(self) -> List[Location]:
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

    def get_location_json(self, location_id) -> dict:
        response = requests.get(
            self.url(SINGLE_LOCATION_ENDPOINT) + f"/{location_id}",
            headers=self.authorisation_header,
        )
        if response.status_code != 200:
            raise ConnectionFailedException(response.text)
        return response.json()

    def get_location(self, location_id) -> SingleLocation:
        data = self.get_location_json(location_id)
        devices = []
        for device in data["devices"]:
            devices.append(create_device_from_rest_response(device))
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
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(prog="Homelypy", description="Query the Homely rest API")
    parser.add_argument("username", help="Same username as in the Homely app")
    args = parser.parse_args()
    password = getpass()

    homely = Homely(args.username, password)
    locations = homely.get_locations()
    for location in locations:
        print(f"Received location '{location}'")
    for location in locations:
        print(f"Full dump for location {location}")
        location_dictionary = homely.get_location_json(location.location_id)
        pprint(location_dictionary)
        print("----------------------------------")
        with open(f"location_{location.name}.json", "w") as o:
            json.dump(location_dictionary, o)
    # location = homely.get_location(locations[0].location_id)
    # logger.debug(f"Received single location '{location}'")
    # for device in location.devices:
    #     logger.debug(f"Device: {device} is of type {device.__class__}")
    #
    # location = homely.get_location(locations[0].location_id)
    # ws = homely.get_web_socket(location.location_id, lambda data: logger.debug(f"Received data: {data}"))
    # import rel
    #
    # ws.run_forever(
    #     dispatcher=rel, reconnect=5
    # )  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    # rel.signal(2, rel.abort)  # Keyboard Interrupt
    # rel.dispatch()
