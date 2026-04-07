def read_file_safe(filename, binary=False):
    with open(filename, "rb" if binary else "r") as fp:
        return fp.read()
