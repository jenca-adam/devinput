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
        ("tv_sec", time_t),
        ("tv_usec", time_t),
        ("_type", ctypes.c_ushort),
        ("_code", ctypes.c_ushort),
        ("value", ctypes.c_uint),
    ]

    def __init__(self, code, value):
        timestamp = time.time()
        self.tv_sec = int(timestamp)
        self.tv_usec = int((timestamp - self.tv_sec) * 1_000_000)
        self._type = EVENT_ENUMS[code.__class__].value
        self._code = code.value
        self.value = value

    @property
    def timestamp(self):
        return self.tv_sec + self.tv_usec / 1_000_000

    @property
    def datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp)

    @property
    def type(self):
        return EventType(self._type)

    @property
    def code(self):
        return EVENT_TYPES.get(self._type, UnknownEvent)(self._code)

    @classmethod
    def read(cls, fd):
        buf = os.read(fd, ctypes.sizeof(cls))
        return cls.from_buffer_copy(buf)

    @classmethod
    async def read_async(cls, fd, timeout=None):
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

    def write(self, fd):
        return os.write(fd, bytes(self))

    async def write_async(self, fd, timeout=None):

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
