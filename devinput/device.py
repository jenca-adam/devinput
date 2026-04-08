import os
import select
import functools
import ctypes

from .const import DEVICE_PATH, DEVICE_INFO_PATH, CAPABILITIES_PATH
from .capabilities import Capabilities
from .utils import read_file_safe
from .event import Event
from .ioctl import IoctlInterface, InputKeymapEntry
from .event_types import *


class Device:
    def __init__(self, event_path):
        self.closed = True
        self.event_path = event_path
        self.event_code = os.path.split(event_path)[-1]
        self.info_path = os.path.join(DEVICE_INFO_PATH, self.event_code)
        if not os.path.exists(self.event_path):
            raise LookupError(f"no such device: {self.event_path}")
        self.name_path = os.path.join(self.info_path, "device", "name")
        self.modalias_path = os.path.join(self.info_path, "device", "modalias")
        try:
            self.name = read_file_safe(self.name_path).strip()
        except:
            self.name = None
        try:
            self.modalias = read_file_safe(self.modalias_path).strip()
        except:
            self.modalias = None
        self._capabilities = None
        self.fd = None
        self.ioctl = None

    @staticmethod
    def _require_open(fun):
        @functools.wraps(fun)
        def replace(self, *args, **kwargs):
            if self.closed:
                raise ValueError("device closed")
            return fun(self, *args, **kwargs)

        return replace

    def open(self):
        self.closed = False
        try:
            self.fd = os.open(self.event_path, os.O_RDWR)
        except PermissionError as err:
            raise PermissionError(
                "can't open device: make sure the user is in the input group"
            ) from err

        self.ioctl = IoctlInterface(self.fd)
        self._capabilities = Capabilities(
            os.path.join(self.info_path, CAPABILITIES_PATH), self.ioctl
        )

    @_require_open
    def poll(self, timeout=0.0):
        return bool(select.select([self.fd], [], [], timeout)[0])

    def wait(self):
        self.poll(None)

    @_require_open
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
        if (
            hasattr(self, "closed")
            and not self.closed
            and os is not None
            and os.close is not None
        ):
            self.close()

    @property
    def capabilities(self):
        if self._capabilities is None:
            raise ValueError("device not open yet")
        return self._capabilities

    @classmethod
    def from_event(cls, event_code):
        return cls(os.path.join(DEVICE_PATH, event_code))

    def has_cap(self, cap):
        return cap in self.capabilities

    @_require_open
    def get_absolute(self, abs_type):
        if not self.has_cap(EventType.EV_ABS):
            raise ValueError("device doesn't support absolute events")
        if not self.has_cap(abs_type):
            raise ValueError(
                f"absolute event {abs_type!r} not supported on this device"
            )
        return self.ioctl.GABS(abs_type)

    @_require_open
    def get_keys(self):
        if not self.has_cap(EventType.EV_KEY):
            raise ValueError("device doesn't support key events")

        keys_buffer = self.ioctl.GKEY(128)
        keys_mask = int.from_bytes(keys_buffer, "little")
        keys = set()
        for (
            key
        ) in (
            self.capabilities.key_cap
        ):  # it's not efficient to iterate through all 700 keys
            if (1 << key.value) & keys_mask:
                keys.add(key)
        return keys

    @_require_open
    def get_leds(self):
        if not self.has_cap(EventType.EV_LED):
            raise ValueError("device has no LEDs")
        leds_buffer = self.ioctl.GLED(8)
        leds_mask = int.from_bytes(leds_buffer, "little")
        leds = set()
        for led in LedEvent:
            if (1 << led.value) & leds_mask:
                leds.add(led)
        return leds

    @_require_open
    def get_sounds(self):
        if not self.has_cap(EventType.EV_SND):
            raise ValueError("device doesn't support sound events")
        sounds_buffer = self.ioctl.GSND(2)
        sounds_mask = int.from_bytes(sounds_buffer, "little")
        sounds = set()
        for snd in SndEvent:
            if (1 << snd.value) & sounds_mask:
                sounds.add(snd)
        return sounds

    @_require_open
    def get_switches(self):
        if not self.has_cap(EventType.EV_SW):
            raise ValueError("device doesn't support switch events")
        switches_buffer = self.ioctl.GSW(8)
        switches_mask = int.from_bytes(switches_buffer, "little")
        switches = set()
        for sw in SwEvent:
            if (1 << sw.value) & switches_mask:
                switches.add(sw)
        return switches

    @_require_open
    def get_keycode(self, scancode_or_index, by_index=False):
        if not self.has_cap(EventType.EV_KEY):
            raise ValueError("device doesn't support key events")
        buffer = bytearray(ctypes.sizeof(InputKeymapEntry))
        entry = InputKeymapEntry.from_buffer(buffer)
        if by_index:
            entry.index = scancode_or_index
            entry.flags |= 1
        else:
            entry.scancode = (ctypes.c_uint8 * 32)(*scancode_or_index)
            entry.len = len(scancode_or_index)
        self.ioctl.GKEYCODE_V2(buffer)
        return entry.keycode

    @_require_open
    def get_multi_touch_values(self, mt_code, num_slots=16):
        if not self.has_cap(EventType.EV_ABS):
            raise ValueError("device doesn't support absolute events")
        if not self.has_cap(mt_code):
            raise ValueError(
                f"multi-touch event {mt_code!r} not supported on this device"
            )
        return list(self.ioctl.GMTSLOTS(mt_code, num_slots).values)

    @_require_open
    def get_multi_touch_state(self, num_slots=16):
        available_mt_events = MT_EVENTS & self.capabilities.abs_cap
        if not available_mt_events:
            raise ValueError("no multi-touch events supported on this device")
        event_slots = {}
        for event in available_mt_events:
            event_slots[event] = self.get_multi_touch_values(event, num_slots)
        return event_slots

    ### No force feedback for now, since I have no device to test it on.


def list_devices():
    device_list = []
    for device in os.listdir(DEVICE_PATH):
        if device.startswith("event"):
            device_list.append(Device.from_event(device))
    return device_list
