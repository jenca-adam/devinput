import enum

from .utils import UnknownEnumMeta


class MtTool(enum.IntEnum, metaclass=UnknownEnumMeta):
    MT_TOOL_FINGER = 0
    MT_TOOL_PEN = 1
    MT_TOOL_PALM = 2
