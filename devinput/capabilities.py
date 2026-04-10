import os
from .ioctl import IoctlInterface
from .utils import read_file_safe
from .event_types import *

CapabilityTypeUnion = EventType | EventTypeUnion


def parse_cap(content: str) -> int:
    hex_code = []
    for word in content.strip().split(" "):
        hex_code.append(f"{word:>016}")  # pad from left with 16 zeroes
    return int("".join(hex_code), 16)


def parse_cap_file(filename: str) -> int:
    return parse_cap(read_file_safe(filename))


def get_cap_set(
    cap_code: int, cap_enum: type[CapabilityTypeUnion]
) -> set[CapabilityTypeUnion]:
    cap_set = set()
    for cap in cap_enum:
        if cap_code & (1 << cap.value):
            cap_set.add(cap)
    return cap_set


class Capabilities:
    abs_path: str
    ev_path: str
    ff_path: str
    key_path: str
    led_path: str
    msc_path: str
    rel_path: str
    snd_path: str
    sw_path: str

    abs_cap_code: int
    event_types_code: int
    key_cap_code: int
    led_cap_code: int
    msc_cap_code: int
    rel_cap_code: int
    snd_cap_code: int
    sw_cap_code: int

    ioctl: IoctlInterface
    path: str

    def __init__(self, path: str, ioctl: IoctlInterface):
        self.path = path
        self.ioctl = ioctl

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
        self.event_types_code = parse_cap_file(self.ev_path)
        self.key_cap_code = parse_cap_file(self.key_path)
        self.led_cap_code = parse_cap_file(self.led_path)
        self.msc_cap_code = parse_cap_file(self.msc_path)
        self.rel_cap_code = parse_cap_file(self.rel_path)
        self.snd_cap_code = parse_cap_file(self.snd_path)
        self.sw_cap_code = parse_cap_file(self.sw_path)

        self._abs_cap = self._event_types = self._key_cap = self._led_cap = (
            self._msc_cap
        ) = self._rel_cap = self._snd_cap = self._sw_cap = self._syn_cap = None

        self._syn_cap_code = None

    @property
    def abs_cap(self) -> set[AbsEvent]:
        """
        All ABS capabilities
        """
        if self._abs_cap is None:
            self._abs_cap = get_cap_set(self.abs_cap_code, AbsEvent)
        return self._abs_cap

    @property
    def event_types(self) -> set[EventType]:
        """
        All supported event types
        """
        if self._event_types is None:
            self._event_types = get_cap_set(self.event_types_code, EventType)
        return self._event_types

    @property
    def key_cap(self) -> set[KeyEvent]:
        """
        All KEY capabilities
        """
        if self._key_cap is None:
            self._key_cap = get_cap_set(self.key_cap_code, KeyEvent)
        return self._key_cap

    @property
    def led_cap(self) -> set[LedEvent]:
        """
        All LED capabilities
        """
        if self._led_cap is None:
            self._led_cap = get_cap_set(self.led_cap_code, LedEvent)
        return self._led_cap

    @property
    def msc_cap(self) -> set[MscEvent]:
        """
        All MSC capabilities
        """
        if self._msc_cap is None:
            self._msc_cap = get_cap_set(self.msc_cap_code, MscEvent)
        return self._msc_cap

    @property
    def rel_cap(self) -> set[RelEvent]:
        """
        All REL capabilities
        """
        if self._rel_cap is None:
            self._rel_cap = get_cap_set(self.rel_cap_code, RelEvent)
        return self._rel_cap

    @property
    def snd_cap(self) -> set[SndEvent]:
        """
        All SND capabilities
        """
        if self._snd_cap is None:
            self._snd_cap = get_cap_set(self.snd_cap_code, SndEvent)
        return self._snd_cap

    @property
    def sw_cap(self) -> set[SwEvent]:
        """
        All SW capabilities
        """
        if self._sw_cap is None:
            self._sw_cap = get_cap_set(self.sw_cap_code, SwEvent)
        return self._sw_cap

    @property
    def syn_cap_code(self) -> int:
        """
        The bitmask of all SYN capabilities.
        (the reason this is a property is that it requires an ioctl call)
        """
        if self._syn_cap_code is None:
            self._syn_cap_code = self._gbit(EventType.EV_SYN)
        return self._syn_cap_code

    @property
    def syn_cap(self) -> set[SynEvent]:
        """
        All SYN capabilities
        """
        if self._syn_cap is None:
            self._syn_cap = get_cap_set(self.syn_cap_code, SynEvent)
        return self._syn_cap

    def _gbit(self, ev):
        length = 128  # should be enough even if new events get added
        buf = self.ioctl.GBIT(ev, length)
        return int.from_bytes(buf, "little")

    def has_cap(self, cap: CapabilityTypeUnion) -> bool:
        """
        Checks for a capability

        :param cap: the capability to check
        """
        mask = 1 << cap
        if isinstance(cap, SynEvent):
            return bool(mask & self.syn_cap_code)
        if isinstance(cap, KeyEvent):
            return bool(mask & self.key_cap_code)
        if isinstance(cap, RelEvent):
            return bool(mask & self.rel_cap_code)
        if isinstance(cap, AbsEvent):
            return bool(mask & self.abs_cap_code)
        if isinstance(cap, MscEvent):
            return bool(mask & self.msc_cap_code)
        if isinstance(cap, SwEvent):
            return bool(mask & self.sw_cap_code)
        if isinstance(cap, LedEvent):
            return bool(mask & self.led_cap_code)
        if isinstance(cap, SndEvent):
            return bool(mask & self.snd_cap_code)
        if isinstance(cap, EventType):
            return bool(mask & self.event_types_code)
        return False

    def list(self, cap_type: EventType) -> set[EventTypeUnion]:
        if cap_type == EventType.EV_SYN:
            return self.syn_cap
        if cap_type == EventType.EV_KEY:
            return self.key_cap
        if cap_type == EventType.EV_REL:
            return self.rel_cap
        if cap_type == EventType.EV_ABS:
            return self.abs_cap
        if cap_type == EventType.EV_MSC:
            return self.msc_cap
        if cap_type == EventType.EV_SW:
            return self.sw_cap
        if cap_type == EventType.EV_LED:
            return self.led_cap
        if cap_type == EventType.EV_SND:
            return self.snd_cap
        return set()

    def __contains__(self, cap):
        return self.has_cap(cap)
