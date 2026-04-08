import os
import select
from .const import DEVICE_PATH, DEVICE_INFO_PATH, CAPABILITIES_PATH
from .capabilities import Capabilities
from .utils import read_file_safe
from .event import Event


class Device:
    def __init__(self, event_code):
        self.event_code = event_code
        self.event_path = os.path.join(DEVICE_PATH, event_code)
        self.info_path = os.path.join(DEVICE_INFO_PATH, event_code)
        if not os.path.exists(self.event_path) or not os.path.exists(self.info_path):
            raise LookupError(f"no such device: {event_code}")
        self.name_path = os.path.join(self.info_path, "device", "name")
        self.modalias_path = os.path.join(self.info_path, "device", "modalias")
        self.name = read_file_safe(self.name_path).strip()
        self.modalias = read_file_safe(self.modalias_path).strip()
        self.fd = os.open(self.event_path, os.O_RDWR)
        self.capabilities = Capabilities(
            os.path.join(self.info_path, CAPABILITIES_PATH), self.fd
        )

        self.closed = False

    def poll(self, timeout=0.0):
        return bool(select.select([self.fd], [], [], timeout)[0])

    def wait(self):
        self.poll(None)

    def get_event(self):
        return Event.read(self.fd)

    def iter_events(self):
        while self.poll():
            yield self.get_event()

    def close(self):
        self.closed = True
        os.close(self.fd)

    def __repr__(self):
        return f"<Device {self.name!r} ({self.event_path})>"

    def __del__(self):
        if not self.closed and os is not None and os.close is not None:
            self.close()


def list_devices():
    device_list = []
    for device in os.listdir(DEVICE_PATH):
        if device.startswith("event") or device.startswith("mouse"):
            device_list.append(Device(device))
    return device_list
