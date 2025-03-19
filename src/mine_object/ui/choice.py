import wx
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import MineObject


class Choice(wx.Panel):
    def __init__(self, parent, mode="all"):
        super().__init__(parent)
        self.items = []
        self.selection = None
        self.mode = mode
        sz = wx.BoxSizer(wx.VERTICAL)
        self.choice = wx.Choice(self)
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

    def load(self): ...

    def on_open(self, event): ...

    def on_refresh(self, event): ...

    def on_choice(self, event): ...

    def update_controls_state(self): ...
