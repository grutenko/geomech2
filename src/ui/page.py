from typing import Protocol, runtime_checkable

import wx
import wx.lib.newevent

PageHdrChangedEvent, EVT_PAGE_HDR_CHANGED = wx.lib.newevent.NewEvent()


@runtime_checkable
class PageProto(Protocol):
    def get_name(self) -> str: ...
    def get_icon(self) -> wx.Bitmap | None: ...
