import wx

from src.ui.icon import get_icon


class PmSampleSetEditor(wx.Panel):
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sz)
        self.Layout()

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return "[Проба] " + self.o.Name

    def get_icon(self):
        return get_icon("file")
