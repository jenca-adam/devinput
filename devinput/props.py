import enum
from .utils import UnknownEnumMeta


class Props(enum.Enum, metaclass=UnknownEnumMeta):
    INPUT_PROP_POINTER = 0x00  # needs a pointer
    INPUT_PROP_DIRECT = 0x01  # direct input devices
    INPUT_PROP_BUTTONPAD = 0x02  # has button(s) under pad
    INPUT_PROP_SEMI_MT = 0x03  # touch rectangle only
    INPUT_PROP_TOPBUTTONPAD = 0x04  # softbuttons at top of pad
    INPUT_PROP_POINTING_STICK = 0x05  # is a pointing stick
    INPUT_PROP_ACCELEROMETER = 0x06  # has accelerometer
