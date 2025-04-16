import wx
from pony.orm import db_session, select

from src.ctx import app_ctx
from src.database import MineObject, Station


class Choice(wx.Panel):
    def __init__(self, parent, mode="all"):
        super().__init__(parent)
        self.items = []
        self.selection = None
        self.mode = mode
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
        self.update_controls_state()

    @db_session
    def load(self):
        self.items = []
        self.choice.Clear()

        def _r(p=None):
            if p is None:
                q = select(o for o in MineObject if o.Level == 0)
            else:
                q = select(o for o in MineObject if o.parent == p)
            if p is not None and self.mode == "all_with_stations":
                for o in select(o for o in Station if o.mine_object == p):
                    self.items.append(o)
                    self.choice.Append((" . " * (p.Level + 1)) + o.get_tree_name())
            for o in q:
                self.items.append(o)
                self.choice.Append((" . " * o.Level) + o.get_tree_name())
                if self.mode == "all" or (self.mode == "all_without_excavation" and o.Type != "HORIZON"):
                    _r(o)

        if self.mode in ["all", "all_with_stations", "all_without_excavation"]:
            _r()
        elif self.mode == "region":
            q = select(o for o in MineObject if o.Type == "REGION")
        elif self.mode == "rocks":
            q = select(o for o in MineObject if o.Type == "ROCKS")
        elif self.mode == "field":
            q = select(o for o in MineObject if o.Type == "FIELDS")
        elif self.mode == "horizon":
            q = select(o for o in MineObject if o.Type == "HORIZON")
        elif self.mode == "excavation":
            q = select(o for o in MineObject if o.Type == "EXCAVATION")

        if self.mode not in ["all", "all_with_stations", "all_without_excavation"]:
            for o in q:
                self.items.append(o)
                self.choice.Append(o.get_tree_name())

        if self.selection is not None:
            for _i, o in enumerate(self.items):
                if type(o) == type(self.selection) and o.RID == self.selection.RID:  # noqa: E721
                    self.selection = o
                    self.choice.SetSelection(_i)
                    break

    def on_open(self, event):
        o = self.items[self.choice.GetSelection()]
        app_ctx().main.open("mine_object_editor", is_new=False, o=o)

    def on_refresh(self, event):
        self.load()
        self.update_controls_state()

    def on_choice(self, event):
        self.selection = self.items[self.choice.GetSelection()]
        self.update_controls_state()

    def update_controls_state(self):
        self.btn_open.Enable(self.selection is not None)

    def SetValue(self, value):
        for _i, o in enumerate(self.items):
            if type(o) == type(value) and o.RID == value.RID:
                self.selection = o
                self.choice.SetSelection(_i)
                break
        self.update_controls_state()

    def GetValue(self):
        return self.selection

    def Disable(self):
        self.choice.Disable()

    def Enable(self, enable=True):
        return self.choice.Enable(enable)
