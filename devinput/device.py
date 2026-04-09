import os
import select
import functools
import ctypes
import contextlib
import asyncio

from .const import DEVICE_PATH, DEVICE_INFO_PATH, CAPABILITIES_PATH
from .capabilities import Capabilities
from .utils import read_file_safe
from .event import Event
from .ioctl import IoctlInterface, InputKeymapEntry
from .props import Props
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
        except IOError:
            self.name = None
        try:
            self.modalias = read_file_safe(self.modalias_path).strip()
        except IOError:
            self.modalias = None
        self._capabilities = None
        self.fd = None
        self.ioctl = None
        self.input_id = None

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
        self.input_id = self.ioctl.GID()
        self._capabilities = Capabilities(
            os.path.join(self.info_path, CAPABILITIES_PATH), self.ioctl
        )

    @_require_open
    def poll(self, timeout=0.0):
        return bool(select.select([self.fd], [], [], timeout)[0])

    @_require_open
    async def poll_async(self, timeout=0.0):
        if timeout == 0.0:
            return self.poll(timeout)  # it's okay because it doesn't block
        loop = asyncio.get_event_loop()
        future = asyncio.Future()

        def callback():
            if not future.done():
                future.set_result(None)

        loop.add_reader(self.fd, callback)
        try:
            await asyncio.wait_for(future, timeout)
            return True
        except TimeoutError:
            return False
        finally:
            loop.remove_reader(self.fd)

    def wait(self):
        self.poll(None)

    async def wait_async(self):
        await self.poll_async(None)

    @_require_open
    def get_event(self):
        return Event.read(self.fd)

    @_require_open
    def send_event(self, event):
        return event.write(self.fd)

    @_require_open
    def flush(self):
        while self.poll():
            self.get_event()

    @_require_open
    async def get_event_async(self, timeout=None):
        try:
            return await Event.read_async(self.fd, timeout)
        except TimeoutError:
            return None

    @_require_open
    async def send_event_async(self, event):
        return await event.write_async(self.fd)

    @_require_open
    async def flush_async(self):
        while await self.poll_async():
            await self.get_event_async()

    @_require_open
    def iter_events(self):
        while self.poll():
            yield self.get_event()

    @_require_open
    async def iter_events_async(self):
        while await self.poll_async():
            yield await self.get_event_async()

    @_require_open
    def __iter__(self):
        while True:
            yield self.get_event()

    @_require_open
    async def __aiter__(self):
        while True:
            yield await self.get_event_async()

    def close(self):
        if self.fd and not self.closed:
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

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
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
    def get_keys(self, interesting=None):
        if not self.has_cap(EventType.EV_KEY):
            raise ValueError("device doesn't support key events")

        keys_buffer = self.ioctl.GKEY(128)
        keys_mask = int.from_bytes(keys_buffer, "little")
        keys = set()
        for (
            key
        ) in (
            interesting or self.capabilities.key_cap
        ):  # it's not efficient to iterate through all 700 keys
            if (1 << key.value) & keys_mask:
                keys.add(key)
        return keys

    @_require_open
    def get_leds(self, interesting=None):
        if not self.has_cap(EventType.EV_LED):
            raise ValueError("device has no LEDs")
        leds_buffer = self.ioctl.GLED(8)
        leds_mask = int.from_bytes(leds_buffer, "little")
        leds = set()
        for led in (interesting or LedEvent):
            if (1 << led.value) & leds_mask:
                leds.add(led)
        return leds

    @_require_open
    def get_sounds(self, interesting=None):
        if not self.has_cap(EventType.EV_SND):
            raise ValueError("device doesn't support sound events")
        sounds_buffer = self.ioctl.GSND(2)
        sounds_mask = int.from_bytes(sounds_buffer, "little")
        sounds = set()
        for snd in (interesting or SndEvent):
            if (1 << snd.value) & sounds_mask:
                sounds.add(snd)
        return sounds

    @_require_open
    def get_switches(self, interesting=None):
        if not self.has_cap(EventType.EV_SW):
            raise ValueError("device doesn't support switch events")
        switches_buffer = self.ioctl.GSW(8)
        switches_mask = int.from_bytes(switches_buffer, "little")
        switches = set()
        for sw in (interesting or SwEvent):
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

    @_require_open
    def get_properties(self):
        prop_bytes = self.ioctl.GPROP(16)
        prop_mask = int.from_bytes(prop_bytes, "little")
        props = set()
        for prop in Props:
            if (1 << prop.value) & prop_mask:
                props.add(prop)
        return props

    @_require_open
    def grab(self):
        self.ioctl.GRAB(1)

    @_require_open
    def ungrab(self):
        self.ioctl.GRAB(0)

    @contextlib.contextmanager
    @_require_open
    def grabbed(self):
        try:
            yield self.grab()
        finally:
            self.ungrab()

    ### No force feedback for now, since I have no device to test it on.


def list_devices():
    device_list = []
    for device in os.listdir(DEVICE_PATH):
        if device.startswith("event"):
            device_list.append(Device.from_event(device))
    return device_list


def list_capable_devices(*caps):
    device_list = []
    for device in list_devices():
        with device:
            if all(device.has_cap(cap) for cap in caps):
                device_list.append(Device(device.event_path))
    return device_list
