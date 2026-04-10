import ctypes
import datetime
import os
import time
import asyncio

from .event_types import *

time_t_size = ctypes.sizeof(ctypes.c_void_p)
time_t: type
if time_t_size == 8:
    time_t = ctypes.c_uint64
else:
    time_t = ctypes.c_uint32


class Event(ctypes.Structure):
    _fields_ = [
        ("_tv_sec", time_t),
        ("_tv_usec", time_t),
        ("_type", ctypes.c_ushort),
        ("_code", ctypes.c_ushort),
        ("value", ctypes.c_uint),
    ]
    value: int
    def __init__(self, code: EventTypeUnion, value: int, timestamp: float | None = None):
        timestamp = timestamp or time.time()
        self._tv_sec = time_t(int(timestamp))
        self._tv_usec = time_t(int((timestamp - self._tv_sec) * 1_000_000))
        self._type = ctypes.c_ushort(EVENT_ENUMS[code.__class__].value)
        self._code = ctypes.c_ushort(code.value)
        self.value = value

    @property
    def timestamp(self) -> float:
        return self._tv_sec + self._tv_usec / 1_000_000

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    @property
    def type(self) -> EventType:
        return EventType(self._type)

    @property
    def code(self) -> EventTypeUnion:
        return EVENT_TYPES.get(self._type, UnknownEvent)(self._code)

    @classmethod
    def read(cls, fd: int) -> Event:
        buf = os.read(fd, ctypes.sizeof(cls))
        return cls.from_buffer_copy(buf)

    @classmethod
    async def read_async(cls, fd: int, timeout: int | float | None = None) -> Event:
        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        length = ctypes.sizeof(cls)

        def callback():
            future.set_result(os.read(fd, length))

        loop.add_reader(fd, callback)
        try:
            await asyncio.wait_for(future, timeout)
        finally:
            loop.remove_reader(fd)
        return cls.from_buffer_copy(future.result())

    def write(self, fd: int) -> int:
        return os.write(fd, bytes(self))

    async def write_async(self, fd: int, timeout: int | float | None = None) -> int:

        loop = asyncio.get_event_loop()
        future = asyncio.Future()

        def callback(*_):
            future.set_result(None)

        loop.add_reader(fd, callback)
        try:
            await asyncio.wait_for(future, timeout)
            os.write(fd, bytes(self))
        finally:
            loop.remove_reader(fd)

    def __repr__(self):
        return f"<Event type={self.type!r} code={self.code!r} value={self.value}>"
