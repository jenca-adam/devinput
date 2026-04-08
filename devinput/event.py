import ctypes
import datetime
import os
import time

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

    def write(self, fd):
        return os.write(fd, bytes(self))

    def __repr__(self):
        return f"<Event type={self.type!r} code={self.code!r} value={self.value}>"
