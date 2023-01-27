import datetime
import logging

from dateutil.parser import parse

logging.basicConfig(
    format="%(asctime)s %(threadName)-15s %(name)-15s: %(levelname)-8s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
import argparse
import json
import time
from getpass import getpass
from typing import Callable, Dict, List, Tuple, Any, Optional

import requests
import socketio
import websocket

from homelypy.devices import Location, SingleLocation, create_device_from_rest_response, UnknownDeviceException, Device
from homelypy.states import State

WEB_SOCKET_URL = "wss://sdk.iotiliti.cloud"

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
    single_location: SingleLocation
    state_change_callback: Callable[[SingleLocation, Device, List[State]], Any]
    sio: socketio.Client

    def __init__(self, username: str, password: str):
        super().__init__()
        self.refresh_expires_in = 0
        self.expires_in = 0
        self.authentication_time = 0
        self.access_token = None
        self.refresh_token = None
        self.username = username
        self.password = password

    def _register_callbacks(self):
        @self.sio.event
        def connect():
            logger.info("websocket: connected to server")

        @self.sio.event
        def disconnect():
            logger.info("websocket: disconnected from server")
            # Disconnected, refresh login
            self.sio.connection_headers = self.build_connection_header()

        @self.sio.on("event")
        def on_message(data):
            # logger.info(data)
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
            if data["type"] == "device-state-changed":
                if self.single_location:
                    device, states = self.single_location.update_device_state_from_stream(data["data"])
                    if self.state_change_callback:
                        self.state_change_callback(None, device, states)
            elif data["type"] == "alarm-state-changed":
                if self.single_location:
                    self.single_location.alarm_state = data["data"]["state"]
                    self.single_location.alarm_state_last_updated = parse(data["data"]["timestamp"])
                    if self.state_change_callback:
                        self.state_change_callback(self.single_location, None, [])

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
            try:
                devices.append(create_device_from_rest_response(device))
            except UnknownDeviceException as ex:
                logger.error(str(ex))
        return SingleLocation(
            data["locationId"],
            data["gatewayserial"],
            data["name"],
            data["alarmState"],
            datetime.datetime.now(datetime.timezone.utc),
            data["userRoleAtLocation"],
            devices,
        )

    def build_connection_header(self) -> dict:
        return {**self.authorisation_header, "locationId": self.single_location.location_id}

    def run_socket_io(
        self,
        single_location: SingleLocation,
        state_change_callback: Optional[Callable[[Device, List[State]], Any]] = None,
    ):
        self.state_change_callback = state_change_callback
        self.single_location = single_location
        self.authenticate_if_required()
        websocket.enableTrace(True)
        url = f"{WEB_SOCKET_URL}?locationId={single_location.location_id}&token=Bearer%20{self.access_token}"
        logger.debug(f"Connecting to web socket {url}")
        self.sio = socketio.Client(logger=logger, engineio_logger=False, reconnection=False)
        self._register_callbacks()
        logging.getLogger("socketio").setLevel(logger.level)
        logging.getLogger("websocket").setLevel(logger.level)
        logging.getLogger("engineio").setLevel(logger.level)
        while True:
            try:
                header = self.build_connection_header()
                self.sio.connect(url, headers=header)
                self.sio.wait()
            except:
                logger.exception("Exception while running socketio")
            try:
                self.sio.disconnect()
            except Exception as ex:
                logger.warning(f"Failed disconnecting after unexpected websocket termination: {ex}")
            logger.info("Socket terminating restarting in 5 seconds")
            time.sleep(5)


def test_callback(single_location: Optional[SingleLocation], device: Optional[Device], states: List[State]):
    if device is not None:
        logger.info(f"Received update for device '{device}'")
        for state in states:
            logger.info(f"\t{state.feature_name} change to {state}")
    if single_location is not None:
        logger.info(f"Received alarm update: {single_location.alarm_state}")


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    parser = argparse.ArgumentParser(prog="Homelypy", description="Query the Homely rest API")
    parser.add_argument("username", help="Same username as in the Homely app")
    parser.add_argument("-s", "--stream", action="store_true", help="Initiate websocket stream")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug output")
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    password = getpass()

    homely = Homely(args.username, password)
    locations = homely.get_locations()
    for location in locations:
        logger.info(f"Received location '{location}'")
    for location in locations:
        filename = f"location_{location.name}.json"
        location_dictionary = homely.get_location_json(location.location_id)
        # pprint(location_dictionary)
        # logger.info("----------------------------------")
        with open(filename, "w") as o:
            json.dump(location_dictionary, o)
        logger.info(f"Full dump for location {location} written to {filename}")

    location = homely.get_location(locations[0].location_id)
    if args.stream:
        homely.run_socket_io(location, test_callback)
