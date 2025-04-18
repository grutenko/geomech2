import wx
import wx.lib.agw.flatnotebook

from src.ui.icon import get_icon

from .table import FmsTable
from .tree import TreePage


class FmsPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.lib.agw.flatnotebook.FlatNotebookCompatible(
            self, agwStyle=wx.lib.agw.flatnotebook.FNB_NO_X_BUTTON
        )
        self.tree = TreePage(self.notebook)
        self.table = FmsTable(self.notebook)
        self.notebook.AddPage(self.tree, "Данные")
        self.notebook.AddPage(self.table, "Сводка")
        self.notebook.AddPage(wx.Panel(self.notebook), "Статистика")
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        sz.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def on_page_changed(self, event):
        if self.notebook.GetSelection() == 1:
            self.table.start()
        else:
            self.table.end()

    def get_name(self):
        return "ФМС"

    def get_icon(self):
        return get_icon("folder")
