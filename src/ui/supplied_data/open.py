import ctypes


def open_file(path: str) -> bool:
    print(path)
    ctypes.windll.shell32.ShellExecuteW(None, "open", '"' + path + '"', None, None, 1)
