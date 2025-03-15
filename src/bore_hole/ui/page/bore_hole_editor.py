import wx

from src.ui.icon import get_icon


class BoreHoleEditor(wx.Panel):
    def __init__(self, parent, is_new: bool = False, o=None, parent_object=None):
        super().__init__(parent)
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        sz = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self)
        self.left = wx.Panel(self.splitter)
        l_sz = wx.BoxSizer(wx.VERTICAL)
        self.left.SetSizer(l_sz)
        self.right = wx.Notebook(self.splitter)
        self.splitter.SplitVertically(self.left, self.right)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return self.o.get_tree_name()

    def get_icon(self):
        return get_icon("file")
