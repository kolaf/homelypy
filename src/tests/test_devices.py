import datetime
from unittest import TestCase

from dateutil.tz import tzutc

from homelypy.devices import create_device_from_rest_response, WindowSensor, SmokeAlarm, MotionSensorMini, \
    UnknownDeviceException


class TestDeviceCreation(TestCase):

    def test_unknown_sensor(self):
        rest_response = {
            "features": {
                "alarm": {
                    "states": {
                        "alarm": {"lastUpdated": "2022-12-31T16:34:31.189Z", "value": False},
                        "tamper": {"lastUpdated": "2022-06-10T15:43:20.402Z", "value": False},
                    }
                },
                "battery": {
                    "states": {
                        "defect": {"lastUpdated": None, "value": None},
                        "low": {"lastUpdated": "2022-06-10T15:29:20.956Z", "value": False},
                        "voltage": {"lastUpdated": "2022-12-09T12:33:11.390Z", "value": 2.9},
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkaddress": {"lastUpdated": "2022-11-19T22:00:31.223Z", "value": "0015BC0041001B88"},
                        "networklinkstrength": {"lastUpdated": "2022-12-31T16:07:13.769Z", "value": 92},
                    }
                },
                "temperature": {"states": {"temperature": {"lastUpdated": "2022-12-31T16:26:12.692Z", "value": 16}}},
            },
            "id": "f6210e83-a41c-49c6-a24a-57733ba8ea44",
            "location": "Floor 0 - Entrance",
            "modelId": "87fa1ae0-824f-4d42-be7a-cc5b6c7b1e35",
            "modelName": "Bogus model",
            "name": "Window Sensor",
            "online": True,
            "serialNumber": "0015BC001E014469",
        }
        with self.assertRaises(UnknownDeviceException):
            device: WindowSensor = create_device_from_rest_response(rest_response)
    def test_create_window_sensor(self):
        rest_response = {
            "features": {
                "alarm": {
                    "states": {
                        "alarm": {"lastUpdated": "2022-12-31T16:34:31.189Z", "value": False},
                        "tamper": {"lastUpdated": "2022-06-10T15:43:20.402Z", "value": False},
                    }
                },
                "battery": {
                    "states": {
                        "defect": {"lastUpdated": None, "value": None},
                        "low": {"lastUpdated": "2022-06-10T15:29:20.956Z", "value": False},
                        "voltage": {"lastUpdated": "2022-12-09T12:33:11.390Z", "value": 2.9},
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkaddress": {"lastUpdated": "2022-11-19T22:00:31.223Z", "value": "0015BC0041001B88"},
                        "networklinkstrength": {"lastUpdated": "2022-12-31T16:07:13.769Z", "value": 92},
                    }
                },
                "temperature": {"states": {"temperature": {"lastUpdated": "2022-12-31T16:26:12.692Z", "value": 16}}},
            },
            "id": "f6210e83-a41c-49c6-a24a-57733ba8ea44",
            "location": "Floor 0 - Entrance",
            "modelId": "87fa1ae0-824f-4d42-be7a-cc5b6c7b1e35",
            "modelName": "Window Sensor",
            "name": "Window Sensor",
            "online": True,
            "serialNumber": "0015BC001E014469",
        }
        device: WindowSensor = create_device_from_rest_response(rest_response)
        self.assertTrue(isinstance(device, WindowSensor))
        self.assertEqual("Window Sensor", device.name)
        self.assertEqual(16, device.temperature.temperature)
        self.assertEqual(
            datetime.datetime(2022, 12, 31, 16, 26, 12, 692000, tzinfo=tzutc()),
            device.temperature.temperature_last_updated,
        )

    def test_create_smoke_alarm(self):
        rest_response = {
            "features": {
                "alarm": {"states": {"fire": {"lastUpdated": "2022-12-15T10:41:00.825Z", "value": False}}},
                "battery": {
                    "states": {
                        "low": {"lastUpdated": "2022-06-10T15:30:20.675Z", "value": False},
                        "voltage": {"lastUpdated": "2022-12-24T00:44:01.043Z", "value": 3},
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkaddress": {"lastUpdated": "2022-12-23T21:40:30.214Z", "value": "0015BC002C101A48"},
                        "networklinkstrength": {"lastUpdated": "2022-12-31T16:17:42.676Z", "value": 47},
                    }
                },
                "temperature": {"states": {"temperature": {"lastUpdated": "2022-12-31T16:30:06.306Z", "value": 17.6}}},
            },
            "id": "c90f6b7e-c451-498e-a1c6-ba3b46150ce5",
            "location": "Floor 0 - Living room",
            "modelId": "ffe30099-92c5-4471-879f-41f412d423ab",
            "modelName": "Smoke Alarm",
            "name": "Smoke Alarm",
            "online": True,
            "serialNumber": "0015BC003100CE07",
        }
        device: SmokeAlarm = create_device_from_rest_response(rest_response)
        self.assertTrue(isinstance(device, SmokeAlarm))
        self.assertFalse(device.alarm.fire)

    def test_create_motion_sensor_mini(self):
        rest_response = {
            "features": {
                "alarm": {
                    "states": {
                        "alarm": {"lastUpdated": "2022-12-31T16:28:43.861Z", "value": True},
                        "sensitivitylevel": {"lastUpdated": None, "value": None},
                        "tamper": {"lastUpdated": "2022-06-10T16:17:58.161Z", "value": False},
                    }
                },
                "battery": {
                    "states": {
                        "defect": {"lastUpdated": "2022-06-10T16:15:05.770Z", "value": False},
                        "low": {"lastUpdated": "2022-06-10T16:15:05.741Z", "value": False},
                        "voltage": {"lastUpdated": "2022-12-22T06:50:30.112Z", "value": 2.9},
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkaddress": {"lastUpdated": "2022-12-22T05:50:26.083Z", "value": "0015BC002C101A48"},
                        "networklinkstrength": {"lastUpdated": "2022-12-31T16:27:48.088Z", "value": 89},
                    }
                },
                "temperature": {"states": {"temperature": {"lastUpdated": "2022-12-31T16:27:03.967Z", "value": 19.4}}},
            },
            "id": "28e0b340-26a6-475c-a419-a5f31bc8f479",
            "location": "Floor 1 - Hallway",
            "modelId": "e806ca73-4be0-4bd2-98cb-71f273b09812",
            "modelName": "Motion Sensor Mini",
            "name": "Motion Sensor Mini",
            "online": True,
            "serialNumber": "0015BC001A012223",
        }
        device: MotionSensorMini = create_device_from_rest_response(rest_response)
        self.assertTrue(isinstance(device, MotionSensorMini))
        self.assertEqual(89, device.diagnostic.network_link_strength)
