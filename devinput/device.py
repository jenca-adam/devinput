import os
from .const import DEVICE_PATH, DEVICE_INFO_PATH, CAPABILITIES_PATH
from .capabilities import Capabilities
from .utils import read_file_safe


class Device:
    def __init__(self, event_code):
        self.event_code = event_code
        self.event_path = os.path.join(DEVICE_PATH, event_code)
        self.info_path = os.path.join(DEVICE_INFO_PATH, event_code)
        if not os.path.exists(self.event_path) or not os.path.exists(self.info_path):
            raise LookupError(f"no such device: {event_code}")
        self.capabilities = Capabilities(
            os.path.join(self.info_path, CAPABILITIES_PATH)
        )
        self.name_path = os.path.join(self.info_path, "device", "name")
        self.modalias_path = os.path.join(self.info_path, "device", "modalias")
        self.name = read_file_safe(self.name_path).strip()
        self.modalias = read_file_safe(self.modalias_path).strip()

    def __repr__(self):
        return f"<Device {self.name!r} ({self.event_path})>"

def list_devices():
    device_list = []
    for device in os.listdir(DEVICE_PATH):
        if device.startswith("event") or device.startswith("mouse"):
            device_list.append(Device(device))
    return device_list
