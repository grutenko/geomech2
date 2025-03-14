import wx

from src.ui.icon import get_icon


class BoreHoleEditor(wx.Panel):
    def __init__(self, parent, is_new: bool = False, o=None, parent_object=None):
        super().__init__(parent)
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")
