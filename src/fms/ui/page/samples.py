import wx
import wx.propgrid

from src.ui.icon import get_icon
from src.ui.overlay import Overlay


class PropertiesWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.propgrid = wx.propgrid.PropertyGrid(self)
        sz.Add(self.propgrid, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()


ID_PROP_ADD = wx.ID_HIGHEST + 135
ID_PROP_DELETE = ID_PROP_ADD + 1


class SampleDialog(wx.Dialog): ...


class PropertyDialog(wx.Dialog): ...


class SamplesWidget(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.o = None
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить образец", get_icon("file-add"))
        self.toolbar.AddTool(ID_PROP_ADD, "Добавить свойство", get_icon("file-add"))
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.toolbar.EnableTool(ID_PROP_ADD, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.list = wx.ListCtrl(self.splitter, style=wx.LC_REPORT)
        self.list.AppendColumn("№ Образца")
        self.properties = PropertiesWidget(self.splitter)
        self.splitter.SplitVertically(self.list, self.properties, 150)
        self.splitter.SetMinimumPaneSize(100)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.Disable()
        self.overlay = Overlay(self)
        self.overlay.Show()

    def start(self, o):
        self.o = o
        self.Enable()
        self.update_controls_state()
        self.overlay.Hide()

    def end(self):
        self.o = None
        self.Disable()
        self.update_controls_state()
        self.overlay.Show()
        self.overlay.Raise()

    def update_controls_state(self): ...
