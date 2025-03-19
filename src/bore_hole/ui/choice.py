import wx
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import BoreHole


class Choice(wx.Panel):
    def __init__(self, parent, query=None):
        super().__init__(parent)
        self.items = []
        self.selection = None
        self.query = query
        sz = wx.BoxSizer(wx.VERTICAL)
        self.choice = wx.Choice(self)
        self.choice.SetMaxSize(wx.Size(250, -1))
        sz.Add(self.choice, 0, wx.EXPAND)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(hsz, 0, wx.EXPAND)
        self.btn_open = wx.StaticText(self, label="Окрыть")
        font = wx.Font().Underlined()
        self.btn_open.SetFont(font)
        self.btn_open.SetForegroundColour(wx.Colour(100, 100, 255))
        self.btn_open.Bind(wx.EVT_LEFT_DOWN, self.on_open)
        self.btn_open.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        hsz.Add(self.btn_open, 0, wx.RIGHT, border=5)
        self.btn_open.Disable()
        self.btn_refresh = wx.StaticText(self, label="Обновить")
        font = wx.Font().Underlined()
        self.btn_refresh.SetFont(font)
        self.btn_refresh.SetForegroundColour(wx.Colour(100, 100, 255))
        self.btn_refresh.Bind(wx.EVT_LEFT_DOWN, self.on_refresh)
        self.btn_refresh.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        hsz.Add(self.btn_refresh, 0, wx.RIGHT, border=5)
        self.SetSizer(sz)
        self.Layout()
        self.load()
        self.choice.Bind(wx.EVT_CHOICE, self.on_choice)

    @db_session
    def load(self):
        if self.query is not None:
            query = self.query
        else:
            query = select(o for o in BoreHole)
        self.choice.Clear()
        self.items = []
        for _i, o in enumerate(query):
            self.items.append(o)
            self.choice.Append(o.Name)
            if self.selection is not None and o.RID == self.selection.RID:
                self.selection = o
                self.choice.SetSelection(_i)

    def on_open(self, event):
        o = self.items[self.choice.GetSelection()]
        app_ctx().main.open("bore_hole_editor", is_new=False, o=o)

    def on_refresh(self, event):
        self.load()
        self.update_controls_state()

    def on_choice(self, event): ...

    def update_controls_state(self):
        self.btn_open.Enable(self.selection is not None)

    def GetValue(self):
        return self.selection

    def SetValue(self, value):
        for _i, o in enumerate(self.items):
            if isinstance(value, BoreHole) or value.RID == o.RID:
                self.selection = o
                self.choice.SetSelection(_i)
                break

    def Disable(self):
        self.choice.Disable()

    def Enable(self, enable=True):
        self.choice.Enable(enable)
