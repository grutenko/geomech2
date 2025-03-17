import wx
from pony.orm import db_session, select

from src.ui.icon import get_icon


class EntityList(wx.Panel):
    def __init__(self, parent, columns, entity, query=None):
        super().__init__(parent)
        self.columns = columns
        self.entity = entity
        self.query = query
        sz = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_FLAT | wx.TB_HORZ_TEXT)
        self.toolbar.AddTool(wx.ID_ADD, "Добавить", get_icon("file-add"))
        self.toolbar.AddTool(wx.ID_EDIT, "Изменить", get_icon("edit"))
        self.toolbar.AddTool(wx.ID_DELETE, "Удалить", get_icon("delete"))
        self.toolbar.EnableTool(wx.ID_EDIT, False)
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.Realize()
        sz.Add(self.toolbar, 0, wx.EXPAND)
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT)
        for code, (name, converter, width) in self.columns.items():
            self.list.AppendColumn(name, width=width)
        sz.Add(self.list, 1, wx.EXPAND)
        self.statusbar = wx.StatusBar(self)
        sz.Add(self.statusbar, 0, wx.EXPAND)
        self.SetSizer(sz)
        self.items = []
        self.load()

    @db_session
    def load(self):
        self.items = []
        self.list.DeleteAllItems()
        if len(self.columns.keys()) == 0:
            return
        if self.query is not None:
            query = self.query
        else:
            query = select(o for o in self.entity)
        for index, row in enumerate(query):
            first_column = list(self.columns.keys()).__getitem__(0)
            self.list.InsertItem(index, getattr(row, first_column))
