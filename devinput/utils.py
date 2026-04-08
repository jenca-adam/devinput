import enum


class UnknownEnumMember:
    def __init__(self, enum_cls, value):
        self.enum = enum_cls
        self.value = value
        self.name = "UNKNOWN"
        self.__dict__.update(enum_cls.__dict__)

    def __repr__(self):
        return f"<{self.enum.__name__}.{self.name}: {self.value}>"


class UnknownEnumMeta(enum.EnumMeta):
    def __call__(cls, value, *args, **kwargs):
        try:
            return super().__call__(value, *args, **kwargs)
        except ValueError:
            return UnknownEnumMember(cls, value)


def read_file_safe(filename, binary=False):
    with open(filename, "rb" if binary else "r") as fp:
        return fp.read()
