import wx

from src.ui.icon import get_icon
from src.ui.supplied_data import SuppliedDataWidget

from .samples import SamplesWidget


class PmSampleSetEditor(wx.Panel):
    def __init__(self, parent, is_new=False, o=None, parent_object=None):
        self.is_new = is_new
        self.o = o
        self.parent_object = parent_object
        super().__init__(parent)
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_SAVE, "Сохранить", get_icon("save"))
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left = wx.ScrolledWindow(self.splitter)
        p_sz = wx.BoxSizer(wx.VERTICAL)
        p_sz_in = wx.BoxSizer(wx.VERTICAL)
        p_sz.Add(p_sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.left.SetSizer(p_sz)
        self.left.SetVirtualSize(self.left.GetBestSize() + (250, 250))
        self.left.SetScrollRate(10, 10)
        self.right = wx.Notebook(self.splitter)
        self.samples = SamplesWidget(self.right)
        self.right.AddPage(self.samples, "Образцы")
        self.supplied_data = SuppliedDataWidget(self.right, deputy_text="Недоступно для новых объектов.")
        self.right.AddPage(self.supplied_data, "Сопутствующие материалы")
        self.splitter.SplitVertically(self.left, self.right, 250)
        self.splitter.SetMinimumPaneSize(250)
        sz.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()
        self.SetSizer(sz)
        self.Layout()
        if not self.is_new:
            self.supplied_data.start(self.o, _type="PM_SAMPLE_SET")
            self.samples.start(self.o)

    def get_name(self):
        if self.is_new:
            return "(новый)"
        return "[Проба] " + self.o.Name

    def get_icon(self):
        return get_icon("file")
