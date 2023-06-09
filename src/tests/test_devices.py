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

    def test_create_entry_sensor_2(self):
        rest_response = {
            "features": {
                "alarm": {
                    "states": {
                        "alarm": {
                            "value": False,
                            "lastUpdated": "2023-06-06T17:44:38.401Z",
                        },
                        "tamper": {
                            "value": False,
                            "lastUpdated": "2023-05-01T17:41:31.157Z",
                        },
                    }
                },
                "temperature": {
                    "states": {
                        "temperature": {
                            "value": 26.4,
                            "lastUpdated": "2023-06-09T18:22:11.817Z",
                        }
                    }
                },
                "battery": {
                    "states": {
                        "low": {
                            "value": False,
                            "lastUpdated": "2023-05-01T17:41:31.082Z",
                        },
                        "defect": {"value": None, "lastUpdated": None},
                        "voltage": {
                            "value": 3,
                            "lastUpdated": "2023-06-09T14:42:13.160Z",
                        },
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkstrength": {
                            "value": 75,
                            "lastUpdated": "2023-06-09T17:54:51.847Z",
                        },
                        "networklinkaddress": {
                            "value": "0015BC0041003169",
                            "lastUpdated": "2023-05-01T20:24:05.798Z",
                        },
                    }
                },
            },
            "id": "3f37711f-cb83-4174-babe-7f492ee8de5a",
            "name": "Alarm Entry Sensor 2",
            "serialNumber": "0015BC004400810A",
            "location": "Floor 2 - Loftgang",
            "online": True,
            "modelId": "9b765375-e3f4-4627-b73c-b4143ce86c2c",
            "modelName": "Alarm Entry Sensor 2",
        }

        device: EntrySensor = create_device_from_rest_response(rest_response)
        self.assertTrue(isinstance(device, EntrySensor))
        self.assertEqual("Alarm Entry Sensor 2", device.name)
        self.assertEqual(26.4, device.temperature.temperature)
        self.assertEqual(
            datetime.datetime(2023, 6, 9, 18, 22, 11, 817000, tzinfo=tzutc()),
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

    def test_create_motion_sensor_2(self):
        rest_response = {
            "features": {
                "alarm": {
                    "states": {
                        "alarm": {
                            "value": False,
                            "lastUpdated": "2023-06-09T18:21:11.541Z",
                        },
                        "tamper": {
                            "value": False,
                            "lastUpdated": "2023-05-01T17:00:41.908Z",
                        },
                        "sensitivitylevel": {
                            "value": 3,
                            "lastUpdated": "2023-05-01T17:00:41.742Z",
                        },
                    }
                },
                "temperature": {
                    "states": {
                        "temperature": {
                            "value": 26.3,
                            "lastUpdated": "2023-06-09T18:23:07.538Z",
                        }
                    }
                },
                "battery": {
                    "states": {
                        "low": {
                            "value": False,
                            "lastUpdated": "2023-05-01T17:00:41.839Z",
                        },
                        "defect": {
                            "value": False,
                            "lastUpdated": "2023-05-01T17:00:41.857Z",
                        },
                        "voltage": {
                            "value": 3,
                            "lastUpdated": "2023-05-11T05:01:05.016Z",
                        },
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkstrength": {
                            "value": 94,
                            "lastUpdated": "2023-06-09T17:37:39.567Z",
                        },
                        "networklinkaddress": {
                            "value": "0015BC002C100EBD",
                            "lastUpdated": "2023-05-01T17:00:40.479Z",
                        },
                    }
                },
            },
            "id": "51ecf8af-fc27-4d95-af14-295355e5f33d",
            "name": "Alarm Motion Sensor 2",
            "serialNumber": "0015BC001A1064CE",
            "location": "Floor 1 - Living room",
            "online": True,
            "modelId": "17ddbcb4-8c00-4bc3-b06f-d20f51c0fe52",
            "modelName": "Alarm Motion Sensor 2",
        }
        device: MotionSensor2 = create_device_from_rest_response(rest_response)
        self.assertTrue(isinstance(device, MotionSensor2))
        self.assertEqual(94, device.diagnostic.network_link_strength)

    def test_create_water_leak_sensor(self):
        rest_response = {
            "features": {
                "alarm": {
                    "states": {
                        "flood": {
                            "value": False,
                            "lastUpdated": "2023-05-17T09:20:46.868Z",
                        }
                    }
                },
                "temperature": {
                    "states": {
                        "temperature": {
                            "value": 21.9,
                            "lastUpdated": "2023-06-08T15:58:39.078Z",
                        }
                    }
                },
                "battery": {
                    "states": {
                        "low": {
                            "value": False,
                            "lastUpdated": "2023-05-17T09:20:46.850Z",
                        },
                        "voltage": {
                            "value": 3,
                            "lastUpdated": "2023-05-17T10:36:16.891Z",
                        },
                    }
                },
                "diagnostic": {
                    "states": {
                        "networklinkstrength": {
                            "value": 92,
                            "lastUpdated": "2023-06-08T16:08:58.577Z",
                        },
                        "networklinkaddress": {
                            "value": "0015BC004100389B",
                            "lastUpdated": "2023-06-03T07:26:15.037Z",
                        },
                    }
                },
            },
            "id": "1a03becf-be4d-4189-ac5f-eedff786e76a",
            "name": "Water Leak Detector",
            "serialNumber": "0015BC00330053A3",
            "location": "Floor 1 - Kitchen",
            "online": True,
            "modelId": "22f7b47e-c40a-4943-b44a-c70f7ce820ff",
            "modelName": "Water Leak Detector",
        }
        device: WaterLeakDetector = create_device_from_rest_response(rest_response)
        self.assertTrue(isinstance(device, WaterLeakDetector))
        self.assertEqual(92, device.diagnostic.network_link_strength)
