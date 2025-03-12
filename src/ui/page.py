from typing import Protocol, runtime_checkable

import wx


@runtime_checkable
class PageProto(Protocol):
    def get_name(self) -> str: ...
    def get_icon(self) -> wx.Bitmap | None: ...
