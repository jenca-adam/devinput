import enum

from .utils import UnknownEnumMeta


class BusType(enum.IntEnum, metaclass=UnknownEnumMeta):
    BUS_PCI = 0x01
    BUS_ISAPNP = 0x02
    BUS_USB = 0x03
    BUS_HIL = 0x04
    BUS_BLUETOOTH = 0x05
    BUS_VIRTUAL = 0x06

    BUS_ISA = 0x10
    BUS_I8042 = 0x11
    BUS_XTKBD = 0x12
    BUS_RS232 = 0x13
    BUS_GAMEPORT = 0x14
    BUS_PARPORT = 0x15
    BUS_AMIGA = 0x16
    BUS_ADB = 0x17
    BUS_I2C = 0x18
    BUS_HOST = 0x19
    BUS_GSC = 0x1A
    BUS_ATARI = 0x1B
    BUS_SPI = 0x1C
