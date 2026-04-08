import os
import enum
from .utils import read_file_safe
from . import evioc
from .event_types import *


def parse_cap(content):
    hex_code = []
    for word in content.strip().split(" "):
        hex_code.append(f"{word:>016}")  # pad from left with 16 zeroes
    return int("".join(hex_code), 16)


def parse_cap_file(filename):
    return parse_cap(read_file_safe(filename))


def get_cap_set(cap_code, cap_enum):
    cap_set = set()
    for cap in cap_enum:
        if cap_code & (1 << cap.value):
            cap_set.add(cap)
    return cap_set


class Capabilities:
    def __init__(self, path, event_fd):
        self.path = path
        self.event_fd = event_fd

        self.abs_path = os.path.join(path, "abs")
        self.ev_path = os.path.join(path, "ev")
        self.ff_path = os.path.join(path, "ff")
        self.key_path = os.path.join(path, "key")
        self.led_path = os.path.join(path, "led")
        self.msc_path = os.path.join(path, "msc")
        self.rel_path = os.path.join(path, "rel")
        self.snd_path = os.path.join(path, "snd")
        self.sw_path = os.path.join(path, "sw")

        self.abs_cap_code = parse_cap_file(self.abs_path)
        self.ev_cap_code = parse_cap_file(self.ev_path)
        self.key_cap_code = parse_cap_file(self.key_path)
        self.led_cap_code = parse_cap_file(self.led_path)
        self.msc_cap_code = parse_cap_file(self.msc_path)
        self.rel_cap_code = parse_cap_file(self.rel_path)
        self.snd_cap_code = parse_cap_file(self.snd_path)
        self.sw_cap_code = parse_cap_file(self.sw_path)

        self._abs_cap = self._ev_cap = self._key_cap = self._led_cap = self._msc_cap = (
            self._rel_cap
        ) = self._snd_cap = self._sw_cap = self._syn_cap = None

        self._syn_cap_code = None

    @property
    def abs_cap(self):
        if self._abs_cap is None:
            self._abs_cap = get_cap_set(self.abs_cap_code, AbsEvent)
        return self._abs_cap

    @property
    def ev_cap(self):
        if self._ev_cap is None:
            self._ev_cap = get_cap_set(self.ev_cap_code, EvEvent)
        return self._ev_cap

    @property
    def key_cap(self):
        if self._key_cap is None:
            self._key_cap = get_cap_set(self.key_cap_code, KeyEvent)
        return self._key_cap

    @property
    def led_cap(self):
        if self._led_cap is None:
            self._led_cap = get_cap_set(self.led_cap_code, LedEvent)
        return self._led_cap

    @property
    def msc_cap(self):
        if self._msc_cap is None:
            self._msc_cap = get_cap_set(self.msc_cap_code, MscEvent)
        return self._msc_cap

    @property
    def rel_cap(self):
        if self._rel_cap is None:
            self._rel_cap = get_cap_set(self.rel_cap_code, RelEvent)
        return self._rel_cap

    @property
    def snd_cap(self):
        if self._snd_cap is None:
            self._snd_cap = get_cap_set(self.snd_cap_code, SndEvent)
        return self._snd_cap

    @property
    def sw_cap(self):
        if self._sw_cap is None:
            self._sw_cap = get_cap_set(self.sw_cap_code, SwEvent)
        return self._sw_cap

    @property
    def syn_cap_code(self):
        if self._syn_cap_code is None:
            self._syn_cap_code = self._gbit(EvEvent.EV_SYN)
        return self._syn_cap_code

    @property
    def syn_cap(self):
        if self._syn_cap is None:
            self._syn_cap = get_cap_set(self.syn_cap_code, SynEvent)
        return self._syn_cap

    def _gbit(self, ev):
        length = 4
        buf = evioc.GBIT(self.event_fd, ev, length)
        return int.from_bytes(buf, "little")

    def has_cap(self, cap):
        if isinstance(cap, SynEvent):
            return bool(cap.value & self.syn_cap_code)
        elif isinstance(cap, KeyEvent):
            return bool(cap.value & self.key_cap_code)
        elif isinstance(cap, RelEvent):
            return bool(cap.value & self.rel_cap_code)
        elif isinstance(cap, AbsEvent):
            return bool(cap.value & self.abs_cap_code)
        elif isinstance(cap, MscEvent):
            return bool(cap.value & self.msc_cap_code)
        elif isinstance(cap, SwEvent):
            return bool(cap.value & self.sw_cap_code)
        elif isinstance(cap, LedEvent):
            return bool(cap.value & self.led_cap_code)
        elif isinstance(cap, SndEvent):
            return bool(cap.value & self.snd_cap_code)
        return False

    def __contains__(self, cap):
        return self.has_cap(cap)
