import ctypes
from ctypes import wintypes

import wx
from PIL import Image

# Константы
SHGFI_ICON = 0x000000100
SHGFI_USEFILEATTRIBUTES = 0x000000010
FILE_ATTRIBUTE_NORMAL = 0x80


class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", wintypes.INT),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


def get_file_icon(extension):
    import tempfile

    shfileinfo = SHFILEINFO()
    flags = SHGFI_ICON | SHGFI_USEFILEATTRIBUTES
    shell32 = ctypes.windll.shell32

    with tempfile.TemporaryFile(suffix="." + extension) as file:
        result = shell32.SHGetFileInfoW(
            file.name, FILE_ATTRIBUTE_NORMAL, ctypes.byref(shfileinfo), ctypes.sizeof(shfileinfo), flags
        )

        if result:
            icon = wx.Icon()
            icon.CreateFromHICON(shfileinfo.hIcon)

            # Прямое преобразование wx.Icon → wx.Bitmap
            bmp = wx.Bitmap(icon.GetWidth(), icon.GetHeight())
            dc = wx.MemoryDC(bmp)
            dc.Clear()
            dc.DrawIcon(icon, 0, 0)
            dc.SelectObject(wx.NullBitmap)
            wx.Bitmap.Rescale(bmp, wx.Size(16, 16))
            return bmp

        return None
