import wx

from src.datetimeutil import decode_date
from src.ui.icon import get_icon

from .prevent_action_dialog import PreventActionDialog


class PreventActionsList(wx.Panel):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.items = []
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE | wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить мероприятие", get_icon("file-add"))
        self.Bind(wx.EVT_TOOL, self.on_add, id=wx.ID_ADD)
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.list.AppendColumn("Мероприятие", width=250)
        self.list.AppendColumn("Дата проведения", width=100)
        sz.Add(self.list, 1, wx.EXPAND)
        self.SetSizer(sz)
        self.Layout()

    def load(self):
        self.list.DeleteAllItems()
        for index, o in self.items:
            self.list.InsertItem(index, o.rb_typical_prevent_action.Name)
            self.list.SetItem(index, decode_date(o.Date).__str__())

    def on_add(self, event):
        dlg = PreventActionDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self.items.append(dlg.o)
            self.load()
            self.update_controls_state()

    def update_controls_state(self):
        self.toolbar.EnableTool(wx.ID_DELETE, self.list.GetSelectedItemCount() > 0)


1
