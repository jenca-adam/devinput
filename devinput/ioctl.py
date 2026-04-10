import enum
import ctypes
import functools
import fcntl

from .bus import BusType


class IOC_DIR(enum.IntEnum):
    NONE = 0
    WRITE = 1
    READ = 2


_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS


def build_ioctl_request(dir, type, nr, size):
    return (
        (dir << _IOC_DIRSHIFT)
        | (type << _IOC_TYPESHIFT)
        | (nr << _IOC_NRSHIFT)
        | (size << _IOC_SIZESHIFT)
    )


def build_ev_read_request(nr, size):
    return build_ioctl_request(IOC_DIR.READ, ord("E"), nr, size)


def build_ev_write_request(nr, size):
    return build_ioctl_request(IOC_DIR.WRITE, ord("E"), nr, size)


def _ioctl_read_factory(nr, target=None):

    def decorate(fun):
        if target is None:

            @functools.wraps(fun)
            def _ioctl_read(fd, size):
                request = build_ev_read_request(nr, size)
                buffer = bytearray(size)
                fcntl.ioctl(fd, request, buffer)
                return bytes(buffer)

            return _ioctl_read
        else:
            request = build_ev_read_request(nr, ctypes.sizeof(target))

            @functools.wraps(fun)
            def _ioctl_read(fd):

                buffer = bytearray(ctypes.sizeof(target))
                fcntl.ioctl(fd, request, buffer)
                return target.from_buffer(buffer)

            return _ioctl_read

    return decorate


def _ioctl_write_factory(nr, source=None, as_int=False):

    def decorate(fun):
        if source is None:

            @functools.wraps(fun)
            def _ioctl_write(fd, buffer):

                request = build_ev_write_request(nr, len(buffer))
                fcntl.ioctl(fd, request, buffer)

            return _ioctl_write
        else:
            request = build_ev_write_request(nr, ctypes.sizeof(source))

            @functools.wraps(fun)
            def _ioctl_write(fd, what):
                if not isinstance(what, source):
                    what = source(what)
                if as_int:
                    what = what.value
                else:
                    what = bytes(what)
                fcntl.ioctl(fd, request, what)

            return _ioctl_write

    return decorate


class InputId(ctypes.Structure):
    _bustype: ctypes.c_uint16
    vendor: ctypes.c_uint16
    product: ctypes.c_uint16
    version: ctypes.c_uint16
    _fields_ = [
        ("_bustype", ctypes.c_uint16),
        ("vendor", ctypes.c_uint16),
        ("product", ctypes.c_uint16),
        ("version", ctypes.c_uint16),
    ]

    @property
    def bus_type(self) -> BusType:
        return BusType(self._bustype)


class RepeatSettings(ctypes.Structure):
    delay: ctypes.c_uint32
    period: ctypes.c_uint32

    _fields_ = [("delay", ctypes.c_uint32), ("period", ctypes.c_uint32)]


class InputKeymapEntry(ctypes.Structure):
    flags: ctypes.c_uint8
    len: ctypes.c_uint8
    index: ctypes.c_uint8
    keycode: ctypes.c_uint32
    scancode: ctypes.c_uint8 * 32
    _fields_ = [
        ("flags", ctypes.c_uint8),
        ("len", ctypes.c_uint8),
        ("index", ctypes.c_uint16),
        ("keycode", ctypes.c_uint32),
        ("scancode", ctypes.c_uint8 * 32),
    ]


class InputAbsInfo(ctypes.Structure):
    value: ctypes.c_int32
    minimum: ctypes.c_int32
    maximum: ctypes.c_int32
    fuzz: ctypes.c_int32
    flat: ctypes.c_int32
    resolution: ctypes.c_int32
    _fields_ = [
        ("value", ctypes.c_int32),
        ("minimum", ctypes.c_int32),
        ("maximum", ctypes.c_int32),
        ("fuzz", ctypes.c_int32),
        ("flat", ctypes.c_int32),
        ("resolution", ctypes.c_int32),
    ]


class FfReplay(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint16), ("delay", ctypes.c_uint16)]


class FfTrigger(ctypes.Structure):
    _fields_ = [("button", ctypes.c_uint16), ("interval", ctypes.c_uint16)]


class FfEnvelope(ctypes.Structure):
    _fields_ = [
        ("attack_length", ctypes.c_uint16),
        ("attack_level", ctypes.c_uint16),
        ("fade_length", ctypes.c_uint16),
        ("fade_level", ctypes.c_uint16),
    ]


class FfConstantEffect(ctypes.Structure):
    _fields_ = [("level", ctypes.c_int16), ("envelope", FfEnvelope)]


class FfRampEffect(ctypes.Structure):
    _fields_ = [
        ("start_level", ctypes.c_int16),
        ("end_level", ctypes.c_int16),
        ("envelope", FfEnvelope),
    ]


class FfConditionEffect(ctypes.Structure):
    _fields_ = [
        ("right_saturation", ctypes.c_uint16),
        ("left_saturation", ctypes.c_uint16),
        ("right_coeff", ctypes.c_int16),
        ("left_coeff", ctypes.c_int16),
        ("deadband", ctypes.c_uint16),
        ("center", ctypes.c_int16),
    ]


class FfPeriodicEffect(ctypes.Structure):
    _fields_ = [
        ("waveform", ctypes.c_uint16),
        ("period", ctypes.c_uint16),
        ("magnitude", ctypes.c_int16),
        ("offset", ctypes.c_int16),
        ("phase", ctypes.c_uint16),
        ("envelope", FfEnvelope),
        ("custom_len", ctypes.c_uint32),
        ("custom_data", ctypes.POINTER(ctypes.c_int16)),
    ]


class FfRumbleEffect(ctypes.Structure):
    _fields_ = [
        ("strong_magnitude", ctypes.c_uint16),
        ("weak_magnitude", ctypes.c_uint16),
    ]


class FfEffect(ctypes.Structure):
    class _effect_union(ctypes.Union):
        _fields_ = [
            ("constant", FfConstantEffect),
            ("ramp", FfRampEffect),
            ("periodic", FfPeriodicEffect),
            ("condition", FfConditionEffect * 2),
            ("rumble", FfRumbleEffect),
        ]

    _fields_ = [
        ("type", ctypes.c_uint16),
        ("id", ctypes.c_int16),
        ("direction", ctypes.c_uint16),
        ("trigger", FfTrigger),
        ("replay", FfReplay),
        ("u", _effect_union),
    ]


class IoctlInterface:
    def __init__(self, fd):
        self.fd = fd

    @_ioctl_read_factory(0x01, ctypes.c_int)
    def GVERSION(self):
        pass

    @_ioctl_read_factory(0x02, InputId)
    def GID(self):
        pass

    @_ioctl_read_factory(0x03, RepeatSettings)
    def GREP(self):
        pass

    @_ioctl_read_factory(0x04, ctypes.c_uint * 2)
    def GKEYCODE(self):
        pass

    def GKEYCODE_V2(self, buffer):
        assert len(buffer) == ctypes.sizeof(InputKeymapEntry)
        request = build_ev_read_request(0x04, len(buffer))
        fcntl.ioctl(self.fd, request, buffer)

    @_ioctl_read_factory(0x06)
    def GNAME(self, size):
        pass

    @_ioctl_read_factory(0x07)
    def GPHYS(self, size):
        pass

    @_ioctl_read_factory(0x08)
    def GUNIQ(self, size):
        pass

    @_ioctl_read_factory(0x09)
    def GPROP(self, size):
        pass

    @_ioctl_read_factory(0x18)
    def GKEY(self, size):
        pass

    @_ioctl_read_factory(0x19)
    def GLED(self, size):
        pass

    @_ioctl_read_factory(0x1A)
    def GSND(self, size):
        pass

    @_ioctl_read_factory(0x1B)
    def GSW(self, size):
        pass

    @_ioctl_write_factory(0x03, RepeatSettings)
    def SREP(self, what):
        pass

    @_ioctl_write_factory(0x04, ctypes.c_uint * 2)
    def SKEYCODE(self, what):
        pass

    @_ioctl_write_factory(0x04, InputKeymapEntry)
    def SKEYCODE_V2(self, what):
        pass

    @_ioctl_write_factory(0x80, FfEffect)
    def SFF(self, what):
        pass

    @_ioctl_write_factory(0x81, ctypes.c_int, True)
    def RMFF(self, what):
        pass

    @_ioctl_write_factory(0x90, ctypes.c_int, True)
    def GRAB(self, what):
        pass

    @_ioctl_write_factory(0x91, ctypes.c_int, True)
    def REVOKE(self, what):
        pass

    @_ioctl_write_factory(0xA0, ctypes.c_int, True)
    def SCLOCKID(self, what):
        pass

    @_ioctl_read_factory(0x84, ctypes.c_int)
    def GEFFECTS(self):
        pass

    def GMTSLOTS(self, code, num_slots):
        class MtRequest(ctypes.Structure):
            _pack_ = 1
            _fields_ = [
                ("code", ctypes.c_uint32),
                ("values", ctypes.c_int32 * num_slots),
            ]

        buffer = bytearray(ctypes.sizeof(MtRequest))
        mt_request = MtRequest.from_buffer(buffer)
        mt_request.code = code
        request = build_ev_read_request(0x0A, len(buffer))
        fcntl.ioctl(self.fd, request, buffer)
        return mt_request

    def GBIT(self, ev, length):
        return _ioctl_read_factory(0x20 + ev)(lambda x, y: x)(self.fd, length)

    def GABS(self, abs_code):
        return _ioctl_read_factory(0x40 + abs_code, InputAbsInfo)(lambda x: x)(self.fd)

    def SABS(self, abs_code, absinfo):
        return _ioctl_write_factory(0xC0 + abs_code, InputAbsInfo)(lambda x, y: x)(
            self.fd, absinfo
        )

    def fileno(self):
        return self.fd
