import enum
import ctypes
import functools
import fcntl
import _ctypes


class IOC_DIR(enum.IntEnum):
    NONE = 1
    READ = 2
    WRITE = 4


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


def _ioctl_write_factory(nr, source=None):
    def decorate(fun):
        if source is None:

            @functools.wraps(fun)
            def _ioctl_write(fd, buffer):
                request = build_ev_write_request(nr, len(buffer))
                fcntl.ioctl(fd, buffer)

            return _ioctl_write
        else:
            request = build_ev_write_request(nr, ctypes.sizeof(source))

            @functools.wraps(fun)
            def _ioctl_write(fd, what):
                if not isinstance(what, source):
                    what = source(what)
                fcntl.ioctl(fd, request, bytes(what))

            return _ioctl_write

    return decorate


class InputId(ctypes.Structure):
    _fields_ = [
        ("bustype", ctypes.c_uint16),
        ("vendor", ctypes.c_uint16),
        ("product", ctypes.c_uint16),
        ("version", ctypes.c_uint16),
    ]


class InputKeymapEntry(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint8),
        ("len", ctypes.c_uint8),
        ("index", ctypes.c_uint16),
        ("keycode", ctypes.c_uint32),
        ("scancode", ctypes.c_uint8 * 32),
    ]


class InputAbsInfo(ctypes.Structure):
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


@_ioctl_read_factory(0x01, ctypes.c_int)
def GVERSION(fd):
    pass


@_ioctl_read_factory(0x02, InputId)
def GID(fd):
    pass


@_ioctl_read_factory(0x03, ctypes.c_uint * 2)
def GREP(fd):
    pass


@_ioctl_write_factory(0x03, ctypes.c_uint * 2)
def SREP(fd, what):
    pass


@_ioctl_read_factory(0x04, ctypes.c_uint * 2)
def GKEYCODE(fd):
    pass


@_ioctl_read_factory(0x04, InputKeymapEntry)
def GKEYCODE_V2(fd):
    pass


@_ioctl_write_factory(0x04, ctypes.c_uint * 2)
def SKEYCODE(fd, what):
    pass


@_ioctl_write_factory(0x04, InputKeymapEntry)
def SKEYCODE_V2(fd, what):
    pass


@_ioctl_read_factory(0x06)
def GNAME(fd):
    pass


@_ioctl_read_factory(0x07)
def GPHYS(fd):
    pass


@_ioctl_read_factory(0x08)
def GUNIQ(fd):
    pass


@_ioctl_read_factory(0x09)
def GPROP(fd):
    pass


# ugh
def GMTSLOTS(fd, num_slots):
    class MtRequestLayout(ctypes.Structure):
        _fields_ = [
            ("code", ctypes.c_uint32),
            ("values", ctypes.c_int32 * num_slots),
        ]

    return _ioctl_read_factory(0x0A, MtRequestLayout)(GMTSLOTS)(fd)


@_ioctl_read_factory(0x18)
def GKEY(fd):
    pass


@_ioctl_read_factory(0x19)
def GLED(fd):
    pass


@_ioctl_read_factory(0x1A)
def GSND(fd):
    pass


@_ioctl_read_factory(0x1B)
def GSW(fd):
    pass


def GBIT(fd, ev, length):
    return _ioctl_read_factory(0x20 + ev)(GBIT)(fd, length)


def GABS(fd, abs):
    return _ioctl_read_factory(0x40 + abs, InputAbsInfo)(GABS)(fd)


def SABS(fd, abs, absinfo):
    return _ioctl_write_factory(0xC0 + abs, InputAbsInfo)(SABS)(fd, absinfo)


@_ioctl_write_factory(0x80, FfEffect)
def SFF(fd, what):
    pass


@_ioctl_write_factory(0x81, ctypes.c_int)
def RMFF(fd, what):
    pass


@_ioctl_read_factory(0x84, ctypes.c_int)
def GEFFECTS(fd):
    pass


@_ioctl_write_factory(0x90, ctypes.c_int)
def GRAB(fd, what):
    pass


@_ioctl_write_factory(0x91, ctypes.c_int)
def REVOKE(fd, what):
    pass


@_ioctl_write_factory(0xA0, ctypes.c_int)
def SCLOCKID(fd, what):
    pass
