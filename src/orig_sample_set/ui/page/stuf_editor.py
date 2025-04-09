import wx

from src.ui.icon import get_icon


class StufEditor(wx.Panel):
    def __init__(self, parent, is_new, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        super().__init__(parent)

    def get_name(self):
        if self.is_new:
            return "(новый) Штуф"
        return self.o.Name

    def get_icon(self):
        return get_icon("file")
